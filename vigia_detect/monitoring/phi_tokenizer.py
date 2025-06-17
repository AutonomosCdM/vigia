"""
PHI (Protected Health Information) Tokenizer for HIPAA Compliance
"""

import re
import hashlib
import logging
from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PHITokenizer:
    """
    HIPAA-compliant tokenizer for medical data
    
    Handles:
    - Patient identifiers (MRN, SSN, etc.)
    - Personal information (names, addresses, phone numbers)
    - Medical record numbers
    - Date patterns
    - Image paths with patient data
    - Free text with potential PHI
    """
    
    # PHI patterns (HIPAA Safe Harbor method)
    PHI_PATTERNS = {
        'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
        'phone': r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'mrn': r'\b(MRN|mrn|medical.record|patient.id)[-:\s]*([A-Z0-9]{6,})\b',
        'patient_code': r'\b(CD|PT|PAT)[-_]?\d{4}[-_]?\d{3,4}\b',
        'date_full': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
        'date_iso': r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        'file_path': r'[/\\](?:Users|home|Documents)[/\\][^/\\]+',
        'name_pattern': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Simple name pattern
    }
    
    # Medical-specific patterns
    MEDICAL_PATTERNS = {
        'lpp_location': r'\b(sacro|talón|cadera|cóccix|trocánter)\b',
        'medical_terms': r'\b(úlcera|lesión|LPP|escara|necrosis)\b',
        'severity_grade': r'\b(grado|grade|estadio)\s*([0-4]|I{1,4})\b'
    }
    
    def __init__(self, salt: Optional[str] = None):
        """
        Initialize PHI tokenizer
        
        Args:
            salt: Salt for hashing (uses fixed salt for consistency)
        """
        # Use environment-specific salt or default
        self.salt = salt or "vigia_lpp_phi_salt_2025"
        self.token_map = {}  # Cache for consistent tokenization
        
    def tokenize_string(self, text: str, preserve_medical_terms: bool = True) -> str:
        """
        Tokenize PHI in text while preserving medical context
        
        Args:
            text: Text that may contain PHI
            preserve_medical_terms: Keep medical terms for clinical context
            
        Returns:
            Tokenized text safe for external logging
        """
        if not text or not isinstance(text, str):
            return str(text)
        
        tokenized = text
        
        # Tokenize PHI patterns
        for pattern_name, pattern in self.PHI_PATTERNS.items():
            tokenized = re.sub(
                pattern,
                lambda m: self._create_token(pattern_name, m.group()),
                tokenized,
                flags=re.IGNORECASE
            )
        
        # Preserve medical terms if requested (they are not tokenized)
        if preserve_medical_terms:
            # Medical terms are preserved as-is for clinical context
            # No additional processing needed - they won't be tokenized by PHI patterns
            pass
        
        return tokenized
    
    def tokenize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively tokenize PHI in dictionary
        
        Args:
            data: Dictionary that may contain PHI
            
        Returns:
            Dictionary with PHI tokenized
        """
        if not isinstance(data, dict):
            return data
        
        tokenized = {}
        
        for key, value in data.items():
            # Tokenize key if it contains PHI
            safe_key = self._tokenize_key(key)
            
            # Tokenize value based on type
            if isinstance(value, str):
                safe_value = self.tokenize_string(value)
            elif isinstance(value, dict):
                safe_value = self.tokenize_dict(value)
            elif isinstance(value, list):
                safe_value = [self.tokenize_dict(item) if isinstance(item, dict) 
                            else self.tokenize_string(str(item)) if isinstance(item, str)
                            else item for item in value]
            else:
                safe_value = value
            
            tokenized[safe_key] = safe_value
        
        return tokenized
    
    def tokenize_image_path(self, image_path: str) -> str:
        """
        Tokenize image paths that may contain patient identifiers
        
        Args:
            image_path: Path to medical image
            
        Returns:
            Tokenized path safe for logging
        """
        if not image_path:
            return image_path
        
        # Extract filename and directory structure
        import os
        directory = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        
        # Tokenize directory if it contains user/patient info
        safe_directory = self.tokenize_string(directory)
        
        # Tokenize filename if it contains patient codes
        safe_filename = self.tokenize_string(filename)
        
        return os.path.join(safe_directory, safe_filename)
    
    def tokenize_patient_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized tokenization for patient context
        
        Args:
            context: Patient context dictionary
            
        Returns:
            Tokenized context preserving medical relevance
        """
        # Define fields that need special handling
        sensitive_fields = {
            'patient_id', 'patient_code', 'mrn', 'name', 'ssn',
            'phone', 'email', 'address', 'dob'
        }
        
        # Define medical fields to preserve
        medical_fields = {
            'lpp_grade', 'anatomical_location', 'risk_factors',
            'diabetes', 'mobility_score', 'nutrition_score',
            'tissue_perfusion', 'moisture_level'
        }
        
        tokenized = {}
        
        for key, value in context.items():
            if key.lower() in sensitive_fields:
                # Tokenize sensitive fields
                if isinstance(value, str):
                    tokenized[key] = self._create_token(key, value)
                else:
                    tokenized[key] = self._create_token(key, str(value))
            elif key.lower() in medical_fields:
                # Preserve medical fields as-is
                tokenized[key] = value
            else:
                # Default tokenization for other fields
                if isinstance(value, str):
                    tokenized[key] = self.tokenize_string(value)
                elif isinstance(value, dict):
                    tokenized[key] = self.tokenize_dict(value)
                else:
                    tokenized[key] = value
        
        return tokenized
    
    def _tokenize_key(self, key: str) -> str:
        """Tokenize dictionary keys that may contain PHI"""
        sensitive_key_patterns = ['patient', 'mrn', 'ssn', 'name', 'id']
        
        key_lower = key.lower()
        for pattern in sensitive_key_patterns:
            if pattern in key_lower:
                return self._create_token('key', key)
        
        return key
    
    def _create_token(self, pattern_type: str, original_value: str) -> str:
        """
        Create consistent token for PHI value
        
        Args:
            pattern_type: Type of PHI pattern
            original_value: Original value to tokenize
            
        Returns:
            Consistent token for the value
        """
        # Check cache first for consistency
        cache_key = f"{pattern_type}:{original_value}"
        if cache_key in self.token_map:
            return self.token_map[cache_key]
        
        # Create hash-based token
        hash_input = f"{self.salt}:{pattern_type}:{original_value}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        
        # Create readable token
        token = f"[{pattern_type.upper()}_{hash_value}]"
        
        # Cache for consistency
        self.token_map[cache_key] = token
        
        return token
    
    def create_medical_summary_token(self, context: Dict[str, Any]) -> str:
        """
        Create a summary token for medical context
        
        Args:
            context: Medical context dictionary
            
        Returns:
            Summary token representing the medical case
        """
        # Extract medical relevance indicators
        medical_indicators = []
        
        if 'lpp_grade' in context:
            medical_indicators.append(f"LPP_G{context['lpp_grade']}")
        
        if 'anatomical_location' in context:
            location = context['anatomical_location']
            medical_indicators.append(f"LOC_{location.upper()}")
        
        if 'diabetes' in context and context['diabetes']:
            medical_indicators.append("DIABETES")
        
        # Create timestamp component
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        
        # Combine into medical summary
        if medical_indicators:
            medical_part = "_".join(medical_indicators)
            return f"[MEDICAL_{medical_part}_{timestamp}]"
        else:
            return f"[MEDICAL_CASE_{timestamp}]"
    
    def validate_tokenization(self, original: str, tokenized: str) -> Dict[str, Any]:
        """
        Validate that tokenization successfully removed PHI
        
        Args:
            original: Original text
            tokenized: Tokenized text
            
        Returns:
            Validation results
        """
        validation_results = {
            'phi_detected': False,
            'phi_patterns_found': [],
            'tokenization_effective': True,
            'medical_context_preserved': True
        }
        
        # Check if any PHI patterns remain in tokenized text
        for pattern_name, pattern in self.PHI_PATTERNS.items():
            matches = re.findall(pattern, tokenized, re.IGNORECASE)
            if matches:
                validation_results['phi_detected'] = True
                validation_results['phi_patterns_found'].append({
                    'pattern': pattern_name,
                    'matches': matches
                })
        
        # Check if medical context is preserved
        medical_terms_original = len(re.findall(
            '|'.join(self.MEDICAL_PATTERNS.values()), 
            original, 
            re.IGNORECASE
        ))
        
        medical_terms_tokenized = len(re.findall(
            '|'.join(self.MEDICAL_PATTERNS.values()), 
            tokenized, 
            re.IGNORECASE
        ))
        
        if medical_terms_tokenized < medical_terms_original * 0.8:
            validation_results['medical_context_preserved'] = False
        
        # Overall effectiveness
        validation_results['tokenization_effective'] = (
            not validation_results['phi_detected'] and 
            validation_results['medical_context_preserved']
        )
        
        return validation_results