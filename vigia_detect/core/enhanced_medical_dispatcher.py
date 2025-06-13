"""
Enhanced Medical Dispatcher with MINSAL Integration
=================================================

Enhanced version of medical dispatcher that routes to appropriate
decision engines based on jurisdiction and patient context.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import json

from .medical_dispatcher import MedicalDispatcher, ProcessingRoute
from ..agents.enhanced_medical_agent_wrapper import create_medical_agent
from ..systems.minsal_medical_decision_engine import make_minsal_clinical_decision
from ..utils.secure_logger import SecureLogger

logger = SecureLogger("enhanced_medical_dispatcher")


class JurisdictionType(Enum):
    """Medical jurisdiction types for routing decisions."""
    CHILE = "chile"
    INTERNATIONAL = "international" 
    AUTO_DETECT = "auto_detect"


class EnhancedMedicalDispatcher(MedicalDispatcher):
    """
    Enhanced medical dispatcher with jurisdiction-aware routing.
    Extends base dispatcher to support MINSAL integration.
    """
    
    def __init__(self, default_jurisdiction: str = "chile"):
        super().__init__()
        self.default_jurisdiction = default_jurisdiction
        self.jurisdiction_detectors = self._setup_jurisdiction_detectors()
        
    def _setup_jurisdiction_detectors(self) -> Dict[str, Any]:
        """Setup jurisdiction detection rules"""
        return {
            'chile_indicators': [
                'chile', 'chileno', 'chilena', 'minsal', 'fonasa', 'isapre',
                'hospital_publico', 'consultorio', 'cesfam'
            ],
            'language_indicators': {
                'spanish': ['lesiones por presión', 'úlceras por presión', 'lpp', 'upp'],
                'english': ['pressure injury', 'pressure ulcer', 'pi', 'pu']
            }
        }
    
    async def enhanced_route_medical_request(self, standardized_input, 
                                           session_state) -> Dict[str, Any]:
        """
        Enhanced routing with jurisdiction detection and appropriate engine selection.
        
        Args:
            standardized_input: Standardized medical input
            session_state: Current session state
            
        Returns:
            Enhanced routing decision with jurisdiction context
        """
        try:
            # 1. Detect jurisdiction from input context
            jurisdiction = self._detect_jurisdiction(standardized_input)
            
            # 2. Create appropriate medical agent
            medical_agent = create_medical_agent(
                jurisdiction=jurisdiction,
                use_minsal=(jurisdiction == "chile")
            )
            
            # 3. Route based on input type and jurisdiction
            routing_decision = await self._make_enhanced_routing_decision(
                standardized_input, session_state, jurisdiction, medical_agent
            )
            
            # 4. Add jurisdiction context to decision
            routing_decision.update({
                'jurisdiction': jurisdiction,
                'decision_engine': 'minsal' if jurisdiction == 'chile' else 'international',
                'agent_type': 'enhanced_lpp_medical_agent',
                'routing_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"Enhanced routing error: {e}")
            # Fallback to base routing
            return await super().route_medical_request(standardized_input, session_state)
    
    def _detect_jurisdiction(self, standardized_input) -> str:
        """
        Detect medical jurisdiction from input context.
        
        Args:
            standardized_input: Standardized medical input
            
        Returns:
            Detected jurisdiction ('chile' or 'international')
        """
        # Check patient context for Chilean indicators
        patient_context = getattr(standardized_input, 'patient_context', {})
        
        # Explicit jurisdiction setting
        if 'jurisdiction' in patient_context:
            return patient_context['jurisdiction'].lower()
        
        # Chilean healthcare system indicators
        chile_indicators = self.jurisdiction_detectors['chile_indicators']
        
        # Check in patient context
        for key, value in patient_context.items():
            if isinstance(value, str):
                if any(indicator in value.lower() for indicator in chile_indicators):
                    return "chile"
        
        # Check in metadata
        metadata = getattr(standardized_input, 'metadata', {})
        for key, value in metadata.items():
            if isinstance(value, str):
                if any(indicator in value.lower() for indicator in chile_indicators):
                    return "chile"
        
        # Check medical content language
        medical_content = getattr(standardized_input, 'medical_content', {})
        text_content = str(medical_content.get('description', '')).lower()
        
        spanish_terms = self.jurisdiction_detectors['language_indicators']['spanish']
        if any(term in text_content for term in spanish_terms):
            return "chile"
        
        # Default to configured jurisdiction
        return self.default_jurisdiction
    
    async def _make_enhanced_routing_decision(self, standardized_input, session_state,
                                            jurisdiction: str, medical_agent) -> Dict[str, Any]:
        """
        Make enhanced routing decision with jurisdiction context.
        
        Args:
            standardized_input: Standardized input
            session_state: Session state
            jurisdiction: Detected jurisdiction
            medical_agent: Selected medical agent
            
        Returns:
            Enhanced routing decision
        """
        # Get base routing decision
        base_decision = await super().route_medical_request(standardized_input, session_state)
        
        # Enhance with jurisdiction-specific logic
        if base_decision['route'] == ProcessingRoute.CLINICAL_IMAGE:
            
            # Add jurisdiction-specific processing parameters
            enhanced_params = base_decision.get('processing_parameters', {})
            enhanced_params.update({
                'jurisdiction': jurisdiction,
                'use_minsal_engine': (jurisdiction == "chile"),
                'language_preference': 'spanish' if jurisdiction == 'chile' else 'english',
                'regulatory_compliance': self._get_regulatory_requirements(jurisdiction),
                'medical_agent': medical_agent
            })
            
            base_decision['processing_parameters'] = enhanced_params
            
        elif base_decision['route'] == ProcessingRoute.MEDICAL_QUERY:
            
            # Enhance medical query processing
            query_params = base_decision.get('processing_parameters', {})
            query_params.update({
                'knowledge_sources': self._get_knowledge_sources(jurisdiction),
                'terminology_preference': self._get_terminology_preference(jurisdiction),
                'medical_agent': medical_agent
            })
            
            base_decision['processing_parameters'] = query_params
        
        return base_decision
    
    def _get_regulatory_requirements(self, jurisdiction: str) -> Dict[str, Any]:
        """Get regulatory requirements for jurisdiction"""
        if jurisdiction == "chile":
            return {
                'primary_standards': ['MINSAL_2018', 'NPUAP_EPUAP_2019'],
                'audit_requirements': ['minsal_compliance', 'hipaa_compliance'],
                'documentation_language': 'spanish',
                'escalation_protocols': 'chile_healthcare_system'
            }
        else:
            return {
                'primary_standards': ['NPUAP_EPUAP_2019'],
                'audit_requirements': ['hipaa_compliance', 'iso_13485'],
                'documentation_language': 'english',
                'escalation_protocols': 'international_standards'
            }
    
    def _get_knowledge_sources(self, jurisdiction: str) -> List[str]:
        """Get knowledge sources for jurisdiction"""
        base_sources = ['npuap_epuap_guidelines', 'medical_literature']
        
        if jurisdiction == "chile":
            base_sources.extend([
                'minsal_guidelines_2018',
                'minsal_protocols_2015',
                'chilean_hospital_protocols'
            ])
        
        return base_sources
    
    def _get_terminology_preference(self, jurisdiction: str) -> Dict[str, str]:
        """Get terminology preferences for jurisdiction"""
        if jurisdiction == "chile":
            return {
                'condition_name': 'lesiones_por_presion',
                'alternative_names': ['ulceras_por_presion', 'escaras'],
                'classification_system': 'categorias_minsal',
                'severity_terms': 'spanish_medical'
            }
        else:
            return {
                'condition_name': 'pressure_injury',
                'alternative_names': ['pressure_ulcer', 'decubitus_ulcer'],
                'classification_system': 'npuap_stages',
                'severity_terms': 'english_medical'
            }


# Factory function for easy instantiation
def create_enhanced_dispatcher(default_jurisdiction: str = "chile") -> EnhancedMedicalDispatcher:
    """
    Create enhanced medical dispatcher with jurisdiction detection.
    
    Args:
        default_jurisdiction: Default jurisdiction when auto-detection fails
        
    Returns:
        Configured enhanced dispatcher
    """
    return EnhancedMedicalDispatcher(default_jurisdiction=default_jurisdiction)