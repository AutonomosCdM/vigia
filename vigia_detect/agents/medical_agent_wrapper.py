"""
Legacy wrapper for medical agents.
Provides backward compatibility during transition to ADK architecture.
"""

# Import ADK agents for backward compatibility
from .adk.clinical_assessment import ClinicalAssessmentAgent
from .adk.image_analysis import ImageAnalysisAgent
from .adk.communication import CommunicationAgent
from .adk.protocol import ProtocolAgent
from .adk.workflow_orchestration import WorkflowOrchestrationAgent

# Legacy aliases for backward compatibility
LPPMedicalAgent = ClinicalAssessmentAgent
MedicalAgent = ClinicalAssessmentAgent
ImageAgent = ImageAnalysisAgent
CommunicationWrapper = CommunicationAgent
ProtocolWrapper = ProtocolAgent
WorkflowWrapper = WorkflowOrchestrationAgent

# Export for backward compatibility
__all__ = [
    'LPPMedicalAgent',
    'MedicalAgent', 
    'ImageAgent',
    'CommunicationWrapper',
    'ProtocolWrapper',
    'WorkflowWrapper',
    'ClinicalAssessmentAgent',
    'ImageAnalysisAgent',
    'CommunicationAgent',
    'ProtocolAgent',
    'WorkflowOrchestrationAgent'
]