"""
Test Async Medical Pipeline
===========================

Tests para el pipeline médico asíncrono con tareas Celery, verificando
timeouts, retry policies y manejo de fallos específicos médicos.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from vigia_detect.core.async_pipeline import AsyncMedicalPipeline
from vigia_detect.utils.failure_handler import TaskFailureHandler

class TestAsyncMedicalPipeline:
    """Tests del pipeline médico asíncrono"""
    
    @pytest.fixture
    def pipeline(self):
        """Crea instancia del pipeline async"""
        return AsyncMedicalPipeline()
    
    @pytest.fixture
    def mock_celery_app(self):
        """Mock de Celery app para testing"""
        with patch('vigia_detect.core.async_pipeline.celery_app') as mock_app:
            # Mock de AsyncResult
            mock_result = MagicMock()
            mock_result.id = 'test_task_id_123'
            mock_result.status = 'PENDING'
            mock_result.ready.return_value = False
            mock_result.successful.return_value = False
            mock_result.failed.return_value = False
            
            mock_app.AsyncResult.return_value = mock_result
            yield mock_app
    
    @pytest.fixture
    def sample_patient_context(self):
        """Contexto de paciente para testing"""
        return {
            'patient_code': 'TEST-2025-001',
            'age': 75,
            'risk_factors': ['diabetes', 'movilidad_reducida'],
            'admission_date': '2025-01-09',
            'department': 'internal_medicine'
        }
    
    def test_process_medical_case_async_success(
        self, 
        pipeline, 
        mock_celery_app, 
        sample_patient_context
    ):
        """Test procesamiento asíncrono exitoso"""
        
        # Mock de tareas
        with patch('vigia_detect.core.async_pipeline.image_analysis_task') as mock_image_task, \
             patch('vigia_detect.core.async_pipeline.medical_analysis_task') as mock_medical_task, \
             patch('vigia_detect.core.async_pipeline.audit_log_task') as mock_audit_task:
            
            # Configurar mocks
            mock_image_task.delay.return_value.id = 'image_task_123'
            mock_medical_task.delay.return_value.id = 'medical_task_456'
            mock_audit_task.delay.return_value.id = 'audit_task_789'
            
            # Ejecutar pipeline
            result = pipeline.process_medical_case_async(
                image_path='/test/image.jpg',
                patient_code='TEST-2025-001',
                patient_context=sample_patient_context,
                processing_options={'analysis_type': 'complete'}
            )
            
            # Verificar resultado
            assert result['success'] is True
            assert result['patient_code'] == 'TEST-2025-001'
            assert result['status'] == 'processing'
            assert 'pipeline_id' in result
            assert 'task_ids' in result
            
            # Verificar que las tareas fueron llamadas
            mock_image_task.delay.assert_called_once()
            mock_medical_task.delay.assert_called_once()
            mock_audit_task.delay.assert_called_once()
            
            # Verificar task IDs
            assert result['task_ids']['image_analysis'] == 'image_task_123'
            assert result['task_ids']['medical_analysis'] == 'medical_task_456'
            assert result['task_ids']['audit_log'] == 'audit_task_789'
    
    def test_process_medical_case_async_failure(
        self, 
        pipeline, 
        sample_patient_context
    ):
        """Test manejo de fallo en procesamiento asíncrono"""
        
        # Mock que falla
        with patch('vigia_detect.core.async_pipeline.image_analysis_task') as mock_image_task:
            mock_image_task.delay.side_effect = Exception("Redis connection failed")
            
            # Ejecutar pipeline
            result = pipeline.process_medical_case_async(
                image_path='/test/image.jpg',
                patient_code='TEST-2025-001',
                patient_context=sample_patient_context
            )
            
            # Verificar manejo del fallo
            assert result['success'] is False
            assert 'error' in result
            assert result['patient_code'] == 'TEST-2025-001'
            assert result['failure_logged'] is True
    
    def test_get_pipeline_status(self, pipeline, mock_celery_app):
        """Test obtención de estado del pipeline"""
        
        # Configurar mock de AsyncResult
        mock_result = mock_celery_app.AsyncResult.return_value
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {'success': True, 'lpp_grade': 2}
        
        # IDs de tareas de test
        task_ids = {
            'image_analysis': 'task_123',
            'medical_analysis': 'task_456',
            'audit_log': 'task_789'
        }
        
        # Obtener estado
        status = pipeline.get_pipeline_status('test_pipeline_001', task_ids)
        
        # Verificar estado
        assert status['pipeline_id'] == 'test_pipeline_001'
        assert status['overall_status'] == 'completed'
        assert status['completed_tasks'] == 3
        assert status['total_tasks'] == 3
        assert status['has_failures'] is False
        
        # Verificar estado de tareas individuales
        for task_name in task_ids.keys():
            task_status = status['tasks_status'][task_name]
            assert task_status['status'] == 'SUCCESS'
            assert task_status['ready'] is True
            assert task_status['successful'] is True
    
    def test_get_pipeline_status_with_failures(self, pipeline, mock_celery_app):
        """Test estado del pipeline con fallos"""
        
        # Configurar mock con fallo
        mock_result = mock_celery_app.AsyncResult.return_value
        mock_result.status = 'FAILURE'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.info = Exception("Processing failed")
        
        task_ids = {'image_analysis': 'task_123'}
        
        # Obtener estado
        status = pipeline.get_pipeline_status('test_pipeline_002', task_ids)
        
        # Verificar estado de fallo
        assert status['overall_status'] == 'failed'
        assert status['has_failures'] is True
        assert status['completed_tasks'] == 0
    
    def test_trigger_escalation_pipeline(self, pipeline, sample_patient_context):
        """Test disparador de pipeline de escalación"""
        
        with patch('vigia_detect.core.async_pipeline.medical_alert_slack_task') as mock_alert, \
             patch('vigia_detect.core.async_pipeline.escalation_notification_task') as mock_escalation, \
             patch('vigia_detect.core.async_pipeline.medical_decision_audit_task') as mock_audit:
            
            # Configurar mocks
            mock_alert.delay.return_value.id = 'alert_task_123'
            mock_escalation.delay.return_value.id = 'escalation_task_456'
            mock_audit.delay.return_value.id = 'audit_task_789'
            
            # Datos de escalación
            escalation_data = {
                'lpp_grade': 4,
                'confidence': 0.9,
                'requires_emergency': True
            }
            
            # Disparar escalación
            result = pipeline.trigger_escalation_pipeline(
                escalation_data=escalation_data,
                escalation_type='emergency',
                patient_context=sample_patient_context
            )
            
            # Verificar resultado
            assert result['success'] is True
            assert result['escalation_type'] == 'emergency'
            assert 'escalation_id' in result
            assert 'task_ids' in result
            
            # Verificar que las tareas fueron llamadas
            mock_alert.delay.assert_called_once()
            mock_escalation.delay.assert_called_once()
            mock_audit.delay.assert_called_once()
            
            # Verificar escalación a canales de emergencia
            assert '#emergencias' in result['target_channels']
            assert 'emergency' in result['target_roles']
    
    def test_escalation_channels_mapping(self, pipeline):
        """Test mapeo correcto de canales de escalación"""
        
        # Test diferentes tipos de escalación
        test_cases = [
            ('human_review', ['#equipo-medico']),
            ('emergency', ['#emergencias', '#especialistas', '#equipo-medico']),
            ('specialist_review', ['#especialistas', '#equipo-medico']),
            ('unknown_type', ['#general-medico'])  # Fallback
        ]
        
        for escalation_type, expected_channels in test_cases:
            channels = pipeline._get_escalation_channels(escalation_type)
            assert channels == expected_channels
    
    def test_escalation_roles_mapping(self, pipeline):
        """Test mapeo correcto de roles de escalación"""
        
        test_cases = [
            ('human_review', ['medical_team']),
            ('emergency', ['emergency', 'specialists', 'medical_team']),
            ('specialist_review', ['specialists', 'medical_team']),
            ('unknown_type', ['medical_team'])  # Fallback
        ]
        
        for escalation_type, expected_roles in test_cases:
            roles = pipeline._get_escalation_roles(escalation_type)
            assert roles == expected_roles
    
    @pytest.mark.slow
    def test_wait_for_pipeline_completion_timeout(self, pipeline):
        """Test timeout en espera de completación"""
        
        with patch('vigia_detect.core.async_pipeline.group') as mock_group:
            # Configurar mock que simula timeout
            mock_group_instance = MagicMock()
            mock_group_instance.get.side_effect = Exception("TimeoutError")
            mock_group.return_value = mock_group_instance
            
            task_ids = {'test_task': 'task_123'}
            
            # Ejecutar con timeout
            result = pipeline.wait_for_pipeline_completion(
                pipeline_id='test_pipeline',
                task_ids=task_ids,
                timeout=1  # Timeout muy corto para test
            )
            
            # Verificar manejo de timeout
            assert result['success'] is False
            assert 'error' in result
            assert result['pipeline_id'] == 'test_pipeline'

class TestTaskFailureIntegration:
    """Tests de integración con manejo de fallos"""
    
    @pytest.fixture
    def failure_handler(self):
        """Crea instancia del manejador de fallos"""
        return TaskFailureHandler()
    
    def test_medical_task_failure_logging(self, failure_handler):
        """Test logging específico de fallos médicos"""
        
        # Simular fallo de tarea médica crítica
        exception = ValueError("MedGemma analysis failed")
        
        result = failure_handler.handle_task_failure(
            task_name='medical_analysis_task',
            task_id='task_critical_123',
            exception=exception,
            traceback_str='Traceback...',
            context={'image_path': '/test/image.jpg'},
            patient_context={'patient_code': 'CRITICAL-2025-001'}
        )
        
        # Verificar manejo crítico
        assert result['failure_logged'] is True
        assert result['severity'] == 'critical'
        assert result['escalation_response']['requires_escalation'] is True
        assert result['notification_sent'] is True
    
    def test_retry_exhausted_escalation(self, failure_handler):
        """Test escalación cuando se agotan reintentos"""
        
        final_exception = Exception("Final retry failed")
        
        result = failure_handler.handle_retry_exhausted(
            task_name='risk_score_task',
            task_id='task_exhausted_456',
            retry_count=3,
            final_exception=final_exception,
            patient_context={'patient_code': 'RETRY-2025-001'}
        )
        
        # Verificar escalación crítica
        assert result['escalated'] is True
        assert result['escalation_type'] == 'human_review_required'
        assert result['requires_immediate_attention'] is True

@pytest.mark.integration
class TestAsyncPipelineIntegration:
    """Tests de integración completa del pipeline asíncrono"""
    
    def test_complete_medical_workflow_mock(self):
        """Test workflow médico completo con mocks"""
        
        # Este test simula el flujo completo sin dependencias externas
        pipeline = AsyncMedicalPipeline()
        
        with patch('vigia_detect.core.async_pipeline.image_analysis_task') as mock_image, \
             patch('vigia_detect.core.async_pipeline.medical_analysis_task') as mock_medical, \
             patch('vigia_detect.core.async_pipeline.audit_log_task') as mock_audit:
            
            # Configurar mocks para éxito
            mock_image.delay.return_value.id = 'workflow_image_123'
            mock_medical.delay.return_value.id = 'workflow_medical_456'
            mock_audit.delay.return_value.id = 'workflow_audit_789'
            
            # Ejecutar workflow completo
            result = pipeline.process_medical_case_async(
                image_path='/test/lpp_image.jpg',
                patient_code='WORKFLOW-2025-001',
                patient_context={
                    'patient_code': 'WORKFLOW-2025-001',
                    'age': 80,
                    'diabetes': True,
                    'mobility': 'limited'
                },
                processing_options={
                    'analysis_type': 'complete',
                    'notify_channels': ['#equipo-medico']
                }
            )
            
            # Verificar workflow iniciado correctamente
            assert result['success'] is True
            assert 'pipeline_id' in result
            assert len(result['task_ids']) == 3
            
            # Verificar que todas las tareas médicas fueron disparadas
            mock_image.delay.assert_called_once()
            mock_medical.delay.assert_called_once()
            mock_audit.delay.assert_called_once()

if __name__ == '__main__':
    # Ejecutar tests básicos
    print("🧪 Testing Async Medical Pipeline...")
    
    # Test básico de instanciación
    pipeline = AsyncMedicalPipeline()
    assert pipeline is not None
    print("✅ Pipeline instance created successfully")
    
    # Test de configuración de escalación
    channels = pipeline._get_escalation_channels('emergency')
    assert '#emergencias' in channels
    print("✅ Escalation channels configured correctly")
    
    print("🎉 Basic async pipeline tests passed!")