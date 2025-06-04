"""
Módulo de pipeline de visión computacional para LPP-Detect.

Este módulo implementa la canalización completa para procesamiento de imágenes,
detección y clasificación de lesiones por presión (LPP).
"""

from .detector import LPPDetector as Detector
from .preprocessor import ImagePreprocessor as Preprocessor
from .yolo_loader import YOLOLoader

__all__ = ['Detector', 'Preprocessor', 'YOLOLoader']
