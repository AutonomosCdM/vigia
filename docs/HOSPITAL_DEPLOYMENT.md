# Vigia Hospital Deployment Guide

🏥 **Production-Ready Medical System for Hospital Environments**

## Overview

Vigia is a hospital-grade pressure injury (LPP) detection system designed for secure deployment in medical facilities. This guide covers the complete deployment process for hospital IT teams.

## 🎯 Deployment Objectives

- ✅ **Medical Compliance**: HIPAA, ISO 13485, SOC2 ready
- ✅ **High Availability**: 99.9% SLA with automated failover
- ✅ **Security**: Enterprise-grade encryption and access controls
- ✅ **Audit Trail**: Complete medical-legal documentation
- ✅ **Scalability**: Container orchestration for hospital-scale

## 📋 Prerequisites

### System Requirements

**Minimum Hardware**:
- CPU: 8 cores (Intel Xeon or AMD EPYC)
- RAM: 32 GB
- Storage: 1 TB SSD (RAID 1 recommended)
- Network: Gigabit Ethernet
- GPU: Optional (NVIDIA RTX 3080+ for faster inference)

**Operating System**:
- Ubuntu 22.04 LTS (recommended)
- RHEL 8+ / CentOS Stream 8+
- Docker 24.0+
- Docker Compose 2.0+

### Network Requirements

**Ports**:
- `443/tcp`: HTTPS (external)
- `80/tcp`: HTTP redirect (external)
- `8443/tcp`: Management interface (internal)
- `5432/tcp`: PostgreSQL (internal)
- `6379/tcp`: Redis (internal)
- `9090/tcp`: Prometheus (internal)
- `3001/tcp`: Grafana (internal)
- `5555/tcp`: Celery Flower (internal)

**Network Segmentation**:
```
172.20.0.0/24 - Medical Data Network (PHI/PII)
172.21.0.0/24 - Internal Service Network
172.22.0.0/24 - Management Network
172.23.0.0/24 - DMZ Network (external facing)
```

### Security Requirements

**Certificates**:
- Hospital-issued SSL certificates
- Internal CA for service-to-service communication
- Certificate rotation strategy

**Secrets Management**:
- Docker Swarm secrets (recommended)
- External secret management (HashiCorp Vault, AWS Secrets Manager)
- Encrypted storage for sensitive configuration

## 🚀 Quick Deployment

### 1. Clone and Prepare

```bash
git clone https://github.com/your-org/vigia.git
cd vigia

# Set hospital configuration
export HOSPITAL_NAME="Your Hospital Name"
export ENVIRONMENT="hospital"
```

### 2. Run Deployment Script

```bash
# Deploy complete hospital system
./scripts/hospital-deploy.sh deploy
```

### 3. Verify Deployment

```bash
# Check service status
./scripts/hospital-deploy.sh status

# View logs
./scripts/hospital-deploy.sh logs

# Health check
curl -k https://localhost/health
```

## 📁 Directory Structure

```
vigia/
├── docker-compose.hospital.yml     # Main orchestration
├── .env.hospital                    # Hospital environment
├── scripts/
│   └── hospital-deploy.sh          # Deployment automation
├── docker/
│   ├── nginx/                      # Reverse proxy config
│   ├── postgres/                   # Database config
│   ├── celery/                     # Async workers
│   └── monitoring/                 # Observability
├── docs/
│   └── HOSPITAL_DEPLOYMENT.md      # This guide
└── configs/
    └── hospital/                   # Hospital-specific configs
```

## 🔧 Detailed Configuration

### PostgreSQL Medical Database

**Configuration**: `docker/postgres/postgresql.conf`
- Medical-grade settings for HIPAA compliance
- Point-in-time recovery enabled
- Row-level security for PHI protection
- Automated backups every 6 hours
- 7-year audit retention

**Schema**: `docker/postgres/init.sql`
- Encrypted PHI storage
- Audit trail tables
- Medical protocol data
- Session management
- Row-level security policies

### NGINX Reverse Proxy

**Security Features**:
- SSL/TLS termination
- Rate limiting by endpoint
- ModSecurity WAF rules
- Security headers (OWASP)
- Request filtering

**Network Segmentation**:
- DMZ network for external traffic
- Internal network for service communication
- Management network for admin access

### Celery Async Pipeline

**Medical Task Queues**:
- `medical_priority`: Critical LPP cases
- `image_processing`: Medical image analysis
- `notifications`: Medical team alerts
- `audit_logging`: Compliance tracking

**Configuration**:
- Task acknowledgment late (medical safety)
- Retry policies for failed medical tasks
- Worker prefetch multiplier = 1
- Max 100 tasks per worker (memory management)

### Monitoring Stack

**Prometheus Metrics**:
- Medical processing times
- LPP detection accuracy
- System performance
- Error rates and alerts

**Grafana Dashboards**:
- Medical operations overview
- Performance monitoring
- Compliance metrics
- Alert management

**Audit Logging**:
- All medical data access
- PHI access tracking
- System events
- Compliance reporting

## 🔐 Security Configuration

### Docker Secrets

Required secrets for hospital deployment:

```bash
# Database credentials
echo "vigia_user" | docker secret create postgres_user -
echo "$(openssl rand -base64 32)" | docker secret create postgres_password -

# Redis password
echo "$(openssl rand -base64 32)" | docker secret create redis_password -

# Encryption keys
echo "$(openssl rand -base64 32)" | docker secret create encryption_key -
echo "$(openssl rand -base64 64)" | docker secret create jwt_secret -

# SSL certificates
docker secret create ssl_cert /path/to/hospital.crt
docker secret create ssl_key /path/to/hospital.key

# External service credentials
echo "your_twilio_sid" | docker secret create twilio_sid -
echo "your_twilio_token" | docker secret create twilio_token -
echo "your_slack_token" | docker secret create slack_token -
echo "your_slack_signing_secret" | docker secret create slack_signing -
echo "your_agentops_key" | docker secret create agentops_api_key -
```

### Volume Encryption

**LUKS Encryption** (recommended for PHI data):

```bash
# Create encrypted volume for medical data
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup luksOpen /dev/sdb1 vigia_medical
sudo mkfs.ext4 /dev/mapper/vigia_medical
sudo mount /dev/mapper/vigia_medical /var/lib/vigia
```

### Network Security

**Firewall Rules** (ufw example):

```bash
# Allow SSH (hospital network only)
sudo ufw allow from 10.0.0.0/8 to any port 22

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow HTTP (redirect only)
sudo ufw allow 80/tcp

# Management interface (admin network only)
sudo ufw allow from 172.22.0.0/16 to any port 8443

# Deny all other traffic
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

## 📊 Monitoring & Observability

### Health Checks

**Service Health Endpoints**:
- Main API: `https://vigia.hospital.local/health`
- Database: Internal PostgreSQL health check
- Redis: Internal cache health check
- Celery: Worker queue monitoring

**Custom Monitoring**:

```bash
# Medical-specific metrics
curl -s https://vigia.hospital.local/api/metrics | grep lpp_detection_
curl -s https://vigia.hospital.local/api/metrics | grep medical_session_
curl -s https://vigia.hospital.local/api/metrics | grep audit_events_
```

### Alerting

**Critical Alerts**:
- LPP Grade 3-4 detections (immediate)
- System failures (5 minutes)
- Security breaches (immediate)
- Audit trail failures (immediate)

**Configuration** (Prometheus AlertManager):

```yaml
groups:
- name: vigia_medical
  rules:
  - alert: CriticalLPPDetection
    expr: lpp_detection_grade >= 3
    for: 0s
    labels:
      severity: critical
    annotations:
      summary: "Critical pressure injury detected"
      
  - alert: MedicalSystemDown
    expr: up{job="vigia-detection"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Vigia medical system is down"
```

## 💾 Backup & Recovery

### Automated Backups

**Schedule**: Every 6 hours
**Retention**: 90 days local, 7 years offsite
**Encryption**: AES-256 with hospital keys

**Backup Components**:
- PostgreSQL database (point-in-time recovery)
- Medical images (encrypted)
- Configuration files
- SSL certificates
- Audit logs

**Manual Backup**:

```bash
# Create immediate backup
./scripts/hospital-deploy.sh backup

# Restore from backup
docker-compose -f docker-compose.hospital.yml exec vigia-backup restore-backup.sh 2024-01-15
```

### Disaster Recovery

**RTO**: 4 hours (Recovery Time Objective)
**RPO**: 6 hours (Recovery Point Objective)

**Recovery Steps**:
1. Provision new hardware/cloud instance
2. Restore encrypted volumes
3. Deploy containers with same configuration
4. Restore database from backup
5. Verify system integrity
6. Resume medical operations

## 🔄 Maintenance

### Updates

**Security Updates** (monthly):

```bash
# Update base images
docker-compose -f docker-compose.hospital.yml pull

# Rolling update (zero downtime)
./scripts/hospital-deploy.sh update
```

**Medical Model Updates**:

```bash
# Download new model version
wget https://models.vigia.ai/lpp_detection_v2024.2.pt -O models/lpp_detection/

# Update model version in environment
sed -i 's/LPP_MODEL_VERSION=2024.1/LPP_MODEL_VERSION=2024.2/' .env.hospital

# Restart detection service
docker-compose -f docker-compose.hospital.yml restart vigia-detection
```

### Log Rotation

**Medical Audit Logs** (7-year retention):

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/vigia-medical <<EOF
/var/lib/vigia/audit/*.log {
    daily
    rotate 2555
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 🏥 Hospital Integration

### HIS Integration

**HL7/FHIR Support**:

```yaml
# Add to docker-compose.hospital.yml
vigia-hl7-gateway:
  image: vigia/hl7-gateway:latest
  environment:
    HIS_ENDPOINT: https://his.hospital.local/api
    HL7_VERSION: 2.5
    FHIR_VERSION: R4
  networks:
    - internal
```

### PACS Integration

**DICOM Support**:

```yaml
vigia-dicom-gateway:
  image: vigia/dicom-gateway:latest
  ports:
    - "11112:11112"  # DICOM port
  volumes:
    - medical_images:/app/dicom
  environment:
    PACS_HOST: pacs.hospital.local
    PACS_PORT: 11112
```

### Active Directory

**LDAP Authentication**:

```yaml
vigia-ldap-connector:
  image: vigia/ldap-connector:latest
  environment:
    LDAP_HOST: ldap.hospital.local
    LDAP_BASE_DN: dc=hospital,dc=local
    LDAP_BIND_DN: cn=vigia,ou=services,dc=hospital,dc=local
    LDAP_BIND_PASSWORD_FILE: /run/secrets/ldap_password
```

## 📞 Support & Troubleshooting

### Common Issues

**Database Connection Failures**:

```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.hospital.yml logs vigia-postgres

# Test connection
docker-compose -f docker-compose.hospital.yml exec vigia-postgres psql -U vigia_user -d vigia_medical -c "SELECT 1;"
```

**SSL Certificate Issues**:

```bash
# Verify certificate
openssl x509 -in /etc/vigia/ssl/vigia.crt -text -noout

# Test SSL connection
curl -I -k https://vigia.hospital.local
```

**Performance Issues**:

```bash
# Check resource usage
docker stats

# Medical processing metrics
curl -s https://vigia.hospital.local/api/metrics | grep -E "(processing_time|queue_size)"
```

### Log Analysis

**Medical Audit Trail**:

```bash
# Search for specific patient
grep "patient_code:JC-2025-001" /var/lib/vigia/audit/medical_audit.log

# Find LPP detections
grep "lpp_detection" /var/lib/vigia/audit/medical_audit.log | jq .

# Security events
grep "security_event" /var/lib/vigia/audit/system_events.log
```

### Emergency Procedures

**System Failure**:

1. **Assessment**: Check service status
2. **Isolation**: Stop affected services
3. **Recovery**: Restore from backup if needed
4. **Validation**: Verify medical data integrity
5. **Communication**: Notify medical staff
6. **Documentation**: Record incident for audit

**Security Incident**:

1. **Immediate**: Isolate affected systems
2. **Assessment**: Determine scope of breach
3. **Containment**: Stop further damage
4. **Recovery**: Restore from clean backups
5. **Reporting**: Notify hospital security team
6. **Investigation**: Forensic analysis

## 📋 Compliance Checklist

### HIPAA Compliance

- ✅ PHI encryption at rest and in transit
- ✅ Access controls and authentication
- ✅ Audit logging of all PHI access
- ✅ User access management
- ✅ Breach notification procedures
- ✅ Risk assessment documentation
- ✅ Staff training requirements

### ISO 13485 (Medical Devices)

- ✅ Quality management system
- ✅ Medical device software lifecycle
- ✅ Risk management (ISO 14971)
- ✅ Clinical evaluation
- ✅ Post-market surveillance
- ✅ Corrective and preventive actions

### SOC2 Type II

- ✅ Security controls
- ✅ Availability monitoring
- ✅ Processing integrity
- ✅ Confidentiality protection
- ✅ Privacy controls

## 📞 Contact Information

**Technical Support**:
- Email: support@vigia.ai
- Phone: +1-555-VIGIA-AI
- Emergency: +1-555-VIGIA-ER (24/7)

**Hospital IT Team**:
- Deployment Lead: [Your Name]
- Security Contact: [Security Officer]
- Medical Director: [Medical Director]

---

**Document Version**: 1.3.1
**Last Updated**: 2024-01-15
**Next Review**: 2024-04-15

*This document contains confidential information. Distribution restricted to authorized hospital personnel only.*