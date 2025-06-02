
#!/usr/bin/env python3
"""
SOLUCIÓN SIMPLE: Actualizar el mensaje para usar request URL existente
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from vigia_detect.messaging.slack_notifier import SlackNotifier

def enviar_mensaje_con_modal_funcional():
    """
    Envía mensaje usando la Request URL que ya está configurada
    """
    
    notifier = SlackNotifier()
    
    # Mensaje con botón que debe usar la URL existente
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text", 
                "text": "🟡 VIGÍA - CÉSAR DURÁN - CON MODAL FUNCIONAL",
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
                    "action_id": "view_historial_cesar",  # Nuevo action_id único
                    "text": {
                        "type": "plain_text",
                        "text": "📋 Ver Historial Completo",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": "cesar_duran_cd_2025_001"  # Datos del caso
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "📋 Presionar para ver ficha médica completa con medicamentos, antecedentes e historial"
                }
            ]
        }
    ]
    
    try:
        print("🚀 Enviando mensaje con modal funcional...")
        
        response = notifier.client.chat_postMessage(
            channel='C08KK1SRE5S',  # #project-lpp
            text="🟡 VIGÍA - César Durán - Modal Funcional",
            blocks=blocks
        )
        
        print(f"✅ MENSAJE ENVIADO!")
        print(f"📍 Timestamp: {response['ts']}")
        print(f"🔧 Action ID: view_historial_cesar")
        print(f"💾 Value: cesar_duran_cd_2025_001")
        
        print("\n📋 Modal incluirá:")
        print("  👤 César Durán, 45 años")
        print("  🆔 CD-2025-001") 
        print("  🏥 Traumatología - Cama 302-A")
        print("  📅 Ingreso: 15/01/2025")
        print("  💊 Metformina 850mg + Losartán 50mg")
        print("  ⚠️ Alergias: Ninguna conocida")
        print("  🩺 Antecedentes: DM2, HTA, Riesgo Braden 14/23")
        print("  📊 Signos vitales: PA, FC, Temp")
        print("  📋 Historial: 12/01, 14/01, 16/01 ESTE CASO")
        
        return response
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    print("📋 VIGÍA - MODAL HISTORIAL FUNCIONAL")
    print("="*50)
    print("🎯 Usando Request URL existente de Slack App")
    
    response = enviar_mensaje_con_modal_funcional()
    
    if response:
        print("\n✅ MENSAJE CON MODAL PREPARADO!")
        print("📱 Ir a Slack y presionar botón")
        print("📋 Debe abrir modal con ficha médica de César Durán")
        print("\n💡 Si no funciona: verificar Request URL en Slack App settings")
    else:
        print("❌ Error enviando mensaje")
