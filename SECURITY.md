# Security Guide - Vigia Medical AI System

## Recent Security Fix

**Issue**: GitGuardian detected a hardcoded secret key in `vigia_detect/a2a/base_infrastructure.py:186`

**Fix Applied**: 
- Removed hardcoded `"vigia_a2a_secret_key"` 
- Implemented environment variable `VIGIA_A2A_SECRET_KEY`
- Added automatic secure key generation with warnings for development
- Created `.env.example` with all required environment variables

## Environment Variables Setup

### Required for Production

```bash
# Generate a secure A2A secret key
VIGIA_A2A_SECRET_KEY=$(openssl rand -hex 32)

# Generate JWT secret key  
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Generate Fernet encryption key (for PHI data)
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### Complete Environment Setup

1. Copy the example file:
```bash
cp .env.example .env
```

2. Update all placeholders with actual values
3. Never commit `.env` files to version control

## Security Best Practices

### Authentication & Authorization
- Use environment variables for all secrets
- Rotate keys every 90 days in production
- Implement proper JWT token expiration
- Use secure random key generation

### Medical Data (PHI) Protection
- All PHI data is encrypted using Fernet encryption
- Keys are never hardcoded
- Compliance with HIPAA and MINSAL regulations
- Audit trails for all PHI access

### A2A Communication Security
- JWT tokens for agent authentication
- Encrypted payloads for medical data
- Rate limiting and audit logging
- Secure communication channels only

## Monitoring & Alerts

- GitGuardian integration for secret detection
- AgentOps for runtime monitoring
- Custom security alerts in Slack
- Audit logs for compliance

## Emergency Response

If secrets are compromised:
1. Immediately rotate all affected keys
2. Review audit logs for unauthorized access
3. Notify security team and compliance officer
4. Update documentation and incident response

## Compliance Certifications

- HIPAA compliant
- ISO 13485 medical device standards
- SOC2 Type II controls
- MINSAL (Chile) healthcare regulations