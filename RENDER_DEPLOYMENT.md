# Vigia Render Deployment Guide

This guide covers deploying Vigia to Render.com for production use.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your Vigia code should be in a GitHub repository
3. **Environment Variables**: Prepare your configuration values

## Deployment Options

### Option 1: Web Service (Recommended)

This deploys Vigia as a unified web service handling all endpoints.

#### 1. Create Web Service

1. Go to Render Dashboard
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:

```yaml
Name: vigia-medical-detection
Environment: Docker
Region: Choose your preferred region
Branch: main
Dockerfile Path: Dockerfile.render
```

#### 2. Environment Variables

Add these environment variables in Render:

**Required:**
```
ENVIRONMENT=production
MEDICAL_COMPLIANCE_LEVEL=basic
PHI_PROTECTION_ENABLED=true
```

**Optional (for full functionality):**
```
# External Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis (if using external Redis)
REDIS_URL=redis://your-redis-instance:6379

# WhatsApp Integration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token

# AI Services
ANTHROPIC_API_KEY=your_anthropic_key

# Monitoring
AGENTOPS_API_KEY=your_agentops_key
```

#### 3. Advanced Settings

```yaml
Build Command: (leave empty - uses Dockerfile)
Start Command: (leave empty - uses Dockerfile CMD)
Health Check Path: /health
```

### Option 2: Background Worker

For Celery workers (requires Redis):

1. Create a new "Background Worker"
2. Use same repository and Dockerfile
3. Set Start Command: `./render_entrypoint.sh worker`
4. Add required environment variables

## Service Configuration

### Health Checks

Render will automatically check `/health` endpoint. The service returns:

```json
{
  "status": "healthy",
  "timestamp": "...",
  "services": {
    "webhook": true,
    "whatsapp": true,
    "detection": true,
    "redis": false,
    "database": true
  }
}
```

### Scaling

- **Starter Plan**: 1 instance, 512MB RAM
- **Standard Plan**: Multiple instances, 2GB RAM
- **Pro Plan**: Auto-scaling, 4GB+ RAM

For medical applications, Standard or Pro recommended.

## External Services

### Database Options

**Option A: Supabase (Recommended)**
- Already integrated in Vigia
- Set `SUPABASE_URL` and `SUPABASE_KEY`

**Option B: Render PostgreSQL**
- Create PostgreSQL database in Render
- Set `DATABASE_URL` environment variable

### Redis Options

**Option A: External Redis**
- Use Redis Cloud, Upstash, or similar
- Set `REDIS_URL` environment variable

**Option B: Render Redis**
- Available on paid plans
- Automatically sets `REDIS_URL`

## Security Considerations

### Environment Variables

Store sensitive data in Render environment variables:

```bash
# Example secure configuration
TWILIO_AUTH_TOKEN=secret_token
ANTHROPIC_API_KEY=secret_key
SUPABASE_KEY=secret_key
```

### HTTPS

Render provides automatic HTTPS for all services.

### Compliance

For HIPAA compliance:
- Use Business plan minimum
- Enable audit logging
- Configure proper data retention
- Use encrypted databases

## Monitoring and Logging

### Built-in Monitoring

Render provides:
- Service metrics
- Error tracking  
- Log aggregation
- Alert notifications

### External Monitoring

Configure AgentOps for medical AI monitoring:
```
AGENTOPS_API_KEY=your_key
AGENTOPS_ENVIRONMENT=production
```

## Deployment Commands

### Local Testing

Test Render deployment locally:

```bash
# Build Render image
docker build -f Dockerfile.render -t vigia-render .

# Test unified server
docker run -p 8000:8000 -e PORT=8000 vigia-render

# Test WhatsApp only
docker run -p 8000:8000 -e PORT=8000 vigia-render whatsapp

# Test with Redis
docker-compose -f docker-compose.render.yml up
```

### Environment Testing

```bash
# Test health check
curl http://localhost:8000/health

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/webhook
curl http://localhost:8000/whatsapp
```

## Troubleshooting

### Common Issues

**Build Timeout:**
- Reduce Docker image size
- Use .dockerignore effectively
- Consider multi-stage builds

**Memory Issues:**
- Upgrade to Standard plan
- Optimize Python dependencies
- Monitor memory usage

**Port Issues:**
- Ensure service listens on `$PORT`
- Check health check endpoint
- Verify Dockerfile EXPOSE

**Dependencies:**
- Check requirements.txt
- Verify system dependencies
- Test locally first

### Debug Commands

```bash
# Check service logs
render logs -s your-service-name

# Test health endpoint
curl https://your-service.onrender.com/health

# Check environment
render env -s your-service-name
```

## Performance Optimization

### Docker Optimization

```dockerfile
# Use specific Python version
FROM python:3.11-slim

# Layer caching
COPY requirements*.txt ./
RUN pip install -r requirements.txt

# Minimize image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### Application Optimization

```python
# Use async endpoints
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Optimize imports
from vigia_detect.core import only_needed_modules
```

## Cost Optimization

### Service Sizing

- **Development**: Starter ($7/month)
- **Production**: Standard ($25/month)  
- **Enterprise**: Pro ($85/month)

### External Services

- **Database**: Render PostgreSQL ($7/month)
- **Redis**: Render Redis ($10/month)
- **Storage**: Render Disk storage ($0.25/GB)

## Support

For deployment issues:
1. Check Render documentation
2. Review service logs
3. Test locally first
4. Contact Render support

For Vigia-specific issues:
1. Check CLAUDE.md
2. Run local tests
3. Review medical compliance requirements