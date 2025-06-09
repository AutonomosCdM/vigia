"""
Simplified Medical Testing for LPP Medical Agent
================================================

Simplified tests to verify the medical testing suite works correctly.
"""

import pytest
from vigia_detect.agents.medical_agent_wrapper import LPPMedicalAgent
from tests.medical.synthetic_patients import get_patient_by_profile, LPPGradeSynthetic


class TestLPPMedicalAgentSimple:
    """Simplified testing of LPP Medical Agent"""
    
    @pytest.fixture
    def lpp_agent(self):
        """Create LPP Medical Agent for testing"""
        return LPPMedicalAgent()
    
    def test_no_lpp_detection(self, lpp_agent):
        """Test analysis when no LPP is detected"""
        patient = get_patient_by_profile("low_risk")
        
        # Empty detection (no LPP)
        mock_detection = {'detections': []}
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        assert result['success'] is True
        assert result['analysis']['lpp_grade'] == 0
        assert result['analysis']['severity_assessment'] == 'RUTINA_PREVENTIVA'
        assert 'preventiv' in result['analysis']['clinical_recommendations'][0].lower()
    
    def test_grade_1_lpp_detection(self, lpp_agent):
        """Test Grade 1 LPP detection and recommendations"""
        patient = get_patient_by_profile("moderate_risk")
        
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_1',
                'confidence': 0.85,
                'anatomical_location': 'sacrum',
                'bbox': [100, 100, 200, 200]
            }]
        }
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        assert result['success'] is True
        assert result['analysis']['lpp_grade'] == 1
        assert result['analysis']['severity_assessment'] == 'ATENCIÓN'
        assert result['analysis']['confidence_score'] == 0.85
        assert result['analysis']['anatomical_location'] == 'sacrum'
        
        # Check recommendations are appropriate for Grade 1
        recommendations = result['analysis']['clinical_recommendations']
        recommendations_text = ' '.join(recommendations).lower()
        assert 'alivio' in recommendations_text
        assert 'presión' in recommendations_text
    
    def test_grade_4_emergency(self, lpp_agent):
        """Test Grade 4 LPP triggers emergency protocols"""
        patient = get_patient_by_profile("emergency")
        
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_4',
                'confidence': 0.92,
                'anatomical_location': 'sacrum',
                'bbox': [100, 100, 200, 200]
            }]
        }
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        assert result['success'] is True
        assert result['analysis']['lpp_grade'] == 4
        assert result['analysis']['severity_assessment'] == 'EMERGENCY'
        assert result['analysis']['requires_human_review'] is True
        assert result['analysis']['requires_specialist_review'] is True
        
        # Check emergency recommendations
        recommendations = result['analysis']['clinical_recommendations']
        recommendations_text = ' '.join(recommendations).lower()
        assert 'quirúrgica' in recommendations_text or 'cirugía' in recommendations_text
    
    def test_low_confidence_triggers_review(self, lpp_agent):
        """Test low confidence triggers human review"""
        patient = get_patient_by_profile("moderate_risk")
        
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_2',
                'confidence': 0.45,  # Low confidence
                'anatomical_location': 'heel',
                'bbox': [100, 100, 200, 200]
            }]
        }
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        assert result['success'] is True
        assert result['analysis']['lpp_grade'] == 2
        assert result['analysis']['confidence_score'] == 0.45
        assert result['analysis']['requires_human_review'] is True
        assert result['analysis']['human_review_reason'] == 'very_low_confidence_detection'
    
    def test_patient_context_diabetes(self, lpp_agent):
        """Test patient context affects recommendations (diabetes)"""
        patient = get_patient_by_profile("high_risk")
        
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_3',
                'confidence': 0.88,
                'anatomical_location': 'sacrum',
                'bbox': [100, 100, 200, 200]
            }]
        }
        
        patient_context = {
            'diabetes': True,
            'anticoagulants': True,
            'malnutrition': False
        }
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection,
            patient_context=patient_context
        )
        
        assert result['success'] is True
        analysis = result['analysis']
        
        # Check diabetes-specific warnings and recommendations
        warnings = analysis['medical_warnings']
        recommendations = analysis['clinical_recommendations']
        contraindications = analysis['contraindications']
        
        # Should have diabetes warnings
        diabetes_warning = any('diabetes' in w.lower() for w in warnings)
        assert diabetes_warning
        
        # Should have glucose control recommendation
        glucose_rec = any('glucémico' in r.lower() or 'control' in r.lower() for r in recommendations)
        assert glucose_rec
        
        # Should have anticoagulant contraindications
        bleeding_warning = any('sangrado' in w.lower() for w in warnings)
        assert bleeding_warning


def test_synthetic_patient_generation():
    """Test that synthetic patient generation works correctly"""
    profiles = ["low_risk", "moderate_risk", "high_risk", "critical", "emergency"]
    
    for profile in profiles:
        patient = get_patient_by_profile(profile)
        
        # Validate patient has required attributes
        assert hasattr(patient, 'patient_code')
        assert hasattr(patient, 'age')
        assert hasattr(patient, 'risk_level')
        assert hasattr(patient, 'has_lpp')
        
        # Validate profile characteristics
        if profile == "low_risk":
            assert patient.has_lpp is False
        elif profile == "emergency":
            assert patient.has_lpp is True
            assert patient.lpp_grade in [LPPGradeSynthetic.GRADE_4]
        
        print(f"✅ {profile}: {patient.patient_code} - Age {patient.age} - LPP: {patient.has_lpp}")


if __name__ == "__main__":
    # Can run directly
    test_synthetic_patient_generation()
    print("🎉 All basic tests would pass!")