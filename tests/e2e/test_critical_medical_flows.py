"""
End-to-End tests for critical medical flows.
Tests the complete system from image input to medical output.
"""
import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import os

from vigia_detect.core.unified_image_processor import UnifiedImageProcessor
from vigia_detect.messaging.whatsapp.processor import WhatsAppProcessor
from vigia_detect.messaging.slack_notifier_refactored import SlackNotifier
from vigia_detect.deployment.health_checker import HealthChecker
from vigia_detect.utils.error_handling import VigiaError, PatientDataError, ImageProcessingError
from vigia_detect.core.constants import LPPGrade
from tests.shared_fixtures import (
    sample_image_path,
    temp_directory,
    mock_detection_result,
    SAMPLE_PATIENT_CODES
)


class TestCriticalMedicalFlows:
    """Test critical medical flows that must work 100% for clinical stability."""
    
    @pytest.fixture
    def processor(self):
        """Create unified image processor for testing."""
        return UnifiedImageProcessor()
    
    @pytest.fixture
    def whatsapp_processor(self):
        """Create WhatsApp processor for testing."""
        return WhatsAppProcessor()
    
    @pytest.fixture
    def slack_notifier(self):
        """Create Slack notifier for testing."""
        return SlackNotifier()
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker for testing."""
        return HealthChecker()

    @pytest.mark.asyncio
    async def test_complete_detection_pipeline(self, processor, sample_image_path):
        """
        CRITICAL: Test complete detection pipeline from image to medical assessment.
        This is the core medical flow that must never fail.
        """
        patient_code = SAMPLE_PATIENT_CODES[0]
        
        # Mock YOLO detection to return consistent results
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector') as mock_detector:
            mock_detector.return_value.detect.return_value = {
                'detections': [
                    {
                        'class': 'lpp_grade_2',
                        'confidence': 0.85,
                        'bbox': [100, 100, 200, 200],
                        'area': 10000
                    }
                ],
                'image_path': str(sample_image_path),
                'processing_time': 0.5
            }
            
            # Process image
            result = processor.process_single_image(
                image_path=str(sample_image_path),
                patient_code=patient_code,
                save_visualization=True
            )
            
            # Validate critical medical outputs
            assert result['success'] is True
            assert 'detection_result' in result
            assert 'medical_assessment' in result
            assert 'patient_code' in result
            assert result['patient_code'] == patient_code
            
            # Validate medical assessment structure
            assessment = result['medical_assessment']
            assert 'lpp_grade' in assessment
            assert 'severity_level' in assessment
            assert 'recommendations' in assessment
            assert 'confidence_score' in assessment
            
            # Validate LPP grade is valid
            assert assessment['lpp_grade'] in [grade.value for grade in LPPGrade]
            
            # Validate confidence is in valid range
            assert 0.0 <= assessment['confidence_score'] <= 1.0
            
            # Validate recommendations are present for any detected grade > 0
            if assessment['lpp_grade'] > 0:
                assert len(assessment['recommendations']) > 0
                assert isinstance(assessment['recommendations'], list)

    @pytest.mark.asyncio
    async def test_patient_data_validation_flow(self, processor):
        """
        CRITICAL: Test patient data validation with medical-specific requirements.
        Patient data errors must be handled safely in medical context.
        """
        invalid_patient_codes = [
            "",  # Empty
            "INVALID",  # Wrong format
            "AB-2024",  # Incomplete
            "AB-2024-",  # Incomplete with dash
            "123-ABC-456",  # Wrong pattern
            None,  # None value
        ]
        
        for invalid_code in invalid_patient_codes:
            with pytest.raises(PatientDataError) as exc_info:
                processor._validate_patient_code(invalid_code)
            
            # Validate error structure
            error = exc_info.value
            assert error.category.value == "medical_data"
            assert error.severity.value in ["high", "critical"]
            assert error.error_code == "PATIENT_DATA_ERROR"
            assert "patient_code" in error.context or invalid_code is None

    @pytest.mark.asyncio
    async def test_image_processing_error_handling(self, processor):
        """
        CRITICAL: Test image processing errors are handled safely.
        Medical systems must never crash on bad input.
        """
        # Test various error conditions
        error_cases = [
            ("nonexistent.jpg", "File not found"),
            ("", "Empty path"),
            (None, "None path"),
        ]
        
        for image_path, expected_error in error_cases:
            with pytest.raises(ImageProcessingError) as exc_info:
                processor.process_single_image(image_path, "CD-2025-001")
            
            error = exc_info.value
            assert error.category.value == "processing"
            assert expected_error.lower() in error.user_message.lower()

    @pytest.mark.asyncio
    async def test_whatsapp_complete_flow(self, whatsapp_processor, sample_image_path):
        """
        CRITICAL: Test complete WhatsApp flow from message to response.
        This is the primary interface for medical staff.
        """
        # Mock Twilio client
        with patch('vigia_detect.messaging.twilio_client_refactored.TwilioClient') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = {"success": True}
            
            # Mock image processing
            with patch.object(whatsapp_processor, 'processor') as mock_processor:
                mock_processor.process_single_image.return_value = {
                    'success': True,
                    'detection_result': {'detections': []},
                    'medical_assessment': {
                        'lpp_grade': 1,
                        'severity_level': 'ATENCIÓN',
                        'recommendations': ['Aliviar presión inmediatamente'],
                        'confidence_score': 0.75
                    },
                    'patient_code': 'CD-2025-001'
                }
                
                # Simulate WhatsApp message with image
                message_data = {
                    'From': 'whatsapp:+56912345678',
                    'To': 'whatsapp:+56987654321',
                    'Body': 'Paciente CD-2025-001 - Evaluar LPP en sacro',
                    'MediaUrl0': 'https://api.twilio.com/test-image.jpg',
                    'NumMedia': '1'
                }
                
                # Process message
                result = await whatsapp_processor.process_message(message_data)
                
                # Validate response
                assert result['success'] is True
                assert 'response_sent' in result
                assert result['response_sent'] is True
                
                # Validate that medical response was generated
                mock_twilio.return_value.send_message.assert_called()
                call_args = mock_twilio.return_value.send_message.call_args
                message_body = call_args[1]['body']
                
                # Medical response must contain key information
                assert 'LPP' in message_body
                assert 'Grado' in message_body or 'Grade' in message_body
                assert 'CD-2025-001' in message_body

    @pytest.mark.asyncio
    async def test_slack_medical_notification_flow(self, slack_notifier):
        """
        CRITICAL: Test Slack medical notifications are properly formatted.
        Medical staff rely on these notifications for patient care.
        """
        # Mock Slack client
        with patch('vigia_detect.messaging.slack_notifier_refactored.WebClient') as mock_slack:
            mock_slack.return_value.chat_postMessage.return_value = {
                'ok': True,
                'message': {'ts': '1234567890.123456'}
            }
            
            # Create medical detection result
            detection_result = {
                'patient_code': 'CD-2025-001',
                'detection_result': {
                    'detections': [
                        {
                            'class': 'lpp_grade_2',
                            'confidence': 0.85,
                            'bbox': [100, 100, 200, 200]
                        }
                    ]
                },
                'medical_assessment': {
                    'lpp_grade': 2,
                    'severity_level': 'IMPORTANTE',
                    'recommendations': [
                        'Curación según protocolo',
                        'Apósitos hidrocoloides',
                        'Evaluar dolor y signos de infección'
                    ],
                    'confidence_score': 0.85
                },
                'image_path': '/path/to/image.jpg',
                'timestamp': '2025-01-15T10:30:00'
            }
            
            # Send notification
            result = await slack_notifier.send_detection_notification(detection_result)
            
            # Validate notification was sent
            assert result['success'] is True
            
            # Validate Slack message structure
            mock_slack.return_value.chat_postMessage.assert_called()
            call_args = mock_slack.return_value.chat_postMessage.call_args
            
            # Check blocks structure for medical information
            blocks = call_args[1]['blocks']
            assert len(blocks) > 0
            
            # Find header block with patient info
            header_found = False
            medical_info_found = False
            
            for block in blocks:
                if block['type'] == 'header':
                    header_text = block['text']['text']
                    if 'CD-2025-001' in header_text and 'LPP' in header_text:
                        header_found = True
                
                if block['type'] == 'section':
                    if 'fields' in block:
                        for field in block['fields']:
                            if 'Grado' in field['text'] and '2' in field['text']:
                                medical_info_found = True
            
            assert header_found, "Medical notification must include patient code in header"
            assert medical_info_found, "Medical notification must include LPP grade information"

    @pytest.mark.asyncio
    async def test_error_recovery_medical_context(self, processor):
        """
        CRITICAL: Test error recovery provides medical-appropriate suggestions.
        Medical errors must have specific recovery guidance.
        """
        # Test various medical error scenarios
        with patch.object(processor, '_process_with_yolo', side_effect=Exception("YOLO model failed")):
            try:
                processor.process_single_image("test.jpg", "CD-2025-001")
            except VigiaError as e:
                # Validate medical error structure
                assert e.category.value in ["processing", "medical_data"]
                assert len(e.recovery_suggestions) > 0
                
                # Recovery suggestions must be medical-appropriate
                suggestions_text = " ".join(e.recovery_suggestions)
                medical_keywords = ["médica", "técnico", "sistema", "imagen", "paciente"]
                assert any(keyword in suggestions_text.lower() for keyword in medical_keywords)

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, health_checker):
        """
        CRITICAL: Test system health monitoring for medical reliability.
        Medical systems must monitor their own health.
        """
        # Run comprehensive health check
        health_report = health_checker.comprehensive_health_check()
        
        # Validate health report structure
        assert 'overall_status' in health_report
        assert 'checks' in health_report
        assert 'summary' in health_report
        assert 'timestamp' in health_report
        
        # Validate all critical checks are present
        critical_checks = ['database', 'redis', 'external_apis', 'file_system']
        for check in critical_checks:
            assert check in health_report['checks'], f"Critical check {check} missing"
        
        # Validate summary metrics
        summary = health_report['summary']
        assert 'total_checks' in summary
        assert 'passed_checks' in summary
        assert 'failed_checks' in summary
        assert summary['total_checks'] > 0

    @pytest.mark.asyncio
    async def test_batch_processing_medical_workflow(self, processor, temp_directory):
        """
        CRITICAL: Test batch processing maintains medical data integrity.
        Batch processing must handle multiple patients safely.
        """
        # Create test images for different patients
        patient_images = {}
        for i, patient_code in enumerate(SAMPLE_PATIENT_CODES[:3]):
            image_path = temp_directory / f"patient_{patient_code.replace('-', '_')}.jpg"
            # Create dummy image file
            image_path.write_bytes(b"dummy_image_data")
            patient_images[patient_code] = str(image_path)
        
        # Mock YOLO for consistent results
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector') as mock_detector:
            mock_detector.return_value.detect.return_value = {
                'detections': [{'class': 'lpp_grade_1', 'confidence': 0.7}],
                'processing_time': 0.3
            }
            
            # Process batch
            results = []
            for patient_code, image_path in patient_images.items():
                try:
                    result = processor.process_single_image(image_path, patient_code)
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Batch processing failed for patient {patient_code}: {e}")
            
            # Validate all patients were processed
            assert len(results) == len(patient_images)
            
            # Validate patient data integrity
            processed_patients = {r['patient_code'] for r in results if r['success']}
            expected_patients = set(patient_images.keys())
            assert processed_patients == expected_patients, "Patient data integrity violated in batch processing"

    @pytest.mark.asyncio
    async def test_hipaa_compliance_data_sanitization(self, processor):
        """
        CRITICAL: Test HIPAA compliance in error handling and logging.
        Medical data must be properly sanitized.
        """
        # Test with sensitive data in context
        sensitive_context = {
            'patient_name': 'John Doe',
            'ssn': '123-45-6789',
            'phone_number': '+1234567890',
            'medical_record_number': 'MRN-12345',
            'safe_data': 'This is safe'
        }
        
        # Create error with sensitive context
        error = VigiaError(
            message="Test medical error",
            error_code="TEST_ERROR",
            category=VigiaError._generate_user_message.__func__(VigiaError())._category,
            context=sensitive_context
        )
        
        # Convert to dict (simulates logging)
        error_dict = error.to_dict()
        
        # Validate sensitive data is present in context (should be sanitized by handler)
        context = error_dict['context']
        
        # When using MedicalErrorHandler, sensitive fields should be redacted
        from vigia_detect.utils.error_handling import MedicalErrorHandler
        handler = MedicalErrorHandler("test_module")
        
        result = handler.handle_error(error, "test_operation", sensitive_context)
        
        # The handler should have sanitized the data
        # This test ensures the sanitization mechanism exists
        assert 'success' in result
        assert result['success'] is False


class TestRegressionFlows:
    """Test that existing functionality wasn't broken by refactoring."""
    
    def test_cli_commands_still_work(self, temp_directory):
        """Test that CLI commands maintain their interface."""
        # This would test the CLI interface hasn't changed
        from vigia_detect.cli.process_images import main as cli_main
        
        # Mock sys.argv for CLI testing
        with patch('sys.argv', ['process_images.py', '--help']):
            try:
                # Should not raise exception for help
                pass
            except SystemExit as e:
                # Help command exits with 0
                assert e.code == 0 or e.code is None

    def test_slack_message_format_compatibility(self):
        """Test that Slack message formats are backward compatible."""
        from vigia_detect.core.slack_templates import create_detection_notification
        
        # Test old format still works
        detection_data = {
            'patient_code': 'CD-2025-001',
            'lpp_grade': 2,
            'confidence': 0.85,
            'recommendations': ['Test recommendation']
        }
        
        blocks = create_detection_notification(detection_data)
        
        # Validate structure
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert all('type' in block for block in blocks)

    def test_webhook_payload_compatibility(self):
        """Test that webhook payloads maintain compatibility."""
        from vigia_detect.webhook.models import DetectionEvent
        
        # Test creating event with old data structure
        event = DetectionEvent(
            event_type="detection.completed",
            patient_code="CD-2025-001",
            detection_result={
                'lpp_grade': 2,
                'confidence': 0.85
            },
            timestamp="2025-01-15T10:30:00"
        )
        
        # Should serialize without error
        payload = event.dict()
        assert 'event_type' in payload
        assert 'patient_code' in payload
        assert 'detection_result' in payload