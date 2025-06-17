# CLAUDE.md

Guides Claude Code when working with this medical AI system.

## Project Overview
Vigia: Medical-grade pressure injury detection system with ADK architecture for healthcare compliance (HIPAA, ISO 13485, SOC2).

## Core Architecture
**ADK Medical Agents**
- Image analysis, clinical assessment, protocols, communication, workflow orchestration
- Master orchestrator with A2A communication
- Distributed infrastructure (protocol, discovery, load balancing, monitoring)

**Key Systems**
- Async medical pipeline with timeout prevention
- Evidence-based decision engine (NPUAP/EPUAP + MINSAL)
- Medical AI (MedGemma local) with HIPAA compliance

## Commands & Modes

### Planning Mode
```bash
/plan [topic]    # Design and architecture without code execution
```

### YOLO Mode  
```bash
/yolo [task]     # Execute immediately without confirmations
```

## Essential Commands

### Testing
```bash
# Core test suites
python -m pytest tests/unit/ -m unit           # Unit tests
python -m pytest tests/adk/ -m adk             # ADK agent tests
python -m pytest tests/medical/ -m medical     # Medical validation
python -m pytest tests/integration/ -m integration  # Integration tests

# Key test files
python -m pytest tests/medical/test_minsal_integration.py -v    # Chilean compliance (14/14 PASSED)
python -m pytest tests/adk/test_simple_adk_integration.py -v    # ADK integration (4/4 PASSED)
python -m pytest tests/integration/test_async_simple.py -v     # Async pipeline (5/5 PASSED)
```

### Services
```bash
# Start core services
./scripts/hospital-deploy.sh deploy           # Hospital system
./scripts/start_celery_worker.sh               # Async workers
./start_whatsapp_server.sh                    # WhatsApp server

# System validation
python scripts/validate_post_refactor_simple.py --verbose
redis-cli ping                                # Redis connectivity
```

### Development
```bash
# Environment setup
source scripts/quick_env_setup.sh

# Image processing
python vigia_detect/cli/process_images_refactored.py --input /path/to/images

# Medical AI (local)
python scripts/setup_medgemma_ollama.py --model 27b --install
```

### Medical AI & Evaluation
```bash
# MedGemma setup (local AI)
python scripts/setup_medgemma_ollama.py --model 27b --install
ollama run symptoma/medgemma3 "¿Cuáles son los grados de LPP?"

# MedHELM evaluation
python evaluate_medhelm.py --quick --visualize
python test_medhelm_basic.py

# Medical datasets (2,088+ real images)
cd datasets/medical_images && python create_azh_yolo_dataset.py
python quick_train_lpp.py
```

## System Architecture

### Core Components
- **ADK Agents** (`vigia_detect/agents/`): 5 specialized medical agents with A2A communication
- **Medical Systems** (`vigia_detect/systems/`): Evidence-based decision engines (NPUAP/EPUAP + MINSAL)
- **AI Module** (`vigia_detect/ai/`): MedGemma local HIPAA-compliant processing
- **Async Pipeline** (`vigia_detect/core/async_pipeline.py`): Timeout-resistant medical workflows
- **A2A Infrastructure** (`vigia_detect/a2a/`): Distributed JSON-RPC 2.0 communication

### Medical Workflow
1. WhatsApp/Slack input → Medical triage → Clinical analysis → Human escalation → Team notification → Audit trail

### Compliance & Security
- HIPAA/ISO 13485/SOC2 ready
- Medical data encryption, audit trails, temporal isolation
- Evidence-based decisions with scientific justification
- Local AI processing (MedGemma) for privacy

## Project Status (v1.3.3 - Production Ready)
**✅ HOSPITAL PRODUCTION READY** - Clean ADK architecture with comprehensive medical compliance:

**Key Achievements:**
- Clean ADK-only architecture (5 specialized medical agents)
- Professional test structure (50+ organized test files)
- FASE 3 distributed infrastructure (A2A JSON-RPC 2.0)
- Real medical detection (2,088+ images, 5 datasets)
- Evidence-based decisions (NPUAP/EPUAP + MINSAL)
- Async medical pipeline (Celery, timeout prevention)
- Hospital infrastructure (Docker, HIPAA compliance)
- Local medical AI (MedGemma, privacy-first)

**Validation:**
- ✅ 4/4 ADK tests, 7/7 infrastructure tests, 14/14 MINSAL tests
- ✅ 100% medical test coverage with synthetic patients
- ✅ HIPAA/ISO 13485/SOC2 compliance ready

## Development Guidelines

### Medical Safety Requirements
- Evidence-based decisions with NPUAP/EPUAP/MINSAL references
- Scientific justification for all clinical recommendations
- Human escalation for low-confidence decisions
- Complete audit trails for compliance
- Local processing preferred (MedGemma)
- Synthetic patient testing required

## Development Patterns

```python
# Medical decision with evidence
from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
engine = MedicalDecisionEngine()
decision = engine.make_clinical_decision(lpp_grade=2, confidence=0.85)

# MINSAL integration (Chilean context)
from vigia_detect.systems.minsal_medical_decision_engine import make_minsal_clinical_decision
decision = make_minsal_clinical_decision(lpp_grade=2, confidence=0.75,
                                       patient_context={'diabetes': True})

# Async medical task
from vigia_detect.tasks.medical import image_analysis_task
result = image_analysis_task.delay(image_path, patient_code)
```

## Key Directories
- **ADK Agents**: `vigia_detect/agents/` (5 specialized agents)
- **Medical Systems**: `vigia_detect/systems/` (decision engines)
- **Tests**: `tests/unit/`, `tests/adk/`, `tests/medical/` (organized structure)
- **Infrastructure**: `vigia_detect/a2a/` (distributed communication)
- **Datasets**: `datasets/medical_images/` (2,088+ real images)

## Architecture Rules
- Single implementations only (no _v2, _adk duplicates)
- ADK framework for all medical agents
- Evidence-based medical decisions
- Async pipeline for timeout prevention
- Local AI processing (MedGemma)
- Professional test organization