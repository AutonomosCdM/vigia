"""
Temporary compatibility module for medical_dispatcher imports.
This module provides backward compatibility during the transition to ADK agents.
The medical dispatching functionality has been replaced by ADK agents.
"""

# Import from triage engine for backward compatibility
from .triage_engine import TriageResult as TriageDecision
from .triage_engine import MedicalTriageEngine

# Create compatibility aliases
class MedicalDispatcher:
    """Compatibility class for legacy MedicalDispatcher usage."""
    
    def __init__(self):
        self.triage_engine = MedicalTriageEngine()
    
    async def initialize(self):
        """Initialize the dispatcher."""
        return True
    
    async def dispatch(self, standardized_input):
        """Legacy dispatch method - delegates to triage engine."""
        # This is a simplified implementation for compatibility
        triage_result = await self.triage_engine.evaluate_medical_urgency(
            standardized_input.content
        )
        return {
            'success': True,
            'triage_decision': triage_result,
            'route': 'adk_agents'
        }

class ProcessingRoute:
    """Compatibility class for processing routes."""
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    ROUTINE = "routine"
    
# Ensure backward compatibility
__all__ = ['MedicalDispatcher', 'TriageDecision', 'ProcessingRoute']