# Vigia Medical Database Schema

Complete schema documentation for the medical-grade LPP detection database with HIPAA compliance.

## Database Structure Overview

The medical database uses four specialized schemas for security and compliance:

```
vigia_medical_db/
├── clinical_data/          # Patient records and medical assessments
├── staff_data/             # Medical staff and access control
├── ml_operations/          # AI/ML medical image processing
└── audit_logs/             # Medical compliance and audit trails
```

## Schema 1: clinical_data

### Table: patients
**Purpose**: Anonymous patient records with medical risk factors (HIPAA-compliant)

```sql
CREATE TABLE clinical_data.patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_code TEXT UNIQUE NOT NULL,  -- De-identified code (e.g., "CD-2025-001")
    age_range TEXT CHECK (age_range IN ('0-18', '19-40', '41-60', '61-80', '81+')),
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    risk_factors JSONB,  -- Medical risk factors (diabetes, mobility, etc.)
    mobility_status TEXT,
    medical_facility TEXT,
    admission_date DATE,
    discharge_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medical indices for performance
CREATE INDEX idx_patients_code ON clinical_data.patients (patient_code);
CREATE INDEX idx_patients_facility ON clinical_data.patients (medical_facility);
CREATE INDEX idx_patients_risk_factors ON clinical_data.patients USING GIN (risk_factors);

-- RLS Policy
ALTER TABLE clinical_data.patients ENABLE ROW LEVEL SECURITY;
CREATE POLICY medical_staff_patients ON clinical_data.patients
    FOR ALL TO lpp_doctor, lpp_nurse USING (true);
```

### Table: patient_assessments
**Purpose**: Medical risk assessments using standard scales (Braden, Norton, Emina)

```sql
CREATE TABLE clinical_data.patient_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    assessment_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Medical assessment scores
    braden_score SMALLINT CHECK (braden_score BETWEEN 6 AND 23),  -- Lower = higher risk
    norton_score SMALLINT CHECK (norton_score BETWEEN 5 AND 20),  -- Lower = higher risk
    emina_score SMALLINT CHECK (emina_score BETWEEN 0 AND 15),    -- Higher = higher risk
    
    -- Assessment details
    assessor_id UUID REFERENCES staff_data.medical_staff(id),
    medical_notes TEXT,
    risk_level TEXT CHECK (risk_level IN ('low', 'moderate', 'high', 'very_high')),
    next_assessment_due TIMESTAMPTZ,
    
    -- Medical context
    patient_condition JSONB,  -- Current medical condition factors
    environmental_factors JSONB,  -- Bed type, support surfaces, etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medical assessment indices
CREATE INDEX idx_assessments_patient ON clinical_data.patient_assessments (patient_id, assessment_date DESC);
CREATE INDEX idx_assessments_risk ON clinical_data.patient_assessments (braden_score, norton_score, emina_score);
CREATE INDEX idx_assessments_due ON clinical_data.patient_assessments (next_assessment_due);
```

### Table: care_plans
**Purpose**: Medical care plans and treatment protocols

```sql
CREATE TABLE clinical_data.care_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Care plan details
    intervention_type TEXT NOT NULL,  -- Prevention, treatment, monitoring
    medical_recommendations TEXT[],   -- Array of medical recommendations
    treatment_protocols JSONB,        -- Structured treatment protocols
    
    -- Medical oversight
    created_by UUID NOT NULL REFERENCES staff_data.medical_staff(id),
    approved_by UUID REFERENCES staff_data.medical_staff(id),
    
    -- Timeline and status
    start_date DATE DEFAULT CURRENT_DATE,
    target_completion_date DATE,
    follow_up_days INTEGER DEFAULT 7,
    status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'completed', 'discontinued')),
    
    -- Medical evidence
    clinical_evidence JSONB,          -- Evidence base for care plan
    guideline_references TEXT[],      -- NPUAP, EPUAP, etc. references
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Care plan indices
CREATE INDEX idx_care_plans_patient ON clinical_data.care_plans (patient_id, status);
CREATE INDEX idx_care_plans_status ON clinical_data.care_plans (status, start_date);
```

## Schema 2: staff_data

### Table: medical_staff
**Purpose**: Medical personnel with role-based access control

```sql
CREATE TABLE staff_data.medical_staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_code TEXT UNIQUE NOT NULL,    -- Professional identifier
    
    -- Professional information
    role TEXT NOT NULL CHECK (role IN ('doctor', 'nurse', 'nurse_practitioner', 'wound_specialist', 'administrator')),
    department TEXT,
    medical_license_number TEXT,
    specialty JSONB,                    -- Medical specializations
    
    -- Authentication and access
    email TEXT UNIQUE,
    phone TEXT,
    access_level TEXT DEFAULT 'standard' CHECK (access_level IN ('standard', 'elevated', 'admin')),
    
    -- Professional status
    employment_status TEXT DEFAULT 'active' CHECK (employment_status IN ('active', 'inactive', 'suspended')),
    hire_date DATE,
    certifications JSONB,               -- Professional certifications
    
    -- Shift and availability
    shift_pattern JSONB,                -- Work schedule information
    on_call_availability BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Staff indices
CREATE INDEX idx_staff_role ON staff_data.medical_staff (role, employment_status);
CREATE INDEX idx_staff_department ON staff_data.medical_staff (department);
CREATE INDEX idx_staff_access ON staff_data.medical_staff (access_level);
```

### Table: staff_sessions
**Purpose**: Medical staff session tracking for audit compliance

```sql
CREATE TABLE staff_data.staff_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES medical_staff(id),
    
    -- Session details
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT,
    
    -- Medical context
    department_access TEXT[],           -- Departments accessed during session
    patient_interactions INTEGER DEFAULT 0,
    medical_actions_performed JSONB,
    
    -- Security and compliance
    authentication_method TEXT,
    security_level TEXT DEFAULT 'standard',
    audit_trail_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session tracking indices
CREATE INDEX idx_sessions_staff ON staff_data.staff_sessions (staff_id, session_start DESC);
CREATE INDEX idx_sessions_active ON staff_data.staff_sessions (session_start, session_end) WHERE session_end IS NULL;
```

## Schema 3: ml_operations

### Table: lpp_images
**Purpose**: Medical image storage with LPP detection metadata

```sql
CREATE TABLE ml_operations.lpp_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    
    -- File management
    file_path TEXT NOT NULL,
    file_hash TEXT UNIQUE,              -- SHA-256 for duplicate detection
    file_size_bytes BIGINT,
    
    -- Image classification
    image_type TEXT CHECK (image_type IN ('original', 'processed', 'anonymized', 'synthetic')),
    body_location TEXT,                 -- sacrum, heel, elbow, etc.
    
    -- Medical metadata
    capture_date TIMESTAMPTZ,
    capture_device JSONB,               -- Camera, smartphone, medical device
    lighting_conditions TEXT,
    image_quality_score DECIMAL(3,2),  -- 0.00-1.00
    
    -- Privacy and compliance
    privacy_compliant BOOLEAN DEFAULT false,
    phi_removed BOOLEAN DEFAULT false,
    anonymization_method TEXT,
    
    -- Medical context
    clinical_indication TEXT,           -- Why image was taken
    anatomical_landmarks JSONB,        -- Reference points in image
    medical_annotations JSONB,          -- Medical professional annotations
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Image management indices
CREATE INDEX idx_images_patient ON ml_operations.lpp_images (patient_id, capture_date DESC);
CREATE INDEX idx_images_location ON ml_operations.lpp_images (body_location, image_type);
CREATE INDEX idx_images_hash ON ml_operations.lpp_images (file_hash);
CREATE INDEX idx_images_privacy ON ml_operations.lpp_images (privacy_compliant, phi_removed);
```

### Table: vigia_detections
**Purpose**: AI detection results with medical validation tracking

```sql
CREATE TABLE ml_operations.vigia_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES lpp_images(id) ON DELETE CASCADE,
    
    -- AI model information
    model_version TEXT NOT NULL,
    model_type TEXT DEFAULT 'yolov5',
    inference_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Detection results
    lpp_stage SMALLINT CHECK (lpp_stage BETWEEN 0 AND 4),  -- NPUAP/EPUAP stages
    confidence_score DECIMAL(4,3) CHECK (confidence_score BETWEEN 0 AND 1),
    bounding_box JSONB,                 -- Detection coordinates
    detection_area_cm2 DECIMAL(8,2),   -- Size of detected area
    
    -- Medical assessment
    anatomical_location TEXT,
    medical_urgency TEXT CHECK (medical_urgency IN ('low', 'moderate', 'high', 'emergency')),
    clinical_significance TEXT,
    
    -- Processing metadata
    processing_time_ms INTEGER,
    gpu_used BOOLEAN DEFAULT false,
    preprocessing_applied JSONB,        -- Preprocessing steps
    
    -- Validation tracking
    requires_validation BOOLEAN DEFAULT true,
    validation_priority TEXT DEFAULT 'standard' CHECK (validation_priority IN ('low', 'standard', 'high', 'urgent')),
    
    -- Evidence and references
    detection_evidence JSONB,          -- Supporting evidence for detection
    ai_explanation TEXT,               -- AI decision explanation
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detection analysis indices
CREATE INDEX idx_detections_image ON ml_operations.vigia_detections (image_id);
CREATE INDEX idx_detections_stage ON ml_operations.vigia_detections (lpp_stage, confidence_score DESC);
CREATE INDEX idx_detections_urgency ON ml_operations.vigia_detections (medical_urgency, created_at DESC);
CREATE INDEX idx_detections_validation ON ml_operations.vigia_detections (requires_validation, validation_priority);
```

### Table: medical_validations
**Purpose**: Medical professional validation of AI detections

```sql
CREATE TABLE ml_operations.medical_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL REFERENCES vigia_detections(id) ON DELETE CASCADE,
    validator_id UUID NOT NULL REFERENCES staff_data.medical_staff(id),
    
    -- Validation results
    validated_stage SMALLINT CHECK (validated_stage BETWEEN 0 AND 4),
    validation_confidence SMALLINT CHECK (validation_confidence BETWEEN 1 AND 5),  -- 1=low, 5=very high
    agrees_with_ai BOOLEAN,
    
    -- Medical assessment
    clinical_notes TEXT,
    differential_diagnosis TEXT[],      -- Alternative diagnoses considered
    recommended_treatment JSONB,        -- Treatment recommendations
    
    -- Professional consensus
    requires_second_opinion BOOLEAN DEFAULT false,
    medical_consensus BOOLEAN,
    consensus_reached_at TIMESTAMPTZ,
    
    -- Escalation and follow-up
    escalation_required BOOLEAN DEFAULT false,
    escalation_reason TEXT,
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_timeline INTERVAL,
    
    -- Evidence and guidelines
    clinical_evidence JSONB,           -- Supporting medical evidence
    guideline_compliance JSONB,        -- NPUAP/EPUAP guideline adherence
    
    validation_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medical validation indices
CREATE INDEX idx_validations_detection ON ml_operations.medical_validations (detection_id);
CREATE INDEX idx_validations_validator ON ml_operations.medical_validations (validator_id, validation_timestamp DESC);
CREATE INDEX idx_validations_consensus ON ml_operations.medical_validations (medical_consensus, escalation_required);
```

### Table: model_performance
**Purpose**: AI model performance tracking and medical accuracy metrics

```sql
CREATE TABLE ml_operations.model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version TEXT NOT NULL,
    evaluation_date DATE DEFAULT CURRENT_DATE,
    
    -- Performance metrics
    accuracy DECIMAL(5,4),              -- Overall accuracy
    precision_by_stage JSONB,           -- Precision for each LPP stage
    recall_by_stage JSONB,              -- Recall for each LPP stage
    f1_score_by_stage JSONB,            -- F1 scores for each stage
    
    -- Medical validation metrics
    medical_agreement_rate DECIMAL(5,4), -- Agreement with medical professionals
    false_positive_rate DECIMAL(5,4),
    false_negative_rate DECIMAL(5,4),
    critical_miss_rate DECIMAL(5,4),    -- Missed high-urgency cases
    
    -- Dataset information
    test_dataset_size INTEGER,
    validation_dataset_size INTEGER,
    medical_reviewer_count INTEGER,
    
    -- Clinical impact metrics
    diagnostic_efficiency JSONB,        -- Time saved in diagnosis
    clinical_decision_support JSONB,    -- Impact on clinical decisions
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Schema 4: audit_logs

### Table: system_logs
**Purpose**: System-wide audit logging for medical compliance

```sql
CREATE TABLE audit_logs.system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event identification
    event_type TEXT NOT NULL,           -- login, logout, data_access, medical_decision, etc.
    event_category TEXT NOT NULL,       -- security, medical, system, compliance
    severity_level TEXT DEFAULT 'info' CHECK (severity_level IN ('debug', 'info', 'warning', 'error', 'critical')),
    
    -- User and session
    user_id UUID REFERENCES staff_data.medical_staff(id),
    session_id UUID,
    user_role TEXT,
    
    -- Medical context
    patient_code TEXT,                  -- De-identified patient reference
    medical_action TEXT,
    clinical_context JSONB,
    
    -- System details
    system_component TEXT,
    api_endpoint TEXT,
    request_method TEXT,
    response_status INTEGER,
    
    -- Compliance and audit
    compliance_framework TEXT[],        -- HIPAA, MINSAL, etc.
    audit_trail_id UUID,
    requires_review BOOLEAN DEFAULT false,
    
    -- Technical details
    ip_address INET,
    user_agent TEXT,
    processing_time_ms INTEGER,
    
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logging indices
CREATE INDEX idx_system_logs_event ON audit_logs.system_logs (event_type, event_timestamp DESC);
CREATE INDEX idx_system_logs_user ON audit_logs.system_logs (user_id, event_timestamp DESC);
CREATE INDEX idx_system_logs_patient ON audit_logs.system_logs (patient_code, event_timestamp DESC);
CREATE INDEX idx_system_logs_compliance ON audit_logs.system_logs USING GIN (compliance_framework);
```

### Table: medical_access_logs
**Purpose**: Detailed medical data access logging for HIPAA compliance

```sql
CREATE TABLE audit_logs.medical_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Access details
    access_type TEXT NOT NULL,          -- view, edit, delete, export
    data_type TEXT NOT NULL,            -- patient_data, medical_image, detection_result
    data_id UUID,                       -- ID of accessed data
    
    -- Medical context
    patient_code TEXT,
    medical_justification TEXT NOT NULL, -- Required medical reason for access
    clinical_necessity BOOLEAN DEFAULT true,
    
    -- User details
    accessor_id UUID NOT NULL REFERENCES staff_data.medical_staff(id),
    accessor_role TEXT,
    department TEXT,
    
    -- Compliance tracking
    phi_accessed BOOLEAN DEFAULT false,
    consent_verified BOOLEAN DEFAULT false,
    minimum_necessary BOOLEAN DEFAULT true, -- HIPAA minimum necessary principle
    
    -- Session and technical
    session_id UUID,
    ip_address INET,
    access_method TEXT,                 -- web, api, mobile_app
    
    access_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medical access audit indices
CREATE INDEX idx_medical_access_patient ON audit_logs.medical_access_logs (patient_code, access_timestamp DESC);
CREATE INDEX idx_medical_access_user ON audit_logs.medical_access_logs (accessor_id, access_timestamp DESC);
CREATE INDEX idx_medical_access_phi ON audit_logs.medical_access_logs (phi_accessed, access_timestamp DESC);
```

## Database Security Policies

### Row Level Security (RLS) Policies

```sql
-- Enable RLS on all medical tables
ALTER TABLE clinical_data.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_data.patient_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_data.care_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_data.medical_staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.lpp_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.vigia_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_operations.medical_validations ENABLE ROW LEVEL SECURITY;

-- Medical roles
CREATE ROLE lpp_admin;                  -- Full system access
CREATE ROLE lpp_doctor;                 -- Clinical data and validations
CREATE ROLE lpp_nurse;                  -- Patient care and assessments
CREATE ROLE lpp_analyst;                -- Anonymized research data
CREATE ROLE lpp_app;                    -- Application service access

-- Example policy: Doctors can access all patient data
CREATE POLICY doctor_patient_access ON clinical_data.patients
    FOR ALL TO lpp_doctor USING (true);

-- Example policy: Nurses can access patients in their department
CREATE POLICY nurse_patient_access ON clinical_data.patients
    FOR SELECT TO lpp_nurse 
    USING (
        EXISTS (
            SELECT 1 FROM staff_data.medical_staff s 
            WHERE s.id = current_setting('app.current_user_id')::UUID 
            AND s.department = medical_facility
        )
    );
```

### Medical Data Encryption

```sql
-- Encrypt sensitive medical fields
ALTER TABLE clinical_data.patients 
ADD COLUMN encrypted_notes TEXT,
ADD COLUMN encryption_key_id TEXT;

-- Function for medical data encryption
CREATE OR REPLACE FUNCTION encrypt_medical_data(data TEXT, key_id TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Implementation would use PostgreSQL pgcrypto
    -- or external encryption service
    RETURN pgp_sym_encrypt(data, key_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Medical Database Functions

### Medical Risk Assessment
```sql
CREATE OR REPLACE FUNCTION calculate_lpp_risk(
    braden_score INTEGER,
    norton_score INTEGER, 
    emina_score INTEGER,
    risk_factors JSONB
) RETURNS TEXT AS $$
DECLARE
    risk_level TEXT;
BEGIN
    -- Calculate composite risk based on multiple scales
    IF braden_score <= 12 OR norton_score <= 10 OR emina_score >= 12 THEN
        risk_level := 'very_high';
    ELSIF braden_score <= 15 OR norton_score <= 14 OR emina_score >= 8 THEN
        risk_level := 'high';
    ELSIF braden_score <= 18 OR norton_score <= 16 OR emina_score >= 5 THEN
        risk_level := 'moderate';
    ELSE
        risk_level := 'low';
    END IF;
    
    -- Adjust for additional risk factors
    IF risk_factors ? 'diabetes' AND (risk_factors->>'diabetes')::BOOLEAN THEN
        risk_level := CASE 
            WHEN risk_level = 'low' THEN 'moderate'
            WHEN risk_level = 'moderate' THEN 'high'
            WHEN risk_level = 'high' THEN 'very_high'
            ELSE risk_level
        END;
    END IF;
    
    RETURN risk_level;
END;
$$ LANGUAGE plpgsql;
```

### Medical Validation Triggers
```sql
-- Trigger to automatically update medical urgency based on detection
CREATE OR REPLACE FUNCTION update_medical_urgency()
RETURNS TRIGGER AS $$
BEGIN
    -- Update urgency based on LPP stage and confidence
    NEW.medical_urgency := CASE
        WHEN NEW.lpp_stage >= 3 THEN 'emergency'
        WHEN NEW.lpp_stage = 2 AND NEW.confidence_score > 0.8 THEN 'high'
        WHEN NEW.lpp_stage = 1 THEN 'moderate'
        ELSE 'low'
    END;
    
    -- Set validation priority
    NEW.validation_priority := CASE
        WHEN NEW.medical_urgency = 'emergency' THEN 'urgent'
        WHEN NEW.medical_urgency = 'high' THEN 'high'
        ELSE 'standard'
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_medical_urgency
    BEFORE INSERT OR UPDATE ON ml_operations.vigia_detections
    FOR EACH ROW EXECUTE FUNCTION update_medical_urgency();
```

## Medical Data Views

### Medical Dashboard View
```sql
CREATE VIEW medical_dashboard AS
SELECT 
    p.patient_code,
    p.age_range,
    p.risk_factors,
    a.braden_score,
    a.norton_score,
    a.emina_score,
    calculate_lpp_risk(a.braden_score, a.norton_score, a.emina_score, p.risk_factors) as risk_level,
    COUNT(d.id) as detection_count,
    MAX(d.lpp_stage) as highest_stage_detected,
    MAX(d.medical_urgency) as highest_urgency,
    COUNT(v.id) as validation_count,
    COUNT(CASE WHEN v.escalation_required THEN 1 END) as escalations_required
FROM clinical_data.patients p
LEFT JOIN clinical_data.patient_assessments a ON p.id = a.patient_id
LEFT JOIN ml_operations.lpp_images i ON p.id = i.patient_id
LEFT JOIN ml_operations.vigia_detections d ON i.id = d.image_id
LEFT JOIN ml_operations.medical_validations v ON d.id = v.detection_id
GROUP BY p.id, p.patient_code, p.age_range, p.risk_factors, 
         a.braden_score, a.norton_score, a.emina_score;
```

This schema provides a comprehensive foundation for medical-grade LPP detection with full audit compliance, security, and clinical workflow support.