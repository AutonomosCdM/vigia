"""
Vigia ADK Agents - Google Agent Development Kit Integration
=========================================================

This module contains native Google ADK implementations of Vigia's medical agents.
All agents are built using Google ADK patterns without wrappers or legacy code.

Architecture:
- BaseAgent: Custom agents with specialized logic (ImageAnalysisAgent)
- LLMAgent: Agents using language models for reasoning (ClinicalAssessmentAgent, ProtocolAgent)
- WorkflowAgent: Deterministic process orchestration (CommunicationAgent, WorkflowOrchestrationAgent)

A2A Protocol:
- Agent Cards for capability discovery
- HTTP/SSE communication between agents
- Secure authentication and task management
"""

from .base import VigiaBaseAgent
from .image_analysis import ImageAnalysisAgent
from .clinical_assessment import ClinicalAssessmentAgent
from .protocol import ProtocolAgent
from .communication import CommunicationAgent
from .workflow_orchestration import WorkflowOrchestrationAgent

__all__ = [
    "VigiaBaseAgent",
    "ImageAnalysisAgent", 
    "ClinicalAssessmentAgent",
    "ProtocolAgent",
    "CommunicationAgent",
    "WorkflowOrchestrationAgent"
]

# Version info
__version__ = "1.0.0"
__adk_version__ = "1.0.0"