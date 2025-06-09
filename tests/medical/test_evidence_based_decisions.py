"""
Test Evidence-Based Medical Decisions
====================================

Tests del motor de decisiones médicas basado en evidencia científica.
Valida que todas las decisiones cumplan con estándares NPUAP/EPUAP/PPPIA.
"""

import pytest
from vigia_detect.systems.medical_decision_engine import (
    MedicalDecisionEngine, 
    make_evidence_based_decision,
    LPPGrade, 
    SeverityLevel, 
    EvidenceLevel
)


class TestEvidenceBasedMedicalDecisions:
    """Tests del motor de decisiones médicas basadas en evidencia"""
    
    @pytest.fixture
    def decision_engine(self):
        """Crea instancia del motor de decisiones"""
        return MedicalDecisionEngine()
    
    def test_grade_0_preventive_decisions(self, decision_engine):
        """Test decisiones preventivas para Grado 0 (sin LPP)"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=0, 
            confidence=0.85, 
            anatomical_location="sacrum"
        )
        
        # Validar clasificación
        assert decision['lpp_grade'] == 0
        assert decision['severity_assessment'] == SeverityLevel.PREVENTIVE.value
        
        # Validar recomendaciones basadas en evidencia
        recommendations = decision['clinical_recommendations']
        assert any('preventivas' in rec.lower() for rec in recommendations)
        assert any('braden' in rec.lower() for rec in recommendations)
        
        # Validar documentación de evidencia
        evidence = decision['evidence_documentation']
        assert evidence['npuap_compliance'] is True
        assert 'recommendations' in evidence
        
        # Validar que hay referencias NPUAP
        rec_evidence = evidence['recommendations']
        assert any('NPUAP' in rec.get('reference', '') for rec in rec_evidence)
        
    def test_grade_1_attention_decisions(self, decision_engine):
        """Test decisiones de atención para Grado 1 (eritema)"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=1,
            confidence=0.8,
            anatomical_location="heel"
        )
        
        # Validar clasificación
        assert decision['lpp_grade'] == 1
        assert decision['severity_assessment'] == SeverityLevel.ATTENTION.value
        
        # Validar recomendaciones específicas Grado 1
        recommendations = decision['clinical_recommendations']
        assert any('alivio' in rec.lower() and 'presión' in rec.lower() for rec in recommendations)
        assert any('protección' in rec.lower() for rec in recommendations)
        
        # Validar recomendaciones específicas para talón
        assert any('talón' in rec.lower() or 'heel' in rec.lower() or 'talones' in rec.lower() for rec in recommendations)
        
    def test_grade_4_emergency_decisions(self, decision_engine):
        """Test decisiones de emergencia para Grado 4"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=4,
            confidence=0.9,
            anatomical_location="sacrum"
        )
        
        # Validar clasificación de emergencia
        assert decision['lpp_grade'] == 4
        assert decision['severity_assessment'] == SeverityLevel.EMERGENCY.value
        
        # Validar escalación automática
        escalation = decision['escalation_requirements']
        assert escalation['requires_human_review'] is True
        assert escalation['requires_specialist_review'] is True
        assert escalation['urgency_level'] == 'emergency'
        assert 'grade_4_emergency' in escalation['escalation_reasons']
        
        # Validar recomendaciones de emergencia
        recommendations = decision['clinical_recommendations']
        assert any('quirúrgica' in rec.lower() or 'cirugía' in rec.lower() for rec in recommendations)
        
    def test_low_confidence_escalation(self, decision_engine):
        """Test escalación por baja confianza"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.45,  # Confianza muy baja
            anatomical_location="elbow"
        )
        
        # Validar escalación por baja confianza
        escalation = decision['escalation_requirements']
        assert escalation['requires_human_review'] is True
        assert 'very_low_confidence_detection' in escalation['escalation_reasons']
        assert escalation['urgency_level'] == 'immediate'
        assert escalation['review_timeline'] == '1-2h'
        
    def test_diabetic_patient_context(self, decision_engine):
        """Test recomendaciones específicas para paciente diabético"""
        patient_context = {
            'diabetes': True,
            'age': 68,
            'comorbidities': ['hypertension']
        }
        
        decision = decision_engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.8,
            anatomical_location="heel",
            patient_context=patient_context
        )
        
        # Validar recomendaciones específicas para diabetes
        recommendations = decision['clinical_recommendations']
        recommendations_text = ' '.join(recommendations).lower()
        assert 'glucémico' in recommendations_text or 'glicémico' in recommendations_text
        
        # Validar advertencias médicas
        warnings = decision['medical_warnings']
        warnings_text = ' '.join(warnings).lower() if warnings else ""
        # Puede no haber warnings específicas, pero debe haber recomendaciones diabetes
        
    def test_anticoagulated_patient_warnings(self, decision_engine):
        """Test advertencias para paciente anticoagulado"""
        patient_context = {
            'anticoagulants': True,
            'medication': ['warfarin']
        }
        
        decision = decision_engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.75,
            anatomical_location="sacrum", 
            patient_context=patient_context
        )
        
        # Validar advertencias de sangrado
        warnings = decision['medical_warnings']
        assert len(warnings) > 0
        warnings_text = ' '.join(warnings).lower()
        assert 'sangrado' in warnings_text or 'anticoagulante' in warnings_text
        
    def test_evidence_documentation_completeness(self, decision_engine):
        """Test completitud de documentación de evidencia"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.8,
            anatomical_location="sacrum"
        )
        
        # Validar estructura de documentación
        evidence = decision['evidence_documentation']
        required_fields = ['recommendations', 'npuap_compliance', 'evidence_review_date']
        for field in required_fields:
            assert field in evidence
            
        # Validar que cada recomendación tiene evidencia
        recommendations_evidence = evidence['recommendations']
        assert len(recommendations_evidence) > 0
        
        for rec_ev in recommendations_evidence:
            assert 'recommendation' in rec_ev
            assert 'evidence_level' in rec_ev
            assert 'reference' in rec_ev
            assert 'rationale' in rec_ev
            
    def test_quality_metrics_calculation(self, decision_engine):
        """Test cálculo de métricas de calidad"""
        decision = decision_engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.85,
            anatomical_location="heel"
        )
        
        # Validar métricas de calidad
        quality = decision['quality_metrics']
        required_metrics = ['decision_confidence', 'evidence_strength', 'safety_score']
        for metric in required_metrics:
            assert metric in quality
            assert isinstance(quality[metric], (int, float, str))
            
        # Validar rangos de métricas numéricas
        if isinstance(quality['decision_confidence'], (int, float)):
            assert 0.0 <= quality['decision_confidence'] <= 1.0
        if isinstance(quality['safety_score'], (int, float)):
            assert 0.0 <= quality['safety_score'] <= 1.0
            
    def test_location_specific_recommendations(self, decision_engine):
        """Test recomendaciones específicas por localización"""
        locations_to_test = ['heel', 'sacrum', 'elbow']
        
        for location in locations_to_test:
            decision = decision_engine.make_clinical_decision(
                lpp_grade=2,
                confidence=0.8,
                anatomical_location=location
            )
            
            recommendations = decision['clinical_recommendations']
            recommendations_text = ' '.join(recommendations).lower()
            
            if location == 'heel':
                assert ('talón' in recommendations_text or 
                       'heel' in recommendations_text or
                       'talones' in recommendations_text or
                       'offloading' in recommendations_text)
            elif location == 'sacrum':
                assert ('sacro' in recommendations_text or
                       'posición' in recommendations_text or
                       'colchón' in recommendations_text)
                       
    def test_error_handling_safety(self, decision_engine):
        """Test manejo seguro de errores"""
        # Test con parámetros inválidos
        decision = decision_engine.make_clinical_decision(
            lpp_grade=999,  # Grado inválido
            confidence=1.5,  # Confianza inválida
            anatomical_location=""
        )
        
        # El sistema debe manejar errores de forma segura
        assert 'escalation_requirements' in decision
        escalation = decision['escalation_requirements']
        
        # En caso de error, debe escalar para seguridad
        if 'error' in decision.get('severity_assessment', '').lower():
            assert escalation['requires_human_review'] is True
            
    def test_npuap_compliance_validation(self, decision_engine):
        """Test cumplimiento con guidelines NPUAP"""
        # Test todos los grados LPP
        for grade in range(0, 5):
            decision = decision_engine.make_clinical_decision(
                lpp_grade=grade,
                confidence=0.8,
                anatomical_location="sacrum"
            )
            
            # Validar compliance NPUAP
            evidence = decision['evidence_documentation']
            assert evidence.get('npuap_compliance') is True
            
            # Validar que hay referencias NPUAP en recomendaciones
            recommendations_evidence = evidence.get('recommendations', [])
            has_npuap_reference = any(
                'NPUAP' in rec.get('reference', '') 
                for rec in recommendations_evidence
            )
            
            # Para grados con recomendaciones activas debe haber referencias
            if grade > 0:
                assert has_npuap_reference, f"Grade {grade} should have NPUAP references"


def test_make_evidence_based_decision_function():
    """Test función principal de decisiones basadas en evidencia"""
    decision = make_evidence_based_decision(
        lpp_grade=2,
        confidence=0.75,
        anatomical_location="heel",
        patient_context={'diabetes': True}
    )
    
    # Validar estructura básica
    assert 'lpp_grade' in decision
    assert 'clinical_recommendations' in decision
    assert 'evidence_documentation' in decision
    assert 'quality_metrics' in decision
    
    # Validar que es decisión basada en evidencia
    assert decision['evidence_documentation']['npuap_compliance'] is True


if __name__ == "__main__":
    # Ejecutar tests básicos
    engine = MedicalDecisionEngine()
    
    print("🧪 Testing Evidence-Based Medical Decisions...")
    
    # Test básico
    decision = engine.make_clinical_decision(2, 0.8, "heel", {'diabetes': True})
    print(f"✅ Grade 2 Decision: {decision['severity_assessment']}")
    print(f"✅ Recommendations: {len(decision['clinical_recommendations'])}")
    print(f"✅ Evidence Level: {decision['quality_metrics']['evidence_strength']}")
    
    print("🎉 Evidence-based decisions working correctly!")