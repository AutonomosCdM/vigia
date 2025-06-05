"""
Slack Orchestrator - Sistema de notificaciones especializadas para equipos médicos.

Este módulo implementa el orquestador de notificaciones Slack que maneja:
- Enrutamiento de alertas por urgencia y tipo
- Canales especializados por equipo médico
- Escalamiento automático de notificaciones críticas
- Formateo de mensajes médicos con contexto clínico
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

from vigia_detect.utils.audit_service import AuditService, AuditEvent, AuditLevel
from vigia_detect.messaging.slack_notifier_refactored import SlackNotifier


class NotificationType(Enum):
    """Tipos de notificaciones médicas."""
    EMERGENCY_ALERT = "emergency_alert"
    CLINICAL_RESULT = "clinical_result"
    HUMAN_REVIEW_REQUEST = "human_review_request"
    SYSTEM_STATUS = "system_status"
    AUDIT_ALERT = "audit_alert"
    PROTOCOL_TRIGGERED = "protocol_triggered"


class NotificationPriority(Enum):
    """Prioridades de notificación."""
    CRITICAL = 1    # Emergencias médicas - inmediato
    HIGH = 2        # Resultados urgentes - < 30 min
    MEDIUM = 3      # Revisión humana - < 2 horas
    LOW = 4         # Información general - < 24 horas


class SlackChannel(Enum):
    """Canales Slack especializados."""
    EMERGENCY_ROOM = "emergencias"
    CLINICAL_TEAM = "equipo-clinico"
    LPP_SPECIALISTS = "especialistas-lpp"
    NURSING_STAFF = "personal-enfermeria"
    SYSTEM_ALERTS = "alertas-sistema"
    AUDIT_LOG = "auditoria-medica"


@dataclass
class NotificationPayload:
    """Payload estandarizado para notificaciones."""
    notification_id: str
    session_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    target_channels: List[SlackChannel]
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str
    escalation_rules: Optional[Dict[str, Any]] = None


@dataclass
class SlackMessage:
    """Mensaje Slack formateado."""
    channel: str
    text: str
    blocks: List[Dict[str, Any]]
    attachments: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None


class SlackOrchestrator:
    """
    Orquestrador de notificaciones Slack especializadas para equipos médicos.
    
    Maneja el enrutamiento inteligente de notificaciones basado en:
    - Tipo de notificación médica
    - Prioridad clínica
    - Disponibilidad de equipos
    - Reglas de escalamiento
    """
    
    def __init__(self, slack_notifier: Optional[SlackNotifier] = None):
        self.slack_notifier = slack_notifier or SlackNotifier()
        self.audit_service = AuditService()
        self.logger = logging.getLogger(__name__)
        
        # Configuración de canales por tipo de notificación
        self.channel_routing = self._initialize_channel_routing()
        
        # Configuración de escalamiento automático
        self.escalation_config = self._initialize_escalation_config()
        
        # Tracking de notificaciones activas
        self.active_notifications: Dict[str, NotificationPayload] = {}
        
    def _initialize_channel_routing(self) -> Dict[NotificationType, List[SlackChannel]]:
        """Inicializa el enrutamiento de canales por tipo de notificación."""
        return {
            NotificationType.EMERGENCY_ALERT: [
                SlackChannel.EMERGENCY_ROOM,
                SlackChannel.CLINICAL_TEAM
            ],
            NotificationType.CLINICAL_RESULT: [
                SlackChannel.CLINICAL_TEAM,
                SlackChannel.LPP_SPECIALISTS
            ],
            NotificationType.HUMAN_REVIEW_REQUEST: [
                SlackChannel.CLINICAL_TEAM,
                SlackChannel.NURSING_STAFF
            ],
            NotificationType.SYSTEM_STATUS: [
                SlackChannel.SYSTEM_ALERTS
            ],
            NotificationType.AUDIT_ALERT: [
                SlackChannel.AUDIT_LOG,
                SlackChannel.SYSTEM_ALERTS
            ],
            NotificationType.PROTOCOL_TRIGGERED: [
                SlackChannel.CLINICAL_TEAM,
                SlackChannel.LPP_SPECIALISTS
            ]
        }
    
    def _initialize_escalation_config(self) -> Dict[NotificationPriority, Dict[str, Any]]:
        """Configura reglas de escalamiento por prioridad."""
        return {
            NotificationPriority.CRITICAL: {
                "immediate_notify": True,
                "escalation_time": timedelta(minutes=5),
                "max_escalations": 3,
                "additional_channels": [SlackChannel.EMERGENCY_ROOM]
            },
            NotificationPriority.HIGH: {
                "immediate_notify": True,
                "escalation_time": timedelta(minutes=30),
                "max_escalations": 2,
                "additional_channels": [SlackChannel.CLINICAL_TEAM]
            },
            NotificationPriority.MEDIUM: {
                "immediate_notify": False,
                "escalation_time": timedelta(hours=2),
                "max_escalations": 1,
                "additional_channels": []
            },
            NotificationPriority.LOW: {
                "immediate_notify": False,
                "escalation_time": timedelta(hours=24),
                "max_escalations": 0,
                "additional_channels": []
            }
        }
    
    async def send_notification(self, payload: NotificationPayload) -> Dict[str, Any]:
        """
        Envía notificación a través de Slack con enrutamiento inteligente.
        
        Args:
            payload: Payload de notificación con toda la información médica
            
        Returns:
            Resultado del envío con detalles de entrega
        """
        try:
            # Registrar inicio de notificación
            await self.audit_service.log_event(
                AuditEvent(
                    event_type="slack_notification_start",
                    session_id=payload.session_id,
                    level=AuditLevel.MEDIUM,
                    details={
                        "notification_id": payload.notification_id,
                        "notification_type": payload.notification_type.value,
                        "priority": payload.priority.value,
                        "target_channels": [ch.value for ch in payload.target_channels]
                    }
                )
            )
            
            # Formatear mensaje según tipo de notificación
            slack_message = await self._format_message(payload)
            
            # Determinar canales objetivo
            target_channels = await self._determine_target_channels(payload)
            
            # Enviar a cada canal
            delivery_results = []
            for channel in target_channels:
                try:
                    result = await self._send_to_channel(
                        channel=channel,
                        message=slack_message,
                        payload=payload
                    )
                    delivery_results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error enviando a canal {channel}: {str(e)}")
                    delivery_results.append({
                        "channel": channel,
                        "success": False,
                        "error": str(e)
                    })
            
            # Configurar escalamiento automático si es necesario
            if payload.priority in [NotificationPriority.CRITICAL, NotificationPriority.HIGH]:
                await self._setup_escalation(payload)
            
            # Registrar notificación activa
            self.active_notifications[payload.notification_id] = payload
            
            # Auditar resultado
            await self.audit_service.log_event(
                AuditEvent(
                    event_type="slack_notification_sent",
                    session_id=payload.session_id,
                    level=AuditLevel.LOW,
                    details={
                        "notification_id": payload.notification_id,
                        "channels_sent": len([r for r in delivery_results if r.get("success")]),
                        "total_channels": len(delivery_results),
                        "delivery_results": delivery_results
                    }
                )
            )
            
            return {
                "success": True,
                "notification_id": payload.notification_id,
                "channels_sent": len([r for r in delivery_results if r.get("success")]),
                "delivery_results": delivery_results
            }
            
        except Exception as e:
            self.logger.error(f"Error en orquestador Slack: {str(e)}")
            await self.audit_service.log_event(
                AuditEvent(
                    event_type="slack_notification_error",
                    session_id=payload.session_id,
                    level=AuditLevel.HIGH,
                    details={
                        "notification_id": payload.notification_id,
                        "error": str(e)
                    }
                )
            )
            raise
    
    async def _format_message(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea mensaje según el tipo de notificación médica."""
        formatters = {
            NotificationType.EMERGENCY_ALERT: self._format_emergency_alert,
            NotificationType.CLINICAL_RESULT: self._format_clinical_result,
            NotificationType.HUMAN_REVIEW_REQUEST: self._format_review_request,
            NotificationType.SYSTEM_STATUS: self._format_system_status,
            NotificationType.AUDIT_ALERT: self._format_audit_alert,
            NotificationType.PROTOCOL_TRIGGERED: self._format_protocol_alert
        }
        
        formatter = formatters.get(payload.notification_type)
        if not formatter:
            raise ValueError(f"Tipo de notificación no soportado: {payload.notification_type}")
        
        return await formatter(payload)
    
    async def _format_emergency_alert(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea alerta de emergencia médica."""
        content = payload.content
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":rotating_light: *ALERTA MÉDICA DE EMERGENCIA* :rotating_light:\n\n*Sesión:* `{payload.session_id}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Tipo:* {content.get('emergency_type', 'No especificado')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Criticidad:* {content.get('criticality', 'Alta')}"
                    }
                ]
            }
        ]
        
        if content.get("patient_info"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Información del paciente:*\n{content['patient_info']}"
                }
            })
        
        if content.get("recommended_action"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Acción recomendada:*\n{content['recommended_action']}"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sistema Vigia • {payload.timestamp}"
                }
            ]
        })
        
        return SlackMessage(
            channel="",  # Se asignará dinámicamente
            text=f"ALERTA MÉDICA: {content.get('emergency_type', 'Emergencia detectada')}",
            blocks=blocks
        )
    
    async def _format_clinical_result(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea resultado clínico de LPP."""
        content = payload.content
        
        # Determinar emoji según grado de LPP
        grade_emojis = {
            1: ":yellow_circle:",
            2: ":orange_circle:",
            3: ":red_circle:",
            4: ":black_circle:"
        }
        
        lpp_grade = content.get("lpp_grade", 0)
        emoji = grade_emojis.get(lpp_grade, ":question:")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Resultado de Análisis LPP*\n\n*Sesión:* `{payload.session_id}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Grado LPP:* {lpp_grade}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confianza:* {content.get('confidence', 0):.1%}"
                    }
                ]
            }
        ]
        
        if content.get("clinical_description"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Descripción clínica:*\n{content['clinical_description']}"
                }
            })
        
        if content.get("recommendations"):
            recommendations = "\n".join([f"• {rec}" for rec in content['recommendations']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recomendaciones:*\n{recommendations}"
                }
            })
        
        return SlackMessage(
            channel="",
            text=f"Resultado LPP Grado {lpp_grade}",
            blocks=blocks
        )
    
    async def _format_review_request(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea solicitud de revisión humana."""
        content = payload.content
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":eyes: *Solicitud de Revisión Médica*\n\n*Sesión:* `{payload.session_id}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Prioridad:* {content.get('priority', 'Media')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Especialidad:* {content.get('specialty', 'General')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Motivo:*\n{content.get('reason', 'Revisión médica requerida')}"
                }
            }
        ]
        
        # Agregar botones de acción
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Aceptar Revisión"
                    },
                    "style": "primary",
                    "value": f"accept_{payload.session_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Escalar"
                    },
                    "style": "danger",
                    "value": f"escalate_{payload.session_id}"
                }
            ]
        })
        
        return SlackMessage(
            channel="",
            text=f"Revisión médica requerida - {content.get('specialty', 'General')}",
            blocks=blocks
        )
    
    async def _format_system_status(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea estado del sistema."""
        content = payload.content
        
        status_emoji = {
            "healthy": ":white_check_mark:",
            "warning": ":warning:",
            "error": ":x:",
            "maintenance": ":construction:"
        }.get(content.get("status", "unknown"), ":question:")
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *Estado del Sistema Vigia*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Estado:* {content.get('status', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Componente:* {content.get('component', 'Sistema general')}"
                    }
                ]
            }
        ]
        
        if content.get("message"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Detalles:*\n{content['message']}"
                }
            })
        
        return SlackMessage(
            channel="",
            text=f"Sistema {content.get('status', 'Unknown')} - {content.get('component', 'Vigia')}",
            blocks=blocks
        )
    
    async def _format_audit_alert(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea alerta de auditoría."""
        content = payload.content
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":shield: *Alerta de Auditoría*\n\n*Event ID:* `{content.get('event_id', 'Unknown')}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Nivel:* {content.get('level', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tipo:* {content.get('event_type', 'Unknown')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Descripción:*\n{content.get('description', 'Evento de auditoría detectado')}"
                }
            }
        ]
        
        return SlackMessage(
            channel="",
            text=f"Auditoría: {content.get('event_type', 'Evento detectado')}",
            blocks=blocks
        )
    
    async def _format_protocol_alert(self, payload: NotificationPayload) -> SlackMessage:
        """Formatea alerta de protocolo médico."""
        content = payload.content
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":medical_symbol: *Protocolo Médico Activado*\n\n*Sesión:* `{payload.session_id}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Protocolo:* {content.get('protocol_name', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Trigger:* {content.get('trigger_condition', 'Unknown')}"
                    }
                ]
            }
        ]
        
        if content.get("actions_required"):
            actions = "\n".join([f"• {action}" for action in content['actions_required']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Acciones requeridas:*\n{actions}"
                }
            })
        
        return SlackMessage(
            channel="",
            text=f"Protocolo activado: {content.get('protocol_name', 'Unknown')}",
            blocks=blocks
        )
    
    async def _determine_target_channels(self, payload: NotificationPayload) -> List[str]:
        """Determina canales objetivo basado en tipo y prioridad."""
        # Canales base por tipo de notificación
        base_channels = self.channel_routing.get(payload.notification_type, [])
        
        # Canales adicionales por prioridad
        escalation_config = self.escalation_config.get(payload.priority, {})
        additional_channels = escalation_config.get("additional_channels", [])
        
        # Combinar y convertir a strings
        all_channels = list(set(base_channels + additional_channels))
        return [channel.value for channel in all_channels]
    
    async def _send_to_channel(self, channel: str, message: SlackMessage, payload: NotificationPayload) -> Dict[str, Any]:
        """Envía mensaje a un canal específico de Slack."""
        try:
            # Configurar canal en el mensaje
            message.channel = f"#{channel}"
            
            # Enviar usando el notificador de Slack
            result = await self.slack_notifier.send_slack_message(
                text=message.text,
                blocks=message.blocks,
                channel=message.channel
            )
            
            return {
                "channel": channel,
                "success": True,
                "message_ts": result.get("ts"),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error enviando a canal {channel}: {str(e)}")
            return {
                "channel": channel,
                "success": False,
                "error": str(e)
            }
    
    async def _setup_escalation(self, payload: NotificationPayload) -> None:
        """Configura escalamiento automático para notificaciones críticas."""
        escalation_config = self.escalation_config.get(payload.priority)
        if not escalation_config:
            return
        
        escalation_time = escalation_config.get("escalation_time")
        if not escalation_time:
            return
        
        # Programar escalamiento (en una implementación real usaríamos un scheduler)
        self.logger.info(
            f"Escalamiento programado para notificación {payload.notification_id} "
            f"en {escalation_time.total_seconds()} segundos"
        )
        
        # Registrar escalamiento programado
        await self.audit_service.log_event(
            AuditEvent(
                event_type="escalation_scheduled",
                session_id=payload.session_id,
                level=AuditLevel.MEDIUM,
                details={
                    "notification_id": payload.notification_id,
                    "escalation_time": escalation_time.total_seconds(),
                    "priority": payload.priority.value
                }
            )
        )
    
    async def create_emergency_notification(
        self,
        session_id: str,
        emergency_type: str,
        patient_info: str,
        recommended_action: str,
        criticality: str = "Alta"
    ) -> NotificationPayload:
        """Crear notificación de emergencia médica."""
        notification_id = f"emergency_{session_id}_{int(datetime.now().timestamp())}"
        
        return NotificationPayload(
            notification_id=notification_id,
            session_id=session_id,
            notification_type=NotificationType.EMERGENCY_ALERT,
            priority=NotificationPriority.CRITICAL,
            target_channels=[SlackChannel.EMERGENCY_ROOM, SlackChannel.CLINICAL_TEAM],
            content={
                "emergency_type": emergency_type,
                "patient_info": patient_info,
                "recommended_action": recommended_action,
                "criticality": criticality
            },
            metadata={
                "created_by": "vigia_system",
                "auto_escalate": True
            },
            timestamp=datetime.now().isoformat()
        )
    
    async def create_clinical_result_notification(
        self,
        session_id: str,
        lpp_grade: int,
        confidence: float,
        clinical_description: str,
        recommendations: List[str]
    ) -> NotificationPayload:
        """Crear notificación de resultado clínico."""
        notification_id = f"clinical_{session_id}_{int(datetime.now().timestamp())}"
        
        # Determinar prioridad según grado LPP
        priority_map = {
            1: NotificationPriority.LOW,
            2: NotificationPriority.MEDIUM,
            3: NotificationPriority.HIGH,
            4: NotificationPriority.CRITICAL
        }
        priority = priority_map.get(lpp_grade, NotificationPriority.MEDIUM)
        
        return NotificationPayload(
            notification_id=notification_id,
            session_id=session_id,
            notification_type=NotificationType.CLINICAL_RESULT,
            priority=priority,
            target_channels=[SlackChannel.CLINICAL_TEAM, SlackChannel.LPP_SPECIALISTS],
            content={
                "lpp_grade": lpp_grade,
                "confidence": confidence,
                "clinical_description": clinical_description,
                "recommendations": recommendations
            },
            metadata={
                "created_by": "clinical_system",
                "requires_review": lpp_grade >= 3
            },
            timestamp=datetime.now().isoformat()
        )
    
    async def create_review_request_notification(
        self,
        session_id: str,
        priority: str,
        specialty: str,
        reason: str
    ) -> NotificationPayload:
        """Crear notificación de solicitud de revisión."""
        notification_id = f"review_{session_id}_{int(datetime.now().timestamp())}"
        
        # Mapear prioridad string a enum
        priority_map = {
            "baja": NotificationPriority.LOW,
            "media": NotificationPriority.MEDIUM,
            "alta": NotificationPriority.HIGH,
            "critica": NotificationPriority.CRITICAL
        }
        priority_enum = priority_map.get(priority.lower(), NotificationPriority.MEDIUM)
        
        return NotificationPayload(
            notification_id=notification_id,
            session_id=session_id,
            notification_type=NotificationType.HUMAN_REVIEW_REQUEST,
            priority=priority_enum,
            target_channels=[SlackChannel.CLINICAL_TEAM, SlackChannel.NURSING_STAFF],
            content={
                "priority": priority,
                "specialty": specialty,
                "reason": reason
            },
            metadata={
                "created_by": "review_system",
                "requires_response": True
            },
            timestamp=datetime.now().isoformat()
        )
    
    async def get_active_notifications(self) -> Dict[str, NotificationPayload]:
        """Obtiene notificaciones activas."""
        return self.active_notifications.copy()
    
    async def mark_notification_resolved(self, notification_id: str) -> bool:
        """Marca una notificación como resuelta."""
        if notification_id in self.active_notifications:
            payload = self.active_notifications.pop(notification_id)
            
            await self.audit_service.log_event(
                AuditEvent(
                    event_type="notification_resolved",
                    session_id=payload.session_id,
                    level=AuditLevel.LOW,
                    details={
                        "notification_id": notification_id,
                        "notification_type": payload.notification_type.value
                    }
                )
            )
            return True
        return False