# Vigia Setup Guide - Sistema Médico de Producción v1.3.3

Guía unificada de configuración para el sistema médico Vigia con arquitectura ADK.

## 📋 Configuración Rápida

### 1. Configuración Inicial del Sistema

```bash
# 1. Configurar credenciales de forma segura
python scripts/setup_credentials.py
# Selecciona opción 1 y configura: Twilio, Anthropic, Supabase

# 2. Cargar credenciales en tu sesión
source scripts/quick_env_setup.sh

# 3. Instalar dependencias
pip install -r config/requirements.txt
```

### 2. Configuración MedGemma Local (IA Médica)

```bash
# Instalar Ollama y MedGemma
python scripts/setup_medgemma_ollama.py --install-ollama
python scripts/setup_medgemma_ollama.py --model 27b --install
python scripts/setup_medgemma_ollama.py --model 27b --test

# Configurar Redis con protocolos médicos
python scripts/setup_redis_simple.py

# Probar integración completa
python examples/redis_integration_demo.py
```

### 3. Validación del Sistema

```bash
# Ejecutar suite completa de pruebas
python -m pytest tests/ -m "not slow"

# Tests críticos de validación
python -m pytest tests/medical/test_minsal_integration.py -v
python -m pytest tests/adk/test_simple_adk_integration.py -v
python -m pytest tests/integration/test_async_simple.py -v

# Validación post-instalación
python scripts/validate_post_refactor_simple.py --verbose
```

## 🏥 Despliegue Hospitalario

### Opción 1: Docker Hospital-Grade (Recomendado)

```bash
# Despliegue completo en hospital
./scripts/hospital-deploy.sh deploy

# Verificar servicios
./scripts/hospital-deploy.sh status

# Ver logs del sistema
./scripts/hospital-deploy.sh logs
```

### Opción 2: Desarrollo Local

```bash
# Iniciar servicios de desarrollo
./scripts/start_celery_worker.sh               # Workers asíncronos
./start_whatsapp_server.sh                    # Webhook WhatsApp
./scripts/start_slack_server.sh               # Notificaciones Slack
```

## 💻 Requisitos del Sistema

### Para Desarrollo
- **Python**: 3.11+
- **RAM**: 8GB mínimo, 16GB recomendado
- **Almacenamiento**: 5GB libres

### Para Producción Hospitalaria
- **RAM**: 32GB+ (para MedGemma 27B)
- **GPU**: 8GB VRAM mínimo, 32GB VRAM recomendado
- **Almacenamiento**: 50GB+ libres
- **Docker**: Para despliegue hospitalario

### Verificar Requisitos
```bash
python scripts/setup_medgemma_local.py --check-only
redis-cli ping
```

## 🔐 Gestión de Credenciales

### Sistema de Keychain Seguro

```bash
# Configurar por primera vez
python scripts/setup_credentials.py

# Cargar en sesión actual
source scripts/quick_env_setup.sh
```

### Credenciales Requeridas

1. **Twilio** (WhatsApp):
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM`

2. **Supabase** (Base de datos):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

3. **Slack** (Notificaciones):
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`

4. **Redis** (Cache médico):
   - `REDIS_URL` (opcional, usa local por defecto)

## 🧪 Tests y Validación

### Estructura de Tests Organizados

```bash
# Tests por categoría (38 marcadores disponibles)
python -m pytest tests/unit/ -m unit           # Tests unitarios
python -m pytest tests/adk/ -m adk             # Tests ADK
python -m pytest tests/medical/ -m medical     # Validación médica
python -m pytest tests/integration/ -m integration  # Integración

# Tests de cumplimiento
python -m pytest tests/medical/test_minsal_integration.py -v    # 14/14 PASSED
```

### Suite Completa

```bash
# Suite Redis + MedGemma
./scripts/run_redis_medgemma_tests.sh

# Validación médica completa
python -m pytest tests/medical/ -v
```

## 🔧 Configuración Avanzada

### MCP (Model Context Protocol)

```bash
# Configurar MCP para Claude Code
python scripts/setup_mcp.py
```

### GitHub Secrets (CI/CD)

```bash
# Configurar secrets para GitHub Actions
python scripts/setup_github_secrets.py
```

### Configuración Personalizada

Editar archivos en `config/`:
- `config/.env.development` - Desarrollo local
- `config/.env.hospital` - Producción hospitalaria
- `config/pytest.ini` - Configuración de tests

## 🔍 Troubleshooting

### Problemas Comunes

1. **MedGemma no responde**:
   ```bash
   ollama ps
   ollama pull symptoma/medgemma3
   ```

2. **Redis no conecta**:
   ```bash
   redis-cli ping
   python scripts/setup_redis_simple.py
   ```

3. **Tests fallan**:
   ```bash
   python scripts/validate_post_refactor_simple.py --verbose
   ```

4. **Credenciales no cargan**:
   ```bash
   python scripts/setup_credentials.py
   source scripts/quick_env_setup.sh
   ```

## 📚 Documentación Detallada

- **[Arquitectura ADK](../architecture/)** - Sistema de agentes médicos
- **[Motor de Decisiones Médicas](../medical/)** - Evidencia científica NPUAP/EPUAP
- **[Despliegue Hospitalario](../deployment/)** - Docker multi-capa
- **[Cumplimiento Médico](../compliance/)** - HIPAA, ISO 13485, SOC2

## 🚀 Próximos Pasos

Después de la configuración:

1. **Procesar primera imagen médica**:
   ```bash
   python vigia_detect/cli/process_images_refactored.py --input /path/to/images
   ```

2. **Iniciar servidor de desarrollo**:
   ```bash
   ./scripts/start_slack_server.sh
   ```

3. **Revisar logs médicos**:
   ```bash
   tail -f logs/medical_decisions.log
   ```

---

**✅ Sistema Listo para Producción Hospitalaria** - v1.3.3 Clean Architecture