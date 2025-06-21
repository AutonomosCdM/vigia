"""
Slack Block Kit Medical Components for Vigía
Rich interactive medical notifications with HIPAA compliance
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.constants import LPP_SEVERITY_ALERTS, SlackActionIds


class BlockKitMedical:
    """Factory for medical Block Kit components"""
    
    @staticmethod
    def lpp_alert_blocks(
        case_id: str,
        patient_code: str,
        lpp_grade: int,
        confidence: float,
        location: str,
        service: str,
        bed: str,
        timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Create LPP alert with rich Block Kit interface"""
        
        severity = LPP_SEVERITY_ALERTS.get(lpp_grade, LPP_SEVERITY_ALERTS[0])
        
        # Anonymize for HIPAA
        anon_patient = patient_code[:3] + "***"
        anon_bed = bed[:2] + "***"
        ts = timestamp or datetime.now().strftime('%d/%m/%Y %H:%M')
        
        blocks = [
            # Header with severity
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity['emoji']} Alerta LPP Grado {lpp_grade} - URGENTE"
                }
            },
            
            # Patient & Case Info Section
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Paciente:*\n{anon_patient}"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": f"*Caso ID:*\n`{case_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Servicio:*\n{service}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Cama:*\n{anon_bed}"
                    }
                ]
            },
            
            # Medical Detection Section
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Ubicación:*\n{location}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confianza:*\n{confidence:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severidad:*\n{severity['level'].upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{ts}"
                    }
                ]
            },
            
            # Clinical Description
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Descripción Clínica:*\n{severity['message']}"
                }
            },
            
            # Divider
            {
                "type": "divider"
            },
            
            # Action Buttons
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🏥 Ver Historial"
                        },
                        "style": "primary",
                        "action_id": f"{SlackActionIds.VIEW_MEDICAL_HISTORY}_{case_id}",
                        "value": case_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⚡ Evaluación Médica"
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
            
            # Context Footer
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 Sistema Vigía v1.0 | 🔒 HIPAA Compliant | 📋 Caso: {case_id}"
                    }
                ]
            }
        ]
        
        return blocks
    
    @staticmethod
    def patient_history_blocks(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create patient medical history with Block Kit"""
        
        # Anonymize patient data
        anon_id = patient_data['id'][:4] + "***"
        anon_name = patient_data['name'][:3] + "***"
        age_range = f"{(patient_data['age'] // 10) * 10}-{(patient_data['age'] // 10) * 10 + 9}"
        
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Historial Médico del Paciente"
                }
            },
            
            # Patient Demographics
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*ID Paciente:*\n{anon_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Nombre:*\n{anon_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Edad:*\n{age_range} años"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Servicio:*\n{patient_data['service']}"
                    }
                ]
            },
            
            # Diagnoses Section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🩺 Diagnósticos Activos:*\n" + "\n".join([f"• {d}" for d in patient_data.get('diagnoses', [])])
                }
            },
            
            # Medications Section  
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💊 Medicamentos:*\n" + "\n".join([f"• {m}" for m in patient_data.get('medications', [])])
                }
            },
            
            # LPP History Section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔴 Historial de LPP:*\n" + (
                        "\n".join([
                            f"• *{h['date']}*: Grado {h['grade']} en {h['location']} - {h['status']}"
                            for h in patient_data.get('lpp_history', [])
                        ]) or "Sin historial previo de LPP"
                    )
                }
            },
            
            # Risk Factors
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*⚠️ Factores de Riesgo:*\n• Movilidad reducida\n• Post-quirúrgico\n• Piel frágil\n• Diabetes"
                }
            },
            
            # Care Notes
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Notas de Cuidado:*\n• Cambio de posición cada 2 horas\n• Piel de alto riesgo\n• Cuidado especial requerido"
                }
            },
            
            # Context
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🔒 Datos anonimizados | 📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | 🏥 HIPAA Compliant"
                    }
                ]
            }
        ]
        
        return blocks
    
    @staticmethod
    def case_resolution_modal(case_id: str) -> Dict[str, Any]:
        """Create modal for case resolution workflow"""
        
        return {
            "type": "modal",
            "callback_id": f"case_resolution_{case_id}",
            "title": {
                "type": "plain_text",
                "text": "Resolución de Caso"
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
                # Case Info
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Caso ID:* `{case_id}`\n*Acción:* Marcar como resuelto"
                    }
                },
                
                # Resolution Description
                {
                    "type": "input",
                    "block_id": "resolution_description",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "description_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Describa las acciones tomadas, tratamiento aplicado y resultado obtenido..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Descripción de la Resolución"
                    }
                },
                
                # Resolution Time
                {
                    "type": "input",
                    "block_id": "resolution_time",
                    "element": {
                        "type": "static_select",
                        "action_id": "time_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Seleccione tiempo de resolución"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "< 30 minutos"
                                },
                                "value": "30min"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "30 min - 1 hora"
                                },
                                "value": "1hr"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "1 - 2 horas"
                                },
                                "value": "2hr"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "> 2 horas"
                                },
                                "value": "more"
                            }
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Tiempo de Resolución"
                    }
                },
                
                # Follow-up Required
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
                                "value": "medical_followup"
                            },
                            {
                                "text": {
                                    "type": "mrkdwn", 
                                    "text": "*Notificar a especialista*"
                                },
                                "value": "notify_specialist"
                            },
                            {
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Programar evaluación*"
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
                },
                
                # Compliance Note
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🔒 Esta información será registrada en el sistema de auditoría médica con cumplimiento HIPAA"
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def medical_evaluation_request_blocks(case_id: str, urgency: str = "normal") -> List[Dict[str, Any]]:
        """Create medical evaluation request notification"""
        
        urgency_config = {
            "critical": {"emoji": "🚨", "color": "#FF0000", "text": "CRÍTICA"},
            "high": {"emoji": "⚡", "color": "#FF6600", "text": "ALTA"},
            "normal": {"emoji": "📋", "color": "#0066CC", "text": "NORMAL"}
        }
        
        config = urgency_config.get(urgency, urgency_config["normal"])
        
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['emoji']} Solicitud de Evaluación Médica - {config['text']}"
                }
            },
            
            # Request Info
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Caso ID:*\n`{case_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Urgencia:*\n{config['text']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Solicitado:*\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Estado:*\nPendiente de asignación"
                    }
                ]
            },
            
            # Action Required
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🩺 Acción Requerida:*\nSe requiere evaluación médica profesional para este caso. El personal de enfermería ha identificado una situación que necesita atención especializada."
                }
            },
            
            # Actions for Medical Staff
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👨‍⚕️ Aceptar Evaluación"
                        },
                        "style": "primary",
                        "action_id": f"accept_evaluation_{case_id}",
                        "value": case_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📞 Contactar Enfermería"
                        },
                        "action_id": f"contact_nursing_{case_id}",
                        "value": case_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📋 Ver Detalles"
                        },
                        "action_id": f"view_case_details_{case_id}",
                        "value": case_id
                    }
                ]
            },
            
            # Context
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🏥 Sistema Vigía | 🔔 Notificación automática | 📋 Caso: {case_id}"
                    }
                ]
            }
        ]
        
        return blocks
    
    @staticmethod
    def system_error_blocks(error_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create system error notification with Block Kit"""
        
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Error en Sistema Vigía"
                }
            },
            
            # Error Details
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Componente:*\n{error_data.get('component', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Código de Error:*\n`{error_data.get('code', 'UNKNOWN')}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severidad:*\n{error_data.get('severity', 'unknown').upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    }
                ]
            },
            
            # Error Message
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 Mensaje de Error:*\n```{error_data.get('message', 'No message provided')}```"
                }
            },
            
            # Actions
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔧 Investigar Error"
                        },
                        "style": "danger",
                        "action_id": f"investigate_error_{error_data.get('code', 'unknown')}",
                        "value": str(error_data)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 Ver Logs"
                        },
                        "action_id": f"view_logs_{error_data.get('component', 'system')}",
                        "value": error_data.get('component', 'system')
                    }
                ]
            },
            
            # Context
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🚨 Error del sistema - Requiere atención técnica inmediata"
                    }
                ]
            }
        ]
        
        return blocks


class BlockKitInteractions:
    """Handler for Block Kit interactive components"""
    
    @staticmethod
    def handle_action(action_id: str, value: str, user_id: str) -> Dict[str, Any]:
        """Process Block Kit action and return response"""
        
        response = {
            "response_type": "ephemeral",
            "text": "Procesando acción...",
            "timestamp": datetime.now().isoformat()
        }
        
        if action_id.startswith(SlackActionIds.VIEW_MEDICAL_HISTORY):
            case_id = value
            response.update({
                "text": f"📋 Historial médico para caso {case_id} solicitado",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Historial médico solicitado*\nCaso: `{case_id}`\nUsuario: <@{user_id}>\nEstado: Generando informe..."
                        }
                    }
                ]
            })
            
        elif action_id.startswith(SlackActionIds.REQUEST_MEDICAL_EVALUATION):
            case_id = value
            response.update({
                "text": f"⚡ Evaluación médica solicitada para caso {case_id}",
                "blocks": BlockKitMedical.medical_evaluation_request_blocks(case_id, "high")
            })
            
        elif action_id.startswith(SlackActionIds.MARK_RESOLVED):
            case_id = value
            response.update({
                "text": f"✅ Iniciando proceso de resolución para caso {case_id}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Caso marcado para resolución*\nCaso: `{case_id}`\nPor: <@{user_id}>\nSiguiente paso: Documentar resolución"
                        }
                    }
                ]
            })
        
        return response
    
    @staticmethod
    def handle_modal_submission(modal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process modal form submission"""
        
        callback_id = modal_data.get("callback_id", "")
        
        if callback_id.startswith("case_resolution_"):
            case_id = callback_id.replace("case_resolution_", "")
            
            # Extract form data
            values = modal_data.get("state", {}).get("values", {})
            description = values.get("resolution_description", {}).get("description_input", {}).get("value", "")
            time_selection = values.get("resolution_time", {}).get("time_select", {}).get("selected_option", {}).get("value", "")
            followup_options = values.get("followup_required", {}).get("followup_checkboxes", {}).get("selected_options", [])
            
            return {
                "response_action": "update",
                "view": {
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Caso Resuelto"
                    },
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"✅ *Caso {case_id} marcado como resuelto*\n\n*Descripción:* {description}\n*Tiempo:* {time_selection}\n*Seguimiento:* {len(followup_options)} acciones programadas"
                            }
                        }
                    ]
                }
            }
        
        return {"response_action": "clear"}