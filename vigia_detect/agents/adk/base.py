"""
Vigia Base Agent - Native Google ADK Implementation
==================================================

Base class for all Vigia medical agents using Google ADK.
Provides common medical functionality, A2A communication, and agent discovery.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

from google.adk.agents import BaseAgent, AgentContext
from google.adk.core import AdkConfig
from google.adk.core.types import AgentCapability, AgentMetadata
from google.adk.communication import A2AClient, AgentCard
from google.adk.tools import Tool

logger = logging.getLogger(__name__)


class VigiaBaseAgent(BaseAgent):
    """
    Base class for all Vigia medical agents.
    
    Provides:
    - Medical-specific capabilities and metadata
    - A2A communication for agent-to-agent coordination
    - Common medical tools and utilities
    - HIPAA-compliant logging and audit trails
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: List[AgentCapability],
        medical_specialties: List[str] = None,
        config: AdkConfig = None
    ):
        """
        Initialize Vigia medical agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name
            capabilities: List of agent capabilities
            medical_specialties: Medical specialties this agent handles
            config: ADK configuration
        """
        
        # Initialize base ADK agent
        super().__init__(
            agent_id=agent_id,
            config=config or AdkConfig()
        )
        
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.medical_specialties = medical_specialties or []
        
        # Initialize A2A communication
        self.a2a_client = A2AClient(self.config)
        
        # Medical context tracking
        self.active_cases: Dict[str, Dict[str, Any]] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Register with agent discovery service
        self._register_agent_card()
        
        logger.info(f"Initialized Vigia medical agent: {agent_name} ({agent_id})")
    
    def _register_agent_card(self) -> None:
        """Register agent capabilities with A2A discovery service."""
        agent_card = AgentCard(
            agent_id=self.agent_id,
            name=self.agent_name,
            description=f"Vigia medical agent specialized in {', '.join(self.medical_specialties)}",
            capabilities=self.capabilities,
            metadata=AgentMetadata(
                specialties=self.medical_specialties,
                medical_grade=True,
                hipaa_compliant=True,
                version="1.0.0"
            ),
            endpoints={
                "health": f"/agents/{self.agent_id}/health",
                "capabilities": f"/agents/{self.agent_id}/capabilities",
                "task": f"/agents/{self.agent_id}/task"
            }
        )
        
        # Register with A2A discovery service
        self.a2a_client.register_agent_card(agent_card)
    
    async def discover_medical_agent(
        self, 
        capability: AgentCapability,
        specialty: str = None
    ) -> Optional[AgentCard]:
        """
        Discover another medical agent by capability and specialty.
        
        Args:
            capability: Required agent capability
            specialty: Optional medical specialty filter
            
        Returns:
            AgentCard of discovered agent or None
        """
        
        filters = {"capability": capability}
        if specialty:
            filters["specialty"] = specialty
            
        agent_cards = await self.a2a_client.discover_agents(filters)
        
        # Prefer medical-grade agents
        for card in agent_cards:
            if card.metadata.get("medical_grade", False):
                return card
                
        return agent_cards[0] if agent_cards else None
    
    async def send_medical_message(
        self,
        target_agent_id: str,
        message_type: str,
        medical_data: Dict[str, Any],
        patient_id: str = None,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send HIPAA-compliant medical message to another agent.
        
        Args:
            target_agent_id: ID of target agent
            message_type: Type of medical message
            medical_data: Medical data to send
            patient_id: Patient identifier (for audit)
            urgency: Message urgency (normal, high, critical)
            
        Returns:
            Response from target agent
        """
        
        # Create medical message with audit trail
        message = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "sender": self.agent_id,
            "recipient": target_agent_id,
            "timestamp": datetime.now().isoformat(),
            "data": medical_data,
            "patient_id": patient_id,
            "urgency": urgency,
            "encrypted": True,  # ADK handles encryption
            "audit_trail": True
        }
        
        # Log for audit
        self.audit_trail.append({
            "action": "send_medical_message",
            "message_id": message["id"],
            "target": target_agent_id,
            "timestamp": message["timestamp"],
            "patient_id": patient_id,
            "urgency": urgency
        })
        
        # Send via A2A protocol
        response = await self.a2a_client.send_message(target_agent_id, message)
        
        return response
    
    def create_medical_tools(self) -> List[Tool]:
        """
        Create common medical tools available to all agents.
        
        Returns:
            List of medical tools
        """
        tools = []
        
        # Medical context tool
        def get_medical_context(patient_id: str) -> dict:
            """Get medical context for a patient case.
            
            Args:
                patient_id: Patient identifier
                
            Returns:
                dict: Medical context data
            """
            return self.active_cases.get(patient_id, {})
        
        tools.append(Tool(
            name="get_medical_context",
            function=get_medical_context,
            description="Retrieve medical context for patient case"
        ))
        
        # Audit logging tool
        def log_medical_action(action: str, patient_id: str, details: dict) -> dict:
            """Log medical action for audit trail.
            
            Args:
                action: Medical action performed
                patient_id: Patient identifier
                details: Action details
                
            Returns:
                dict: Confirmation of logging
            """
            audit_entry = {
                "action": action,
                "patient_id": patient_id,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            
            self.audit_trail.append(audit_entry)
            
            return {"status": "logged", "audit_id": str(uuid.uuid4())}
        
        tools.append(Tool(
            name="log_medical_action",
            function=log_medical_action,
            description="Log medical action for compliance audit"
        ))
        
        return tools
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent.
        
        Returns:
            Health status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": "healthy",
            "capabilities": [cap.value for cap in self.capabilities],
            "medical_specialties": self.medical_specialties,
            "active_cases": len(self.active_cases),
            "audit_entries": len(self.audit_trail),
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Process a medical case (to be implemented by subclasses).
        
        Args:
            case_id: Unique case identifier
            patient_data: Patient medical data
            context: Agent execution context
            
        Returns:
            Medical processing result
        """
        raise NotImplementedError("Subclasses must implement process_medical_case")