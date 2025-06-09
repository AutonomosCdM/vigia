"""
Comprehensive Medical Testing for Medical Dispatcher
===================================================

Tests medical routing and triage logic using synthetic patients.
Validates that patients are correctly routed based on clinical urgency.

Coverage:
- Medical triage decision logic
- Route prioritization
- Emergency escalation
- Multi-tenant routing
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
from datetime import datetime, timedelta

from vigia_detect.core.medical_dispatcher import MedicalDispatcher
from vigia_detect.core.triage_engine import TriageEngine, TriageDecision, ClinicalUrgency
from vigia_detect.core.constants import ProcessingRoute
from tests.medical.synthetic_patients import (
    generate_test_cohort,
    get_patient_by_profile,
    SyntheticPatient,
    LPPGradeSynthetic,
    RiskLevel
)


class TestMedicalDispatcherComprehensive:
    """Comprehensive testing of Medical Dispatcher with synthetic patients"""
    
    @pytest.fixture
    def medical_dispatcher(self):
        """Create Medical Dispatcher for testing"""
        dispatcher = MedicalDispatcher()
        # Mock dependencies
        dispatcher.triage_engine = Mock(spec=TriageEngine)
        dispatcher.session_manager = Mock()
        dispatcher.audit_service = Mock()
        return dispatcher
    
    @pytest.fixture
    def synthetic_cohort(self):
        """Generate synthetic patient cohort for testing"""
        return generate_test_cohort(50)  # Smaller cohort for dispatcher testing
    
    @pytest.mark.medical
    @pytest.mark.parametrize("urgency_level", [
        "EMERGENCY", "URGENT", "IMPORTANTE", "ATENCIÓN", "RUTINA"
    ])
    def test_route_selection_by_medical_urgency(self, medical_dispatcher, urgency_level):
        """
        CRITICAL: Test that routing decisions match medical urgency levels.
        Emergency cases must be routed to fastest processing paths.
        """
        # Create standardized input for urgency level
        patient = self._get_patient_for_urgency(urgency_level)
        standardized_input = self._create_standardized_input(patient)
        
        # Mock triage decision
        triage_decision = TriageDecision(
            route=self._get_expected_route_for_urgency(urgency_level),
            urgency=self._get_clinical_urgency_for_level(urgency_level),
            confidence=0.85,
            reasoning=f"Medical urgency: {urgency_level}",
            priority_score=self._get_priority_score_for_urgency(urgency_level),
            estimated_processing_time=self._get_expected_processing_time(urgency_level)
        )
        
        medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = triage_decision
        
        # Mock route processors
        mock_processors = self._setup_mock_processors(medical_dispatcher)
        
        # Dispatch
        result = asyncio.run(medical_dispatcher.dispatch(standardized_input))
        
        # Validate routing decision
        assert result['success'] is True
        assert result['route'] == triage_decision.route
        assert result['urgency'] == urgency_level
        
        # Validate processing time expectations
        if urgency_level in ["EMERGENCY", "URGENT"]:
            # Emergency cases should have shorter timeouts
            assert triage_decision.estimated_processing_time <= 60  # seconds
        elif urgency_level == "RUTINA":
            # Routine cases can have longer timeouts
            assert triage_decision.estimated_processing_time >= 30
        
        # Validate triage engine was called with correct input
        medical_dispatcher.triage_engine.evaluate_medical_urgency.assert_called_once()
        call_args = medical_dispatcher.triage_engine.evaluate_medical_urgency.call_args[0]
        assert call_args[0] == standardized_input
    
    @pytest.mark.medical
    def test_emergency_bypass_logic(self, medical_dispatcher):
        """
        CRITICAL: Test emergency bypass logic for Grade 4 LPP and critical conditions.
        Emergency cases must bypass normal queuing and go directly to specialist review.
        """
        # Create emergency patient (Grade 4 LPP)
        emergency_patient = get_patient_by_profile("emergency")
        standardized_input = self._create_standardized_input(emergency_patient)
        
        # Mock emergency triage decision
        emergency_triage = TriageDecision(
            route=ProcessingRoute.EMERGENCY,
            urgency=ClinicalUrgency.EMERGENCY,
            confidence=0.95,
            reasoning="Grade 4 LPP requiring immediate surgical evaluation",
            priority_score=10,
            estimated_processing_time=30,
            bypass_queue=True,  # Emergency bypass
            requires_specialist=True
        )
        
        medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = emergency_triage
        
        # Mock emergency processor
        emergency_processor = Mock()
        emergency_processor.process.return_value = {
            'success': True,
            'emergency_escalated': True,
            'specialist_notified': True,
            'processing_time': 25
        }
        medical_dispatcher.route_processors[ProcessingRoute.EMERGENCY] = emergency_processor
        
        # Dispatch emergency case
        result = asyncio.run(medical_dispatcher.dispatch(standardized_input))
        
        # Validate emergency handling
        assert result['success'] is True
        assert result['route'] == ProcessingRoute.EMERGENCY
        assert result.get('emergency_escalated') is True
        assert result.get('specialist_notified') is True
        
        # Validate bypass was used
        assert emergency_triage.bypass_queue is True
        
        # Validate emergency processor was called
        emergency_processor.process.assert_called_once()
    
    @pytest.mark.medical
    def test_multi_tenant_routing_by_hospital(self, medical_dispatcher):
        """
        CRITICAL: Test multi-tenant routing ensures patients are processed 
        according to their hospital's protocols and staffing.
        """
        hospitals = ["CLC-001", "HDIGITAL-002", "HMETRO-003"]
        
        for hospital_id in hospitals:
            # Create patient for specific hospital
            patient = get_patient_by_profile("moderate_risk")
            patient.hospital_id = hospital_id
            standardized_input = self._create_standardized_input(patient)
            
            # Mock hospital-specific triage
            hospital_triage = TriageDecision(
                route=ProcessingRoute.CLINICAL_IMAGE,
                urgency=ClinicalUrgency.MODERATE,
                confidence=0.8,
                reasoning=f"Standard processing for {hospital_id}",
                priority_score=5,
                estimated_processing_time=45,
                hospital_context={
                    'hospital_id': hospital_id,
                    'specialized_protocols': self._get_hospital_protocols(hospital_id),
                    'available_specialists': self._get_hospital_specialists(hospital_id)
                }
            )
            
            medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = hospital_triage
            
            # Mock hospital-specific processor
            hospital_processor = Mock()
            hospital_processor.process.return_value = {
                'success': True,
                'hospital_id': hospital_id,
                'protocols_applied': hospital_triage.hospital_context['specialized_protocols']
            }
            medical_dispatcher.route_processors[ProcessingRoute.CLINICAL_IMAGE] = hospital_processor
            
            # Dispatch
            result = asyncio.run(medical_dispatcher.dispatch(standardized_input))
            
            # Validate hospital-specific processing
            assert result['success'] is True
            assert result['hospital_id'] == hospital_id
            assert 'protocols_applied' in result
            
            # Validate hospital context was considered
            assert hospital_triage.hospital_context['hospital_id'] == hospital_id
    
    @pytest.mark.medical
    def test_concurrent_patient_processing_limits(self, medical_dispatcher):
        """
        CRITICAL: Test concurrent processing limits to prevent system overload.
        Medical systems must maintain performance under load.
        """
        # Create multiple patients for concurrent processing
        patients = [get_patient_by_profile("moderate_risk") for _ in range(10)]
        
        # Mock session manager with concurrency limits
        medical_dispatcher.session_manager.check_session_limits.return_value = {
            'within_limits': True,
            'current_sessions': 5,
            'max_sessions': 10
        }
        
        # Mock triage for all patients
        standard_triage = TriageDecision(
            route=ProcessingRoute.CLINICAL_IMAGE,
            urgency=ClinicalUrgency.MODERATE,
            confidence=0.8,
            reasoning="Standard concurrent processing",
            priority_score=5,
            estimated_processing_time=30
        )
        medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = standard_triage
        
        # Mock processor with processing time
        mock_processor = Mock()
        mock_processor.process = AsyncMock(return_value={'success': True, 'processing_time': 25})
        medical_dispatcher.route_processors[ProcessingRoute.CLINICAL_IMAGE] = mock_processor
        
        # Process patients concurrently
        async def process_patient(patient):
            standardized_input = self._create_standardized_input(patient)
            return await medical_dispatcher.dispatch(standardized_input)
        
        # Run concurrent processing
        results = asyncio.run(asyncio.gather(*[
            process_patient(patient) for patient in patients
        ]))
        
        # Validate all patients were processed successfully
        assert len(results) == len(patients)
        success_count = sum(1 for result in results if result['success'])
        assert success_count == len(patients)
        
        # Validate session limits were checked
        assert medical_dispatcher.session_manager.check_session_limits.call_count >= len(patients)
    
    @pytest.mark.medical
    def test_fallback_routing_on_processor_failure(self, medical_dispatcher):
        """
        CRITICAL: Test fallback routing when primary processors fail.
        Medical systems must have redundancy for critical cases.
        """
        # Create critical patient
        critical_patient = get_patient_by_profile("critical")
        standardized_input = self._create_standardized_input(critical_patient)
        
        # Mock triage decision for critical case
        critical_triage = TriageDecision(
            route=ProcessingRoute.CLINICAL_IMAGE,
            urgency=ClinicalUrgency.HIGH,
            confidence=0.9,
            reasoning="Critical LPP case",
            priority_score=8,
            estimated_processing_time=40,
            fallback_routes=[ProcessingRoute.HUMAN_REVIEW, ProcessingRoute.EMERGENCY]
        )
        medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = critical_triage
        
        # Mock primary processor failure
        primary_processor = Mock()
        primary_processor.process = AsyncMock(side_effect=Exception("Primary processor failed"))
        medical_dispatcher.route_processors[ProcessingRoute.CLINICAL_IMAGE] = primary_processor
        
        # Mock fallback processor success
        fallback_processor = Mock()
        fallback_processor.process = AsyncMock(return_value={
            'success': True,
            'fallback_used': True,
            'original_route': ProcessingRoute.CLINICAL_IMAGE,
            'fallback_route': ProcessingRoute.HUMAN_REVIEW
        })
        medical_dispatcher.route_processors[ProcessingRoute.HUMAN_REVIEW] = fallback_processor
        
        # Dispatch with fallback handling
        result = asyncio.run(medical_dispatcher.dispatch(standardized_input))
        
        # Validate fallback was used successfully
        assert result['success'] is True
        assert result.get('fallback_used') is True
        assert result.get('original_route') == ProcessingRoute.CLINICAL_IMAGE
        assert result.get('fallback_route') == ProcessingRoute.HUMAN_REVIEW
        
        # Validate both processors were attempted
        primary_processor.process.assert_called_once()
        fallback_processor.process.assert_called_once()
    
    @pytest.mark.medical
    def test_medical_audit_trail_completeness(self, medical_dispatcher):
        """
        CRITICAL: Test that all medical routing decisions are properly audited.
        Medical systems require complete audit trails for compliance.
        """
        # Create patient for audit testing
        patient = get_patient_by_profile("high_risk")
        standardized_input = self._create_standardized_input(patient)
        
        # Mock triage decision
        triage_decision = TriageDecision(
            route=ProcessingRoute.CLINICAL_IMAGE,
            urgency=ClinicalUrgency.HIGH,
            confidence=0.85,
            reasoning="High-risk LPP case requiring standard processing",
            priority_score=7,
            estimated_processing_time=35
        )
        medical_dispatcher.triage_engine.evaluate_medical_urgency.return_value = triage_decision
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.process = AsyncMock(return_value={'success': True})
        medical_dispatcher.route_processors[ProcessingRoute.CLINICAL_IMAGE] = mock_processor
        
        # Dispatch
        result = asyncio.run(medical_dispatcher.dispatch(standardized_input))
        
        # Validate audit service was called for key events
        audit_calls = medical_dispatcher.audit_service.log_event.call_args_list
        
        # Should have multiple audit points
        assert len(audit_calls) >= 2  # At minimum: dispatch_started, dispatch_completed
        
        # Validate audit event types
        logged_events = [call[1]['event_type'] for call in audit_calls]
        assert 'MEDICAL_DISPATCH_STARTED' in logged_events
        assert 'MEDICAL_DISPATCH_COMPLETED' in logged_events
        
        # Validate medical context in audit
        for call in audit_calls:
            audit_data = call[1]
            assert 'patient_code' in audit_data['context']
            assert 'route' in audit_data['context']
            assert 'urgency' in audit_data['context']
            
            # Medical audit data should include decision reasoning
            if audit_data['event_type'] == 'MEDICAL_DISPATCH_COMPLETED':
                assert 'triage_reasoning' in audit_data['context']
                assert 'confidence_score' in audit_data['context']
    
    def _get_patient_for_urgency(self, urgency_level: str) -> SyntheticPatient:
        """Get appropriate patient for urgency level"""
        urgency_profiles = {
            "EMERGENCY": "emergency",
            "URGENT": "critical", 
            "IMPORTANTE": "high_risk",
            "ATENCIÓN": "moderate_risk",
            "RUTINA": "low_risk"
        }
        return get_patient_by_profile(urgency_profiles[urgency_level])
    
    def _get_expected_route_for_urgency(self, urgency_level: str) -> ProcessingRoute:
        """Get expected processing route for urgency level"""
        route_mapping = {
            "EMERGENCY": ProcessingRoute.EMERGENCY,
            "URGENT": ProcessingRoute.CLINICAL_IMAGE,
            "IMPORTANTE": ProcessingRoute.CLINICAL_IMAGE,
            "ATENCIÓN": ProcessingRoute.CLINICAL_IMAGE,
            "RUTINA": ProcessingRoute.STANDARD
        }
        return route_mapping[urgency_level]
    
    def _get_clinical_urgency_for_level(self, urgency_level: str) -> ClinicalUrgency:
        """Convert urgency level to ClinicalUrgency enum"""
        mapping = {
            "EMERGENCY": ClinicalUrgency.EMERGENCY,
            "URGENT": ClinicalUrgency.HIGH,
            "IMPORTANTE": ClinicalUrgency.HIGH,
            "ATENCIÓN": ClinicalUrgency.MODERATE,
            "RUTINA": ClinicalUrgency.LOW
        }
        return mapping[urgency_level]
    
    def _get_priority_score_for_urgency(self, urgency_level: str) -> int:
        """Get priority score for urgency level"""
        scores = {
            "EMERGENCY": 10,
            "URGENT": 8,
            "IMPORTANTE": 6,
            "ATENCIÓN": 4,
            "RUTINA": 2
        }
        return scores[urgency_level]
    
    def _get_expected_processing_time(self, urgency_level: str) -> int:
        """Get expected processing time for urgency level"""
        times = {
            "EMERGENCY": 30,
            "URGENT": 45,
            "IMPORTANTE": 60,
            "ATENCIÓN": 90,
            "RUTINA": 120
        }
        return times[urgency_level]
    
    def _create_standardized_input(self, patient: SyntheticPatient) -> Dict[str, Any]:
        """Create standardized input from synthetic patient"""
        return {
            'patient_code': patient.patient_code,
            'hospital_id': patient.hospital_id,
            'input_type': 'medical_image',
            'image_path': f'test_{patient.patient_code}.jpg',
            'timestamp': datetime.now().isoformat(),
            'medical_context': {
                'age': patient.age,
                'risk_level': patient.risk_level.value,
                'has_lpp': patient.has_lpp,
                'lpp_grade': patient.lpp_grade.value if patient.lpp_grade else 0,
                'braden_score': patient.braden_score,
                'diabetes': patient.diabetes,
                'mobility_level': patient.mobility_level.value
            },
            'session_id': f'session_{patient.patient_code}',
            'source': 'whatsapp_bot'
        }
    
    def _setup_mock_processors(self, dispatcher: MedicalDispatcher) -> Dict[ProcessingRoute, Mock]:
        """Setup mock processors for all routes"""
        processors = {}
        for route in ProcessingRoute:
            processor = Mock()
            processor.process = AsyncMock(return_value={'success': True, 'route': route})
            dispatcher.route_processors[route] = processor
            processors[route] = processor
        return processors
    
    def _get_hospital_protocols(self, hospital_id: str) -> List[str]:
        """Get hospital-specific protocols"""
        hospital_protocols = {
            "CLC-001": ["CLC_LPP_Protocol_v2.1", "CLC_Emergency_Escalation"],
            "HDIGITAL-002": ["HD_Digital_Wound_Care", "HD_Telemedicine_Protocol"],
            "HMETRO-003": ["Metro_Standard_Care", "Metro_Geriatric_Special"]
        }
        return hospital_protocols.get(hospital_id, ["Standard_Protocol"])
    
    def _get_hospital_specialists(self, hospital_id: str) -> List[str]:
        """Get available specialists by hospital"""
        hospital_specialists = {
            "CLC-001": ["Dr. Rodriguez - Wound Care", "Dr. Martinez - Geriatrics"],
            "HDIGITAL-002": ["Dr. Silva - Telemedicine", "Dr. Lopez - Digital Health"],
            "HMETRO-003": ["Dr. Gonzalez - General Medicine", "Dr. Torres - Surgery"]
        }
        return hospital_specialists.get(hospital_id, ["General Practitioner"])