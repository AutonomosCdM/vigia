# Vigia Setup Guide - Medical System v1.3.3

Complete setup guide for the medical-grade LPP detection system with ADK architecture.

## Table of Contents

- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Credentials Management](#credentials-management)
- [Medical AI Setup (MedGemma)](#medical-ai-setup-medgemma)
- [Redis Medical Protocols](#redis-medical-protocols)
- [Hospital Deployment](#hospital-deployment)
- [Development Setup](#development-setup)
- [Testing & Validation](#testing--validation)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Initial System Setup

```bash
# 1. Configure credentials securely
python scripts/setup_credentials.py
# Select option 1 and configure: Twilio, Anthropic, Supabase

# 2. Load credentials in your session
source scripts/quick_env_setup.sh

# 3. Install dependencies
pip install -r config/requirements.txt
```

### 2. Medical AI Setup (MedGemma Local)

```bash
# Install Ollama and MedGemma for HIPAA-compliant local processing
python scripts/setup_medgemma_ollama.py --install-ollama
python scripts/setup_medgemma_ollama.py --model 27b --install
python scripts/setup_medgemma_ollama.py --model 27b --test

# Configure Redis with medical protocols
python scripts/setup_redis_simple.py

# Test complete medical integration
python examples/redis_integration_demo.py
```

### 3. System Validation

```bash
# Run complete test suite (excluding slow tests)
python -m pytest tests/ -m "not slow"

# Critical medical validation tests
python -m pytest tests/medical/test_minsal_integration.py -v    # Chilean compliance (14/14 PASSED)
python -m pytest tests/adk/test_simple_adk_integration.py -v    # ADK integration (4/4 PASSED)
python -m pytest tests/integration/test_async_simple.py -v     # Async pipeline (5/5 PASSED)

# Post-installation validation
python scripts/validate_post_refactor_simple.py --verbose
```

## System Requirements

### Development Environment
- **Python**: 3.11+
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space
- **OS**: macOS, Linux, Windows (WSL2 for Windows)

### Hospital Production Environment
- **RAM**: 32GB+ (for MedGemma 27B medical model)
- **GPU**: 8GB VRAM minimum, 32GB VRAM recommended
- **Storage**: 50GB+ free space for medical models and data
- **Docker**: For hospital-grade deployment
- **Network**: Isolated medical network compliance

### Verify System Requirements
```bash
python scripts/setup_medgemma_local.py --check-only
redis-cli ping
docker --version
```

## Credentials Management

### Secure Keychain System

Vigia includes a secure credential management system that stores medical-grade credentials in the system keychain.

#### Initial Setup
```bash
python scripts/setup_credentials.py
```

This script:
- Stores credentials securely in system keychain (encrypted)
- Allows updating existing credentials
- Exports to `.env.local` for development
- Generates files for cloud deployment

#### Load Credentials for Current Session
```bash
source scripts/quick_env_setup.sh
```

### Required Credentials

#### 1. Twilio (Medical WhatsApp Communication)
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID for medical messaging
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_WHATSAPP_FROM`: WhatsApp number (format: whatsapp:+1234567890)

#### 2. Supabase (Medical Database)
- `SUPABASE_URL`: Medical database URL
- `SUPABASE_KEY`: Database access key for medical records

#### 3. Slack (Medical Notifications - Optional)
- `SLACK_BOT_TOKEN`: Bot token for medical alerts (xoxb-...)
- `SLACK_SIGNING_SECRET`: Slack webhook signing secret

#### 4. Redis (Medical Protocol Cache - Optional)
- `REDIS_URL`: Redis connection URL (defaults to local instance)

#### 5. AgentOps (Medical AI Monitoring - Optional)
- `AGENTOPS_API_KEY`: For medical AI monitoring and compliance

### Credential Workflow

#### Development:
1. Configure credentials once:
   ```bash
   python scripts/setup_credentials.py
   # Option 1: Configure credentials
   # Option 3: Export to .env.local
   ```

2. For each development session:
   ```bash
   source scripts/quick_env_setup.sh
   ```

#### Hospital Production:
1. Generate secure credential files:
   ```bash
   python scripts/setup_credentials.py
   # Option 4: Generate production deployment file
   ```

2. Use Docker secrets for hospital deployment

## Medical AI Setup (MedGemma)

### Why MedGemma Local vs External APIs

#### ✅ **MedGemma Local (Recommended for Medical)**
- 🔒 **Complete Privacy**: Medical data never leaves your infrastructure
- 💰 **No Per-Use Costs**: Unlimited medical consultations
- ⚡ **Predictable Latency**: No internet dependency for medical decisions
- 🎛️ **Full Control**: Customizable parameters for medical analysis
- 🔐 **HIPAA Compliance**: Built-in medical data protection
- 📊 **Scalability**: Consistent performance under medical workloads

#### ❌ **External APIs (Problematic for Medical)**
- 🌐 Requires stable internet connection
- 💸 Per-use costs for medical consultations
- 🔑 API key management complexity
- 🚨 Medical data sent to external servers
- ⏱️ Variable latency affecting medical decisions
- 📈 Scalability limited by external quotas

### Installation Steps

#### 1. System Requirements Check
```bash
python scripts/setup_medgemma_local.py --check-only
```

**Minimum Requirements:**
- **RAM**: 16GB+ (32GB recommended for 27B model)
- **GPU**: 8GB VRAM (4B model) or 32GB VRAM (27B model)
- **Storage**: 20GB free space for models and cache
- **CUDA**: 11.8+ or 12.0+ for GPU acceleration

#### 2. Install MedGemma via Ollama (Recommended)
```bash
# Install Ollama (medical AI runtime)
python scripts/setup_medgemma_ollama.py --install-ollama

# Install MedGemma 27B (production medical model)
python scripts/setup_medgemma_ollama.py --model 27b --install

# Test medical AI functionality
python scripts/setup_medgemma_ollama.py --model 27b --test

# For development (lighter 4B model)
python scripts/setup_medgemma_ollama.py --model 4b --install
```

#### 3. Alternative: Hugging Face Setup
```bash
# If Ollama installation fails
python scripts/setup_medgemma_local.py --huggingface
python scripts/setup_medgemma_local.py --test
```

### Medical AI Testing

```bash
# Test Spanish medical queries (Chilean healthcare focus)
ollama run symptoma/medgemma3 "¿Cuáles son los grados de LPP según NPUAP?"

# Test medical protocol integration
python examples/medgemma_medical_demo.py
```

## Redis Medical Protocols

### Architecture Overview

Redis integration provides:
1. **Medical Protocol Cache**: Intelligent caching with TTL for medical decisions
2. **Vector Search**: Similarity search for medical protocols and guidelines
3. **Session Management**: Medical session tracking for audit compliance
4. **Knowledge Base**: Enhanced LPP protocols and medical references

### Setup Redis for Medical Use

#### 1. Basic Redis Setup
```bash
# Setup Redis with medical protocol preloading
python scripts/setup_redis_simple.py

# For advanced setup with vector indices
python scripts/setup_redis_development.py
```

#### 2. Medical Protocol Integration
```bash
# Load medical protocols into Redis
python scripts/load_medical_protocols.py

# Test protocol search functionality
python examples/redis_protocol_search_demo.py
```

#### 3. Verify Medical Integration
```bash
# Test complete Redis + MedGemma integration
python examples/redis_integration_demo.py

# Run Redis medical test suite
./scripts/run_redis_medgemma_tests.sh
```

### Medical Data Flow
```
Medical Query → Cache Check → Protocol Search → MedGemma Analysis → Cache Storage → Medical Response
```

## Hospital Deployment

### Production Hospital Setup (Recommended)

```bash
# Full hospital-grade deployment with Docker
./scripts/hospital-deploy.sh deploy

# Verify all medical services
./scripts/hospital-deploy.sh status

# Monitor medical system logs
./scripts/hospital-deploy.sh logs
```

**Hospital deployment includes:**
- Medical-grade security and encryption
- HIPAA-compliant audit logging
- Isolated medical network configuration
- Automated backup and disaster recovery
- Medical staff access controls

### Manual Hospital Services

```bash
# Start individual medical services
./scripts/start_celery_worker.sh               # Async medical workers
./start_whatsapp_server.sh                    # Medical WhatsApp webhook
./scripts/start_slack_server.sh               # Medical alert notifications
```

## Development Setup

### Local Development Environment

```bash
# Install all development dependencies
pip install -r config/requirements-dev.txt
pip install -r config/requirements-medical.txt

# Setup development environment
python scripts/setup_development_env.py

# Start development services
docker-compose -f deploy/docker/docker-compose.dev.yml up -d
```

### Medical Development Workflow

1. **Process Medical Images**:
   ```bash
   python vigia_detect/cli/process_images_refactored.py --input /path/to/medical/images
   ```

2. **Start Medical Development Server**:
   ```bash
   ./scripts/start_slack_server.sh
   ```

3. **Monitor Medical Logs**:
   ```bash
   tail -f logs/medical_decisions.log
   ```

## Testing & Validation

### Organized Test Structure

The test suite is organized into 38 test markers across categories:

```bash
# Run tests by medical category
python -m pytest tests/unit/ -m unit           # Unit tests
python -m pytest tests/adk/ -m adk             # ADK agent tests  
python -m pytest tests/medical/ -m medical     # Medical validation
python -m pytest tests/integration/ -m integration  # Integration tests

# Medical compliance tests
python -m pytest tests/medical/test_minsal_integration.py -v    # Chilean compliance (14/14 PASSED)
python -m pytest tests/medical/test_npuap_guidelines.py -v     # NPUAP/EPUAP compliance
```

### Critical Medical Validation

```bash
# Essential medical validation tests
python -m pytest tests/adk/test_simple_adk_integration.py -v    # ADK integration (4/4 PASSED) 
python -m pytest tests/integration/test_async_simple.py -v     # Async pipeline (5/5 PASSED)

# Medical decision engine validation
python -m pytest tests/medical/test_medical_decision_engine.py -v

# Complete medical test suite
python -m pytest tests/medical/ -v
```

### Performance and Load Testing

```bash
# Medical system performance tests
python -m pytest tests/performance/ -m performance

# Load testing for hospital deployment
python scripts/medical_load_test.py --concurrent-patients 50
```

### Skip Slow Tests During Development

```bash
# Skip time-intensive tests during development
python -m pytest tests/ -m "not slow"

# Run only fast medical tests
python -m pytest tests/medical/ -m "not slow"
```

## Advanced Configuration

### Model Context Protocol (MCP) Setup

```bash
# Configure MCP for enhanced Claude Code integration
python scripts/setup_mcp.py
```

**Configured MCPs:**
- **Slack MCP**: Medical alert integration (#medical-alerts channel)
- **GitHub MCP**: Repository management for medical system
- **Filesystem MCP**: Secure access to medical project files
- **Brave Search MCP**: Medical research and documentation search

### GitHub Secrets for CI/CD

```bash
# Setup GitHub secrets for medical system CI/CD
python scripts/setup_github_secrets.py
```

**Required GitHub Secrets:**
- Medical database credentials
- Twilio medical messaging credentials
- Slack medical notification tokens
- Docker registry credentials for hospital deployment

### Custom Configuration Files

Edit configuration files in `config/`:
- `config/.env.example` - Template for development
- `config/.env.hospital` - Hospital production configuration
- `config/pytest.ini` - Medical test configuration (38 markers)
- `config/logging_config.json` - Medical audit logging

### Medical Compliance Configuration

```bash
# Setup HIPAA compliance monitoring
python scripts/setup_hipaa_compliance.py

# Configure medical audit logging
python scripts/setup_medical_audit.py

# Setup medical data encryption
python scripts/setup_medical_encryption.py
```

## Troubleshooting

### Common Medical System Issues

#### 1. MedGemma Not Responding
```bash
# Check Ollama service status
ollama ps

# Restart MedGemma medical model
ollama stop symptoma/medgemma3
ollama run symptoma/medgemma3

# Force re-download if corrupted
ollama pull symptoma/medgemma3
```

#### 2. Redis Medical Protocols Not Loading
```bash
# Check Redis connectivity
redis-cli ping

# Reload medical protocols
python scripts/setup_redis_simple.py --force-reload

# Check protocol search functionality
python examples/redis_protocol_search_demo.py
```

#### 3. Medical Tests Failing
```bash
# Run comprehensive validation
python scripts/validate_post_refactor_simple.py --verbose

# Check medical decision engine
python -m pytest tests/medical/test_medical_decision_engine.py -v

# Validate ADK agent integration
python -m pytest tests/adk/ -v
```

#### 4. Credentials Not Loading
```bash
# Reconfigure credentials
python scripts/setup_credentials.py

# Reload environment
source scripts/quick_env_setup.sh

# Verify credential loading
python -c "import os; print('TWILIO_ACCOUNT_SID:', os.getenv('TWILIO_ACCOUNT_SID')[:10] + '...' if os.getenv('TWILIO_ACCOUNT_SID') else 'Not set')"
```

#### 5. Hospital Deployment Issues
```bash
# Check Docker medical services
docker-compose -f deploy/docker/docker-compose.hospital.yml ps

# View medical service logs
./scripts/hospital-deploy.sh logs --service medical-api

# Restart medical services
./scripts/hospital-deploy.sh restart
```

#### 6. WhatsApp Medical Messaging Issues
```bash
# Test WhatsApp webhook connectivity
./start_whatsapp_server.sh --test

# Verify Twilio medical credentials
python scripts/test_twilio_connection.py

# Check medical message templates
python examples/whatsapp_template_test.py
```

### Medical Data Privacy Issues

#### PHI Protection Verification
```bash
# Verify PHI data protection
python scripts/verify_phi_protection.py

# Test medical data anonymization
python scripts/test_medical_anonymization.py

# Audit medical data access
python scripts/audit_medical_access.py
```

#### Medical Compliance Validation
```bash
# HIPAA compliance check
python scripts/validate_hipaa_compliance.py

# Chilean MINSAL compliance verification
python -m pytest tests/medical/test_minsal_integration.py -v

# Medical audit trail verification
python scripts/verify_medical_audit_trail.py
```

## Getting Help

### Medical System Documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete development documentation
- **[API Reference](API_REFERENCE.md)** - Medical API documentation
- **[Medical Evidence](medical/NPUAP_EPUAP_CLINICAL_DECISIONS.md)** - Clinical decision guidelines
- **[Hospital Deployment](deployment/HOSPITAL_DEPLOYMENT.md)** - Production deployment guide

### Support Channels
- **Slack**: #medical-system-support for medical system issues
- **GitHub Issues**: For bug reports and feature requests
- **Medical Compliance**: Contact compliance team for regulatory questions

### Emergency Medical System Support
For critical medical system failures affecting patient care:
1. Contact on-call medical system engineer
2. Enable emergency fallback procedures
3. Document incident for medical compliance review

---

**✅ Medical System Ready for Hospital Production** - v1.3.3 Clean Architecture with ADK