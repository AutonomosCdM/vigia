#!/usr/bin/env python3
"""
LPP-Detect CLI para procesamiento de imágenes de lesiones por presión.

Este CLI permite cargar imágenes desde un directorio, procesarlas con el pipeline
de visión computacional, y almacenar los resultados en Supabase.
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent))

from cv_pipeline.detector import LPPDetector
from cv_pipeline.preprocessor import ImagePreprocessor
from db.supabase_client import SupabaseClient
from utils.image_utils import list_image_files, save_detection_result
from webhook.client import WebhookClient
from webhook.models import WebhookEvent, EventType, Severity
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lpp-detect-cli')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Procesar imágenes para detección de LPP')
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=os.path.join(Path(__file__).resolve().parent.parent, 'data', 'input'),
        help='Directorio de imágenes de entrada'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=os.path.join(Path(__file__).resolve().parent.parent, 'data', 'output'),
        help='Directorio para resultados procesados'
    )
    parser.add_argument(
        '--patient-code',
        type=str,
        help='Código único del paciente (si se conoce)'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.25,
        help='Umbral de confianza para detecciones (0.0-1.0)'
    )
    parser.add_argument(
        '--save-db',
        action='store_true',
        help='Guardar resultados en Supabase'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='yolov5s',
        choices=['yolov5s', 'yolov5m', 'yolov5l'],
        help='Modelo YOLOv5 a utilizar'
    )
    parser.add_argument(
        '--webhook',
        action='store_true',
        help='Enviar notificaciones via webhook'
    )
    parser.add_argument(
        '--webhook-url',
        type=str,
        help='URL del webhook (override de variable de entorno)'
    )
    return parser.parse_args()

def send_webhook_notification(detection_results, patient_code, image_path, webhook_url=None):
    """Envía notificación via webhook."""
    try:
        # Get webhook config from env or args
        webhook_url = webhook_url or os.getenv('WEBHOOK_URL')
        if not webhook_url:
            logger.warning("No webhook URL configured")
            return
        
        api_key = os.getenv('WEBHOOK_API_KEY')
        
        # Create webhook client
        client = WebhookClient(webhook_url, api_key=api_key)
        
        # Determine risk level based on detections
        risk_level = "LOW"
        if detection_results['detections']:
            stages = [d['stage'] for d in detection_results['detections']]
            if 4 in stages:
                risk_level = "CRITICAL"
            elif 3 in stages:
                risk_level = "HIGH"
            elif 2 in stages:
                risk_level = "MEDIUM"
        
        # Create webhook event
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={
                "patient_code": patient_code or "UNKNOWN",
                "risk_level": risk_level,
                "image_path": str(image_path),
                "detections": [
                    {
                        "stage": d['stage'],
                        "confidence": d['confidence'],
                        "bbox": d['bbox'],
                        "area": d.get('area', 0),
                        "severity": "critical" if d['stage'] >= 3 else "high" if d['stage'] == 2 else "medium"
                    }
                    for d in detection_results['detections']
                ],
                "total_detected": len(detection_results['detections']),
                "processing_time": detection_results.get('processing_time', 0)
            },
            source="vigia_cli"
        )
        
        # Send webhook
        response = client.send(event)
        if response.success:
            logger.info(f"Webhook sent successfully: {response.status_code}")
        else:
            logger.error(f"Webhook failed: {response.message}")
            
    except Exception as e:
        logger.error(f"Error sending webhook: {str(e)}")

def process_directory(input_dir, output_dir, detector, preprocessor, patient_code=None, 
                     save_to_db=False, db_client=None, send_webhook=False, webhook_url=None):
    """
    Procesa todas las imágenes en el directorio de entrada.
    
    Args:
        input_dir: Directorio con imágenes de entrada
        output_dir: Directorio para guardar resultados
        detector: Instancia de LPPDetector
        preprocessor: Instancia de ImagePreprocessor
        patient_code: Código de paciente opcional
        save_to_db: Indica si se guardan los resultados en la BD
        db_client: Cliente de Supabase (si save_to_db es True)
    
    Returns:
        dict: Resumen de procesamiento
    """
    image_files = list_image_files(input_dir)
    if not image_files:
        logger.warning(f"No se encontraron imágenes en {input_dir}")
        return {"processed": 0, "detected": 0}
    
    logger.info(f"Procesando {len(image_files)} imágenes...")
    
    # Estadísticas para retornar
    stats = {
        "processed": 0,
        "detected": 0,
        "detections": []
    }
    
    for img_path in image_files:
        try:
            # Preprocesar imagen
            logger.info(f"Preprocesando {img_path.name}...")
            processed_img = preprocessor.preprocess(img_path)
            
            # Detectar LPP
            logger.info(f"Detectando LPP en {img_path.name}...")
            detection_results = detector.detect(processed_img)
            
            if detection_results["detections"]:
                stats["detected"] += 1
                stats["detections"].append({
                    "filename": img_path.name,
                    "results": detection_results
                })
                
                # Guardar imagen con anotaciones
                output_path = Path(output_dir) / f"{img_path.stem}_detected{img_path.suffix}"
                save_detection_result(processed_img, detection_results, output_path)
                logger.info(f"Resultado guardado en {output_path}")
                
                # Guardar en BD si se solicita
                if save_to_db and db_client:
                    logger.info(f"Guardando resultados en Supabase...")
                    db_client.save_detection(
                        img_path, 
                        detection_results, 
                        patient_code,
                        str(output_path)
                    )
                
                # Enviar webhook si se solicita
                if send_webhook:
                    send_webhook_notification(detection_results, patient_code, img_path, webhook_url)
            else:
                logger.info(f"No se detectaron LPP en {img_path.name}")
            
            stats["processed"] += 1
                
        except Exception as e:
            logger.error(f"Error procesando {img_path.name}: {str(e)}")
    
    return stats

def main():
    """Función principal del CLI."""
    args = parse_args()
    
    # Asegurar que los directorios existan
    os.makedirs(args.output, exist_ok=True)
    
    # Inicializar componentes
    logger.info("Inicializando detector y preprocesador...")
    detector = LPPDetector(model_type=args.model, conf_threshold=args.confidence)
    preprocessor = ImagePreprocessor()
    
    # Cliente DB si es necesario
    db_client = None
    if args.save_db:
        logger.info("Inicializando conexión a Supabase...")
        db_client = SupabaseClient()
    
    # Procesar directorio
    logger.info(f"Procesando imágenes desde {args.input}...")
    stats = process_directory(
        args.input,
        args.output,
        detector,
        preprocessor,
        patient_code=args.patient_code,
        save_to_db=args.save_db,
        db_client=db_client,
        send_webhook=args.webhook,
        webhook_url=args.webhook_url
    )
    
    # Mostrar resumen
    logger.info(f"Procesamiento completado: {stats['processed']} imágenes procesadas")
    logger.info(f"Detecciones encontradas: {stats['detected']} imágenes con LPP")
    
    for detection in stats["detections"]:
        logger.info(f"  - {detection['filename']}: " + 
                  f"{len(detection['results']['detections'])} LPP detectadas")
        for i, det in enumerate(detection['results']['detections']):
            logger.info(f"    > LPP {i+1}: Etapa {det['stage']}, " +
                      f"Confianza: {det['confidence']:.2f}")
    
if __name__ == "__main__":
    main()
