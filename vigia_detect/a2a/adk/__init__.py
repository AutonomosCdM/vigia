"""
Vigia A2A Protocol - Native Google ADK Implementation
===================================================

Agent-to-Agent communication protocol implementation using Google's A2A standards.
Provides secure, reliable communication between medical agents with HIPAA compliance.

Components:
- Agent Cards: Agent capability discovery and metadata
- Communication Protocol: HTTP/SSE-based messaging with medical extensions
- Service Registry: Dynamic agent discovery and health monitoring
- Message Queue: Reliable message delivery with medical priority handling
"""

from .agent_cards import VigiaAgentCard, MedicalCapabilityRegistry
from .communication_protocol import VigiaA2AProtocol, MedicalMessageHandler
from .service_registry import VigiaServiceRegistry, AgentDiscoveryService
from .message_queue import MedicalMessageQueue, PriorityMessageHandler

__all__ = [
    "VigiaAgentCard",
    "MedicalCapabilityRegistry", 
    "VigiaA2AProtocol",
    "MedicalMessageHandler",
    "VigiaServiceRegistry",
    "AgentDiscoveryService",
    "MedicalMessageQueue",
    "PriorityMessageHandler"
]

# A2A Protocol version
__a2a_version__ = "1.0.0"
__adk_compatibility__ = "1.0.0"