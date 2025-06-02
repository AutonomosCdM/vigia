#!/usr/bin/env python3
"""
TEST FINAL: Botón que abre modal historial completo
SOLO para probar que funciona el botón → modal
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from vigia_detect.messaging.slack_notifier import SlackNotifier

def test_boton_modal():
    """
    Envía mensaje simple con botón que debe abrir modal
    """
    
    notifier = SlackNotifier()
    
    # Mensaje minimo con SOLO el botón que debe funcionar
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🟡 TEST BOTÓN HISTORIAL",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*👤 Paciente:*\nCésar Durán, 45 años"
                },
                {
                    "type": "mrkdwn", 
                    "text": "*🆔 ID Caso:*\nCD-2025-001"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "view_full_history_modal",  # ESTE ES EL ACTION_ID CLAVE
                    "text": {
                        "type": "plain_text",
                        "text": "📋 Ver Historial Completo",
                        "emoji": True
                    },
                    "style": "primary"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⚠️ Presionar botón para abrir modal con ficha médica"
                }
            ]
        }
    ]
    
    try:
        print("🔧 Enviando test botón modal...")
        
        response = notifier.client.chat_postMessage(
            channel='C08KK1SRE5S',  # #project-lpp
            text="🔧 TEST - Botón Historial",
            blocks=blocks
        )
        
        print(f"✅ TEST ENVIADO!")
        print(f"📍 Timestamp: {response['ts']}")
        print(f"🎯 Action ID: view_full_history_modal")
        print(f"📋 Al presionar debe abrir modal con:")
        print(f"   👤 César Durán, 45 años")
        print(f"   🏥 Traumatología - Cama 302-A")
        print(f"   💊 Medicamentos + Antecedentes")
        
        return response
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    print("🔧 TEST FINAL - BOTÓN → MODAL HISTORIAL")
    print("="*50)
    
    response = test_boton_modal()
    
    if response:
        print("\n✅ TEST LISTO!")
        print("📱 Ir a Slack y presionar 'Ver Historial Completo'")
        print("📋 Debe abrir modal con ficha médica exacta")
        print("\n🎯 Si no funciona, verificar:")
        print("  1. Action ID: view_full_history_modal")
        print("  2. Handler configurado en Slack App")
        print("  3. Permisos de modal en Slack")
    else:
        print("❌ Error enviando test")
