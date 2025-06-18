# LPP-Detect: Índice de Documentación de Base de Datos

## Resumen

Este documento sirve como punto central de referencia para acceder a toda la documentación relacionada con la base de datos del sistema LPP-Detect. El sistema utiliza Supabase (PostgreSQL) para almacenar y gestionar datos clínicos, imágenes, detecciones de machine learning y registros de auditoría.

## Proyecto Supabase

- **Nombre del Proyecto**: vigia_detect
- **ID de Referencia**: jfcwziciqdmhodozowhv
- **Región**: South America (São Paulo)
- **URL del Proyecto**: https://jfcwziciqdmhodozowhv.supabase.co
- **Dashboard Admin**: https://supabase.com/dashboard/project/jfcwziciqdmhodozowhv

## Documentos Disponibles

### Documentación Técnica

| Documento | Descripción | Enlace |
|-----------|-------------|--------|
| Documentación del Esquema | Detalle completo de la estructura de la base de datos | [schema_documentation.md](schema_documentation.md) |
| Script SQL Completo | Script SQL para crear el esquema completo | [full_schema.sql](full_schema.sql) |
| Datos de Ejemplo | Script SQL con datos de prueba | [sample_data.sql](sample_data.sql) |
| Políticas de Acceso | Especificación de políticas RLS | [access_policies.md](access_policies.md) |
| Guía para Desarrolladores | Guía práctica para desarrolladores | [developer_guide.md](developer_guide.md) |

### Esquemas

El sistema utiliza cuatro esquemas separados para organizar los datos:

1. **clinical_data**: Almacena información de pacientes, evaluaciones y planes de cuidado
2. **staff_data**: Contiene datos del personal médico y administrativo
3. **ml_operations**: Gestiona imágenes, modelos ML y resultados de detección
4. **audit_logs**: Registra eventos del sistema para auditoría y cumplimiento

### Diagramas

![Diagrama Entidad-Relación Simplificado](er_diagram.png)

*Nota: La imagen del diagrama ER debe ser generada y colocada en la misma carpeta que este archivo.*

## Aspectos Clave

### Características de Seguridad

- **Row Level Security (RLS)**: Todas las tablas tienen RLS habilitado
- **Cifrado**: Datos sensibles cifrados a nivel de columna
- **Auditoría**: Registro completo de todas las operaciones críticas
- **Control de Acceso**: Roles con permisos específicos

### Características Técnicas

- **UUIDs**: Uso de identificadores universales para todas las claves primarias
- **JSONB**: Campos flexibles para datos dinámicos
- **Comentarios**: Documentación integrada en el esquema
- **Triggers**: Actualización automática de campos de timestamp
- **Índices**: Optimización para consultas frecuentes

### Estándares de Salud

- **Compatibilidad FHIR**: Diseño orientado a migración a FHIR
- **HIPAA/GDPR**: Estructurado para cumplimiento normativo
- **Escalas Médicas**: Soporte para Braden, Norton y Emina

## Comandos CLI Útiles

### Acceso a Supabase

```bash
# Listar proyectos
supabase projects list

# Enlazar proyecto local con proyecto Supabase
supabase link --project-ref jfcwziciqdmhodozowhv

# Aplicar migraciones
supabase db push

# Exportar esquema actual
supabase db dump -f schema_dump.sql --schema clinical_data,staff_data,ml_operations,audit_logs
```

## Notas de Implementación

### Fase Actual

El sistema se encuentra en fase de implementación inicial. Las tablas y esquemas han sido creados, pero las políticas RLS específicas aún deben ser implementadas según las necesidades exactas del proyecto.

### Próximos Pasos

1. Implementar políticas RLS detalladas
2. Crear roles y usuarios según perfiles definidos
3. Completar la carga de datos iniciales para pruebas
4. Configurar sincronización con sistema de archivos para imágenes
5. Implementar hooks para registro automático en audit_logs

## Recursos Relacionados

- [Especificación FHIR](https://www.hl7.org/fhir/)
- [Documentación de Supabase](https://supabase.com/docs)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [HIPAA Compliance](https://www.hhs.gov/hipaa/index.html)
- [GDPR](https://gdpr.eu/)

## Contacto

Para consultas relacionadas con la base de datos del proyecto LPP-Detect, contactar al equipo de Bases de Datos.
