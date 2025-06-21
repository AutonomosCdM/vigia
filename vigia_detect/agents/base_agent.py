"""
Base Agent Framework for Vigia Medical System
=============================================

Base classes and utilities for agent-based medical processing.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class AgentCapability(Enum):
    """Capabilities that agents can have."""
    IMAGE_ANALYSIS = "image_analysis"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    PROTOCOL_CONSULTATION = "protocol_consultation"
    MEDICAL_COMMUNICATION = "medical_communication"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    # Additional medical capabilities
    MEDICAL_PROTOCOL_SEARCH = "medical_protocol_search"
    CLINICAL_KNOWLEDGE = "clinical_knowledge"
    EVIDENCE_RETRIEVAL = "evidence_retrieval"
    MEDICAL_RECOMMENDATIONS = "medical_recommendations"


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Response structure from agent processing."""
    response_id: str
    agent_id: str
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent:
    """Base class for all medical agents."""
    
    def __init__(self, agent_id: str, capabilities: List[AgentCapability], 
                 name: str = None, description: str = None, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.name = name or agent_id
        self.description = description or f"Medical agent: {agent_id}"
        self.version = version
        self.is_active = False
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the agent."""
        self.is_active = True
        return True
    
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """Process a message and return response."""
        raise NotImplementedError("Subclasses must implement process_message")
    
    async def health_check(self) -> bool:
        """Check agent health."""
        return self.is_active
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities."""
        return self.capabilities