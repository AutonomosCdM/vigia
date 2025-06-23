# 🔧 MATRIZ DE SERVICIOS Y CONFIGURACIÓN - SISTEMA VIGIA

## 🎯 GUÍA RÁPIDA DE CONFIGURACIÓN

Esta matriz proporciona **todos los detalles técnicos necesarios** para configurar cada servicio del sistema Vigia según el entorno de deployment.

---

## 📊 MATRIZ COMPLETA DE SERVICIOS

### **🔴 SERVICIOS CRÍTICOS (OBLIGATORIOS)**

#### **1. PostgreSQL Dual Database**
```yaml
Criticidad: 🔴 CRÍTICO
Función: Almacenamiento médico con separación PHI
Alternativas: ❌ No hay - Core architecture
```

**Hospital PHI Database:**
```yaml
Container: vigia-hospital-phi-db
Image: postgres:15-alpine
Port: 5432 (internal only)
Network: hospital_internal (no external access)
Environment:
  POSTGRES_DB: hospital_phi
  POSTGRES_USER: hospital_admin
  POSTGRES_PASSWORD_FILE: /run/secrets/hospital_db_password
Resources:
  Memory: 2GB limit, 1GB reservation
  CPU: 1.0 limit, 0.5 reservation
Volumes:
  - /var/lib/vigia/hospital_phi_data:/var/lib/postgresql/data
  - ./hospital/schemas/hospital_phi_database.sql
```

**Processing Database:**
```yaml
Container: vigia-processing-db  
Image: postgres:15-alpine
Port: 5433 (external access)
Network: processing_external + tokenization_bridge
Environment:
  POSTGRES_DB: vigia_processing
  POSTGRES_USER: vigia_admin
  POSTGRES_PASSWORD_FILE: /run/secrets/processing_db_password
Resources:
  Memory: 4GB limit, 2GB reservation
  CPU: 2.0 limit, 1.0 reservation
Volumes:
  - /var/lib/vigia/processing_data:/var/lib/postgresql/data
  - ./processing/schemas/processing_database.sql
```

#### **2. Redis Medical Cache**
```yaml
Criticidad: 🔴 CRÍTICO
Función: Cache médico semántico + vector search
Alternativas: ✅ Mock local para testing
```

**Configuración:**
```yaml
Container: vigia-redis-cache
Image: redis:7-alpine
Port: 6379
Network: processing_external
Memory: 1GB con LRU eviction
Command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 1gb --maxmemory-policy allkeys-lru
Environment Variables:
  REDIS_HOST: localhost (desarrollo) | redis-cache (producción)
  REDIS_PORT: 6379
  REDIS_PASSWORD: [CONFIGURAR VIA SECRETS]
  REDIS_DB: 0
  REDIS_SSL: false (local) | true (cloud)
  REDIS_CACHE_TTL: 3600
  REDIS_CACHE_INDEX: lpp_semantic_cache
  REDIS_VECTOR_INDEX: lpp_protocols
  REDIS_VECTOR_DIM: 768
```

#### **3. Twilio WhatsApp**
```yaml
Criticidad: 🔴 CRÍTICO
Función: Comunicación bidireccional pacientes
Alternativas: ❌ No hay - Core communication
```

**Configuración:**
```yaml
Environment Variables:
  TWILIO_ACCOUNT_SID: [ACCOUNT SID FROM TWILIO CONSOLE]
  TWILIO_AUTH_TOKEN: [AUTH TOKEN FROM TWILIO CONSOLE]
  TWILIO_WHATSAPP_FROM: whatsapp:+14155238886 (sandbox) | whatsapp:+[YOUR_NUMBER] (production)
  TWILIO_PHONE_FROM: +[YOUR_TWILIO_NUMBER]
```

**Setup Steps:**
```bash
1. Crear cuenta Twilio: https://console.twilio.com
2. Activar WhatsApp sandbox (desarrollo)
3. Solicitar número WhatsApp (producción)
4. Configurar webhook endpoint
5. Verificar signature validation
```

#### **4. Slack API**
```yaml
Criticidad: 🔴 CRÍTICO
Función: Comunicación equipos médicos
Alternativas: ❌ No hay - Medical team communication
```

**Configuración:**
```yaml
Environment Variables:
  SLACK_BOT_TOKEN: xoxb-[BOT TOKEN FROM SLACK APP]
  SLACK_APP_TOKEN: xapp-[APP TOKEN IF USING SOCKET MODE]
  SLACK_SIGNING_SECRET: [SIGNING SECRET FROM SLACK APP]
  SLACK_CHANNEL_LPP: C08KK1SRE5S (channel ID para alerts LPP)
  SLACK_CHANNEL_VIGIA: C08TJHZFVD1 (channel ID para general)
```

**Setup Steps:**
```bash
1. Crear Slack App: https://api.slack.com/apps
2. Habilitar permisos: chat:write, channels:read, groups:read
3. Instalar app en workspace
4. Copiar Bot User OAuth Token
5. Configurar Event Subscriptions (opcional)
6. Agregar bot a canales médicos
```

---

### **🟡 SERVICIOS RECOMENDADOS (FUNCIONALIDAD MEJORADA)**

#### **5. Hume AI Voice Analysis**
```yaml
Criticidad: 🟡 RECOMENDADO
Función: Análisis emocional voz + dolor
Alternativas: ✅ Mock voice analysis (confidence reducida)
```

**Configuración:**
```yaml
Environment Variables:
  HUME_API_KEY: [API KEY FROM HUME AI CONSOLE]
  HUME_API_URL: https://api.hume.ai/v0
  HUME_TIMEOUT: 30
  VOICE_ANALYSIS_ENABLED: true
```

**Setup Steps:**
```bash
1. Registrarse: https://dev.hume.ai
2. Crear proyecto
3. Obtener API key
4. Verificar límites de rate
```

**Impact sin servicio:**
- Análisis únicamente imagen (confidence 0.85 vs 0.93)
- No análisis de dolor por voz
- Reduced patient emotional context

#### **6. MedGemma Local AI**
```yaml
Criticidad: 🟡 RECOMENDADO
Función: AI médico local HIPAA-compliant
Alternativas: ✅ Anthropic Claude (external API)
```

**Configuración Ollama (Recomendado):**
```bash
# Instalación
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull symptoma/medgemma3

# Variables de entorno
MEDGEMMA_ENABLED: true
MEDGEMMA_MODEL: symptoma/medgemma3
MEDGEMMA_TEMPERATURE: 0.1
MEDGEMMA_MAX_TOKENS: 2048
```

**Configuración Google Cloud (Alternativa):**
```yaml
GOOGLE_API_KEY: [API KEY FROM GOOGLE CLOUD CONSOLE]
GOOGLE_CLOUD_PROJECT: [YOUR PROJECT ID]
VERTEX_AI_LOCATION: us-central1
```

#### **7. Anthropic Claude (AI Backup)**
```yaml
Criticidad: 🟡 RECOMENDADO
Función: AI médico backup cuando MedGemma insuficiente
Alternativas: ✅ Solo MedGemma local
```

**Configuración:**
```yaml
Environment Variables:
  ANTHROPIC_API_KEY: [API KEY FROM ANTHROPIC CONSOLE]
  ANTHROPIC_MODEL: claude-3-sonnet-20240229
```

---

### **🟢 SERVICIOS OPCIONALES (ENHANCEMENT)**

#### **8. Supabase Storage**
```yaml
Criticidad: 🟢 OPCIONAL
Función: Storage complementario específico
Alternativas: ✅ PostgreSQL local completo
```

**Configuración:**
```yaml
SUPABASE_URL: https://[PROJECT_REF].supabase.co
SUPABASE_KEY: [ANON KEY FROM SUPABASE DASHBOARD]
```

#### **9. Monitoring Stack**
```yaml
Criticidad: 🟢 OPCIONAL
Función: Prometheus + Grafana monitoring
Alternativas: ✅ Logs + health checks
```

**Prometheus:**
```yaml
Container: vigia-prometheus
Port: 9090
Config: ./monitoring/prometheus-dual.yml
```

**Grafana:**
```yaml
Container: vigia-grafana
Port: 3000
Environment:
  GF_SECURITY_ADMIN_PASSWORD_FILE: /run/secrets/grafana_admin_password
```

---

## 🏥 CONFIGURACIONES POR ENTORNO

### **🔬 DESARROLLO LOCAL**

**Servicios Mínimos:**
```yaml
✅ PostgreSQL local (single database)
✅ Redis local
✅ Mock Twilio/Slack
✅ Mock Hume AI
✅ MedGemma local o Anthropic
❌ Monitoring (logs únicamente)
```

**Docker Compose Simplificado:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: vigia_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --requirepass dev_password
```

**Environment Variables (.env.development):**
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/vigia_dev

# Redis
REDIS_HOST=localhost
REDIS_PASSWORD=dev_password

# Mock Services
USE_MOCK_SERVICES=true
TWILIO_ACCOUNT_SID=mock_sid
SLACK_BOT_TOKEN=mock_token
HUME_API_KEY=mock_key
```

### **🧪 TESTING/STAGING**

**Servicios Testing:**
```yaml
✅ PostgreSQL dual (containerized)
✅ Redis (containerized)
✅ Twilio sandbox
✅ Slack testing workspace
✅ Hume AI limited
✅ MedGemma + Anthropic backup
✅ Basic monitoring
```

**Environment Variables (.env.testing):**
```bash
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=INFO

# Dual Database
HOSPITAL_PHI_DB_URL=postgresql://hospital_admin:test_pass@localhost:5432/hospital_phi_test
VIGIA_PROCESSING_DB_URL=postgresql://vigia_admin:test_pass@localhost:5433/vigia_processing_test

# Services
TWILIO_ACCOUNT_SID=[SANDBOX SID]
SLACK_BOT_TOKEN=[TEST WORKSPACE TOKEN]
HUME_API_KEY=[LIMITED API KEY]
ANTHROPIC_API_KEY=[TEST API KEY]
```

### **🏥 PRODUCCIÓN HOSPITAL**

**Servicios Completos:**
```yaml
✅ PostgreSQL dual (enterprise)
✅ Redis cluster
✅ Twilio production
✅ Slack enterprise
✅ Hume AI production
✅ MedGemma local (privacy)
✅ Monitoring completo
✅ Security hardening
✅ Backup/Recovery
```

**Environment Variables (.env.production):**
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Security
SECRET_KEY=[STRONG RANDOM KEY]
ALLOWED_HOSTS=["hospital.domain.com"]

# Database (External Managed)
HOSPITAL_PHI_DB_URL=postgresql://[ENCRYPTED]
VIGIA_PROCESSING_DB_URL=postgresql://[ENCRYPTED]

# Services Production
TWILIO_ACCOUNT_SID=[PRODUCTION SID]
SLACK_BOT_TOKEN=[ENTERPRISE TOKEN]
HUME_API_KEY=[PRODUCTION KEY]

# Security Features
RATE_LIMIT_ENABLED=true
WEBHOOK_SECRET=[STRONG SECRET]
PHI_TOKENIZATION_JWT_SECRET=[STRONG SECRET]
```

---

## 🔐 GESTIÓN DE SECRETS

### **Desarrollo:**
```bash
# .env file
TWILIO_AUTH_TOKEN=your_dev_token
SLACK_BOT_TOKEN=your_dev_token
```

### **Docker Compose:**
```yaml
secrets:
  hospital_db_password:
    file: ./secrets/hospital_db_password.txt
  processing_db_password:
    file: ./secrets/processing_db_password.txt
  tokenization_jwt_secret:
    file: ./secrets/tokenization_jwt_secret.txt
```

### **Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: vigia-secrets
data:
  hospital-db-password: [BASE64 ENCODED]
  processing-db-password: [BASE64 ENCODED]
  twilio-auth-token: [BASE64 ENCODED]
```

### **Cloud (AWS/GCP):**
```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name vigia/twilio-auth-token

# GCP Secret Manager  
gcloud secrets create vigia-twilio-auth-token --data-file=token.txt
```

---

## ✅ CHECKLIST DE CONFIGURACIÓN

### **Pre-Deploy:**
- [ ] PostgreSQL dual databases configuradas
- [ ] Redis authentication habilitada
- [ ] Twilio account y WhatsApp número
- [ ] Slack app y bot permissions
- [ ] Secrets management configurado
- [ ] Network isolation validada

### **Post-Deploy:**
- [ ] Health checks pasando
- [ ] Database connections working
- [ ] Redis cache responding
- [ ] WhatsApp messages sending
- [ ] Slack notifications working
- [ ] PHI tokenization functional
- [ ] Monitoring dashboards active

### **Validación End-to-End:**
- [ ] Bruce Wayne case completo
- [ ] PHI → Batman tokenization
- [ ] Image analysis + voice analysis
- [ ] Medical team notifications
- [ ] Patient communication response
- [ ] Complete audit trail
- [ ] Compliance validation

---

**🎯 RESULTADO**: Con esta matriz tienes **todos los detalles técnicos** necesarios para configurar el sistema Vigia en cualquier entorno, desde desarrollo local hasta producción hospitalaria enterprise.

*Última actualización: 2025-06-23 | Guía de configuración v1.0*