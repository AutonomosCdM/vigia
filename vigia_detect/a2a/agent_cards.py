"""
A2A Agent Cards for Vigia Medical System
========================================

Defines Agent Cards for all medical agents in the Vigia system.
Agent Cards provide capability discovery and communication endpoints
for distributed A2A medical processing.
"""

from vigia_detect.a2a.base_infrastructure import AgentCard

# Agent Cards for all Vigia medical agents
VIGIA_MEDICAL_AGENT_CARDS = {
    
    "master_medical_orchestrator": AgentCard(
        agent_id="master_medical_orchestrator",
        name="Master Medical Orchestrator",
        description="Central orchestrator for coordinating all medical agents in LPP detection and management workflow",
        version="1.0.0",
        capabilities=[
            "medical_case_orchestration",
            "agent_coordination", 
            "medical_workflow_management",
            "compliance_enforcement",
            "escalation_management",
            "audit_trail_generation"
        ],
        endpoints={
            "base_url": "http://localhost:8080",
            "agent_card": "/agent-card",
            "tasks": "/tasks",
            "health": "/health",
            "status": "/status"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key",
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "streaming"],
        medical_specialization="medical_workflow_orchestration",
        compliance_certifications=["HIPAA", "MINSAL", "ISO_13485"]
    ),
    
    "image_analysis_agent": AgentCard(
        agent_id="image_analysis_agent", 
        name="Medical Image Analysis Agent",
        description="Specialized agent for computer vision analysis of medical images using YOLOv5 for LPP detection",
        version="1.0.0",
        capabilities=[
            "medical_image_preprocessing",
            "lpp_detection_yolov5",
            "image_quality_assessment",
            "anatomical_location_detection",
            "confidence_scoring",
            "medical_image_anonymization"
        ],
        endpoints={
            "base_url": "http://localhost:8081",
            "agent_card": "/agent-card", 
            "tasks": "/tasks",
            "analyze_image": "/analyze-image",
            "preprocess": "/preprocess",
            "health": "/health"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key",
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "streaming"],
        medical_specialization="medical_imaging_cv",
        compliance_certifications=["HIPAA", "DICOM", "FDA_510K"]
    ),
    
    "clinical_assessment_agent": AgentCard(
        agent_id="clinical_assessment_agent",
        name="Clinical Assessment Agent", 
        description="Evidence-based clinical decision engine for LPP grading and medical recommendations",
        version="1.0.0",
        capabilities=[
            "evidence_based_decision_making",
            "lpp_grading_npuap_epuap",
            "clinical_risk_assessment",
            "medical_recommendation_generation",
            "patient_context_analysis",
            "escalation_determination",
            "medical_documentation"
        ],
        endpoints={
            "base_url": "http://localhost:8082",
            "agent_card": "/agent-card",
            "tasks": "/tasks", 
            "assess": "/clinical-assessment",
            "grade_lpp": "/grade-lpp",
            "risk_score": "/risk-assessment",
            "health": "/health"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key",
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "streaming"],
        medical_specialization="clinical_decision_support",
        compliance_certifications=["HIPAA", "MINSAL", "NPUAP_EPUAP_2019"]
    ),
    
    "protocol_agent": AgentCard(
        agent_id="protocol_agent",
        name="Medical Protocol Agent",
        description="Medical knowledge base agent for NPUAP/EPUAP protocols and clinical guidelines",
        version="1.0.0", 
        capabilities=[
            "medical_protocol_lookup",
            "npuap_epuap_guidelines",
            "minsal_chilean_protocols",
            "evidence_retrieval",
            "clinical_guideline_application",
            "protocol_recommendation",
            "medical_knowledge_search"
        ],
        endpoints={
            "base_url": "http://localhost:8083",
            "agent_card": "/agent-card",
            "tasks": "/tasks",
            "lookup_protocol": "/protocol-lookup", 
            "search_guidelines": "/search-guidelines",
            "get_recommendations": "/recommendations",
            "health": "/health"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key", 
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "streaming"],
        medical_specialization="medical_knowledge_protocols",
        compliance_certifications=["NPUAP_EPUAP_2019", "MINSAL", "WHO_GUIDELINES"]
    ),
    
    "communication_agent": AgentCard(
        agent_id="communication_agent",
        name="Medical Communication Agent",
        description="Handles medical team notifications via WhatsApp and Slack with appropriate urgency levels",
        version="1.0.0",
        capabilities=[
            "medical_team_notification",
            "slack_integration",
            "whatsapp_integration", 
            "urgency_based_routing",
            "notification_templating",
            "escalation_notifications",
            "audit_trail_communication"
        ],
        endpoints={
            "base_url": "http://localhost:8084",
            "agent_card": "/agent-card",
            "tasks": "/tasks",
            "send_notification": "/send-notification",
            "send_slack": "/slack-notification",
            "send_whatsapp": "/whatsapp-notification", 
            "health": "/health"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key",
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "push_notifications"],
        medical_specialization="medical_communication",
        compliance_certifications=["HIPAA", "GDPR", "MEDICAL_PRIVACY"]
    ),
    
    "workflow_orchestration_agent": AgentCard(
        agent_id="workflow_orchestration_agent",
        name="Workflow Orchestration Agent",
        description="Manages async medical workflows with Celery integration and timeout prevention",
        version="1.0.0",
        capabilities=[
            "async_workflow_management",
            "celery_task_orchestration",
            "timeout_prevention",
            "medical_pipeline_coordination",
            "retry_policy_management",
            "failure_escalation",
            "workflow_monitoring"
        ],
        endpoints={
            "base_url": "http://localhost:8085",
            "agent_card": "/agent-card",
            "tasks": "/tasks",
            "start_workflow": "/start-workflow",
            "monitor_pipeline": "/monitor-pipeline",
            "retry_task": "/retry-task",
            "health": "/health"
        },
        authentication={
            "methods": ["api_key", "jwt"],
            "api_key_header": "X-API-Key",
            "jwt_header": "Authorization"
        },
        supported_modes=["request_response", "streaming", "push_notifications"],
        medical_specialization="workflow_orchestration",
        compliance_certifications=["HIPAA", "ASYNC_MEDICAL_SAFETY"]
    )
}

# JSON representation of agent cards for external discovery
AGENT_CARDS_JSON = {
    agent_id: card.to_dict() 
    for agent_id, card in VIGIA_MEDICAL_AGENT_CARDS.items()
}

def get_agent_card(agent_id: str) -> AgentCard:
    """
    Get agent card by ID.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        AgentCard object
        
    Raises:
        KeyError: If agent not found
    """
    if agent_id not in VIGIA_MEDICAL_AGENT_CARDS:
        raise KeyError(f"Agent card not found for ID: {agent_id}")
    
    return VIGIA_MEDICAL_AGENT_CARDS[agent_id]

def get_all_agent_cards() -> dict:
    """
    Get all agent cards as dictionary.
    
    Returns:
        Dictionary of agent_id -> AgentCard
    """
    return VIGIA_MEDICAL_AGENT_CARDS.copy()

def get_agent_cards_json() -> dict:
    """
    Get all agent cards in JSON format for API responses.
    
    Returns:
        Dictionary with JSON representations
    """
    return AGENT_CARDS_JSON.copy()

def get_agents_by_capability(capability: str) -> list:
    """
    Get agents that support specific capability.
    
    Args:
        capability: Capability to search for
        
    Returns:
        List of agent IDs that support the capability
    """
    matching_agents = []
    
    for agent_id, card in VIGIA_MEDICAL_AGENT_CARDS.items():
        if capability in card.capabilities:
            matching_agents.append(agent_id)
    
    return matching_agents

def get_medical_specialists() -> dict:
    """
    Get agents grouped by medical specialization.
    
    Returns:
        Dictionary of specialization -> list of agent IDs
    """
    specialists = {}
    
    for agent_id, card in VIGIA_MEDICAL_AGENT_CARDS.items():
        specialization = card.medical_specialization
        if specialization:
            if specialization not in specialists:
                specialists[specialization] = []
            specialists[specialization].append(agent_id)
    
    return specialists

# Export main functions and data
__all__ = [
    'VIGIA_MEDICAL_AGENT_CARDS',
    'AGENT_CARDS_JSON', 
    'get_agent_card',
    'get_all_agent_cards',
    'get_agent_cards_json',
    'get_agents_by_capability',
    'get_medical_specialists'
]