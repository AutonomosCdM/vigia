# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Vigia is a production-ready medical-grade pressure injury (LPP) detection system using computer vision and local AI. It implements an ADK (Agent Development Kit) architecture for healthcare compliance (HIPAA, ISO 13485, SOC2) with WhatsApp/Slack integration and comprehensive audit trails.

## Essential Commands

### Testing & Validation
```bash
# Core test suites (organized by category)
python -m pytest tests/unit/ -m unit           # Unit tests
python -m pytest tests/adk/ -m adk             # ADK agent tests  
python -m pytest tests/medical/ -m medical     # Medical validation
python -m pytest tests/integration/ -m integration  # Integration tests

# Critical validation tests
python -m pytest tests/medical/test_minsal_integration.py -v    # Chilean compliance (14/14 PASSED)
python -m pytest tests/adk/test_adk_a2a_foundation.py -v       # ADK A2A communication (4/4 PASSED) 
python -m pytest tests/integration/test_async_pipeline_structure.py -v     # Async pipeline (5/5 PASSED)

# Medical cohort testing (120+ synthetic patients)
./scripts/testing/run_medical_tests.sh all         # Complete medical test suite
./scripts/testing/run_medical_tests.sh cohort      # 120+ patient cohort validation
./scripts/testing/run_infrastructure_tests.sh      # A2A and system infrastructure

# Skip slow tests during development
python -m pytest tests/ -m "not slow"

# Configuration: config/pytest.ini with 38 test markers, 300s timeout
```

### Service Management
```bash
# Hospital deployment (ready for production)
./scripts/deployment/hospital-deploy.sh deploy     # Complete hospital system with Docker secrets
./scripts/deployment/hospital-deploy.sh status     # Check all services and health
./scripts/deployment/hospital-deploy.sh logs       # View comprehensive logs

# Development services
./scripts/utilities/start_celery_worker.sh         # Medical priority async workers
./start_whatsapp_server.sh                         # WhatsApp webhook server
./scripts/utilities/start_slack_server.sh          # Slack medical notifications

# System validation
python scripts/validate_post_refactor_simple.py --verbose
redis-cli ping                                     # Redis connectivity check
```

### Medical AI & Processing
```bash
# MedGemma local AI setup (HIPAA-compliant)
python scripts/setup_medgemma_ollama.py --install-ollama
python scripts/setup_medgemma_ollama.py --model 27b --install
ollama run symptoma/medgemma3 "¿Cuáles son los grados de LPP?"

# Medical image processing
python vigia_detect/cli/process_images_refactored.py --input /path/to/images
python vigia_detect/cli/process_images_refactored.py --webhook --patient-code CD-2025-001

# Redis medical protocol setup
python scripts/setup_redis_simple.py
python examples/redis_integration_demo.py
```

### Environment & Configuration
```bash
# Environment setup (loads .env files from config/)
source scripts/quick_env_setup.sh

# Secure credential management
python scripts/setup/setup_credentials.py

# Docker deployment configurations
deploy/docker/docker-compose.hospital.yml     # Hospital production
deploy/docker/docker-compose.render.yml       # Cloud deployment
```

## Architecture Overview

### ADK Agent System
The system uses a clean ADK (Agent Development Kit) architecture with 5 specialized medical agents:
- **ImageAnalysisAgent** (`vigia_detect/agents/adk/image_analysis.py`): Native ADK BaseAgent with YOLOv5 integration for LPP detection
- **ClinicalAssessmentAgent** (`vigia_detect/agents/adk/clinical_assessment.py`): ADK LLMAgent with Gemini-1.5-Pro for evidence-based NPUAP/EPUAP decisions
- **ProtocolAgent** (`vigia_detect/agents/adk/protocol.py`): ADK LLMAgent for medical protocol consultation with vector search
- **CommunicationAgent** (`vigia_detect/agents/adk/communication.py`): ADK WorkflowAgent for WhatsApp/Slack notifications
- **WorkflowOrchestrationAgent** (`vigia_detect/agents/adk/workflow_orchestration.py`): ADK WorkflowAgent for medical workflow coordination

All agents inherit from **VigiaBaseAgent** (Google ADK BaseAgent) with native **AgentMessage**/**AgentResponse** patterns and **AgentCapability** enums.

### A2A Distributed Infrastructure
Agent-to-Agent communication via JSON-RPC 2.0 protocol (`vigia_detect/a2a/`):
- **adk/communication_protocol.py**: Native ADK A2A protocol with medical extensions and HIPAA compliance
- **adk/agent_cards.py**: ADK Agent Card implementation for medical agent discovery
- **agent_discovery_service.py**: Service registry with Redis/Consul/ZooKeeper backends
- **load_balancer.py**: 7 intelligent routing algorithms with health-aware medical priority
- **health_monitoring.py**: Real-time monitoring with 10 metric types and predictive alerts
- **message_queuing.py**: 6 queue types with guaranteed delivery and medical compliance
- **fault_tolerance.py**: Circuit breakers, emergency protocols, automatic recovery

### Medical Decision Engine
Evidence-based clinical decisions (`vigia_detect/systems/`):
- **medical_decision_engine.py**: NPUAP/EPUAP/PPPIA 2019 guidelines with scientific justification
- **minsal_medical_decision_engine.py**: Chilean Ministry of Health integration for regulatory compliance
- All decisions include evidence levels (A/B/C), scientific references, and automatic escalation protocols

### Asynchronous Medical Pipeline
Timeout-resistant medical workflows (`vigia_detect/core/async_pipeline.py`):
- **Celery-based processing**: 3-5 minute task limits vs 30-60 second blocking operations
- **Medical task queues**: medical_priority, image_processing, notifications, audit_logging
- **Retry policies**: Max 3 retries with human escalation for critical medical failures
- **Task modules**: `vigia_detect/tasks/` (medical.py, audit.py, notifications.py)

## Development Patterns

### Medical Decision Making
```python
# International evidence-based decisions
from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
engine = MedicalDecisionEngine()
decision = engine.make_clinical_decision(
    lpp_grade=2, confidence=0.85, anatomical_location="sacrum"
)

# Chilean regulatory compliance (MINSAL)
from vigia_detect.systems.minsal_medical_decision_engine import make_minsal_clinical_decision
decision = make_minsal_clinical_decision(
    lpp_grade=2, confidence=0.75,
    patient_context={'diabetes': True, 'public_healthcare': True}
)
```

### Asynchronous Medical Tasks
```python
# Async medical processing (prevents timeouts)
from vigia_detect.tasks.medical import image_analysis_task
result = image_analysis_task.delay(image_path, patient_code, patient_context)

# Medical protocol search with Redis vector storage
from vigia_detect.redis_layer.vector_service import VectorService
protocols = vector_service.search_protocols("LPP Grade 3 treatment")
```

### ADK Agent Communication
```python
# Native ADK Agent-to-Agent messaging
from vigia_detect.agents.adk.base import VigiaBaseAgent
from google.adk.agents import AgentMessage, AgentResponse

# Agent initialization
agent = VigiaBaseAgent(
    agent_id="clinical_agent",
    agent_name="Clinical Assessment Agent",
    capabilities=[AgentCapability.MEDICAL_DIAGNOSIS, AgentCapability.CLINICAL_REASONING]
)

# A2A communication
message = AgentMessage(
    message_id="msg_001",
    sender_id="clinical_agent",
    recipient_id="protocol_agent",
    message_type="protocol_query",
    content={"lpp_grade": 2, "location": "sacrum"}
)
```

### MedGemma ADK Integration
```python
# Native ADK Tool for medical reasoning
from vigia_detect.ai.medgemma_adk import MedGemmaADKTool, MedicalReasoningType

medgemma_tool = MedGemmaADKTool(
    model_type=MedGemmaModelType.MEDGEMMA_9B,
    deployment_mode="vertex"  # or "ollama" for local HIPAA-compliant processing
)

# Medical reasoning with evidence levels
result = await medgemma_tool.medical_reasoning(
    reasoning_type=MedicalReasoningType.CLINICAL_ASSESSMENT,
    patient_context={"age": 75, "diabetes": True, "mobility": "limited"},
    clinical_question="Assess pressure injury risk and recommend preventive measures"
)
```

## Medical Safety Requirements

### Evidence-Based Medicine
- All clinical logic must reference NPUAP/EPUAP/PPPIA 2019 guidelines
- Include scientific justification with evidence levels (A/B/C)
- Low-confidence decisions automatically escalate to human review
- Complete audit trails required for regulatory compliance

### Local AI Processing
- **MedGemma ADK integration** (`vigia_detect/ai/medgemma_adk.py`): Native ADK Tool with dual deployment (Vertex AI + Ollama)
- HIPAA-compliant medical AI without external dependencies for sensitive data
- Medical protocol caching with Redis vector search (`vigia_detect/redis_layer/vector_service.py`)
- Synthetic patient testing with 120+ patient cohort required before production
- Evidence-based medical reasoning with A/B/C evidence level classification

## Architecture Rules

### Clean Architecture Principles
- **Native ADK implementation**: No wrappers, all agents inherit directly from Google ADK (BaseAgent, LLMAgent, WorkflowAgent)
- **Single implementations only**: No _v2, _refactored, _adk file duplicates
- **Professional test organization**: 50+ test files with 14,340+ lines categorized in tests/unit/, tests/adk/, tests/medical/, tests/integration/
- **Evidence-based decisions**: 100% preservation of medical decision logic with scientific justification
- **A2A protocol compliance**: Native Agent Card discovery and JSON-RPC 2.0 medical extensions

### Directory Structure (Native ADK Architecture)
```
vigia/
├── vigia_detect/          # Core medical system
│   ├── agents/adk/       # 5 native ADK medical agents (BaseAgent, LLMAgent, WorkflowAgent)
│   ├── systems/          # Evidence-based decision engines (NPUAP/EPUAP/MINSAL)
│   ├── a2a/adk/         # Native ADK A2A protocol with Agent Cards
│   ├── core/            # Async pipeline orchestrator
│   ├── ai/              # MedGemma ADK Tool integration
│   └── tasks/           # Celery async medical tasks
├── config/               # Centralized configuration (.env, requirements, pytest.ini)
├── deploy/               # Docker deployment configurations
│   └── docker/          # Hospital production deployment
├── docs/                 # Essential documentation (medical, deployment, setup)
├── tests/                # 50+ test files with 14,340+ lines (unit, adk, medical, integration)
├── dev/                  # Development files (demos, evaluations, renders)
└── scripts/              # 50+ utility scripts organized by category
    ├── deployment/      # Hospital and cloud deployment scripts
    ├── testing/         # Medical cohort and infrastructure testing
    ├── setup/           # Environment and credential setup
    └── utilities/       # Service management and validation
```

## Production Status
✅ **Production-Ready ADK Implementation** - v1.4.0 Native Architecture:
- **Google ADK Hackathon Ready**: 5 native ADK agents with complete A2A protocol and Agent Cards
- **Medical AI Excellence**: Evidence-based decision engine with NPUAP/EPUAP/MINSAL compliance
- **Comprehensive Testing**: 50+ test files with 14,340+ lines across unit/adk/medical/integration categories
- **Real Medical Validation**: 2,088+ validated images across 5 datasets with evidence-based decisions
- **Privacy-First Architecture**: Local MedGemma processing via Ollama, comprehensive audit trails
- **Deployment-Ready**: Complete infrastructure for hospital environments with secure medical workflows