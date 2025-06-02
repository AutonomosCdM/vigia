"""
Cliente Twilio para LPP-Detect.

Este módulo proporciona una interfaz para interactuar con la API de Twilio,
específicamente para enviar mensajes de WhatsApp y procesar webhooks.
"""

import os
from twilio.rest import Client
from typing import Dict, Optional, Any, Union

class TwilioClient:
    def __init__(self):
        """
        Inicializa el cliente Twilio con credenciales de las variables de entorno.
        
        Raises:
            ValueError: Si faltan las credenciales requeridas.
        """
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', '+14155238886')  # Default to sandbox
        
        if not all([self.account_sid, self.auth_token]):
            raise ValueError("Missing required Twilio credentials in environment variables")
            
        self.client = Client(self.account_sid, self.auth_token)

    def send_whatsapp(self, to_number: str, message: str) -> str:
        """
        Envía un mensaje de WhatsApp vía API de Twilio
        
        Args:
            to_number: Número de destino en formato E.164 (ej: +56912345678)
            message: Contenido del mensaje
            
        Returns:
            str: SID del mensaje enviado
        
        Raises:
            Exception: Si hay un error en el envío
        """
        try:
            # Ensure number has proper format
            to_number = self._format_whatsapp_number(to_number)
            
            message = self.client.messages.create(
                body=message,
                from_=f'whatsapp:{self.whatsapp_from}',
                to=to_number
            )
            return message.sid
        except Exception as e:
            raise Exception(f"Failed to send WhatsApp message: {str(e)}")

    def send_whatsapp_template(self, to_number: str, template_sid: str, params: Dict[str, Any]) -> str:
        """
        Envía un mensaje basado en plantilla de WhatsApp
        
        Args:
            to_number: Número de destino en formato E.164
            template_sid: SID de la plantilla aprobada
            params: Parámetros para la plantilla
            
        Returns:
            str: SID del mensaje enviado
        
        Raises:
            Exception: Si hay un error en el envío
        """
        try:
            # Ensure number has proper format
            to_number = self._format_whatsapp_number(to_number)
            
            message = self.client.messages.create(
                from_=f'whatsapp:{self.whatsapp_from}',
                body="", # El cuerpo se genera a partir de la plantilla
                to=to_number,
                content_sid=template_sid,
                content_variables=str(params)
            )
            return message.sid
        except Exception as e:
            raise Exception(f"Failed to send WhatsApp template: {str(e)}")

    def handle_incoming_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud webhook entrante de Twilio
        
        Args:
            data: Datos del webhook
            
        Returns:
            Dict: Datos procesados
        """
        return {
            'message': 'Message processed',
            'sender': data.get('From'),
            'body': data.get('Body'),
            'num_media': int(data.get('NumMedia', 0)),
            'media_urls': [data.get(f'MediaUrl{i}') for i in range(int(data.get('NumMedia', 0)))],
            'media_types': [data.get(f'MediaContentType{i}') for i in range(int(data.get('NumMedia', 0)))]
        }

    def validate_phone_number(self, number: str) -> bool:
        """
        Valida el formato de un número de teléfono
        
        Args:
            number: Número a validar
            
        Returns:
            bool: True si el formato es válido
        """
        # Validación básica - extender con Twilio Lookup API si es necesario
        return number and number.startswith('+') and number[1:].isdigit()

    def _format_whatsapp_number(self, number: str) -> str:
        """
        Asegura que el número tenga el formato correcto para WhatsApp
        
        Args:
            number: Número de teléfono (con o sin prefijo whatsapp:)
            
        Returns:
            str: Número con formato correcto
        """
        if not number.startswith('whatsapp:'):
            number = f'whatsapp:{number}'
        return number
