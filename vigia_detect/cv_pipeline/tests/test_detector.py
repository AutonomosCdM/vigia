"""
Tests para el detector de lesiones por presión.

Verifica que el detector YOLOv5 funcione correctamente para
detectar y clasificar lesiones por presión en imágenes.
"""

import os
import pytest
import numpy as np
import torch
from pathlib import Path
from unittest.mock import patch, MagicMock

from cv_pipeline.detector import LPPDetector

# Tests
def test_detector_initialization():
    """Verifica la inicialización del detector con diferentes parámetros."""
    # Mock para torch.hub.load
    with patch('torch.hub.load') as mock_load:
        # Configurar mock para devolver un objeto con los métodos necesarios
        mock_model = MagicMock()
        mock_model.eval = MagicMock(return_value=None)
        mock_model.to = MagicMock(return_value=mock_model)
        mock_load.return_value = mock_model
        
        # Inicialización con valores por defecto
        detector = LPPDetector()
        assert detector.model_type == 'yolov5s'
        assert detector.conf_threshold == 0.25
        assert detector.model is mock_model
        
        # Verificar que se llamó a torch.hub.load
        mock_load.assert_called_once()
        
        # Inicialización con valores personalizados
        mock_load.reset_mock()
        custom_detector = LPPDetector(
            model_type='yolov5m',
            conf_threshold=0.5
        )
        assert custom_detector.model_type == 'yolov5m'
        assert custom_detector.conf_threshold == 0.5
        
        # Verificar que se volvió a llamar a torch.hub.load
        mock_load.assert_called_once()

def test_detect_with_no_detections():
    """Verifica el comportamiento cuando no hay detecciones."""
    # Crear imagen de prueba
    test_img = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # Mock para torch.hub.load y results
    with patch('torch.hub.load') as mock_load:
        # Crear mock para resultados sin detecciones
        mock_results = MagicMock()
        mock_results.pred = [torch.zeros((0, 6))]  # Sin detecciones
        mock_results.t = [0, 100]  # Tiempo de procesamiento
        
        # Configurar mock para modelo
        mock_model = MagicMock()
        mock_model.eval = MagicMock(return_value=None)
        mock_model.to = MagicMock(return_value=mock_model)
        mock_model.return_value = mock_results
        mock_load.return_value = mock_model
        
        # Inicializar detector
        detector = LPPDetector()
        
        # Detectar
        results = detector.detect(test_img)
        
        # Verificar resultados
        assert 'detections' in results
        assert len(results['detections']) == 0
        assert 'processing_time_ms' in results
        assert results['processing_time_ms'] == 100

def test_detect_with_detections():
    """Verifica el procesamiento correcto de detecciones."""
    # Crear imagen de prueba
    test_img = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # Mock para torch.hub.load y results
    with patch('torch.hub.load') as mock_load:
        # Crear detecciones sintéticas: [x1, y1, x2, y2, conf, cls]
        mock_detections = torch.tensor([
            [10.0, 20.0, 100.0, 150.0, 0.85, 0.0],  # Etapa 1
            [200.0, 50.0, 250.0, 120.0, 0.70, 2.0]  # Etapa 3
        ])
        
        # Crear mock para resultados con detecciones
        mock_results = MagicMock()
        mock_results.pred = [mock_detections]
        mock_results.t = [0, 120]  # Tiempo de procesamiento
        
        # Configurar mock para modelo
        mock_model = MagicMock()
        mock_model.eval = MagicMock(return_value=None)
        mock_model.to = MagicMock(return_value=mock_model)
        mock_model.return_value = mock_results
        mock_load.return_value = mock_model
        
        # Inicializar detector
        detector = LPPDetector()
        
        # Detectar
        results = detector.detect(test_img)
        
        # Verificar resultados
        assert 'detections' in results
        assert len(results['detections']) == 2
        assert 'processing_time_ms' in results
        assert results['processing_time_ms'] == 120
        
        # Verificar primera detección - usando aproximación para punto flotante
        assert results['detections'][0]['bbox'] == [10.0, 20.0, 100.0, 150.0]
        assert abs(results['detections'][0]['confidence'] - 0.85) < 1e-5
        assert results['detections'][0]['stage'] == 0
        assert results['detections'][0]['class_name'] == 'LPP-Stage1'
        
        # Verificar segunda detección
        assert results['detections'][1]['bbox'] == [200.0, 50.0, 250.0, 120.0]
        assert abs(results['detections'][1]['confidence'] - 0.70) < 1e-5
        assert results['detections'][1]['stage'] == 2
        assert results['detections'][1]['class_name'] == 'LPP-Stage3'

def test_get_model_info():
    """Verifica la obtención de información del modelo."""
    # Mock para torch.hub.load
    with patch('torch.hub.load') as mock_load:
        # Configurar mock para devolver un objeto con los métodos necesarios
        mock_model = MagicMock()
        mock_model.eval = MagicMock(return_value=None)
        mock_model.to = MagicMock(return_value=mock_model)
        mock_load.return_value = mock_model
        
        # Inicializar detector
        detector = LPPDetector(model_type='yolov5l', conf_threshold=0.3)
        
        # Obtener información
        info = detector.get_model_info()
        
        # Verificar información
        assert info['type'] == 'yolov5l'
        assert info['conf_threshold'] == 0.3
        assert 'device' in info
        assert 'classes' in info
        assert len(info['classes']) == 5  # 5 clases (4 etapas + no-LPP)

if __name__ == "__main__":
    test_detector_initialization()
    test_detect_with_no_detections()
    test_detect_with_detections()
    test_get_model_info()
    print("Todos los tests de detector pasaron correctamente.")
