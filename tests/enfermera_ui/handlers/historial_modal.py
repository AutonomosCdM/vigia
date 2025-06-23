#!/usr/bin/env python3
"""
Handler para botón "Ver Historial Completo"
Refactorizado para usar módulos centralizados
"""

import sys
import os
from pathlib import Path

# Agregar rutas al path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config.settings import settings
from vigia_detect.core.slack_templates import SlackModalTemplates
from vigia_detect.core.constants import SlackActionIds

# Configurar Slack App usando configuración centralizada
app = App(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret
)

# Handler para el botón usando action_id centralizado
@app.action(SlackActionIds.VER_HISTORIAL)
def handle_historial_completo(ack, body, client):
    """
    Maneja el click del botón "Ver Historial Completo"
    Usa el template centralizado para el modal
    """
    ack()
    
    try:
        # Usar template centralizado para crear modal
        # En producción, obtendríamos los datos del paciente de la DB
        modal = SlackModalTemplates.historial_medico()
        
        # Abrir modal
        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal
        )
        
        app.logger.info("Modal historial abierto exitosamente")
        
    except Exception as e:
        app.logger.error(f"Error abriendo modal: {e}")

# Handler para múltiples action_ids (compatibilidad con versiones anteriores)
@app.action("view_full_history_modal")
@app.action("view_full_history_vigia")
@app.action("view_historial_cesar_definitivo")
@app.action("view_historial_cesar")
def handle_historial_legacy(ack, body, client):
    """
    Handler de compatibilidad para action_ids antiguos
    Redirige al handler principal
    """
    handle_historial_completo(ack, body, client)


if __name__ == "__main__":
    print("🔧 Handler de Historial Médico - Refactorizado")
    print("="*50)
    
    print("✅ Usando módulos centralizados:")
    print(f"  📁 Configuración desde: config.settings")
    print(f"  📋 Templates desde: core.slack_templates")
    print(f"  🔧 Action IDs desde: core.constants")
    
    print("\n🎯 Action IDs soportados:")
    print(f"  - {SlackActionIds.VER_HISTORIAL} (principal)")
    print("  - view_full_history_modal (legacy)")
    print("  - view_full_history_vigia (legacy)")
    
    print("\n✅ LISTO PARA FUNCIONAR")
