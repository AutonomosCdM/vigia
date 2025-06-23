# VIGIA Deployment Guide

## Quick Deploy Commands
```bash
# Hospital System Deployment
./scripts/hospital-deploy.sh deploy

# WhatsApp Server
./start_whatsapp_server.sh

# Medical Processing Pipeline
python vigia_detect/cli/process_images_refactored.py --input /path/to/images
```

## Environment Setup
```bash
# MedGemma AI Setup (recommended)
python scripts/setup_medgemma_ollama.py --install-ollama

# Alternative Hugging Face setup
python scripts/setup_medgemma_local.py --check-only
```

## Service Configuration
All services configured via environment variables. Reference `CLAUDE.md` for complete configuration matrix.

## Render.com Deployment
- Docker-based deployment with health checks
- Automatic scaling based on medical processing load
- Secure environment variable management
- Integrated logging and monitoring

## Security Considerations
- PHI tokenization mandatory for all deployments
- Local processing preferred for HIPAA compliance
- Secure credential management via environment variables
- Audit trail enabled by default