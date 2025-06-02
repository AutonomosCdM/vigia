#!/usr/bin/env python3
"""
Script de prueba para el cliente Twilio de LPP-Detect

Este script envía un mensaje de prueba vía WhatsApp usando
el cliente Twilio configurado.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twilio-test")

# Cargar variables de entorno
load_dotenv()

# Verificar credenciales
if not os.getenv('TWILIO_ACCOUNT_SID') or not os.getenv('TWILIO_AUTH_TOKEN'):
    logger.error("ERROR: Faltan credenciales de Twilio en variables de entorno")
    logger.error("Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM")
    sys.exit(1)

# Importar el cliente
try:
    from vigia_detect.messaging.twilio_client import TwilioClient
    client = TwilioClient()
    logger.info("Cliente Twilio inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando cliente Twilio: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    # Obtener número de destino
    if len(sys.argv) < 2:
        logger.error("Uso: python test_twilio.py <número_destino>")
        logger.error("Ejemplo: python test_twilio.py +56912345678")
        sys.exit(1)
    
    to_number = sys.argv[1]
    
    # Validar número
    if not client.validate_phone_number(to_number):
        logger.error(f"Número inválido: {to_number}")
        logger.error("Debe tener formato E.164 (ej: +56912345678)")
        sys.exit(1)
    
    # Enviar mensaje de prueba
    try:
        message = "🔬 Este es un mensaje de prueba del sistema LPP-Detect. Si lo recibe, la configuración es correcta."
        message_sid = client.send_whatsapp(to_number, message)
        logger.info(f"Mensaje enviado correctamente. SID: {message_sid}")
    except Exception as e:
        logger.error(f"Error enviando mensaje: {str(e)}")
        sys.exit(1)
