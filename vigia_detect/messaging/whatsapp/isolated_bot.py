"""
WhatsApp Bot Aislado - Capa 1: Entrada Segura
Principio: Zero Medical Knowledge

Responsabilidades ÚNICAS:
- Recibir inputs multimedia (imagen/texto/video)
- Validar formato básico (no contenido médico)
- Generar session token único
- Empaquetar payload estandarizado
- Enviar a Input Queue

Restricciones CRÍTICAS:
- ❌ NO lee códigos de paciente
- ❌ NO interpreta contenido médico
- ❌ NO accede a bases de datos clínicas
- ❌ NO toma decisiones de routing
- ❌ NO mantiene estado médico
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from ..utils.twilio_utils import validate_media_format
from ...utils.secure_logger import SecureLogger

# Configurar logging seguro
logger = SecureLogger("isolated_whatsapp_bot")


class IsolatedWhatsAppBot:
    """
    WhatsApp Bot completamente aislado de conocimiento médico.
    Solo maneja entrada y empaquetado básico.
    """
    
    # Formatos permitidos (validación técnica básica)
    ALLOWED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        """Inicializar bot aislado sin acceso a servicios médicos."""
        self.session_prefix = "VIGIA_SESSION"
        
        # CRITICAL: No medical database connections
        # CRITICAL: No patient code validation
        # CRITICAL: No medical content interpretation
        
        logger.audit("isolated_whatsapp_bot_initialized", {
            "component": "layer1_input",
            "medical_access": False,
            "isolation_level": "complete"
        })
    
    def receive_whatsapp_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recibir mensaje de WhatsApp sin interpretación médica.
        
        Args:
            webhook_data: Raw webhook data from Twilio
            
        Returns:
            Standardized input package or error response
        """
        try:
            # Generar session ID único
            session_id = self._generate_session_id()
            
            # Validar formato básico (NO contenido médico)
            validation_result = self._validate_basic_format(webhook_data)
            if not validation_result['valid']:
                return self._create_error_response(
                    session_id, 
                    validation_result['error'],
                    "format_validation_failed"
                )
            
            # Crear payload estandarizado
            standardized_payload = self._create_standardized_payload(
                webhook_data, session_id
            )
            
            # Log de actividad (sin datos PII)
            logger.audit("whatsapp_message_received", {
                "session_id": session_id,
                "input_type": standardized_payload['input_type'],
                "source": "whatsapp",
                "timestamp": standardized_payload['timestamp'],
                "has_media": standardized_payload.get('metadata', {}).get('has_media', False)
            })
            
            return {
                "success": True,
                "session_id": session_id,
                "payload": standardized_payload,
                "next_step": "input_queue"
            }
            
        except Exception as e:
            session_id = self._generate_session_id()
            logger.error("whatsapp_message_processing_failed", {
                "session_id": session_id,
                "error": str(e),
                "component": "isolated_whatsapp_bot"
            })
            
            return self._create_error_response(
                session_id,
                "Internal processing error",
                "processing_failed"
            )
    
    def _generate_session_id(self) -> str:
        """Generar session ID único para rastreo."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{self.session_prefix}_{timestamp}_{unique_id}"
    
    def _validate_basic_format(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación básica de formato SIN interpretación médica.
        
        CRITICAL: No medical validation, only technical format checks
        """
        try:
            # Verificar estructura básica del webhook
            if not webhook_data.get('Body') and not webhook_data.get('MediaUrl0'):
                return {
                    "valid": False,
                    "error": "Empty message: no text or media provided"
                }
            
            # Validar media si existe
            media_url = webhook_data.get('MediaUrl0')
            if media_url:
                media_type = webhook_data.get('MediaContentType0', '')
                file_size = int(webhook_data.get('MediaSize0', 0))
                
                # Validar tamaño
                if file_size > self.MAX_FILE_SIZE:
                    return {
                        "valid": False,
                        "error": f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
                    }
                
                # Validar tipo de archivo
                if not self._is_supported_media_type(media_type):
                    return {
                        "valid": False,
                        "error": f"Unsupported media type: {media_type}"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Format validation error: {str(e)}"
            }
    
    def _is_supported_media_type(self, media_type: str) -> bool:
        """Verificar si el tipo de media es soportado."""
        if not media_type:
            return False
        
        # Formatos de imagen
        if media_type.startswith('image/'):
            return any(fmt[1:] in media_type for fmt in self.ALLOWED_IMAGE_FORMATS)
        
        # Formatos de video
        if media_type.startswith('video/'):
            return any(fmt[1:] in media_type for fmt in self.ALLOWED_VIDEO_FORMATS)
        
        return False
    
    def _create_standardized_payload(self, webhook_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Crear payload estandarizado según especificación del documento.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Determinar tipo de input
        has_media = bool(webhook_data.get('MediaUrl0'))
        has_text = bool(webhook_data.get('Body', '').strip())
        
        if has_media and has_text:
            input_type = "mixed"
        elif has_media:
            input_type = "image" if webhook_data.get('MediaContentType0', '').startswith('image/') else "video"
        else:
            input_type = "text"
        
        # Crear contenido sin procesar (raw_content)
        raw_content = {
            "text": webhook_data.get('Body', ''),
            "media_url": webhook_data.get('MediaUrl0'),
            "media_type": webhook_data.get('MediaContentType0'),
            "from_number": webhook_data.get('From', ''),
            "to_number": webhook_data.get('To', '')
        }
        
        # Crear checksum para integridad
        content_string = str(raw_content)
        checksum = hashlib.sha256(content_string.encode()).hexdigest()
        
        # Crear ID anonimizado de fuente
        source_id = hashlib.sha256(
            webhook_data.get('From', '').encode()
        ).hexdigest()[:16]
        
        return {
            'session_id': session_id,
            'timestamp': timestamp,
            'input_type': input_type,
            'raw_content': raw_content,
            'metadata': {
                'source': 'whatsapp',
                'format': webhook_data.get('MediaContentType0', 'text/plain'),
                'size': int(webhook_data.get('MediaSize0', 0)),
                'checksum': checksum,
                'has_media': has_media,
                'has_text': has_text
            },
            'audit_trail': {
                'received_at': timestamp,
                'source_id': source_id,
                'processing_id': str(uuid.uuid4())
            }
        }
    
    def _create_error_response(self, session_id: str, error_message: str, error_code: str) -> Dict[str, Any]:
        """Crear respuesta de error estandarizada."""
        return {
            "success": False,
            "session_id": session_id,
            "error": {
                "message": error_message,
                "code": error_code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "next_step": "error_handler"
        }
    
    def generate_whatsapp_response(self, error_info: Dict[str, Any]) -> str:
        """
        Generar respuesta de WhatsApp para errores de formato.
        
        CRITICAL: No medical advice, only technical guidance
        """
        error_code = error_info.get('error', {}).get('code', 'unknown_error')
        
        # Respuestas técnicas básicas (sin contenido médico)
        responses = {
            "format_validation_failed": (
                "❌ *Error de Formato*\n\n"
                "El archivo enviado no cumple con los requisitos técnicos:\n"
                "• Formatos permitidos: JPG, PNG, MP4\n"
                "• Tamaño máximo: 10MB\n"
                "• Incluir texto con la imagen\n\n"
                "Por favor, reenvía el archivo en el formato correcto."
            ),
            "processing_failed": (
                "❌ *Error Técnico*\n\n"
                "Ocurrió un problema técnico procesando tu mensaje.\n"
                "Por favor, intenta nuevamente en unos minutos.\n\n"
                "Si el problema persiste, contacta al administrador del sistema."
            ),
            "file_too_large": (
                "❌ *Archivo Muy Grande*\n\n"
                "El archivo supera el límite de 10MB.\n"
                "Por favor, reduce el tamaño del archivo y reenvía."
            )
        }
        
        return responses.get(error_code, responses["processing_failed"])


class WhatsAppResponseGenerator:
    """Generador de respuestas de WhatsApp sin conocimiento médico."""
    
    @staticmethod
    def generate_technical_error_response(error_type: str) -> str:
        """Generar respuesta técnica de error."""
        bot = IsolatedWhatsAppBot()
        return bot.generate_whatsapp_response({"error": {"code": error_type}})
    
    @staticmethod
    def generate_processing_confirmation() -> str:
        """Confirmar recepción para procesamiento."""
        return (
            "✅ *Mensaje Recibido*\n\n"
            "Tu imagen ha sido recibida y está siendo procesada.\n"
            "Recibirás una respuesta en breve.\n\n"
            "⏱️ Tiempo estimado: 30 segundos"
        )