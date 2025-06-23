# 🚀 GUÍA DE SETUP - SERVICIOS PENDIENTES VIGIA

## ✅ ESTADO ACTUAL VERIFICADO

### **SERVICIOS OPERATIVOS:**
- ✅ **Redis**: Completamente funcional (localhost:6379)
- ✅ **Supabase**: Configurado con credenciales reales
- ✅ **MedGemma**: Ollama funcionando con modelo `alibayram/medgemma:latest`
- ✅ **Anthropic Claude**: API key configurada y operativa
- ✅ **Slack**: Token funcional consolidado en .env principal

### **SERVICIOS PENDIENTES:**
- 🔴 **Twilio (WhatsApp)**: Necesita cuenta y credenciales reales

### **SERVICIOS CONFIGURADOS:**
- ✅ **Hume AI**: API key configurada y lista para análisis de voz

---

## 🔴 SETUP CRÍTICO: TWILIO WHATSAPP

### **Paso 1: Crear Cuenta Twilio**
```bash
# 1. Ir a: https://console.twilio.com
# 2. Crear cuenta gratuita
# 3. Verificar teléfono
# 4. Obtener $15 USD crédito inicial
```

### **Paso 2: Configurar WhatsApp Sandbox (Desarrollo)**
```bash
# 1. En Twilio Console -> Messaging -> Try it out -> Send a WhatsApp message
# 2. Seguir instrucciones para conectar tu WhatsApp al sandbox
# 3. Enviar mensaje "join [sandbox-name]" al número +1 415 523 8886
# 4. Configurar webhook URL (ngrok para desarrollo local)
```

### **Paso 3: Obtener Credenciales**
En Twilio Console, copiar:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886  # Sandbox number
```

### **Paso 4: Actualizar .env**
```bash
# Reemplazar en /Users/autonomos_dev/Projects/vigia/.env:
TWILIO_ACCOUNT_SID=YOUR_REAL_ACCOUNT_SID
TWILIO_AUTH_TOKEN=YOUR_REAL_AUTH_TOKEN
```

### **Paso 5: Configurar Webhook (Desarrollo)**
```bash
# Instalar ngrok para túnel local
brew install ngrok

# Crear túnel para puerto 5000 (WhatsApp server)
ngrok http 5000

# Copiar HTTPS URL y configurar en Twilio Console:
# Messaging -> Settings -> WhatsApp sandbox settings
# Webhook URL: https://abc123.ngrok.io/slack/events
```

---

## 🟡 SETUP RECOMENDADO: HUME AI

### **Paso 1: Crear Cuenta Hume AI**
```bash
# 1. Ir a: https://dev.hume.ai
# 2. Sign up / Login
# 3. Crear nuevo proyecto
# 4. Obtener API key
```

### **Paso 2: Configurar API Key**
```bash
# En .env, reemplazar:
HUME_API_KEY=YOUR_REAL_HUME_API_KEY
VOICE_ANALYSIS_ENABLED=true
```

### **Paso 3: Verificar Funcionalidad**
```python
# Test básico en Python:
from vigia_detect.ai.hume_ai_client import create_hume_ai_client
client = create_hume_ai_client()
# Si no hay errores, está configurado correctamente
```

---

## 🧪 VALIDACIÓN END-TO-END

### **Test Completo del Sistema**
```bash
# 1. Verificar Redis
redis-cli ping  # Debe responder PONG

# 2. Test MedGemma
echo "What is Stage 2 pressure ulcer?" | ollama run alibayram/medgemma:latest

# 3. Test Slack (una vez configurado Twilio)
python vigia_detect/agents/medical_team_agent.py

# 4. Test WhatsApp (una vez configurado Twilio)
python vigia_detect/agents/patient_communication_agent.py

# 5. Test completo Bruce Wayne case
python test_bruce_wayne_case.py
```

---

## 📋 CHECKLIST DE CONFIGURACIÓN

### **Pre-Deployment:**
- [ ] Twilio account creada
- [ ] WhatsApp sandbox configurado
- [ ] Webhook URL configurada (ngrok para dev)
- [ ] Hume AI API key obtenida
- [ ] Todas las API keys actualizadas en .env

### **Post-Configuration:**
- [ ] Test individual de cada servicio
- [ ] Validación de comunicación WhatsApp
- [ ] Test de análisis de voz Hume AI
- [ ] Test end-to-end Bruce Wayne case
- [ ] Verificación de logs de auditoría

---

## 🎯 PRIORIDADES DE IMPLEMENTACIÓN

### **INMEDIATO (Critical Path):**
1. **Twilio Setup** - Sin esto no hay comunicación con pacientes
2. **Validación WhatsApp** - Core del sistema de comunicación

### **SIGUIENTE (Enhanced Functionality):**
3. **Hume AI Setup** - Mejora análisis con voz (0.85 → 0.93 confidence)
4. **Test End-to-End** - Validación completa del flujo médico

### **OPCIONAL (Future Enhancement):**
5. **Producción WhatsApp** - Número real vs sandbox
6. **Monitoring Setup** - Prometheus + Grafana
7. **Hospital Deployment** - Docker production setup

---

## 🏥 NOTAS IMPORTANTES

### **Desarrollo vs Producción:**
- **Desarrollo**: Usar Twilio sandbox (gratis, limitado)
- **Producción**: Necesita número WhatsApp Business ($$ mensual)

### **Costos Estimados:**
- **Twilio Sandbox**: Gratis para desarrollo
- **Hume AI**: Free tier disponible
- **Twilio Production**: ~$20-50/mes dependiendo uso
- **Total Desarrollo**: $0 (todo gratis para testing)

### **Seguridad:**
- Todas las API keys deben estar en `.env` (no commitear)
- Usar webhooks HTTPS únicamente
- Validar signatures de Twilio/Slack

---

**🎖️ RESULTADO ESPERADO**: Con Twilio configurado tendrás un sistema médico 100% funcional con comunicación bidireccional WhatsApp ↔ Slack, análisis LPP con MONAI/YOLOv5, y AI médico con MedGemma local.

*Tiempo estimado de setup: 30-45 minutos para Twilio + 15 minutos para Hume AI*