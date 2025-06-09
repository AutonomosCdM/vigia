"""
Comprehensive Medical Testing for LPP Medical Agent
==================================================

Tests all medical decision-making logic in the LPP Medical Agent using
synthetic patient data and clinical scenarios.

Coverage:
- 120+ synthetic patient cases
- All LPP grades (0-4, Unstageable, DTI)
- Medical decision validation
- NPUAP/EPUAP compliance testing
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import json

from vigia_detect.agents.medical_agent_wrapper import LPPMedicalAgent
from vigia_detect.core.constants import LPPGrade
from tests.medical.synthetic_patients import (
    generate_test_cohort, 
    get_patient_by_profile,
    SyntheticPatient,
    LPPGradeSynthetic,
    RiskLevel
)


class TestLPPMedicalAgentComprehensive:
    """Comprehensive testing of LPP Medical Agent with synthetic patients"""
    
    @pytest.fixture
    def lpp_agent(self):
        """Create LPP Medical Agent for testing"""
        agent = LPPMedicalAgent()
        # Mock dependencies to avoid external calls
        agent.medgemma_client = Mock()
        agent.medical_knowledge = Mock()
        return agent
    
    @pytest.fixture
    def synthetic_cohort(self):
        """Generate comprehensive synthetic patient cohort"""
        return generate_test_cohort(120)
    
    @pytest.mark.medical
    @pytest.mark.parametrize("risk_profile", [
        "low_risk", "moderate_risk", "high_risk", "critical", "emergency"
    ])
    def test_lpp_classification_by_risk_profile(self, lpp_agent, risk_profile):
        """
        CRITICAL: Test LPP classification accuracy across all risk profiles.
        Reference: NPUAP/EPUAP/PPPIA Clinical Practice Guideline
        """
        # Get patient for specific risk profile
        patient = get_patient_by_profile(risk_profile)
        
        # Create mock image analysis result
        mock_detection = self._create_mock_detection(patient)
        
        # Mock MedGemma response based on patient profile
        mock_medgemma_response = self._create_mock_medgemma_response(patient)
        lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_medgemma_response
        
        # Process with LPP agent
        result = lpp_agent.analyze_lpp_image(
            image_path="test_image.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        # Validate medical classification
        assert result['success'] is True
        assert 'lpp_grade' in result['analysis']
        assert 'severity_assessment' in result['analysis']
        assert 'clinical_recommendations' in result['analysis']
        
        # Validate LPP grade matches expected profile
        detected_grade = result['analysis']['lpp_grade']
        if patient.has_lpp:
            expected_grade = patient.lpp_grade.value
            assert detected_grade == expected_grade, f"Grade mismatch for {risk_profile}"
        else:
            assert detected_grade == 0, f"Should detect no LPP for {risk_profile}"
        
        # Validate severity assessment is appropriate
        severity = result['analysis']['severity_assessment']
        expected_severities = {
            "low_risk": ["RUTINA", "PREVENTIVO"],
            "moderate_risk": ["ATENCIÓN", "PREVENTIVO"],
            "high_risk": ["IMPORTANTE", "ATENCIÓN"],
            "critical": ["URGENTE", "IMPORTANTE"],
            "emergency": ["EMERGENCY", "URGENTE"]
        }
        assert any(exp in severity for exp in expected_severities[risk_profile])
    
    @pytest.mark.medical
    def test_comprehensive_patient_cohort(self, lpp_agent, synthetic_cohort):
        """
        CRITICAL: Test LPP agent with full 120-patient synthetic cohort.
        Validates medical decision consistency across diverse patient population.
        """
        results = []
        errors = []
        
        for patient in synthetic_cohort:
            try:
                # Create detection result for patient
                mock_detection = self._create_mock_detection(patient)
                
                # Mock MedGemma for this patient
                mock_response = self._create_mock_medgemma_response(patient)
                lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_response
                
                # Analyze with LPP agent
                result = lpp_agent.analyze_lpp_image(
                    image_path=f"test_{patient.patient_code}.jpg",
                    patient_code=patient.patient_code,
                    detection_result=mock_detection
                )
                
                # Validate result structure
                assert result['success'] is True
                assert 'analysis' in result
                analysis = result['analysis']
                
                # Validate required fields
                required_fields = [
                    'lpp_grade', 'severity_assessment', 'clinical_recommendations',
                    'confidence_score', 'anatomical_location'
                ]
                for field in required_fields:
                    assert field in analysis, f"Missing {field} for {patient.patient_code}"
                
                # Validate medical logic
                self._validate_medical_logic(patient, analysis)
                
                results.append({
                    'patient_code': patient.patient_code,
                    'input_profile': {
                        'age': patient.age,
                        'risk_level': patient.risk_level.value,
                        'has_lpp': patient.has_lpp,
                        'expected_grade': patient.lpp_grade.value if patient.lpp_grade else 0
                    },
                    'output_analysis': analysis
                })
                
            except Exception as e:
                errors.append({
                    'patient_code': patient.patient_code,
                    'error': str(e),
                    'patient_profile': {
                        'age': patient.age,
                        'risk_level': patient.risk_level.value,
                        'has_lpp': patient.has_lpp
                    }
                })
        
        # Validate cohort results
        success_rate = len(results) / len(synthetic_cohort)
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        
        if errors:
            print(f"\nErrors encountered in {len(errors)} patients:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error['patient_code']}: {error['error']}")
        
        # Validate medical accuracy
        self._validate_cohort_medical_accuracy(results)
    
    @pytest.mark.medical
    @pytest.mark.parametrize("lpp_grade", [0, 1, 2, 3, 4])
    def test_lpp_grade_specific_recommendations(self, lpp_agent, lpp_grade):
        """
        CRITICAL: Test that recommendations are appropriate for each LPP grade.
        Reference: NPUAP Clinical Practice Guideline recommendations
        """
        # Create patient with specific LPP grade
        grade_mapping = {
            0: None,
            1: LPPGradeSynthetic.GRADE_1,
            2: LPPGradeSynthetic.GRADE_2,
            3: LPPGradeSynthetic.GRADE_3,
            4: LPPGradeSynthetic.GRADE_4
        }
        
        patient = get_patient_by_profile("moderate_risk")
        patient.lpp_grade = grade_mapping[lpp_grade]
        patient.has_lpp = lpp_grade > 0
        
        # Create mock detection
        mock_detection = self._create_mock_detection(patient)
        mock_response = self._create_mock_medgemma_response(patient)
        lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_response
        
        # Analyze
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection
        )
        
        analysis = result['analysis']
        recommendations = analysis['clinical_recommendations']
        
        # Validate grade-specific recommendations
        expected_recommendations = {
            0: ["prevención", "braden", "posicionamiento"],
            1: ["alivio", "presión", "protección", "cutánea"],
            2: ["curación", "húmeda", "apósitos", "hidrocoloides"],
            3: ["desbridamiento", "apósitos", "avanzados", "especialista"],
            4: ["cirugía", "quirúrgica", "dolor", "cuidados", "avanzados"]
        }
        
        expected_keywords = expected_recommendations[lpp_grade]
        recommendations_text = " ".join(recommendations).lower()
        
        matched_keywords = sum(1 for keyword in expected_keywords 
                              if keyword in recommendations_text)
        
        assert matched_keywords >= 2, (
            f"Grade {lpp_grade} recommendations should contain at least 2 of {expected_keywords}. "
            f"Got: {recommendations}"
        )
    
    @pytest.mark.medical
    def test_anatomical_location_specific_logic(self, lpp_agent):
        """
        CRITICAL: Test location-specific medical recommendations.
        Different anatomical locations require different approaches.
        """
        anatomical_locations = [
            "sacrum", "heel", "ankle", "elbow", "shoulder", "trochanter"
        ]
        
        for location in anatomical_locations:
            patient = get_patient_by_profile("high_risk")
            patient.lpp_location = location
            
            # Create location-specific detection
            mock_detection = {
                'detections': [{
                    'class': 'lpp_grade_2',
                    'confidence': 0.85,
                    'anatomical_location': location,
                    'bbox': [100, 100, 200, 200]
                }]
            }
            
            mock_response = self._create_mock_medgemma_response(patient)
            lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_response
            
            result = lpp_agent.analyze_lpp_image(
                image_path="test.jpg",
                patient_code=patient.patient_code,
                detection_result=mock_detection
            )
            
            analysis = result['analysis']
            
            # Validate location is correctly identified
            assert analysis['anatomical_location'] == location
            
            # Validate location-specific considerations
            recommendations = " ".join(analysis['clinical_recommendations']).lower()
            
            if location == "heel":
                assert "talón" in recommendations or "heel" in recommendations
                assert "protección" in recommendations or "offloading" in recommendations
            elif location == "sacrum":
                assert "sacro" in recommendations or "sacrum" in recommendations
                assert "posicionamiento" in recommendations or "positioning" in recommendations
            elif location in ["elbow", "shoulder"]:
                assert "codo" in recommendations or "hombro" in recommendations or location in recommendations
    
    @pytest.mark.medical
    def test_confidence_score_correlation_with_medical_urgency(self, lpp_agent):
        """
        CRITICAL: Test that confidence scores correlate appropriately with medical urgency.
        Low confidence should trigger human review for medical safety.
        """
        confidence_scenarios = [
            (0.95, "high_confidence"),
            (0.75, "medium_confidence"), 
            (0.55, "low_confidence"),
            (0.35, "very_low_confidence")
        ]
        
        for confidence, scenario in confidence_scenarios:
            patient = get_patient_by_profile("critical")
            
            # Create detection with specific confidence
            mock_detection = {
                'detections': [{
                    'class': 'lpp_grade_3',
                    'confidence': confidence,
                    'bbox': [100, 100, 200, 200]
                }]
            }
            
            mock_response = self._create_mock_medgemma_response(patient)
            mock_response['confidence'] = confidence
            lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_response
            
            result = lpp_agent.analyze_lpp_image(
                image_path="test.jpg",
                patient_code=patient.patient_code,
                detection_result=mock_detection
            )
            
            analysis = result['analysis']
            
            # Validate confidence is properly reported
            assert 'confidence_score' in analysis
            reported_confidence = analysis['confidence_score']
            assert abs(reported_confidence - confidence) < 0.1
            
            # Validate human review trigger for low confidence
            if confidence < 0.6:
                assert analysis.get('requires_human_review', False) is True
                assert "baja confianza" in analysis['severity_assessment'].lower() or \
                       "revisión" in analysis['severity_assessment'].lower()
            
            # Validate urgency escalation for high-grade + low confidence
            if patient.lpp_grade and patient.lpp_grade.value >= 3 and confidence < 0.7:
                assert "urgente" in analysis['severity_assessment'].lower() or \
                       "emergency" in analysis['severity_assessment'].lower()
    
    @pytest.mark.medical
    def test_medical_contraindications_and_warnings(self, lpp_agent):
        """
        CRITICAL: Test detection of medical contraindications and warnings.
        System should flag conditions that affect treatment decisions.
        """
        # Test patient with multiple contraindications
        patient = get_patient_by_profile("critical")
        patient.anticoagulants = True
        patient.diabetes = True
        patient.malnutrition = True
        patient.compromised_circulation = True
        
        mock_detection = self._create_mock_detection(patient)
        mock_response = self._create_mock_medgemma_response(patient)
        lpp_agent.medgemma_client.analyze_medical_image.return_value = mock_response
        
        result = lpp_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code=patient.patient_code,
            detection_result=mock_detection,
            patient_context={
                'anticoagulants': patient.anticoagulants,
                'diabetes': patient.diabetes,
                'malnutrition': patient.malnutrition,
                'compromised_circulation': patient.compromised_circulation
            }
        )
        
        analysis = result['analysis']
        
        # Validate warnings are included
        warnings = analysis.get('medical_warnings', [])
        recommendations = " ".join(analysis['clinical_recommendations']).lower()
        
        # Check for specific warnings based on conditions
        if patient.anticoagulants:
            assert any("anticoagulante" in warning.lower() or "sangrado" in warning.lower() 
                      for warning in warnings) or "sangrado" in recommendations
        
        if patient.diabetes:
            assert any("diabetes" in warning.lower() or "glucemia" in warning.lower() 
                      for warning in warnings) or "glucemia" in recommendations
        
        if patient.malnutrition:
            assert any("nutrición" in warning.lower() or "albúmina" in warning.lower() 
                      for warning in warnings) or "nutrición" in recommendations
    
    def _create_mock_detection(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Create mock CV detection result based on patient profile"""
        if not patient.has_lpp or not patient.lpp_grade:
            return {'detections': []}
        
        grade_class_mapping = {
            LPPGradeSynthetic.GRADE_1: 'lpp_grade_1',
            LPPGradeSynthetic.GRADE_2: 'lpp_grade_2',
            LPPGradeSynthetic.GRADE_3: 'lpp_grade_3',
            LPPGradeSynthetic.GRADE_4: 'lpp_grade_4',
            LPPGradeSynthetic.UNSTAGEABLE: 'lpp_unstageable',
            LPPGradeSynthetic.SUSPECTED_DTI: 'lpp_suspected_dti'
        }
        
        # Confidence based on risk level and grade
        confidence_base = 0.85
        if patient.risk_level == RiskLevel.CRITICAL:
            confidence_base = 0.9  # More obvious in critical patients
        elif patient.risk_level == RiskLevel.LOW:
            confidence_base = 0.75  # Harder to detect in low-risk
        
        # Adjust for grade complexity
        if patient.lpp_grade in [LPPGradeSynthetic.UNSTAGEABLE, LPPGradeSynthetic.SUSPECTED_DTI]:
            confidence_base -= 0.15  # These are harder to classify
        
        return {
            'detections': [{
                'class': grade_class_mapping[patient.lpp_grade],
                'confidence': max(0.5, min(0.98, confidence_base + random.uniform(-0.1, 0.1))),
                'bbox': [100, 100, 200, 200],
                'anatomical_location': patient.lpp_location.value if patient.lpp_location else None,
                'area': random.randint(500, 5000)
            }],
            'processing_time': 0.5
        }
    
    def _create_mock_medgemma_response(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Create mock MedGemma response based on patient profile"""
        if not patient.has_lpp:
            return {
                'analysis': f"No se observa evidencia de LPP en paciente {patient.patient_code}. Continuar con medidas preventivas.",
                'confidence': 0.8,
                'recommendations': ["Continuar prevención según protocolo", "Evaluación Braden regular"]
            }
        
        grade_descriptions = {
            LPPGradeSynthetic.GRADE_1: "eritema no blanqueable",
            LPPGradeSynthetic.GRADE_2: "pérdida parcial del espesor de la piel",
            LPPGradeSynthetic.GRADE_3: "pérdida completa del espesor de la piel",
            LPPGradeSynthetic.GRADE_4: "pérdida completa del tejido",
            LPPGradeSynthetic.UNSTAGEABLE: "lesión no clasificable",
            LPPGradeSynthetic.SUSPECTED_DTI: "sospecha de lesión de tejido profundo"
        }
        
        analysis_text = f"LPP Grado {patient.lpp_grade.value} - {grade_descriptions[patient.lpp_grade]} "
        analysis_text += f"en {patient.lpp_location.value if patient.lpp_location else 'localización no especificada'}. "
        
        if patient.age > 75:
            analysis_text += "Paciente de edad avanzada con factores de riesgo aumentados. "
        
        if patient.diabetes:
            analysis_text += "Considerar diabetes en plan de tratamiento. "
            
        return {
            'analysis': analysis_text,
            'confidence': 0.85,
            'recommendations': self._get_grade_specific_recommendations(patient.lpp_grade)
        }
    
    def _get_grade_specific_recommendations(self, grade: LPPGradeSynthetic) -> List[str]:
        """Get appropriate recommendations for LPP grade"""
        recommendations = {
            LPPGradeSynthetic.GRADE_1: [
                "Alivio inmediato de presión",
                "Protección cutánea",
                "Reposicionamiento cada 2 horas"
            ],
            LPPGradeSynthetic.GRADE_2: [
                "Curación húmeda",
                "Apósitos hidrocoloides",
                "Evaluación dolor"
            ],
            LPPGradeSynthetic.GRADE_3: [
                "Desbridamiento si necesario",
                "Apósitos avanzados",
                "Evaluación especializada"
            ],
            LPPGradeSynthetic.GRADE_4: [
                "Evaluación quirúrgica urgente",
                "Manejo dolor avanzado",
                "Cuidados multidisciplinarios"
            ],
            LPPGradeSynthetic.UNSTAGEABLE: [
                "Evaluación especializada",
                "Desbridamiento para clasificación",
                "Monitoreo estricto"
            ],
            LPPGradeSynthetic.SUSPECTED_DTI: [
                "Monitoreo estricto evolución",
                "Protección área sospechosa",
                "Reevaluación en 24-48h"
            ]
        }
        return recommendations.get(grade, ["Evaluación médica"])
    
    def _validate_medical_logic(self, patient: SyntheticPatient, analysis: Dict[str, Any]):
        """Validate that analysis follows medical logic"""
        
        # Grade should match patient's actual condition
        if patient.has_lpp and patient.lpp_grade:
            assert analysis['lpp_grade'] == patient.lpp_grade.value
        else:
            assert analysis['lpp_grade'] == 0
        
        # Severity should escalate with grade
        severity = analysis['severity_assessment'].lower()
        if patient.has_lpp and patient.lpp_grade:
            if patient.lpp_grade.value >= 4:
                assert "emergency" in severity or "urgente" in severity
            elif patient.lpp_grade.value >= 3:
                assert "urgente" in severity or "importante" in severity
            elif patient.lpp_grade.value >= 2:
                assert "importante" in severity or "atención" in severity
        
        # Confidence should be reasonable
        confidence = analysis.get('confidence_score', 0)
        assert 0.0 <= confidence <= 1.0
        
        # Recommendations should exist for any detected LPP
        if patient.has_lpp:
            recommendations = analysis.get('clinical_recommendations', [])
            assert len(recommendations) > 0
    
    def _validate_cohort_medical_accuracy(self, results: List[Dict[str, Any]]):
        """Validate medical accuracy across the entire cohort"""
        
        # Calculate accuracy metrics
        correct_classifications = 0
        total_lpp_cases = 0
        severity_escalations = 0
        
        for result in results:
            input_profile = result['input_profile']
            output_analysis = result['output_analysis']
            
            # Check grade classification accuracy
            expected_grade = input_profile['expected_grade']
            detected_grade = output_analysis['lpp_grade']
            
            if expected_grade == detected_grade:
                correct_classifications += 1
            
            if expected_grade > 0:
                total_lpp_cases += 1
            
            # Check severity escalation for high grades
            if detected_grade >= 3:
                severity = output_analysis['severity_assessment'].lower()
                if "urgente" in severity or "emergency" in severity:
                    severity_escalations += 1
        
        # Validate accuracy thresholds
        overall_accuracy = correct_classifications / len(results) if results else 0
        assert overall_accuracy >= 0.85, f"Overall accuracy {overall_accuracy:.2%} below 85% threshold"
        
        # Validate severity escalation for critical cases
        high_grade_cases = sum(1 for r in results if r['output_analysis']['lpp_grade'] >= 3)
        if high_grade_cases > 0:
            escalation_rate = severity_escalations / high_grade_cases
            assert escalation_rate >= 0.8, f"High-grade escalation rate {escalation_rate:.2%} below 80%"

import random  # Add this import for the random functions used