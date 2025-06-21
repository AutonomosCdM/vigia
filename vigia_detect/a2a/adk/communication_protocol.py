"""
A2A Communication Protocol - Medical Extensions
==============================================

Implementation of Google's A2A communication protocol with medical-specific
extensions for HIPAA compliance, medical urgency handling, and clinical workflows.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable, AsyncIterator
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import aiohttp
from aiohttp import web, WSMsgType
import ssl

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """A2A message types with medical extensions."""
    # Standard A2A types
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR_RESPONSE = "error_response"
    
    # Medical-specific types
    MEDICAL_ALERT = "medical_alert"
    CLINICAL_CONSULTATION = "clinical_consultation"
    EMERGENCY_ESCALATION = "emergency_escalation"
    CARE_COORDINATION = "care_coordination"
    PROTOCOL_UPDATE = "protocol_update"
    AUDIT_LOG = "audit_log"


class UrgencyLevel(Enum):
    """Medical urgency levels for priority handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EncryptionLevel(Enum):
    """HIPAA-compliant encryption levels."""
    NONE = "none"
    STANDARD = "aes256"
    MEDICAL_GRADE = "aes256_medical"
    END_TO_END = "e2e_medical"


@dataclass
class MedicalContext:
    """Medical context for HIPAA compliance."""
    patient_id: Optional[str] = None
    case_id: Optional[str] = None
    medical_record_number: Optional[str] = None
    care_team_ids: List[str] = None
    consent_verified: bool = False
    audit_required: bool = True
    
    def __post_init__(self):
        if self.care_team_ids is None:
            self.care_team_ids = []


@dataclass
class A2AMessage:
    """
    A2A Protocol message with medical extensions.
    
    Follows Google's A2A specification with additional medical compliance fields.
    """
    
    # Core A2A fields
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    timestamp: str
    
    # Message content
    payload: Dict[str, Any]
    
    # Medical extensions
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    medical_context: Optional[MedicalContext] = None
    encryption_level: EncryptionLevel = EncryptionLevel.MEDICAL_GRADE
    
    # Protocol fields
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    
    # HIPAA compliance
    audit_trail: List[Dict[str, Any]] = None
    access_log: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if self.audit_trail is None:
            self.audit_trail = []
        
        if self.access_log is None:
            self.access_log = []
        
        # Add initial audit entry
        self.add_audit_entry("message_created", {"sender": self.sender_id})
    
    def add_audit_entry(self, action: str, details: Dict[str, Any]) -> None:
        """Add entry to audit trail for HIPAA compliance."""
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "message_id": self.message_id
        }
        
        self.audit_trail.append(audit_entry)
    
    def add_access_log(self, accessor_id: str, access_type: str) -> None:
        """Log access to message for HIPAA compliance."""
        
        access_entry = {
            "timestamp": datetime.now().isoformat(),
            "accessor_id": accessor_id,
            "access_type": access_type,
            "message_id": self.message_id
        }
        
        self.access_log.append(access_entry)
    
    def is_expired(self) -> bool:
        """Check if message has exceeded TTL."""
        
        message_time = datetime.fromisoformat(self.timestamp)
        expiry_time = message_time + timedelta(seconds=self.ttl_seconds)
        
        return datetime.now() > expiry_time
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment retry count and add audit entry."""
        self.retry_count += 1
        self.add_audit_entry("message_retry", {"retry_count": self.retry_count})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for transmission."""
        
        message_dict = {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "urgency": self.urgency.value,
            "encryption_level": self.encryption_level.value,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl_seconds": self.ttl_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "audit_trail": self.audit_trail,
            "access_log": self.access_log
        }
        
        # Include medical context if present
        if self.medical_context:
            message_dict["medical_context"] = asdict(self.medical_context)
        
        return message_dict
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, message_dict: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary."""
        
        # Convert enums
        message_type = MessageType(message_dict["message_type"])
        urgency = UrgencyLevel(message_dict.get("urgency", "medium"))
        encryption_level = EncryptionLevel(message_dict.get("encryption_level", "aes256_medical"))
        
        # Convert medical context
        medical_context = None
        if "medical_context" in message_dict:
            medical_context = MedicalContext(**message_dict["medical_context"])
        
        return cls(
            message_id=message_dict["message_id"],
            sender_id=message_dict["sender_id"],
            recipient_id=message_dict["recipient_id"],
            message_type=message_type,
            timestamp=message_dict["timestamp"],
            payload=message_dict["payload"],
            urgency=urgency,
            medical_context=medical_context,
            encryption_level=encryption_level,
            correlation_id=message_dict.get("correlation_id"),
            reply_to=message_dict.get("reply_to"),
            ttl_seconds=message_dict.get("ttl_seconds", 300),
            retry_count=message_dict.get("retry_count", 0),
            max_retries=message_dict.get("max_retries", 3),
            audit_trail=message_dict.get("audit_trail", []),
            access_log=message_dict.get("access_log", [])
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'A2AMessage':
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))


class MedicalMessageHandler:
    """
    Message handler with medical-specific processing.
    
    Provides HIPAA-compliant message handling, medical urgency routing,
    and clinical workflow integration.
    """
    
    def __init__(self):
        """Initialize medical message handler."""
        
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.urgency_queues: Dict[UrgencyLevel, asyncio.Queue] = {}
        self.active_messages: Dict[str, A2AMessage] = {}
        self.message_stats: Dict[str, int] = {
            "total_processed": 0,
            "emergency_messages": 0,
            "failed_messages": 0,
            "audit_entries": 0
        }
        
        # Initialize urgency queues
        for urgency in UrgencyLevel:
            self.urgency_queues[urgency] = asyncio.Queue()
        
        logger.info("Medical Message Handler initialized")
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[A2AMessage], Any]
    ) -> None:
        """Register message handler for specific message type."""
        
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type.value}")
    
    async def process_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """
        Process incoming A2A message with medical compliance.
        
        Args:
            message: A2A message to process
            
        Returns:
            Optional response message
        """
        
        try:
            # Add access log
            message.add_access_log("message_handler", "process_start")
            
            # Validate message
            if not self._validate_medical_message(message):
                return self._create_error_response(message, "Message validation failed")
            
            # Check expiration
            if message.is_expired():
                return self._create_error_response(message, "Message expired")
            
            # Route by urgency
            await self._route_by_urgency(message)
            
            # Process based on message type
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                return self._create_error_response(message, "No handler for message type")
            
            # Execute handler
            response = await self._execute_handler(handler, message)
            
            # Update statistics
            self._update_message_stats(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            return self._create_error_response(message, str(e))
    
    def _validate_medical_message(self, message: A2AMessage) -> bool:
        """Validate medical message for HIPAA compliance."""
        
        # Check required fields
        if not all([message.message_id, message.sender_id, message.recipient_id]):
            return False
        
        # Validate medical context for medical messages
        if message.message_type in [MessageType.MEDICAL_ALERT, MessageType.CLINICAL_CONSULTATION]:
            if not message.medical_context:
                return False
            
            # Verify consent for patient data
            if message.medical_context.patient_id and not message.medical_context.consent_verified:
                logger.warning(f"Message {message.message_id} lacks patient consent verification")
                return False
        
        # Validate encryption for medical data
        if message.medical_context and message.medical_context.patient_id:
            if message.encryption_level == EncryptionLevel.NONE:
                return False
        
        return True
    
    async def _route_by_urgency(self, message: A2AMessage) -> None:
        """Route message based on medical urgency."""
        
        urgency_queue = self.urgency_queues[message.urgency]
        await urgency_queue.put(message)
        
        # Store active message
        self.active_messages[message.message_id] = message
        
        message.add_audit_entry("message_routed", {"urgency": message.urgency.value})
    
    async def _execute_handler(
        self,
        handler: Callable,
        message: A2AMessage
    ) -> Optional[A2AMessage]:
        """Execute message handler with timeout based on urgency."""
        
        # Determine timeout based on urgency
        timeout_map = {
            UrgencyLevel.EMERGENCY: 5,
            UrgencyLevel.CRITICAL: 10,
            UrgencyLevel.HIGH: 30,
            UrgencyLevel.MEDIUM: 60,
            UrgencyLevel.LOW: 120
        }
        
        timeout = timeout_map.get(message.urgency, 60)
        
        try:
            # Execute handler with timeout
            response = await asyncio.wait_for(handler(message), timeout=timeout)
            
            message.add_audit_entry("handler_executed", {"timeout": timeout})
            
            return response
            
        except asyncio.TimeoutError:
            message.add_audit_entry("handler_timeout", {"timeout": timeout})
            return self._create_error_response(message, "Handler timeout")
    
    def _create_error_response(self, original_message: A2AMessage, error: str) -> A2AMessage:
        """Create error response message."""
        
        error_response = A2AMessage(
            message_id=str(uuid.uuid4()),
            sender_id=original_message.recipient_id,
            recipient_id=original_message.sender_id,
            message_type=MessageType.ERROR_RESPONSE,
            timestamp=datetime.now().isoformat(),
            payload={"error": error, "original_message_id": original_message.message_id},
            correlation_id=original_message.message_id,
            urgency=original_message.urgency,
            medical_context=original_message.medical_context
        )
        
        return error_response
    
    def _update_message_stats(self, message: A2AMessage) -> None:
        """Update message processing statistics."""
        
        self.message_stats["total_processed"] += 1
        
        if message.urgency == UrgencyLevel.EMERGENCY:
            self.message_stats["emergency_messages"] += 1
        
        self.message_stats["audit_entries"] += len(message.audit_trail)
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get message processing statistics."""
        
        return {
            **self.message_stats,
            "active_messages": len(self.active_messages),
            "queue_depths": {
                urgency.value: queue.qsize() 
                for urgency, queue in self.urgency_queues.items()
            },
            "timestamp": datetime.now().isoformat()
        }


class VigiaA2AProtocol:
    """
    Vigia A2A Protocol implementation with medical extensions.
    
    Provides HTTP/SSE-based communication with HIPAA compliance,
    medical urgency handling, and clinical workflow integration.
    """
    
    def __init__(
        self,
        agent_id: str,
        base_url: str,
        port: int = 8080,
        ssl_context: Optional[ssl.SSLContext] = None
    ):
        """Initialize Vigia A2A Protocol."""
        
        self.agent_id = agent_id
        self.base_url = base_url
        self.port = port
        self.ssl_context = ssl_context
        
        # Initialize components
        self.message_handler = MedicalMessageHandler()
        self.app = web.Application()
        self.session = None
        
        # Connection tracking
        self.connected_agents: Dict[str, Dict[str, Any]] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Vigia A2A Protocol initialized for agent {agent_id}")
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes for A2A communication."""
        
        # Core A2A endpoints
        self.app.router.add_post('/a2a/message', self._handle_message)
        self.app.router.add_get('/a2a/capabilities', self._handle_capabilities)
        self.app.router.add_get('/a2a/status', self._handle_status)
        self.app.router.add_get('/a2a/health', self._handle_health)
        
        # SSE endpoints for streaming
        self.app.router.add_get('/a2a/stream', self._handle_stream)
        
        # Medical-specific endpoints
        self.app.router.add_post('/a2a/medical/alert', self._handle_medical_alert)
        self.app.router.add_post('/a2a/medical/emergency', self._handle_emergency)
        self.app.router.add_get('/a2a/medical/audit', self._handle_audit_request)
    
    async def _handle_message(self, request: web.Request) -> web.Response:
        """Handle incoming A2A message."""
        
        try:
            # Parse message
            message_data = await request.json()
            message = A2AMessage.from_dict(message_data)
            
            # Process message
            response_message = await self.message_handler.process_message(message)
            
            if response_message:
                return web.json_response(response_message.to_dict())
            else:
                return web.Response(status=202)  # Accepted, no response
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_capabilities(self, request: web.Request) -> web.Response:
        """Handle capabilities query."""
        
        # This would typically return the agent's capabilities
        # For now, return a placeholder response
        capabilities = {
            "agent_id": self.agent_id,
            "capabilities": ["medical_processing", "hipaa_compliant"],
            "message_types_supported": [mt.value for mt in MessageType],
            "urgency_levels_supported": [ul.value for ul in UrgencyLevel],
            "encryption_supported": [el.value for el in EncryptionLevel]
        }
        
        return web.json_response(capabilities)
    
    async def _handle_status(self, request: web.Request) -> web.Response:
        """Handle status request."""
        
        status = {
            "agent_id": self.agent_id,
            "status": "healthy",
            "connected_agents": len(self.connected_agents),
            "message_stats": self.message_handler.get_message_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response(status)
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check."""
        
        health = {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response(health)
    
    async def _handle_stream(self, request: web.Request) -> web.StreamResponse:
        """Handle SSE streaming for real-time updates."""
        
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        
        await response.prepare(request)
        
        try:
            # Stream updates to client
            while True:
                # Send periodic status updates
                status_data = {
                    "type": "status_update",
                    "data": self.message_handler.get_message_stats(),
                    "timestamp": datetime.now().isoformat()
                }
                
                await response.write(f"data: {json.dumps(status_data)}\\n\\n".encode())
                await asyncio.sleep(10)  # Update every 10 seconds
                
        except asyncio.CancelledError:
            pass
        
        return response
    
    async def _handle_medical_alert(self, request: web.Request) -> web.Response:
        """Handle medical alert messages."""
        
        try:
            alert_data = await request.json()
            
            # Create medical alert message
            alert_message = A2AMessage(
                message_id=str(uuid.uuid4()),
                sender_id=alert_data.get("sender_id", "unknown"),
                recipient_id=self.agent_id,
                message_type=MessageType.MEDICAL_ALERT,
                timestamp=datetime.now().isoformat(),
                payload=alert_data,
                urgency=UrgencyLevel(alert_data.get("urgency", "high")),
                medical_context=MedicalContext(**alert_data.get("medical_context", {}))
            )
            
            # Process with high priority
            response = await self.message_handler.process_message(alert_message)
            
            return web.json_response(response.to_dict() if response else {"status": "processed"})
            
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_emergency(self, request: web.Request) -> web.Response:
        """Handle emergency escalation messages."""
        
        try:
            emergency_data = await request.json()
            
            # Create emergency message with highest priority
            emergency_message = A2AMessage(
                message_id=str(uuid.uuid4()),
                sender_id=emergency_data.get("sender_id", "unknown"),
                recipient_id=self.agent_id,
                message_type=MessageType.EMERGENCY_ESCALATION,
                timestamp=datetime.now().isoformat(),
                payload=emergency_data,
                urgency=UrgencyLevel.EMERGENCY,
                medical_context=MedicalContext(**emergency_data.get("medical_context", {})),
                ttl_seconds=60  # Short TTL for emergency
            )
            
            # Process immediately
            response = await self.message_handler.process_message(emergency_message)
            
            return web.json_response(response.to_dict() if response else {"status": "emergency_processed"})
            
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_audit_request(self, request: web.Request) -> web.Response:
        """Handle audit trail requests for HIPAA compliance."""
        
        # This would typically require authentication and authorization
        # For now, return basic audit information
        
        audit_data = {
            "agent_id": self.agent_id,
            "message_stats": self.message_handler.get_message_stats(),
            "audit_summary": {
                "total_messages_processed": self.message_handler.message_stats["total_processed"],
                "emergency_messages": self.message_handler.message_stats["emergency_messages"],
                "audit_entries_created": self.message_handler.message_stats["audit_entries"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response(audit_data)
    
    async def send_message(
        self,
        recipient_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
        medical_context: Optional[MedicalContext] = None
    ) -> Optional[A2AMessage]:
        """
        Send A2A message to another agent.
        
        Args:
            recipient_id: Target agent ID
            message_type: Type of message
            payload: Message payload
            urgency: Medical urgency level
            medical_context: Medical context for HIPAA compliance
            
        Returns:
            Response message if received
        """
        
        try:
            # Create message
            message = A2AMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                timestamp=datetime.now().isoformat(),
                payload=payload,
                urgency=urgency,
                medical_context=medical_context
            )
            
            # Send via HTTP
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Determine recipient URL (this would typically use service discovery)
            recipient_url = f"http://{recipient_id}:{self.port}/a2a/message"
            
            async with self.session.post(
                recipient_url,
                json=message.to_dict(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    return A2AMessage.from_dict(response_data)
                elif response.status == 202:
                    return None  # Accepted, no response
                else:
                    logger.error(f"Failed to send message: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error sending message to {recipient_id}: {e}")
            return None
    
    async def start_server(self) -> None:
        """Start A2A protocol server."""
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(
            runner,
            '0.0.0.0',
            self.port,
            ssl_context=self.ssl_context
        )
        
        await site.start()
        
        logger.info(f"Vigia A2A Protocol server started on port {self.port}")
    
    async def stop_server(self) -> None:
        """Stop A2A protocol server."""
        
        if self.session:
            await self.session.close()
        
        logger.info("Vigia A2A Protocol server stopped")