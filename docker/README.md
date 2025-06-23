# Docker Deployment Configurations

This directory contains multiple Docker Compose configurations for different deployment scenarios:

## 🔧 **Development Setup**
```bash
docker-compose up
```
**File**: `docker-compose.yml`
- Basic development environment
- Single database setup
- Minimal security (for local testing only)

## 🏥 **Hospital Production Deployment**
```bash
docker-compose -f docker-compose.hospital.yml up
```
**File**: `docker-compose.hospital.yml`
- **HIPAA/ISO 13485 compliant**
- Medical-grade security
- Health checks and monitoring
- Secrets management
- Production resource limits

## 🔒 **Dual Database (PHI Compliance)**
```bash
docker-compose -f docker-compose.dual-database.yml up
```
**File**: `docker-compose.dual-database.yml`
- **PHI tokenization architecture**
- Hospital PHI Database (Bruce Wayne data)
- Processing Database (Batman tokens only)
- Maximum compliance and security

## 📂 **Additional Components**

### **Celery Workers**
- `celery/worker.dockerfile` - Async medical task processing
- `celery/beat.dockerfile` - Scheduled medical monitoring

### **Cloud Deployment**
- `cloud-run/agent-services.yaml` - Google Cloud Run configuration

### **Infrastructure**
- `nginx/` - Load balancer and reverse proxy configs
- `postgres/` - Database initialization scripts
- `mongodb/` - Audit trail database setup

## 🚀 **Quick Start**

```bash
# Development
make dev-up

# Hospital deployment
make hospital-deploy

# PHI-compliant setup
make dual-db-deploy
```

Refer to the main project README for detailed deployment instructions.