"""
Cargador aislado de YOLOv5 para evitar conflictos de nombres con el módulo utils.

Este módulo proporciona una función para cargar YOLOv5 de manera aislada,
evitando el conflicto de nombres entre nuestro módulo utils y el de YOLOv5.
"""

import sys
import os
import logging
import subprocess
import importlib
from typing import Optional

logger = logging.getLogger(__name__)


def load_yolo_model_isolated(model_type='yolov5s', model_path=None):
    """
    Carga un modelo YOLOv5 de manera aislada para evitar conflictos de nombres.
    
    Args:
        model_type: Tipo de modelo YOLOv5 ('yolov5s', 'yolov5m', 'yolov5l')
        model_path: Ruta al modelo personalizado (opcional)
        
    Returns:
        Modelo YOLOv5 cargado o None si hay error
    """
    # Verificar si está en modo de desarrollo/test (usar procesamiento real por defecto)
    if os.getenv('VIGIA_USE_MOCK_YOLO', 'false').lower() == 'true':
        logger.info("VIGIA_USE_MOCK_YOLO está activado, usando modelo simulado")
        return None
    
    try:
        # Estrategia 1: Intentar cargar con entorno aislado
        logger.info("Intentando cargar YOLOv5 con entorno aislado...")
        
        # Limpiar caché de módulos relacionados con YOLOv5
        modules_to_remove = []
        for module_name in sys.modules.keys():
            if any(keyword in module_name.lower() for keyword in ['yolo', 'ultralytics', 'models']):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # Guardar estado actual del path
        original_path = sys.path.copy()
        original_modules = sys.modules.copy()
        
        try:
            # Crear un path limpio sin nuestros módulos
            clean_path = []
            for path in sys.path:
                # Excluir paths que contienen 'vigia' o son el directorio actual
                if 'vigia' not in path.lower() and path != os.getcwd() and path != '':
                    clean_path.append(path)
            
            # Asignar path limpio temporalmente
            sys.path = clean_path
            
            # Limpiar referencia a nuestro módulo utils
            if 'utils' in sys.modules:
                del sys.modules['utils']
            
            # Importar torch hub en el contexto limpio
            import torch
            
            if model_path and os.path.exists(model_path):
                logger.info(f"Cargando modelo personalizado desde {model_path}")
                model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            else:
                logger.info(f"Cargando modelo preentrenado {model_type}")
                model = torch.hub.load('ultralytics/yolov5', model_type)
            
            logger.info("✅ YOLOv5 cargado exitosamente con entorno aislado")
            return model
            
        except Exception as isolated_error:
            logger.warning(f"Falló carga aislada: {isolated_error}")
            raise isolated_error
            
        finally:
            # Restaurar estado original
            sys.path = original_path
            # Solo restaurar módulos que no sean de YOLOv5
            for module_name, module in original_modules.items():
                if module_name not in sys.modules and 'yolo' not in module_name.lower():
                    sys.modules[module_name] = module
                    
    except Exception as e:
        logger.error(f"Error cargando YOLOv5: {e}")
        return None


def create_mock_yolo_model():
    """
    Crea un modelo simulado que imita la interfaz de YOLOv5.
    
    Returns:
        Objeto que simula un modelo YOLOv5
    """
    import numpy as np
    
    # Intentar importar torch, pero si falla, usar un mock
    try:
        import torch
        torch_available = True
    except ImportError:
        torch_available = False
        logger.warning("PyTorch no disponible, usando simulación completa")
    
    class MockYOLOModel:
        def __init__(self):
            self.conf = 0.25
            if torch_available:
                self.device = torch.device('cpu')
            else:
                self.device = 'cpu'
            
        def to(self, device):
            self.device = device
            return self
            
        def eval(self):
            return self
            
        def __call__(self, image):
            # Simular detección de LPP
            class MockResults:
                def __init__(self):
                    # Simular 1-2 detecciones aleatorias
                    num_detections = np.random.randint(0, 3)
                    detections = []
                    
                    for i in range(num_detections):
                        # Generar bbox aleatorio
                        x1 = np.random.randint(0, 400)
                        y1 = np.random.randint(0, 400)
                        x2 = x1 + np.random.randint(50, 200)
                        y2 = y1 + np.random.randint(50, 200)
                        
                        # Confianza aleatoria
                        conf = np.random.uniform(0.3, 0.9)
                        
                        # Clase aleatoria (0-3 para LPP stages)
                        cls = np.random.randint(0, 4)
                        
                        detections.append([x1, y1, x2, y2, conf, cls])
                    
                    if torch_available:
                        self.pred = [torch.tensor(detections) if detections else torch.empty((0, 6))]
                    else:
                        # Mock tensor-like object
                        class MockTensor:
                            def __init__(self, data):
                                self.data = np.array(data) if data else np.empty((0, 6))
                            def cpu(self):
                                return self
                            def numpy(self):
                                return self.data
                        self.pred = [MockTensor(detections)]
                    self.t = [0, np.random.uniform(30, 100), 0]  # Tiempo simulado
                    
            return MockResults()
    
    logger.info("Creado modelo YOLOv5 simulado")
    return MockYOLOModel()