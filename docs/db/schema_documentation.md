# LPP-Detect: Documentación de Base de Datos

## Información General

- **Proyecto**: vigia_detect
- **Referencia ID**: jfcwziciqdmhodozowhv
- **Región**: South America (São Paulo)
- **Fecha de creación**: 2025-05-21
- **Organización ID**: cklrbqpounsoeajoxigh

## Estructura General

La base de datos está estructurada en cuatro esquemas separados, cada uno con un propósito específico:

1. **clinical_data**: Datos clínicos de pacientes, historial médico y planes de cuidado
2. **staff_data**: Información del personal médico y administrativo
3. **ml_operations**: Operaciones de machine learning, imágenes y detecciones
4. **audit_logs**: Registros de auditoría para cumplimiento normativo

## Detalle de Esquemas y Tablas

### Esquema: clinical_data

#### Tabla: patients
**Descripción**: Información básica de pacientes (anonimizada para HIPAA/GDPR)

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| patient_code | TEXT | Código único del paciente | UNIQUE NOT NULL |
| age_range | TEXT | Rango de edad | CHECK (age_range IN ('0-18', '19-40', '41-60', '61-80', '81+')) |
| gender | TEXT | Género | CHECK (gender IN ('male', 'female', 'other')) |
| risk_factors | JSONB | Factores de riesgo como diabetes, hipertensión, etc. | |
| mobility_status | TEXT | Estado de movilidad | |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | Fecha de actualización | DEFAULT NOW() |

#### Tabla: patient_assessments
**Descripción**: Evaluaciones de riesgo de LPP usando escalas estándar

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| patient_id | UUID | Referencia al paciente | NOT NULL, REFERENCES patients(id) ON DELETE CASCADE |
| assessment_date | TIMESTAMPTZ | Fecha de evaluación | DEFAULT NOW() |
| braden_score | SMALLINT | Escala Braden (bajo = mayor riesgo) | |
| norton_score | SMALLINT | Escala Norton (bajo = mayor riesgo) | |
| emina_score | SMALLINT | Escala Emina (alto = mayor riesgo) | |
| additional_data | JSONB | Datos específicos de la evaluación | |
| assessor_id | UUID | Referencia al personal que realizó la evaluación | |
| notes | TEXT | Notas adicionales | |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |

#### Tabla: care_plans
**Descripción**: Planes de cuidado basados en protocolos MINSAL para prevención y tratamiento de LPP

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| patient_id | UUID | Referencia al paciente | NOT NULL, REFERENCES patients(id) ON DELETE CASCADE |
| detection_id | UUID | Referencia a la detección que originó el plan | REFERENCES vigia_detections(id) |
| intervention_type | TEXT | Tipo de intervención | NOT NULL |
| recommendations | TEXT | Recomendaciones específicas | NOT NULL |
| follow_up_days | SMALLINT | Días para seguimiento | |
| status | TEXT | Estado del plan | CHECK (status IN ('active', 'completed', 'cancelled')) |
| created_by | UUID | Referencia al personal que creó el plan | REFERENCES medical_staff(id) |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | Fecha de actualización | DEFAULT NOW() |

### Esquema: staff_data

#### Tabla: medical_staff
**Descripción**: Personal médico y administrativo con acceso al sistema

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| staff_code | TEXT | Código único de personal | UNIQUE NOT NULL |
| role | TEXT | Rol en el sistema | NOT NULL, CHECK (role IN ('doctor', 'nurse', 'technician', 'admin')) |
| specialties | TEXT[] | Especialidades médicas | |
| active | BOOLEAN | Indica si el personal está activo | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | Fecha de actualización | DEFAULT NOW() |

### Esquema: ml_operations

#### Tabla: lpp_images
**Descripción**: Imágenes de lesiones por presión (LPP) para procesamiento ML

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| patient_id | UUID | Referencia al paciente | NOT NULL, REFERENCES patients(id) ON DELETE CASCADE |
| file_path | TEXT | Ruta al archivo | NOT NULL |
| file_hash | TEXT | Hash SHA-256 para garantizar integridad | NOT NULL |
| image_type | TEXT | Tipo de imagen | NOT NULL, CHECK (image_type IN ('original', 'preprocessed', 'annotated')) |
| body_location | TEXT | Ubicación en el cuerpo | |
| metadata | JSONB | Metadatos adicionales | |
| upload_date | TIMESTAMPTZ | Fecha de carga | DEFAULT NOW() |

#### Tabla: models
**Descripción**: Registro de modelos de machine learning usados para detección de LPP

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| model_name | TEXT | Nombre del modelo | NOT NULL |
| model_version | TEXT | Versión del modelo | NOT NULL |
| model_type | TEXT | Tipo de modelo | NOT NULL |
| model_path | TEXT | Ruta al archivo del modelo | NOT NULL |
| active | BOOLEAN | Indica si el modelo está activo | DEFAULT TRUE |
| parameters | JSONB | Parámetros del modelo | |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |
| | | | UNIQUE (model_name, model_version) |

#### Tabla: vigia_detections
**Descripción**: Detecciones de LPP realizadas por modelos de ML

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| image_id | UUID | Referencia a la imagen | NOT NULL, REFERENCES lpp_images(id) ON DELETE CASCADE |
| model_id | UUID | Referencia al modelo | NOT NULL, REFERENCES models(id) |
| detection_results | JSONB | Bounding boxes, scores, clases | NOT NULL |
| lpp_stage | SMALLINT | Etapa de LPP (0-4) | CHECK (lpp_stage BETWEEN 0 AND 4) |
| confidence_score | REAL | Confianza de la detección | CHECK (confidence_score BETWEEN 0 AND 1) |
| processing_time_ms | INTEGER | Tiempo de procesamiento en ms | |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |

#### Tabla: medical_validations
**Descripción**: Validaciones médicas de las detecciones automáticas de LPP

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| detection_id | UUID | Referencia a la detección | NOT NULL, REFERENCES vigia_detections(id) ON DELETE CASCADE |
| validator_id | UUID | Referencia al validador | NOT NULL, REFERENCES medical_staff(id) |
| validated_stage | SMALLINT | Etapa confirmada por médico | CHECK (validated_stage BETWEEN 0 AND 4) |
| validation_notes | TEXT | Notas adicionales | |
| validation_score | SMALLINT | Puntuación de precisión (1-5) | CHECK (validation_score BETWEEN 1 AND 5) |
| validated_at | TIMESTAMPTZ | Fecha de validación | DEFAULT NOW() |

### Esquema: audit_logs

#### Tabla: system_logs
**Descripción**: Registro de auditoría para cumplimiento normativo

| Columna | Tipo | Descripción | Restricciones |
|---------|------|-------------|---------------|
| id | UUID | Identificador único | PRIMARY KEY, DEFAULT gen_random_uuid() |
| event_type | TEXT | Tipo de evento | NOT NULL |
| entity_type | TEXT | Tipo de entidad | NOT NULL |
| entity_id | UUID | ID de la entidad relacionada | |
| user_id | UUID | ID del usuario que realizó la acción | |
| ip_address | TEXT | Dirección IP | |
| details | JSONB | Detalles adicionales | |
| created_at | TIMESTAMPTZ | Fecha de creación | DEFAULT NOW() |

## Funciones y Triggers

### Función: update_updated_at
**Propósito**: Actualiza automáticamente el campo updated_at al valor actual cuando se modifica un registro

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Triggers
1. **set_updated_at_patients**: Actualiza updated_at en tabla patients
2. **set_updated_at_medical_staff**: Actualiza updated_at en tabla medical_staff
3. **set_updated_at_care_plans**: Actualiza updated_at en tabla care_plans

## Índices

1. **idx_patient_code**: clinical_data.patients(patient_code)
2. **idx_patient_assessments_patient_id**: clinical_data.patient_assessments(patient_id)
3. **idx_lpp_images_patient_id**: ml_operations.lpp_images(patient_id)
4. **idx_vigia_detections_image_id**: ml_operations.vigia_detections(image_id)
5. **idx_vigia_detections_model_id**: ml_operations.vigia_detections(model_id)
6. **idx_medical_validations_detection_id**: ml_operations.medical_validations(detection_id)
7. **idx_care_plans_patient_id**: clinical_data.care_plans(patient_id)
8. **idx_care_plans_detection_id**: clinical_data.care_plans(detection_id)
9. **idx_system_logs_event_type**: audit_logs.system_logs(event_type)
10. **idx_system_logs_entity_type**: audit_logs.system_logs(entity_type)

## Seguridad

Todas las tablas tienen habilitado Row Level Security (RLS), lo que permite un control granular de acceso a nivel de fila:

```sql
ALTER TABLE clinical_data.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_data.patient_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_data.care_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_data.medical_staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.lpp_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.models ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.vigia_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.medical_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs.system_logs ENABLE ROW LEVEL SECURITY;
```

> Nota: Las políticas específicas de RLS serán configuradas posteriormente según los roles y permisos requeridos.

## Comandos de Implementación

Los siguientes comandos fueron utilizados para implementar la base de datos:

```bash
# Crear proyecto Supabase
supabase projects create vigia_detect --org-id cklrbqpounsoeajoxigh

# Vincular proyecto local con Supabase
cd /Users/autonomos_dev/Projects/pressure/vigia_detect
supabase link --project-ref jfcwziciqdmhodozowhv

# Crear archivo de migración para el esquema
nano supabase/migrations/20250521000000_initial_schema.sql

# Aplicar la migración al proyecto Supabase
supabase db push

# Verificar el esquema aplicado
supabase db dump -f dump.sql --schema clinical_data,staff_data,ml_operations,audit_logs
```

## Diagrama Entidad-Relación

```
+---------------------+       +----------------------+       +-------------------+
| clinical_data       |       | ml_operations        |       | staff_data        |
+---------------------+       +----------------------+       +-------------------+
| patients            |<--+   | lpp_images           |       | medical_staff     |
| patient_assessments |   |   | models               |       +-------------------+
| care_plans          |   |   | vigia_detections       |               ^
+---------------------+   |   | medical_validations  |               |
                          |   +----------------------+               |
                          |             ^                            |
                          |             |                            |
                          +-------------+----------------------------+
                                        |
                                        v
                              +--------------------+
                              | audit_logs         |
                              +--------------------+
                              | system_logs        |
                              +--------------------+
```

## Consideraciones FHIR

Aunque no es completamente compatible con FHIR en esta fase, el diseño de la base de datos sigue principios similares, particularmente:

- Los pacientes tienen un identificador único y datos demográficos básicos (similar a FHIR Patient)
- Las evaluaciones se registran como observaciones (similar a FHIR Observation)
- Los planes de cuidado incluyen intervenciones y seguimiento (similar a FHIR CarePlan)
- Las imágenes tienen metadatos y referencias (similar a FHIR Media)

Esta estructura facilitará la migración a un esquema completamente compatible con FHIR en el futuro.
