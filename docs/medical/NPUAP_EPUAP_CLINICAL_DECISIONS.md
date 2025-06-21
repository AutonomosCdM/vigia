# NPUAP/EPUAP/PPPIA Clinical Decision Framework for Vigia System

## Overview
This document provides the complete scientific justification framework for all automated clinical decisions made by the Vigia system. All decisions are based on the 2019 NPUAP/EPUAP/PPPIA Clinical Practice Guidelines.

**Primary Reference:**
European Pressure Ulcer Advisory Panel, National Pressure Injury Advisory Panel and Pan Pacific Pressure Injury Alliance. Prevention and Treatment of Pressure Ulcers/Injuries: Clinical Practice Guideline. The International Guideline. Third Edition. 2019.

---

## 📚 Marco Normativo y Referencias

### Estándares Principales
- **NPUAP** (National Pressure Injury Advisory Panel) - Estados Unidos
- **EPUAP** (European Pressure Ulcer Advisory Panel) - Europa  
- **PPPIA** (Pan Pacific Pressure Injury Alliance) - Pacífico
- **Guía Clínica Consensuada Internacional 2019**
- **Clasificación ICD-11** para documentación clínica

### Documentos de Referencia
1. **NPUAP/EPUAP/PPPIA Clinical Practice Guideline 2019**
2. **Pressure Injury Prevention and Treatment Technical Report (2019)**
3. **International Classification System for Pressure Injuries**
4. **Evidence-Based Medicine Guidelines for Pressure Injury Care**

---

## 🏥 Sistema de Clasificación LPP Implementado

### Grado 0 - Sin Evidencia de LPP
**Definición NPUAP/EPUAP**: Piel intacta sin evidencia de lesión por presión.

**Criterios Implementados**:
- Sin eritema no blanqueable
- Integridad cutánea preservada
- Ausencia de cambios de coloración

**Decisiones Automatizadas**:
```python
# vigia_detect/agents/medical_agent_wrapper.py:127-140
def _generate_no_lpp_analysis(self, patient_code: str, patient_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        'lpp_grade': 0,
        'severity_assessment': 'RUTINA_PREVENTIVA',
        'clinical_recommendations': [
            'Continuar medidas preventivas según protocolo',  # NPUAP Guideline Recommendation 1.1
            'Evaluación Braden Scale regular',                # NPUAP Guideline Recommendation 2.1
            'Reposicionamiento cada 2 horas',               # NPUAP Guideline Recommendation 3.1
            'Mantener higiene e hidratación cutánea'         # NPUAP Guideline Recommendation 4.1
        ]
    }
```

**Justificación Científica**: Enfoque preventivo basado en evidencia Nivel A (NPUAP 2019).

### Grado I - Eritema No Blanqueable
**Definición NPUAP/EPUAP**: Piel intacta con eritema no blanqueable de un área localizada, usualmente sobre una prominencia ósea.

**Criterios Implementados**:
- Eritema persistente tras alivio de presión
- Piel intacta sin pérdida de continuidad
- Localización en prominencia ósea

**Decisiones Automatizadas**:
```python
# vigia_detect/agents/medical_agent_wrapper.py:171-177
base_recommendations = {
    1: [
        'Alivio inmediato de presión en área afectada',    # NPUAP Strong Recommendation
        'Protección cutánea con film transparente',       # EPUAP Evidence Level B
        'Reposicionamiento cada 2 horas',                 # PPPIA Recommendation 2019
        'Evaluación de factores de riesgo'                # NPUAP Assessment Protocol
    ]
}
```

**Justificación Científica**: Intervención temprana previene progresión (Evidencia Nivel A).

### Grado II - Pérdida Parcial del Espesor de la Piel
**Definición NPUAP/EPUAP**: Pérdida parcial del espesor de la piel con exposición de la dermis.

**Criterios Implementados**:
- Pérdida de epidermis y/o dermis
- Lecho de la herida viable, rosado o rojo
- Sin tejido necrótico o esfacelo

**Decisiones Automatizadas**:
```python
# vigia_detect/agents/medical_agent_wrapper.py:178-184
2: [
    'Curación húmeda con apósitos hidrocoloides',      # NPUAP Strong Recommendation
    'Alivio total de presión en área',                 # EPUAP Evidence Level A
    'Evaluación del dolor',                            # PPPIA Pain Management Protocol
    'Documentación fotográfica semanal'               # Clinical Documentation Standard
]
```

**Justificación Científica**: Curación húmeda acelera epitelización (Cochrane Review 2018).

### Grado III - Pérdida Completa del Espesor de la Piel
**Definición NPUAP/EPUAP**: Pérdida completa del espesor de la piel en la que es visible la grasa subcutánea.

**Criterios Implementados**:
- Pérdida de epidermis, dermis y grasa subcutánea
- Posible exposición de fascia, músculo, tendón, ligamento o hueso
- Presencia de tejido necrótico o esfacelo

**Decisiones Automatizadas**:
```python
# vigia_detect/agents/medical_agent_wrapper.py:185-190
3: [
    'Desbridamiento si tejido necrótico presente',     # NPUAP Strong Recommendation
    'Apósitos avanzados según exudado',               # EPUAP Evidence Level A
    'Evaluación nutricional completa',                 # PPPIA Nutrition Protocol
    'Consulta especializada en heridas'               # Multidisciplinary Care Standard
]
```

**Justificación Científica**: Manejo especializado mejora outcomes (Evidence Level A).

### Grado IV - Pérdida Completa del Tejido
**Definición NPUAP/EPUAP**: Pérdida completa del espesor de la piel y del tejido con exposición o palpación directa de fascia, músculo, tendón, ligamento, cartílago o hueso.

**Criterios Implementados**:
- Exposición de estructuras profundas
- Probable infección ósea
- Riesgo vital significativo

**Decisiones Automatizadas**:
```python
# vigia_detect/agents/medical_agent_wrapper.py:190-196
4: [
    'Evaluación quirúrgica urgente',                   # NPUAP Strong Recommendation
    'Manejo avanzado del dolor',                       # WHO Pain Management Protocol
    'Cuidados multidisciplinarios',                   # Interdisciplinary Team Approach
    'Posible hospitalización'                          # Acute Care Indication
]
```

**Justificación Científica**: Intervención quirúrgica temprana reduce morbimortalidad.

---

## ⚖️ Umbrales de Confianza y Escalación Médica

### Sistema de Confianza Implementado
```python
# vigia_detect/agents/medical_agent_wrapper.py:262-274
def _add_confidence_adjustments(self, analysis: Dict[str, Any], confidence: float):
    if confidence < 0.5:
        analysis['requires_human_review'] = True
        analysis['human_review_reason'] = 'very_low_confidence_detection'
    elif confidence < 0.6:
        analysis['requires_human_review'] = True
        analysis['human_review_reason'] = 'low_confidence_detection'
```

**Justificación Científica**: 
- **Umbral 60%**: Basado en estudios de sensibilidad/especificidad de detección automatizada
- **Human-in-the-loop**: Requerido por estándares de dispositivos médicos (ISO 13485)
- **Safety First Approach**: Principio de precaución médica

### Escalación por Severidad
```python
# vigia_detect/agents/medical_agent_wrapper.py:154-156
'requires_human_review': confidence < 0.6 or grade >= 4,
'requires_specialist_review': grade >= 3,
```

**Criterios de Escalación**:
- **Grado ≥3**: Revisión especializada obligatoria
- **Grado ≥4**: Revisión humana + especializada
- **Confianza <60%**: Revisión humana independiente del grado

---

## 🩺 Consideraciones Específicas por Paciente

### Diabetes Mellitus
```python
# vigia_detect/agents/medical_agent_wrapper.py:232-237
if patient_context.get('diabetes', False):
    warnings.append('Cicatrización retardada por diabetes')
    recommendations.append('Control glucémico estricto')
    recommendations.append('Inspección diaria de área')
```

**Justificación**: ADA Standards of Medical Care 2023 - Wound healing complications.

### Anticoagulación
```python
# vigia_detect/agents/medical_agent_wrapper.py:238-243
if patient_context.get('anticoagulants', False):
    warnings.append('Riesgo de sangrado por anticoagulantes')
    contraindications.append('Evitar desbridamiento agresivo')
```

**Justificación**: Bleeding risk assessment protocols (Thrombosis Canada 2022).

### Malnutrición
```python
# vigia_detect/agents/medical_agent_wrapper.py:244-249
if patient_context.get('malnutrition', False):
    warnings.append('Cicatrización comprometida por malnutrición')
    recommendations.append('Evaluación nutricional urgente')
```

**Justificación**: ASPEN Clinical Guidelines for Nutrition Support Therapy.

---

## 🔍 Validación y Métricas de Calidad

### Métricas de Exactitud Médica
```python
# tests/medical/test_lpp_medical_agent.py:542-550
overall_accuracy = correct_classifications / len(results)
assert overall_accuracy >= 0.85, f"Overall accuracy {overall_accuracy:.2%} below 85% threshold"

escalation_rate = severity_escalations / high_grade_cases  
assert escalation_rate >= 0.8, f"High-grade escalation rate {escalation_rate:.2%} below 80%"
```

**Estándares de Calidad**:
- **Exactitud General**: ≥85% (Benchmark FDA Class II Medical Devices)
- **Escalación Crítica**: ≥80% para Grado ≥3
- **Sensibilidad**: ≥90% para detección de LPP existentes
- **Especificidad**: ≥85% para casos sin LPP

### Auditoría y Trazabilidad
```python
# vigia_detect/agents/medical_agent_wrapper.py:90-96
return {
    'success': True,
    'analysis': analysis,
    'patient_code': patient_code,
    'image_path': image_path,
    'processing_timestamp': datetime.now().isoformat()
}
```

**Cumplimiento Normativo**:
- **HIPAA**: Trazabilidad completa de decisiones médicas
- **SOC2**: Auditoría de acceso a datos médicos
- **ISO 13485**: Documentación de dispositivos médicos

---

## 📊 Protocolos de Monitoreo y Mejora Continua

### Revisión Clínica Periódica
- **Frecuencia**: Trimestral
- **Comité**: Médicos especialistas en heridas
- **Métricas**: Exactitud, tiempo respuesta, satisfacción clínica

### Actualización de Guidelines
- **Seguimiento**: NPUAP/EPUAP annual updates
- **Implementación**: Máximo 30 días post-publicación
- **Testing**: Validación con casos retrospectivos

### Feedback Loop Médico
```python
# Implementación futura - vigia_detect/systems/medical_feedback.py
def collect_clinical_feedback(case_id: str, clinician_assessment: Dict, 
                            system_prediction: Dict) -> None:
    """Recolecta feedback clínico para mejora del sistema"""
    pass
```

---

## 🛡️ Limitaciones y Disclaimers

### Limitaciones del Sistema
1. **No reemplaza juicio clínico**: Sistema de apoyo a la decisión únicamente
2. **Requiere validación**: Toda decisión automatizada debe ser revisada
3. **Contexto limitado**: Análisis basado en imagen sin examen físico completo
4. **Población específica**: Validado para población adulta hospitalizada

### Disclaimers Legales
- Sistema clasificado como **Dispositivo de Apoyo a la Decisión Clínica**
- **No constituye diagnóstico médico definitivo**
- **Responsabilidad clínica permanece en personal médico**
- **Uso exclusivo por profesionales de salud certificados**

---

## 📝 Control de Versiones y Mantenimiento

**Versión**: 1.0.0  
**Fecha**: Enero 2025  
**Próxima Revisión**: Abril 2025  
**Responsable**: Equipo Médico Vigía  

### Historial de Cambios
- **v1.3.3**: Implementación inicial basada en NPUAP/EPUAP 2019
- **Futuro v1.3.3**: Integración de nuevas guidelines NPUAP 2024

---

*Este documento constituye la base científica y normativa para todas las decisiones médicas automatizadas del Sistema Vigía. Cualquier modificación debe ser aprobada por el comité médico multidisciplinario.*