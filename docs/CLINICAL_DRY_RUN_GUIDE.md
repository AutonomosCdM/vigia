# Clinical Dry Run Guide for Vigia

This guide explains how to perform a complete Clinical Dry Run to test the entire patient workflow: **WhatsApp → Image → Processing → Slack Notification**.

## Prerequisites

1. **Environment Setup**
   - Staging environment deployed
   - Redis running with limited configuration
   - Rate limiting enabled
   - All services healthy

2. **Required Credentials**
   - Twilio WhatsApp credentials configured
   - Slack Bot token active
   - Supabase connection configured

## Quick Start

### 1. Verify Services

First, ensure all services are running:

```bash
# Check service health
./scripts/verify_services.py

# Expected output:
# ✓ WhatsApp Server is healthy
# ✓ Webhook Server is healthy
# ✓ Redis Cache is healthy
# ✅ All required services are healthy - Ready for Clinical Dry Run!
```

### 2. Run Clinical Dry Run

Execute the complete clinical workflow test:

```bash
# Run all test cases
./scripts/clinical_dry_run.py

# Run with WhatsApp integration (requires real phone number)
./scripts/clinical_dry_run.py --phone +1234567890

# Run specific test case
./scripts/clinical_dry_run.py --test-case "Grade 2"

# List available test cases
./scripts/clinical_dry_run.py --list-cases
```

### 3. Simulate WhatsApp Flow

Test the WhatsApp webhook directly:

```bash
# Run WhatsApp simulation
./scripts/simulate_whatsapp_flow.py

# Send test message
./scripts/simulate_whatsapp_flow.py --test-message "Hola"

# Send test image
./scripts/simulate_whatsapp_flow.py --test-image /path/to/image.jpg
```

## Test Cases

The Clinical Dry Run includes the following test scenarios:

1. **Grade 1 Lesion** - Low severity, early stage
2. **Grade 2 Lesion** - Medium severity, partial thickness loss
3. **Grade 3/4 Lesion** - High severity, full thickness loss
4. **Non-Medical Image** - Should be rejected
5. **Poor Quality Image** - Blurry/unclear image handling

## Expected Flow

### 1. Patient Sends Image via WhatsApp

```
Patient → WhatsApp Message → Twilio Webhook → Vigia WhatsApp Server
```

- Patient sends image to configured WhatsApp number
- Server validates and acknowledges receipt
- Image queued for processing

### 2. Image Processing

```
WhatsApp Server → CV Pipeline → Detection & Classification
```

- Image preprocessed and validated
- YOLO model detects pressure injuries
- Severity classified (Grade 1-4)
- Confidence score calculated

### 3. Slack Notification

```
Detection Results → Slack Notifier → Medical Team Channel
```

Expected Slack message format:
```
🔴 **Medical Alert - Pressure Injury Detected** 🔴

**Patient Code:** DRY-RUN-003
**Time:** 2025-05-28 18:15:00 UTC

**Detection Results:**
• **Detected:** Yes
• **Severity:** High
• **Confidence:** 85.5%
• **Location:** Sacral region
• **Stage:** Grade 3

**Recommendations:**
• Immediate medical attention required
• Pressure relief mandatory
• Document and photograph every 4 hours

---
_Clinical Dry Run Test - Not a real patient_
```

### 4. Data Storage

```
Results → Supabase → Redis Cache → Webhook Notifications
```

- Detection results stored in Supabase
- Cached in Redis for quick access
- Webhook sent to external systems

## Performance Metrics

Expected performance benchmarks:

- **Total End-to-End Time:** < 30 seconds
- **Image Detection:** < 5 seconds
- **Slack Notification:** < 2 seconds
- **Database Storage:** < 1 second

## Monitoring During Dry Run

### Grafana Dashboard
Access at: http://localhost:3001

Monitor:
- Response latencies (should be < 500ms)
- Error rates (should be < 5%)
- Request rates per user

### Prometheus Metrics
Access at: http://localhost:9091

Key metrics:
- `http_request_duration_seconds`
- `rate_limit_exceeded_total`
- `detection_processing_duration_seconds`

## Troubleshooting

### Service Not Running
```bash
# Start all staging services
./scripts/deploy.sh staging

# Start individual services
./start_whatsapp_server.sh
docker-compose -f docker-compose.staging.yml up webhook-server
```

### WhatsApp Not Receiving Messages
1. Check Twilio webhook configuration
2. Verify ngrok tunnel if testing locally
3. Check WhatsApp server logs: `docker logs vigia-whatsapp-staging`

### Slack Notifications Not Arriving
1. Verify Slack Bot token
2. Check channel ID is correct
3. Ensure bot has permissions to post

### Rate Limiting Issues
Check Redis for rate limit keys:
```bash
docker exec vigia-redis-staging redis-cli
> KEYS rate_limit:*
> TTL rate_limit:192.168.1.1:1234567890
```

## Results and Reports

After running the Clinical Dry Run:

1. **JSON Report**: `clinical_dry_run_report_TIMESTAMP.json`
2. **E2E Validation**: `e2e_validation_results_TIMESTAMP.json`
3. **WhatsApp Simulation**: `whatsapp_simulation_results_TIMESTAMP.json`

Example report structure:
```json
{
  "summary": {
    "total_tests": 5,
    "successful": 4,
    "failed": 1,
    "success_rate": 80.0
  },
  "performance": {
    "avg_total_time": 12.5,
    "avg_detection_time": 3.2
  },
  "test_results": [...]
}
```

## Next Steps

After successful Clinical Dry Run:

1. Review performance metrics
2. Validate Slack message formatting with medical team
3. Test with real clinical images (with proper authorization)
4. Schedule training session for medical staff
5. Plan production deployment

## Safety Notes

- This is a **test environment** - not for real patient data
- Always use test phone numbers during dry runs
- Clear test data after validation
- Document any issues found for resolution

---

For questions or issues, check logs:
```bash
# WhatsApp logs
docker logs vigia-whatsapp-staging -f

# Webhook logs
docker logs vigia-webhook-staging -f

# Redis logs
docker logs vigia-redis-staging -f
```