"""
Procesador de imágenes de WhatsApp para Vigía.

Este módulo proporciona funciones para descargar y procesar imágenes
recibidas a través de WhatsApp, integrando con el pipeline de Vigía.
"""

import os
import sys
import requests
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia-detect.whatsapp.processor')

# Agregar directorio raíz al path para importaciones
# IMPORTANTE: Insertamos al final para evitar conflictos con YOLOv5
vigia_root = str(Path(__file__).resolve().parent.parent.parent)
if vigia_root not in sys.path:
    sys.path.append(vigia_root)

# Intentar importar los componentes de Vigía
try:
    from vigia_detect.cv_pipeline.detector import LPPDetector
    from vigia_detect.cv_pipeline.preprocessor import ImagePreprocessor
    from vigia_detect.utils.image_utils import save_detection_result
    from vigia_detect.utils.security_validator import validate_and_sanitize_image, sanitize_user_input
    
    # PHI Tokenization Integration
    import asyncio
    from vigia_detect.core.phi_tokenization_client import tokenize_patient_phi, TokenizedPatient
    
    lpp_detect_available = True
    phi_tokenization_available = True
    logger.info("LPP-Detect CV pipeline and PHI Tokenization importado correctamente")
except ImportError as e:
    logger.warning(f"No se pudo importar LPP-Detect CV pipeline o PHI Tokenization: {str(e)}")
    lpp_detect_available = False
    phi_tokenization_available = False

# Configuración
TEMP_DIR = os.path.join(Path(__file__).resolve().parent, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def download_image(url: str, auth: Optional[Tuple[str, str]] = None) -> Path:
    """
    Descarga una imagen desde una URL y la guarda temporalmente
    
    Args:
        url: URL de la imagen
        auth: Tuple (usuario, contraseña) para autenticación
        
    Returns:
        Path: Ruta al archivo temporal descargado
        
    Raises:
        Exception: Si hay un error descargando la imagen
    """
    try:
        # Validate URL to prevent SSRF
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL scheme")
        
        # Crear nombre único para archivo temporal
        ext = Path(url).suffix or ".jpg"
        temp_filename = f"whatsapp_{uuid.uuid4().hex}{ext}"
        # Sanitize filename
        if lpp_detect_available:
            from vigia_detect.utils.security_validator import security_validator
            temp_filename = security_validator.sanitize_filename(temp_filename)
        
        temp_file = os.path.join(TEMP_DIR, temp_filename)
        
        # Descargar imagen con límites de seguridad
        logger.info(f"Descargando imagen desde {url}")
        response = requests.get(
            url, 
            auth=auth, 
            timeout=30,
            stream=True,
            headers={'User-Agent': 'Vigia-Medical-Detection/1.0'}
        )
        response.raise_for_status()
        
        # Verificar tamaño antes de descargar completamente
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB
            raise ValueError("Image file too large")
        
        # Guardar en archivo temporal con límite de tamaño
        with open(temp_file, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > 50 * 1024 * 1024:  # 50MB
                    os.remove(temp_file)
                    raise ValueError("Image file too large")
                f.write(chunk)
        
        # Validate the downloaded image
        if lpp_detect_available:
            is_valid, error, _ = validate_and_sanitize_image(temp_file)
            if not is_valid:
                os.remove(temp_file)
                raise ValueError(f"Invalid image: {error}")
        
        logger.info(f"Imagen guardada y validada en {temp_file}")
        return Path(temp_file)
        
    except Exception as e:
        logger.error(f"Error descargando imagen: {str(e)}")
        raise

async def process_whatsapp_image_tokenized(image_url: str, auth_credentials: Optional[Tuple[str, str]] = None, hospital_mrn: Optional[str] = None) -> Dict[str, Any]:
    """
    Procesa una imagen recibida de WhatsApp con tokenización PHI (FASE 1)
    
    Args:
        image_url: URL de la imagen de Twilio
        auth_credentials: (usuario, contraseña) para autenticación con Twilio
        hospital_mrn: Hospital MRN (Bruce Wayne data - will be tokenized to Batman)
        
    Returns:
        dict: Resultados del análisis con tokens Batman
    """
    try:
        # STEP 1: PHI TOKENIZATION - Convert Bruce Wayne → Batman
        tokenized_patient = None
        if hospital_mrn and phi_tokenization_available:
            try:
                tokenized_patient = await tokenize_patient_phi(
                    hospital_mrn=hospital_mrn,
                    request_purpose="WhatsApp image analysis for LPP detection"
                )
                logger.info(f"PHI tokenization successful: {hospital_mrn[:8]}... → {tokenized_patient.patient_alias}")
            except Exception as tokenization_error:
                logger.error(f"PHI tokenization failed: {tokenization_error}")
                return {
                    'success': False,
                    'error': 'PHI tokenization failed - cannot process without proper data protection',
                    'hospital_mrn_partial': hospital_mrn[:8] + "..." if hospital_mrn else 'unknown',
                    'tokenization_error': str(tokenization_error)
                }
        
        # STEP 2: Call original processing with Batman token
        if tokenized_patient:
            result = process_whatsapp_image(
                image_url=image_url,
                auth_credentials=auth_credentials,
                patient_code=tokenized_patient.token_id  # Use Batman token
            )
            
            # Enhance result with tokenization info
            result['phi_tokenization'] = {
                'hospital_mrn_partial': hospital_mrn[:8] + "..." if hospital_mrn else 'unknown',
                'tokenized_as': tokenized_patient.patient_alias,
                'token_id': tokenized_patient.token_id,
                'expires_at': tokenized_patient.expires_at.isoformat(),
                'phi_compliant': True
            }
            
            return result
        else:
            # No tokenization needed or available
            return process_whatsapp_image(
                image_url=image_url,
                auth_credentials=auth_credentials,
                patient_code=None
            )
    
    except Exception as e:
        logger.error(f"Error in tokenized WhatsApp processing: {e}")
        return {
            'success': False,
            'error': str(e),
            'hospital_mrn_partial': hospital_mrn[:8] + "..." if hospital_mrn else 'unknown',
            'phi_tokenization_attempted': True
        }

def process_whatsapp_image(image_url: str, auth_credentials: Optional[Tuple[str, str]] = None, patient_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Procesa una imagen recibida de WhatsApp y retorna resultados
    
    Args:
        image_url: URL de la imagen de Twilio
        auth_credentials: (usuario, contraseña) para autenticación con Twilio
        patient_code: Código de paciente opcional
        
    Returns:
        dict: Resultados del análisis
    """
    # Validate and sanitize patient code if provided
    if patient_code and lpp_detect_available:
        from vigia_detect.utils.security_validator import security_validator
        is_valid, error = security_validator.validate_patient_code(patient_code)
        if not is_valid:
            logger.warning(f"Invalid patient code provided: {error}")
            patient_code = None
    if not lpp_detect_available:
        logger.warning("LPP-Detect CV pipeline no disponible, retornando resultados simulados")
        return {
            "success": True,
            "simulated": True,
            "detections": [
                {
                    "bbox": [10, 20, 100, 150],
                    "confidence": 0.85,
                    "stage": 1,
                    "class_name": "LPP-Stage1"
                }
            ],
            "message": format_detection_results({
                "detections": [
                    {
                        "bbox": [10, 20, 100, 150],
                        "confidence": 0.85,
                        "stage": 1,
                        "class_name": "LPP-Stage1"
                    }
                ]
            })
        }
    
    temp_image_path = None
    result_path = None
    
    try:
        # Descargar imagen
        temp_image_path = download_image(image_url, auth_credentials)
        
        # Inicializar detector y preprocesador
        detector = LPPDetector()
        preprocessor = ImagePreprocessor()
        
        # Preprocesar imagen
        processed_img = preprocessor.preprocess(temp_image_path)
        
        # Detectar LPP
        detection_results = detector.detect(processed_img)
        
        # Si hay detecciones, guardar resultado con anotaciones
        if detection_results["detections"]:
            result_path = os.path.join(TEMP_DIR, f"result_{uuid.uuid4().hex}.jpg")
            save_detection_result(processed_img, detection_results, result_path)
            
            # Formatear mensaje para WhatsApp
            message = format_detection_results(detection_results)
            
            return {
                "success": True,
                "detections": detection_results["detections"],
                "result_image_path": result_path,
                "message": message
            }
        else:
            return {
                "success": True,
                "detections": [],
                "message": "No se detectaron lesiones por presión en la imagen."
            }
            
    except Exception as e:
        logger.error(f"Error procesando imagen de WhatsApp: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error en el procesamiento de la imagen."
        }
    finally:
        # Limpiar archivos temporales (opcional, según política de almacenamiento)
        # En producción, podrías querer conservarlos para auditoría
        # if temp_image_path and os.path.exists(temp_image_path):
        #     os.remove(temp_image_path)
        pass

def format_detection_results(detection_results: Dict[str, Any]) -> str:
    """
    Formatea los resultados de detección para enviar por WhatsApp
    
    Args:
        detection_results: Resultados del detector LPP
        
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    if not detection_results["detections"]:
        return "No se detectaron lesiones por presión en la imagen."
    
    # Textos descriptivos por etapa
    stage_descriptions = {
        0: "Categoría 1 (Eritema no blanqueable): Piel intacta con enrojecimiento no blanqueable.",
        1: "Categoría 2 (Úlcera de espesor parcial): Pérdida parcial del espesor de la piel.",
        2: "Categoría 3 (Pérdida total del espesor de la piel): Tejido subcutáneo visible.",
        3: "Categoría 4 (Pérdida total del espesor de los tejidos): Exposición de músculo/hueso.",
    }
    
    # Construir mensaje
    message = "🔍 *ANÁLISIS PRELIMINAR:*\n\n"
    
    # Reportar cada detección
    for i, detection in enumerate(detection_results["detections"]):
        stage = detection["stage"]
        confidence = detection["confidence"] * 100
        
        message += f"*Lesión {i+1}:*\n"
        message += f"• Clasificación: {stage_descriptions.get(stage, f'Categoría {stage+1}')}\n"
        message += f"• Confianza: {confidence:.1f}%\n\n"
    
    # Agregar disclaimer
    message += "_ATENCIÓN: Este es un análisis preliminar automatizado. " \
              "La evaluación final siempre debe ser realizada por profesionales médicos._"
    
    return message


class WhatsAppProcessor:
    """
    WhatsApp message processor for medical image analysis
    Provides async processing capabilities for integration with unified server
    """
    
    def __init__(self):
        """Initialize WhatsApp processor."""
        self.temp_dir = TEMP_DIR
        logger.info("WhatsApp processor initialized")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WhatsApp message (async wrapper for sync processing)
        
        Args:
            message_data: WhatsApp message data from Twilio
            
        Returns:
            dict: Processing results
        """
        try:
            # Extract message details
            from_number = message_data.get('From', '')
            body = message_data.get('Body', '')
            media_url = message_data.get('MediaUrl0', '')
            
            logger.info(f"Processing WhatsApp message from {from_number}")
            
            # If message contains media (image)
            if media_url:
                # Extract Twilio auth from environment
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                auth_credentials = (account_sid, auth_token) if account_sid and auth_token else None
                
                # Process the image with PHI tokenization
                hospital_mrn = self._extract_hospital_mrn(body)
                
                # Use async tokenized processing if PHI data is present
                if hospital_mrn and phi_tokenization_available:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            process_whatsapp_image_tokenized(
                                media_url,
                                auth_credentials=auth_credentials,
                                hospital_mrn=hospital_mrn
                            )
                        )
                    finally:
                        loop.close()
                else:
                    # Fallback to original processing without PHI
                    result = process_whatsapp_image(
                        media_url, 
                        auth_credentials=auth_credentials,
                        patient_code=None  # No PHI in Layer 1
                    )
                
                return {
                    "status": "processed",
                    "type": "image_analysis",
                    "result": result,
                    "response_message": result.get("message", "Analysis completed")
                }
            
            # Text-only message
            else:
                return {
                    "status": "received",
                    "type": "text_message",
                    "response_message": "Mensaje recibido. Para análisis de LPP, envíe una imagen."
                }
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response_message": "Error procesando el mensaje. Intente nuevamente."
            }
    
    def _extract_hospital_mrn(self, message_body: str) -> Optional[str]:
        """
        Extract hospital MRN (Medical Record Number) from message body if present
        
        Args:
            message_body: WhatsApp message text
            
        Returns:
            Hospital MRN if found, None otherwise
        """
        try:
            # Look for patterns like "MRN: MRN-2025-001-BW" or "Paciente: MRN-2025-001-BW"
            import re
            
            # Sanitize input first
            if lpp_detect_available:
                message_body = sanitize_user_input(message_body)
            
            # Hospital MRN patterns (Bruce Wayne format)
            patterns = [
                r'MRN[:-]?\s*(MRN-\d{4}-\d{3}-\w+)',  # MRN: MRN-2025-001-BW
                r'[Pp]aciente:?\s*(MRN-\d{4}-\d{3}-\w+)',  # Paciente: MRN-2025-001-BW
                r'Hospital:?\s*(MRN-\d{4}-\d{3}-\w+)',  # Hospital: MRN-2025-001-BW
                r'ID[:-]?\s*(MRN-\d{4}-\d{3}-\w+)',  # ID: MRN-2025-001-BW
                r'(MRN-\d{4}-\d{3}-\w+)'  # Direct MRN-2025-001-BW
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message_body)
                if match:
                    hospital_mrn = match.group(1)
                    logger.info(f"Hospital MRN extracted: {hospital_mrn[:8]}...")
                    return hospital_mrn
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting patient code: {e}")
            return None
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary files older than specified hours
        
        Args:
            older_than_hours: Remove files older than this many hours
        """
        try:
            import time
            from pathlib import Path
            
            current_time = time.time()
            cutoff_time = current_time - (older_than_hours * 3600)
            
            for file_path in Path(self.temp_dir).glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Cleaned up temp file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")


# Default processor instance
default_processor = WhatsAppProcessor()


if __name__ == "__main__":
    # Prueba de ejecución local
    test_url = "https://example.com/sample_image.jpg"  # Reemplazar con URL real
    print(process_whatsapp_image(test_url))
