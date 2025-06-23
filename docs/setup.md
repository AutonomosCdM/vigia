# VIGIA Setup Guide

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
./scripts/run_tests.sh

# Security analysis
./scripts/run_security_analysis.sh
```

## Development Setup
```bash
# Medical validation tests
python -m pytest tests/ -m "medical"

# Async pipeline validation
python test_async_simple.py

# Code quality
python -m pylint vigia_detect/
```

## Database Setup
- Hospital PHI Database: Contains real patient data (internal)
- Processing Database: Tokenized data only (external access)
- PHI Tokenization Service: Secure conversion with JWT auth

## AI/ML Components
- **Primary**: MONAI medical detection
- **Backup**: YOLOv5 detection
- **Voice**: Hume AI voice analysis
- **Medical AI**: MedGemma local processing

## Communication Setup
- **WhatsApp**: Twilio integration for patient communication
- **Slack**: Medical team notifications and review
- **Redis**: Protocol coordination and caching

## Production Checklist
- [ ] PHI tokenization configured
- [ ] Local MedGemma installation
- [ ] Environment variables set
- [ ] Security analysis passed
- [ ] Medical validation tests passed
- [ ] Audit trails enabled