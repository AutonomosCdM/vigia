#!/usr/bin/env python3
"""
CLI refactorizado para procesamiento de imágenes de lesiones por presión.
Usa el ImageProcessor centralizado para eliminar duplicación de código.
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent))

from vigia_detect.core.image_processor import ImageProcessor
from vigia_detect.core.constants import LPP_SEVERITY_ALERTS
from vigia_detect.db.supabase_client_refactored import SupabaseClientRefactored
from vigia_detect.utils.image_utils import list_image_files
from vigia_detect.utils.energy_monitor import track_energy, energy_monitor
from vigia_detect.webhook.client import SyncWebhookClient
from vigia_detect.webhook.models import DetectionPayload, Detection, Severity
from vigia_detect.config.settings import settings

# FASE 1: PHI Tokenization Integration
import asyncio
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / 'fase1'))
from fase1.phi_tokenization.client.phi_tokenization_client import tokenize_patient_phi, TokenizedPatient

# Configurar logging usando el módulo centralizado
from vigia_detect.core.base_client import BaseClient

# Configurar logger
logger = BaseClient("CLI", {}, {})._setup_logger()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Procesar imágenes para detección de LPP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Procesar todas las imágenes en el directorio por defecto
  python process_images.py
  
  # Procesar imágenes de un paciente específico
  python process_images.py --patient-code CD-2025-001
  
  # Procesar y guardar en base de datos
  python process_images.py --save-db --patient-code CD-2025-001
  
  # Usar directorio personalizado
  python process_images.py -i /path/to/images -o /path/to/output
        """
    )
    
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
        '--hospital-mrn',
        type=str,
        help='Hospital MRN (Medical Record Number) para tokenización PHI (formato: MRN-YYYY-NNN-XX)'
    )
    
    parser.add_argument(
        '--patient-code',
        type=str,
        help='[DEPRECATED] Use --hospital-mrn instead. Legacy patient code support.'
    )
    
    parser.add_argument(
        '--save-db',
        action='store_true',
        help='Guardar resultados en la base de datos'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.25,
        help='Umbral de confianza para detecciones (0-1)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='yolov5s',
        choices=['yolov5s', 'yolov5m', 'yolov5l'],
        help='Modelo YOLO a utilizar'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Número de imágenes a procesar en paralelo'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    parser.add_argument(
        '--webhook',
        action='store_true',
        help='Enviar resultados via webhook'
    )
    
    parser.add_argument(
        '--webhook-url',
        type=str,
        help='URL del webhook (sobrescribe configuración)'
    )
    
    return parser.parse_args()


async def tokenize_hospital_mrn(hospital_mrn: str) -> Optional[TokenizedPatient]:
    """
    Tokeniza el Hospital MRN (Bruce Wayne → Batman)
    
    Args:
        hospital_mrn: Hospital MRN (formato: MRN-2025-001-BW)
        
    Returns:
        TokenizedPatient object o None si falla
    """
    try:
        tokenized_patient = await tokenize_patient_phi(
            hospital_mrn=hospital_mrn,
            request_purpose="CLI image processing for LPP detection"
        )
        logger.info(f"PHI tokenization successful: {hospital_mrn[:8]}... → {tokenized_patient.patient_alias}")
        return tokenized_patient
    except Exception as e:
        logger.error(f"PHI tokenization failed: {e}")
        return None

def validate_patient_code(code: str) -> bool:
    """Valida el formato del código de paciente usando el validador centralizado"""
    from utils.validators import validate_patient_code
    return validate_patient_code(code)

def validate_hospital_mrn(mrn: str) -> bool:
    """Valida el formato del Hospital MRN"""
    import re
    pattern = r'^MRN-\d{4}-\d{3}-\w+$'
    return re.match(pattern, mrn) is not None


def print_detection_summary(results: List[dict]):
    """Imprime un resumen de las detecciones"""
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    
    # Contar detecciones por grado
    grade_counts = {}
    total_detections = 0
    
    for result in results:
        if result.get('success') and 'results' in result:
            detections = result['results'].get('detections', [])
            total_detections += len(detections)
            
            for detection in detections:
                grade = detection.get('class', 0)
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    # Imprimir resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print("="*50)
    print(f"📁 Total de imágenes procesadas: {total}")
    print(f"✅ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    print(f"\n🔍 Total de detecciones: {total_detections}")
    
    if grade_counts:
        print("\n📈 Detecciones por grado:")
        for grade in sorted(grade_counts.keys()):
            severity = LPP_SEVERITY_ALERTS.get(grade, {})
            emoji = severity.get('emoji', '❓')
            count = grade_counts[grade]
            print(f"  {emoji} Grado {grade}: {count} detección(es)")
    
    print("="*50)


def process_with_db(results: List[dict], patient_code: str, db_client: SupabaseClientRefactored):
    """Guarda los resultados en la base de datos"""
    logger.info("Guardando resultados en base de datos...")
    
    # Obtener o crear paciente
    patient = db_client.get_or_create_patient(patient_code)
    patient_id = patient['id']
    
    saved_count = 0
    for result in results:
        if not result.get('success'):
            continue
        
        try:
            # Guardar cada detección
            detection_data = result.get('results', {})
            db_result = db_client.save_detection(
                patient_id=patient_id,
                detection_data=detection_data,
                image_path=result.get('image_path')
            )
            
            if db_result:
                saved_count += 1
                logger.info(f"Detección guardada: {db_result.get('id')}")
                
        except Exception as e:
            logger.error(f"Error guardando detección: {e}")
    
    logger.info(f"Se guardaron {saved_count} detecciones en la base de datos")


def send_webhook_notifications(results: List[dict], patient_code: Optional[str], webhook_url: Optional[str]):
    """Envía notificaciones via webhook"""
    from datetime import datetime
    
    # Usar URL del argumento o de la configuración
    url = webhook_url or settings.webhook_url
    if not url:
        logger.warning("No se configuró URL de webhook")
        return
    
    logger.info(f"Enviando resultados a webhook: {url}")
    
    # Crear cliente webhook
    webhook_client = SyncWebhookClient(
        webhook_url=url,
        api_key=settings.webhook_api_key,
        timeout=settings.webhook_timeout,
        retry_count=settings.webhook_retry_count
    )
    
    # Enviar cada resultado exitoso
    sent_count = 0
    for result in results:
        if not result.get('success'):
            continue
            
        try:
            detection_data = result.get('results', {})
            detections = []
            
            # Convertir detecciones al formato del webhook
            for det in detection_data.get('detections', []):
                severity_map = {
                    1: Severity.LOW,
                    2: Severity.MEDIUM,
                    3: Severity.HIGH,
                    4: Severity.CRITICAL
                }
                
                detection = Detection(
                    stage=det.get('stage', det.get('class', 0)),
                    confidence=det.get('confidence', 0.0),
                    bbox=det.get('bbox', []),
                    area=det.get('area', 0.0),
                    severity=severity_map.get(det.get('stage', 1), Severity.INFO)
                )
                detections.append(detection)
            
            # Crear payload
            payload = DetectionPayload(
                image_path=result.get('image_path', ''),
                patient_id=patient_code,
                timestamp=datetime.utcnow(),
                detections=detections,
                total_detected=len(detections),
                processing_time=result.get('processing_time', 0.0),
                metadata={
                    'filename': result.get('filename', ''),
                    'success': result.get('success', False)
                }
            )
            
            # Enviar webhook
            response = webhook_client.send_detection(payload)
            
            if response.success:
                sent_count += 1
                logger.info(f"Webhook enviado exitosamente para {result.get('filename')}")
            else:
                logger.error(f"Error enviando webhook: {response.message}")
                
        except Exception as e:
            logger.error(f"Error procesando webhook para {result.get('filename')}: {e}")
    
    logger.info(f"Se enviaron {sent_count} notificaciones via webhook")


@track_energy("cli_process_images")
def main():
    """Función principal del CLI con tokenización PHI"""
    args = parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar directorios
    if not os.path.exists(args.input):
        logger.error(f"El directorio de entrada no existe: {args.input}")
        return 1
    
    # Crear directorio de salida si no existe
    os.makedirs(args.output, exist_ok=True)
    
    # FASE 1: PHI TOKENIZATION VALIDATION AND PROCESSING
    tokenized_patient = None
    effective_patient_id = None
    
    # Priorizar hospital-mrn sobre patient-code (legacy)
    if args.hospital_mrn:
        # Validar formato Hospital MRN
        if not validate_hospital_mrn(args.hospital_mrn):
            logger.error(f"Hospital MRN inválido: {args.hospital_mrn}")
            logger.info("Formato esperado: MRN-YYYY-NNN-XX (ej: MRN-2025-001-BW)")
            return 1
        
        # Tokenizar PHI: Bruce Wayne → Batman
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tokenized_patient = loop.run_until_complete(
                tokenize_hospital_mrn(args.hospital_mrn)
            )
            if not tokenized_patient:
                logger.error("PHI tokenization failed - cannot process without proper data protection")
                return 1
            
            effective_patient_id = tokenized_patient.token_id  # Use Batman token
            logger.info(f"Using tokenized patient: {tokenized_patient.patient_alias} (Token: {effective_patient_id})")
            
        finally:
            loop.close()
            
    elif args.patient_code:
        # Legacy patient code support (deprecated)
        logger.warning("Using deprecated --patient-code. Consider using --hospital-mrn for PHI compliance.")
        if not validate_patient_code(args.patient_code):
            logger.error(f"Código de paciente inválido: {args.patient_code}")
            logger.info("Formato esperado: XX-YYYY-NNN (ej: CD-2025-001)")
            return 1
        effective_patient_id = args.patient_code
    
    # Listar imágenes
    image_files = list_image_files(args.input)
    if not image_files:
        logger.warning(f"No se encontraron imágenes en: {args.input}")
        return 0
    
    logger.info(f"Se encontraron {len(image_files)} imágenes para procesar")
    
    # Inicializar procesador de imágenes
    processor = ImageProcessor(
        model_type=args.model,
        confidence_threshold=args.confidence,
        anonymize=True  # Siempre anonimizar para proteger privacidad
    )
    
    # Procesar imágenes
    results = []
    for i in range(0, len(image_files), args.batch_size):
        batch = image_files[i:i + args.batch_size]
        logger.info(f"Procesando batch {i//args.batch_size + 1}/{(len(image_files) + args.batch_size - 1)//args.batch_size}")
        
        batch_results = processor.process_batch(
            batch,
            patient_code=effective_patient_id,  # Use Batman token or legacy patient_code
            save_visualizations=True,
            output_dir=args.output
        )
        results.extend(batch_results)
    
    # Mostrar resumen
    print_detection_summary(results)
    
    # Guardar en base de datos si se solicita
    if args.save_db:
        if not effective_patient_id:
            logger.error("Se requiere --hospital-mrn o --patient-code para guardar en base de datos")
            return 1
        
        try:
            db_client = SupabaseClientRefactored()
            process_with_db(results, effective_patient_id, db_client)
        except Exception as e:
            logger.error(f"Error conectando con base de datos: {e}")
            return 1
    
    # Enviar notificaciones via webhook si se solicita
    if args.webhook or settings.webhook_enabled:
        send_webhook_notifications(results, effective_patient_id, args.webhook_url)
    
    # Guardar resumen en archivo
    summary_path = os.path.join(args.output, 'processing_summary.json')
    import json
    from datetime import datetime
    with open(summary_path, 'w') as f:
        summary_data = {
            'effective_patient_id': effective_patient_id,
            'total_images': len(image_files),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add tokenization info if available
        if tokenized_patient:
            summary_data['phi_tokenization'] = {
                'hospital_mrn_partial': args.hospital_mrn[:8] + "..." if args.hospital_mrn else None,
                'tokenized_as': tokenized_patient.patient_alias,
                'token_id': tokenized_patient.token_id,
                'expires_at': tokenized_patient.expires_at.isoformat(),
                'phi_compliant': True
            }
        elif args.patient_code:
            summary_data['legacy_patient_code'] = args.patient_code
            summary_data['phi_compliant'] = False
            
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Resumen guardado en: {summary_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())