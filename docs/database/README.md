# Vigia Database Documentation

Complete database documentation for the medical-grade LPP detection system.

## Database Overview

**Project**: Vigia Medical Database  
**Technology**: Supabase (PostgreSQL)  
**Project ID**: jfcwziciqdmhodozowhv  
**Region**: South America (São Paulo)  
**URL**: https://jfcwziciqdmhodozowhv.supabase.co  

## Database Architecture

The medical database is organized into four specialized schemas for medical data security and compliance:

### 1. clinical_data
**Purpose**: Patient medical records, assessments, and care plans
- Patient information (anonymized for HIPAA/GDPR compliance)
- Medical risk assessments (Braden, Norton, Emina scales)
- Care plans and treatment protocols
- Medical session tracking

### 2. staff_data  
**Purpose**: Medical staff and administrative personnel
- Medical staff profiles and credentials
- Role-based access control
- Medical staff scheduling and assignments
- Professional certifications tracking

### 3. ml_operations
**Purpose**: AI/ML medical image processing and analysis
- Medical image storage and metadata
- LPP detection results and confidence scores
- Medical model performance tracking
- Validation by medical professionals

### 4. audit_logs
**Purpose**: Medical compliance and audit trails
- System access logs for medical compliance
- Medical decision audit trails
- PHI access tracking
- Regulatory compliance logging

## Key Medical Tables

### Patient Management (`clinical_data.patients`)
```sql
-- Anonymous patient records with medical risk factors
CREATE TABLE clinical_data.patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_code TEXT UNIQUE NOT NULL,  -- De-identified patient code
    age_range TEXT CHECK (age_range IN ('0-18', '19-40', '41-60', '61-80', '81+')),
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    risk_factors JSONB,  -- Diabetes, mobility issues, etc.
    mobility_status TEXT,
    medical_facility TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Medical Assessments (`clinical_data.patient_assessments`)
```sql
-- Medical risk assessments using standard scales
CREATE TABLE clinical_data.patient_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    assessment_date TIMESTAMPTZ DEFAULT NOW(),
    braden_score SMALLINT,    -- Braden scale (lower = higher risk)
    norton_score SMALLINT,    -- Norton scale (lower = higher risk) 
    emina_score SMALLINT,     -- Emina scale (higher = higher risk)
    assessor_id UUID REFERENCES staff_data.medical_staff(id),
    medical_notes TEXT,
    next_assessment_due TIMESTAMPTZ
);
```

### Medical Images (`ml_operations.lpp_images`)
```sql
-- Medical image storage with LPP detection metadata
CREATE TABLE ml_operations.lpp_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    file_path TEXT NOT NULL,
    file_hash TEXT UNIQUE,    -- SHA-256 for duplicate detection
    image_type TEXT CHECK (image_type IN ('original', 'processed', 'anonymized')),
    body_location TEXT,       -- sacrum, heel, etc.
    capture_date TIMESTAMPTZ,
    medical_metadata JSONB,   -- Camera, lighting, angle, etc.
    privacy_compliant BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### LPP Detections (`ml_operations.vigia_detections`)
```sql
-- AI detection results with medical validation
CREATE TABLE ml_operations.vigia_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES lpp_images(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL,
    lpp_stage SMALLINT CHECK (lpp_stage BETWEEN 0 AND 4),
    confidence_score DECIMAL(4,3) CHECK (confidence_score BETWEEN 0 AND 1),
    bounding_box JSONB,       -- Detection coordinates
    anatomical_location TEXT,
    medical_urgency TEXT CHECK (medical_urgency IN ('low', 'moderate', 'high', 'emergency')),
    requires_validation BOOLEAN DEFAULT true,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Medical Validation (`ml_operations.medical_validations`)
```sql
-- Medical professional validation of AI detections
CREATE TABLE ml_operations.medical_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL REFERENCES vigia_detections(id) ON DELETE CASCADE,
    validator_id UUID NOT NULL REFERENCES staff_data.medical_staff(id),
    validated_stage SMALLINT CHECK (validated_stage BETWEEN 0 AND 4),
    validation_confidence SMALLINT CHECK (validation_confidence BETWEEN 1 AND 5),
    clinical_notes TEXT,
    validation_timestamp TIMESTAMPTZ DEFAULT NOW(),
    medical_consensus BOOLEAN,
    escalation_required BOOLEAN DEFAULT false
);
```

## Medical Security & Compliance

### Row-Level Security (RLS)
All tables have RLS enabled with role-based access:

```sql
-- Medical staff roles
CREATE ROLE lpp_admin;          -- Full medical system access
CREATE ROLE lpp_doctor;         -- Clinical data and validations
CREATE ROLE lpp_nurse;          -- Patient care and assessments
CREATE ROLE lpp_analyst;        -- Anonymized data for research
CREATE ROLE lpp_app;            -- Application service access
```

### Medical Data Protection
- **Encryption**: Sensitive medical data encrypted at column level
- **Anonymization**: Patient identifiers replaced with codes
- **Audit Trails**: All medical data access logged
- **PHI Protection**: HIPAA-compliant data handling

### FHIR Compatibility
The schema is designed for future FHIR standard migration:
- `patients` → FHIR `Patient` resource
- `patient_assessments` → FHIR `Observation` resource  
- `care_plans` → FHIR `CarePlan` resource
- `lpp_images` → FHIR `Media` resource

## Medical Database Operations

### Patient Record Management
```python
# Create anonymous patient record
patient_data = {
    "patient_code": "CD-2025-001",
    "age_range": "61-80",
    "risk_factors": {"diabetes": True, "immobility": True},
    "medical_facility": "Hospital Central"
}
response = supabase.table("clinical_data.patients").insert(patient_data).execute()
```

### Medical Assessment Recording
```python
# Record medical risk assessment
assessment = {
    "patient_id": patient_uuid,
    "braden_score": 12,     # High risk (< 15)
    "norton_score": 11,     # High risk (< 14) 
    "emina_score": 15,      # High risk (> 8)
    "assessor_id": nurse_uuid,
    "medical_notes": "Patient shows multiple pressure injury risk factors"
}
response = supabase.table("clinical_data.patient_assessments").insert(assessment).execute()
```

### LPP Detection Storage
```python
# Store AI detection results
detection = {
    "image_id": image_uuid,
    "model_version": "yolov5-medical-v2.1",
    "lpp_stage": 2,
    "confidence_score": 0.87,
    "anatomical_location": "sacrum",
    "medical_urgency": "moderate",
    "requires_validation": True
}
response = supabase.table("ml_operations.vigia_detections").insert(detection).execute()
```

### Medical Validation Recording
```python
# Record medical professional validation
validation = {
    "detection_id": detection_uuid,
    "validator_id": doctor_uuid,
    "validated_stage": 2,
    "validation_confidence": 4,   # Scale 1-5
    "clinical_notes": "Confirmed Stage 2 LPP, consistent with AI detection",
    "medical_consensus": True
}
response = supabase.table("ml_operations.medical_validations").insert(validation).execute()
```

## Medical Audit & Compliance

### Audit Logging
```python
# Log medical system access
audit_entry = {
    "user_id": medical_staff_id,
    "action": "patient_data_access",
    "patient_code": "CD-2025-001",
    "medical_context": {
        "reason": "lpp_assessment",
        "detection_review": True,
        "clinical_urgency": "moderate"
    },
    "compliance_frameworks": ["HIPAA", "MINSAL"],
    "access_justification": "Medical review of LPP detection results"
}
response = supabase.table("audit_logs.medical_access").insert(audit_entry).execute()
```

### Medical Queries

#### High-Risk Patients
```sql
-- Identify patients with high LPP risk
SELECT 
    p.patient_code,
    p.age_range,
    p.risk_factors,
    a.braden_score,
    a.norton_score,
    a.emina_score,
    a.assessment_date
FROM clinical_data.patients p
JOIN clinical_data.patient_assessments a ON p.id = a.patient_id
WHERE a.braden_score < 15 
   OR a.norton_score < 14 
   OR a.emina_score > 8
ORDER BY a.braden_score ASC, a.assessment_date DESC;
```

#### Medical Validation Accuracy
```sql
-- Calculate AI vs medical professional agreement
SELECT 
    d.lpp_stage as ai_detected_stage,
    v.validated_stage as medical_validated_stage,
    COUNT(*) as case_count,
    AVG(d.confidence_score) as avg_ai_confidence,
    AVG(v.validation_confidence) as avg_medical_confidence,
    COUNT(CASE WHEN d.lpp_stage = v.validated_stage THEN 1 END)::float / 
    COUNT(*) as accuracy_rate
FROM ml_operations.vigia_detections d
JOIN ml_operations.medical_validations v ON d.id = v.detection_id
GROUP BY d.lpp_stage, v.validated_stage
ORDER BY d.lpp_stage, v.validated_stage;
```

#### Medical Escalation Cases
```sql
-- Cases requiring medical escalation
SELECT 
    p.patient_code,
    d.lpp_stage,
    d.confidence_score,
    d.medical_urgency,
    v.escalation_required,
    v.clinical_notes,
    ms.staff_code as validator
FROM ml_operations.vigia_detections d
JOIN ml_operations.lpp_images i ON d.image_id = i.id
JOIN clinical_data.patients p ON i.patient_id = p.id
LEFT JOIN ml_operations.medical_validations v ON d.id = v.detection_id
LEFT JOIN staff_data.medical_staff ms ON v.validator_id = ms.id
WHERE d.medical_urgency IN ('high', 'emergency') 
   OR v.escalation_required = true
ORDER BY d.created_at DESC;
```

## Database Maintenance

### Medical Data Retention
```sql
-- Clean up old anonymized test data (retain medical data per regulations)
DELETE FROM ml_operations.lpp_images 
WHERE image_type = 'test' 
  AND created_at < NOW() - INTERVAL '30 days';

-- Archive old audit logs (after regulatory retention period)
INSERT INTO audit_logs.archived_medical_access 
SELECT * FROM audit_logs.medical_access 
WHERE created_at < NOW() - INTERVAL '7 years';
```

### Performance Optimization
```sql
-- Medical query performance indices
CREATE INDEX idx_patients_risk_factors ON clinical_data.patients USING GIN (risk_factors);
CREATE INDEX idx_assessments_scores ON clinical_data.patient_assessments (braden_score, norton_score, emina_score);
CREATE INDEX idx_detections_urgency ON ml_operations.vigia_detections (medical_urgency, created_at);
CREATE INDEX idx_images_body_location ON ml_operations.lpp_images (body_location, capture_date);
```

## Medical Compliance Notes

### HIPAA Compliance
- All patient data anonymized with coded identifiers
- Access logging for all PHI interactions
- Encryption for sensitive medical fields
- Role-based access controls implemented

### Chilean MINSAL Compliance
- Medical decision audit trails maintained
- Evidence-based medical protocols referenced
- Public healthcare integration support
- Local medical regulation compliance

### Medical Data Governance
- Medical professional validation required for clinical decisions
- Escalation protocols for high-risk cases
- Medical consensus tracking for AI/human agreement
- Clinical note requirements for medical validation

For detailed implementation examples and medical query patterns, see the [Developer Guide](../DEVELOPER_GUIDE.md) and [API Reference](../API_REFERENCE.md).