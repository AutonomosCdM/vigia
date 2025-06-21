"""
Slack Event Handler ADK Agent - Native Google ADK Implementation
==============================================================

ADK EventHandler for Slack webhook events and interactions.
Processes Slack events through proper ADK patterns.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from google.adk.agents import EventHandler, AgentContext, AgentResponse
from google.adk.core.types import AgentCapability, AgentMessage, AgentEvent
from google.adk.tools import Tool

from .base import VigiaBaseAgent
from .slack_block_kit import create_slack_block_kit_agent
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class SlackEventHandlerAgent(VigiaBaseAgent, EventHandler):
    """
    ADK EventHandler for Slack webhook events.
    
    Capabilities:
    - EVENT_PROCESSING: Process Slack webhook events
    - INTERACTION_HANDLING: Handle interactive components
    - MEDICAL_COMMUNICATION: Medical event routing
    - WORKFLOW_COORDINATION: Coordinate medical workflows
    """
    
    def __init__(self):
        """Initialize Slack Event Handler Agent with ADK capabilities."""
        
        super().__init__(
            agent_id="slack_event_handler_agent",
            agent_name="Slack Event Handler Medical Agent",
            capabilities=[
                AgentCapability.EVENT_PROCESSING,
                AgentCapability.INTERACTION_HANDLING,
                AgentCapability.MEDICAL_COMMUNICATION,
                AgentCapability.WORKFLOW_COORDINATION
            ],
            medical_specialties=[
                "event_processing",
                "webhook_handling",
                "medical_communication",
                "workflow_coordination"
            ]
        )
        
        # Initialize EventHandler
        EventHandler.__init__(self)
        
        # Create Block Kit agent for UI operations
        self.block_kit_agent = None
        
        # Register event handling tools
        self.tools.extend(self._create_event_tools())
        
        logger.info("Slack Event Handler ADK Agent initialized")
    
    async def get_block_kit_agent(self):
        """Get or create Block Kit agent instance."""
        if self.block_kit_agent is None:
            self.block_kit_agent = create_slack_block_kit_agent()
        return self.block_kit_agent
    
    def _create_event_tools(self) -> list[Tool]:
        """Create ADK Tools for event processing."""
        tools = []
        
        # URL Verification Tool
        def handle_url_verification(challenge: str) -> Dict[str, Any]:
            """Handle Slack URL verification challenge.
            
            Args:
                challenge: Slack verification challenge
                
            Returns:
                Challenge response for URL verification
            """
            logger.info("Processing Slack URL verification challenge")
            return {"challenge": challenge}
        
        tools.append(Tool(
            name="handle_url_verification",
            function=handle_url_verification,
            description="Handle Slack URL verification challenge"
        ))
        
        # App Mention Tool
        def handle_app_mention(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle app mention events.
            
            Args:
                event_data: Slack app mention event data
                
            Returns:
                Response for app mention
            """
            text = event_data.get('text', '').lower()
            channel = event_data.get('channel')
            user = event_data.get('user')
            
            logger.info(f"Processing app mention from user {user} in channel {channel}")
            
            # Simple command parsing
            if 'help' in text or 'ayuda' in text:
                return {
                    "type": "help_request",
                    "channel": channel,
                    "user": user
                }
            elif 'test' in text or 'prueba' in text:
                return {
                    "type": "test_request",
                    "channel": channel,
                    "user": user
                }
            elif 'historia' in text or 'historial' in text:
                return {
                    "type": "history_request",
                    "channel": channel,
                    "user": user
                }
            else:
                return {
                    "type": "unknown_command",
                    "channel": channel,
                    "user": user,
                    "text": text
                }
        
        tools.append(Tool(
            name="handle_app_mention",
            function=handle_app_mention,
            description="Process Slack app mention events"
        ))
        
        # Interaction Processing Tool
        def process_interaction_event(payload: Dict[str, Any]) -> Dict[str, Any]:
            """Process Slack interaction events.
            
            Args:
                payload: Slack interaction payload
                
            Returns:
                Processed interaction event
            """
            event_type = payload.get('type')
            
            if event_type == 'block_actions':
                actions = payload.get('actions', [])
                if actions:
                    action = actions[0]
                    return {
                        "type": "button_click",
                        "action_id": action.get('action_id'),
                        "value": action.get('value'),
                        "user_id": payload.get('user', {}).get('id'),
                        "channel_id": payload.get('channel', {}).get('id')
                    }
            
            elif event_type == 'view_submission':
                view = payload.get('view', {})
                return {
                    "type": "modal_submission",
                    "callback_id": view.get('callback_id'),
                    "state_values": view.get('state', {}).get('values', {}),
                    "user_id": payload.get('user', {}).get('id')
                }
            
            return {
                "type": "unknown_interaction",
                "payload_type": event_type
            }
        
        tools.append(Tool(
            name="process_interaction_event",
            function=process_interaction_event,
            description="Process Slack interactive component events"
        ))
        
        return tools
    
    async def handle_event(self, event: AgentEvent, context: AgentContext) -> AgentResponse:
        """Handle incoming Slack events via ADK pattern.
        
        Args:
            event: ADK AgentEvent containing Slack webhook data
            context: Agent execution context
            
        Returns:
            AgentResponse with event processing result
        """
        
        try:
            event_data = event.data
            event_type = event_data.get('type')
            
            logger.info(f"Processing Slack event type: {event_type}")
            
            if event_type == 'url_verification':
                # Handle URL verification
                challenge = event_data.get('challenge')
                result = await self.tools["handle_url_verification"](challenge)
                
                return AgentResponse(
                    success=True,
                    data=result,
                    message="URL verification challenge processed"
                )
                
            elif event_type == 'event_callback':
                # Handle app events
                inner_event = event_data.get('event', {})
                inner_event_type = inner_event.get('type')
                
                if inner_event_type == 'app_mention':
                    # Process app mention
                    mention_result = await self.tools["handle_app_mention"](inner_event)
                    
                    # Route to appropriate handler based on mention type
                    if mention_result["type"] == "help_request":
                        return await self._send_help_response(mention_result["channel"])
                    elif mention_result["type"] == "test_request":
                        return await self._send_test_alert(mention_result["channel"])
                    elif mention_result["type"] == "history_request":
                        return await self._send_test_history(mention_result["channel"])
                    else:
                        return AgentResponse(
                            success=True,
                            data={"status": "mention_processed"},
                            message="App mention processed"
                        )
                
                return AgentResponse(
                    success=True,
                    data={"status": "event_processed"},
                    message="Event callback processed"
                )
                
            elif event_type in ['block_actions', 'view_submission']:
                # Handle interactive components
                interaction_result = await self.tools["process_interaction_event"](event_data)
                
                if interaction_result["type"] == "button_click":
                    return await self._handle_button_click(interaction_result)
                elif interaction_result["type"] == "modal_submission":
                    return await self._handle_modal_submission(interaction_result)
                else:
                    return AgentResponse(
                        success=True,
                        data={"response_type": "ephemeral", "text": "Interacción no reconocida"},
                        message="Unknown interaction processed"
                    )
                    
            else:
                logger.warning(f"Unhandled Slack event type: {event_type}")
                return AgentResponse(
                    success=True,
                    data={"status": "ignored"},
                    message=f"Event type {event_type} ignored"
                )
                
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Slack event processing failed"
            )
    
    async def _handle_button_click(self, interaction_data: Dict[str, Any]) -> AgentResponse:
        """Handle button click interactions via Block Kit agent."""
        try:
            block_kit_agent = await self.get_block_kit_agent()
            
            # Use Block Kit agent to handle the interaction
            agent_response = await block_kit_agent.handle_slack_interaction(
                action_id=interaction_data["action_id"],
                value=interaction_data["value"],
                user_id=interaction_data["user_id"]
            )
            
            return AgentResponse(
                success=agent_response.success,
                data=agent_response.data,
                error=agent_response.error,
                message="Button click processed via Block Kit agent"
            )
            
        except Exception as e:
            logger.error(f"Error handling button click: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Button click processing failed"
            )
    
    async def _handle_modal_submission(self, interaction_data: Dict[str, Any]) -> AgentResponse:
        """Handle modal submission interactions."""
        try:
            callback_id = interaction_data["callback_id"]
            state_values = interaction_data["state_values"]
            user_id = interaction_data["user_id"]
            
            # Log medical action
            await self.tools["log_medical_action"](
                action="modal_submission",
                patient_id=callback_id.replace("case_resolution_", ""),
                details={"user_id": user_id, "callback_id": callback_id}
            )
            
            if callback_id.startswith('case_resolution_'):
                case_id = callback_id.replace('case_resolution_', '')
                
                # Extract form values
                description = self._extract_input_value(state_values, 'resolution_description', 'description_input')
                time_selection = self._extract_select_value(state_values, 'resolution_time', 'time_select')
                followup_options = self._extract_checkbox_values(state_values, 'followup_required', 'followup_checkboxes')
                
                # Process case resolution
                await self._process_case_resolution(case_id, description, time_selection, followup_options)
                
                return AgentResponse(
                    success=True,
                    data={
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
                    },
                    message="Case resolution modal processed successfully"
                )
            
            return AgentResponse(
                success=True,
                data={"response_action": "clear"},
                message="Modal submission processed"
            )
            
        except Exception as e:
            logger.error(f"Error handling modal submission: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Modal submission processing failed"
            )
    
    async def _send_help_response(self, channel: str) -> AgentResponse:
        """Send help message via Block Kit agent."""
        try:
            from ..mcp.gateway import create_mcp_gateway
            
            help_blocks = [
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
            
            # Send via MCP gateway (maintaining existing integration)
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                await gateway.send_slack_block_kit(channel, help_blocks, "Ayuda del Sistema Vigía")
            
            return AgentResponse(
                success=True,
                data={"status": "help_sent"},
                message="Help message sent successfully"
            )
            
        except Exception as e:
            logger.error(f"Error sending help response: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Help response failed"
            )
    
    async def _send_test_alert(self, channel: str) -> AgentResponse:
        """Send test LPP alert via Block Kit agent."""
        try:
            block_kit_agent = await self.get_block_kit_agent()
            
            # Generate test LPP alert
            test_case_data = {
                "interface_type": "lpp_alert",
                "case_id": "TEST_ADK_001",
                "patient_code": "PAT_TEST_001",
                "lpp_grade": 2,
                "confidence": 0.85,
                "location": "sacrum",
                "service": "UCI",
                "bed": "TEST_201A"
            }
            
            # Process via Block Kit agent
            response = await block_kit_agent.process_medical_case(
                case_id="TEST_ADK_001",
                patient_data=test_case_data,
                context=None
            )
            
            if response.success:
                # Send via MCP gateway
                from ..mcp.gateway import create_mcp_gateway
                async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                    await gateway.send_slack_block_kit(
                        channel, 
                        response.data["blocks"], 
                        "Test LPP Alert - ADK Generated"
                    )
            
            return AgentResponse(
                success=True,
                data={"status": "test_alert_sent"},
                message="Test alert sent successfully via ADK agent"
            )
            
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Test alert failed"
            )
    
    async def _send_test_history(self, channel: str) -> AgentResponse:
        """Send test patient history via Block Kit agent."""
        try:
            block_kit_agent = await self.get_block_kit_agent()
            
            # Generate test patient history
            test_patient = {
                'interface_type': 'patient_history',
                'id': 'TEST_ADK_123',
                'name': 'Test Patient ADK',
                'age': 75,
                'service': 'UCI',
                'bed': 'TEST-ADK-001',
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
            
            # Process via Block Kit agent
            response = await block_kit_agent.process_medical_case(
                case_id="TEST_HISTORY_ADK_001",
                patient_data=test_patient,
                context=None
            )
            
            if response.success:
                # Send via MCP gateway
                from ..mcp.gateway import create_mcp_gateway
                async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                    await gateway.send_slack_block_kit(
                        channel, 
                        response.data["blocks"], 
                        "Test Patient History - ADK Generated"
                    )
            
            return AgentResponse(
                success=True,
                data={"status": "test_history_sent"},
                message="Test patient history sent successfully via ADK agent"
            )
            
        except Exception as e:
            logger.error(f"Error sending test history: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Test history failed"
            )
    
    def _extract_input_value(self, state_values: Dict, block_id: str, action_id: str) -> str:
        """Extract text input value from modal state."""
        return state_values.get(block_id, {}).get(action_id, {}).get('value', '')
    
    def _extract_select_value(self, state_values: Dict, block_id: str, action_id: str) -> str:
        """Extract select value from modal state."""
        return state_values.get(block_id, {}).get(action_id, {}).get('selected_option', {}).get('value', '')
    
    def _extract_checkbox_values(self, state_values: Dict, block_id: str, action_id: str) -> list:
        """Extract checkbox values from modal state."""
        return [opt.get('value') for opt in state_values.get(block_id, {}).get(action_id, {}).get('selected_options', [])]
    
    async def _process_case_resolution(self, case_id: str, description: str, 
                                     time_selection: str, followup_options: list):
        """Process case resolution in medical system."""
        try:
            # Log the resolution
            resolution_data = {
                'case_id': case_id,
                'description': description,
                'resolution_time': time_selection,
                'followup_actions': followup_options,
                'resolved_at': datetime.now().isoformat(),
                'resolved_via': 'slack_adk_agent'
            }
            
            logger.info(f"Case resolution processed via ADK: {resolution_data}")
            
            # Log medical action for audit
            await self.tools["log_medical_action"](
                action="case_resolution",
                patient_id=case_id,
                details=resolution_data
            )
            
        except Exception as e:
            logger.error(f"Error processing case resolution: {e}")
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> AgentResponse:
        """Process medical case for event handling.
        
        Args:
            case_id: Unique case identifier
            patient_data: Patient medical data
            context: Agent execution context
            
        Returns:
            AgentResponse with event processing result
        """
        
        try:
            # Route to Block Kit agent for UI generation
            block_kit_agent = await self.get_block_kit_agent()
            
            response = await block_kit_agent.process_medical_case(
                case_id=case_id,
                patient_data=patient_data,
                context=context
            )
            
            return AgentResponse(
                success=response.success,
                data=response.data,
                error=response.error,
                message="Medical case processed via event handler and Block Kit agent"
            )
            
        except Exception as e:
            logger.error(f"Error processing medical case via event handler: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                message="Medical case processing failed in event handler"
            )


# Factory function for ADK agent creation
def create_slack_event_handler_agent() -> SlackEventHandlerAgent:
    """Create and initialize Slack Event Handler ADK Agent.
    
    Returns:
        Initialized SlackEventHandlerAgent instance
    """
    return SlackEventHandlerAgent()
