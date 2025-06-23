# CLAUDE.md

## Project Overview
Vigia is a medical-grade pressure injury (LPP) detection system using computer vision and AI. The system implements a secure 3-layer architecture for healthcare compliance (HIPAA, ISO 13485, SOC2) with messaging integration and comprehensive audit capabilities.

## Architecture Overview

### Phase-Based Development Structure
- **FASE 1**: `fase1/` - Patient reception with dual database architecture (COMPLETED)
- **FASE 2**: `vigia_detect/` - Multimodal medical processing with voice + image analysis (COMPLETED)  
- **FASE 3**: `vigia_detect/a2a/` - Distributed infrastructure for agent communication (READY)

### 3-Layer Security Architecture
**Layer 1 - Input Isolation**: WhatsApp bot with no medical data access
**Layer 2 - Medical Orchestration**: Triage engine and medical routing
**Layer 3 - Specialized Medical Systems**: LPP detection and clinical processing

### Dual Database Architecture
**Hospital PHI Database**: Contains real patient data (Bruce Wayne) - internal only
**Processing Database**: Contains ONLY tokenized data (Batman) - external access
**PHI Tokenization Service**: Secure Bruce Wayne → Batman conversion with JWT auth

## Commands & Modes

### Planning & YOLO Modes
```bash
/plan [topic]    # Enter planning mode without code execution
/yolo [task]     # Execute task immediately without confirmations
```

### Essential Commands
```bash
# Testing
./scripts/run_tests.sh                         # Run all tests
python -m pytest tests/ -m "medical"           # Medical validation tests  
python test_async_simple.py                    # Async pipeline validation

# System Operations  
./scripts/hospital-deploy.sh deploy            # Deploy hospital system
./start_whatsapp_server.sh                     # Start WhatsApp server
python vigia_detect/cli/process_images_refactored.py --input /path/to/images

# Code Quality
./scripts/run_security_analysis.sh             # Security analysis
python -m pylint vigia_detect/                 # Python linting

# MedGemma AI Setup
python scripts/setup_medgemma_ollama.py --install-ollama   # Install Ollama (recommended)
python scripts/setup_medgemma_local.py --check-only        # Hugging Face setup
```

## Development Context

### Core Architecture
- **CV Pipeline** (`vigia_detect/cv_pipeline/`): MONAI primary + YOLOv5 backup detection
- **Communication Agents** (`vigia_detect/agents/`): WhatsApp + Slack bidirectional messaging
- **Database** (`vigia_detect/db/`): Supabase with PHI tokenization  
- **AI Module** (`vigia_detect/ai/`): MedGemma local + Hume AI voice analysis
- **Medical Systems** (`vigia_detect/systems/`): Evidence-based decision engine
- **Async Pipeline** (`vigia_detect/core/async_pipeline.py`): Celery orchestrator

### Medical Workflow
1. **Input**: WhatsApp receives patient images/messages
2. **Triage**: Engine assesses urgency and routes appropriately  
3. **Analysis**: MONAI/YOLOv5 performs LPP detection and grading
4. **Notification**: Slack delivers results to medical teams
5. **Review**: Medical professionals approve patient communications
6. **Response**: Approved messages sent back to patients
7. **Audit**: Complete traceability for compliance

### Key Technologies
- **AI**: MedGemma Local (HIPAA-compliant), MONAI medical detection
- **Data**: Dual database (Hospital PHI + Processing Batman tokens)
- **Security**: Fernet encryption, granular permissions, audit trails
- **Integration**: Twilio (WhatsApp), Slack API, Redis (protocols)

### Current Status (Production Ready)
**✅ HIPAA COMPLIANT** - 100% PHI tokenization with Batman token system  
**✅ MULTIMODAL AI** - MONAI primary + YOLOv5 backup + voice analysis  
**✅ BIDIRECTIONAL COMMUNICATION** - WhatsApp patients ↔ Slack medical teams  
**✅ COMPREHENSIVE TRACEABILITY** - Complete decision audit trails for regulatory compliance

## Development Guidelines

### Mode Instructions
- **Planning Mode** (`/plan`): NO code execution, focus on design and strategy
- **YOLO Mode** (`/yolo`): Execute immediately without confirmations

### Medical Development Standards
- **PHI Tokenization MANDATORY**: Use Batman tokens (token_id) instead of PHI (patient_code)
- **Evidence-Based Decisions**: Reference NPUAP/EPUAP/PPPIA guidelines
- **Safety First**: Low confidence medical decisions escalate to human review  
- **Audit Trail**: All medical decisions fully traceable for compliance
- **Async by Default**: Use async pipeline to prevent timeouts
- **Privacy Compliance**: Prefer local processing (MedGemma) over external APIs

### Common Development Patterns
```python
# PHI Tokenization (CRITICAL)
from fase1.phi_tokenization.client.tokenization_client import PHITokenizationClient
tokenizer = PHITokenizationClient()
batman_token = await tokenizer.create_token_async(hospital_mrn, patient_data)

# Adaptive Medical Detection (MONAI + YOLOv5)
from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector
detector = create_medical_detector()
assessment = await detector.detect_medical_condition(image_path, token_id, patient_context)

# Async Medical Tasks
from vigia_detect.tasks.medical import image_analysis_task
result = image_analysis_task.delay(image_path, token_id, patient_context)

# Communication Agents
from vigia_detect.agents.patient_communication_agent import PatientCommunicationAgentFactory
from vigia_detect.agents.medical_team_agent import MedicalTeamAgentFactory
patient_agent = PatientCommunicationAgentFactory.create_agent()
medical_agent = MedicalTeamAgentFactory.create_agent()
```

### Project Structure
- **FASE 1**: `fase1/` - Patient reception, PHI tokenization, dual database
- **Medical Logic**: `vigia_detect/systems/` and `vigia_detect/agents/`
- **CV Pipeline**: `vigia_detect/cv_pipeline/` - MONAI + YOLOv5 detection
- **AI Integration**: `vigia_detect/ai/` - MedGemma + Hume AI
- **A2A Infrastructure**: `vigia_detect/a2a/` - Distributed agent communication
- **Async Tasks**: `vigia_detect/tasks/` - Celery medical pipeline
- **Testing**: `tests/medical/`, `test_adk_a2a_foundation.py`, `test_fase3_simple_mock.py`
- **Hospital Deploy**: `scripts/hospital-deploy.sh`, `docker-compose.hospital.yml`


# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.