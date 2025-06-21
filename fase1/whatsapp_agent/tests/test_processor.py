"""
Tests para la integración con WhatsApp de LPP-Detect.

Este módulo contiene tests para el procesador de imágenes y el servidor webhook.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Agregar directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# Importar componentes a testear
from vigia_detect.messaging.whatsapp.processor import (
    download_image,
    process_whatsapp_image,
    format_detection_results
)

class TestWhatsAppProcessor:
    """Tests para el procesador de imágenes WhatsApp"""
    
    @patch('requests.get')
    def test_download_image(self, mock_get):
        """Verifica la descarga de imágenes desde URLs"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.content = b'test image content'
        mock_get.return_value = mock_response
        
        # Llamar función
        result = download_image('https://example.com/test.jpg')
        
        # Verificar que se guardó la imagen
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0
        
        # Limpiar archivo de prueba
        os.remove(result)
    
    @patch('vigia_detect.messaging.whatsapp.processor.download_image')
    @patch('vigia_detect.messaging.whatsapp.processor.lpp_detect_available', False)
    def test_process_image_simulation(self, mock_download):
        """Verifica el procesamiento simulado cuando LPP-Detect no está disponible"""
        # Llamar función
        result = process_whatsapp_image('https://example.com/test.jpg')
        
        # Verificar resultado
        assert result['success'] is True
        assert result['simulated'] is True
        assert len(result['detections']) > 0
        assert 'message' in result
    
    def test_format_detection_results_no_detections(self):
        """Verifica el formato de mensaje cuando no hay detecciones"""
        # Preparar datos
        detection_results = {'detections': []}
        
        # Llamar función
        result = format_detection_results(detection_results)
        
        # Verificar resultado
        assert 'No se detectaron' in result
    
    def test_format_detection_results_with_detections(self):
        """Verifica el formato de mensaje cuando hay detecciones"""
        # Preparar datos
        detection_results = {
            'detections': [
                {
                    'bbox': [10, 20, 100, 150],
                    'confidence': 0.85,
                    'stage': 1,
                    'class_name': 'LPP-Stage2'
                }
            ]
        }
        
        # Llamar función
        result = format_detection_results(detection_results)
        
        # Verificar resultado
        assert 'ANÁLISIS PRELIMINAR' in result
        assert 'Categoría 2' in result
        assert '85.0%' in result
        assert 'ATENCIÓN' in result
