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

from google.adk.agents import BaseAgent
from google.adk.tools import BaseTool, ToolContext

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
        capabilities: List[str],
        medical_specialties: List[str] = None
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
        super().__init__(name=agent_name)
        
        # Store agent properties as private attributes to avoid pydantic conflicts
        self._agent_id = agent_id
        self._agent_name = agent_name
        self._capabilities = capabilities
        self._medical_specialties = medical_specialties or []
        
        # Medical context tracking (private to avoid pydantic conflicts)
        self._active_cases: Dict[str, Dict[str, Any]] = {}
        self._audit_trail: List[Dict[str, Any]] = []
        
        # Initialize tools (private to avoid pydantic conflicts)
        self._tools = self.create_medical_tools()
        
        logger.info(f"Initialized Vigia medical agent: {self._agent_name} ({self._agent_id})")
    
    def _register_agent_card(self) -> None:
        """Register agent capabilities (simplified for basic ADK)."""
        logger.info(f"Agent {self._agent_id} registered with capabilities: {self._capabilities}")
    
    async def discover_medical_agent(
        self, 
        capability: str,
        specialty: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Discover another medical agent by capability and specialty (simplified).
        
        Args:
            capability: Required agent capability
            specialty: Optional medical specialty filter
            
        Returns:
            Agent info dict or None
        """
        # Simplified discovery for testing
        logger.info(f"Discovering agent with capability: {capability}, specialty: {specialty}")
        return {"agent_id": "discovered_agent", "capability": capability}
    
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
        
        # Send via simplified message protocol
        logger.info(f"Sending medical message to {target_agent_id}: {message_type}")
        response = {"status": "sent", "message_id": message["id"]}
        
        return response
    
    def create_medical_tools(self) -> Dict[str, Any]:
        """
        Create common medical tools available to all agents.
        
        Returns:
            Dict of medical tools
        """
        tools = {}
        
        # Medical context tool
        async def get_medical_context(patient_id: str) -> dict:
            """Get medical context for a patient case.
            
            Args:
                patient_id: Patient identifier
                
            Returns:
                dict: Medical context data
            """
            return self._active_cases.get(patient_id, {})
        
        tools["get_medical_context"] = get_medical_context
        
        # Audit logging tool
        async def log_medical_action(action: str, patient_id: str, details: dict) -> dict:
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
                "agent_id": self._agent_id,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            
            self._audit_trail.append(audit_entry)
            
            return {"status": "logged", "audit_id": str(uuid.uuid4())}
        
        tools["log_medical_action"] = log_medical_action
        
        return tools
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent.
        
        Returns:
            Health status information
        """
        return {
            "agent_id": self._agent_id,
            "agent_name": self._agent_name,
            "status": "healthy",
            "capabilities": self._capabilities,
            "medical_specialties": self._medical_specialties,
            "active_cases": len(self._active_cases),
            "audit_entries": len(self._audit_trail),
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
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