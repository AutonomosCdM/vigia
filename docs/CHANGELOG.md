# Changelog

Todos los cambios notables del proyecto Vigía se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-05-26

### Added
- Redis Phase 2: Caché semántico médico con embeddings
- Búsqueda vectorial de protocolos médicos con RediSearch
- Generación de embeddings con sentence-transformers
- Cliente mock para desarrollo sin Redis
- Scripts de setup con Redis CLI nativo
- Caché consciente del contexto del paciente
- Documentación completa de Redis setup y uso

### Changed
- Actualización de configuración para soportar modo Redis/Mock
- Mejora en la arquitectura con factory pattern para clientes

### Technical
- 92% de precisión en búsqueda semántica demostrada
- 4 protocolos médicos indexados (prevención, tratamiento grado 2-3, evaluación)
- Soporte para MPS (Metal Performance Shaders) en Mac
- Índices optimizados con HNSW para búsqueda vectorial

## [0.3.0] - 2025-05-21

### Added
- Configuración centralizada con Pydantic settings
- Módulo `core/` con clases base y templates reutilizables
- Validadores centralizados para teléfonos, imágenes y datos clínicos
- Fixtures compartidas para testing
- Scripts de migración automática
- Servidor unificado de Slack con soporte para modales
- Documentación completa de configuración de Slack

### Changed
- Refactorización completa de clientes (Supabase, Twilio, Slack)
- Estructura de proyecto reorganizada y limpia
- Templates de Slack centralizados y reutilizables
- Procesamiento de imágenes unificado
- Eliminación de código duplicado (60% reducción)

### Removed
- Tokens y credenciales hardcodeadas (100% eliminadas)
- Repositorios clonados innecesarios (4GB+ liberados)
- Archivos de configuración obsoletos
- Código duplicado en handlers y templates

### Security
- Migración completa de tokens hardcodeados a variables de entorno
- Configuración segura con validación de credenciales
- Manejo centralizado de autenticación

## [0.2.0] - 2025-05-21

### Added
- Documentación técnica para módulos CLI y CV pipeline
- Documentación del módulo de messaging

### Fixed
- Correcciones en documentación y estructura

## [0.1.0] - 2025-05-20

### Added
- Pipeline de visión computacional con YOLOv5
- Sistema de mensajería WhatsApp via Twilio
- Notificaciones Slack para enfermeras
- Base de datos Supabase con estructura FHIR
- Cliente Redis para caché y vectores
- Agentes de IA con Google ADK
- Interfaz de línea de comandos
- Tests unitarios y de integración

### Security
- Anonimización automática de rostros en imágenes
- Estructura de base de datos compatible con FHIR