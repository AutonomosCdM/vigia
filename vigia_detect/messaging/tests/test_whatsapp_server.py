"""
Tests para el servidor de webhooks de WhatsApp

Este módulo contiene tests para verificar que el servidor Flask
para webhooks de WhatsApp funciona correctamente.
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from twilio.twiml.messaging_response import MessagingResponse

# Importar componentes a testear
from vigia_detect.messaging.whatsapp.server import app, whatsapp_webhook

@pytest.fixture
def client():
    """Fixture para cliente de prueba Flask"""
    with app.test_client() as client:
        yield client

class TestWhatsAppServer:
    """Tests para el servidor de webhooks"""
    
    def test_index_route(self, client):
        """Verifica que la ruta principal devuelve HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'html' in response.data.decode('utf-8').lower()
        assert 'LPP-Detect WhatsApp Server' in response.data.decode('utf-8')
    
    @patch('vigia_detect.messaging.whatsapp.server.process_whatsapp_image')
    @patch('vigia_detect.messaging.whatsapp.server.twilio_client')
    def test_whatsapp_webhook_image(self, mock_twilio_client, mock_process_image, client):
        """Verifica que el webhook procesa imágenes correctamente"""
        # Configurar mocks
        mock_process_image.return_value = {
            'success': True,
            'message': 'Análisis completado',
            'detections': [{'stage': 1, 'confidence': 0.85}]
        }
        
        # Datos de prueba para webhook
        data = {
            'From': 'whatsapp:+1234567890',
            'NumMedia': '1',
            'MediaUrl0': 'https://example.com/image.jpg',
            'MediaContentType0': 'image/jpeg'
        }
        
        # Enviar solicitud
        response = client.post('/webhook/whatsapp', data=data)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert 'Imagen recibida' in response.data.decode('utf-8')
    
    def test_whatsapp_webhook_text(self, client):
        """Verifica que el webhook procesa mensajes de texto correctamente"""
        # Datos de prueba para webhook
        data = {
            'From': 'whatsapp:+1234567890',
            'Body': 'hola',
            'NumMedia': '0'
        }
        
        # Enviar solicitud
        response = client.post('/webhook/whatsapp', data=data)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert '¡Hola!' in response.data.decode('utf-8')
    
    def test_whatsapp_webhook_error_handling(self, client):
        """Verifica que el webhook maneja errores correctamente"""
        # Enviar solicitud sin datos requeridos
        response = client.post('/webhook/whatsapp', data={})
        
        # Verificar que no falla y devuelve respuesta TwiML
        assert response.status_code == 200
        assert 'Response' in response.data.decode('utf-8')
        assert 'Comando no reconocido' in response.data.decode('utf-8')
