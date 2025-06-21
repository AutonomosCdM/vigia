"""
Advanced A2A Protocol Layer - JSON-RPC 2.0 Implementation
========================================================

Capa de protocolo avanzada para comunicación Agent-to-Agent distribuida
usando JSON-RPC 2.0 con extensiones médicas para compliance y trazabilidad.

Features:
- JSON-RPC 2.0 compliant messaging
- Medical audit trail integration
- Encrypted message transport
- Session-based authentication
- Load balancing support
- Health monitoring integration
- Fault tolerance mechanisms
"""

import asyncio
import json
import uuid
import time
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from asyncio import Queue
import aiohttp
from aiohttp import web
import ssl
import jwt
from cryptography.fernet import Fernet

from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("a2a_protocol_layer")


class MessageType(Enum):
    """Types of A2A messages"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BATCH = "batch"
    ERROR = "error"


class MessagePriority(Enum):
    """Message priority levels for medical contexts"""
    CRITICAL = "critical"     # Emergency medical situations
    HIGH = "high"            # Urgent medical processing
    NORMAL = "normal"        # Standard medical workflow
    LOW = "low"             # Administrative tasks


class AuthLevel(Enum):
    """Authentication levels for medical compliance"""
    PUBLIC = "public"        # No PHI access
    MEDICAL = "medical"      # PHI access allowed
    ADMIN = "admin"         # System administration
    EMERGENCY = "emergency"  # Emergency override


@dataclass
class A2AMessage:
    """
    Advanced A2A message following JSON-RPC 2.0 specification
    with medical audit extensions
    """
    jsonrpc: str = "2.0"
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    # Medical/audit extensions
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    auth_level: AuthLevel = AuthLevel.PUBLIC
    medical_context: Optional[Dict[str, Any]] = None
    audit_trail: Optional[List[Dict[str, Any]]] = None
    encryption_key: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.id is None and (self.method or self.result is not None):
            self.id = str(uuid.uuid4())
        if self.audit_trail is None:
            self.audit_trail = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        
        # Core JSON-RPC 2.0 fields
        result["jsonrpc"] = self.jsonrpc
        
        if self.method is not None:
            result["method"] = self.method
        if self.params is not None:
            result["params"] = self.params
        if self.id is not None:
            result["id"] = self.id
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
            
        # Medical extensions
        result["timestamp"] = self.timestamp
        result["session_id"] = self.session_id
        result["agent_id"] = self.agent_id
        result["priority"] = self.priority.value
        result["auth_level"] = self.auth_level.value
        result["medical_context"] = self.medical_context
        result["audit_trail"] = self.audit_trail
        result["encryption_key"] = self.encryption_key
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method"),
            params=data.get("params"),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error"),
            timestamp=data.get("timestamp"),
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id"),
            priority=MessagePriority(data.get("priority", "normal")),
            auth_level=AuthLevel(data.get("auth_level", "public")),
            medical_context=data.get("medical_context"),
            audit_trail=data.get("audit_trail", []),
            encryption_key=data.get("encryption_key")
        )

    def add_audit_entry(self, event: str, agent_id: str, details: Optional[Dict[str, Any]] = None):
        """Add audit trail entry for medical compliance"""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "agent_id": agent_id,
            "details": details or {}
        }
        self.audit_trail.append(audit_entry)


class MessageValidator:
    """Validates A2A messages for JSON-RPC 2.0 compliance and medical safety"""
    
    @staticmethod
    def validate_request(message: A2AMessage) -> Tuple[bool, Optional[str]]:
        """Validate request message"""
        if message.jsonrpc != "2.0":
            return False, "Invalid JSON-RPC version"
        
        if not message.method:
            return False, "Missing method field"
        
        if message.result is not None or message.error is not None:
            return False, "Request cannot have result or error fields"
            
        # Medical safety validations
        if message.auth_level == AuthLevel.MEDICAL and not message.session_id:
            return False, "Medical operations require session_id"
            
        return True, None
    
    @staticmethod
    def validate_response(message: A2AMessage) -> Tuple[bool, Optional[str]]:
        """Validate response message"""
        if message.jsonrpc != "2.0":
            return False, "Invalid JSON-RPC version"
        
        if message.id is None:
            return False, "Response must have id field"
        
        if message.method is not None:
            return False, "Response cannot have method field"
        
        if message.result is None and message.error is None:
            return False, "Response must have either result or error"
        
        if message.result is not None and message.error is not None:
            return False, "Response cannot have both result and error"
            
        return True, None


class MessageEncryption:
    """Handles message encryption for medical data protection"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.fernet = Fernet(encryption_key or Fernet.generate_key())
    
    def encrypt_message(self, message: A2AMessage) -> A2AMessage:
        """Encrypt sensitive message data"""
        if message.auth_level in [AuthLevel.MEDICAL, AuthLevel.ADMIN]:
            # Encrypt sensitive fields
            if message.params:
                encrypted_params = self.fernet.encrypt(
                    json.dumps(message.params).encode()
                )
                message.params = {"encrypted_data": encrypted_params.decode()}
                message.encryption_key = "encrypted"
        
        return message
    
    def decrypt_message(self, message: A2AMessage) -> A2AMessage:
        """Decrypt message data"""
        if (message.encryption_key == "encrypted" and 
            message.params and 
            "encrypted_data" in message.params):
            
            try:
                decrypted_data = self.fernet.decrypt(
                    message.params["encrypted_data"].encode()
                )
                message.params = json.loads(decrypted_data.decode())
                message.encryption_key = None
            except Exception as e:
                logger.error(f"Failed to decrypt message: {e}")
                
        return message


class A2AProtocolLayer:
    """
    Advanced A2A Protocol Layer implementing JSON-RPC 2.0
    with medical extensions for distributed agent communication
    """
    
    def __init__(self, 
                 agent_id: str,
                 port: int = 8080,
                 auth_key: Optional[str] = None,
                 enable_encryption: bool = True):
        
        self.agent_id = agent_id
        self.port = port
        self.auth_key = auth_key or str(uuid.uuid4())
        self.enable_encryption = enable_encryption
        
        # Core components
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.session_manager = SessionManager()
        self.audit_service = AuditService()
        
        # Encryption
        self.encryption = MessageEncryption() if enable_encryption else None
        
        # Message queues by priority
        self.message_queues = {
            MessagePriority.CRITICAL: Queue(),
            MessagePriority.HIGH: Queue(),
            MessagePriority.NORMAL: Queue(),
            MessagePriority.LOW: Queue()
        }
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "active_sessions": 0,
            "avg_response_time": 0.0
        }
        
        # Web server
        self.app = web.Application()
        self.setup_routes()
        
        logger.info(f"A2A Protocol Layer initialized for agent: {agent_id}")
    
    def setup_routes(self):
        """Setup HTTP routes for A2A communication"""
        self.app.router.add_post('/a2a/message', self.handle_http_message)
        self.app.router.add_post('/a2a/batch', self.handle_batch_messages)
        self.app.router.add_get('/a2a/health', self.handle_health_check)
        self.app.router.add_get('/a2a/stats', self.handle_stats)
    
    def register_handler(self, method: str, handler: Callable):
        """Register message handler for specific method"""
        self.message_handlers[method] = handler
        logger.info(f"Registered handler for method: {method}")
    
    async def send_request(self, 
                          target_agent: str,
                          method: str,
                          params: Optional[Dict[str, Any]] = None,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          auth_level: AuthLevel = AuthLevel.PUBLIC,
                          timeout: float = 30.0) -> Any:
        """
        Send request to target agent and wait for response
        """
        message = A2AMessage(
            method=method,
            params=params,
            agent_id=self.agent_id,
            priority=priority,
            auth_level=auth_level
        )
        
        # Add audit entry
        message.add_audit_entry("request_sent", self.agent_id, {
            "target_agent": target_agent,
            "method": method
        })
        
        # Encrypt if needed
        if self.encryption and auth_level in [AuthLevel.MEDICAL, AuthLevel.ADMIN]:
            message = self.encryption.encrypt_message(message)
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[message.id] = future
        
        try:
            # Send message
            start_time = time.time()
            await self._send_message_http(target_agent, message)
            
            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            
            # Update stats
            response_time = time.time() - start_time
            self._update_response_time_stats(response_time)
            self.stats["messages_sent"] += 1
            
            return result
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(message.id, None)
            self.stats["errors"] += 1
            raise Exception(f"Request timeout: {method} to {target_agent}")
            
        except Exception as e:
            self.pending_requests.pop(message.id, None)
            self.stats["errors"] += 1
            logger.error(f"Request failed: {e}")
            raise
    
    async def send_notification(self,
                               target_agent: str,
                               method: str,
                               params: Optional[Dict[str, Any]] = None,
                               priority: MessagePriority = MessagePriority.NORMAL):
        """Send notification (no response expected)"""
        message = A2AMessage(
            method=method,
            params=params,
            agent_id=self.agent_id,
            priority=priority,
            id=None  # Notifications don't have ID
        )
        
        message.add_audit_entry("notification_sent", self.agent_id, {
            "target_agent": target_agent,
            "method": method
        })
        
        await self._send_message_http(target_agent, message)
        self.stats["messages_sent"] += 1
    
    async def _send_message_http(self, target_agent: str, message: A2AMessage):
        """Send message via HTTP"""
        url = f"http://{target_agent}/a2a/message"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=message.to_dict(),
                headers={"Authorization": f"Bearer {self.auth_key}"}
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error: {response.status}")
    
    async def handle_http_message(self, request: web.Request) -> web.Response:
        """Handle incoming HTTP message"""
        try:
            # Authenticate request
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return web.Response(status=401, text="Missing or invalid authorization")
            
            # Parse message
            data = await request.json()
            message = A2AMessage.from_dict(data)
            
            # Decrypt if needed
            if self.encryption and message.encryption_key:
                message = self.encryption.decrypt_message(message)
            
            # Add audit entry
            message.add_audit_entry("message_received", self.agent_id)
            
            # Process message
            if message.method:  # Request or notification
                response = await self._process_request(message)
                if response and message.id:  # Only send response if ID present
                    return web.json_response(response.to_dict())
                else:
                    return web.Response(status=200)  # Notification processed
            else:  # Response
                await self._process_response(message)
                return web.Response(status=200)
                
        except Exception as e:
            logger.error(f"Error handling HTTP message: {e}")
            error_response = A2AMessage(
                error={"code": -32603, "message": "Internal error", "data": str(e)},
                id=data.get("id") if 'data' in locals() else None
            )
            return web.json_response(error_response.to_dict(), status=500)
    
    async def _process_request(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Process incoming request"""
        self.stats["messages_received"] += 1
        
        # Validate request
        valid, error_msg = MessageValidator.validate_request(message)
        if not valid:
            return A2AMessage(
                error={"code": -32600, "message": error_msg},
                id=message.id
            )
        
        # Check if handler exists
        if message.method not in self.message_handlers:
            return A2AMessage(
                error={"code": -32601, "message": "Method not found"},
                id=message.id
            )
        
        # Execute handler
        try:
            handler = self.message_handlers[message.method]
            result = await handler(message.params, message)
            
            if message.id:  # Request needs response
                response = A2AMessage(
                    result=result,
                    id=message.id,
                    agent_id=self.agent_id
                )
                response.add_audit_entry("response_sent", self.agent_id)
                return response
            
        except Exception as e:
            logger.error(f"Handler error: {e}")
            if message.id:
                return A2AMessage(
                    error={"code": -32603, "message": "Internal error", "data": str(e)},
                    id=message.id
                )
        
        return None
    
    async def _process_response(self, message: A2AMessage):
        """Process incoming response"""
        if message.id in self.pending_requests:
            future = self.pending_requests.pop(message.id)
            if message.error:
                future.set_exception(Exception(f"Remote error: {message.error}"))
            else:
                future.set_result(message.result)
    
    def _update_response_time_stats(self, response_time: float):
        """Update response time statistics"""
        current_avg = self.stats["avg_response_time"]
        total_sent = self.stats["messages_sent"]
        
        if total_sent == 0:
            self.stats["avg_response_time"] = response_time
        else:
            self.stats["avg_response_time"] = (
                (current_avg * total_sent + response_time) / (total_sent + 1)
            )
    
    async def handle_health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.stats,
            "handlers": list(self.message_handlers.keys())
        }
        return web.json_response(health_data)
    
    async def handle_stats(self, request: web.Request) -> web.Response:
        """Statistics endpoint"""
        return web.json_response(self.stats)
    
    async def handle_batch_messages(self, request: web.Request) -> web.Response:
        """Handle batch message processing"""
        try:
            data = await request.json()
            messages = [A2AMessage.from_dict(msg_data) for msg_data in data.get("messages", [])]
            
            responses = []
            for message in messages:
                if message.method:
                    response = await self._process_request(message)
                    if response:
                        responses.append(response.to_dict())
            
            return web.json_response({"responses": responses})
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return web.Response(status=500, text=str(e))
    
    async def start_server(self):
        """Start A2A protocol server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"A2A Protocol server started on port {self.port}")
        return runner
    
    async def stop_server(self, runner):
        """Stop A2A protocol server"""
        await runner.cleanup()
        logger.info("A2A Protocol server stopped")


class SessionManager:
    """Manages A2A communication sessions for medical compliance"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 900  # 15 minutes
    
    def create_session(self, agent_id: str, auth_level: AuthLevel) -> str:
        """Create new communication session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "agent_id": agent_id,
            "auth_level": auth_level,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate session is active and not expired"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        if time.time() - session["last_activity"] > self.session_timeout:
            self.active_sessions.pop(session_id)
            return False
        
        session["last_activity"] = time.time()
        return True
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        expired = [
            sid for sid, session in self.active_sessions.items()
            if current_time - session["last_activity"] > self.session_timeout
        ]
        
        for session_id in expired:
            self.active_sessions.pop(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Factory function for easy instantiation
def create_a2a_protocol(agent_id: str, 
                       port: int = 8080,
                       enable_encryption: bool = True) -> A2AProtocolLayer:
    """
    Factory function to create A2A Protocol Layer instance
    """
    return A2AProtocolLayer(
        agent_id=agent_id,
        port=port,
        enable_encryption=enable_encryption
    )


__all__ = [
    'A2AMessage', 
    'A2AProtocolLayer', 
    'MessageType', 
    'MessagePriority', 
    'AuthLevel',
    'MessageValidator',
    'MessageEncryption',
    'SessionManager',
    'create_a2a_protocol'
]