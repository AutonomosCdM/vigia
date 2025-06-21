"""
Slack Webhook Handler for Block Kit Interactions
Handles interactive components like buttons, modals, and form submissions
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from ..mcp.gateway import create_mcp_gateway
from ..utils.shared_utilities import VigiaLogger
from .block_kit_medical import BlockKitMedical, BlockKitInteractions

logger = VigiaLogger.get_logger(__name__)


class SlackWebhookHandler:
    """Handler for Slack webhook events and interactions"""
    
    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret
    
    async def handle_event(self, request: Request) -> Dict[str, Any]:
        """Handle incoming Slack events"""
        try:
            body = await request.body()
            payload = await self._parse_payload(body)
            
            event_type = payload.get('type')
            
            if event_type == 'url_verification':
                # Slack URL verification challenge
                return {"challenge": payload.get('challenge')}
            
            elif event_type == 'event_callback':
                # Handle app events
                return await self._handle_app_event(payload.get('event', {}))
            
            elif event_type == 'interactive_message' or event_type == 'block_actions':
                # Handle interactive components
                return await self._handle_interaction(payload)
            
            elif event_type == 'view_submission':
                # Handle modal submissions
                return await self._handle_modal_submission(payload)
            
            else:
                logger.warning(f"Unhandled event type: {event_type}")
                return {"status": "ignored"}
                
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _parse_payload(self, body: bytes) -> Dict[str, Any]:
        """Parse incoming webhook payload"""
        try:
            # Handle URL-encoded payload (form data)
            body_str = body.decode('utf-8')
            if body_str.startswith('payload='):
                # Extract JSON from URL-encoded form
                import urllib.parse
                payload_str = urllib.parse.unquote_plus(body_str[8:])
                return json.loads(payload_str)
            else:
                # Direct JSON payload
                return json.loads(body_str)
        except Exception as e:
            logger.error(f"Failed to parse payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload format")
    
    async def _handle_app_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack app events"""
        event_type = event.get('type')
        
        if event_type == 'app_mention':
            # Handle @mention of the app
            return await self._handle_mention(event)
        
        elif event_type == 'message':
            # Handle direct messages
            return await self._handle_message(event)
        
        return {"status": "event_processed"}
    
    async def _handle_mention(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle when the app is mentioned"""
        text = event.get('text', '').lower()
        channel = event.get('channel')
        user = event.get('user')
        
        # Simple command parsing
        if 'help' in text or 'ayuda' in text:
            return await self._send_help_message(channel)
        
        elif 'test' in text or 'prueba' in text:
            return await self._send_test_alert(channel)
        
        elif 'historia' in text or 'historial' in text:
            return await self._send_test_patient_history(channel)
        
        return {"status": "mention_processed"}
    
    async def _handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct messages to the app"""
        # For now, just acknowledge
        return {"status": "message_processed"}
    
    async def _handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive component actions"""
        try:
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                response = await gateway.handle_slack_interaction(payload)
                return response
                
        except Exception as e:
            logger.error(f"Error handling interaction: {e}")
            return {
                "response_type": "ephemeral",
                "text": f"Error procesando acción: {str(e)}"
            }
    
    async def _handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal form submissions"""
        try:
            view = payload.get('view', {})
            callback_id = view.get('callback_id', '')
            
            if callback_id.startswith('case_resolution_'):
                case_id = callback_id.replace('case_resolution_', '')
                
                # Extract form values
                state_values = view.get('state', {}).get('values', {})
                description = self._extract_input_value(state_values, 'resolution_description', 'description_input')
                time_selection = self._extract_select_value(state_values, 'resolution_time', 'time_select')
                followup_options = self._extract_checkbox_values(state_values, 'followup_required', 'followup_checkboxes')
                
                # Process the case resolution
                await self._process_case_resolution(case_id, description, time_selection, followup_options)
                
                return {
                    "response_action": "update",
                    "view": {
                        "type": "modal",
                        "title": {
                            "type": "plain_text",
                            "text": "Caso Resuelto ✅"
                        },
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"✅ *Caso {case_id} ha sido marcado como resuelto exitosamente.*\n\n*Descripción:* {description[:100]}...\n*Tiempo de resolución:* {time_selection}\n*Acciones de seguimiento:* {len(followup_options)} programadas"
                                }
                            },
                            {
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        "text": "🔒 Información registrada en sistema de auditoría médica"
                                    }
                                ]
                            }
                        ]
                    }
                }
            
            return {"response_action": "clear"}
            
        except Exception as e:
            logger.error(f"Error handling modal submission: {e}")
            return {
                "response_action": "errors",
                "errors": {
                    "resolution_description": "Error procesando formulario"
                }
            }
    
    def _extract_input_value(self, state_values: Dict, block_id: str, action_id: str) -> str:
        """Extract text input value from modal state"""
        return state_values.get(block_id, {}).get(action_id, {}).get('value', '')
    
    def _extract_select_value(self, state_values: Dict, block_id: str, action_id: str) -> str:
        """Extract select value from modal state"""
        return state_values.get(block_id, {}).get(action_id, {}).get('selected_option', {}).get('value', '')
    
    def _extract_checkbox_values(self, state_values: Dict, block_id: str, action_id: str) -> list:
        """Extract checkbox values from modal state"""
        return [opt.get('value') for opt in state_values.get(block_id, {}).get(action_id, {}).get('selected_options', [])]
    
    async def _process_case_resolution(self, case_id: str, description: str, 
                                     time_selection: str, followup_options: list):
        """Process case resolution in medical system"""
        try:
            # Log the resolution
            resolution_data = {
                'case_id': case_id,
                'description': description,
                'resolution_time': time_selection,
                'followup_actions': followup_options,
                'resolved_at': logger.get_timestamp(),
                'resolved_via': 'slack_block_kit'
            }
            
            logger.info(f"Case resolution processed: {resolution_data}")
            
            # In production, save to database and trigger workflows
            # await self.medical_system.resolve_case(resolution_data)
            
        except Exception as e:
            logger.error(f"Error processing case resolution: {e}")
    
    async def _send_help_message(self, channel: str) -> Dict[str, Any]:
        """Send help message with available commands"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 Vigía Medical Assistant - Ayuda"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Comandos disponibles:*\n• `@vigia help` - Mostrar esta ayuda\n• `@vigia test` - Enviar alerta de prueba\n• `@vigia historial` - Mostrar historial de paciente de prueba"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Funciones automáticas:*\n• Alertas LPP con botones interactivos\n• Historial médico HIPAA-compliant\n• Resolución de casos con formularios\n• Escalamiento de emergencias médicas"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🏥 Sistema Vigía v1.0 | 🔒 HIPAA Compliant"
                    }
                ]
            }
        ]
        
        try:
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                await gateway.send_slack_block_kit(channel, blocks, "Ayuda del Sistema Vigía")
        except Exception as e:
            logger.error(f"Error sending help message: {e}")
        
        return {"status": "help_sent"}
    
    async def _send_test_alert(self, channel: str) -> Dict[str, Any]:
        """Send test LPP alert"""
        try:
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                await gateway.send_lpp_alert_slack(
                    case_id="TEST_001",
                    patient_code="PAT001",
                    lpp_grade=2,
                    confidence=0.85,
                    location="sacrum",
                    service="UCI",
                    bed="201A",
                    channel=channel
                )
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
        
        return {"status": "test_alert_sent"}
    
    async def _send_test_patient_history(self, channel: str) -> Dict[str, Any]:
        """Send test patient history"""
        test_patient = {
            'id': 'TEST123',
            'name': 'Test Patient',
            'age': 75,
            'service': 'UCI',
            'bed': 'TEST-001',
            'diagnoses': ['Diabetes mellitus tipo 2', 'Hipertensión arterial'],
            'medications': ['Metformina 850mg', 'Enalapril 10mg'],
            'lpp_history': [
                {
                    'date': '2024-01-15',
                    'grade': 2,
                    'location': 'talón derecho',
                    'status': 'resuelto'
                }
            ]
        }
        
        try:
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                await gateway.send_patient_history_slack(test_patient, channel)
        except Exception as e:
            logger.error(f"Error sending test patient history: {e}")
        
        return {"status": "test_history_sent"}


def create_slack_webhook_handler(signing_secret: str) -> SlackWebhookHandler:
    """Factory function to create Slack webhook handler"""
    return SlackWebhookHandler(signing_secret)