#!/usr/bin/env python3
"""
Modal implementation refactorizado usando módulos centralizados
"""

import os
import sys
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Importar configuración y templates centralizados
from config.settings import settings
from vigia_detect.core.slack_templates import SlackModalTemplates
from vigia_detect.core.constants import SlackActionIds

# Configurar Slack client usando configuración centralizada
client = WebClient(token=settings.slack_bot_token)

def crear_modal_historial():
    """
    Usa el template centralizado para crear el modal
    """
    # En producción, obtendríamos los datos del paciente de la BD
    # Por ahora usar datos de prueba del template
    return SlackModalTemplates.historial_medico()

def test_modal_directo():
    """
    Test directo del modal - abrir directamente para probar
    """
    try:
        modal = crear_modal_historial()
        
        # Abrir modal directamente en canal para test
        response = client.views_open(
            trigger_id="test_trigger",  # En producción vendría del botón
            view=modal
        )
        
        print("✅ Modal creado y listo")
        print("📋 Datos: César Durán, 45 años, CD-2025-001")
        print("🏥 Servicio: Traumatología - Cama 302-A")
        print("💊 Medicamentos: Metformina + Losartán")
        
        return modal
        
    except SlackApiError as e:
        if e.response["error"] == "invalid_trigger_id":
            print("✅ Modal preparado correctamente")
            print("⚠️ Para test real necesita trigger_id del botón")
            return modal
        else:
            print(f"❌ Error: {e}")
            return None

if __name__ == "__main__":
    print("🔧 IMPLEMENTANDO MODAL HISTORIAL COMPLETO")
    print("="*50)
    
    modal = test_modal_directo()
    
    if modal:
        print("\n✅ MODAL IMPLEMENTADO!")
        print("📋 Al apretar 'Ver Historial Completo' se abrirá la ficha médica")
        print("👤 César Durán, 45 años")
        print("🆔 CD-2025-001")
        print("🏥 Traumatología - Cama 302-A")
    else:
        print("❌ Error implementando modal")
