"""
Agent Cards - A2A Discovery Protocol Implementation
==================================================

Implementation of Google's A2A Agent Card specification for medical agent discovery.
Provides capability-based agent discovery with medical specialization support.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


class MedicalCapability(Enum):
    """Medical-specific agent capabilities."""
    LPP_DETECTION = "lpp_detection"
    WOUND_ASSESSMENT = "wound_assessment"
    CLINICAL_REASONING = "clinical_reasoning"
    PROTOCOL_CONSULTATION = "protocol_consultation"
    MEDICAL_COMMUNICATION = "medical_communication"
    CARE_COORDINATION = "care_coordination"
    EMERGENCY_RESPONSE = "emergency_response"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"
    RISK_ASSESSMENT = "risk_assessment"


class MedicalSpecialty(Enum):
    """Medical specialties for agent classification."""
    WOUND_CARE = "wound_care"
    NURSING = "nursing"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    EMERGENCY_MEDICINE = "emergency_medicine"
    INFECTIOUS_DISEASE = "infectious_disease"
    NUTRITION = "nutrition"
    PHYSICAL_THERAPY = "physical_therapy"
    SOCIAL_WORK = "social_work"


@dataclass
class MedicalMetadata:
    """Medical-specific metadata for agent cards."""
    medical_grade: bool = True
    hipaa_compliant: bool = True
    evidence_based: bool = True
    regulatory_compliance: List[str] = None
    medical_specialties: List[MedicalSpecialty] = None
    clinical_validation: bool = False
    emergency_capable: bool = False
    
    def __post_init__(self):
        if self.regulatory_compliance is None:
            self.regulatory_compliance = ["HIPAA", "NPUAP", "EPUAP"]
        if self.medical_specialties is None:
            self.medical_specialties = []


@dataclass
class AgentEndpoints:
    """Agent communication endpoints."""
    health: str
    capabilities: str
    task: str
    a2a_webhook: str
    status: str
    metrics: Optional[str] = None


@dataclass
class VigiaAgentCard:
    """
    Vigia Medical Agent Card following Google A2A specification.
    
    Provides comprehensive agent discovery information including
    medical capabilities, specialties, and communication endpoints.
    """
    
    # Core A2A fields
    agent_id: str
    name: str
    description: str
    version: str
    
    # Capability information
    capabilities: List[MedicalCapability]
    medical_metadata: MedicalMetadata
    
    # Communication endpoints
    endpoints: AgentEndpoints
    
    # Additional metadata
    tags: List[str] = None
    created_at: str = None
    updated_at: str = None
    
    # Medical-specific fields
    sla_requirements: Dict[str, Any] = None
    escalation_config: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values and validate card."""
        if self.tags is None:
            self.tags = ["medical", "vigia", "adk"]
        
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        
        if self.updated_at is None:
            self.updated_at = self.created_at
        
        if self.sla_requirements is None:
            self.sla_requirements = {
                "max_response_time_seconds": 30,
                "availability_percentage": 99.9,
                "max_queue_depth": 100
            }
        
        if self.escalation_config is None:
            self.escalation_config = {
                "escalation_timeout_seconds": 300,
                "escalation_contacts": [],
                "emergency_escalation": True
            }
        
        self._validate_card()
    
    def _validate_card(self) -> None:
        """Validate agent card for A2A compliance."""
        
        # Validate required fields
        required_fields = ["agent_id", "name", "description", "version"]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Agent card missing required field: {field}")
        
        # Validate capabilities
        if not self.capabilities:
            raise ValueError("Agent card must specify at least one capability")
        
        # Validate endpoints
        required_endpoints = ["health", "capabilities", "task", "a2a_webhook"]
        for endpoint in required_endpoints:
            if not getattr(self.endpoints, endpoint):
                raise ValueError(f"Agent card missing required endpoint: {endpoint}")
        
        # Validate medical compliance
        if self.medical_metadata.hipaa_compliant and "HIPAA" not in self.medical_metadata.regulatory_compliance:
            self.medical_metadata.regulatory_compliance.append("HIPAA")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent card to dictionary for JSON serialization."""
        
        card_dict = {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [cap.value for cap in self.capabilities],
            "medical_metadata": asdict(self.medical_metadata),
            "endpoints": asdict(self.endpoints),
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sla_requirements": self.sla_requirements,
            "escalation_config": self.escalation_config
        }
        
        # Convert enum lists to strings
        if self.medical_metadata.medical_specialties:
            card_dict["medical_metadata"]["medical_specialties"] = [
                spec.value for spec in self.medical_metadata.medical_specialties
            ]
        
        return card_dict
    
    def to_json(self) -> str:
        """Convert agent card to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, card_dict: Dict[str, Any]) -> 'VigiaAgentCard':
        """Create agent card from dictionary."""
        
        # Convert capability strings back to enums
        capabilities = [MedicalCapability(cap) for cap in card_dict["capabilities"]]
        
        # Convert medical metadata
        metadata_dict = card_dict["medical_metadata"]
        if "medical_specialties" in metadata_dict and metadata_dict["medical_specialties"]:
            metadata_dict["medical_specialties"] = [
                MedicalSpecialty(spec) for spec in metadata_dict["medical_specialties"]
            ]
        
        medical_metadata = MedicalMetadata(**metadata_dict)
        
        # Convert endpoints
        endpoints = AgentEndpoints(**card_dict["endpoints"])
        
        return cls(
            agent_id=card_dict["agent_id"],
            name=card_dict["name"],
            description=card_dict["description"],
            version=card_dict["version"],
            capabilities=capabilities,
            medical_metadata=medical_metadata,
            endpoints=endpoints,
            tags=card_dict.get("tags"),
            created_at=card_dict.get("created_at"),
            updated_at=card_dict.get("updated_at"),
            sla_requirements=card_dict.get("sla_requirements"),
            escalation_config=card_dict.get("escalation_config")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VigiaAgentCard':
        """Create agent card from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now().isoformat()
    
    def supports_capability(self, capability: MedicalCapability) -> bool:
        """Check if agent supports a specific capability."""
        return capability in self.capabilities
    
    def supports_specialty(self, specialty: MedicalSpecialty) -> bool:
        """Check if agent supports a specific medical specialty."""
        return specialty in self.medical_metadata.medical_specialties
    
    def is_emergency_capable(self) -> bool:
        """Check if agent is capable of handling emergencies."""
        return (self.medical_metadata.emergency_capable and 
                MedicalCapability.EMERGENCY_RESPONSE in self.capabilities)
    
    def get_availability_score(self) -> float:
        """Get agent availability score based on SLA requirements."""
        return self.sla_requirements.get("availability_percentage", 99.0) / 100.0


class MedicalCapabilityRegistry:
    """
    Registry for managing medical agent capabilities and discovery.
    
    Provides efficient capability-based agent discovery with medical
    specialty filtering and emergency response prioritization.
    """
    
    def __init__(self):
        """Initialize the medical capability registry."""
        
        self.registered_agents: Dict[str, VigiaAgentCard] = {}
        self.capability_index: Dict[MedicalCapability, Set[str]] = {}
        self.specialty_index: Dict[MedicalSpecialty, Set[str]] = {}
        self.emergency_agents: Set[str] = set()
        
        # Initialize capability index
        for capability in MedicalCapability:
            self.capability_index[capability] = set()
        
        # Initialize specialty index  
        for specialty in MedicalSpecialty:
            self.specialty_index[specialty] = set()
        
        logger.info("Medical Capability Registry initialized")
    
    def register_agent(self, agent_card: VigiaAgentCard) -> bool:
        """
        Register an agent in the capability registry.
        
        Args:
            agent_card: Agent card to register
            
        Returns:
            bool: True if registration successful
        """
        try:
            agent_id = agent_card.agent_id
            
            # Store agent card
            self.registered_agents[agent_id] = agent_card
            
            # Index by capabilities
            for capability in agent_card.capabilities:
                self.capability_index[capability].add(agent_id)
            
            # Index by medical specialties
            for specialty in agent_card.medical_metadata.medical_specialties:
                self.specialty_index[specialty].add(agent_id)
            
            # Track emergency-capable agents
            if agent_card.is_emergency_capable():
                self.emergency_agents.add(agent_id)
            
            logger.info(f"Registered agent {agent_id} with {len(agent_card.capabilities)} capabilities")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_card.agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the capability registry.
        
        Args:
            agent_id: Agent identifier to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if agent_id not in self.registered_agents:
                return False
            
            agent_card = self.registered_agents[agent_id]
            
            # Remove from capability index
            for capability in agent_card.capabilities:
                self.capability_index[capability].discard(agent_id)
            
            # Remove from specialty index
            for specialty in agent_card.medical_metadata.medical_specialties:
                self.specialty_index[specialty].discard(agent_id)
            
            # Remove from emergency agents
            self.emergency_agents.discard(agent_id)
            
            # Remove agent card
            del self.registered_agents[agent_id]
            
            logger.info(f"Unregistered agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def discover_agents_by_capability(
        self,
        capability: MedicalCapability,
        specialty: Optional[MedicalSpecialty] = None,
        emergency_only: bool = False
    ) -> List[VigiaAgentCard]:
        """
        Discover agents by medical capability.
        
        Args:
            capability: Required medical capability
            specialty: Optional medical specialty filter
            emergency_only: Only return emergency-capable agents
            
        Returns:
            List of matching agent cards
        """
        
        # Get agents with required capability
        candidate_agents = self.capability_index.get(capability, set()).copy()
        
        # Filter by specialty if specified
        if specialty:
            specialty_agents = self.specialty_index.get(specialty, set())
            candidate_agents = candidate_agents.intersection(specialty_agents)
        
        # Filter by emergency capability if specified
        if emergency_only:
            candidate_agents = candidate_agents.intersection(self.emergency_agents)
        
        # Return agent cards sorted by availability score
        agent_cards = [self.registered_agents[agent_id] for agent_id in candidate_agents]
        return sorted(agent_cards, key=lambda card: card.get_availability_score(), reverse=True)
    
    def discover_emergency_agents(
        self,
        capability: Optional[MedicalCapability] = None
    ) -> List[VigiaAgentCard]:
        """
        Discover emergency-capable agents.
        
        Args:
            capability: Optional capability filter
            
        Returns:
            List of emergency-capable agent cards
        """
        
        emergency_agents = self.emergency_agents.copy()
        
        # Filter by capability if specified
        if capability:
            capability_agents = self.capability_index.get(capability, set())
            emergency_agents = emergency_agents.intersection(capability_agents)
        
        # Return agent cards sorted by availability
        agent_cards = [self.registered_agents[agent_id] for agent_id in emergency_agents]
        return sorted(agent_cards, key=lambda card: card.get_availability_score(), reverse=True)
    
    def get_agent_card(self, agent_id: str) -> Optional[VigiaAgentCard]:
        """Get agent card by ID."""
        return self.registered_agents.get(agent_id)
    
    def get_all_agents(self) -> List[VigiaAgentCard]:
        """Get all registered agent cards."""
        return list(self.registered_agents.values())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        
        capability_counts = {
            cap.value: len(agents) 
            for cap, agents in self.capability_index.items() 
            if agents
        }
        
        specialty_counts = {
            spec.value: len(agents)
            for spec, agents in self.specialty_index.items()
            if agents
        }
        
        return {
            "total_agents": len(self.registered_agents),
            "emergency_agents": len(self.emergency_agents),
            "capability_distribution": capability_counts,
            "specialty_distribution": specialty_counts,
            "last_updated": datetime.now().isoformat()
        }
    
    def save_registry(self, file_path: Path) -> bool:
        """Save registry to file."""
        try:
            registry_data = {
                "agents": {
                    agent_id: card.to_dict() 
                    for agent_id, card in self.registered_agents.items()
                },
                "stats": self.get_registry_stats()
            }
            
            with open(file_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            logger.info(f"Saved registry to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            return False
    
    def load_registry(self, file_path: Path) -> bool:
        """Load registry from file."""
        try:
            with open(file_path, 'r') as f:
                registry_data = json.load(f)
            
            # Clear current registry
            self.__init__()
            
            # Load agents
            for agent_id, card_dict in registry_data.get("agents", {}).items():
                agent_card = VigiaAgentCard.from_dict(card_dict)
                self.register_agent(agent_card)
            
            logger.info(f"Loaded registry from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return False