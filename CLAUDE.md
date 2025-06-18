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
python -m pytest tests/adk/test_simple_adk_integration.py -v    # ADK integration (4/4 PASSED) 
python -m pytest tests/integration/test_async_simple.py -v     # Async pipeline (5/5 PASSED)

# Skip slow tests during development
python -m pytest tests/ -m "not slow"

# Configuration: config/pytest.ini with 38 test markers, 300s timeout
```

### Service Management
```bash
# Hospital deployment (production)
./scripts/hospital-deploy.sh deploy           # Full hospital system
./scripts/hospital-deploy.sh status           # Check services
./scripts/hospital-deploy.sh logs             # View logs

# Development services
./scripts/start_celery_worker.sh               # Async medical workers
./start_whatsapp_server.sh                    # WhatsApp webhook server
./scripts/start_slack_server.sh               # Slack notification server

# System validation
python scripts/validate_post_refactor_simple.py --verbose
redis-cli ping                                # Redis connectivity check
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
python scripts/setup_credentials.py

# Docker deployment configurations
deploy/docker/docker-compose.hospital.yml     # Hospital production
deploy/docker/docker-compose.render.yml       # Cloud deployment
```

## Architecture Overview

### ADK Agent System
The system uses a clean ADK (Agent Development Kit) architecture with 5 specialized medical agents:
- **ImageAnalysisAgent** (`vigia_detect/agents/image_analysis_agent.py`): YOLOv5 integration for LPP detection
- **ClinicalAssessmentAgent** (`vigia_detect/agents/clinical_assessment_agent.py`): Evidence-based NPUAP/EPUAP decisions
- **ProtocolAgent** (`vigia_detect/agents/protocol_agent.py`): Medical protocol consultation with vector search
- **CommunicationAgent** (`vigia_detect/agents/communication_agent.py`): WhatsApp/Slack notifications
- **WorkflowOrchestrationAgent** (`vigia_detect/agents/workflow_orchestration_agent.py`): Medical workflow coordination

All agents inherit from **BaseAgent** with standardized **AgentMessage**/**AgentResponse** patterns and **AgentCapability** enums.

### A2A Distributed Infrastructure
Agent-to-Agent communication via JSON-RPC 2.0 protocol (`vigia_detect/a2a/`):
- **protocol_layer.py**: JSON-RPC 2.0 with medical extensions and encryption
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
# Agent-to-Agent messaging
from vigia_detect.agents.base_agent import AgentMessage, AgentResponse
message = AgentMessage(
    message_id="msg_001",
    sender_id="clinical_agent",
    recipient_id="protocol_agent",
    message_type="protocol_query",
    content={"lpp_grade": 2, "location": "sacrum"}
)
```

## Medical Safety Requirements

### Evidence-Based Medicine
- All clinical logic must reference NPUAP/EPUAP/PPPIA 2019 guidelines
- Include scientific justification with evidence levels (A/B/C)
- Low-confidence decisions automatically escalate to human review
- Complete audit trails required for regulatory compliance

### Local AI Processing
- Prefer MedGemma local processing over external APIs for medical data
- HIPAA-compliant medical AI without external dependencies
- Medical protocol caching with Redis vector search
- Synthetic patient testing required before production

## Architecture Rules

### Clean Architecture Principles
- **Single implementations only**: No _v2, _refactored, _adk file duplicates
- **ADK framework exclusive**: All medical agents use Google ADK with proper tool definitions
- **Professional test organization**: 50+ test files categorized in tests/unit/, tests/adk/, tests/medical/
- **Evidence-based decisions**: 100% preservation of medical decision logic through refactoring

### Directory Structure (Post-Organization)
```
vigia/
├── vigia_detect/          # Core medical system
│   ├── agents/           # 5 ADK medical agents
│   ├── systems/          # Evidence-based decision engines
│   ├── a2a/             # Distributed infrastructure
│   ├── core/            # Async pipeline orchestrator
│   ├── ai/              # MedGemma local client
│   └── tasks/           # Celery async tasks
├── config/               # Centralized configuration (.env, requirements, pytest.ini)
├── deploy/               # Docker deployment (hospital, render)
├── docs/                 # Essential documentation (medical, deployment, setup)
├── tests/                # Organized test structure (unit, adk, medical, integration)
├── dev/                  # Development files (demos, evaluations, renders)
└── scripts/              # Utility scripts (50+ medical operations)
```

## Production Status
✅ **Hospital Production Ready** - v1.3.3 Clean Architecture:
- 4/4 ADK tests, 7/7 infrastructure tests, 14/14 MINSAL tests
- Real medical detection with 2,088+ validated images across 5 datasets
- HIPAA/ISO 13485/SOC2 compliance ready
- Evidence-based decisions with complete scientific justification
- Local medical AI processing with MedGemma (privacy-first)