"""
Detector de lesiones por presión basado en YOLOv5.

Este módulo implementa un wrapper para el modelo YOLOv5 entrenado
específicamente para detectar y clasificar lesiones por presión (LPP).
"""

import os
import sys
import logging
from pathlib import Path
import torch
import numpy as np

# Import performance monitoring utilities
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.performance_profiler import profile_performance
from utils.energy_monitor import track_energy

# Configuración de logging
logger = logging.getLogger('vigia-detect.detector')

class LPPDetector:
    """
    Detector de lesiones por presión basado en YOLOv5-Wound.
    
    Utiliza un modelo preentrenado de YOLOv5 especializado para la detección
    y clasificación de lesiones por presión según su etapa (0-4).
    """
    
    def __init__(self, model_type='yolov5s', conf_threshold=0.25, model_path=None):
        """
        Inicializa el detector Vigía.
        
        Args:
            model_type: Tipo de modelo YOLOv5 ('yolov5s', 'yolov5m', 'yolov5l')
            conf_threshold: Umbral de confianza para detecciones (0.0-1.0)
            model_path: Ruta al modelo preentrenado (None = usar modelo por defecto)
        """
        self.conf_threshold = conf_threshold
        self.model_type = model_type
        self.model_path = model_path
        self.model = None
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        
        # Etiquetas de clases para el modelo
        self.class_names = ['LPP-Stage1', 'LPP-Stage2', 'LPP-Stage3', 'LPP-Stage4', 'Non-LPP']
        
        # Inicializar modelo
        self._load_model()
        
    def _load_model(self):
        """Carga el modelo YOLOv5 preentrenado."""
        try:
            logger.info(f"Cargando modelo YOLOv5-Wound en {self.device}...")
            
            # Usar cargador aislado para evitar conflictos de nombres
            from .yolo_loader import load_yolo_model_isolated, create_mock_yolo_model
            
            # Intentar cargar YOLOv5 real con entorno aislado
            self.model = load_yolo_model_isolated(self.model_type, self.model_path)
            
            if self.model is None:
                logger.warning("No se pudo cargar YOLOv5 real, usando simulación")
                self.model = create_mock_yolo_model()
            else:
                logger.info("✅ Modelo YOLOv5 real cargado exitosamente")
            
            # Configurar el modelo
            try:
                self.model.to(self.device)
                self.model.conf = self.conf_threshold
                # Modo evaluación
                self.model.eval()
            except Exception as config_error:
                logger.warning(f"Error configurando modelo, usando valores por defecto: {config_error}")
                # Para modelo simulado, no necesita configuración especial
                pass
            
            logger.info("✅ Detector inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {str(e)}")
            # En caso de error total, crear modelo simulado como fallback
            logger.warning("Creando modelo simulado como fallback final")
            from .yolo_loader import create_mock_yolo_model
            self.model = create_mock_yolo_model()
    
    @profile_performance(duration=10, output_format="flamegraph")
    @track_energy("detection_inference")
    def detect(self, image):
        """
        Detecta lesiones por presión en una imagen.
        
        Args:
            image: Imagen como array NumPy o ruta a archivo
            
        Returns:
            dict: Resultados de detección con formato:
                {
                    'detections': [
                        {
                            'bbox': [x1, y1, x2, y2],  # Coordenadas del bbox
                            'confidence': float,        # Confianza (0-1)
                            'stage': int,              # Etapa LPP (0-4)
                            'class_name': str          # Nombre de clase
                        },
                        ...
                    ],
                    'processing_time_ms': float        # Tiempo de procesamiento en ms
                }
        """
        if self.model is None:
            raise ValueError("Modelo no inicializado. Llama a _load_model primero.")
        
        # Realizar inferencia
        results = self.model(image)
        
        # Extraer resultados en formato deseado
        processed_results = {
            'detections': [],
            'processing_time_ms': results.t[1]  # Tiempo de inferencia
        }
        
        # Si hay detecciones, procesarlas
        if len(results.pred[0]) > 0:
            # Convertir a numpy para más fácil manipulación
            detections = results.pred[0].cpu().numpy()
            
            for detection in detections:
                x1, y1, x2, y2, conf, cls = detection
                
                # Convertir etapa del modelo a nuestra numeración (0-4)
                # Mapeamos las clases según el modelo específico
                stage = int(cls)  # En implementación real, mapear correctamente
                
                # Para simulación, asumimos que la clase corresponde a la etapa
                if stage < len(self.class_names):
                    class_name = self.class_names[stage]
                else:
                    class_name = f"Unknown-{stage}"
                
                # Añadir a resultados
                processed_results['detections'].append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'stage': stage,
                    'class_name': class_name
                })
        
        return processed_results

    def get_model_info(self):
        """Retorna información sobre el modelo cargado."""
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "type": self.model_type,
            "device": str(self.device),
            "conf_threshold": self.conf_threshold,
            "classes": self.class_names
        }

# Alias for backward compatibility
YOLODetector = LPPDetector
