#!/usr/bin/env python3
"""
Script para debuggear el detector localmente
"""
import sys
import os
sys.path.append('.')

# Simular el entorno de Render sin PyTorch
import importlib.util
torch_spec = importlib.util.find_spec("torch")
if torch_spec:
    print("✅ PyTorch disponible")
else:
    print("❌ PyTorch NO disponible")

# Test del detector
try:
    from vigia_detect.cv_pipeline.detector import LPPDetector
    print("✅ Detector importado correctamente")
    
    # Inicializar detector
    detector = LPPDetector()
    print("✅ Detector inicializado correctamente")
    
    # Test imagen dummy
    import numpy as np
    dummy_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    result = detector.detect(dummy_image)
    print(f"✅ Detección exitosa: {len(result['detections'])} detecciones")
    print(f"   Tiempo: {result['processing_time_ms']:.1f}ms")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()