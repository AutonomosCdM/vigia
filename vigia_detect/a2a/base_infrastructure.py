"""
A2A (Agent-to-Agent) Base Infrastructure for Vigia Medical System
================================================================

Implements the core A2A protocol infrastructure with JSON-RPC 2.0 communication,
authentication, task management, and medical compliance for distributed agents.

Based on Google A2A specification:
https://google-a2a.github.io/A2A/specification/
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from aiohttp import web, ClientSession
import jwt
import hashlib
from cryptography.fernet import Fernet

# Configure logging
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """A2A Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuthenticationMethod(Enum):
    """Authentication methods supported"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"


class CommunicationMode(Enum):
    """A2A Communication modes"""
    REQUEST_RESPONSE = "request_response"
    STREAMING = "streaming"
    PUSH_NOTIFICATIONS = "push_notifications"


@dataclass
class AgentCard:
    """
    A2A Agent Card for capability discovery.
    Defines what capabilities an agent provides.
    """
    agent_id: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    authentication: Dict[str, Any]
    supported_modes: List[str]
    medical_specialization: Optional[str] = None
    compliance_certifications: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class A2ATask:
    """
    A2A Task with complete lifecycle management.
    Represents a unit of work between agents.
    """
    task_id: str
    agent_from: str
    agent_to: str
    task_type: str
    payload: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    medical_context: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, critical
    timeout_seconds: int = 300  # 5 minutes default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['status'] = self.status.value
        return data


class MedicalComplianceValidator:
    """
    Validates medical compliance for A2A communications.
    Ensures HIPAA and medical regulation compliance.
    """
    
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Medical data patterns that require encryption
        self.phi_patterns = [
            'patient_id', 'patient_code', 'patient_name',
            'medical_record', 'ssn', 'insurance_id'
        ]
    
    def validate_medical_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize medical payload for A2A transmission.
        
        Args:
            payload: Raw payload potentially containing PHI
            
        Returns:
            Sanitized payload with PHI encrypted/tokenized
        """
        sanitized = payload.copy()
        
        # Encrypt PHI fields
        for key, value in payload.items():
            if any(phi_pattern in key.lower() for phi_pattern in self.phi_patterns):
                if isinstance(value, str):
                    # Encrypt PHI data
                    encrypted_value = self.cipher.encrypt(value.encode()).decode()
                    sanitized[key] = f"ENCRYPTED:{encrypted_value}"
                    logger.info(f"Encrypted PHI field: {key}")
        
        # Add compliance metadata
        sanitized['_compliance'] = {
            'phi_encrypted': True,
            'encryption_timestamp': datetime.now().isoformat(),
            'regulatory_compliance': ['HIPAA', 'MINSAL'],
            'data_retention_policy': '7_years'
        }
        
        return sanitized
    
    def decrypt_medical_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt medical payload received via A2A.
        
        Args:
            payload: Payload with encrypted PHI
            
        Returns:
            Payload with decrypted PHI data
        """
        decrypted = payload.copy()
        
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("ENCRYPTED:"):
                try:
                    encrypted_data = value.replace("ENCRYPTED:", "").encode()
                    decrypted_value = self.cipher.decrypt(encrypted_data).decode()
                    decrypted[key] = decrypted_value
                    logger.info(f"Decrypted PHI field: {key}")
                except Exception as e:
                    logger.error(f"Failed to decrypt PHI field {key}: {str(e)}")
                    decrypted[key] = "[DECRYPTION_FAILED]"
        
        return decrypted


class A2AAuthenticationManager:
    """
    Manages authentication for A2A communications.
    Supports API keys, OAuth 2.0, and JWT tokens.
    """
    
    def __init__(self, secret_key: str = "vigia_a2a_secret_key"):
        self.secret_key = secret_key
        self.api_keys = {}  # agent_id -> api_key mapping
        self.jwt_tokens = {}  # agent_id -> jwt_token mapping
        
        # Initialize with default medical agent API keys
        self._initialize_default_keys()
    
    def _initialize_default_keys(self):
        """Initialize default API keys for medical agents"""
        medical_agents = [
            'image_analysis_agent',
            'clinical_assessment_agent', 
            'protocol_agent',
            'communication_agent',
            'workflow_orchestration_agent',
            'master_medical_orchestrator'
        ]
        
        for agent_id in medical_agents:
            api_key = self._generate_api_key(agent_id)
            self.api_keys[agent_id] = api_key
            logger.info(f"Generated API key for {agent_id}")
    
    def _generate_api_key(self, agent_id: str) -> str:
        """Generate secure API key for agent"""
        # Create deterministic but secure API key
        raw_key = f"{agent_id}:{self.secret_key}:{datetime.now().strftime('%Y-%m-%d')}"
        return hashlib.sha256(raw_key.encode()).hexdigest()[:32]
    
    def generate_jwt_token(self, agent_id: str, capabilities: List[str]) -> str:
        """
        Generate JWT token for agent authentication.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            
        Returns:
            JWT token string
        """
        payload = {
            'agent_id': agent_id,
            'capabilities': capabilities,
            'issued_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'medical_authorized': True
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        self.jwt_tokens[agent_id] = token
        return token
    
    def validate_api_key(self, agent_id: str, provided_api_key: str) -> bool:
        """Validate API key for agent"""
        expected_key = self.api_keys.get(agent_id)
        return expected_key and expected_key == provided_api_key
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return payload.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.now() > expires_at:
                logger.warning("JWT token expired")
                return None
            
            return payload
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            return None
    
    def get_api_key(self, agent_id: str) -> Optional[str]:
        """Get API key for agent"""
        return self.api_keys.get(agent_id)


class A2ATaskManager:
    """
    Manages A2A task lifecycle with medical compliance.
    Handles task creation, status updates, and completion.
    """
    
    def __init__(self):
        self.tasks: Dict[str, A2ATask] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        
        # Medical priority queue
        self.priority_queues = {
            'critical': [],  # Emergency medical cases
            'high': [],      # Urgent medical attention
            'normal': [],    # Standard medical processing
            'low': []        # Routine checks
        }
    
    def create_task(self, agent_from: str, agent_to: str, task_type: str, 
                   payload: Dict[str, Any], priority: str = "normal",
                   medical_context: Optional[Dict[str, Any]] = None) -> A2ATask:
        """
        Create new A2A task with medical compliance.
        
        Args:
            agent_from: Source agent ID
            agent_to: Target agent ID  
            task_type: Type of task (e.g., 'image_analysis', 'clinical_assessment')
            payload: Task payload data
            priority: Task priority (low, normal, high, critical)
            medical_context: Medical context for compliance
            
        Returns:
            Created A2ATask object
        """
        task_id = str(uuid.uuid4())
        
        # Determine timeout based on medical priority
        timeout_map = {
            'critical': 60,     # 1 minute for emergencies
            'high': 180,        # 3 minutes for urgent cases
            'normal': 300,      # 5 minutes for standard cases
            'low': 600          # 10 minutes for routine
        }
        
        task = A2ATask(
            task_id=task_id,
            agent_from=agent_from,
            agent_to=agent_to,
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            medical_context=medical_context,
            priority=priority,
            timeout_seconds=timeout_map.get(priority, 300)
        )
        
        # Store task
        self.tasks[task_id] = task
        
        # Add to priority queue
        if priority in self.priority_queues:
            self.priority_queues[priority].append(task_id)
        
        logger.info(f"Created A2A task {task_id}: {agent_from} -> {agent_to} ({task_type})")
        return task
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result: Optional[Dict[str, Any]] = None,
                          error: Optional[str] = None) -> bool:
        """
        Update task status with audit trail.
        
        Args:
            task_id: Task identifier
            status: New status
            result: Task result (if completed)
            error: Error message (if failed)
            
        Returns:
            True if updated successfully
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        # Update task
        task.status = status
        task.updated_at = datetime.now()
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.error = error
        
        # Execute callback if registered
        callback = self.task_callbacks.get(task_id)
        if callback:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Task callback error for {task_id}: {str(e)}")
        
        logger.info(f"Updated task {task_id} status to {status.value}")
        return True
    
    def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_agent(self, agent_id: str, include_completed: bool = True) -> List[A2ATask]:
        """Get all tasks for specific agent"""
        tasks = []
        for task in self.tasks.values():
            if task.agent_to == agent_id or task.agent_from == agent_id:
                if include_completed or task.status != TaskStatus.COMPLETED:
                    tasks.append(task)
        return tasks
    
    def get_pending_tasks(self, agent_id: str) -> List[A2ATask]:
        """Get pending tasks for agent (prioritized)"""
        agent_tasks = self.get_tasks_by_agent(agent_id, include_completed=False)
        pending_tasks = [t for t in agent_tasks if t.status == TaskStatus.PENDING]
        
        # Sort by priority (critical first)
        priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t.priority, 99))
        
        return pending_tasks
    
    def register_task_callback(self, task_id: str, callback: Callable):
        """Register callback for task status changes"""
        self.task_callbacks[task_id] = callback
    
    def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """Clean up completed tasks older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                and task.completed_at and task.completed_at < cutoff_time):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            logger.info(f"Cleaned up completed task {task_id}")


class A2AServer:
    """
    Base A2A Server implementing JSON-RPC 2.0 protocol.
    Handles agent registration, authentication, and task processing.
    """
    
    def __init__(self, agent_card: AgentCard, port: int = 8080):
        self.agent_card = agent_card
        self.port = port
        self.app = web.Application()
        self.auth_manager = A2AAuthenticationManager()
        self.task_manager = A2ATaskManager()
        self.compliance_validator = MedicalComplianceValidator()
        
        # Registered agent endpoints
        self.agent_registry: Dict[str, AgentCard] = {}
        
        # Setup routes
        self._setup_routes()
        
        # Task processing handlers
        self.task_handlers: Dict[str, Callable] = {}
    
    def _setup_routes(self):
        """Setup HTTP routes for A2A protocol"""
        # Core A2A endpoints
        self.app.router.add_get('/agent-card', self._get_agent_card)
        self.app.router.add_post('/tasks', self._create_task)
        self.app.router.add_get('/tasks/{task_id}', self._get_task)
        self.app.router.add_put('/tasks/{task_id}/status', self._update_task_status)
        
        # Agent registry endpoints
        self.app.router.add_post('/agents/register', self._register_agent)
        self.app.router.add_get('/agents', self._list_agents)
        
        # Health and status
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/status', self._get_status)
        
        # Authentication endpoints
        self.app.router.add_post('/auth/token', self._generate_token)
    
    async def _get_agent_card(self, request: web.Request) -> web.Response:
        """Return agent card for capability discovery"""
        return web.json_response(self.agent_card.to_dict())
    
    async def _create_task(self, request: web.Request) -> web.Response:
        """Create new A2A task"""
        try:
            # Authenticate request
            if not await self._authenticate_request(request):
                return web.json_response({'error': 'Authentication failed'}, status=401)
            
            # Parse request
            data = await request.json()
            agent_from = data.get('agent_from')
            task_type = data.get('task_type')
            payload = data.get('payload', {})
            priority = data.get('priority', 'normal')
            medical_context = data.get('medical_context')
            
            # Validate medical payload
            if medical_context:
                payload = self.compliance_validator.validate_medical_payload(payload)
            
            # Create task
            task = self.task_manager.create_task(
                agent_from=agent_from,
                agent_to=self.agent_card.agent_id,
                task_type=task_type,
                payload=payload,
                priority=priority,
                medical_context=medical_context
            )
            
            # Process task asynchronously
            asyncio.create_task(self._process_task(task))
            
            return web.json_response({
                'task_id': task.task_id,
                'status': task.status.value,
                'created_at': task.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _get_task(self, request: web.Request) -> web.Response:
        """Get task status and result"""
        task_id = request.match_info['task_id']
        task = self.task_manager.get_task(task_id)
        
        if not task:
            return web.json_response({'error': 'Task not found'}, status=404)
        
        return web.json_response(task.to_dict())
    
    async def _update_task_status(self, request: web.Request) -> web.Response:
        """Update task status"""
        try:
            task_id = request.match_info['task_id']
            data = await request.json()
            
            status_str = data.get('status')
            status = TaskStatus(status_str)
            result = data.get('result')
            error = data.get('error')
            
            success = self.task_manager.update_task_status(task_id, status, result, error)
            
            if success:
                return web.json_response({'message': 'Task updated successfully'})
            else:
                return web.json_response({'error': 'Task not found'}, status=404)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def _register_agent(self, request: web.Request) -> web.Response:
        """Register external agent for communication"""
        try:
            data = await request.json()
            agent_card = AgentCard(**data)
            
            self.agent_registry[agent_card.agent_id] = agent_card
            
            # Generate API key for agent
            api_key = self.auth_manager._generate_api_key(agent_card.agent_id)
            self.auth_manager.api_keys[agent_card.agent_id] = api_key
            
            return web.json_response({
                'message': f'Agent {agent_card.agent_id} registered successfully',
                'api_key': api_key
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _list_agents(self, request: web.Request) -> web.Response:
        """List registered agents"""
        agents = {agent_id: card.to_dict() for agent_id, card in self.agent_registry.items()}
        return web.json_response(agents)
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'agent_id': self.agent_card.agent_id,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _get_status(self, request: web.Request) -> web.Response:
        """Get server status"""
        pending_tasks = len([t for t in self.task_manager.tasks.values() 
                           if t.status == TaskStatus.PENDING])
        
        return web.json_response({
            'agent_id': self.agent_card.agent_id,
            'agent_card': self.agent_card.to_dict(),
            'registered_agents': len(self.agent_registry),
            'pending_tasks': pending_tasks,
            'total_tasks': len(self.task_manager.tasks),
            'uptime': datetime.now().isoformat()
        })
    
    async def _generate_token(self, request: web.Request) -> web.Response:
        """Generate JWT token for agent"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')
            api_key = data.get('api_key')
            
            # Validate API key
            if not self.auth_manager.validate_api_key(agent_id, api_key):
                return web.json_response({'error': 'Invalid credentials'}, status=401)
            
            # Get agent capabilities
            agent_card = self.agent_registry.get(agent_id)
            capabilities = agent_card.capabilities if agent_card else []
            
            # Generate JWT token
            token = self.auth_manager.generate_jwt_token(agent_id, capabilities)
            
            return web.json_response({
                'token': token,
                'expires_in': 86400  # 24 hours
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _authenticate_request(self, request: web.Request) -> bool:
        """Authenticate incoming request"""
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Extract agent ID from request or use a default validation
            agent_id = request.headers.get('X-Agent-ID')
            if agent_id and self.auth_manager.validate_api_key(agent_id, api_key):
                return True
        
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            payload = self.auth_manager.validate_jwt_token(token)
            if payload:
                return True
        
        return False
    
    async def _process_task(self, task: A2ATask):
        """Process A2A task asynchronously"""
        try:
            # Update status to in_progress
            self.task_manager.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
            
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Decrypt medical payload if needed
            payload = task.payload
            if task.medical_context:
                payload = self.compliance_validator.decrypt_medical_payload(payload)
            
            # Execute handler
            result = await handler(payload, task.medical_context)
            
            # Update task with result
            self.task_manager.update_task_status(task.task_id, TaskStatus.COMPLETED, result)
            
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            self.task_manager.update_task_status(task.task_id, TaskStatus.FAILED, error=str(e))
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register handler for specific task type"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def start(self):
        """Start A2A server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"A2A Server started for {self.agent_card.agent_id} on port {self.port}")
        print(f"Agent Card available at: http://localhost:{self.port}/agent-card")
        print(f"Health check at: http://localhost:{self.port}/health")


# Export main classes
__all__ = [
    'AgentCard', 'A2ATask', 'TaskStatus', 'CommunicationMode',
    'MedicalComplianceValidator', 'A2AAuthenticationManager', 
    'A2ATaskManager', 'A2AServer'
]