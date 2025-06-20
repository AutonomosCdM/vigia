# Vigia Local Development Setup

This guide shows how to set up Vigia for local development with **real services** instead of mocks.

## Quick Start

```bash
# 1. Run the automated setup
./scripts/setup/setup_development_env.sh

# 2. Configure external APIs
python scripts/setup/configure_external_apis.py

# 3. Test all services
python scripts/testing/test_real_services.py

# 4. Start the application
python -m vigia_detect.api.main
```

## Prerequisites

- **Docker & Docker Compose** - For PostgreSQL, Redis, Celery
- **Python 3.10+** - Main application
- **Ollama** (optional) - For local AI models

### Installing Prerequisites

**macOS:**
```bash
# Install Docker Desktop from docker.com
# Install Python via homebrew
brew install python@3.11

# Install Ollama for local AI
brew install ollama
```

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Python
sudo apt update
sudo apt install python3.11 python3.11-pip

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

## Step-by-Step Setup

### 1. Environment Configuration

The setup script automatically creates a `.env` file from the template:

```bash
# Copy development template
cp .env.development .env

# Edit with your credentials
nano .env
```

### 2. Start Core Services

```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up -d postgres-dev redis-dev

# Verify services
docker-compose -f docker-compose.dev.yml ps
```

### 3. Configure External APIs

Use the interactive configurator:

```bash
python scripts/setup/configure_external_apis.py
```

This will prompt you for credentials for:
- **Supabase** - Database and storage
- **Twilio** - WhatsApp messaging  
- **Slack** - Team notifications
- **SendGrid** - Email alerts
- **Google Cloud** - Vertex AI (optional)

### 4. Install Dependencies

```bash
# Install Python packages
pip install -r requirements-cloudrun.txt

# Setup local AI models (optional)
ollama pull medgemma:7b
```

### 5. Initialize Database

The PostgreSQL container automatically runs initialization scripts:

```bash
# Check database tables
docker exec -it vigia-postgres-dev psql -U vigia_user -d vigia_dev -c "\dt medical.*"
```

### 6. Start Celery Workers

```bash
# Start in Docker (recommended)
docker-compose -f docker-compose.dev.yml up -d celery-worker-dev

# Or start locally for debugging
celery -A vigia_detect.tasks worker --loglevel=info
```

## Service Configuration

### Real vs Mock Services

The system automatically detects which services to use:

- **Testing** (`pytest`) - Always uses mocks
- **Development** (`.env` configured) - Uses real services
- **CI/CD** - Uses mocks

You can force a mode:

```python
from vigia_detect.core.service_config import get_service_config, ServiceMode

# Force real services
config = get_service_config(ServiceMode.REAL)

# Force mocks
config = get_service_config(ServiceMode.MOCK)
```

### Service Status

Check which services are configured:

```bash
# Show configuration status
python scripts/setup/configure_external_apis.py status

# Test all services
python scripts/testing/test_real_services.py

# Check service configuration
python -c "
from vigia_detect.core.service_config import get_service_config
config = get_service_config()
config.log_configuration()
"
```

## Available Services

### 🐘 PostgreSQL Database
- **URL**: `localhost:5432`
- **Database**: `vigia_dev`
- **User**: `vigia_user` / `vigia_password`
- **GUI**: pgAdmin at `http://localhost:8080`

### 🔴 Redis Cache
- **URL**: `localhost:6379`
- **GUI**: Redis Commander at `http://localhost:8081`

### 🌸 Celery Tasks
- **Monitoring**: Flower at `http://localhost:5555`
- **Queues**: medical_priority, image_processing, notifications, audit_logging

### 📦 Supabase
- **Real-time database and storage**
- **File uploads and processing**

### 📱 Twilio WhatsApp
- **Sandbox**: `whatsapp:+14155238886`
- **Production**: Your verified WhatsApp Business number

### 💬 Slack
- **Bot integration for medical alerts**
- **Interactive Block Kit interface**

### 📧 SendGrid
- **Transactional emails**
- **Medical alert notifications**

### 🤖 AI Models
- **Local**: Ollama + MedGemma
- **Cloud**: Google Vertex AI

## Development Workflow

### 1. Start Services
```bash
# Start all development services
docker-compose -f docker-compose.dev.yml up -d

# Check health
docker-compose -f docker-compose.dev.yml ps
```

### 2. Run Tests
```bash
# Test with real services
python scripts/testing/test_real_services.py

# Run pytest with mocks (default)
python -m pytest tests/

# Run specific integration tests
python -m pytest tests/integration/ -v
```

### 3. Start Application
```bash
# Start main API
python -m vigia_detect.api.main

# Start WhatsApp webhook
python -m vigia_detect.api.whatsapp_webhook

# Start Slack webhook
python -m vigia_detect.api.slack_webhook
```

### 4. Send Test Messages
```bash
# Test WhatsApp integration
python examples/whatsapp_integration_demo.py

# Test Slack integration  
python examples/slack_block_kit_demo.py

# Test complete medical workflow
python examples/complete_medical_workflow_demo.py
```

## Monitoring & Debugging

### Service Health

```bash
# Check all services
curl http://localhost:8000/health

# Check specific services
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/celery
```

### Logs

```bash
# View all service logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service
docker-compose -f docker-compose.dev.yml logs -f postgres-dev
docker-compose -f docker-compose.dev.yml logs -f redis-dev
docker-compose -f docker-compose.dev.yml logs -f celery-worker-dev

# Application logs
tail -f logs/vigia.log
```

### Monitoring UIs

- **pgAdmin**: http://localhost:8080 (`admin@vigia.dev` / `admin123`)
- **Redis Commander**: http://localhost:8081
- **Flower (Celery)**: http://localhost:5555

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres-dev

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres-dev

# Restart service
docker-compose -f docker-compose.dev.yml restart postgres-dev
```

**2. Redis Connection Failed**
```bash
# Test Redis connectivity
redis-cli -h localhost -p 6379 ping

# Check container logs
docker-compose -f docker-compose.dev.yml logs redis-dev
```

**3. Celery Tasks Not Running**
```bash
# Check worker status
celery -A vigia_detect.tasks inspect active

# Check Flower monitoring
open http://localhost:5555
```

**4. External API Errors**
```bash
# Test API configuration
python scripts/setup/configure_external_apis.py status

# Test individual services
python scripts/testing/test_real_services.py
```

### Reset Environment

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Remove volumes (⚠️  deletes data)
docker-compose -f docker-compose.dev.yml down -v

# Restart fresh
./scripts/setup/setup_development_env.sh
```

## Production Deployment

For production deployment:

```bash
# Hospital deployment
./scripts/deployment/hospital-deploy.sh deploy

# Cloud Run deployment  
./deploy/cloud-run/deploy.sh deploy

# MCP services deployment
./scripts/deployment/deploy-mcp-messaging.sh deploy
```

## Security Notes

- 🔒 All credentials are stored in `.env` (gitignored)
- 🔑 Use Docker secrets for production
- 🛡️ Enable TLS for external connections
- 📋 Audit logs are automatically generated
- 🏥 HIPAA compliance features are enabled

## Need Help?

- **Documentation**: `/docs/` directory
- **Examples**: `/examples/` directory  
- **Scripts**: `/scripts/` directory
- **Issues**: Create GitHub issue with logs

## Next Steps

1. **Configure APIs**: Set up real external service credentials
2. **Test Integration**: Verify all services work together
3. **Medical Testing**: Use synthetic patient data for validation
4. **Deploy**: Move to hospital or cloud production environment