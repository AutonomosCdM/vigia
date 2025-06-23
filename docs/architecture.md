# VIGIA Architecture Documentation

## System Overview
Vigia is a medical-grade pressure injury (LPP) detection system implementing a secure 3-layer architecture for healthcare compliance.

## Core Architecture Components

### 3-Layer Security Architecture
- **Layer 1**: Input Isolation (WhatsApp bot with no medical data access)
- **Layer 2**: Medical Orchestration (Triage engine and medical routing)  
- **Layer 3**: Specialized Medical Systems (LPP detection and clinical processing)

### Dual Database Architecture
- **Hospital PHI Database**: Real patient data (Bruce Wayne) - internal only
- **Processing Database**: Tokenized data only (Batman) - external access
- **PHI Tokenization Service**: Secure Bruce Wayne → Batman conversion with JWT auth

### Phase Structure
- **FASE 1**: `fase1/` - Patient reception with dual database architecture
- **FASE 2**: `vigia_detect/` - Multimodal medical processing with voice + image analysis
- **FASE 3**: `vigia_detect/a2a/` - Distributed infrastructure for agent communication

## Technology Stack
- **AI**: MedGemma Local (HIPAA-compliant), MONAI medical detection
- **Data**: Supabase with PHI tokenization
- **Security**: Fernet encryption, granular permissions, audit trails
- **Integration**: Twilio (WhatsApp), Slack API, Redis protocols
- **Orchestration**: Celery async pipeline

## Compliance Features
- HIPAA, ISO 13485, SOC2 compliance
- Complete audit trails for regulatory requirements
- Evidence-based decision engine with medical team review
- Secure bidirectional communication between patients and medical teams