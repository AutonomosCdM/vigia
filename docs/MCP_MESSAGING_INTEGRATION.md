# Vigia MCP Messaging Integration

This document provides comprehensive guidance for integrating WhatsApp and Slack messaging platforms with the Vigia medical system using the Model Context Protocol (MCP).

## Overview

The Vigia MCP Messaging Integration enables seamless communication between medical AI systems and healthcare teams through:

- **WhatsApp Integration** via Twilio Business API
- **Direct WhatsApp Web** integration for local processing
- **Slack Integration** for team communication
- **HIPAA-compliant** message handling with PHI protection
- **Automated medical alerts** and escalation workflows

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vigia Core    │    │   MCP Gateway   │    │  Messaging      │
│   Medical AI    │───▶│   Router        │───▶│  Platforms      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Audit &       │    │   - Twilio      │
                    │   Compliance    │    │   - WhatsApp    │
                    │   Layer         │    │   - Slack       │
                    └─────────────────┘    └─────────────────┘
```

## Features

### 🔐 Medical Compliance
- **HIPAA-compliant** message routing and storage
- **PHI protection** with automatic data anonymization
- **Audit logging** for all medical communications
- **Digital signatures** for critical alerts

### 📱 WhatsApp Integration
- **Twilio Business API** for production-grade messaging
- **Direct WhatsApp Web** for local, privacy-first processing
- **Message history** stored locally in SQLite
- **Media support** (images, documents, audio)

### 💬 Slack Integration
- **Team channels** for medical communication
- **Emergency escalation** workflows
- **Bot integration** with standardized MCP protocol
- **Real-time notifications** for critical events

### 🚨 Automated Workflows
- **LPP detection alerts** with severity-based routing
- **Emergency escalation** for critical findings
- **Acknowledgment tracking** for high-priority alerts
- **Multi-platform redundancy** for critical communications

## Quick Start

### 1. Prerequisites

Ensure you have:
- Docker and Docker Compose
- Twilio account with WhatsApp Business API access
- Slack workspace with bot permissions
- Vigia system deployed and running

### 2. Setup Credentials

```bash
# Setup MCP messaging secrets
./scripts/setup/setup-mcp-secrets.sh messaging

# Or setup individually
./scripts/setup/setup-mcp-secrets.sh twilio
./scripts/setup/setup-mcp-secrets.sh slack
```

### 3. Deploy Services

```bash
# Deploy all messaging services
./scripts/deployment/deploy-mcp-messaging.sh deploy

# Check service status
./scripts/deployment/deploy-mcp-messaging.sh status
```

### 4. Verify Integration

```bash
# Run integration tests
pytest tests/integration/test_mcp_messaging_integration.py -v

# Run demo
python examples/mcp_messaging_demo.py
```

## Configuration

### Twilio WhatsApp Setup

1. **Create Twilio Account**
   - Sign up at [Twilio Console](https://console.twilio.com)
   - Verify your phone number
   - Purchase a phone number with WhatsApp capability

2. **Get API Credentials**
   ```bash
   Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   API Key: SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   API Secret: your_api_secret_here
   WhatsApp Number: whatsapp:+1415xxxxxxx
   ```

3. **Configure Webhook** (Optional)
   ```
   Webhook URL: https://your-domain.com/mcp/twilio/webhook
   HTTP Method: POST
   ```

### Slack Bot Setup

1. **Create Slack App**
   - Go to [Slack API](https://api.slack.com/apps)
   - Create new app from manifest or scratch
   - Enable Socket Mode for real-time events

2. **Configure Permissions**
   ```
   Bot Token Scopes:
   - chat:write
   - channels:read
   - groups:read
   - im:read
   - mpim:read
   - users:read
   ```

3. **Get Tokens**
   ```bash
   Bot User OAuth Token: xoxb-your-bot-token
   App-Level Token: xapp-your-app-token
   Signing Secret: your-signing-secret
   ```

### Medical Channels Setup

Create dedicated Slack channels:
```
#medical-alerts     - General medical notifications
#lpp-notifications  - LPP detection alerts
#emergency-escalation - Critical alerts requiring immediate response
#wound-care-team     - Wound care specialist notifications
```

## Usage Examples

### Basic WhatsApp Notification

```python
from vigia_detect.mcp.gateway import MCPGateway

async def send_whatsapp_alert():
    config = {'medical_compliance': 'hipaa', 'audit_enabled': True}
    
    async with MCPGateway(config) as gateway:
        response = await gateway.whatsapp_operation(
            'send_message',
            patient_context={'patient_id': 'PAT-001'},
            to='whatsapp:+1234567890',
            message='🏥 LPP Grade 2 detected. Please review patient.'
        )
        
        print(f"Status: {response.status}")
```

### Slack Team Notification

```python
async def notify_medical_team():
    async with MCPGateway(config) as gateway:
        response = await gateway.slack_operation(
            'send_message',
            medical_context={'department': 'wound_care', 'priority': 'high'},
            channel='#medical-alerts',
            message='🚨 Grade 3 LPP detected in Room 305. Immediate intervention required.'
        )
```

### Automated LPP Workflow

```python
async def automated_lpp_notification(lpp_grade, confidence, patient_context):
    async with MCPGateway(config) as gateway:
        response = await gateway.notify_lpp_detection(
            lpp_grade=lpp_grade,
            confidence=confidence,
            patient_context=patient_context,
            platform='slack'  # or 'whatsapp'
        )
        
        return response
```

### Emergency Escalation

```python
async def emergency_escalation(patient_id):
    async with MCPGateway(config) as gateway:
        # Send critical alert
        response = await gateway.send_medical_alert(
            alert_type='lpp_critical',
            patient_id=patient_id,
            severity='critical',
            platform='slack',
            message='🚨 CRITICAL: Grade 4 LPP - IMMEDIATE intervention required'
        )
        
        # Follow up via WhatsApp to on-call physician
        if response.status == 'success':
            await gateway.whatsapp_operation(
                'send_message',
                to='whatsapp:+1234567890',  # On-call physician
                message=f'🚨 URGENT: Critical alert for {patient_id}. Please respond.'
            )
```

## Security & Compliance

### PHI Protection

```python
# Automatic PHI protection
async def secure_notification():
    response = await gateway.slack_operation(
        'send_message',
        medical_context={
            'phi_protection': True,
            'anonymize_patient_data': True
        },
        channel='#medical-team',
        message='Patient in Room 12 requires assessment. See secure system for details.'
    )
```

### Audit Logging

All messaging operations are automatically logged:
```json
{
    "timestamp": "2024-01-15T14:30:00Z",
    "request_id": "mcp_1705327800000",
    "service": "twilio_whatsapp",
    "tool": "send_message",
    "status": "success",
    "compliance_level": "hipaa",
    "phi_accessed": true,
    "response_time": 0.75
}
```

### Rate Limiting

Built-in rate limiting protects against abuse:
- **WhatsApp (Twilio)**: 8 messages/minute
- **WhatsApp (Direct)**: 5 messages/minute  
- **Slack**: 15 messages/minute

## Monitoring & Health Checks

### Service Status

```python
async def check_messaging_health():
    async with MCPGateway(config) as gateway:
        status = await gateway.get_service_status()
        
        for service_name, info in status['services'].items():
            if 'messaging' in info.get('type', ''):
                print(f"{service_name}: {'✅' if info['healthy'] else '❌'}")
```

### Health Check Endpoints

- Twilio WhatsApp: `http://localhost:8085/health`
- Direct WhatsApp: `http://localhost:8086/health`
- Slack: `http://localhost:8087/health`
- MCP Gateway: `http://localhost:8080/health`

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check Docker secrets
   docker secret ls | grep vigia_
   
   # Check logs
   ./scripts/deployment/deploy-mcp-messaging.sh logs
   ```

2. **Twilio Authentication Errors**
   ```bash
   # Verify credentials
   curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}.json" \
     -u "{AccountSid}:{AuthToken}"
   ```

3. **Slack Bot Permissions**
   ```bash
   # Test bot permissions
   curl -X POST https://slack.com/api/auth.test \
     -H "Authorization: Bearer xoxb-your-bot-token"
   ```

4. **WhatsApp Direct Connection Issues**
   ```bash
   # Check QR code for authentication
   docker logs vigia-mcp-whatsapp-direct
   ```

### Debug Mode

Enable debug logging:
```bash
export MCP_DEBUG=true
export MCP_LOG_LEVEL=DEBUG
./scripts/deployment/deploy-mcp-messaging.sh deploy
```

### Network Connectivity

```bash
# Test MCP Gateway connectivity
curl -X GET http://localhost:8080/health

# Test individual services
curl -X GET http://localhost:8085/health  # Twilio
curl -X GET http://localhost:8086/health  # WhatsApp Direct  
curl -X GET http://localhost:8087/health  # Slack
```

## Testing

### Unit Tests

```bash
# Run messaging integration tests
pytest tests/integration/test_mcp_messaging_integration.py -v

# Run with coverage
pytest tests/integration/test_mcp_messaging_integration.py --cov=vigia_detect.mcp
```

### Manual Testing

```bash
# Test Twilio WhatsApp
curl -X POST http://localhost:8085/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send_sms",
    "parameters": {
      "to": "+1234567890",
      "body": "Test message from Vigia MCP"
    }
  }'

# Test Slack
curl -X POST http://localhost:8087/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send_message", 
    "parameters": {
      "channel": "#test-channel",
      "text": "Test message from Vigia MCP"
    }
  }'
```

### Load Testing

```bash
# Run load tests
python -m pytest tests/performance/test_mcp_messaging_load.py
```

## Production Deployment

### Environment Variables

```bash
# Production configuration
export MCP_MODE=production
export MEDICAL_COMPLIANCE_LEVEL=hipaa
export PHI_PROTECTION_ENABLED=true
export AUDIT_LOG_ENABLED=true
export RATE_LIMITING_ENABLED=true
```

### SSL/TLS Configuration

Configure SSL certificates for production:
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/mcp-gateway.key \
  -out docker/nginx/ssl/mcp-gateway.crt
```

### Backup & Recovery

```bash
# Backup WhatsApp session data
docker run --rm -v vigia_whatsapp_session_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/whatsapp-session-$(date +%Y%m%d).tar.gz -C /data .

# Backup MCP secrets
./scripts/backup/backup_mcp_secrets.sh
```

## Integration with Existing Systems

### Hospital Information Systems (HIS)

```python
# Integration with HIS via FHIR
async def integrate_with_his(patient_id, lpp_data):
    async with MCPGateway(config) as gateway:
        # Send to FHIR gateway
        fhir_response = await gateway.fhir_integration(
            'create_observation',
            {
                'patient_id': patient_id,
                'observation_type': 'pressure_injury',
                'grade': lpp_data['grade'],
                'confidence': lpp_data['confidence']
            }
        )
        
        # Notify team if successful
        if fhir_response.status == 'success':
            await gateway.slack_operation(
                'send_message',
                channel='#medical-records',
                message=f'✅ LPP observation recorded in HIS for patient {patient_id}'
            )
```

### Electronic Health Records (EHR)

```python
# EHR integration workflow
async def ehr_workflow(patient_data, lpp_detection):
    # 1. Update EHR
    # 2. Notify care team via Slack
    # 3. Send follow-up reminders via WhatsApp
    pass
```

## API Reference

### MCPGateway Class

#### `whatsapp_operation(operation, patient_context=None, **kwargs)`
Send WhatsApp messages via Twilio.

**Parameters:**
- `operation` (str): Operation type ('send_message', 'send_media', etc.)
- `patient_context` (dict): Patient context for medical compliance
- `**kwargs`: Additional parameters (to, message, etc.)

**Returns:** `MCPResponse` object

#### `slack_operation(operation, medical_context=None, **kwargs)`
Send Slack messages for team communication.

**Parameters:**
- `operation` (str): Operation type ('send_message', 'send_alert', etc.)
- `medical_context` (dict): Medical context for compliance
- `**kwargs`: Additional parameters (channel, message, etc.)

**Returns:** `MCPResponse` object

#### `send_medical_alert(alert_type, patient_id, severity, platform='slack', message=None)`
Send medical alerts with automatic escalation.

**Parameters:**
- `alert_type` (str): Type of alert ('lpp_detection', 'lpp_critical', etc.)
- `patient_id` (str): Patient identifier
- `severity` (str): Alert severity ('low', 'medium', 'high', 'critical')
- `platform` (str): Target platform ('slack', 'whatsapp')
- `message` (str): Custom alert message

**Returns:** `MCPResponse` object

#### `notify_lpp_detection(lpp_grade, confidence, patient_context, image_path=None, platform='slack')`
Automated LPP detection notification workflow.

**Parameters:**
- `lpp_grade` (int): LPP grade (1-4)
- `confidence` (float): Detection confidence (0.0-1.0)
- `patient_context` (dict): Patient information
- `image_path` (str): Path to detection image
- `platform` (str): Notification platform

**Returns:** `MCPResponse` object

## Support & Resources

### Documentation
- [MCP Specification](https://modelcontextprotocol.io/)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [Slack Bot API](https://api.slack.com/bot-users)

### Community
- [Vigia GitHub Issues](https://github.com/vigia-medical/vigia/issues)
- [MCP Community Discord](https://discord.gg/mcp)
- [Healthcare AI Slack](https://healthcare-ai.slack.com)

### Contact
- **Technical Support**: support@vigia.medical
- **Medical Compliance**: compliance@vigia.medical
- **Security Issues**: security@vigia.medical

---

**Last Updated:** January 2024  
**Version:** 1.4.0  
**Compliance:** HIPAA, ISO 13485, SOC2