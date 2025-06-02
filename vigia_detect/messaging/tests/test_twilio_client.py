"""
Tests para el cliente Twilio de LPP-Detect

Este módulo contiene tests para verificar que los componentes
del cliente Twilio funcionan correctamente.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Importar componentes a testear
from vigia_detect.messaging.twilio_client import TwilioClient

class TestTwilioClient:
    """Tests para el cliente de Twilio"""
    
    @patch('twilio.rest.Client')
    def test_client_initialization(self, mock_client):
        """Verifica la inicialización del cliente Twilio"""
        # Configurar variables de entorno para el test
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_WHATSAPP_FROM': '+14155238886'
        }):
            # Inicializar cliente
            client = TwilioClient()
            
            # Verificar valores
            assert client.account_sid == 'test_sid'
            assert client.auth_token == 'test_token'
            assert client.whatsapp_from == '+14155238886'
    
    @patch('vigia_detect.messaging.twilio_client.Client')
    def test_send_whatsapp(self, mock_client):
        """Verifica el envío de mensajes WhatsApp"""
        # Configurar mock
        mock_messages = MagicMock()
        mock_messages.create.return_value = MagicMock(sid='test_message_sid')
        mock_client.return_value.messages = mock_messages
        
        # Configurar variables de entorno para el test
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_WHATSAPP_FROM': '+14155238886'
        }):
            # Inicializar cliente
            client = TwilioClient()
            
            # Enviar mensaje
            message_sid = client.send_whatsapp('+1234567890', 'Test message')
            
            # Verificar llamada a API
            mock_messages.create.assert_called_once_with(
                body='Test message',
                from_='whatsapp:+14155238886',
                to='whatsapp:+1234567890'
            )
            
            # Verificar SID retornado
            assert message_sid == 'test_message_sid'
    
    @patch('twilio.rest.Client')
    def test_handle_incoming_webhook(self, mock_client):
        """Verifica el procesamiento de webhooks entrantes"""
        # Configurar variables de entorno para el test
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_WHATSAPP_FROM': '+14155238886'
        }):
            # Inicializar cliente
            client = TwilioClient()
            
            # Datos de webhook simulados
            webhook_data = {
                'From': 'whatsapp:+1234567890',
                'Body': 'Test message'
            }
            
            # Procesar webhook
            result = client.handle_incoming_webhook(webhook_data)
            
            # Verificar resultado
            assert 'message' in result
            assert result['sender'] == 'whatsapp:+1234567890'
            assert result['body'] == 'Test message'
    
    @patch('vigia_detect.messaging.twilio_client.Client')
    def test_send_whatsapp_template(self, mock_client):
        """Verifica el envío de plantillas WhatsApp"""
        # Configurar mock
        mock_messages = MagicMock()
        mock_messages.create.return_value = MagicMock(sid='test_template_sid')
        mock_client.return_value.messages = mock_messages
        
        # Configurar variables de entorno para el test
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_WHATSAPP_FROM': '+14155238886'
        }):
            # Inicializar cliente
            client = TwilioClient()
            
            # Enviar plantilla
            template_sid = "HSxxxxx"
            params = {"1": "valor1", "2": "valor2"}
            message_sid = client.send_whatsapp_template('+1234567890', template_sid, params)
            
            # Verificar llamada a API
            mock_messages.create.assert_called_once_with(
                from_='whatsapp:+14155238886',
                body="",  # El cuerpo se genera a partir de la plantilla
                to='whatsapp:+1234567890',
                content_sid=template_sid,
                content_variables=str(params)
            )
            
            # Verificar SID retornado
            assert message_sid == 'test_template_sid'
