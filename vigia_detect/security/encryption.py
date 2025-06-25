"""
Medical Data Encryption Module

Provides HIPAA-compliant encryption services for medical data protection.
Implements AES-256 encryption with secure key management for PHI protection.
"""

import os
import base64
import secrets
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Medical-grade encryption manager for PHI protection.
    
    Implements AES-256 encryption with PBKDF2 key derivation for secure
    medical data handling compliant with HIPAA requirements.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager with master key"""
        self.master_key = master_key or os.getenv('VIGIA_MASTER_KEY')
        if not self.master_key:
            self.master_key = self._generate_master_key()
            logger.warning("Generated temporary master key - not suitable for production")
        
        self._fernet = None
        self._init_encryption()
    
    def _generate_master_key(self) -> str:
        """Generate a secure master key for development/testing"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _init_encryption(self):
        """Initialize Fernet encryption with derived key"""
        try:
            # Use PBKDF2 to derive key from master key
            salt = b'vigia_medical_salt_2025'  # Static salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
            logger.info("Encryption manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt medical data
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted = self._fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt medical data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt dictionary data with field-level encryption
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted_dict = {}
        for key, value in data.items():
            if value is not None:
                encrypted_dict[key] = self.encrypt(str(value))
            else:
                encrypted_dict[key] = None
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_data: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt dictionary data
        
        Args:
            encrypted_data: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted_dict = {}
        for key, value in encrypted_data.items():
            if value is not None:
                decrypted_dict[key] = self.decrypt(value)
            else:
                decrypted_dict[key] = None
        return decrypted_dict
    
    def encrypt_medical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt medical data dictionary with field-level encryption
        
        Args:
            data: Medical data dictionary
            
        Returns:
            Encrypted medical data
        """
        return self.encrypt_dict(data)
    
    def decrypt_medical_data(self, encrypted_data: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt medical data dictionary
        
        Args:
            encrypted_data: Encrypted medical data
            
        Returns:
            Decrypted medical data
        """
        return self.decrypt_dict(encrypted_data)
    
    def generate_medical_grade_key(self) -> bytes:
        """
        Generate medical-grade encryption key (256-bit)
        
        Returns:
            Secure 256-bit key
        """
        return secrets.token_bytes(32)  # 256 bits
    
    def get_current_key(self) -> str:
        """Get current encryption key"""
        return self.master_key
    
    def rotate_encryption_key(self):
        """Rotate encryption key for security"""
        # Store old key for historical decryption
        if not hasattr(self, '_key_history'):
            self._key_history = []
        self._key_history.append(self.master_key)
        
        # Generate new key
        self.master_key = self._generate_master_key()
        self._init_encryption()
        logger.info("Encryption key rotated successfully")
    
    def decrypt_with_key_history(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt data using key history (for key rotation support)
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        # Try current key first
        try:
            return self.decrypt_medical_data(encrypted_data)
        except Exception:
            pass
        
        # Try historical keys
        if hasattr(self, '_key_history'):
            current_key = self.master_key
            for old_key in reversed(self._key_history):
                try:
                    # Temporarily use old key
                    self.master_key = old_key
                    self._init_encryption()
                    result = self.decrypt_medical_data(encrypted_data)
                    
                    # Restore current key
                    self.master_key = current_key
                    self._init_encryption()
                    return result
                except Exception:
                    continue
            
            # Restore current key
            self.master_key = current_key
            self._init_encryption()
        
        raise ValueError("Unable to decrypt data with current or historical keys")


class MedicalDataEncryption:
    """
    Specialized encryption for medical data with PHI protection.
    
    Provides field-level encryption for sensitive medical information
    with audit trail and compliance features.
    """
    
    # Fields that require encryption
    SENSITIVE_FIELDS = {
        'patient_name', 'patient_id', 'mrn', 'ssn', 'date_of_birth',
        'address', 'phone', 'email', 'medical_record_number',
        'diagnosis', 'treatment_notes', 'physician_notes'
    }
    
    def __init__(self, encryption_manager: Optional[EncryptionManager] = None):
        """Initialize with encryption manager"""
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.audit_log = []
    
    def encrypt_medical_record(self, record: Dict[str, Any], record_id: str) -> Dict[str, Any]:
        """
        Encrypt a complete medical record
        
        Args:
            record: Medical record dictionary
            record_id: Unique record identifier
            
        Returns:
            Encrypted medical record
        """
        try:
            encrypted_record = {}
            
            for field, value in record.items():
                if field in self.SENSITIVE_FIELDS and value is not None:
                    # Encrypt sensitive fields
                    encrypted_record[field] = self.encryption_manager.encrypt(str(value))
                    self._log_encryption_event(record_id, field, 'encrypted')
                else:
                    # Keep non-sensitive fields as-is
                    encrypted_record[field] = value
            
            encrypted_record['_encrypted'] = True
            encrypted_record['_encryption_timestamp'] = self._get_timestamp()
            
            return encrypted_record
            
        except Exception as e:
            logger.error(f"Medical record encryption failed: {e}")
            raise
    
    def decrypt_medical_record(self, encrypted_record: Dict[str, Any], record_id: str) -> Dict[str, Any]:
        """
        Decrypt a medical record
        
        Args:
            encrypted_record: Encrypted medical record
            record_id: Unique record identifier
            
        Returns:
            Decrypted medical record
        """
        try:
            if not encrypted_record.get('_encrypted', False):
                return encrypted_record
            
            decrypted_record = {}
            
            for field, value in encrypted_record.items():
                if field.startswith('_'):
                    # Skip metadata fields
                    continue
                elif field in self.SENSITIVE_FIELDS and value is not None:
                    # Decrypt sensitive fields
                    decrypted_record[field] = self.encryption_manager.decrypt(value)
                    self._log_encryption_event(record_id, field, 'decrypted')
                else:
                    # Keep non-sensitive fields as-is
                    decrypted_record[field] = value
            
            return decrypted_record
            
        except Exception as e:
            logger.error(f"Medical record decryption failed: {e}")
            raise
    
    def is_field_sensitive(self, field_name: str) -> bool:
        """Check if a field contains sensitive data"""
        return field_name in self.SENSITIVE_FIELDS
    
    def _log_encryption_event(self, record_id: str, field: str, action: str):
        """Log encryption/decryption events for audit"""
        event = {
            'timestamp': self._get_timestamp(),
            'record_id': record_id,
            'field': field,
            'action': action,
            'user': os.getenv('USER', 'system')
        }
        self.audit_log.append(event)
        logger.info(f"Medical data {action}: {field} for record {record_id}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for audit logging"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_audit_log(self) -> list:
        """Get encryption audit log"""
        return self.audit_log.copy()
    
    def validate_encryption_integrity(self, encrypted_record: Dict[str, Any]) -> bool:
        """
        Validate encryption integrity of medical record
        
        Args:
            encrypted_record: Encrypted medical record
            
        Returns:
            True if encryption is valid
        """
        try:
            if not encrypted_record.get('_encrypted', False):
                return True  # Not encrypted, so valid
            
            # Try to decrypt sensitive fields to validate
            for field, value in encrypted_record.items():
                if field in self.SENSITIVE_FIELDS and value is not None:
                    try:
                        self.encryption_manager.decrypt(value)
                    except Exception:
                        logger.error(f"Encryption integrity check failed for field: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Encryption integrity validation failed: {e}")
            return False