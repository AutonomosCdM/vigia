"""
Tests para integración MINSAL en motor de decisiones médicas
"""

import pytest
from vigia_detect.systems.minsal_medical_decision_engine import (
    MINSALDecisionEngine, make_minsal_clinical_decision, MINSALClassification
)
from vigia_detect.systems.medical_decision_engine import LPPGrade, EvidenceLevel


class TestMINSALIntegration:
    """Test suite para verificar integración MINSAL"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.engine = MINSALDecisionEngine()
    
    def test_minsal_engine_initialization(self):
        """Test inicialización correcta del motor MINSAL"""
        assert self.engine is not None
        assert hasattr(self.engine, 'minsal_guidelines')
        assert hasattr(self.engine, 'extracted_minsal_info')
    
    def test_minsal_classification_mapping(self):
        """Test mapeo correcto clasificaciones MINSAL"""
        # Test Categoría I
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=1, confidence=0.8, anatomical_location="sacrum"
        )
        
        assert 'minsal_classification' in decision
        assert 'Categoría I' in decision['minsal_classification']
        assert decision['minsal_classification'] == MINSALClassification.CATEGORIA_I.value
    
    def test_chilean_terminology_integration(self):
        """Test integración terminología chilena"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=2, confidence=0.75, anatomical_location="heel"
        )
        
        assert 'chilean_terminology' in decision
        terminology = decision['chilean_terminology']
        
        assert 'condition_name' in terminology
        assert 'Lesiones Por Presión' in terminology['condition_name']
        assert 'grade_description' in terminology
        assert 'dermis expuesta' in terminology['grade_description']
    
    def test_minsal_specific_recommendations(self):
        """Test recomendaciones específicas MINSAL"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=1, confidence=0.7, anatomical_location="sacrum"
        )
        
        assert 'minsal_specific_recommendations' in decision
        recommendations = decision['clinical_recommendations']
        
        # Verificar recomendaciones específicas MINSAL
        minsal_terms = ['ELPO', 'MINSAL', 'protocolo', 'redistribución']
        has_minsal_content = any(
            any(term.lower() in rec.lower() for term in minsal_terms)
            for rec in recommendations
        )
        assert has_minsal_content, "No se encontraron recomendaciones específicas MINSAL"
    
    def test_prevention_measures_minsal(self):
        """Test medidas preventivas según MINSAL"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=0, confidence=0.9, anatomical_location="sacrum"
        )
        
        assert 'prevention_measures' in decision
        prevention = decision['prevention_measures']
        
        # Verificar medidas específicas MINSAL
        assert len(prevention) > 0
        minsal_prevention_terms = ['ELPO', 'prominencias', 'redistribución', 'viscoelástico']
        has_minsal_prevention = any(
            any(term.lower() in measure.lower() for term in minsal_prevention_terms)
            for measure in prevention
        )
        assert has_minsal_prevention, "No se encontraron medidas preventivas MINSAL"
    
    def test_chilean_healthcare_context(self):
        """Test contexto sistema salud chileno"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=3, confidence=0.6, anatomical_location="sacrum"
        )
        
        assert 'chilean_healthcare_context' in decision
        context = decision['chilean_healthcare_context']
        
        assert 'healthcare_system' in context
        assert 'prevalence_data' in context
        assert 'resource_considerations' in context
        assert 'regulatory_framework' in context
        
        # Verificar datos específicos Chile
        assert context['healthcare_system'] == 'mixed_public_private'
        assert 'minsal_mandatory' in context['regulatory_framework']
    
    def test_regulatory_compliance(self):
        """Test cumplimiento regulatorio MINSAL"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=2, confidence=0.8, anatomical_location="heel"
        )
        
        assert 'regulatory_compliance' in decision
        compliance = decision['regulatory_compliance']
        
        assert compliance['minsal_compliant'] is True
        assert compliance['national_guidelines'] == '2018'
        assert compliance['jurisdiction'] == 'Chile'
        assert 'NPUAP/EPUAP' in compliance['international_standards']
    
    def test_risk_assessment_chilean_population(self):
        """Test evaluación riesgo población chilena"""
        patient_context = {
            'age': 70,
            'diabetes': True,
            'malnutrition': True,
            'public_healthcare': True
        }
        
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=1, confidence=0.75, anatomical_location="sacrum",
            patient_context=patient_context
        )
        
        assert 'minsal_risk_assessment' in decision
        risk_assessment = decision['minsal_risk_assessment']
        
        assert 'elpo_scale_indicated' in risk_assessment
        assert 'chilean_specific_risks' in risk_assessment
        assert 'healthcare_system_factors' in risk_assessment
        
        # Verificar factores específicos detectados
        chilean_risks = risk_assessment['chilean_specific_risks']
        assert len(chilean_risks) > 0
        
        risk_text = ' '.join(chilean_risks).lower()
        assert 'diabetes' in risk_text or 'desnutrición' in risk_text
    
    def test_evidence_integration_minsal_npuap(self):
        """Test integración evidencia MINSAL + NPUAP"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=2, confidence=0.8, anatomical_location="sacrum"
        )
        
        assert 'evidence_documentation' in decision
        evidence = decision['evidence_documentation']
        
        assert evidence['minsal_integration'] is True
        assert evidence['chilean_guidelines'] == '2018'
        assert evidence['npuap_compliance'] is True
        
        # Verificar referencias MINSAL
        assert 'minsal_evidence_base' in decision
        minsal_evidence = decision['minsal_evidence_base']
        
        assert len(minsal_evidence) > 0
        sources = [ref['source'] for ref in minsal_evidence]
        assert 'MINSAL' in sources
    
    def test_escalation_with_minsal_context(self):
        """Test escalación considerando contexto MINSAL"""
        # Test grado alto con baja confianza
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=4, confidence=0.4, anatomical_location="sacrum"
        )
        
        escalation = decision['escalation_requirements']
        
        assert escalation['requires_human_review'] is True
        assert escalation['requires_specialist_review'] is True
        assert escalation['urgency_level'] in ['emergency', 'immediate']
        
        # Verificar consideraciones sistema chileno
        context = decision['chilean_healthcare_context']
        resource_considerations = context['resource_considerations']
        
        assert 'specialist_availability' in resource_considerations
        assert 'concentrated_urban_areas' in resource_considerations['specialist_availability']
    
    def test_linguistic_adaptation_spanish(self):
        """Test adaptación lingüística al español"""
        decision = self.engine.make_clinical_decision_minsal(
            lpp_grade=1, confidence=0.8, anatomical_location="sacrum"
        )
        
        assert 'linguistic_adaptation' in decision
        linguistic = decision['linguistic_adaptation']
        
        assert linguistic['language'] == 'spanish'
        assert linguistic['terminology_standard'] == 'lesiones_por_presion'
        assert linguistic['cultural_context'] == 'chilean_healthcare_system'
        
        # Verificar que recomendaciones están en español
        recommendations = decision['clinical_recommendations']
        spanish_indicators = ['presión', 'evaluación', 'protección', 'alivio']
        has_spanish = any(
            any(indicator in rec.lower() for indicator in spanish_indicators)
            for rec in recommendations
        )
        assert has_spanish, "Recomendaciones no están en español"
    
    def test_make_minsal_clinical_decision_function(self):
        """Test función principal make_minsal_clinical_decision"""
        decision = make_minsal_clinical_decision(
            lpp_grade=2, confidence=0.75, anatomical_location="heel"
        )
        
        # Verificar estructura de respuesta
        required_keys = [
            'lpp_grade', 'severity_assessment', 'confidence_score',
            'clinical_recommendations', 'minsal_classification',
            'chilean_terminology', 'regulatory_compliance'
        ]
        
        for key in required_keys:
            assert key in decision, f"Clave requerida '{key}' no encontrada"
        
        assert decision['lpp_grade'] == 2
        assert decision['confidence_score'] == 0.75
        assert 'Categoría II' in decision['minsal_classification']


@pytest.mark.integration
class TestMINSALIntegrationScenarios:
    """Tests de escenarios completos integración MINSAL"""
    
    def test_complete_patient_scenario_public_system(self):
        """Test escenario completo paciente sistema público"""
        patient_context = {
            'age': 78,
            'diabetes': True,
            'public_healthcare': True,
            'icu_patient': True,
            'braden_score': 12
        }
        
        decision = make_minsal_clinical_decision(
            lpp_grade=2, confidence=0.7, anatomical_location="sacrum",
            patient_context=patient_context
        )
        
        # Verificar respuesta integral
        assert decision['severity_assessment'] == 'IMPORTANTE'
        assert 'sistema público' in str(decision['minsal_risk_assessment']['healthcare_system_factors']).lower()
        assert decision['regulatory_compliance']['minsal_compliant'] is True
        
        # Verificar adaptación recursos limitados
        healthcare_context = decision['chilean_healthcare_context']
        assert healthcare_context['resource_considerations']['public_system_limitations'] is True
    
    def test_emergency_scenario_grade_4_minsal(self):
        """Test escenario emergencia grado 4 con contexto MINSAL"""
        decision = make_minsal_clinical_decision(
            lpp_grade=4, confidence=0.8, anatomical_location="sacrum"
        )
        
        assert decision['severity_assessment'] == 'EMERGENCY'
        assert 'Categoría IV' in decision['minsal_classification']
        
        # Verificar escalación apropiada
        escalation = decision['escalation_requirements']
        assert escalation['requires_specialist_review'] is True
        assert escalation['urgency_level'] == 'emergency'
        
        # Verificar recomendaciones apropiadas para sistema chileno
        recommendations = decision['clinical_recommendations']
        emergency_terms = ['urgente', 'quirúrgica', 'hospitalización', 'especialista']
        has_emergency_content = any(
            any(term.lower() in rec.lower() for term in emergency_terms)
            for rec in recommendations
        )
        assert has_emergency_content, "No se encontraron recomendaciones de emergencia"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])