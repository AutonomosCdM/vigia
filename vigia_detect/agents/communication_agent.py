"""
Communication Agent - Agente ADK especializado en comunicaciones médicas
Implementa Agent Development Kit (ADK) para gestión de notificaciones y comunicaciones.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .base_agent import BaseAgent, AgentCapability, AgentMessage, AgentResponse
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType, AuditSeverity

logger = SecureLogger("communication_agent")


class CommunicationType(Enum):
    """Tipos de comunicación médica."""
    EMERGENCY_ALERT = "emergency_alert"
    CLINICAL_NOTIFICATION = "clinical_notification"
    TEAM_COORDINATION = "team_coordination"
    PATIENT_UPDATE = "patient_update"
    SYSTEM_ALERT = "system_alert"
    AUDIT_NOTIFICATION = "audit_notification"
    ESCALATION_REQUEST = "escalation_request"


class NotificationPriority(Enum):
    """Prioridades de notificación."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationChannel(Enum):
    """Canales de comunicación disponibles."""
    AUDIT_LOG = "audit_log"
    MEDICAL_ALERT_LOG = "medical_alert_log"
    ESCALATION_LOG = "escalation_log"
    INTERNAL_QUEUE = "internal_queue"


@dataclass
class CommunicationRequest:
    """Solicitud de comunicación médica."""
    communication_type: CommunicationType
    channel: CommunicationChannel
    recipients: List[str]
    subject: str
    content: Dict[str, Any]
    priority: str = "medium"
    language: str = "es"
    requires_acknowledgment: bool = False
    escalation_rules: Optional[Dict[str, Any]] = None


@dataclass
class CommunicationResult:
    """Resultado de envío de comunicación."""
    success: bool
    message_id: str
    channels_sent: List[str]
    delivery_status: Dict[str, Any]
    acknowledgments_received: int
    errors: List[str]
    next_actions: List[str]


class CommunicationAgent(BaseAgent):
    """
    Agent especializado en comunicaciones y notificaciones médicas.
    
    Responsabilidades:
    - Envío de notificaciones médicas a equipos
    - Coordinación de comunicaciones entre especialistas
    - Gestión de escalamientos automáticos
    - Integración con múltiples canales de comunicación
    """
    
    def __init__(self, 
                 agent_id: str = "communication_agent",
                 audit_service: Optional[AuditService] = None):
        """
        Inicializar CommunicationAgent.
        
        Args:
            agent_id: Identificador único del agente
            audit_service: Servicio de auditoría para logging
        """
        super().__init__(
            agent_id=agent_id,
            name="Communication Agent",
            description="Agente especializado en comunicaciones y notificaciones médicas",
            capabilities=[
                AgentCapability.MEDICAL_COMMUNICATION,
                AgentCapability.EMERGENCY_ALERTS,
                AgentCapability.TEAM_COORDINATION,
                AgentCapability.ESCALATION_MANAGEMENT
            ],
            version="1.0.0"
        )
        
        # Servicio de auditoría para logging de notificaciones
        self.audit_service = audit_service
        
        # Configuración de comunicaciones
        self.communication_config = {
            "max_retries": 3,
            "retry_delay": 5.0,  # segundos
            "acknowledgment_timeout": 300,  # 5 minutos
            "escalation_enabled": True,
            "supported_channels": [
                CommunicationChannel.AUDIT_LOG,
                CommunicationChannel.MEDICAL_ALERT_LOG,
                CommunicationChannel.ESCALATION_LOG,
                CommunicationChannel.INTERNAL_QUEUE
            ]
        }
        
        # Tracking de comunicaciones activas
        self.active_communications: Dict[str, CommunicationRequest] = {}
        self.pending_acknowledgments: Dict[str, datetime] = {}
        
        logger.audit("communication_agent_initialized", {
            "agent_id": self.agent_id,
            "capabilities": [cap.value for cap in self.capabilities],
            "supported_channels": [ch.value for ch in self.communication_config["supported_channels"]],
            "escalation_enabled": self.communication_config["escalation_enabled"]
        })
    
    async def initialize(self) -> bool:
        """
        Inicializar el agente y sus dependencias.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            # Inicializar servicio de auditoría si no está disponible
            if self.audit_service is None:
                try:
                    from ..utils.audit_service import get_audit_service
                    self.audit_service = await get_audit_service()
                except Exception as e:
                    logger.warning("audit_service_initialization_failed", {
                        "error": str(e),
                        "fallback": "using_direct_logging"
                    })
            
            # Marcar como inicializado
            self.is_initialized = True
            
            logger.audit("communication_agent_ready", {
                "agent_id": self.agent_id,
                "initialization_successful": True,
                "audit_service_ready": self.audit_service is not None
            })
            
            return True
            
        except Exception as e:
            logger.error("communication_agent_initialization_failed", {
                "agent_id": self.agent_id,
                "error": str(e)
            })
            return False
    
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """
        Procesar mensaje y generar comunicación médica.
        
        Args:
            message: Mensaje del agente
            
        Returns:
            AgentResponse: Respuesta del agente
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Validar mensaje
            if not self._validate_message(message):
                return self._create_error_response(
                    message, 
                    "Invalid message format for communication request"
                )
            
            # Extraer solicitud de comunicación
            comm_request = self._extract_communication_request(message)
            
            # Procesar comunicación
            comm_result = await self._process_communication(comm_request)
            
            # Generar respuesta
            response = await self._generate_communication_response(
                message,
                comm_request, 
                comm_result,
                start_time
            )
            
            # Registrar comunicación procesada
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.audit("communication_processed", {
                "agent_id": self.agent_id,
                "session_id": message.session_id,
                "communication_type": comm_request.communication_type.value,
                "channel": comm_request.channel.value,
                "success": comm_result.success,
                "channels_sent": len(comm_result.channels_sent),
                "processing_time": processing_time
            })
            
            return response
            
        except Exception as e:
            logger.error("communication_processing_failed", {
                "agent_id": self.agent_id,
                "session_id": message.session_id,
                "error": str(e)
            })
            
            return self._create_error_response(message, str(e))
    
    async def _process_communication(self, request: CommunicationRequest) -> CommunicationResult:
        """
        Procesar solicitud de comunicación.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            CommunicationResult: Resultado del procesamiento
        """
        try:
            # Generar ID único para la comunicación
            message_id = f"{request.communication_type.value}_{datetime.now().timestamp()}"
            
            # Registrar comunicación activa
            self.active_communications[message_id] = request
            
            # Procesar según el canal
            if request.channel == CommunicationChannel.AUDIT_LOG:
                result = await self._send_audit_log_communication(request, message_id)
            elif request.channel == CommunicationChannel.MEDICAL_ALERT_LOG:
                result = await self._send_medical_alert_communication(request, message_id)
            elif request.channel == CommunicationChannel.ESCALATION_LOG:
                result = await self._send_escalation_communication(request, message_id)
            elif request.channel == CommunicationChannel.INTERNAL_QUEUE:
                result = await self._send_internal_communication(request, message_id)
            else:
                raise ValueError(f"Canal de comunicación no soportado: {request.channel}")
            
            # Configurar seguimiento de acknowledgments si es necesario
            if request.requires_acknowledgment:
                await self._setup_acknowledgment_tracking(message_id)
            
            return result
            
        except Exception as e:
            logger.error("communication_processing_failed", {
                "communication_type": request.communication_type.value,
                "channel": request.channel.value,
                "error": str(e)
            })
            
            return CommunicationResult(
                success=False,
                message_id="",
                channels_sent=[],
                delivery_status={"error": str(e)},
                acknowledgments_received=0,
                errors=[str(e)],
                next_actions=["Reintentar comunicación", "Verificar configuración"]
            )
    
    async def _send_audit_log_communication(self, 
                                           request: CommunicationRequest, 
                                           message_id: str) -> CommunicationResult:
        """
        Enviar comunicación a través de audit log.
        
        Args:
            request: Solicitud de comunicación
            message_id: ID del mensaje
            
        Returns:
            CommunicationResult: Resultado del envío
        """
        try:
            # Mapear tipo de comunicación a evento de auditoría
            audit_event_type = self._map_communication_to_audit_event(request.communication_type)
            
            # Preparar detalles de la notificación
            notification_details = {
                "communication_type": request.communication_type.value,
                "subject": request.subject,
                "content": request.content,
                "recipients": request.recipients,
                "priority": request.priority,
                "language": request.language,
                "requires_acknowledgment": request.requires_acknowledgment,
                "medical_urgency": self._determine_medical_urgency(request),
                "notification_template": self._generate_generic_template(request)
            }
            
            # Log del evento en auditoría
            if self.audit_service:
                await self.audit_service.log_event(
                    event_type=audit_event_type,
                    component="communication_agent",
                    action="medical_notification_sent",
                    details=notification_details,
                    session_id=message_id
                )
            else:
                # Fallback a logging directo
                logger.audit("medical_notification_sent", {
                    "message_id": message_id,
                    "event_type": audit_event_type.value if hasattr(audit_event_type, 'value') else str(audit_event_type),
                    **notification_details
                })
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channels_sent=["audit_log"],
                delivery_status={"logged_to_audit": True, "timestamp": datetime.now(timezone.utc).isoformat()},
                acknowledgments_received=0,
                errors=[],
                next_actions=["Monitor audit logs"] if request.requires_acknowledgment else []
            )
                
        except Exception as e:
            logger.error("audit_log_communication_failed", {
                "message_id": message_id,
                "error": str(e)
            })
            
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channels_sent=[],
                delivery_status={"error": str(e)},
                acknowledgments_received=0,
                errors=[str(e)],
                next_actions=["Retry audit logging", "Use fallback logging"]
            )
    
    async def _send_medical_alert_communication(self, 
                                              request: CommunicationRequest, 
                                              message_id: str) -> CommunicationResult:
        """
        Enviar alerta médica con prioridad alta.
        
        Args:
            request: Solicitud de comunicación
            message_id: ID del mensaje
            
        Returns:
            CommunicationResult: Resultado del envío
        """
        try:
            # Determinar severidad basada en el contenido médico
            severity = self._determine_medical_severity(request)
            
            # Preparar detalles de alerta médica
            alert_details = {
                "alert_type": "medical_emergency" if request.communication_type == CommunicationType.EMERGENCY_ALERT else "medical_notification",
                "medical_urgency": self._determine_medical_urgency(request),
                "clinical_context": request.content.get("clinical_context", {}),
                "patient_code": request.content.get("patient_code", "UNKNOWN"),
                "lpp_grade": request.content.get("lpp_grade", 0),
                "confidence": request.content.get("confidence", 0.0),
                "anatomical_location": request.content.get("anatomical_location", "unspecified"),
                "escalation_required": self._requires_escalation(request),
                "medical_template": self._generate_medical_alert_template(request),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "priority": request.priority,
                "recipients": request.recipients
            }
            
            # Log como evento de auditoría médica
            if self.audit_service:
                await self.audit_service.log_event(
                    event_type=AuditEventType.MEDICAL_DECISION,
                    component="communication_agent",
                    action="medical_alert_generated",
                    details=alert_details,
                    session_id=message_id
                )
            else:
                logger.audit("medical_alert_generated", {
                    "message_id": message_id,
                    **alert_details
                })
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channels_sent=["medical_alert_log"],
                delivery_status={"medical_alert_logged": True, "severity": severity, "escalation_required": alert_details["escalation_required"]},
                acknowledgments_received=0,
                errors=[],
                next_actions=["Monitor medical alerts", "Check escalation requirements"]
            )
                
        except Exception as e:
            logger.error("medical_alert_communication_failed", {
                "message_id": message_id,
                "error": str(e)
            })
            
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channels_sent=[],
                delivery_status={"error": str(e)},
                acknowledgments_received=0,
                errors=[str(e)],
                next_actions=["Retry medical alert", "Use emergency fallback"]
            )
    
    async def _send_escalation_communication(self, 
                                           request: CommunicationRequest, 
                                           message_id: str) -> CommunicationResult:
        """
        Enviar comunicación de escalamiento.
        
        Args:
            request: Solicitud de comunicación
            message_id: ID del mensaje
            
        Returns:
            CommunicationResult: Resultado del envío
        """
        try:
            # Preparar detalles de escalamiento
            escalation_details = {
                "escalation_type": request.communication_type.value,
                "escalation_reason": request.content.get("escalation_reason", "medical_urgency"),
                "original_alert": request.content.get("original_alert", {}),
                "escalation_level": self._determine_escalation_level(request),
                "requires_immediate_attention": request.priority in ["high", "critical"],
                "escalation_template": self._generate_escalation_template(request),
                "medical_context": request.content.get("medical_context", {}),
                "time_sensitive": request.content.get("time_sensitive", True),
                "escalation_chain": request.recipients,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Log como evento de escalamiento
            if self.audit_service:
                await self.audit_service.log_event(
                    event_type=AuditEventType.REVIEW_ASSIGNED,
                    component="communication_agent",
                    action="medical_escalation_triggered",
                    details=escalation_details,
                    session_id=message_id
                )
            else:
                logger.audit("medical_escalation_triggered", {
                    "message_id": message_id,
                    **escalation_details
                })
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channels_sent=["escalation_log"],
                delivery_status={"escalation_logged": True, "escalation_level": escalation_details["escalation_level"]},
                acknowledgments_received=0,
                errors=[],
                next_actions=["Monitor escalation status", "Track response time"]
            )
                
        except Exception as e:
            logger.error("escalation_communication_failed", {
                "message_id": message_id,
                "error": str(e)
            })
            
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channels_sent=[],
                delivery_status={"error": str(e)},
                acknowledgments_received=0,
                errors=[str(e)],
                next_actions=["Retry escalation", "Use emergency protocols"]
            )
    
    async def _send_internal_communication(self, 
                                         request: CommunicationRequest, 
                                         message_id: str) -> CommunicationResult:
        """
        Enviar comunicación interna (cola de mensajes).
        
        Args:
            request: Solicitud de comunicación
            message_id: ID del mensaje
            
        Returns:
            CommunicationResult: Resultado del envío
        """
        try:
            # Simular envío a cola interna
            internal_message = {
                "message_id": message_id,
                "communication_type": request.communication_type.value,
                "recipients": request.recipients,
                "subject": request.subject,
                "content": request.content,
                "priority": request.priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # En una implementación real, esto enviaría a Redis/RabbitMQ/etc.
            logger.info("internal_communication_queued", {
                "message_id": message_id,
                "recipients": len(request.recipients),
                "priority": request.priority
            })
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channels_sent=["internal_queue"],
                delivery_status={"status": "queued", "recipients": len(request.recipients)},
                acknowledgments_received=0,
                errors=[],
                next_actions=["Monitorear cola de mensajes"]
            )
            
        except Exception as e:
            logger.error("internal_communication_failed", {
                "message_id": message_id,
                "error": str(e)
            })
            
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channels_sent=[],
                delivery_status={"error": str(e)},
                acknowledgments_received=0,
                errors=[str(e)],
                next_actions=["Reintentar envío interno"]
            )
    
    def _map_communication_to_audit_event(self, comm_type: CommunicationType) -> AuditEventType:
        """
        Mapear tipo de comunicación a evento de auditoría.
        
        Args:
            comm_type: Tipo de comunicación
            
        Returns:
            AuditEventType: Tipo de evento de auditoría
        """
        mapping = {
            CommunicationType.EMERGENCY_ALERT: AuditEventType.MEDICAL_DECISION,
            CommunicationType.CLINICAL_NOTIFICATION: AuditEventType.MEDICAL_DECISION,
            CommunicationType.TEAM_COORDINATION: AuditEventType.REVIEW_ASSIGNED,
            CommunicationType.PATIENT_UPDATE: AuditEventType.DATA_MODIFIED,
            CommunicationType.SYSTEM_ALERT: AuditEventType.SYSTEM_START,
            CommunicationType.AUDIT_NOTIFICATION: AuditEventType.SUSPICIOUS_ACTIVITY,
            CommunicationType.ESCALATION_REQUEST: AuditEventType.REVIEW_ASSIGNED
        }
        return mapping.get(comm_type, AuditEventType.MEDICAL_DECISION)
    
    def _determine_medical_urgency(self, request: CommunicationRequest) -> str:
        """
        Determinar urgencia médica basada en el contenido.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            str: Nivel de urgencia
        """
        priority_mapping = {
            "critical": "emergency",
            "high": "urgent",
            "medium": "routine",
            "low": "informational"
        }
        
        base_urgency = priority_mapping.get(request.priority, "routine")
        
        # Ajustar basado en contenido médico
        content = request.content
        if content.get("lpp_grade", 0) >= 3:
            return "emergency"
        elif content.get("confidence", 0) > 0.9 and content.get("lpp_grade", 0) >= 2:
            return "urgent"
        
        return base_urgency
    
    def _determine_medical_severity(self, request: CommunicationRequest) -> str:
        """
        Determinar severidad médica.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            str: Severidad médica
        """
        if request.communication_type == CommunicationType.EMERGENCY_ALERT:
            return "critical"
        elif request.priority == "critical":
            return "critical"
        elif request.priority == "high":
            return "high"
        else:
            return "medium"
    
    def _requires_escalation(self, request: CommunicationRequest) -> bool:
        """
        Determinar si se requiere escalamiento.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            bool: True si requiere escalamiento
        """
        # Escalamiento automático para casos críticos
        if request.communication_type == CommunicationType.EMERGENCY_ALERT:
            return True
        
        # Escalamiento basado en grado de LPP
        lpp_grade = request.content.get("lpp_grade", 0)
        if lpp_grade >= 3:
            return True
        
        # Escalamiento basado en prioridad
        if request.priority == "critical":
            return True
        
        return False
    
    def _determine_escalation_level(self, request: CommunicationRequest) -> int:
        """
        Determinar nivel de escalamiento (1-5).
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            int: Nivel de escalamiento
        """
        if request.communication_type == CommunicationType.EMERGENCY_ALERT:
            return 5  # Máximo nivel
        elif request.priority == "critical":
            return 4
        elif request.priority == "high":
            return 3
        elif request.priority == "medium":
            return 2
        else:
            return 1
    
    def _generate_generic_template(self, request: CommunicationRequest) -> Dict[str, Any]:
        """
        Generar template genérico de notificación.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            Dict: Template de notificación
        """
        template = {
            "notification_type": request.communication_type.value,
            "subject": request.subject,
            "priority": request.priority,
            "recipients": request.recipients,
            "content_summary": self._summarize_content(request.content),
            "action_required": request.requires_acknowledgment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "language": request.language
        }
        
        return template
    
    def _generate_medical_alert_template(self, request: CommunicationRequest) -> Dict[str, Any]:
        """
        Generar template de alerta médica.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            Dict: Template de alerta médica
        """
        content = request.content
        template = {
            "alert_type": "medical_pressure_injury_detection",
            "patient_code": content.get("patient_code", "UNKNOWN"),
            "lpp_grade": content.get("lpp_grade", 0),
            "confidence": content.get("confidence", 0.0),
            "anatomical_location": content.get("anatomical_location", "unspecified"),
            "urgency": self._determine_medical_urgency(request),
            "clinical_context": content.get("clinical_context", {}),
            "recommended_actions": self._get_recommended_actions(content),
            "escalation_required": self._requires_escalation(request),
            "hipaa_compliant": True,
            "audit_trail_id": f"medical_alert_{datetime.now().timestamp()}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return template
    
    def _generate_escalation_template(self, request: CommunicationRequest) -> Dict[str, Any]:
        """
        Generar template de escalamiento.
        
        Args:
            request: Solicitud de comunicación
            
        Returns:
            Dict: Template de escalamiento
        """
        template = {
            "escalation_type": request.communication_type.value,
            "escalation_level": self._determine_escalation_level(request),
            "original_alert": request.content.get("original_alert", {}),
            "escalation_reason": request.content.get("escalation_reason", "medical_urgency"),
            "time_sensitive": True,
            "requires_immediate_response": request.priority == "critical",
            "escalation_chain": request.recipients,
            "medical_context": request.content.get("medical_context", {}),
            "audit_trail_id": f"escalation_{datetime.now().timestamp()}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return template
    
    def _summarize_content(self, content: Dict[str, Any]) -> str:
        """
        Resumir contenido de manera segura (sin PII).
        
        Args:
            content: Contenido a resumir
            
        Returns:
            str: Resumen del contenido
        """
        summary_parts = []
        
        if "lpp_grade" in content:
            summary_parts.append(f"LPP Grade {content['lpp_grade']}")
        
        if "confidence" in content:
            summary_parts.append(f"Confidence {content['confidence']:.2f}")
        
        if "anatomical_location" in content:
            summary_parts.append(f"Location: {content['anatomical_location']}")
        
        if "patient_code" in content:
            # Usar solo código anonimizado
            summary_parts.append(f"Patient: {content['patient_code'][:8]}...")
        
        return "; ".join(summary_parts) if summary_parts else "Medical notification"
    
    def _get_recommended_actions(self, content: Dict[str, Any]) -> List[str]:
        """
        Obtener acciones recomendadas basadas en el contenido.
        
        Args:
            content: Contenido de la comunicación
            
        Returns:
            List[str]: Lista de acciones recomendadas
        """
        actions = []
        
        lpp_grade = content.get("lpp_grade", 0)
        
        if lpp_grade >= 3:
            actions.extend([
                "Immediate medical evaluation required",
                "Consider specialist consultation",
                "Implement pressure relief protocol"
            ])
        elif lpp_grade >= 2:
            actions.extend([
                "Schedule medical assessment",
                "Implement preventive measures",
                "Monitor progression"
            ])
        else:
            actions.extend([
                "Continue monitoring",
                "Implement preventive care"
            ])
        
        return actions
    
    def _extract_communication_request(self, message: AgentMessage) -> CommunicationRequest:
        """
        Extraer solicitud de comunicación del mensaje.
        
        Args:
            message: Mensaje del agente
            
        Returns:
            CommunicationRequest: Solicitud de comunicación
        """
        content = message.content
        
        # Determinar tipo de comunicación
        comm_type = self._classify_communication_type(content.get("text", ""))
        
        # Extraer canal (default: audit_log)
        channel_str = content.get("channel", "audit_log")
        channel = CommunicationChannel(channel_str) if channel_str in [c.value for c in CommunicationChannel] else CommunicationChannel.AUDIT_LOG
        
        # Extraer destinatarios
        recipients = content.get("recipients", ["equipo_clinico"])
        
        # Extraer asunto
        subject = content.get("subject", content.get("text", "Comunicación médica")[:50])
        
        # Extraer prioridad
        priority = content.get("priority", "medium")
        
        # Extraer idioma
        language = content.get("language", "es")
        
        # Extraer configuración de acknowledgment
        requires_ack = content.get("requires_acknowledgment", False)
        
        # Extraer reglas de escalamiento
        escalation_rules = content.get("escalation_rules")
        
        return CommunicationRequest(
            communication_type=comm_type,
            channel=channel,
            recipients=recipients,
            subject=subject,
            content=content,
            priority=priority,
            language=language,
            requires_acknowledgment=requires_ack,
            escalation_rules=escalation_rules
        )
    
    def _classify_communication_type(self, text: str) -> CommunicationType:
        """
        Clasificar tipo de comunicación basado en el texto.
        
        Args:
            text: Texto a clasificar
            
        Returns:
            CommunicationType: Tipo de comunicación
        """
        text_lower = text.lower()
        
        # Palabras clave por tipo
        type_keywords = {
            CommunicationType.EMERGENCY_ALERT: [
                "emergencia", "emergency", "crítico", "critical", "alerta", "alert"
            ],
            CommunicationType.CLINICAL_NOTIFICATION: [
                "resultado clínico", "clinical result", "diagnóstico", "diagnosis",
                "lpp", "pressure injury"
            ],
            CommunicationType.TEAM_COORDINATION: [
                "coordinación", "coordination", "equipo", "team", "reunión", "meeting"
            ],
            CommunicationType.PATIENT_UPDATE: [
                "paciente", "patient", "actualización", "update", "estado", "status"
            ],
            CommunicationType.SYSTEM_ALERT: [
                "sistema", "system", "error", "fallo", "maintenance", "mantenimiento"
            ],
            CommunicationType.AUDIT_NOTIFICATION: [
                "auditoría", "audit", "compliance", "cumplimiento", "log"
            ],
            CommunicationType.ESCALATION_REQUEST: [
                "escalamiento", "escalation", "escalate", "urgente", "urgent"
            ]
        }
        
        # Buscar coincidencias
        for comm_type, keywords in type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return comm_type
        
        # Default
        return CommunicationType.CLINICAL_NOTIFICATION
    
    async def _setup_acknowledgment_tracking(self, message_id: str):
        """
        Configurar seguimiento de acknowledgments.
        
        Args:
            message_id: ID del mensaje
        """
        self.pending_acknowledgments[message_id] = datetime.now(timezone.utc)
        
        logger.audit("acknowledgment_tracking_setup", {
            "message_id": message_id,
            "timeout": self.communication_config["acknowledgment_timeout"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def _generate_communication_response(self, 
                                             message: AgentMessage,
                                             request: CommunicationRequest,
                                             result: CommunicationResult,
                                             start_time: datetime) -> AgentResponse:
        """
        Generar respuesta de comunicación.
        
        Args:
            message: Mensaje original
            request: Solicitud de comunicación
            result: Resultado de comunicación
            start_time: Tiempo de inicio
            
        Returns:
            AgentResponse: Respuesta del agente
        """
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        if result.success:
            # Comunicación exitosa
            response_content = {
                "communication_result": asdict(result),
                "status": "sent",
                "channels_delivered": result.channels_sent,
                "delivery_status": result.delivery_status,
                "next_actions": result.next_actions
            }
            
            success = True
            response_text = f"Comunicación enviada a {len(result.channels_sent)} canales"
            
        else:
            # Error en comunicación
            response_content = {
                "communication_result": asdict(result),
                "status": "failed",
                "errors": result.errors,
                "next_actions": result.next_actions,
                "retry_available": True
            }
            
            success = False
            response_text = f"Error enviando comunicación: {', '.join(result.errors)}"
        
        return AgentResponse(
            session_id=message.session_id,
            agent_id=self.agent_id,
            success=success,
            content=response_content,
            metadata={
                "processing_time": processing_time,
                "communication_type": request.communication_type.value,
                "channel": request.channel.value,
                "recipients": len(request.recipients),
                "requires_acknowledgment": request.requires_acknowledgment,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            message=response_text,
            next_actions=result.next_actions,
            requires_human_review=not result.success
        )
    
    def _validate_message(self, message: AgentMessage) -> bool:
        """
        Validar formato del mensaje.
        
        Args:
            message: Mensaje a validar
            
        Returns:
            bool: True si el mensaje es válido
        """
        if not message.content:
            return False
        
        # Debe tener texto o contenido específico
        text = message.content.get("text", "")
        subject = message.content.get("subject", "")
        
        if not text and not subject:
            return False
        
        return True
    
    def _create_error_response(self, message: AgentMessage, error: str) -> AgentResponse:
        """
        Crear respuesta de error.
        
        Args:
            message: Mensaje original
            error: Descripción del error
            
        Returns:
            AgentResponse: Respuesta de error
        """
        return AgentResponse(
            session_id=message.session_id,
            agent_id=self.agent_id,
            success=False,
            content={
                "error": error,
                "status": "error",
                "retry_available": True
            },
            metadata={
                "error_occurred": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            message=f"Error en comunicación: {error}",
            next_actions=["Verificar configuración", "Reintentar comunicación"],
            requires_human_review=True
        )
    
    async def receive_acknowledgment(self, message_id: str, user_id: str) -> bool:
        """
        Recibir acknowledgment de mensaje.
        
        Args:
            message_id: ID del mensaje
            user_id: ID del usuario que confirma
            
        Returns:
            bool: True si se procesó correctamente
        """
        try:
            if message_id in self.pending_acknowledgments:
                # Registrar acknowledgment
                logger.audit("acknowledgment_received", {
                    "message_id": message_id,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Remover de pendientes
                del self.pending_acknowledgments[message_id]
                
                return True
            
            return False
            
        except Exception as e:
            logger.error("acknowledgment_processing_failed", {
                "message_id": message_id,
                "user_id": user_id,
                "error": str(e)
            })
            return False
    
    async def shutdown(self):
        """Cerrar agente y liberar recursos."""
        try:
            logger.audit("communication_agent_shutdown", {
                "agent_id": self.agent_id,
                "active_communications": len(self.active_communications),
                "pending_acknowledgments": len(self.pending_acknowledgments),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Limpiar comunicaciones activas
            self.active_communications.clear()
            self.pending_acknowledgments.clear()
            
            self.is_initialized = False
            
        except Exception as e:
            logger.error("communication_agent_shutdown_error", {
                "agent_id": self.agent_id,
                "error": str(e)
            })


# Factory para crear CommunicationAgent
class CommunicationAgentFactory:
    """Factory para crear instancias de CommunicationAgent."""
    
    @staticmethod
    async def create_agent(config: Optional[Dict[str, Any]] = None) -> CommunicationAgent:
        """
        Crear instancia de CommunicationAgent.
        
        Args:
            config: Configuración opcional
            
        Returns:
            CommunicationAgent: Instancia configurada
        """
        config = config or {}
        
        # Crear servicio de auditoría si se especifica
        audit_service = None
        if config.get("use_audit_service", True):
            try:
                from ..utils.audit_service import get_audit_service
                audit_service = await get_audit_service()
            except Exception as e:
                logger.warning("audit_service_creation_failed", {
                    "error": str(e),
                    "fallback": "using_direct_logging"
                })
        
        # Crear agente
        agent = CommunicationAgent(
            agent_id=config.get("agent_id", "communication_agent"),
            audit_service=audit_service
        )
        
        # Inicializar
        await agent.initialize()
        
        return agent