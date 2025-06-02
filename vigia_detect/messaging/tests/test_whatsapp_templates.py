"""
Tests para las plantillas de mensajes de WhatsApp

Este módulo contiene tests para verificar que las plantillas
de mensajes de WhatsApp funcionan correctamente.
"""

import pytest
from vigia_detect.messaging.templates.whatsapp_templates import (
    welcome_template,
    help_template,
    results_template,
    error_template,
    processing_template,
    info_template
)

class TestWhatsAppTemplates:
    """Tests para las plantillas de WhatsApp"""
    
    def test_welcome_template(self):
        """Verifica que la plantilla de bienvenida contiene elementos clave"""
        message = welcome_template()
        assert '¡Bienvenido a LPP-Detect!' in message
        assert 'Envíe una imagen clara' in message
    
    def test_help_template(self):
        """Verifica que la plantilla de ayuda contiene elementos clave"""
        message = help_template()
        assert '*Comandos disponibles:*' in message
        assert "'ayuda'" in message
        assert "'info'" in message
        assert "'registro'" in message
    
    def test_results_template_with_detections(self):
        """Verifica que la plantilla de resultados muestra detecciones correctamente"""
        detections = [
            {
                'stage': 1,
                'confidence': 0.85,
                'class_name': 'LPP-Stage1'
            }
        ]
        
        message = results_template(detections)
        assert '*ANÁLISIS PRELIMINAR:*' in message
        assert '*Lesión 1:*' in message
        assert 'Categoría 2' in message
        assert '85.0%' in message
        assert '*Recomendaciones:*' in message
        assert 'ATENCIÓN:' in message
    
    def test_results_template_without_detections(self):
        """Verifica que la plantilla de resultados maneja el caso sin detecciones"""
        message = results_template([])
        assert '*ANÁLISIS PRELIMINAR*' in message
        assert 'No se detectaron lesiones por presión' in message
    
    def test_error_template(self):
        """Verifica que la plantilla de error contiene elementos clave"""
        message = error_template("Error de conexión")
        assert '⚠️ *ERROR EN PROCESAMIENTO*' in message
        assert 'Error de conexión' in message
        assert 'Intente nuevamente' in message
    
    def test_processing_template(self):
        """Verifica que la plantilla de procesamiento contiene elementos clave"""
        message = processing_template()
        assert '🔄 *PROCESANDO IMAGEN*' in message
        assert 'analizando su imagen' in message
        assert 'resultados en breve' in message
    
    def test_info_template(self):
        """Verifica que la plantilla de información contiene elementos clave"""
        message = info_template()
        assert '*Sobre LPP-Detect*' in message
        assert '*¿Qué son las LPP?*' in message
        assert '*¿Cómo funciona?*' in message
        assert '*Limitaciones*' in message
        assert '*Privacidad*' in message
