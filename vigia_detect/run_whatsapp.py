#!/usr/bin/env python3
"""
Script para iniciar el servidor WhatsApp de LPP-Detect

Este script configura el entorno y arranca el servidor Flask que maneja
los webhooks de WhatsApp vía Twilio.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('whatsapp_server.log')
    ]
)
logger = logging.getLogger('lpp-detect.run_whatsapp')

# Agregar directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    # Cargar desde el directorio raíz del proyecto
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    logger.info(f"Variables de entorno cargadas desde {env_path}")
except ImportError:
    logger.warning("python-dotenv no instalado, continuando sin cargar .env")
except Exception as e:
    logger.warning(f"Error cargando .env: {e}")

# Verificar credenciales Twilio
if not os.getenv('TWILIO_ACCOUNT_SID') or not os.getenv('TWILIO_AUTH_TOKEN'):
    logger.error("ERROR: Faltan credenciales de Twilio en variables de entorno")
    logger.error("Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM")
    sys.exit(1)

# Asegurar que tenemos modelo YOLOv5 disponible
model_path = os.path.join('lpp_detect', 'cv_pipeline', 'models', 'yolov5s.pt')
if not os.path.exists(model_path):
    logger.warning(f"Modelo YOLOv5 no encontrado en {model_path}")
    logger.warning("La detección operará en modo de simulación")

if __name__ == "__main__":
    try:
        from vigia_detect.messaging.whatsapp.server import start_server
        
        # Obtener puerto de variable de entorno o usar 5005 por defecto
        port = int(os.environ.get('PORT', 5005))
        
        # Informar al usuario sobre la configuración
        logger.info(f"Iniciando servidor WhatsApp en puerto {port}...")
        logger.info(f"Usando cuenta Twilio: {os.getenv('TWILIO_ACCOUNT_SID')}")
        logger.info(f"Número WhatsApp configurado: {os.getenv('TWILIO_WHATSAPP_FROM', 'no configurado')}")
        
        # Iniciar servidor
        start_server(port)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario")
    except Exception as e:
        logger.error(f"Error iniciando servidor: {str(e)}")
        sys.exit(1)
