"""
Comprehensive Medical Testing for Clinical Processing System
===========================================================

Tests end-to-end clinical processing with synthetic patients.
Validates medical workflow from image analysis to clinical recommendations.

Coverage:
- Image quality validation
- LPP detection accuracy
- Medical recommendation generation
- Clinical workflow compliance
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
from pathlib import Path
import tempfile

from vigia_detect.systems.clinical_processing import ClinicalProcessingSystem
from vigia_detect.core.constants import LPPGrade
from vigia_detect.core.triage_engine import TriageDecision, ClinicalUrgency
from tests.medical.synthetic_patients import (
    generate_test_cohort,
    get_patient_by_profile,
    SyntheticPatient,
    LPPGradeSynthetic,
    RiskLevel
)


class TestClinicalProcessingSystemComprehensive:
    """Comprehensive testing of Clinical Processing System"""
    
    @pytest.fixture
    def clinical_processor(self):
        """Create Clinical Processing System for testing"""
        processor = ClinicalProcessingSystem()
        # Mock dependencies
        processor.cv_detector = Mock()
        processor.lpp_agent = Mock()
        processor.medical_knowledge = Mock()
        processor.supabase_client = Mock()
        processor.audit_service = Mock()
        return processor
    
    @pytest.fixture
    def temp_image_file(self):
        """Create temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake_image_data')
            return f.name
    
    @pytest.mark.medical
    @pytest.mark.parametrize("image_quality", ["high", "medium", "low", "invalid"])
    def test_image_quality_validation_medical_standards(self, clinical_processor, image_quality):
        """
        CRITICAL: Test image quality validation meets medical imaging standards.
        Poor quality images must be rejected to prevent misdiagnosis.
        """
        patient = get_patient_by_profile("moderate_risk")
        standardized_input = self._create_standardized_input(patient)
        
        # Mock triage decision
        triage_decision = TriageDecision(
            route="clinical_image",
            urgency=ClinicalUrgency.MODERATE,
            confidence=0.8,
            reasoning="Standard clinical processing"
        )
        
        # Create image quality scenarios
        quality_specs = {
            "high": {"resolution": (1920, 1080), "file_size": 2048000, "format": "JPEG"},
            "medium": {"resolution": (1280, 720), "file_size": 1024000, "format": "JPEG"},
            "low": {"resolution": (640, 480), "file_size": 512000, "format": "JPEG"},
            "invalid": {"resolution": (100, 100), "file_size": 50000, "format": "BMP"}
        }
        
        spec = quality_specs[image_quality]
        
        # Mock image validation
        if image_quality == "invalid":
            clinical_processor._validate_image_quality = Mock(
                side_effect=Exception("Image quality below medical standards")
            )
        else:
            clinical_processor._validate_image_quality = Mock(return_value={
                'valid': image_quality != "invalid",
                'resolution': spec['resolution'],
                'file_size': spec['file_size'],
                'format': spec['format'],
                'quality_score': {"high": 0.9, "medium": 0.7, "low": 0.5}[image_quality]
            })
        
        # Mock successful processing for valid images
        if image_quality != "invalid":
            clinical_processor.cv_detector.detect_lpp.return_value = {
                'detections': [{'class': 'lpp_grade_2', 'confidence': 0.8}],
                'processing_successful': True
            }
            clinical_processor.lpp_agent.analyze_lpp_image.return_value = {
                'success': True,
                'analysis': {'lpp_grade': 2, 'confidence_score': 0.8}
            }
        
        # Process with different image qualities
        if image_quality == "invalid":
            with pytest.raises(Exception, match="Image quality below medical standards"):
                asyncio.run(clinical_processor.process(standardized_input, triage_decision))
        else:
            result = asyncio.run(clinical_processor.process(standardized_input, triage_decision))
            
            # Validate quality-dependent outcomes
            if image_quality == "high":
                assert result['success'] is True
                assert result['image_quality']['quality_score'] >= 0.8
            elif image_quality == "medium":
                assert result['success'] is True
                assert 0.6 <= result['image_quality']['quality_score'] < 0.8
                # Medium quality might trigger additional validation
            elif image_quality == "low":
                # Low quality should succeed but flag for human review
                assert result['success'] is True
                assert result['image_quality']['quality_score'] < 0.6
                assert result.get('requires_human_review', False) is True
    
    @pytest.mark.medical
    def test_comprehensive_clinical_workflow(self, clinical_processor):
        """
        CRITICAL: Test complete clinical workflow with diverse patient scenarios.
        Validates end-to-end processing maintains medical accuracy.
        """
        # Test scenarios covering different clinical complexities
        test_scenarios = [
            ("low_risk_prevention", "low_risk"),
            ("grade1_early_intervention", "moderate_risk"),
            ("grade2_standard_care", "high_risk"),
            ("grade3_advanced_care", "critical"),
            ("grade4_emergency", "emergency")
        ]
        
        workflow_results = []
        
        for scenario_name, profile in test_scenarios:
            patient = get_patient_by_profile(profile)
            standardized_input = self._create_standardized_input(patient)
            
            # Create scenario-specific triage
            triage_decision = self._create_triage_for_scenario(scenario_name, patient)
            
            # Mock CV detection based on patient profile
            cv_result = self._mock_cv_detection_for_patient(patient)
            clinical_processor.cv_detector.detect_lpp.return_value = cv_result
            
            # Mock LPP analysis
            lpp_analysis = self._mock_lpp_analysis_for_patient(patient)
            clinical_processor.lpp_agent.analyze_lpp_image.return_value = lpp_analysis
            
            # Mock medical knowledge retrieval
            medical_context = self._mock_medical_knowledge_for_patient(patient)
            clinical_processor.medical_knowledge.get_treatment_protocols.return_value = medical_context
            
            # Mock image quality validation (assume good quality)
            clinical_processor._validate_image_quality = Mock(return_value={
                'valid': True, 'quality_score': 0.85
            })
            
            # Process clinical workflow
            result = asyncio.run(clinical_processor.process(standardized_input, triage_decision))
            
            # Validate workflow completion
            assert result['success'] is True, f"Workflow failed for {scenario_name}"
            
            # Validate clinical output structure
            self._validate_clinical_output_structure(result, scenario_name)
            
            # Validate medical logic consistency
            self._validate_medical_logic_consistency(patient, result, scenario_name)
            
            workflow_results.append({
                'scenario': scenario_name,
                'patient_profile': profile,
                'result': result
            })
        
        # Validate overall workflow consistency
        self._validate_workflow_consistency_across_scenarios(workflow_results)
    
    @pytest.mark.medical
    def test_confidence_threshold_medical_safety(self, clinical_processor):
        """
        CRITICAL: Test confidence thresholds ensure medical safety.
        Low confidence detections must trigger appropriate safeguards.
        """
        confidence_scenarios = [
            (0.95, "high_confidence_proceed"),
            (0.75, "medium_confidence_proceed"),
            (0.55, "low_confidence_review"),
            (0.35, "very_low_confidence_escalate")
        ]
        
        for confidence, scenario in confidence_scenarios:
            patient = get_patient_by_profile("high_risk")  # Use high-risk patient
            standardized_input = self._create_standardized_input(patient)
            
            triage_decision = TriageDecision(
                route="clinical_image",
                urgency=ClinicalUrgency.HIGH,
                confidence=0.8,
                reasoning="Testing confidence thresholds"
            )
            
            # Mock CV detection with specific confidence
            clinical_processor.cv_detector.detect_lpp.return_value = {
                'detections': [{
                    'class': 'lpp_grade_3',
                    'confidence': confidence,
                    'bbox': [100, 100, 200, 200]
                }],
                'processing_successful': True,
                'overall_confidence': confidence
            }
            
            # Mock LPP analysis with same confidence
            clinical_processor.lpp_agent.analyze_lpp_image.return_value = {
                'success': True,
                'analysis': {
                    'lpp_grade': 3,
                    'confidence_score': confidence,
                    'severity_assessment': 'URGENTE' if confidence > 0.7 else 'REQUIERE_REVISIÓN',
                    'clinical_recommendations': ['Evaluación especializada']
                }
            }
            
            clinical_processor._validate_image_quality = Mock(return_value={
                'valid': True, 'quality_score': 0.8
            })
            
            # Process
            result = asyncio.run(clinical_processor.process(standardized_input, triage_decision))
            
            # Validate confidence-based safety measures
            assert result['success'] is True
            
            if confidence < 0.6:
                # Very low confidence should trigger human review
                assert result.get('requires_human_review', False) is True
                assert result.get('human_review_reason') == 'low_confidence_detection'
                
                # Should escalate to specialist
                assert result.get('escalated_to_specialist', False) is True
                
            elif confidence < 0.7:
                # Low confidence should flag for review
                assert result.get('requires_human_review', False) is True
                assert 'confidence' in result.get('review_triggers', [])
                
            else:
                # High confidence can proceed normally
                assert result.get('requires_human_review', False) is False
                
            # All results should include confidence score
            assert 'confidence_score' in result
            assert abs(result['confidence_score'] - confidence) < 0.1
    
    @pytest.mark.medical
    def test_medical_contraindications_processing(self, clinical_processor):
        """
        CRITICAL: Test processing of medical contraindications affects treatment recommendations.
        System must consider patient comorbidities in treatment planning.
        """
        # Create patient with multiple contraindications
        patient = get_patient_by_profile("critical")
        patient.anticoagulants = True
        patient.diabetes = True
        patient.compromised_circulation = True
        patient.malnutrition = True
        patient.immunosuppression = True
        
        standardized_input = self._create_standardized_input(patient)
        standardized_input['medical_context'].update({
            'anticoagulants': True,
            'diabetes': True,
            'compromised_circulation': True,
            'malnutrition': True,
            'immunosuppression': True,
            'hemoglobin_g_dl': 9.5,  # Low hemoglobin
            'albumin_g_dl': 2.8      # Low albumin
        })
        
        triage_decision = TriageDecision(
            route="clinical_image",
            urgency=ClinicalUrgency.HIGH,
            confidence=0.85,
            reasoning="Critical patient with contraindications"
        )
        
        # Mock detection
        clinical_processor.cv_detector.detect_lpp.return_value = {
            'detections': [{'class': 'lpp_grade_3', 'confidence': 0.85}],
            'processing_successful': True
        }
        
        # Mock LPP analysis with contraindications
        clinical_processor.lpp_agent.analyze_lpp_image.return_value = {
            'success': True,
            'analysis': {
                'lpp_grade': 3,
                'confidence_score': 0.85,
                'severity_assessment': 'URGENTE_CON_COMORBILIDADES',
                'clinical_recommendations': [
                    'Evaluación vascular por compromiso circulatorio',
                    'Control glucémico estricto por diabetes',
                    'Precaución con desbridamiento por anticoagulantes',
                    'Soporte nutricional por malnutrición',
                    'Profilaxis antibiótica por inmunosupresión'
                ],
                'medical_warnings': [
                    'Riesgo de sangrado por anticoagulantes',
                    'Cicatrización retardada por diabetes',
                    'Riesgo infeccioso por inmunosupresión'
                ],
                'contraindications': [
                    'Evitar desbridamiento agresivo',
                    'Contraindicado vendaje oclusivo',
                    'Requiere monitoreo glicémico'
                ]
            }
        }
        
        clinical_processor._validate_image_quality = Mock(return_value={
            'valid': True, 'quality_score': 0.8
        })
        
        # Process
        result = asyncio.run(clinical_processor.process(standardized_input, triage_decision))
        
        # Validate contraindications are considered
        assert result['success'] is True
        analysis = result['clinical_analysis']['analysis']
        
        # Should include medical warnings
        assert 'medical_warnings' in analysis
        warnings = analysis['medical_warnings']
        assert any('anticoagulante' in warning.lower() for warning in warnings)
        assert any('diabetes' in warning.lower() for warning in warnings)
        
        # Should include contraindications
        assert 'contraindications' in analysis
        contraindications = analysis['contraindications']
        assert len(contraindications) > 0
        
        # Recommendations should be modified for comorbidities
        recommendations = analysis['clinical_recommendations']
        recommendations_text = ' '.join(recommendations).lower()
        assert 'glucémico' in recommendations_text or 'diabetes' in recommendations_text
        assert 'vascular' in recommendations_text or 'circulatorio' in recommendations_text
        assert 'nutricional' in recommendations_text or 'malnutrición' in recommendations_text
        
        # Should escalate due to complexity
        assert result.get('requires_specialist_review', False) is True
        assert result.get('escalation_reason') == 'multiple_contraindications'
    
    @pytest.mark.medical
    def test_audit_trail_completeness_clinical_workflow(self, clinical_processor):
        """
        CRITICAL: Test audit trail completeness for clinical processing.
        Medical workflows require complete traceability for legal compliance.
        """
        patient = get_patient_by_profile("high_risk")
        standardized_input = self._create_standardized_input(patient)
        
        triage_decision = TriageDecision(
            route="clinical_image",
            urgency=ClinicalUrgency.HIGH,
            confidence=0.8,
            reasoning="Audit trail testing"
        )
        
        # Mock successful processing
        clinical_processor.cv_detector.detect_lpp.return_value = {
            'detections': [{'class': 'lpp_grade_2', 'confidence': 0.8}],
            'processing_successful': True
        }
        
        clinical_processor.lpp_agent.analyze_lpp_image.return_value = {
            'success': True,
            'analysis': {'lpp_grade': 2, 'confidence_score': 0.8}
        }
        
        clinical_processor._validate_image_quality = Mock(return_value={
            'valid': True, 'quality_score': 0.85
        })
        
        # Mock supabase storage
        clinical_processor.supabase_client.store_clinical_result.return_value = {
            'success': True, 'record_id': 'rec_12345'
        }
        
        # Process
        result = asyncio.run(clinical_processor.process(standardized_input, triage_decision))
        
        # Validate audit calls
        audit_calls = clinical_processor.audit_service.log_event.call_args_list
        
        # Should have multiple audit points
        assert len(audit_calls) >= 4, "Clinical processing should have at least 4 audit points"
        
        # Validate specific audit events
        logged_events = [call[1]['event_type'] for call in audit_calls]
        required_events = [
            'CLINICAL_PROCESSING_STARTED',
            'IMAGE_QUALITY_VALIDATED',
            'LPP_DETECTION_COMPLETED',
            'CLINICAL_PROCESSING_COMPLETED'
        ]
        
        for required_event in required_events:
            assert required_event in logged_events, f"Missing audit event: {required_event}"
        
        # Validate medical context in all audit entries
        for call in audit_calls:
            audit_data = call[1]
            context = audit_data['context']
            
            # All medical audit entries should include patient code
            assert 'patient_code' in context
            
            # Clinical completion should include full analysis
            if audit_data['event_type'] == 'CLINICAL_PROCESSING_COMPLETED':
                assert 'lpp_grade' in context
                assert 'confidence_score' in context
                assert 'processing_time_ms' in context
                assert 'image_quality_score' in context
    
    def _create_standardized_input(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Create standardized input from synthetic patient"""
        return {
            'patient_code': patient.patient_code,
            'hospital_id': patient.hospital_id,
            'input_type': 'medical_image',
            'image_path': f'test_{patient.patient_code}.jpg',
            'medical_context': {
                'age': patient.age,
                'risk_level': patient.risk_level.value,
                'braden_score': patient.braden_score,
                'diabetes': patient.diabetes,
                'malnutrition': patient.malnutrition,
                'mobility_level': patient.mobility_level.value,
                'hemoglobin_g_dl': patient.hemoglobin_g_dl,
                'albumin_g_dl': patient.albumin_g_dl
            },
            'session_id': f'session_{patient.patient_code}',
            'timestamp': '2025-01-15T10:30:00'
        }
    
    def _create_triage_for_scenario(self, scenario: str, patient: SyntheticPatient) -> TriageDecision:
        """Create appropriate triage decision for scenario"""
        urgency_mapping = {
            "low_risk_prevention": ClinicalUrgency.LOW,
            "grade1_early_intervention": ClinicalUrgency.MODERATE,
            "grade2_standard_care": ClinicalUrgency.HIGH,
            "grade3_advanced_care": ClinicalUrgency.HIGH,
            "grade4_emergency": ClinicalUrgency.EMERGENCY
        }
        
        return TriageDecision(
            route="clinical_image",
            urgency=urgency_mapping[scenario],
            confidence=0.85,
            reasoning=f"Scenario: {scenario}"
        )
    
    def _mock_cv_detection_for_patient(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Mock CV detection based on patient profile"""
        if not patient.has_lpp:
            return {
                'detections': [],
                'processing_successful': True,
                'overall_confidence': 0.9
            }
        
        grade_class_mapping = {
            LPPGradeSynthetic.GRADE_1: 'lpp_grade_1',
            LPPGradeSynthetic.GRADE_2: 'lpp_grade_2',
            LPPGradeSynthetic.GRADE_3: 'lpp_grade_3',
            LPPGradeSynthetic.GRADE_4: 'lpp_grade_4',
            LPPGradeSynthetic.UNSTAGEABLE: 'lpp_unstageable',
            LPPGradeSynthetic.SUSPECTED_DTI: 'lpp_suspected_dti'
        }
        
        return {
            'detections': [{
                'class': grade_class_mapping[patient.lpp_grade],
                'confidence': 0.85,
                'bbox': [100, 100, 200, 200],
                'anatomical_location': patient.lpp_location.value if patient.lpp_location else None
            }],
            'processing_successful': True,
            'overall_confidence': 0.85
        }
    
    def _mock_lpp_analysis_for_patient(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Mock LPP analysis based on patient profile"""
        if not patient.has_lpp:
            return {
                'success': True,
                'analysis': {
                    'lpp_grade': 0,
                    'confidence_score': 0.85,
                    'severity_assessment': 'RUTINA_PREVENTIVA',
                    'clinical_recommendations': ['Continuar medidas preventivas', 'Evaluación Braden regular']
                }
            }
        
        severity_mapping = {
            LPPGradeSynthetic.GRADE_1: 'ATENCIÓN',
            LPPGradeSynthetic.GRADE_2: 'IMPORTANTE',
            LPPGradeSynthetic.GRADE_3: 'URGENTE',
            LPPGradeSynthetic.GRADE_4: 'EMERGENCY',
            LPPGradeSynthetic.UNSTAGEABLE: 'EVALUACIÓN_ESPECIALIZADA',
            LPPGradeSynthetic.SUSPECTED_DTI: 'MONITOREO_ESTRICTO'
        }
        
        return {
            'success': True,
            'analysis': {
                'lpp_grade': patient.lpp_grade.value,
                'confidence_score': 0.85,
                'severity_assessment': severity_mapping[patient.lpp_grade],
                'clinical_recommendations': [f'Tratamiento apropiado para Grado {patient.lpp_grade.value}'],
                'anatomical_location': patient.lpp_location.value if patient.lpp_location else None
            }
        }
    
    def _mock_medical_knowledge_for_patient(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Mock medical knowledge retrieval for patient"""
        return {
            'treatment_protocols': ['Standard LPP Protocol'],
            'risk_factors': ['Age', 'Mobility'],
            'contraindications': [],
            'specialist_consultation_criteria': []
        }
    
    def _validate_clinical_output_structure(self, result: Dict[str, Any], scenario: str):
        """Validate clinical output has required structure"""
        required_fields = [
            'success', 'clinical_analysis', 'image_quality', 
            'confidence_score', 'processing_time_ms'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing {field} in {scenario}"
        
        # Clinical analysis should have nested structure
        analysis = result['clinical_analysis']
        assert 'analysis' in analysis
        
        analysis_data = analysis['analysis']
        clinical_required = ['lpp_grade', 'confidence_score', 'severity_assessment']
        for field in clinical_required:
            assert field in analysis_data, f"Missing {field} in clinical analysis for {scenario}"
    
    def _validate_medical_logic_consistency(self, patient: SyntheticPatient, 
                                          result: Dict[str, Any], scenario: str):
        """Validate medical logic consistency"""
        analysis = result['clinical_analysis']['analysis']
        
        # Grade should match patient profile
        if patient.has_lpp:
            expected_grade = patient.lpp_grade.value
            actual_grade = analysis['lpp_grade']
            assert actual_grade == expected_grade, f"Grade mismatch in {scenario}"
        else:
            assert analysis['lpp_grade'] == 0, f"Should detect no LPP in {scenario}"
        
        # Severity should escalate with grade
        severity = analysis['severity_assessment']
        grade = analysis['lpp_grade']
        
        if grade >= 4:
            assert 'EMERGENCY' in severity or 'URGENTE' in severity
        elif grade >= 3:
            assert 'URGENTE' in severity or 'IMPORTANTE' in severity
        elif grade >= 1:
            assert severity in ['ATENCIÓN', 'IMPORTANTE', 'URGENTE']
    
    def _validate_workflow_consistency_across_scenarios(self, results: List[Dict[str, Any]]):
        """Validate consistency across all workflow scenarios"""
        
        # All scenarios should succeed
        success_rate = sum(1 for r in results if r['result']['success']) / len(results)
        assert success_rate == 1.0, "All clinical workflows should succeed"
        
        # Processing times should be reasonable
        processing_times = [r['result']['processing_time_ms'] for r in results]
        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 5000, f"Average processing time {avg_time}ms too high"
        
        # Confidence scores should be reasonable
        confidence_scores = [r['result']['confidence_score'] for r in results]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        assert avg_confidence >= 0.7, f"Average confidence {avg_confidence} too low"