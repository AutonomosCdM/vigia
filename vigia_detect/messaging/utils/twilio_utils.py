"""
Utilidades para trabajar con Twilio y WhatsApp

Este módulo proporciona funciones de utilidad para trabajar con
Twilio y WhatsApp, como validación de números, manejo de URLs de medios, etc.
"""

import re
import json
import hmac
import hashlib
import base64
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, Optional, List, Union

def validate_webhook_signature(request_data: Dict[str, Any], signature: str, auth_token: str) -> bool:
    """
    Valida la firma de un webhook de Twilio
    
    Args:
        request_data: Datos recibidos en el webhook
        signature: Firma X-Twilio-Signature del header
        auth_token: Token de autenticación de Twilio
        
    Returns:
        bool: True si la firma es válida
    """
    # Ordenar los parámetros por clave
    sorted_params = sorted(request_data.items())
    
    # Crear una cadena de validación
    validation_string = ''.join(f"{k}{v}" for k, v in sorted_params)
    
    # Calcular la firma
    computed_signature = hmac.new(
        auth_token.encode('utf-8'),
        validation_string.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    # Codificar en base64
    computed_signature_base64 = base64.b64encode(computed_signature).decode('utf-8')
    
    # Comparar firmas
    return hmac.compare_digest(computed_signature_base64, signature)

def format_whatsapp_number(number: str) -> str:
    """
    Formatea un número de teléfono para uso con WhatsApp
    
    Args:
        number: Número de teléfono (puede tener diferentes formatos)
        
    Returns:
        str: Número formateado para WhatsApp (whatsapp:+123456789)
    """
    # Limpiar el número de cualquier formato
    cleaned = re.sub(r'[^\d+]', '', number)
    
    # Asegurar que tenga prefijo internacional
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # Agregar prefijo WhatsApp si no lo tiene
    if not cleaned.startswith('whatsapp:'):
        cleaned = f'whatsapp:{cleaned}'
    
    return cleaned

def extract_media_info(webhook_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extrae información de medios de un webhook de Twilio
    
    Args:
        webhook_data: Datos del webhook
        
    Returns:
        List[Dict]: Lista de medios con url y tipo
    """
    num_media = int(webhook_data.get('NumMedia', 0))
    media_list = []
    
    for i in range(num_media):
        media_url = webhook_data.get(f'MediaUrl{i}')
        media_type = webhook_data.get(f'MediaContentType{i}')
        
        if media_url and media_type:
            media_list.append({
                'url': media_url,
                'type': media_type
            })
    
    return media_list

def is_image_media(media_type: str) -> bool:
    """
    Verifica si un tipo MIME corresponde a una imagen
    
    Args:
        media_type: Tipo MIME del medio
        
    Returns:
        bool: True si es una imagen
    """
    return media_type.startswith('image/')

def parse_twilio_error(error_json: str) -> Dict[str, Any]:
    """
    Parsea un error de Twilio para mostrar información útil
    
    Args:
        error_json: JSON de error de Twilio
        
    Returns:
        Dict: Información del error parseada
    """
    try:
        error_data = json.loads(error_json)
        return {
            'code': error_data.get('code', 0),
            'message': error_data.get('message', 'Unknown error'),
            'more_info': error_data.get('more_info', ''),
            'status': error_data.get('status', 0)
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            'message': str(error_json),
            'code': 0,
            'status': 0
        }


def validate_media_format(media_url: str, content_type: str = None) -> Dict[str, Any]:
    """
    Validate media format for medical image processing.
    
    Args:
        media_url: URL of the media file
        content_type: MIME type of the media
        
    Returns:
        Dict: Validation result with format info
    """
    # Supported medical image formats
    supported_formats = {
        'image/jpeg': 'jpeg',
        'image/jpg': 'jpeg', 
        'image/png': 'png',
        'image/tiff': 'tiff',
        'image/bmp': 'bmp'
    }
    
    # Extract extension from URL
    parsed_url = urlparse(media_url)
    file_path = parsed_url.path.lower()
    
    if content_type and content_type.lower() in supported_formats:
        return {
            'valid': True,
            'format': supported_formats[content_type.lower()],
            'content_type': content_type,
            'medical_compatible': True
        }
    
    # Check by file extension
    for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
        if file_path.endswith(ext):
            return {
                'valid': True,
                'format': ext[1:],  # Remove dot
                'content_type': f'image/{ext[1:]}',
                'medical_compatible': True
            }
    
    return {
        'valid': False,
        'format': 'unknown',
        'content_type': content_type or 'unknown',
        'medical_compatible': False,
        'error': 'Unsupported media format for medical analysis'
    }
