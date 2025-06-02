# Vigía - Sistema de Detección Temprana de Lesiones Por Presión

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AutonomosCdM/vigia)

Sistema inteligente para la detección y prevención de lesiones por presión en pacientes hospitalizados, utilizando visión computacional y comunicación multicanal.

## 🏥 Características Principales

- **Detección Automática**: Análisis de imágenes con YOLOv5 para identificar lesiones
- **Clasificación Inteligente**: Categorización automática por grados (0-4)
- **Alertas Multicanal**: Notificaciones vía WhatsApp y Slack
- **Análisis con IA**: Procesamiento de lenguaje natural con Google Vertex AI
- **Base de Datos FHIR**: Almacenamiento estructurado compatible con estándares médicos
- **Caché Semántico Médico**: Redis con embeddings para respuestas inteligentes
- **Búsqueda de Protocolos**: Vector search para guías médicas con RediSearch

## 🚀 Inicio Rápido

### Configuración de Credenciales (Primera vez)

```bash
# Configurar credenciales de forma segura
python scripts/setup_credentials.py
# Selecciona opción 1 y configura: Twilio, Anthropic, Supabase

# Cargar credenciales en tu sesión
source scripts/quick_env_setup.sh
```

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r vigia_detect/requirements.txt

# Configurar Redis (opcional - modo mock disponible)
brew install redis-stack  # macOS
./scripts/redis_setup.sh  # Setup automático

# Ejecutar tests
pytest tests/

# Iniciar servidor Slack (desarrollo)
./scripts/start_slack_server.sh

# Procesar imágenes
python vigia_detect/cli/process_images_refactored.py --input /path/to/images
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
- ✅ **Redis Phase 2** - Caché semántico médico implementado
- 🚧 **Redis Phase 3-4** - Búsqueda vectorial avanzada e integración completa
- 🚧 **Agentes ADK** en desarrollo

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.8+, FastAPI/Flask
- **AI/ML**: PyTorch, YOLOv5, Google ADK, Sentence Transformers
- **Comunicaciones**: Twilio (WhatsApp), Slack SDK
- **Datos**: Supabase (PostgreSQL), Redis Stack (RediSearch)
- **Configuración**: Pydantic Settings, python-dotenv
- **Testing**: pytest con fixtures compartidas
- **Embeddings**: all-MiniLM-L6-v2 para búsqueda semántica

## 📚 Documentación

- **[Gestión de Credenciales](docs/CREDENTIALS_MANAGEMENT.md)**
- **[Deployment en Render](docs/RENDER_DEPLOYMENT.md)**
- **[Guía de configuración de Slack](docs/guides/slack_setup.md)**
- **[Redis Setup Guide](docs/REDIS_SETUP.md)**
- **[Redis Phase 2 Documentation](docs/REDIS_PHASE2_DOCS.md)**
- **[Documentación técnica](docs/)**
- **[Changelog](docs/CHANGELOG.md)**
- **[Ejemplos de uso](examples/)**

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

**Actualizado**: Mayo 2025 | **Versión**: 0.4.0 | **Estado**: Redis Phase 2 implementado