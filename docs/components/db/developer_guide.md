# LPP-Detect: Guía para Desarrolladores - Base de Datos

## Introducción

Esta guía proporciona la información necesaria para que los desarrolladores puedan trabajar con la base de datos del sistema LPP-Detect. Incluye detalles sobre la estructura de la base de datos, consultas comunes, y buenas prácticas para interactuar con la base de datos.

## Conexión a la Base de Datos

### Configuración de Entorno

Para conectar a la base de datos, deberá configurar las siguientes variables de entorno:

```
SUPABASE_URL=https://jfcwziciqdmhodozowhv.supabase.co
SUPABASE_KEY=tu_clave_api_supabase
```

Nunca incluya estas credenciales directamente en el código. Utilice un archivo `.env` o variables de entorno del sistema.

### Ejemplo de Conexión con Python

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales de Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Crear cliente Supabase
supabase: Client = create_client(supabase_url, supabase_key)

# Ejemplo: obtener pacientes
response = supabase.table("clinical_data.patients").select("*").execute()
patients = response.data
```

### Ejemplo de Conexión con JavaScript

```javascript
import { createClient } from '@supabase/supabase-js'

// Obtener credenciales de Supabase (desde variables de entorno)
const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY

// Crear cliente Supabase
const supabase = createClient(supabaseUrl, supabaseKey)

// Ejemplo: obtener pacientes
const { data: patients, error } = await supabase
  .from('clinical_data.patients')
  .select('*')

if (error) console.error('Error:', error)
else console.log('Patients:', patients)
```

## Consultas Comunes

### Obtener Pacientes con Riesgo

```sql
SELECT 
  p.id, 
  p.patient_code,
  p.age_range,
  p.mobility_status,
  a.braden_score,
  a.norton_score,
  a.emina_score
FROM
  clinical_data.patients p
JOIN
  clinical_data.patient_assessments a ON p.id = a.patient_id
WHERE
  a.braden_score < 15 OR
  a.norton_score < 14 OR
  a.emina_score > 8
ORDER BY
  a.braden_score ASC;
```

### Obtener Detecciones con Imágenes y Validación Médica

```sql
SELECT 
  d.id as detection_id,
  i.file_path,
  d.lpp_stage,
  d.confidence_score,
  v.validated_stage,
  v.validation_score,
  (v.validated_stage = d.lpp_stage) as is_match,
  p.patient_code,
  m.staff_code as validator
FROM
  ml_operations.lpp_detections d
JOIN
  ml_operations.lpp_images i ON d.image_id = i.id
LEFT JOIN
  ml_operations.medical_validations v ON d.id = v.detection_id
JOIN
  clinical_data.patients p ON i.patient_id = p.id
LEFT JOIN
  staff_data.medical_staff m ON v.validator_id = m.id
ORDER BY
  d.created_at DESC;
```

### Obtener Planes de Cuidado Activos

```sql
SELECT 
  c.id as care_plan_id,
  p.patient_code,
  c.intervention_type,
  c.recommendations,
  c.follow_up_days,
  c.created_at,
  c.created_at + (c.follow_up_days || ' days')::interval as follow_up_date,
  c.status,
  m.staff_code as created_by
FROM
  clinical_data.care_plans c
JOIN
  clinical_data.patients p ON c.patient_id = p.id
LEFT JOIN
  staff_data.medical_staff m ON c.created_by = m.id
WHERE
  c.status = 'active'
ORDER BY
  follow_up_date ASC;
```

### Obtener Estadísticas de Detección

```sql
SELECT
  d.lpp_stage,
  COUNT(*) as total_detections,
  AVG(d.confidence_score) as avg_confidence,
  COUNT(v.id) as validated_count,
  COUNT(CASE WHEN v.validated_stage = d.lpp_stage THEN 1 END) as correct_count,
  COUNT(CASE WHEN v.validated_stage = d.lpp_stage THEN 1 END)::float / 
    NULLIF(COUNT(v.id), 0) as accuracy
FROM
  ml_operations.lpp_detections d
LEFT JOIN
  ml_operations.medical_validations v ON d.id = v.detection_id
GROUP BY
  d.lpp_stage
ORDER BY
  d.lpp_stage;
```

## Operaciones CRUD Comunes

### Insertar un Nuevo Paciente

```sql
INSERT INTO clinical_data.patients (
  patient_code, 
  age_range, 
  gender, 
  risk_factors, 
  mobility_status
) VALUES (
  'PAT999',
  '61-80',
  'female',
  '{"diabetes": true, "hipertension": false}',
  'movilidad reducida'
)
RETURNING id;
```

### Registrar una Nueva Imagen

```sql
INSERT INTO ml_operations.lpp_images (
  patient_id,
  file_path,
  file_hash,
  image_type,
  body_location,
  metadata
) VALUES (
  '123e4567-e89b-12d3-a456-426614174000',  -- ID del paciente
  '/data/images/original/PAT001_sample2.jpg',
  'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
  'original',
  'sacro',
  '{"width": 1280, "height": 960, "device": "smartphone"}'
)
RETURNING id;
```

### Actualizar una Validación Médica

```sql
UPDATE ml_operations.medical_validations
SET 
  validated_stage = 2,
  validation_notes = 'Revisado nuevamente, es etapa 2 no etapa 3',
  validation_score = 4
WHERE
  id = '123e4567-e89b-12d3-a456-426614174000';  -- ID de la validación
```

### Actualizar Estado de Plan de Cuidado

```sql
UPDATE clinical_data.care_plans
SET 
  status = 'completed',
  updated_at = NOW()
WHERE
  id = '123e4567-e89b-12d3-a456-426614174000';  -- ID del plan de cuidado
```

## Buenas Prácticas

### Seguridad

1. **Nunca concatene valores directamente en consultas SQL**. Utilice parámetros para evitar inyecciones SQL.
2. **Evite SELECT * en producción**. Seleccione solo las columnas que necesita.
3. **Utilice transacciones** para operaciones que involucren múltiples tablas.
4. **No exponga identificadores de base de datos reales** a los usuarios finales.

### Rendimiento

1. **Utilice los índices existentes** en sus consultas para optimizar el rendimiento.
2. **Limite los resultados** para consultas grandes, utilizando paginación cuando sea necesario.
3. **Considere el uso de vistas materializadas** para consultas complejas y frecuentes.
4. **Monitoree el rendimiento** de sus consultas en producción.

### Integridad de Datos

1. **Valide los datos antes de insertarlos** en la base de datos, no confíe solo en las restricciones de la base de datos.
2. **Respete las relaciones y restricciones** definidas en el esquema.
3. **Maneje correctamente los valores NULL** cuando sea necesario.
4. **Utilice tipos de datos adecuados** para cada campo.

## Interacción con Campos JSONB

PostgreSQL (usado por Supabase) ofrece operadores avanzados para trabajar con campos JSONB. Aquí hay algunos ejemplos útiles:

### Consultar por Valor de Campo JSONB

```sql
-- Pacientes con diabetes
SELECT * FROM clinical_data.patients
WHERE risk_factors->>'diabetes' = 'true';
```

### Actualizar Campo dentro de JSONB

```sql
-- Actualizar un campo dentro del JSONB
UPDATE clinical_data.patients
SET risk_factors = risk_factors || '{"hipertension": true}'::jsonb
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

### Filtrar por Existencia de Clave

```sql
-- Pacientes que tienen registrada información sobre malnutrición
SELECT * FROM clinical_data.patients
WHERE risk_factors ? 'malnutricion';
```

## Cumplimiento Normativo

Asegúrese de seguir estas prácticas para cumplir con las normativas de datos médicos:

1. **No almacene datos identificativos directos** de pacientes (nombre, RUT, etc.) en texto plano.
2. **Registre todas las acciones críticas** en `audit_logs.system_logs`.
3. **Respete las políticas RLS** establecidas para cada tabla.
4. **Nunca comparta credenciales de acceso** entre usuarios.
5. **Para exportación de datos**, asegúrese de anonimizar adecuadamente según la normativa GDPR/HIPAA.

## Manejo de Errores Comunes

### Error: Row-Level Security Violation

Si obtiene el error "new row violates row-level security policy", verifique:
- El usuario tiene el rol correcto para la operación
- Las políticas RLS aplicadas a esa tabla permiten la operación
- Los datos que intenta insertar/actualizar cumplen con las condiciones WITH CHECK

### Error: Violación de Restricción de Integridad

Si obtiene un error relacionado con restricciones:
- Verifique que las claves foráneas existan antes de insertar referencias
- Asegúrese de que los valores están dentro de los rangos permitidos por los CHECK
- Confirme que los datos cumplen con las restricciones UNIQUE

## Migración a FHIR Completo

En el futuro, el esquema evolucionará hacia una compatibilidad total con FHIR. Tenga en cuenta estas consideraciones para facilitar la migración:

1. Utilice los campos ya definidos de manera consistente con sus equivalentes FHIR:
   - `patients` ↔ `Patient`
   - `patient_assessments` ↔ `Observation`
   - `care_plans` ↔ `CarePlan`
   - `lpp_images` ↔ `Media`

2. Evite agregar campos personalizados que no tengan equivalente en FHIR.

3. Cuando necesite ampliar el esquema, consulte primero la especificación FHIR para mantener la compatibilidad.

## Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Especificación FHIR](https://www.hl7.org/fhir/)
- [Documentación sobre Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

## Contacto para Soporte

Para problemas relacionados con la base de datos, contacte al equipo de Bases de Datos a través de:
- Slack: #lpp-detect-db
- Email: db-support@lppdetect.org
