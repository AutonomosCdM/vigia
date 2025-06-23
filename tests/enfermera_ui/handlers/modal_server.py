#!/usr/bin/env python3
"""
Servidor Flask para manejar eventos de Slack
Implementa SOLO el modal "Ver Historial Completo"
"""

from flask import Flask, request, jsonify
import json
import os
from slack_sdk import WebClient

app = Flask(__name__)

# Slack client
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")
client = WebClient(token=SLACK_BOT_TOKEN)

def crear_modal_historial():
    """
    Modal EXACTO con datos de las imágenes
    """
    return {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Ver Historial Completo"
        },
        "blocks": [
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
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*🏥 Servicio:*\nTraumatología - Cama 302-A"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*📅 Ingreso:*\n15/01/2025"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*💊 Medicamentos actuales:*\n• Metformina 850mg (2 veces/día)\n• Losartán 50mg (1 vez/día)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*⚠️ Alergias:*\nNinguna conocida"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*🩺 Antecedentes:*\nDM2, HTA\nRiesgo Braden: 14/23"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*📊 Signos vitales:*\nPA: 145/90 mmHg\nFC: 78 bpm\nTemp: 36.8°C"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 HISTORIAL DEL CASO*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*12/01:* Consulta preventiva inicial"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*14/01:* Control sin lesión"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*16/01:* **ESTE CASO** - Eritema emergente"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Evolución:* Progresión 48h"
                    }
                ]
            }
        ]
    }

@app.route('/slack/events', methods=['POST'])
def handle_slack_events():
    """
    Maneja eventos de Slack (incluye verificación URL)
    """
    data = request.json
    
    # Verificación de URL de Slack
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data['challenge']})
    
    return jsonify({'status': 'ok'})

@app.route('/slack/interactivity', methods=['POST'])
def handle_slack_interactivity():
    """
    Maneja interacciones de botones
    """
    try:
        payload = json.loads(request.form['payload'])
        
        if payload.get('type') == 'block_actions':
            action = payload['actions'][0]
            
            # Manejar botón "Ver Historial Completo"
            if action['action_id'] == 'view_full_history_modal':
                modal = crear_modal_historial()
                
                # Abrir modal
                client.views_open(
                    trigger_id=payload['trigger_id'],
                    view=modal
                )
                
                print("✅ Modal historial abierto")
                return jsonify({'status': 'ok'})
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({'status': 'healthy', 'service': 'vigía-modal-handler'})

if __name__ == '__main__':
    print("🚀 INICIANDO SERVIDOR MODAL HISTORIAL")
    print("="*50)
    print("📋 Endpoint: /slack/interactivity")
    print("🔧 Action ID: view_full_history_modal")
    print("📄 Modal: César Durán - Ficha médica completa")
    print("\n🌐 Ejecutar ngrok para obtener URL pública:")
    print("   ngrok http 5000")
    print("\n⚙️ Configurar en Slack App:")
    print("   Interactivity URL: https://[ngrok-url]/slack/interactivity")
    print("\n🎯 Luego presionar botón en Slack")
    
    app.run(debug=True, port=5000)
