# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Vigia is a medical-grade pressure injury (LPP - Lesiones Por Presión) detection system using computer vision and AI. The system implements a secure 3-layer architecture for healthcare compliance (HIPAA, ISO 13485, SOC2) with messaging integration (WhatsApp, Slack) and comprehensive audit capabilities.

## Architecture Overview

### 🏗️ 3-Layer Security Architecture
The system implements strict separation of concerns across three layers:

**Layer 1 - Input Isolation (Zero Medical Knowledge)**
- `vigia_detect/messaging/whatsapp/isolated_bot.py` - WhatsApp Bot with no medical data access
- `vigia_detect/core/input_packager.py` - Standardizes inputs without medical analysis  
- `vigia_detect/core/input_queue.py` - Encrypted temporal storage with session tokens

**Layer 2 - Medical Orchestration**
- `vigia_detect/core/medical_dispatcher.py` - Routes based on medical content and urgency
- `vigia_detect/core/triage_engine.py` - Applies medical rules for clinical urgency assessment
- `vigia_detect/core/session_manager.py` - Manages temporal isolation with 15-minute timeouts

**Layer 3 - Specialized Medical Systems**
- `vigia_detect/systems/clinical_processing.py` - LPP detection and medical analysis
- `vigia_detect/systems/medical_knowledge.py` - Medical protocols and knowledge base
- `vigia_detect/systems/human_review_queue.py` - Human escalation with priority queues

**Cross-Cutting Services**
- `vigia_detect/utils/audit_service.py` - Complete audit trail with 7-year retention
- `vigia_detect/interfaces/slack_orchestrator.py` - Medical team notifications
- `vigia_detect/utils/access_control_matrix.py` - Granular permissions by layer and role

## Commands & Modes

### 📋 Planning Mode
```bash
# Use /plan to enter planning mode for brainstorming and ideation
/plan [topic]    # Enter planning mode without code execution
                 # Focus on: design, architecture, research, strategy, brainstorming
                 # Prevents jumping directly to implementation
                 # Ideal for: new features, refactoring, system design, project planning
```

### Testing
```bash
# Run all tests with standardized runner
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh e2e          # End-to-end tests
./scripts/run_tests.sh unit         # Unit tests only  
./scripts/run_tests.sh security     # Security tests
./scripts/run_tests.sh medical      # Medical/clinical tests
./scripts/run_tests.sh quick        # Smoke tests + basic validation

# Direct pytest (with markers)
python -m pytest tests/ -m "unit"           # Unit tests
python -m pytest tests/ -m "not slow"       # Skip slow tests
python -m pytest tests/e2e/ -v              # E2E with verbose output

# Coverage (webhook module)
cd vigia_detect/webhook && python -m pytest --cov=vigia_detect.webhook --cov-report=html
```

### Linting and Code Quality
```bash
# Security analysis
./scripts/run_security_analysis.sh

# Python linting (via pylint in requirements.txt)
python -m pylint vigia_detect/

# Run validation script
python scripts/validate_post_refactor_simple.py --verbose
```

### System Operations
```bash
# Start services
./start_whatsapp_server.sh                    # WhatsApp webhook server
./scripts/start_slack_server.sh               # Slack notification server

# Environment setup
source scripts/quick_env_setup.sh             # Load environment variables
python scripts/setup_credentials.py           # Initial credential setup

# Image processing
python vigia_detect/cli/process_images_refactored.py --input /path/to/images
python vigia_detect/cli/process_images_refactored.py --webhook --patient-code CD-2025-001

# Redis operations
python scripts/test_redis_connection.py       # Test Redis connectivity  
python scripts/setup_redis_simple.py          # Setup Redis with medical protocols and cache
python examples/redis_integration_demo.py     # Demo Redis + MedGemma integration

# MedGemma AI Setup (Local)

## Opción 1: Ollama (Recomendado - Sin autenticación)
python scripts/setup_medgemma_ollama.py --install-ollama   # Install Ollama
python scripts/setup_medgemma_ollama.py --list             # List available models
python scripts/setup_medgemma_ollama.py --model 27b --install  # Install 27B model
python scripts/setup_medgemma_ollama.py --model 27b --test # Test model
ollama run symptoma/medgemma3 "¿Cuáles son los grados de LPP?"  # Direct usage

## Opción 2: Hugging Face (Requiere autenticación)
python scripts/setup_medgemma_local.py --check-only        # Check requirements
python scripts/setup_medgemma_local.py --install-deps      # Install dependencies
python scripts/setup_medgemma_local.py --model 4b --download  # Download 4B model
python scripts/setup_medgemma_local.py --model 4b --test   # Test model installation
python examples/medgemma_local_demo.py                     # Run complete demo
```

## Development Context

### Core Modules
- **CV Pipeline** (`vigia_detect/cv_pipeline/`): YOLOv5-based lesion detection with medical-grade preprocessing
- **Messaging** (`vigia_detect/messaging/`): WhatsApp/Slack integration with template system
- **Database** (`vigia_detect/db/`): Supabase client with row-level security policies
- **Redis Layer** (`vigia_detect/redis_layer/`): Medical protocol caching and vector search
- **Webhook System** (`vigia_detect/webhook/`): FastAPI-based external integrations
- **AI Module** (`vigia_detect/ai/`): MedGemma local client for medical analysis with full privacy

### Security & Compliance
- **Medical data encryption** at rest using Fernet symmetric encryption
- **Session-based temporal isolation** prevents data persistence beyond medical need
- **Complete audit trail** for regulatory compliance (HIPAA/SOC2/ISO 13485)
- **Least privilege access** with granular permissions matrix
- **Human-in-the-loop** escalation for ambiguous medical cases

### External Services
- **MedGemma Local** for medical analysis and natural language processing (fully local, HIPAA-compliant)
- **Anthropic Claude** for medical analysis and natural language processing (optional API-based)
- **Supabase** for persistent medical data storage (shared with autonomos-agent project)
- **Twilio** for WhatsApp messaging integration
- **Slack API** for medical team notifications  
- **Redis** for medical protocol caching and vector embeddings

### Testing Architecture
- **Comprehensive mocking** of external services (Twilio, Slack, Supabase)
- **Medical data safety** using synthetic patient data in tests
- **Async test support** in webhook module with VCR for HTTP recording
- **Test categorization** with markers: unit, integration, e2e, medical, security, smoke
- **Coverage reporting** enabled for webhook module

### Medical Workflow
The system handles the complete medical workflow from input to clinical decision:
1. **Input Reception**: WhatsApp Bot receives images/messages from healthcare staff
2. **Medical Triage**: Triage Engine assesses clinical urgency and routes appropriately  
3. **Clinical Analysis**: Specialized systems perform LPP detection and grading
4. **Human Escalation**: Complex cases route to qualified medical personnel
5. **Team Notification**: Slack Orchestrator delivers results to appropriate medical teams
6. **Audit & Compliance**: All actions logged for medical-legal traceability

### Key Configuration
- Environment variables managed through `.env` files with secure credential handling
- Medical protocols stored in Redis with vector search capabilities
- Session timeouts enforced at 15 minutes for temporal data isolation
- Multi-language support (Spanish/English) for medical notifications

### AI Integration Architecture
The system integrates multiple AI approaches for medical analysis:

**MedGemma Local (Recommended)**
- `vigia_detect/ai/medgemma_local_client.py` - Complete local MedGemma implementation
- Models: 4B multimodal (text+image) and 27B text-only
- Features: Quantization, caching, multimodal support, medical context integration
- Benefits: Full privacy, no API costs, HIPAA-compliant, predictable latency
- Setup: Use `scripts/setup_medgemma_local.py` for automated configuration

**External AI APIs (Fallback)**
- Anthropic Claude for complex medical reasoning when local AI insufficient
- Used only when MedGemma local cannot provide adequate analysis
- Requires careful privacy and compliance consideration

### Data Architecture
**Redis vs Supabase Usage**
- **Redis**: Medical protocol cache, vector embeddings, session data (temporal)
- **Supabase**: Permanent medical records, audit trails, user management (persistent)
- **Local Storage**: AI model cache, temporary image processing

### Recent Architecture Implementation
The system recently implemented a complete 3-layer security architecture to meet medical compliance requirements. All new development should follow the layered access patterns and maintain strict separation between input processing, medical orchestration, and specialized clinical systems.

The MedGemma local integration represents a major shift toward fully private medical AI processing, eliminating external API dependencies for core medical analysis while maintaining professional-grade capabilities.

## Planning Mode Instructions
When user starts a message with `/plan` or requests planning mode:
- **DO NOT execute any code or create files**
- Focus on ideation, brainstorming, architecture design, and strategy
- Provide detailed analysis, options, tradeoffs, and recommendations
- Ask clarifying questions to better understand requirements
- Create conceptual frameworks and high-level designs
- Research and compare different approaches
- Only move to implementation when explicitly asked to exit planning mode