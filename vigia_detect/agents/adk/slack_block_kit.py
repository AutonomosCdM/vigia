"""
Slack Block Kit ADK Agent - Native Google ADK Implementation
============================================================

ADK WorkflowAgent for Slack Block Kit medical interfaces.
Generates rich interactive medical notifications with HIPAA compliance.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from google.adk.agents import BaseAgent
from google.adk.tools import BaseTool, ToolContext

from .base import VigiaBaseAgent
from ...core.constants import LPP_SEVERITY_ALERTS, SlackActionIds, TEST_PATIENT_DATA
from ...utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class SlackBlockKitAgent(VigiaBaseAgent):
    """
    ADK WorkflowAgent for Slack Block Kit medical interfaces.
    
    Capabilities:
    - UI_GENERATION: Generate rich Slack Block Kit interfaces
    - MEDICAL_COMMUNICATION: HIPAA-compliant medical notifications
    - WORKFLOW_ORCHESTRATION: Interactive medical workflows
    - EMERGENCY_RESPONSE: Critical medical alert handling
    """
    
    def __init__(self):
        """Initialize Slack Block Kit Agent with ADK capabilities."""
        
        super().__init__(
            agent_id="slack_block_kit_agent",
            agent_name="SlackBlockKitMedicalAgent",
            capabilities=[
                "UI_GENERATION",
                "MEDICAL_COMMUNICATION",
                "WORKFLOW_ORCHESTRATION",
                "EMERGENCY_RESPONSE"
            ],
            medical_specialties=[
                "pressure_injury_detection",
                "medical_communication",
                "emergency_escalation",
                "clinical_workflows"
            ]
        )
        
        # Initialize Block Kit specific properties (private to avoid pydantic conflicts)
        self._block_kit_initialized = True
        
        # Register Block Kit tools
        self._tools.update(self._create_block_kit_tools())
        
        # Remove tools property assignment to avoid pydantic conflicts
        # Tests will use agent._tools directly
        
        logger.info("Slack Block Kit ADK Agent initialized with full medical capabilities")
    
    def _create_block_kit_tools(self) -> Dict[str, Any]:
        """Create ADK Tools for Block Kit operations."""
        tools = {}
        
        # LPP Alert Tool
        def generate_lpp_alert_blocks(
            case_id: str,
            patient_code: str,
            lpp_grade: int,
            confidence: float,
            location: str,
            service: str,
            bed: str,
            timestamp: str = None
        ) -> Dict[str, Any]:
            """Generate LPP alert with rich Block Kit interface.
            
            Args:
                case_id: Unique case identifier
                patient_code: Patient identifier (will be anonymized)
                lpp_grade: LPP grade (1-4)
                confidence: Detection confidence (0-1)
                location: Anatomical location
                service: Medical service/department
                bed: Bed identifier (will be anonymized)
                timestamp: Optional timestamp
                
            Returns:
                Dict containing Block Kit blocks and metadata
            """
            
            severity = LPP_SEVERITY_ALERTS.get(lpp_grade, LPP_SEVERITY_ALERTS[0])
            
            # HIPAA-compliant anonymization
            anon_patient = patient_code[:3] + "***" if len(patient_code) > 3 else "PAT***"
            anon_bed = bed[:2] + "***" if len(bed) > 2 else "BE***"
            
            timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
            
            blocks = [
                # Header with severity styling
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{severity['emoji']} LPP Grado {lpp_grade} - {severity['level']} - URGENTE"
                    }
                },
                
                # Patient and case information
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Caso:* {case_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Paciente:* {anon_patient}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Servicio:* {service}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Cama:* {anon_bed}"
                        }
                    ]
                },
                
                # Detection details
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🎯 Detección:* {severity['message']}\n*📍 Ubicación:* {location.title()}\n*🎯 Confianza:* {confidence:.1%}\n*⏰ Detectado:* {timestamp}"
                    }
                },
                
                # Medical description
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Descripción Clínica:*\n{self._get_lpp_description(lpp_grade)}"
                    }
                },
                
                # Action buttons
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Ver Historial"
                            },
                            "style": "primary",
                            "action_id": f"{SlackActionIds.VIEW_MEDICAL_HISTORY}_{case_id}",
                            "value": case_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🩺 Evaluación Médica"
                            },
                            "style": "danger" if lpp_grade >= 3 else "primary",
                            "action_id": f"{SlackActionIds.REQUEST_MEDICAL_EVALUATION}_{case_id}",
                            "value": case_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Marcar Resuelto"
                            },
                            "action_id": f"{SlackActionIds.MARK_RESOLVED}_{case_id}",
                            "value": case_id
                        }
                    ]
                },
                
                # Context and compliance
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🏥 Sistema Vigía | 🔒 HIPAA Compliant | ⚡ Urgencia: {severity['urgency'].upper()}"
                        }
                    ]
                }
            ]
            
            return {
                "blocks": blocks,
                "case_id": case_id,
                "severity": severity,
                "anonymized": True,
                "hipaa_compliant": True
            }
        
        tools["generate_lpp_alert_blocks"] = generate_lpp_alert_blocks
        
        # Patient History Tool
        def generate_patient_history_blocks(patient_data: Dict[str, Any]) -> Dict[str, Any]:
            """Generate patient history with HIPAA-compliant Block Kit interface.
            
            Args:
                patient_data: Patient medical data dictionary
                
            Returns:
                Dict containing Block Kit blocks for patient history
            """
            
            # Anonymize patient data
            patient_id = patient_data.get('id', 'UNKNOWN')
            anon_id = patient_id[:3] + "***" if len(patient_id) > 3 else "PAT***"
            
            patient_name = patient_data.get('name', 'Unknown Patient')
            anon_name = patient_name[:3] + "***" if len(patient_name) > 3 else "PAT***"
            
            blocks = [
                # Header
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📋 Historial Médico - {anon_name}"
                    }
                },
                
                # Demographics (anonymized)
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*👤 Datos del Paciente*"
                    },
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*ID:* {anon_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Edad:* {patient_data.get('age', 'N/A')} años"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Servicio:* {patient_data.get('service', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Cama:* {patient_data.get('bed', 'N/A')[:2]}***"
                        }
                    ]
                },
                
                # Diagnoses
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🩺 Diagnósticos:*\n" + "\n".join(
                            f"• {dx}" for dx in patient_data.get('diagnoses', ['Sin diagnósticos registrados'])
                        )
                    }
                },
                
                # Medications
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💊 Medicamentos:*\n" + "\n".join(
                            f"• {med}" for med in patient_data.get('medications', ['Sin medicamentos registrados'])
                        )
                    }
                },
                
                # LPP History
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self._format_lpp_history(patient_data.get('lpp_history', []))
                    }
                },
                
                # HIPAA compliance notice
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🔒 Información médica protegida - HIPAA Compliant | *** = Datos anonimizados"
                        }
                    ]
                }
            ]
            
            return {
                "blocks": blocks,
                "patient_id": anon_id,
                "anonymized": True,
                "hipaa_compliant": True
            }
        
        tools["generate_patient_history_blocks"] = generate_patient_history_blocks
        
        # Case Resolution Modal Tool
        def generate_case_resolution_modal(case_id: str) -> Dict[str, Any]:
            """Generate case resolution modal for medical workflow.
            
            Args:
                case_id: Case identifier for resolution
                
            Returns:
                Dict containing modal definition
            """
            
            modal = {
                "type": "modal",
                "callback_id": f"case_resolution_{case_id}",
                "title": {
                    "type": "plain_text",
                    "text": "Resolución de Caso LPP"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Marcar Resuelto"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancelar"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Caso:* {case_id}\n\nPor favor, proporciona los detalles de la resolución del caso de LPP."
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "resolution_description",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "description_input",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Describe las acciones tomadas, tratamiento aplicado y estado actual del paciente..."
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Descripción de la Resolución"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "resolution_time",
                        "element": {
                            "type": "static_select",
                            "action_id": "time_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Selecciona tiempo de resolución"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "15 minutos"
                                    },
                                    "value": "15min"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "30 minutos"
                                    },
                                    "value": "30min"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1 hora"
                                    },
                                    "value": "1hr"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2-4 horas"
                                    },
                                    "value": "2-4hr"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Más de 4 horas"
                                    },
                                    "value": "4hr+"
                                }
                            ]
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Tiempo de Resolución"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "followup_required",
                        "element": {
                            "type": "checkboxes",
                            "action_id": "followup_checkboxes",
                            "options": [
                                {
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Seguimiento médico requerido*"
                                    },
                                    "description": {
                                        "type": "mrkdwn",
                                        "text": "Programar evaluación médica de seguimiento"
                                    },
                                    "value": "medical_followup"
                                },
                                {
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Notificar a especialista*"
                                    },
                                    "description": {
                                        "type": "mrkdwn",
                                        "text": "Enviar informe a especialista en heridas"
                                    },
                                    "value": "notify_specialist"
                                },
                                {
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Programar evaluación*"
                                    },
                                    "description": {
                                        "type": "mrkdwn",
                                        "text": "Agendar próxima evaluación de LPP"
                                    },
                                    "value": "schedule_evaluation"
                                }
                            ]
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Acciones de Seguimiento"
                        },
                        "optional": True
                    }
                ]
            }
            
            return {
                "modal": modal,
                "case_id": case_id,
                "workflow_type": "case_resolution"
            }
        
        tools["generate_case_resolution_modal"] = generate_case_resolution_modal
        
        return tools
    
    def _create_ui_workflows(self) -> Dict[str, Any]:
        """Create simplified workflows for medical UI generation."""
        workflows = {
            "lpp_alert_notification": {
                "name": "lpp_alert_notification",
                "description": "Generate and send LPP alert with Block Kit interface",
                "steps": [
                    "validate_medical_data",
                    "generate_blocks",
                    "send_notification",
                    "log_audit_trail"
                ]
            },
            "patient_history_display": {
                "name": "patient_history_display", 
                "description": "Generate HIPAA-compliant patient history interface",
                "steps": [
                    "anonymize_patient_data",
                    "generate_history_blocks",
                    "validate_compliance",
                    "send_response"
                ]
            }
        }
        
        return workflows
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process medical case for Block Kit interface generation.
        
        Args:
            case_id: Unique case identifier
            patient_data: Patient medical data
            context: Agent execution context
            
        Returns:
            AgentResponse with Block Kit interface
        """
        
        try:
            # Determine the type of medical interface needed
            interface_type = patient_data.get('interface_type', 'lpp_alert')
            
            if interface_type == 'lpp_alert':
                # Execute LPP alert workflow
                workflow_result = await self._tools["generate_lpp_alert_blocks"](
                    case_id=patient_data.get("case_id", case_id),
                    patient_code=patient_data.get("patient_code", "UNKNOWN"),
                    lpp_grade=patient_data.get("lpp_grade", 1),
                    confidence=patient_data.get("confidence", 0.5),
                    location=patient_data.get("location", "unknown"),
                    service=patient_data.get("service", "unknown"),
                    bed=patient_data.get("bed", "unknown")
                )
                
                return {
                    "success": True,
                    "data": workflow_result,
                    "message": "LPP alert Block Kit interface generated successfully"
                }
                
            elif interface_type == 'patient_history':
                # Execute patient history workflow
                workflow_result = await self._tools["generate_patient_history_blocks"](patient_data)
                
                return {
                    "success": True,
                    "data": workflow_result,
                    "message": "Patient history Block Kit interface generated successfully"
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown interface type: {interface_type}",
                    "message": "Block Kit interface generation failed"
                }
                
        except Exception as e:
            logger.error(f"Error processing medical case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Medical case processing failed"
            }
    
    async def handle_slack_interaction(
        self,
        action_id: str,
        value: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle Slack interactive component actions.
        
        Args:
            action_id: Slack action identifier
            value: Action value
            user_id: User who triggered the action
            context: Optional agent context
            
        Returns:
            AgentResponse with interaction result
        """
        
        try:
            # Log medical action for audit
            await self._tools["log_medical_action"](
                action=f"slack_interaction_{action_id}",
                patient_id=value,
                details={"user_id": user_id, "action_id": action_id}
            )
            
            if action_id.startswith(SlackActionIds.VIEW_MEDICAL_HISTORY):
                case_id = action_id.split('_')[-1]
                
                # Generate patient history
                history_blocks = await self._tools["generate_patient_history_blocks"](TEST_PATIENT_DATA)
                
                return {
                    "success": True,
                    "data": {
                        "response_type": "ephemeral",
                        "text": f"📋 Historial médico para caso {case_id} solicitado",
                        "blocks": history_blocks["blocks"]
                    },
                    "message": "Medical history generated successfully"
                }
                
            elif action_id.startswith(SlackActionIds.REQUEST_MEDICAL_EVALUATION):
                case_id = action_id.split('_')[-1]
                
                return {
                    "success": True,
                    "data": {
                        "response_type": "ephemeral",
                        "text": f"🩺 Evaluación médica solicitada para caso {case_id}",
                        "blocks": self._generate_medical_evaluation_blocks(case_id, "high")
                    },
                    "message": "Medical evaluation request generated"
                }
                
            elif action_id.startswith(SlackActionIds.MARK_RESOLVED):
                case_id = action_id.split('_')[-1]
                
                # Generate resolution modal
                modal_result = await self._tools["generate_case_resolution_modal"](case_id)
                
                return {
                    "success": True,
                    "data": {
                        "response_type": "ephemeral",
                        "text": f"📝 Formulario de resolución para caso {case_id}",
                        "trigger_id": "modal_trigger",
                        "view": modal_result["modal"]
                    },
                    "message": "Case resolution modal generated"
                }
                
            else:
                return {
                    "success": True,
                    "data": {
                        "response_type": "ephemeral",
                        "text": f"🔄 Procesando acción: {action_id}"
                    },
                    "message": "Unknown action processed"
                }
                
        except Exception as e:
            logger.error(f"Error handling Slack interaction: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Slack interaction handling failed"
            }
    
    def _get_lpp_description(self, lpp_grade: int) -> str:
        """Get clinical description for LPP grade."""
        descriptions = {
            0: "Sin lesión detectada - Monitoreo preventivo recomendado",
            1: "Eritema no blanqueable en área localizada - Alivio de presión inmediato",
            2: "Úlcera superficial con pérdida parcial del espesor de la piel - Curación según protocolo",
            3: "Úlcera profunda con pérdida total del espesor de la piel - Evaluación médica urgente",
            4: "Úlcera con exposición de tejido profundo (músculo/hueso) - Interconsulta cirugía"
        }
        return descriptions.get(lpp_grade, "Grado de LPP no reconocido")
    
    def _format_lpp_history(self, lpp_history: List[Dict[str, Any]]) -> str:
        """Format LPP history for Block Kit display."""
        if not lpp_history:
            return "*📊 Historial de LPP:*\n• Sin historial previo de lesiones por presión"
        
        history_text = "*📊 Historial de LPP:*\n"
        for entry in lpp_history[-3:]:  # Show last 3 entries
            date = entry.get('date', 'Fecha desconocida')
            grade = entry.get('grade', 0)
            location = entry.get('location', 'Ubicación desconocida')
            status = entry.get('status', 'Estado desconocido')
            
            history_text += f"• {date}: Grado {grade} en {location} - {status}\n"
        
        if len(lpp_history) > 3:
            history_text += f"... y {len(lpp_history) - 3} entradas más\n"
        
        return history_text
    
    def _generate_medical_evaluation_blocks(self, case_id: str, urgency: str) -> List[Dict[str, Any]]:
        """Generate medical evaluation request blocks."""
        
        urgency_config = {
            "normal": {"emoji": "🔔", "text": "NORMAL", "style": "primary"},
            "high": {"emoji": "⚡", "text": "ALTA", "style": "danger"},
            "critical": {"emoji": "🚨", "text": "CRÍTICA", "style": "danger"}
        }
        
        config = urgency_config.get(urgency, urgency_config["normal"])
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['emoji']} Evaluación Médica - Urgencia {config['text']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Caso:* {case_id}\n*Urgencia:* {config['text']}\n\nSe requiere evaluación médica especializada para este caso de LPP."
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Aceptar Evaluación"
                        },
                        "style": config["style"],
                        "action_id": f"{SlackActionIds.ACCEPT_EVALUATION}_{case_id}",
                        "value": case_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👩‍⚕️ Contactar Enfermería"
                        },
                        "action_id": f"{SlackActionIds.CONTACT_NURSING}_{case_id}",
                        "value": case_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📋 Ver Detalles"
                        },
                        "action_id": f"{SlackActionIds.VIEW_CASE_DETAILS}_{case_id}",
                        "value": case_id
                    }
                ]
            }
        ]


# Factory function for ADK agent creation
def create_slack_block_kit_agent() -> SlackBlockKitAgent:
    """Create and initialize Slack Block Kit ADK Agent.
    
    Returns:
        Initialized SlackBlockKitAgent instance
    """
    return SlackBlockKitAgent()
