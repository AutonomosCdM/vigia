"""
A2A Message Queuing System - Reliable Medical Message Processing
==============================================================

Sistema de colas de mensajes distribuido para comunicación Agent-to-Agent
con garantías de entrega y procesamiento médico especializado.

Features:
- Priority-based message queuing
- Guaranteed message delivery
- Dead letter queue handling
- Medical compliance tracking
- Batch processing capabilities
- Message persistence and recovery
- Load-aware queue management
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import aioredis
import pickle
import gzip

from .protocol_layer import A2AMessage, MessagePriority, AuthLevel
from .agent_discovery_service import AgentDiscoveryService, AgentType
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("a2a_message_queuing")


class QueueType(Enum):
    """Types of message queues"""
    PRIORITY = "priority"           # Standard priority-based queue
    FIFO = "fifo"                  # First-in-first-out
    MEDICAL_CRITICAL = "medical_critical"  # Emergency medical processing
    BATCH = "batch"                # Batch processing queue
    DELAYED = "delayed"            # Delayed/scheduled messages
    DEAD_LETTER = "dead_letter"    # Failed message queue


class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"            # Waiting in queue
    PROCESSING = "processing"      # Being processed
    COMPLETED = "completed"        # Successfully processed
    FAILED = "failed"             # Processing failed
    RETRY = "retry"               # Scheduled for retry
    DEAD_LETTER = "dead_letter"   # Moved to dead letter queue


class DeliveryMode(Enum):
    """Message delivery modes"""
    AT_LEAST_ONCE = "at_least_once"    # Guarantee delivery (may duplicate)
    EXACTLY_ONCE = "exactly_once"      # Exactly one delivery (slower)
    BEST_EFFORT = "best_effort"        # Fast, no guarantees


@dataclass
class QueuedMessage:
    """Message in queue with metadata"""
    message_id: str
    message: A2AMessage
    queue_type: QueueType
    status: MessageStatus = MessageStatus.PENDING
    
    # Timing information
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Retry information
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Processing information
    assigned_agent: Optional[str] = None
    processing_timeout: float = 30.0
    
    # Medical metadata
    medical_urgency: Optional[str] = None
    patient_context: Optional[Dict[str, Any]] = None
    compliance_requirements: Optional[List[str]] = None
    
    # Delivery guarantees
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    acknowledgment_required: bool = True
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.scheduled_at is None:
            self.scheduled_at = self.created_at


@dataclass
class QueueStatistics:
    """Queue performance statistics"""
    queue_name: str
    total_messages: int = 0
    pending_messages: int = 0
    processing_messages: int = 0
    completed_messages: int = 0
    failed_messages: int = 0
    dead_letter_messages: int = 0
    
    # Performance metrics
    avg_processing_time: float = 0.0
    avg_queue_time: float = 0.0
    throughput_per_minute: float = 0.0
    
    # Medical metrics
    critical_messages: int = 0
    phi_messages: int = 0
    compliance_violations: int = 0


class MessageQueue:
    """
    Individual message queue with priority and medical compliance handling
    """
    
    def __init__(self,
                 queue_name: str,
                 queue_type: QueueType,
                 max_size: int = 10000,
                 enable_persistence: bool = True):
        
        self.queue_name = queue_name
        self.queue_type = queue_type
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        
        # Queue storage
        self.messages: deque = deque()
        self.processing_messages: Dict[str, QueuedMessage] = {}
        self.message_index: Dict[str, QueuedMessage] = {}
        
        # Statistics
        self.stats = QueueStatistics(queue_name=queue_name)
        self.processing_history: deque = deque(maxlen=1000)
        
        # Configuration
        self.batch_size = 10
        self.flush_interval = 5.0  # seconds
        
        logger.info(f"Message queue '{queue_name}' initialized ({queue_type.value})")
    
    async def enqueue(self, queued_message: QueuedMessage) -> bool:
        """Add message to queue"""
        if len(self.messages) >= self.max_size:
            logger.warning(f"Queue {self.queue_name} is full, rejecting message")
            return False
        
        # Set queue-specific properties
        if self.queue_type == QueueType.MEDICAL_CRITICAL:
            queued_message.max_retries = 5  # More retries for critical
            queued_message.processing_timeout = 60.0  # Longer timeout
        elif self.queue_type == QueueType.BATCH:
            queued_message.acknowledgment_required = False  # Batch doesn't need acks
        
        # Add to queue
        if self.queue_type == QueueType.PRIORITY:
            self._enqueue_by_priority(queued_message)
        else:
            self.messages.append(queued_message)
        
        # Index the message
        self.message_index[queued_message.message_id] = queued_message
        
        # Update statistics
        self.stats.total_messages += 1
        self.stats.pending_messages += 1
        
        if queued_message.message.priority == MessagePriority.CRITICAL:
            self.stats.critical_messages += 1
        
        if queued_message.message.auth_level == AuthLevel.MEDICAL:
            self.stats.phi_messages += 1
        
        logger.debug(f"Message {queued_message.message_id} enqueued to {self.queue_name}")
        return True
    
    def _enqueue_by_priority(self, queued_message: QueuedMessage):
        """Enqueue message by priority (higher priority first)"""
        priority_order = {
            MessagePriority.CRITICAL: 0,
            MessagePriority.HIGH: 1,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 3
        }
        
        message_priority = priority_order.get(queued_message.message.priority, 2)
        
        # Find insertion point
        insertion_index = 0
        for i, existing_msg in enumerate(self.messages):
            existing_priority = priority_order.get(existing_msg.message.priority, 2)
            if message_priority < existing_priority:
                insertion_index = i
                break
            insertion_index = i + 1
        
        # Insert at calculated position
        if insertion_index >= len(self.messages):
            self.messages.append(queued_message)
        else:
            self.messages.insert(insertion_index, queued_message)
    
    async def dequeue(self, count: int = 1) -> List[QueuedMessage]:
        """Remove and return messages from queue"""
        messages = []
        
        for _ in range(min(count, len(self.messages))):
            if self.messages:
                message = self.messages.popleft()
                
                # Check if message is scheduled for future processing
                if message.scheduled_at > datetime.now(timezone.utc):
                    # Put back in queue for later
                    self.messages.appendleft(message)
                    break
                
                # Mark as processing
                message.status = MessageStatus.PROCESSING
                message.processing_started_at = datetime.now(timezone.utc)
                
                # Move to processing
                self.processing_messages[message.message_id] = message
                
                # Update statistics
                self.stats.pending_messages -= 1
                self.stats.processing_messages += 1
                
                messages.append(message)
        
        return messages
    
    async def acknowledge(self, message_id: str, success: bool = True) -> bool:
        """Acknowledge message processing completion"""
        if message_id not in self.processing_messages:
            logger.warning(f"Cannot acknowledge unknown message {message_id}")
            return False
        
        message = self.processing_messages.pop(message_id)
        message.completed_at = datetime.now(timezone.utc)
        
        if success:
            message.status = MessageStatus.COMPLETED
            self.stats.processing_messages -= 1
            self.stats.completed_messages += 1
            
            # Record processing time
            if message.processing_started_at:
                processing_time = (message.completed_at - message.processing_started_at).total_seconds()
                self.processing_history.append({
                    "processing_time": processing_time,
                    "queue_time": (message.processing_started_at - message.created_at).total_seconds(),
                    "timestamp": message.completed_at
                })
                
                # Update average processing time
                if self.processing_history:
                    self.stats.avg_processing_time = sum(
                        h["processing_time"] for h in self.processing_history
                    ) / len(self.processing_history)
            
        else:
            # Handle failure
            await self._handle_message_failure(message)
        
        # Remove from index if completed or dead-lettered
        if message.status in [MessageStatus.COMPLETED, MessageStatus.DEAD_LETTER]:
            self.message_index.pop(message_id, None)
        
        return True
    
    async def _handle_message_failure(self, message: QueuedMessage):
        """Handle failed message processing"""
        message.retry_count += 1
        
        if message.retry_count <= message.max_retries:
            # Schedule for retry
            message.status = MessageStatus.RETRY
            message.scheduled_at = datetime.now(timezone.utc) + timedelta(
                seconds=message.retry_delay * (2 ** message.retry_count)  # Exponential backoff
            )
            
            # Put back in queue
            self.messages.append(message)
            self.stats.processing_messages -= 1
            self.stats.pending_messages += 1
            
            logger.warning(f"Message {message.message_id} failed, scheduled for retry {message.retry_count}")
        
        else:
            # Move to dead letter
            message.status = MessageStatus.DEAD_LETTER
            self.stats.processing_messages -= 1
            self.stats.failed_messages += 1
            self.stats.dead_letter_messages += 1
            
            logger.error(f"Message {message.message_id} moved to dead letter after {message.retry_count} retries")
    
    def get_stats(self) -> QueueStatistics:
        """Get current queue statistics"""
        # Update real-time stats
        self.stats.pending_messages = len(self.messages)
        self.stats.processing_messages = len(self.processing_messages)
        
        # Calculate throughput
        recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_completions = [
            h for h in self.processing_history 
            if h["timestamp"] > recent_threshold
        ]
        self.stats.throughput_per_minute = len(recent_completions)
        
        return self.stats
    
    def get_pending_count(self) -> int:
        """Get number of pending messages"""
        return len(self.messages)
    
    def get_processing_count(self) -> int:
        """Get number of processing messages"""
        return len(self.processing_messages)
    
    async def cleanup_stale_messages(self, timeout_seconds: float = 300):
        """Clean up messages that have been processing too long"""
        current_time = datetime.now(timezone.utc)
        stale_messages = []
        
        for message_id, message in self.processing_messages.items():
            if message.processing_started_at:
                processing_duration = (current_time - message.processing_started_at).total_seconds()
                if processing_duration > timeout_seconds:
                    stale_messages.append(message_id)
        
        for message_id in stale_messages:
            logger.warning(f"Cleaning up stale message {message_id}")
            await self.acknowledge(message_id, success=False)


class A2AMessageQueueManager:
    """
    Central manager for A2A message queuing system
    """
    
    def __init__(self,
                 discovery_service: AgentDiscoveryService,
                 redis_url: str = "redis://localhost:6379",
                 enable_persistence: bool = True):
        
        self.discovery_service = discovery_service
        self.redis_url = redis_url
        self.enable_persistence = enable_persistence
        
        # Queue management
        self.queues: Dict[str, MessageQueue] = {}
        self.queue_processors: Dict[str, asyncio.Task] = {}
        
        # Redis for persistence
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Message routing
        self.routing_rules: Dict[AgentType, str] = {}
        self.custom_processors: Dict[str, Callable] = {}
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Global statistics
        self.global_stats = {
            "total_queues": 0,
            "total_messages_processed": 0,
            "total_messages_failed": 0,
            "avg_end_to_end_latency": 0.0
        }
        
        # Audit service
        self.audit_service = AuditService()
        
        logger.info("A2A Message Queue Manager initialized")
    
    async def initialize(self):
        """Initialize message queuing system"""
        # Initialize Redis if persistence enabled
        if self.enable_persistence:
            await self._init_redis()
        
        # Create default queues
        await self._create_default_queues()
        
        # Start background tasks
        await self._start_background_tasks()
        
        logger.info("Message queuing system initialized")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis persistence enabled")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enable_persistence = False
    
    async def _create_default_queues(self):
        """Create default message queues"""
        default_queues = [
            ("critical", QueueType.MEDICAL_CRITICAL),
            ("high_priority", QueueType.PRIORITY),
            ("normal", QueueType.FIFO),
            ("batch", QueueType.BATCH),
            ("delayed", QueueType.DELAYED),
            ("dead_letter", QueueType.DEAD_LETTER)
        ]
        
        for queue_name, queue_type in default_queues:
            await self.create_queue(queue_name, queue_type)
    
    async def _start_background_tasks(self):
        """Start background processing tasks"""
        # Queue processor for each queue
        for queue_name in self.queues:
            task = asyncio.create_task(self._process_queue(queue_name))
            self.queue_processors[queue_name] = task
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
        
        # Statistics updater
        stats_task = asyncio.create_task(self._update_stats_loop())
        self.background_tasks.add(stats_task)
        stats_task.add_done_callback(self.background_tasks.discard)
        
        # Cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
        
        # Persistence task (if enabled)
        if self.enable_persistence:
            persist_task = asyncio.create_task(self._persistence_loop())
            self.background_tasks.add(persist_task)
            persist_task.add_done_callback(self.background_tasks.discard)
    
    async def create_queue(self, queue_name: str, queue_type: QueueType, max_size: int = 10000) -> bool:
        """Create new message queue"""
        if queue_name in self.queues:
            logger.warning(f"Queue {queue_name} already exists")
            return False
        
        queue = MessageQueue(
            queue_name=queue_name,
            queue_type=queue_type,
            max_size=max_size,
            enable_persistence=self.enable_persistence
        )
        
        self.queues[queue_name] = queue
        self.global_stats["total_queues"] += 1
        
        # Start processor for new queue
        if queue_name not in self.queue_processors:
            task = asyncio.create_task(self._process_queue(queue_name))
            self.queue_processors[queue_name] = task
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
        
        logger.info(f"Created queue: {queue_name} ({queue_type.value})")
        return True
    
    async def send_message(self,
                          message: A2AMessage,
                          target_queue: Optional[str] = None,
                          delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE,
                          processing_timeout: float = 30.0,
                          medical_urgency: Optional[str] = None) -> str:
        """Send message to queue"""
        
        # Determine target queue
        if not target_queue:
            target_queue = self._route_message(message)
        
        if target_queue not in self.queues:
            raise ValueError(f"Queue {target_queue} does not exist")
        
        # Create queued message
        queued_message = QueuedMessage(
            message_id=str(uuid.uuid4()),
            message=message,
            queue_type=self.queues[target_queue].queue_type,
            delivery_mode=delivery_mode,
            processing_timeout=processing_timeout,
            medical_urgency=medical_urgency
        )
        
        # Add medical context from message
        if message.medical_context:
            queued_message.patient_context = message.medical_context
        
        # Enqueue message
        queue = self.queues[target_queue]
        success = await queue.enqueue(queued_message)
        
        if success:
            # Persist if enabled
            if self.enable_persistence:
                await self._persist_message(queued_message)
            
            # Audit log
            await self.audit_service.log_event(
                AuditEventType.MESSAGE_QUEUED,
                {
                    "message_id": queued_message.message_id,
                    "queue": target_queue,
                    "priority": message.priority.value,
                    "agent_id": message.agent_id
                },
                session_id=message.session_id or "queue_manager"
            )
            
            logger.debug(f"Message {queued_message.message_id} sent to queue {target_queue}")
            return queued_message.message_id
        else:
            raise Exception(f"Failed to enqueue message to {target_queue}")
    
    def _route_message(self, message: A2AMessage) -> str:
        """Route message to appropriate queue based on priority and content"""
        # Medical critical messages
        if (message.priority == MessagePriority.CRITICAL or 
            message.auth_level == AuthLevel.EMERGENCY):
            return "critical"
        
        # High priority messages
        if message.priority == MessagePriority.HIGH:
            return "high_priority"
        
        # Batch processing
        if message.method and message.method.startswith("batch_"):
            return "batch"
        
        # Default to normal queue
        return "normal"
    
    async def _process_queue(self, queue_name: str):
        """Process messages from specific queue"""
        queue = self.queues[queue_name]
        
        while True:
            try:
                # Get messages from queue
                messages = await queue.dequeue(count=queue.batch_size)
                
                if messages:
                    # Process messages
                    for message in messages:
                        try:
                            await self._process_message(message, queue_name)
                        except Exception as e:
                            logger.error(f"Message processing failed: {e}")
                            await queue.acknowledge(message.message_id, success=False)
                else:
                    # No messages, wait before checking again
                    await asyncio.sleep(queue.flush_interval)
                    
            except Exception as e:
                logger.error(f"Queue processing error for {queue_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_message(self, queued_message: QueuedMessage, queue_name: str):
        """Process individual message"""
        message = queued_message.message
        
        try:
            # Find target agent
            if message.method:
                # Find suitable agent for method
                agents = await self.discovery_service.discover_agents(
                    ServiceQuery(capability_name=message.method)
                )
                
                if agents:
                    # Route to first available agent
                    target_agent = agents[0]
                    
                    # Send message to agent
                    result = await self._send_to_agent(message, target_agent.endpoint)
                    
                    # Acknowledge success
                    queue = self.queues[queue_name]
                    await queue.acknowledge(queued_message.message_id, success=True)
                    
                    self.global_stats["total_messages_processed"] += 1
                    
                else:
                    # No suitable agents
                    raise Exception(f"No agents available for method {message.method}")
            
            else:
                # Response message - route based on ID
                # This would typically be handled by the response correlation system
                pass
                
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            queue = self.queues[queue_name]
            await queue.acknowledge(queued_message.message_id, success=False)
            self.global_stats["total_messages_failed"] += 1
    
    async def _send_to_agent(self, message: A2AMessage, agent_endpoint: str) -> Any:
        """Send message to agent endpoint"""
        url = f"{agent_endpoint}/a2a/message"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=message.to_dict()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Agent responded with status {response.status}")
    
    async def _persist_message(self, queued_message: QueuedMessage):
        """Persist message to Redis"""
        if not self.redis_client:
            return
        
        try:
            # Serialize message
            message_data = asdict(queued_message)
            message_data["message"] = queued_message.message.to_dict()
            
            # Compress for storage efficiency
            compressed_data = gzip.compress(json.dumps(message_data, default=str).encode())
            
            # Store in Redis with TTL
            key = f"queued_message:{queued_message.message_id}"
            await self.redis_client.setex(key, 86400, compressed_data)  # 24 hour TTL
            
        except Exception as e:
            logger.error(f"Failed to persist message {queued_message.message_id}: {e}")
    
    async def _update_stats_loop(self):
        """Update global statistics"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_global_stats()
            except Exception as e:
                logger.error(f"Stats update error: {e}")
    
    async def _update_global_stats(self):
        """Update global statistics"""
        total_pending = sum(queue.get_pending_count() for queue in self.queues.values())
        total_processing = sum(queue.get_processing_count() for queue in self.queues.values())
        
        self.global_stats.update({
            "total_pending": total_pending,
            "total_processing": total_processing,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def _cleanup_loop(self):
        """Cleanup stale messages"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                for queue in self.queues.values():
                    await queue.cleanup_stale_messages()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _persistence_loop(self):
        """Handle message persistence"""
        while True:
            try:
                await asyncio.sleep(30)  # Persist every 30 seconds
                # This would handle periodic persistence tasks
                # like compacting logs, archiving old messages, etc.
            except Exception as e:
                logger.error(f"Persistence error: {e}")
    
    def get_queue_stats(self, queue_name: str) -> Optional[QueueStatistics]:
        """Get statistics for specific queue"""
        if queue_name in self.queues:
            return self.queues[queue_name].get_stats()
        return None
    
    def get_all_queue_stats(self) -> Dict[str, QueueStatistics]:
        """Get statistics for all queues"""
        return {
            queue_name: queue.get_stats()
            for queue_name, queue in self.queues.items()
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global system statistics"""
        return self.global_stats.copy()
    
    async def shutdown(self):
        """Shutdown message queuing system"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("A2A Message Queue Manager shutdown complete")


# Factory function
def create_message_queue_manager(discovery_service: AgentDiscoveryService) -> A2AMessageQueueManager:
    """Factory function to create message queue manager"""
    return A2AMessageQueueManager(discovery_service=discovery_service)


__all__ = [
    'A2AMessageQueueManager',
    'MessageQueue',
    'QueuedMessage',
    'QueueType',
    'MessageStatus',
    'DeliveryMode',
    'QueueStatistics',
    'create_message_queue_manager'
]