"""
Slack interface for medical detection interactions.
Refactored from apps/slack_server.py with proper configuration management.
"""
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from ..core.base_client_v2 import BaseClientV2
from ..core.constants import SlackActionIds, SlackChannels


class SlackInterface(BaseClientV2):
    """
    Enhanced Slack interface using centralized configuration.
    Handles buttons, modals, and slash commands.
    """
    
    def __init__(self):
        """Initialize Slack interface with centralized settings"""
        required_fields = [
            'slack_bot_token',
            'slack_signing_secret'
        ]
        
        super().__init__(
            service_name="SlackInterface",
            required_fields=required_fields
        )
    
    def _initialize_client(self):
        """Initialize Slack Bolt app and Flask handler"""
        try:
            # Initialize Slack Bolt App
            self.slack_app = App(
                token=self.settings.slack_bot_token,
                signing_secret=self.settings.slack_signing_secret
            )
            
            # Initialize Flask app for HTTP handling
            self.flask_app = Flask(__name__)
            self.handler = SlackRequestHandler(self.slack_app)
            
            # Slack Web client for additional operations
            self.client = WebClient(token=self.settings.slack_bot_token)
            
            # Register handlers
            self._register_handlers()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Slack interface: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """Validate Slack API connection"""
        try:
            response = self.client.auth_test()
            return response.get("ok", False)
        except Exception as e:
            self.logger.error(f"Slack connection validation failed: {str(e)}")
            return False
    
    def _register_handlers(self):
        """Register all Slack event handlers"""
        
        @self.slack_app.action(SlackActionIds.VER_HISTORIAL)
        def handle_ver_historial(ack, body, client):
            """Handler for medical history button"""
            ack()
            self._handle_medical_history_request(body, client)
        
        @self.slack_app.action(SlackActionIds.SOLICITAR_EVALUACION)
        def handle_solicitar_evaluacion(ack, body, client):
            """Handler for medical evaluation request"""
            ack()
            self._handle_evaluation_request(body, client)
        
        @self.slack_app.action(SlackActionIds.MARCAR_RESUELTO)
        def handle_marcar_resuelto(ack, body, client):
            """Handler for marking case as resolved"""
            ack()
            self._handle_case_resolution(body, client)
        
        # Flask route for health check
        @self.flask_app.route("/health", methods=["GET"])
        def health_check():
            health = self.health_check()
            return jsonify(health)
        
        # Flask route for Slack events
        @self.flask_app.route("/slack/events", methods=["POST"])
        def slack_events():
            return self.handler.handle(request)
    
    def _handle_medical_history_request(self, body: Dict[str, Any], client: WebClient):
        """Handle medical history view request"""
        try:
            user_id = body["user"]["id"]
            trigger_id = body["trigger_id"]
            
            # Get patient data from the message context
            patient_data = self._extract_patient_data(body)
            
            # Create medical history modal
            modal_view = self._create_medical_history_modal(patient_data)
            
            # Open modal
            client.views_open(trigger_id=trigger_id, view=modal_view)
            
        except Exception as e:
            self.logger.error(f"Error handling medical history request: {str(e)}")
    
    def _handle_evaluation_request(self, body: Dict[str, Any], client: WebClient):
        """Handle medical evaluation request"""
        try:
            user_id = body["user"]["id"]
            channel_id = body["container"]["channel_id"]
            
            # Create evaluation request message
            evaluation_message = self._create_evaluation_message(user_id)
            
            # Post to medical channel
            client.chat_postMessage(
                channel=SlackChannels.get_channel("project_lpp"),
                **evaluation_message
            )
            
        except Exception as e:
            self.logger.error(f"Error handling evaluation request: {str(e)}")
    
    def _handle_case_resolution(self, body: Dict[str, Any], client: WebClient):
        """Handle case resolution marking"""
        try:
            user_id = body["user"]["id"]
            trigger_id = body["trigger_id"]
            
            # Create resolution modal
            modal_view = self._create_resolution_modal()
            
            # Open modal
            client.views_open(trigger_id=trigger_id, view=modal_view)
            
        except Exception as e:
            self.logger.error(f"Error handling case resolution: {str(e)}")
    
    def _extract_patient_data(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient data from Slack message context"""
        # In a real implementation, this would extract from the message
        # For now, return sample data structure
        return {
            "patient_id": "SAMPLE_001",
            "patient_name": "Paciente de Ejemplo",
            "age": "65 años",
            "condition": "LPP Grado 2 en sacro"
        }
    
    def _create_medical_history_modal(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create medical history modal view"""
        return {
            "type": "modal",
            "callback_id": SlackActionIds.MODAL_HISTORIAL,
            "title": {"type": "plain_text", "text": "Historial Médico"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Paciente:* {patient_data['patient_name']}\\n"
                               f"*Edad:* {patient_data['age']}\\n"
                               f"*Condición:* {patient_data['condition']}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Historial médico completo disponible en el sistema de gestión hospitalaria.*"
                    }
                }
            ]
        }
    
    def _create_evaluation_message(self, requesting_user: str) -> Dict[str, Any]:
        """Create medical evaluation request message"""
        return {
            "text": "Solicitud de Evaluación Médica",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🏥 *Nueva Solicitud de Evaluación Médica*\\n\\n"
                               f"Solicitado por: <@{requesting_user}>\\n"
                               f"Urgencia: Media\\n"
                               f"Tipo: Evaluación LPP"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Aceptar Evaluación"},
                            "value": "accept_evaluation",
                            "action_id": SlackActionIds.ACEPTAR_EVALUACION,
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
    
    def _create_resolution_modal(self) -> Dict[str, Any]:
        """Create case resolution modal"""
        return {
            "type": "modal",
            "callback_id": SlackActionIds.MODAL_RESOLUCION,
            "title": {"type": "plain_text", "text": "Marcar como Resuelto"},
            "submit": {"type": "plain_text", "text": "Confirmar"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Describir la resolución del caso..."}
                    },
                    "label": {"type": "plain_text", "text": "Comentarios de Resolución"}
                }
            ]
        }
    
    def run_server(self, host: str = "0.0.0.0", port: int = 3000, debug: bool = False):
        """Run the Flask server"""
        self.logger.info(f"Starting Slack interface server on {host}:{port}")
        self.flask_app.run(host=host, port=port, debug=debug)