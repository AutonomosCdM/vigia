"""
Tests para el procesador de WhatsApp de LPP-Detect

Este módulo contiene tests para verificar que el procesador de 
imágenes de WhatsApp funciona correctamente.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Importar componentes a testear
from vigia_detect.messaging.whatsapp.processor import (
    download_image, 
    process_whatsapp_image, 
    format_detection_results
)

class TestWhatsAppProcessor:
    """Tests para el procesador de WhatsApp"""
    
    @patch('requests.get')
    def test_download_image(self, mock_get):
        """Verifica la descarga de imágenes"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.content = b'fake_image_data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Llamar a la función
        result = download_image('https://example.com/image.jpg')
        
        # Verificar llamada a requests.get
        mock_get.assert_called_once_with('https://example.com/image.jpg', auth=None, timeout=30)
        
        # Verificar que se guardó el archivo
        assert os.path.exists(result)
        
        # Limpiar
        if os.path.exists(result):
            os.remove(result)
    
    @patch('vigia_detect.messaging.whatsapp.processor.download_image')
    @patch('vigia_detect.messaging.whatsapp.processor.LPPDetector')
    @patch('vigia_detect.messaging.whatsapp.processor.ImagePreprocessor')
    @patch('vigia_detect.messaging.whatsapp.processor.save_detection_result')
    def test_process_whatsapp_image(self, mock_save, mock_preprocessor_class, mock_detector_class, mock_download):
        """Verifica el procesamiento de imágenes WhatsApp"""
        # Configurar mocks
        mock_download.return_value = Path('/tmp/test_image.jpg')
        
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = 'processed_image'
        mock_preprocessor_class.return_value = mock_preprocessor
        
        mock_detector = MagicMock()
        mock_detector.detect.return_value = {
            'detections': [
                {
                    'bbox': [10, 20, 100, 150],
                    'confidence': 0.85,
                    'stage': 1,
                    'class_name': 'LPP-Stage1'
                }
            ]
        }
        mock_detector_class.return_value = mock_detector
        
        # Llamar a la función
        result = process_whatsapp_image('https://example.com/image.jpg')
        
        # Verificar que se llamaron las funciones esperadas
        mock_download.assert_called_once_with('https://example.com/image.jpg', None)
        mock_preprocessor.preprocess.assert_called_once_with(Path('/tmp/test_image.jpg'))
        mock_detector.detect.assert_called_once_with('processed_image')
        mock_save.assert_called_once()
        
        # Verificar resultado
        assert result['success'] is True
        assert len(result['detections']) == 1
        assert result['detections'][0]['confidence'] == 0.85
        assert result['detections'][0]['stage'] == 1
        assert 'message' in result
    
    def test_format_detection_results_with_detections(self):
        """Verifica el formateo de resultados con detecciones"""
        # Resultados simulados
        detection_results = {
            'detections': [
                {
                    'bbox': [10, 20, 100, 150],
                    'confidence': 0.85,
                    'stage': 1,
                    'class_name': 'LPP-Stage1'
                }
            ]
        }
        
        # Formatear resultados
        message = format_detection_results(detection_results)
        
        # Verificar mensaje
        assert '🔍 *ANÁLISIS PRELIMINAR:*' in message
        assert '*Lesión 1:*' in message
        assert 'Categoría 2' in message
        assert '85.0%' in message
        assert 'profesionales médicos' in message
    
    def test_format_detection_results_without_detections(self):
        """Verifica el formateo de resultados sin detecciones"""
        # Resultados simulados sin detecciones
        detection_results = {
            'detections': []
        }
        
        # Formatear resultados
        message = format_detection_results(detection_results)
        
        # Verificar mensaje
        assert 'No se detectaron lesiones por presión' in message
