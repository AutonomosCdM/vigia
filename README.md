# Vigía - Sistema de Detección Temprana de Lesiones Por Presión

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AutonomosCdM/vigia)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.1.0-blue)
![AI](https://img.shields.io/badge/AI-MedGemma_Local-purple)
![Cache](https://img.shields.io/badge/Cache-Redis_Semantic-red)

Sistema inteligente para la detección y prevención de lesiones por presión en pacientes hospitalizados, utilizando visión computacional, IA médica local (MedGemma) y comunicación multicanal.

## 🆕 **Nuevo en v1.1.0 - Integración MedGemma Local**
- **🤖 IA Médica Local**: MedGemma para análisis clínico sin dependencias externas
- **🗄️ Caché Semántico**: Redis con búsqueda vectorial de protocolos médicos
- **📚 Base de Conocimiento**: Protocolos LPP completos con evidencia científica
- **🧪 Suite de Pruebas**: 15 tests comprehensivos con 100% de éxito
- **🔒 Privacidad Total**: Procesamiento completamente local, cumple HIPAA

## 🏥 Características Principales

- **🤖 IA Médica Local**: MedGemma para análisis clínico sin conexión externa
- **🔍 Detección Automática**: Análisis de imágenes con YOLOv5 para identificar lesiones
- **📊 Clasificación Inteligente**: Categorización automática por grados (0-4)
- **📱 Alertas Multicanal**: Notificaciones vía WhatsApp y Slack
- **🧠 Caché Semántico**: Redis con embeddings para respuestas médicas inteligentes
- **📚 Protocolos Médicos**: Búsqueda vectorial de guías clínicas con evidencia
- **🗄️ Base de Datos FHIR**: Almacenamiento estructurado compatible con estándares médicos
- **🔒 Privacidad Completa**: Todo el procesamiento médico permanece local

## 🚀 Inicio Rápido

### Configuración Inicial

```bash
# 1. Configurar credenciales de forma segura
python scripts/setup_credentials.py
# Selecciona opción 1 y configura: Twilio, Anthropic, Supabase

# 2. Cargar credenciales en tu sesión
source scripts/quick_env_setup.sh

# 3. Instalar dependencias
pip install -r vigia_detect/requirements.txt
```

### Configuración MedGemma Local (Nuevo)

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

### Desarrollo y Testing

```bash
# Ejecutar suite completa de pruebas
./scripts/run_redis_medgemma_tests.sh

# Iniciar servidor Slack (desarrollo)
./scripts/start_slack_server.sh

# Procesar imágenes con IA local
python vigia_detect/cli/process_images_refactored.py --input /path/to/images

# Análisis de imágenes médicas con MedGemma
python examples/medgemma_image_analysis_demo.py
```

## 🔴 Redis - Caché Semántico Médico

### Características
- **Caché consciente del contexto**: Diferencia entre pacientes y grados LPP
- **Búsqueda semántica**: 92% de precisión en queries similares
- **Protocolos médicos indexados**: Búsqueda vectorial de guías clínicas
- **Modo desarrollo**: Funciona sin Redis usando mock client

### Uso
```python
from vigia_detect.redis_layer import create_redis_client

# Cliente automático (Redis real o mock)
client = create_redis_client()

# Buscar protocolos
protocols = await client.search_medical_protocols(
    "tratamiento úlcera grado 2",
    lpp_grade=2
)

# Caché con contexto médico
cached = await client.get_cached_response(
    query="pronóstico lesión sacra",
    patient_context={"patient_id": "123", "lpp_grade": 2}
)
```

## 📁 Estructura del Proyecto

```
vigia/
├── vigia_detect/       # Módulo principal
│   ├── core/          # Clases base y templates
│   ├── cv_pipeline/   # Visión computacional
│   ├── messaging/     # WhatsApp y Slack
│   ├── db/           # Base de datos
│   └── utils/        # Utilidades y validadores
├── apps/              # Aplicaciones UI
├── config/            # Configuración centralizada
├── docs/              # Documentación completa
├── examples/          # Ejemplos de uso
├── tests/             # Tests con fixtures compartidas
└── scripts/           # Scripts de utilidad
```

## 🔧 Características Técnicas

### ✅ **Refactorización Completa (v0.3.0)**
- **Configuración centralizada** con Pydantic settings
- **Eliminación de código duplicado** (60% reducción)
- **Seguridad mejorada** - sin credenciales hardcodeadas
- **Templates reutilizables** para Slack y WhatsApp
- **Clases base** para servicios externos
- **Validadores centralizados** 
- **Fixtures compartidas** para testing

### 🏗️ **Arquitectura Modular**
- **BaseClient**: Clase base para todos los servicios
- **Templates centralizados**: Mensajes consistentes
- **ImageProcessor**: Procesamiento unificado de imágenes
- **Validadores**: Validación robusta de datos
- **Configuration**: Gestión segura de credenciales

## 📋 Estado del Proyecto

- ✅ **Pipeline CV** funcionando con YOLOv5
- ✅ **Integración WhatsApp/Slack** completamente funcional
- ✅ **Base de datos Supabase** con estructura FHIR
- ✅ **Código refactorizado** y optimizado
- ✅ **Configuración centralizada** y segura
- ✅ **Integración MedGemma Local** - IA médica completamente local
- ✅ **Redis Semantic Cache** - Caché inteligente con vector search
- ✅ **Suite de Pruebas Completa** - 15 tests con 100% éxito
- ✅ **Protocolos Médicos Mejorados** - Base de conocimiento expandida
- 🚧 **Agentes de Riesgo** en desarrollo
- 🚧 **Análisis de sentimientos** para adaptación de respuestas

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11+, FastAPI/Flask
- **AI/ML**: MedGemma (local), PyTorch, YOLOv5, Sentence Transformers
- **IA Local**: Ollama, Hugging Face Transformers
- **Cache**: Redis Stack 7.0+ con vector search y semantic cache
- **Comunicaciones**: Twilio (WhatsApp), Slack SDK
- **Datos**: Supabase (PostgreSQL), Redis (cache y protocolos)
- **Configuración**: Pydantic Settings, python-dotenv
- **Testing**: pytest con mocking completo (15 tests, 100% éxito)
- **Embeddings**: Semantic similarity para cache médico

## 📚 Documentación

### 🆕 Nuevas Guías
- **[MedGemma Local Setup](docs/MEDGEMMA_LOCAL_SETUP.md)** - Configuración completa de IA local
- **[Redis + MedGemma Integration](docs/REDIS_MEDGEMMA_INTEGRATION.md)** - Integración completa
- **[Release Notes v1.1.0](docs/releases/RELEASE_NOTES_MEDGEMMA_INTEGRATION.md)** - Notas de la versión

### Documentación Existente
- **[Gestión de Credenciales](docs/CREDENTIALS_MANAGEMENT.md)**
- **[Deployment en Render](docs/RENDER_DEPLOYMENT.md)**
- **[Guía de configuración de Slack](docs/guides/slack_setup.md)**
- **[Documentación técnica](docs/)** - Arquitectura y APIs
- **[Changelog](docs/CHANGELOG.md)** - Historial de cambios
- **[Ejemplos de uso](examples/)** - Demos y casos de uso

## 🔄 Migración

Si tienes código usando la versión anterior, usa el script de migración:

```bash
# Revisar cambios (dry-run)
python scripts/migrate_to_refactored.py /path/to/code

# Aplicar cambios
python scripts/migrate_to_refactored.py /path/to/code --apply
```

## 📄 Licencia

Proyecto privado - Hospital Regional de Quilpué

---

**Actualizado**: Enero 2025 | **Versión**: 1.1.0 | **Estado**: MedGemma Local + Redis Semantic Cache