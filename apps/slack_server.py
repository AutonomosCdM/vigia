"""
Servidor unificado para manejar interactividad de Slack
Maneja botones, modales y comandos slash
"""
import os
import logging
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Importar configuración centralizada
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

# Configurar logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Inicializar Slack App con Bolt
slack_app = App(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret
)

# Inicializar Flask
flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)

# Cliente Slack para operaciones adicionales
client = WebClient(token=settings.slack_bot_token)


# ============= HANDLERS DE BOTONES =============

@slack_app.action("ver_historial_medico")
def handle_ver_historial(ack, body, client):
    """Handler para el botón Ver Historial Médico"""
    ack()
    
    try:
        # Obtener información del usuario y mensaje
        user_id = body["user"]["id"]
        trigger_id = body["trigger_id"]
        
        # Datos del paciente desde el mensaje original
        patient_name = "César Durán"
        patient_id = "CD-2025-001"
        
        # Abrir modal con historial médico
        modal = crear_modal_historial(patient_name, patient_id)
        
        result = client.views_open(
            trigger_id=trigger_id,
            view=modal
        )
        logger.info(f"Modal abierto para usuario {user_id}")
        
    except SlackApiError as e:
        logger.error(f"Error abriendo modal: {e.response['error']}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")


@slack_app.action("solicitar_evaluacion_medica")
def handle_solicitar_evaluacion(ack, body, client):
    """Handler para Solicitar Evaluación Médica"""
    ack()
    
    try:
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        
        # Notificar al médico de turno
        client.chat_postMessage(
            channel=channel_id,
            text=f"🏥 <@{user_id}> ha solicitado evaluación médica urgente para el paciente César Durán (CD-2025-001)",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🚨 Evaluación Médica Solicitada*\n\n" +
                               f"• Solicitado por: <@{user_id}>\n" +
                               f"• Paciente: César Durán\n" +
                               f"• ID: CD-2025-001\n" +
                               f"• Ubicación: Traumatología - Cama 302-A\n" +
                               f"• Prioridad: *ALTA*"
                    }
                }
            ]
        )
        
        # Actualizar el mensaje original
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="✅ Evaluación médica solicitada. El médico de turno ha sido notificado."
        )
        
    except Exception as e:
        logger.error(f"Error solicitando evaluación: {str(e)}")


@slack_app.action("marcar_resuelto")
def handle_marcar_resuelto(ack, body, client):
    """Handler para Marcar como Resuelto"""
    ack()
    
    try:
        # Abrir modal para ingresar resolución
        trigger_id = body["trigger_id"]
        
        modal = {
            "type": "modal",
            "callback_id": "resolucion_modal",
            "title": {"type": "plain_text", "text": "Marcar como Resuelto"},
            "submit": {"type": "plain_text", "text": "Confirmar"},
            "close": {"type": "plain_text", "text": "Cancelar"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "resolucion_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "resolucion_text",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Describa las acciones tomadas y el resultado..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Resolución del Caso"
                    }
                }
            ]
        }
        
        client.views_open(trigger_id=trigger_id, view=modal)
        
    except Exception as e:
        logger.error(f"Error abriendo modal de resolución: {str(e)}")


# ============= HANDLERS DE MODALES =============

@slack_app.view("resolucion_modal")
def handle_resolucion_submission(ack, body, view, client):
    """Handler para el envío del modal de resolución"""
    ack()
    
    try:
        # Obtener valores del modal
        values = view["state"]["values"]
        resolucion = values["resolucion_input"]["resolucion_text"]["value"]
        user_id = body["user"]["id"]
        
        # Aquí se guardaría en la base de datos
        # TODO: Integrar con Supabase
        
        # Notificar en el canal
        client.chat_postMessage(
            channel=settings.slack_channel_lpp,
            text="✅ Caso resuelto",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*✅ Caso Resuelto*\n\n" +
                               f"• Resuelto por: <@{user_id}>\n" +
                               f"• Paciente: César Durán (CD-2025-001)\n\n" +
                               f"*Resolución:*\n{resolucion}"
                    }
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error procesando resolución: {str(e)}")


# ============= FUNCIONES AUXILIARES =============

def crear_modal_historial(patient_name: str, patient_id: str) -> dict:
    """Crear modal con historial médico del paciente"""
    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Historial Médico"},
        "close": {"type": "plain_text", "text": "Cerrar"},
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📋 {patient_name}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*ID Paciente:*\n{patient_id}"},
                    {"type": "mrkdwn", "text": "*Edad:*\n45 años"},
                    {"type": "mrkdwn", "text": "*Servicio:*\nTraumatología"},
                    {"type": "mrkdwn", "text": "*Cama:*\n302-A"}
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🏥 Diagnósticos Actuales:*\n" +
                           "• Fractura de cadera derecha (post-operatorio)\n" +
                           "• Diabetes Mellitus tipo 2\n" +
                           "• Hipertensión arterial controlada"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💊 Medicación Actual:*\n" +
                           "• Metformina 850mg c/12h\n" +
                           "• Losartán 50mg c/24h\n" +
                           "• Tramadol 50mg c/8h PRN\n" +
                           "• Omeprazol 20mg c/24h"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 Úlceras por Presión - Historial:*\n" +
                           "• *2025-01-15*: Grado 1 en sacro - Resuelto\n" +
                           "• *2025-02-01*: Grado 2 en talón izq - En tratamiento\n" +
                           "• *2025-02-22*: Grado 1 en sacro - Nueva detección"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔄 Última Movilización:*\n2025-02-22 14:30 hrs"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Observaciones:*\nPaciente con movilidad reducida post-quirúrgica. " +
                           "Requiere cambios posturales c/2h. Piel frágil, alto riesgo de UPP."
                }
            }
        ]
    }


# ============= RUTAS FLASK =============

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Endpoint principal para eventos de Slack"""
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "vigia-slack-server"})


@flask_app.route("/", methods=["GET"])
def index():
    """Página de inicio"""
    return jsonify({
        "service": "Vigía Slack Integration Server",
        "version": "1.0.0",
        "status": "running"
    })


# ============= MAIN =============

if __name__ == "__main__":
    logger.info(f"Starting Vigía Slack Server on {settings.server_host}:{settings.server_port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Webhook path: {settings.webhook_path}")
    
    # Advertencia si estamos usando credenciales de desarrollo
    if settings.environment == "development":
        logger.warning("Running in DEVELOPMENT mode - ensure ngrok is running for local testing")
    
    flask_app.run(
        host=settings.server_host,
        port=settings.server_port,
        debug=settings.debug
    )