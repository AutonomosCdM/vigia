"""
Módulo de pipeline de visión computacional para LPP-Detect.

Este módulo implementa la canalización completa para procesamiento de imágenes,
detección y clasificación de lesiones por presión (LPP).
"""

from .detector import LPPDetector
from .preprocessor import ImagePreprocessor

__all__ = ['LPPDetector', 'ImagePreprocessor']
