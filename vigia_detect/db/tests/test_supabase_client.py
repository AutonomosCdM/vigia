"""
Tests para el cliente de Supabase.

Verifica la funcionalidad para guardar y recuperar datos
relacionados con las detecciones de LPP en Supabase.
"""

import os
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from db.supabase_client import SupabaseClient

# Tests
def test_initialization_with_env_vars():
    """Verifica la inicialización con variables de entorno."""
    # Mock para variables de entorno
    with patch.dict(os.environ, {
        "SUPABASE_URL": "https://test-url.supabase.co",
        "SUPABASE_KEY": "test-key"
    }):
        # Mock para create_client
        with patch('db.supabase_client.create_client') as mock_create_client:
            # Inicializar cliente
            client = SupabaseClient()
            
            # Verificar que se llamó a create_client con parámetros correctos
            mock_create_client.assert_called_once_with(
                "https://test-url.supabase.co", 
                "test-key"
            )

def test_initialization_without_env_vars():
    """Verifica que se lance una excepción sin variables de entorno."""
    # Mock para variables de entorno vacías
    with patch.dict(os.environ, {}, clear=True):
        # Verificar que se lance ValueError
        with pytest.raises(ValueError):
            client = SupabaseClient()

def test_get_or_create_patient_existing():
    """Verifica obtener un paciente existente."""
    # Mock para create_client
    with patch('db.supabase_client.create_client') as mock_create_client:
        # Mock para respuesta de Supabase
        mock_execute = MagicMock()
        mock_execute.data = [{"id": "123e4567-e89b-12d3-a456-426614174000"}]
        
        # Mock para consulta
        mock_eq = MagicMock()
        mock_eq.execute = MagicMock(return_value=mock_execute)
        
        # Mock para select
        mock_select = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        
        # Mock para table
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_select)
        
        # Mock para client
        mock_client = MagicMock()
        mock_client.table = MagicMock(return_value=mock_table)
        
        # Configurar mock para create_client
        mock_create_client.return_value = mock_client
        
        # Mock para variables de entorno
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test-url.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            # Inicializar cliente
            client = SupabaseClient()
            
            # Obtener paciente existente
            patient_id = client._get_or_create_patient("PAT001")
            
            # Verificar ID
            assert patient_id == "123e4567-e89b-12d3-a456-426614174000"
            
            # Verificar que se llamó a select
            mock_table.select.assert_called_once_with("id")
            
            # Verificar que se llamó a eq
            mock_select.eq.assert_called_once_with("patient_code", "PAT001")

def test_get_or_create_patient_new():
    """Verifica crear un nuevo paciente."""
    # Mock para create_client
    with patch('db.supabase_client.create_client') as mock_create_client:
        # Mock para respuesta de select (vacía)
        mock_execute_select = MagicMock()
        mock_execute_select.data = []
        
        # Mock para respuesta de insert
        mock_execute_insert = MagicMock()
        mock_execute_insert.data = [{"id": "123e4567-e89b-12d3-a456-426614174000"}]
        
        # Mock para consulta select
        mock_eq = MagicMock()
        mock_eq.execute = MagicMock(return_value=mock_execute_select)
        
        # Mock para select
        mock_select = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        
        # Mock para insert
        mock_insert = MagicMock()
        mock_insert.execute = MagicMock(return_value=mock_execute_insert)
        
        # Mock para table
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_select)
        mock_table.insert = MagicMock(return_value=mock_insert)
        
        # Mock para client
        mock_client = MagicMock()
        mock_client.table = MagicMock(return_value=mock_table)
        
        # Configurar mock para create_client
        mock_create_client.return_value = mock_client
        
        # Mock para variables de entorno
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test-url.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            # Inicializar cliente
            client = SupabaseClient()
            
            # Crear nuevo paciente
            patient_id = client._get_or_create_patient("PAT002")
            
            # Verificar ID
            assert patient_id == "123e4567-e89b-12d3-a456-426614174000"
            
            # Verificar que se llamó a insert
            mock_table.insert.assert_called_once()
            
            # Verificar los datos de insert
            args, kwargs = mock_table.insert.call_args
            inserted_data = args[0]
            assert inserted_data["patient_code"] == "PAT002"

def test_get_or_create_patient_no_code():
    """Verifica la generación de código aleatorio si no se proporciona."""
    # Mock para create_client
    with patch('db.supabase_client.create_client') as mock_create_client:
        # Mock para respuesta de insert
        mock_execute_insert = MagicMock()
        mock_execute_insert.data = [{"id": "123e4567-e89b-12d3-a456-426614174000"}]
        
        # Mock para consulta select
        mock_eq = MagicMock()
        mock_eq.execute = MagicMock(return_value=MagicMock(data=[]))
        
        # Mock para select
        mock_select = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        
        # Mock para insert
        mock_insert = MagicMock()
        mock_insert.execute = MagicMock(return_value=mock_execute_insert)
        
        # Mock para table
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_select)
        mock_table.insert = MagicMock(return_value=mock_insert)
        
        # Mock para client
        mock_client = MagicMock()
        mock_client.table = MagicMock(return_value=mock_table)
        
        # Configurar mock para create_client
        mock_create_client.return_value = mock_client
        
        # Mock para variables de entorno
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test-url.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            # Inicializar cliente
            client = SupabaseClient()
            
            # Crear paciente sin código
            patient_id = client._get_or_create_patient(None)
            
            # Verificar ID
            assert patient_id == "123e4567-e89b-12d3-a456-426614174000"
            
            # Verificar que se llamó a insert
            mock_table.insert.assert_called_once()
            
            # Verificar que se generó un código aleatorio
            args, kwargs = mock_table.insert.call_args
            inserted_data = args[0]
            assert inserted_data["patient_code"].startswith("TEMP-")

def test_save_detection():
    """Verifica guardar una detección completa."""
    # Mock para create_client y métodos auxiliares
    with patch('db.supabase_client.create_client') as mock_create_client, \
         patch.object(SupabaseClient, '_get_or_create_patient') as mock_get_patient, \
         patch.object(SupabaseClient, '_save_image') as mock_save_image, \
         patch.object(SupabaseClient, '_get_or_create_model') as mock_get_model:
        
        # Configurar mocks para métodos auxiliares
        mock_get_patient.return_value = "patient-id-123"
        mock_save_image.return_value = "image-id-456"
        mock_get_model.return_value = "model-id-789"
        
        # Mock para respuesta de insert
        mock_execute_insert = MagicMock()
        mock_execute_insert.data = [{"id": "detection-id-101112"}]
        
        # Mock para insert
        mock_insert = MagicMock()
        mock_insert.execute = MagicMock(return_value=mock_execute_insert)
        
        # Mock para table
        mock_table = MagicMock()
        mock_table.insert = MagicMock(return_value=mock_insert)
        
        # Mock para client
        mock_client = MagicMock()
        mock_client.table = MagicMock(return_value=mock_table)
        
        # Configurar mock para create_client
        mock_create_client.return_value = mock_client
        
        # Mock para variables de entorno
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test-url.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            # Inicializar cliente
            client = SupabaseClient()
            
            # Datos de prueba
            image_path = "/path/to/test_image.jpg"
            detection_results = {
                "detections": [
                    {
                        "bbox": [10, 20, 100, 150],
                        "confidence": 0.8,
                        "stage": 2,
                        "class_name": "LPP-Stage2"
                    }
                ],
                "processing_time_ms": 120
            }
            
            # Guardar detección
            result = client.save_detection(
                image_path,
                detection_results,
                patient_code="PAT001",
                output_path="/path/to/output.jpg"
            )
            
            # Verificar resultado
            assert result["success"] == True
            assert result["patient_id"] == "patient-id-123"
            assert result["image_id"] == "image-id-456"
            assert result["detections_saved"] == 1
            
            # Verificar que se llamaron a los métodos auxiliares
            mock_get_patient.assert_called_once_with("PAT001")
            mock_save_image.assert_called_once_with(image_path, "patient-id-123")
            mock_get_model.assert_called_once()
            
            # Verificar llamadas a insert para detección
            assert mock_client.table.call_args_list[0][0][0] == "ml_operations.lpp_detections"
            
            # Verificar llamadas a insert para log
            assert mock_client.table.call_args_list[1][0][0] == "audit_logs.system_logs"

def test_get_patient_detections():
    """Verifica obtener detecciones de un paciente."""
    # Mock para create_client
    with patch('db.supabase_client.create_client') as mock_create_client:
        # Mock para respuesta de consulta
        mock_execute = MagicMock()
        mock_execute.data = [
            {
                "patient_code": "PAT001",
                "file_path": "/path/to/image1.jpg",
                "body_location": "sacrum",
                "detection_results": json.dumps({
                    "bbox": [10, 20, 100, 150],
                    "confidence": 0.8,
                    "stage": 2
                }),
                "lpp_stage": 2,
                "confidence_score": 0.8,
                "created_at": "2025-05-21T12:00:00Z",
                "model_name": "yolov5s"
            }
        ]
        
        # Mock para select
        mock_select = MagicMock()
        mock_select.execute = MagicMock(return_value=mock_execute)
        
        # Mock para table
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_select)
        
        # Mock para client
        mock_client = MagicMock()
        mock_client.table = MagicMock(return_value=mock_table)
        
        # Configurar mock para create_client
        mock_create_client.return_value = mock_client
        
        # Mock para variables de entorno
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test-url.supabase.co",
            "SUPABASE_KEY": "test-key"
        }):
            # Inicializar cliente
            client = SupabaseClient()
            
            # Obtener detecciones
            detections = client.get_patient_detections("PAT001")
            
            # Verificar detecciones
            assert len(detections) == 1
            assert detections[0]["patient_code"] == "PAT001"
            assert detections[0]["lpp_stage"] == 2
            assert detections[0]["model_name"] == "yolov5s"

if __name__ == "__main__":
    test_initialization_with_env_vars()
    test_initialization_without_env_vars()
    test_get_or_create_patient_existing()
    test_get_or_create_patient_new()
    test_get_or_create_patient_no_code()
    test_save_detection()
    test_get_patient_detections()
    print("Todos los tests del cliente Supabase pasaron correctamente.")
