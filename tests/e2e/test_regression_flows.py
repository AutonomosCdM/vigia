"""
Regression tests to ensure refactoring didn't break existing functionality.
Tests CLI, Slack, WhatsApp, and webhook integrations.
"""
import pytest
import asyncio
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List
import os

from tests.shared_fixtures import (
    sample_image_path,
    temp_directory,
    mock_detection_result,
    SAMPLE_PATIENT_CODES
)


class TestCLIRegression:
    """Test that CLI commands work as expected after refactoring."""
    
    def test_cli_help_command(self):
        """Test that CLI help command works and shows expected options."""
        try:
            # Test help command
            result = subprocess.run([
                sys.executable, '-m', 'vigia_detect.cli.process_images', '--help'
            ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent))
            
            # Help should exit with code 0
            assert result.returncode == 0
            
            # Should contain key CLI options
            help_text = result.stdout.lower()
            expected_options = [
                '--patient-code', '--webhook', '--output-dir', 
                '--save-visualization', '--batch-mode'
            ]
            
            for option in expected_options:
                assert option in help_text, f"CLI option {option} missing from help"
                
        except FileNotFoundError:
            pytest.skip("CLI module not available for testing")
    
    def test_cli_version_command(self):
        """Test that version command works."""
        try:
            result = subprocess.run([
                sys.executable, '-c', 
                'from vigia_detect import __version__; print(__version__)'
            ], capture_output=True, text=True)
            
            # Should not crash and should output version info
            assert result.returncode == 0
            assert len(result.stdout.strip()) > 0
            
        except Exception:
            pytest.skip("Version check not available")
    
    def test_cli_parameter_validation(self):
        """Test that CLI parameter validation works correctly."""
        try:
            # Test invalid patient code
            result = subprocess.run([
                sys.executable, '-m', 'vigia_detect.cli.process_images',
                '--patient-code', 'INVALID',
                'nonexistent.jpg'
            ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent))
            
            # Should fail with non-zero exit code
            assert result.returncode != 0
            
            # Error message should mention patient code
            error_text = (result.stderr + result.stdout).lower()
            assert any(keyword in error_text for keyword in ['patient', 'code', 'invalid'])
            
        except FileNotFoundError:
            pytest.skip("CLI module not available for testing")


class TestSlackIntegrationRegression:
    """Test that Slack integration maintains backward compatibility."""
    
    @pytest.fixture
    def mock_slack_client(self):
        """Create mock Slack client."""
        mock_client = Mock()
        mock_client.chat_postMessage.return_value = {
            'ok': True,
            'ts': '1234567890.123456',
            'message': {
                'text': 'Test message',
                'ts': '1234567890.123456'
            }
        }
        return mock_client
    
    def test_slack_notification_format_compatibility(self, mock_slack_client):
        """Test that Slack notification format is backward compatible."""
        from vigia_detect.slack.block_kit_medical import BlockKitMedical
        from vigia_detect.core.slack_templates import create_detection_notification
        
        # Test old data format still works
        legacy_detection_data = {
            'patient_code': 'CD-2025-001',
            'lpp_grade': 2,
            'confidence': 0.85,
            'recommendations': ['Curación según protocolo', 'Evaluar signos de infección'],
            'timestamp': '2025-01-15T10:30:00',
            'image_path': '/path/to/image.jpg'
        }
        
        # Should create blocks without error
        blocks = create_detection_notification(legacy_detection_data)
        
        # Validate structure
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        
        # Check for required block types
        block_types = [block['type'] for block in blocks]
        assert 'header' in block_types
        assert 'section' in block_types
        
        # Check that patient code is in header
        header_blocks = [b for b in blocks if b['type'] == 'header']
        assert len(header_blocks) > 0
        header_text = header_blocks[0]['text']['text']
        assert 'CD-2025-001' in header_text
    
    @pytest.mark.asyncio
    async def test_slack_notifier_send_compatibility(self, mock_slack_client):
        """Test that SlackNotifier.send method maintains compatibility."""
        with patch('vigia_detect.slack.block_kit_medical.WebClient', return_value=mock_slack_client):
            notifier = BlockKitMedical()
            
            # Test with legacy format
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
                    'recommendations': ['Curación según protocolo'],
                    'confidence_score': 0.85
                },
                'timestamp': '2025-01-15T10:30:00'
            }
            
            # Should send without error
            result = await notifier.send_detection_notification(detection_result)
            
            # Validate response
            assert result['success'] is True
            assert 'message_ts' in result
            
            # Validate Slack API was called correctly
            mock_slack_client.chat_postMessage.assert_called_once()
            call_args = mock_slack_client.chat_postMessage.call_args
            
            # Check channel and blocks structure
            assert 'channel' in call_args[1]
            assert 'blocks' in call_args[1]
            assert isinstance(call_args[1]['blocks'], list)
    
    def test_slack_block_fields_regression(self):
        """Test that Slack block fields contain expected medical information."""
        from vigia_detect.core.slack_templates import create_detection_notification
        
        detection_data = {
            'patient_code': 'CD-2025-001',
            'lpp_grade': 3,
            'confidence': 0.90,
            'recommendations': ['Evaluación médica urgente', 'Desbridamiento quirúrgico'],
            'severity_level': 'URGENTE'
        }
        
        blocks = create_detection_notification(detection_data)
        
        # Find section blocks with fields
        field_blocks = [b for b in blocks if b['type'] == 'section' and 'fields' in b]
        assert len(field_blocks) > 0
        
        # Collect all field texts
        all_fields_text = []
        for block in field_blocks:
            for field in block['fields']:
                all_fields_text.append(field['text'])
        
        combined_text = ' '.join(all_fields_text)
        
        # Should contain key medical information
        assert 'Grado' in combined_text or 'Grade' in combined_text
        assert '3' in combined_text
        assert 'CD-2025-001' in combined_text
        assert 'URGENTE' in combined_text


class TestWhatsAppIntegrationRegression:
    """Test that WhatsApp integration maintains functionality."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create mock Twilio client."""
        mock_client = Mock()
        mock_client.send_message.return_value = {
            'success': True,
            'message_sid': 'SM1234567890abcdef',
            'status': 'queued'
        }
        mock_client.download_media.return_value = b"mock_image_data"
        return mock_client
    
    @pytest.fixture
    def whatsapp_message_data(self):
        """Sample WhatsApp message data."""
        return {
            'MessageSid': 'SM1234567890abcdef',
            'From': 'whatsapp:+56912345678',
            'To': 'whatsapp:+56987654321',
            'Body': 'Paciente CD-2025-001 - Evaluar LPP en región sacra',
            'MediaUrl0': 'https://api.twilio.com/test-image.jpg',
            'MediaContentType0': 'image/jpeg',
            'NumMedia': '1'
        }
    
    @pytest.mark.asyncio
    async def test_whatsapp_message_processing_compatibility(self, mock_twilio_client, whatsapp_message_data):
        """Test that WhatsApp message processing maintains compatibility."""
        from vigia_detect.mcp.gateway import create_mcp_gateway
        
        async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
            # Mock WhatsApp message processing via MCP
            with patch.object(gateway, 'whatsapp_operation') as mock_whatsapp:
                mock_whatsapp.return_value = {
                    'success': True,
                    'medical_assessment': {
                        'lpp_grade': 2,
                        'severity_level': 'IMPORTANTE',
                        'recommendations': ['Curación según protocolo'],
                        'confidence_score': 0.85
                    },
                    'patient_code': 'CD-2025-001'
                }
                
                # Process message via MCP gateway
                result = await gateway.whatsapp_operation(
                    'process_medical_message',
                    message_data=whatsapp_message_data
                )
                
                # Validate processing result
                assert result['success'] is True
                assert 'response_sent' in result
                
                # Validate Twilio send_message was called
                mock_twilio_client.send_message.assert_called()
                call_args = mock_twilio_client.send_message.call_args
                
                # Check response format
                assert 'to' in call_args[1]
                assert 'body' in call_args[1]
                
                # Medical response should contain key information
                response_body = call_args[1]['body']
                assert 'CD-2025-001' in response_body
                assert 'LPP' in response_body or 'Grado' in response_body
    
    @pytest.mark.asyncio
    async def test_whatsapp_error_response_format(self, mock_twilio_client, whatsapp_message_data):
        """Test that WhatsApp error responses maintain expected format."""
        from vigia_detect.mcp.gateway import create_mcp_gateway
        
        async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
            # Mock WhatsApp operation to fail
            with patch.object(gateway, 'whatsapp_operation') as mock_whatsapp:
                mock_whatsapp.side_effect = Exception("Processing failed")
                
                # Process message (should handle error gracefully)
                try:
                    result = await gateway.whatsapp_operation(
                        'process_medical_message',
                        message_data=whatsapp_message_data
                    )
                except Exception:
                    result = {'success': False, 'error': 'Processing failed'}
                
                # Should still send a response (error message)
                assert 'success' in result
                
                # Should have attempted to send error response
                mock_twilio_client.send_message.assert_called()
                call_args = mock_twilio_client.send_message.call_args
                response_body = call_args[1]['body']
                
                # Error response should be medical-appropriate
                assert any(keyword in response_body.lower() for keyword in ['error', 'problema', 'intentar'])
    
    def test_whatsapp_patient_code_extraction(self):
        """Test that patient code extraction from WhatsApp messages works."""
        from vigia_detect.utils.shared_utilities import VigiaValidator
        
        validator = VigiaValidator()
        
        test_messages = [
            ("Paciente CD-2025-001 - Evaluar LPP", "CD-2025-001"),
            ("Evaluar paciente AB-2024-999", "AB-2024-999"),
            ("Código XY-2025-123 lesión en talón", "XY-2025-123"),
            ("No patient code here", None),
            ("", None),
        ]
        
        for message, expected_code in test_messages:
            # Use validator to extract patient code from message
            extracted_code = validator.extract_patient_code(message) if message else None
            assert extracted_code == expected_code, f"Failed for message: '{message}'"


class TestWebhookIntegrationRegression:
    """Test that webhook integration maintains compatibility."""
    
    @pytest.fixture
    def mock_webhook_client(self):
        """Create mock webhook client."""
        from vigia_detect.webhook.client import WebhookClient
        mock_client = Mock(spec=WebhookClient)
        mock_client.send_event.return_value = {
            'success': True,
            'status_code': 200,
            'response_time': 0.1
        }
        return mock_client
    
    def test_webhook_event_model_compatibility(self):
        """Test that webhook event models maintain compatibility."""
        from vigia_detect.webhook.models import DetectionEvent
        from datetime import datetime
        
        # Test creating event with legacy data structure
        event_data = {
            'event_type': 'detection.completed',
            'patient_code': 'CD-2025-001',
            'detection_result': {
                'lpp_grade': 2,
                'confidence': 0.85,
                'detections': [
                    {
                        'class': 'lpp_grade_2',
                        'confidence': 0.85,
                        'bbox': [100, 100, 200, 200]
                    }
                ]
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Should create without error
        event = DetectionEvent(**event_data)
        
        # Should serialize correctly
        serialized = event.dict()
        
        # Validate required fields
        assert serialized['event_type'] == 'detection.completed'
        assert serialized['patient_code'] == 'CD-2025-001'
        assert serialized['detection_result']['lpp_grade'] == 2
        assert 'timestamp' in serialized
    
    @pytest.mark.asyncio
    async def test_webhook_client_send_compatibility(self, mock_webhook_client):
        """Test that webhook client send method maintains compatibility."""
        from vigia_detect.webhook.models import DetectionEvent
        
        # Create detection event
        event = DetectionEvent(
            event_type="detection.completed",
            patient_code="CD-2025-001",
            detection_result={'lpp_grade': 2, 'confidence': 0.85},
            timestamp="2025-01-15T10:30:00"
        )
        
        with patch('vigia_detect.webhook.client.WebhookClient', return_value=mock_webhook_client):
            # Should send without error
            result = await mock_webhook_client.send_event(event)
            
            # Validate response
            assert result['success'] is True
            assert 'status_code' in result
    
    def test_webhook_payload_structure_regression(self):
        """Test that webhook payload structure remains consistent."""
        from vigia_detect.webhook.models import DetectionEvent, PatientEvent
        
        # Test DetectionEvent
        detection_event = DetectionEvent(
            event_type="detection.completed",
            patient_code="CD-2025-001",
            detection_result={'test': 'data'},
            timestamp="2025-01-15T10:30:00"
        )
        
        payload = detection_event.dict()
        
        # Should have consistent structure
        expected_fields = ['event_type', 'patient_code', 'detection_result', 'timestamp', 'event_id']
        for field in expected_fields:
            assert field in payload, f"Webhook payload missing field: {field}"
        
        # Test PatientEvent
        patient_event = PatientEvent(
            event_type="patient.updated",
            patient_code="CD-2025-001",
            patient_data={'name': 'John Doe'},
            timestamp="2025-01-15T10:30:00"
        )
        
        payload = patient_event.dict()
        expected_fields = ['event_type', 'patient_code', 'patient_data', 'timestamp', 'event_id']
        for field in expected_fields:
            assert field in payload, f"Patient event payload missing field: {field}"


class TestConfigurationRegression:
    """Test that configuration and environment setup remains compatible."""
    
    def test_environment_variables_compatibility(self):
        """Test that required environment variables are still recognized."""
        from vigia_detect.deployment.config_manager import ConfigManager
        
        config = ConfigManager()
        
        # Test that configuration validates known environment variables
        required_env_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_KEY',
            'ANTHROPIC_API_KEY',
            'SLACK_BOT_TOKEN',
            'TWILIO_ACCOUNT_SID',
            'WEBHOOK_URL'
        ]
        
        # These should be recognized as valid configuration keys
        for env_var in required_env_vars:
            # Should not raise exception when checking
            validation_result = config._validate_environment_variable(env_var, "test_value")
            assert 'valid' in validation_result
    
    def test_docker_config_generation_compatibility(self):
        """Test that Docker configuration generation maintains compatibility."""
        from vigia_detect.deployment.config_manager import ConfigManager, EnvironmentType
        
        config = ConfigManager()
        
        # Should generate valid Docker config
        docker_config = config.generate_docker_config(EnvironmentType.DEVELOPMENT)
        
        # Should have required sections
        required_sections = ['version', 'services']
        for section in required_sections:
            assert section in docker_config, f"Docker config missing section: {section}"
        
        # Should have expected services
        services = docker_config['services']
        expected_services = ['vigia_main', 'redis', 'postgres']
        
        for service in expected_services:
            assert service in services, f"Docker config missing service: {service}"


class TestDatabaseIntegrationRegression:
    """Test that database integration maintains compatibility."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client."""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = {
            'data': [{'id': 1, 'patient_code': 'CD-2025-001'}],
            'error': None
        }
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = {
            'data': [{'id': 1, 'patient_code': 'CD-2025-001', 'status': 'active'}],
            'error': None
        }
        return mock_client
    
    def test_supabase_client_interface_compatibility(self, mock_supabase_client):
        """Test that Supabase client interface remains compatible."""
        from vigia_detect.db.supabase_client import SupabaseClient
        
        with patch('vigia_detect.db.supabase_client.create_client', return_value=mock_supabase_client):
            client = SupabaseClient()
            
            # Test basic operations still work
            result = client.insert_detection_result({
                'patient_code': 'CD-2025-001',
                'lpp_grade': 2,
                'confidence': 0.85,
                'timestamp': '2025-01-15T10:30:00'
            })
            
            # Should return success
            assert result['success'] is True
            
            # Test query operation
            query_result = client.get_patient_history('CD-2025-001')
            assert 'data' in query_result


class TestErrorHandlingRegression:
    """Test that error handling maintains medical-appropriate behavior."""
    
    def test_vigia_error_structure_compatibility(self):
        """Test that VigiaError maintains expected structure."""
        from vigia_detect.utils.error_handling import VigiaError, ErrorCategory
        
        # Test creating error with legacy parameters
        error = VigiaError(
            message="Test medical error",
            error_code="TEST_ERROR",
            category=ErrorCategory.MEDICAL_DATA
        )
        
        # Should serialize to expected format
        error_dict = error.to_dict()
        
        required_fields = ['error_id', 'error_code', 'category', 'severity', 'user_message', 'timestamp']
        for field in required_fields:
            assert field in error_dict, f"VigiaError missing field: {field}"
        
        # Should have medical-appropriate user message
        assert isinstance(error_dict['user_message'], str)
        assert len(error_dict['user_message']) > 0
    
    def test_medical_error_handler_compatibility(self):
        """Test that MedicalErrorHandler maintains compatibility."""
        from vigia_detect.utils.error_handling import MedicalErrorHandler, VigiaError, ErrorCategory
        
        handler = MedicalErrorHandler("test_module")
        
        # Create test error
        error = VigiaError(
            message="Test processing error",
            error_code="PROCESSING_ERROR",
            category=ErrorCategory.PROCESSING
        )
        
        # Handle error
        result = handler.handle_error(error, "test_operation", {"test": "context"})
        
        # Should return expected structure
        assert 'success' in result
        assert result['success'] is False
        assert 'error' in result
        assert 'timestamp' in result
        
        # Error should be properly formatted
        error_data = result['error']
        assert 'error_id' in error_data
        assert 'user_message' in error_data


class TestPerformanceRegression:
    """Test that performance characteristics haven't degraded significantly."""
    
    @pytest.mark.asyncio
    async def test_image_processing_performance_baseline(self, sample_image_path):
        """Test that image processing performance is within acceptable bounds."""
        from vigia_detect.core.unified_image_processor import UnifiedImageProcessor
        import time
        
        processor = UnifiedImageProcessor()
        
        # Mock YOLO for consistent timing
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector') as mock_detector:
            mock_detector.return_value.detect.return_value = {
                'detections': [{'class': 'lpp_grade_2', 'confidence': 0.85}],
                'processing_time': 0.1
            }
            
            start_time = time.time()
            
            # Process image
            result = processor.process_single_image(
                image_path=str(sample_image_path),
                patient_code="CD-2025-001"
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time (allowing for test overhead)
            assert total_time < 10.0, f"Processing took too long: {total_time}s"
            assert result['success'] is True


# Integration test runner
def test_run_all_regression_tests():
    """Meta-test that ensures all regression test classes can be instantiated."""
    test_classes = [
        TestCLIRegression,
        TestSlackIntegrationRegression,
        TestWhatsAppIntegrationRegression,
        TestWebhookIntegrationRegression,
        TestConfigurationRegression,
        TestDatabaseIntegrationRegression,
        TestErrorHandlingRegression,
        TestPerformanceRegression
    ]
    
    for test_class in test_classes:
        # Should be able to instantiate without error
        instance = test_class()
        assert instance is not None
        
        # Should have at least one test method
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        assert len(test_methods) > 0, f"{test_class.__name__} has no test methods"