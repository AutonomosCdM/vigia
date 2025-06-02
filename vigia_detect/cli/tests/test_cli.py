"""
Tests para el CLI de LPP-Detect.

Verifica que el CLI de procesamiento de imágenes funcione correctamente.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Importar módulo a probar
from cli.process_images import process_directory, parse_args

# Tests
def test_parse_args():
    """Verifica el parsing de argumentos de línea de comandos."""
    # Mock para sys.argv
    test_args = [
        "process_images.py",
        "--input", "/test/input",
        "--output", "/test/output",
        "--patient-code", "PAT001",
        "--confidence", "0.3",
        "--save-db",
        "--model", "yolov5m"
    ]
    
    with patch('sys.argv', test_args):
        args = parse_args()
        
        # Verificar argumentos
        assert args.input == "/test/input"
        assert args.output == "/test/output"
        assert args.patient_code == "PAT001"
        assert args.confidence == 0.3
        assert args.save_db == True
        assert args.model == "yolov5m"

def test_process_directory_empty():
    """Verifica el procesamiento de un directorio vacío."""
    # Mocks
    mock_detector = MagicMock()
    mock_preprocessor = MagicMock()
    mock_list_image_files = MagicMock(return_value=[])
    
    # Patch para list_image_files
    with patch('cli.process_images.list_image_files', mock_list_image_files):
        # Procesar directorio vacío
        result = process_directory(
            input_dir="/test/input",
            output_dir="/test/output",
            detector=mock_detector,
            preprocessor=mock_preprocessor
        )
        
        # Verificar resultado
        assert result["processed"] == 0
        assert result["detected"] == 0
        
        # Verificar que no se llamó a preprocess ni detect
        mock_preprocessor.preprocess.assert_not_called()
        mock_detector.detect.assert_not_called()

def test_process_directory_with_images():
    """Verifica el procesamiento de un directorio con imágenes."""
    # Crear imagen de prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear imagen temporal
        img_path = Path(temp_dir) / "test1.jpg"
        with open(img_path, 'wb') as f:
            f.write(b'dummy image data')
        
        # Mocks
        mock_detector = MagicMock()
        mock_preprocessor = MagicMock()
        mock_db_client = MagicMock()
        mock_save_detection_result = MagicMock()
        
        # Configurar mock para preprocesador
        mock_preprocessor.preprocess.return_value = "processed_image_data"
        
        # Configurar mock para detector
        mock_detector.detect.return_value = {
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
        
        # Patch para funciones externas
        with patch('cli.process_images.list_image_files', return_value=[img_path]), \
             patch('cli.process_images.save_detection_result', mock_save_detection_result):
            
            # Procesar directorio
            result = process_directory(
                input_dir=temp_dir,
                output_dir=temp_dir,  # Mismo directorio para simplicidad
                detector=mock_detector,
                preprocessor=mock_preprocessor,
                patient_code="PAT001",
                save_to_db=True,
                db_client=mock_db_client
            )
            
            # Verificar resultado
            assert result["processed"] == 1
            assert result["detected"] == 1
            assert len(result["detections"]) == 1
            assert result["detections"][0]["filename"] == "test1.jpg"
            
            # Verificar que se llamó a preprocess
            mock_preprocessor.preprocess.assert_called_once_with(img_path)
            
            # Verificar que se llamó a detect
            mock_detector.detect.assert_called_once_with("processed_image_data")
            
            # Verificar que se llamó a save_detection_result
            mock_save_detection_result.assert_called_once()
            
            # Verificar que se llamó a save_detection de db_client
            mock_db_client.save_detection.assert_called_once()
            args, kwargs = mock_db_client.save_detection.call_args
            assert args[0] == img_path  # image_path
            assert isinstance(args[1], dict)  # detection_results
            assert args[2] == "PAT001"  # patient_code

def test_process_directory_no_detections():
    """Verifica el procesamiento sin detecciones encontradas."""
    # Crear imagen de prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear imagen temporal
        img_path = Path(temp_dir) / "test1.jpg"
        with open(img_path, 'wb') as f:
            f.write(b'dummy image data')
        
        # Mocks
        mock_detector = MagicMock()
        mock_preprocessor = MagicMock()
        
        # Configurar mock para preprocesador
        mock_preprocessor.preprocess.return_value = "processed_image_data"
        
        # Configurar mock para detector (sin detecciones)
        mock_detector.detect.return_value = {
            "detections": [],
            "processing_time_ms": 120
        }
        
        # Patch para funciones externas
        with patch('cli.process_images.list_image_files', return_value=[img_path]):
            
            # Procesar directorio
            result = process_directory(
                input_dir=temp_dir,
                output_dir=temp_dir,
                detector=mock_detector,
                preprocessor=mock_preprocessor
            )
            
            # Verificar resultado
            assert result["processed"] == 1
            assert result["detected"] == 0
            assert len(result["detections"]) == 0
            
            # Verificar que se llamó a preprocess
            mock_preprocessor.preprocess.assert_called_once_with(img_path)
            
            # Verificar que se llamó a detect
            mock_detector.detect.assert_called_once_with("processed_image_data")

def test_process_directory_error_handling():
    """Verifica el manejo de errores durante el procesamiento."""
    # Crear imagen de prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear imagen temporal
        img_path = Path(temp_dir) / "test1.jpg"
        with open(img_path, 'wb') as f:
            f.write(b'dummy image data')
        
        # Mocks
        mock_detector = MagicMock()
        mock_preprocessor = MagicMock()
        
        # Configurar mock para preprocesador (lanza excepción)
        mock_preprocessor.preprocess.side_effect = Exception("Test error")
        
        # Patch para funciones externas
        with patch('cli.process_images.list_image_files', return_value=[img_path]):
            
            # Procesar directorio
            result = process_directory(
                input_dir=temp_dir,
                output_dir=temp_dir,
                detector=mock_detector,
                preprocessor=mock_preprocessor
            )
            
            # Verificar resultado
            assert result["processed"] == 0
            assert result["detected"] == 0
            
            # Verificar que se llamó a preprocess
            mock_preprocessor.preprocess.assert_called_once_with(img_path)
            
            # Verificar que no se llamó a detect (debido a la excepción)
            mock_detector.detect.assert_not_called()

if __name__ == "__main__":
    test_parse_args()
    test_process_directory_empty()
    test_process_directory_with_images()
    test_process_directory_no_detections()
    test_process_directory_error_handling()
    print("Todos los tests del CLI pasaron correctamente.")
