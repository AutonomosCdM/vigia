# LPP-Detect: Políticas de Acceso a Base de Datos

Este documento describe las políticas de Row Level Security (RLS) que se implementarán para proteger los datos en las distintas tablas y esquemas de la base de datos de LPP-Detect.

## Introducción

Row Level Security (RLS) es una característica de PostgreSQL que permite controlar qué filas de una tabla son visibles para determinados usuarios o roles. Esto es especialmente importante en aplicaciones médicas, donde los datos de pacientes y resultados clínicos deben estar estrictamente controlados.

## Roles de Base de Datos

Para el sistema LPP-Detect, se definen los siguientes roles:

1. **lpp_admin**: Acceso completo a todos los esquemas y tablas
2. **lpp_doctor**: Acceso a datos de pacientes, imágenes, detecciones y validaciones
3. **lpp_nurse**: Acceso limitado a datos de pacientes, evaluaciones y planes de cuidado
4. **lpp_analyst**: Acceso a datos anonimizados para análisis estadísticos
5. **lpp_app**: Rol utilizado por la aplicación para operaciones básicas

## Políticas por Esquema

### Esquema: clinical_data

#### Tabla: patients

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_patients ON clinical_data.patients
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todos los pacientes
CREATE POLICY doctor_all_patients ON clinical_data.patients
    FOR SELECT
    TO lpp_doctor
    USING (true);

-- Para enfermeros - todos los pacientes
CREATE POLICY nurse_all_patients ON clinical_data.patients
    FOR SELECT
    TO lpp_nurse
    USING (true);

-- Para analistas - datos anonimizados
CREATE POLICY analyst_patients ON clinical_data.patients
    FOR SELECT
    TO lpp_analyst
    USING (true)
    WITH CHECK (false);  -- Sin modificaciones

-- Para la aplicación - solo datos necesarios
CREATE POLICY app_patients ON clinical_data.patients
    FOR ALL
    TO lpp_app
    USING (true);
```

#### Tabla: patient_assessments

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_assessments ON clinical_data.patient_assessments
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todos los pacientes
CREATE POLICY doctor_all_assessments ON clinical_data.patient_assessments
    FOR SELECT
    TO lpp_doctor
    USING (true);

-- Para enfermeros - todos los pacientes, con actualización
CREATE POLICY nurse_all_assessments ON clinical_data.patient_assessments
    FOR ALL
    TO lpp_nurse
    USING (true);

-- Para analistas - solo lectura
CREATE POLICY analyst_assessments ON clinical_data.patient_assessments
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - solo lectura
CREATE POLICY app_assessments ON clinical_data.patient_assessments
    FOR SELECT
    TO lpp_app
    USING (true);
```

#### Tabla: care_plans

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_care_plans ON clinical_data.care_plans
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todos los planes, con actualización
CREATE POLICY doctor_all_care_plans ON clinical_data.care_plans
    FOR ALL
    TO lpp_doctor
    USING (true);

-- Para enfermeros - todos los planes, solo lectura y actualización limitada
CREATE POLICY nurse_read_care_plans ON clinical_data.care_plans
    FOR SELECT
    TO lpp_nurse
    USING (true);

CREATE POLICY nurse_update_care_plans ON clinical_data.care_plans
    FOR UPDATE
    TO lpp_nurse
    USING (status != 'completed')
    WITH CHECK (status != 'completed');

-- Para analistas - solo lectura
CREATE POLICY analyst_care_plans ON clinical_data.care_plans
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - solo lectura
CREATE POLICY app_care_plans ON clinical_data.care_plans
    FOR SELECT
    TO lpp_app
    USING (true);
```

### Esquema: staff_data

#### Tabla: medical_staff

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_staff ON staff_data.medical_staff
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - solo ver personal
CREATE POLICY doctor_view_staff ON staff_data.medical_staff
    FOR SELECT
    TO lpp_doctor
    USING (true);

-- Para enfermeros - solo ver personal
CREATE POLICY nurse_view_staff ON staff_data.medical_staff
    FOR SELECT
    TO lpp_nurse
    USING (true);

-- Para analistas - solo ver roles y especialidades, sin datos identificativos
CREATE POLICY analyst_view_staff ON staff_data.medical_staff
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - solo ver personal activo
CREATE POLICY app_view_staff ON staff_data.medical_staff
    FOR SELECT
    TO lpp_app
    USING (active = true);
```

### Esquema: ml_operations

#### Tabla: lpp_images

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_images ON ml_operations.lpp_images
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todas las imágenes
CREATE POLICY doctor_all_images ON ml_operations.lpp_images
    FOR ALL
    TO lpp_doctor
    USING (true);

-- Para enfermeros - solo ver imágenes
CREATE POLICY nurse_view_images ON ml_operations.lpp_images
    FOR SELECT
    TO lpp_nurse
    USING (true);

-- Para analistas - solo ver imágenes con filtrado
CREATE POLICY analyst_view_images ON ml_operations.lpp_images
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - lectura y escritura
CREATE POLICY app_images ON ml_operations.lpp_images
    FOR ALL
    TO lpp_app
    USING (true);
```

#### Tabla: models

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_models ON ml_operations.models
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para todos los demás roles - solo lectura
CREATE POLICY all_read_models ON ml_operations.models
    FOR SELECT
    TO lpp_doctor, lpp_nurse, lpp_analyst, lpp_app
    USING (true);
```

#### Tabla: vigia_detections

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_detections ON ml_operations.vigia_detections
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todas las detecciones
CREATE POLICY doctor_all_detections ON ml_operations.vigia_detections
    FOR ALL
    TO lpp_doctor
    USING (true);

-- Para enfermeros - solo ver detecciones
CREATE POLICY nurse_view_detections ON ml_operations.vigia_detections
    FOR SELECT
    TO lpp_nurse
    USING (true);

-- Para analistas - solo lectura con análisis estadístico
CREATE POLICY analyst_view_detections ON ml_operations.vigia_detections
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - lectura y escritura
CREATE POLICY app_detections ON ml_operations.vigia_detections
    FOR ALL
    TO lpp_app
    USING (true);
```

#### Tabla: medical_validations

```sql
-- Para acceso de administrador
CREATE POLICY admin_all_validations ON ml_operations.medical_validations
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - todas las validaciones, con creación y actualización
CREATE POLICY doctor_all_validations ON ml_operations.medical_validations
    FOR ALL
    TO lpp_doctor
    USING (true);

-- Para enfermeros - solo ver validaciones
CREATE POLICY nurse_view_validations ON ml_operations.medical_validations
    FOR SELECT
    TO lpp_nurse
    USING (true);

-- Para analistas - solo lectura para estadísticas
CREATE POLICY analyst_view_validations ON ml_operations.medical_validations
    FOR SELECT
    TO lpp_analyst
    USING (true);

-- Para la aplicación - solo lectura
CREATE POLICY app_view_validations ON ml_operations.medical_validations
    FOR SELECT
    TO lpp_app
    USING (true);
```

### Esquema: audit_logs

#### Tabla: system_logs

```sql
-- Para acceso de administrador - acceso completo
CREATE POLICY admin_all_logs ON audit_logs.system_logs
    FOR ALL
    TO lpp_admin
    USING (true);

-- Para médicos - solo ver sus propias acciones
CREATE POLICY doctor_own_logs ON audit_logs.system_logs
    FOR SELECT
    TO lpp_doctor
    USING (user_id = current_setting('app.current_user_id', true)::uuid);

-- Para enfermeros - solo ver sus propias acciones
CREATE POLICY nurse_own_logs ON audit_logs.system_logs
    FOR SELECT
    TO lpp_nurse
    USING (user_id = current_setting('app.current_user_id', true)::uuid);

-- Para analistas - sin acceso
-- Sin política, denegación implícita

-- Para la aplicación - solo escritura
CREATE POLICY app_write_logs ON audit_logs.system_logs
    FOR INSERT
    TO lpp_app
    WITH CHECK (true);
```

## Implementación

Estas políticas deberán aplicarse después de crear los roles en la base de datos y antes de conceder acceso a los usuarios finales. Las políticas pueden ajustarse según evolucionen los requisitos del sistema.

Comandos para crear los roles:

```sql
-- Crear roles en la base de datos
CREATE ROLE lpp_admin;
CREATE ROLE lpp_doctor;
CREATE ROLE lpp_nurse;
CREATE ROLE lpp_analyst;
CREATE ROLE lpp_app;

-- Asignar privilegios por esquema
GRANT ALL ON SCHEMA clinical_data, staff_data, ml_operations, audit_logs TO lpp_admin;
GRANT USAGE ON SCHEMA clinical_data, staff_data, ml_operations TO lpp_doctor, lpp_nurse, lpp_analyst, lpp_app;
GRANT USAGE ON SCHEMA audit_logs TO lpp_admin, lpp_doctor, lpp_nurse, lpp_app;

-- Asignar privilegios por tabla (ejemplo para clinical_data)
GRANT ALL ON ALL TABLES IN SCHEMA clinical_data TO lpp_admin;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA clinical_data TO lpp_doctor;
GRANT SELECT, INSERT, UPDATE ON clinical_data.patient_assessments TO lpp_nurse;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_data TO lpp_nurse, lpp_analyst;
GRANT SELECT, INSERT, UPDATE ON clinical_data.patients TO lpp_app;
```

## Consideraciones de Seguridad Adicionales

Además de RLS, se implementarán las siguientes medidas de seguridad:

1. **Enmascaramiento de Datos**: Para roles analíticos, ciertos campos sensibles pueden ser enmascarados parcialmente.
2. **Auditoría de Actividad**: Todas las operaciones CRUD serán registradas en el esquema audit_logs.
3. **Control de Sesión**: Las sesiones tendrán tiempos de expiración adecuados según el rol.
4. **Cifrado**: Los datos sensibles serán cifrados a nivel de columna cuando sea necesario.
5. **Vistas Filtradas**: Para simplificar el acceso, se crearán vistas específicas por rol que apliquen filtros adicionales.

## Próximos Pasos

1. Implementar un sistema de gestión de usuarios que asigne correctamente estos roles a los usuarios del sistema.
2. Desarrollar pruebas de penetración para verificar la efectividad de las políticas RLS.
3. Crear un procedimiento de auditoría periódica para revisar los accesos y modificaciones a datos sensibles.
