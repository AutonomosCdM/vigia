"""
Enhanced medical agent wrapper for legacy compatibility.
Provides enhanced versions of medical agents with additional functionality.
"""

# Import base ADK agents
from .adk.clinical_assessment import ClinicalAssessmentAgent
from .adk.image_analysis import ImageAnalysisAgent
from .adk.communication import CommunicationAgent
from .adk.protocol import ProtocolAgent
from .adk.workflow_orchestration import WorkflowOrchestrationAgent


class EnhancedLPPMedicalAgent(ClinicalAssessmentAgent):
    """Enhanced LPP Medical Agent with additional features."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enhanced_features = True
        
    async def enhanced_assessment(self, image_data, patient_context=None):
        """Enhanced medical assessment with additional features."""
        # Use the base ADK agent functionality
        return await self.assess_clinical_findings(image_data, patient_context)


def create_medical_agent(**kwargs):
    """Factory function to create enhanced medical agent."""
    return EnhancedLPPMedicalAgent(**kwargs)


# Legacy aliases
EnhancedMedicalAgent = EnhancedLPPMedicalAgent
MedicalAgentFactory = create_medical_agent

# Export for backward compatibility
__all__ = [
    'EnhancedLPPMedicalAgent',
    'EnhancedMedicalAgent',
    'create_medical_agent',
    'MedicalAgentFactory'
]