"""
A2A Task Lifecycle Manager for Vigia Medical System
===================================================

Advanced task management system implementing complete A2A task lifecycles
with medical compliance, monitoring, and automated escalation for critical
medical cases.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from vigia_detect.a2a.base_infrastructure import A2ATask, TaskStatus, A2ATaskManager
from vigia_detect.utils.audit_service import AuditService

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Medical task priority levels"""
    CRITICAL = "critical"    # Emergency - process immediately
    HIGH = "high"           # Urgent medical attention needed
    NORMAL = "normal"       # Standard medical processing
    LOW = "low"            # Routine checks and maintenance


class TaskStage(Enum):
    """Task processing stages"""
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    VALIDATING = "validating"
    ESCALATING = "escalating"
    COMPLETING = "completing"
    ARCHIVED = "archived"


class EscalationTrigger(Enum):
    """Escalation trigger types"""
    TIMEOUT = "timeout"
    LOW_CONFIDENCE = "low_confidence"
    CRITICAL_RESULT = "critical_result"
    PROCESSING_ERROR = "processing_error"
    AGENT_FAILURE = "agent_failure"
    MANUAL_REQUEST = "manual_request"


@dataclass
class TaskLifecycleEvent:
    """Represents an event in task lifecycle"""
    event_id: str
    task_id: str
    event_type: str
    stage: TaskStage
    timestamp: datetime
    agent_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    medical_context: Optional[Dict[str, Any]] = None


@dataclass
class MedicalTaskContext:
    """Medical context for task processing with PHI tokenization"""
    token_id: str  # Batman token (NO PHI)
    patient_alias: str  # Patient alias (e.g., "Batman")
    case_priority: TaskPriority
    medical_urgency: str  # ROUTINE, URGENT, CRITICAL, EMERGENCY
    anatomical_location: Optional[str] = None
    risk_factors: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    requires_specialist: bool = False
    max_processing_time: int = 300  # seconds
    escalation_contacts: List[str] = field(default_factory=list)
    phi_compliant: bool = True  # Indicates this uses tokenized data


@dataclass
class TaskDependency:
    """Represents dependencies between tasks"""
    task_id: str
    depends_on: List[str]  # List of task IDs this task depends on
    dependency_type: str   # "sequential", "parallel", "conditional"
    condition: Optional[Dict[str, Any]] = None


class MedicalTaskLifecycleManager:
    """
    Advanced task lifecycle manager for medical A2A tasks.
    Implements complete lifecycle with medical compliance and monitoring.
    """
    
    def __init__(self):
        self.base_task_manager = A2ATaskManager()
        self.audit_service = AuditService()
        
        # Enhanced task tracking
        self.task_events: Dict[str, List[TaskLifecycleEvent]] = {}
        self.task_contexts: Dict[str, MedicalTaskContext] = {}
        self.task_dependencies: Dict[str, TaskDependency] = {}
        
        # Medical priority queues with enhanced metadata
        self.priority_queues = {
            TaskPriority.CRITICAL: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(), 
            TaskPriority.NORMAL: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
        
        # Task monitoring and escalation
        self.task_timeouts: Dict[str, asyncio.Task] = {}
        self.escalation_handlers: Dict[EscalationTrigger, Callable] = {}
        self.task_processors: Dict[str, asyncio.Task] = {}
        
        # Medical compliance tracking
        self.compliance_violations: List[Dict[str, Any]] = []
        self.processing_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'escalated_tasks': 0,
            'avg_processing_time': 0.0,
            'critical_tasks_processed': 0
        }
        
        # Initialize default escalation handlers
        self._initialize_escalation_handlers()
        
        # Start background processors
        self._start_background_processors()
    
    def _initialize_escalation_handlers(self):
        """Initialize default escalation handlers"""
        self.escalation_handlers = {
            EscalationTrigger.TIMEOUT: self._handle_timeout_escalation,
            EscalationTrigger.LOW_CONFIDENCE: self._handle_confidence_escalation,
            EscalationTrigger.CRITICAL_RESULT: self._handle_critical_escalation,
            EscalationTrigger.PROCESSING_ERROR: self._handle_error_escalation,
            EscalationTrigger.AGENT_FAILURE: self._handle_agent_failure_escalation,
            EscalationTrigger.MANUAL_REQUEST: self._handle_manual_escalation
        }
    
    def _start_background_processors(self):
        """Start background task processors for each priority level"""
        for priority in TaskPriority:
            processor = asyncio.create_task(
                self._process_priority_queue(priority)
            )
            self.task_processors[priority.value] = processor
            logger.info(f"Started processor for {priority.value} priority tasks")
    
    async def create_medical_task(
        self,
        agent_from: str,
        agent_to: str, 
        task_type: str,
        payload: Dict[str, Any],
        medical_context: MedicalTaskContext,
        dependencies: Optional[List[str]] = None
    ) -> A2ATask:
        """
        Create medical task with enhanced lifecycle management.
        
        Args:
            agent_from: Source agent ID
            agent_to: Target agent ID
            task_type: Type of medical task
            payload: Task payload data
            medical_context: Medical context and urgency
            dependencies: List of task IDs this task depends on
            
        Returns:
            Created A2ATask with lifecycle tracking
        """
        
        # Create base task
        task = self.base_task_manager.create_task(
            agent_from=agent_from,
            agent_to=agent_to,
            task_type=task_type,
            payload=payload,
            priority=medical_context.case_priority.value,
            medical_context=medical_context.__dict__
        )
        
        # Store medical context
        self.task_contexts[task.task_id] = medical_context
        
        # Setup dependencies if provided
        if dependencies:
            self.task_dependencies[task.task_id] = TaskDependency(
                task_id=task.task_id,
                depends_on=dependencies,
                dependency_type="sequential"
            )
        
        # Record creation event
        await self._record_lifecycle_event(
            task.task_id,
            "task_created",
            TaskStage.CREATED,
            agent_id=agent_from,
            details={
                'task_type': task_type,
                'medical_urgency': medical_context.medical_urgency,
                'max_processing_time': medical_context.max_processing_time
            }
        )
        
        # Setup timeout monitoring
        await self._setup_timeout_monitoring(task, medical_context)
        
        # Add to appropriate priority queue
        await self.priority_queues[medical_context.case_priority].put(task.task_id)
        
        # Record queuing event
        await self._record_lifecycle_event(
            task.task_id,
            "task_queued", 
            TaskStage.QUEUED,
            details={'priority': medical_context.case_priority.value}
        )
        
        # Update metrics
        self.processing_metrics['total_tasks'] += 1
        if medical_context.case_priority == TaskPriority.CRITICAL:
            self.processing_metrics['critical_tasks_processed'] += 1
        
        # Audit trail
        await self.audit_service.log_event(
            event_type='a2a_task_created',
            session_id=task.task_id,
            user_id=agent_from,
            resource_type='a2a_task',
            action='create',
            details={
                'task_type': task_type,
                'agent_from': agent_from,
                'agent_to': agent_to,
                'priority': medical_context.case_priority.value,
                'medical_urgency': medical_context.medical_urgency,
                'token_id': medical_context.token_id,
                'patient_alias': medical_context.patient_alias,
                'phi_compliant': medical_context.phi_compliant
            }
        )
        
        logger.info(f"Created medical task {task.task_id}: {task_type} ({medical_context.case_priority.value})")
        return task
    
    async def _setup_timeout_monitoring(self, task: A2ATask, medical_context: MedicalTaskContext):
        """Setup timeout monitoring for medical task"""
        timeout_seconds = medical_context.max_processing_time
        
        async def timeout_handler():
            await asyncio.sleep(timeout_seconds)
            
            # Check if task is still processing
            current_task = self.base_task_manager.get_task(task.task_id)
            if current_task and current_task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                await self._trigger_escalation(
                    task.task_id,
                    EscalationTrigger.TIMEOUT,
                    f"Task exceeded {timeout_seconds} second timeout"
                )
        
        # Start timeout monitoring
        timeout_task = asyncio.create_task(timeout_handler())
        self.task_timeouts[task.task_id] = timeout_task
    
    async def _process_priority_queue(self, priority: TaskPriority):
        """Process tasks from specific priority queue"""
        queue = self.priority_queues[priority]
        
        while True:
            try:
                # Get next task from queue
                task_id = await queue.get()
                
                # Check dependencies
                if not await self._check_dependencies_satisfied(task_id):
                    # Re-queue for later processing
                    await queue.put(task_id)
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                
                # Process the task
                await self._process_single_task(task_id)
                
            except Exception as e:
                logger.error(f"Error in {priority.value} queue processor: {str(e)}")
                await asyncio.sleep(5)  # Error backoff
    
    async def _check_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if task dependencies are satisfied"""
        dependency = self.task_dependencies.get(task_id)
        if not dependency:
            return True  # No dependencies
        
        for dep_task_id in dependency.depends_on:
            dep_task = self.base_task_manager.get_task(dep_task_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _process_single_task(self, task_id: str):
        """Process individual task through its lifecycle"""
        task = self.base_task_manager.get_task(task_id)
        medical_context = self.task_contexts.get(task_id)
        
        if not task or not medical_context:
            logger.error(f"Task or medical context not found for {task_id}")
            return
        
        try:
            # Record assignment
            await self._record_lifecycle_event(
                task_id,
                "task_assigned",
                TaskStage.ASSIGNED,
                agent_id=task.agent_to
            )
            
            # Update task status to processing
            self.base_task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            await self._record_lifecycle_event(
                task_id,
                "processing_started",
                TaskStage.PROCESSING,
                agent_id=task.agent_to
            )
            
            # Simulate task processing (in real implementation, this would call actual agent)
            await self._simulate_task_processing(task, medical_context)
            
            # Validate results
            await self._validate_task_results(task, medical_context)
            
            # Complete task
            await self._complete_task(task_id)
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            await self._trigger_escalation(
                task_id,
                EscalationTrigger.PROCESSING_ERROR,
                str(e)
            )
    
    async def _simulate_task_processing(self, task: A2ATask, medical_context: MedicalTaskContext):
        """
        Simulate task processing (placeholder for actual agent communication).
        In production, this would make actual A2A calls to target agents.
        """
        processing_time = 2.0  # Simulate processing time
        
        if medical_context.case_priority == TaskPriority.CRITICAL:
            processing_time = 0.5  # Faster processing for critical cases
        
        await asyncio.sleep(processing_time)
        
        # Simulate successful processing with mock results
        mock_result = {
            'processed_by': task.agent_to,
            'processing_time': processing_time,
            'result_type': task.task_type,
            'confidence': 0.85,
            'medical_findings': {
                'lpp_grade': 2,
                'anatomical_location': medical_context.anatomical_location,
                'requires_attention': True
            },
            'compliance_validated': True
        }
        
        # Update task with results
        self.base_task_manager.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            result=mock_result
        )
    
    async def _validate_task_results(self, task: A2ATask, medical_context: MedicalTaskContext):
        """Validate task results for medical compliance"""
        await self._record_lifecycle_event(
            task.task_id,
            "result_validation",
            TaskStage.VALIDATING,
            details={'validation_type': 'medical_compliance'}
        )
        
        # Check if results require escalation
        result = task.result
        if result:
            confidence = result.get('confidence', 0.0)
            medical_findings = result.get('medical_findings', {})
            lpp_grade = medical_findings.get('lpp_grade', 0)
            
            # Low confidence escalation
            if confidence < 0.6:
                await self._trigger_escalation(
                    task.task_id,
                    EscalationTrigger.LOW_CONFIDENCE,
                    f"Low confidence result: {confidence:.2f}"
                )
                return
            
            # Critical medical findings escalation
            if lpp_grade >= 3:
                await self._trigger_escalation(
                    task.task_id,
                    EscalationTrigger.CRITICAL_RESULT,
                    f"Critical LPP Grade {lpp_grade} detected"
                )
                return
        
        logger.info(f"Task {task.task_id} passed validation")
    
    async def _complete_task(self, task_id: str):
        """Complete task lifecycle"""
        await self._record_lifecycle_event(
            task_id,
            "task_completed",
            TaskStage.COMPLETING
        )
        
        # Cancel timeout monitoring
        timeout_task = self.task_timeouts.get(task_id)
        if timeout_task:
            timeout_task.cancel()
            del self.task_timeouts[task_id]
        
        # Update metrics
        self.processing_metrics['completed_tasks'] += 1
        
        # Archive lifecycle events
        await self._archive_task_lifecycle(task_id)
        
        logger.info(f"Completed task {task_id}")
    
    async def _trigger_escalation(self, task_id: str, trigger: EscalationTrigger, reason: str):
        """Trigger task escalation"""
        task = self.base_task_manager.get_task(task_id)
        medical_context = self.task_contexts.get(task_id)
        
        await self._record_lifecycle_event(
            task_id,
            "escalation_triggered",
            TaskStage.ESCALATING,
            details={
                'trigger': trigger.value,
                'reason': reason
            }
        )
        
        # Get escalation handler
        handler = self.escalation_handlers.get(trigger)
        if handler:
            await handler(task_id, reason, medical_context)
        
        # Update metrics
        self.processing_metrics['escalated_tasks'] += 1
        
        # Audit escalation
        if task and medical_context:
            await self.audit_service.log_event(
                event_type='a2a_task_escalated',
                session_id=task_id,
                user_id=task.agent_to,
                resource_type='a2a_task',
                action='escalate',
                details={
                    'escalation_trigger': trigger.value,
                    'escalation_reason': reason,
                    'agent_to': task.agent_to,
                    'medical_urgency': medical_context.medical_urgency,
                    'token_id': medical_context.token_id,
                    'patient_alias': medical_context.patient_alias,
                    'phi_compliant': medical_context.phi_compliant
                }
            )
    
    async def _handle_timeout_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle timeout escalation"""
        logger.warning(f"Task {task_id} escalated due to timeout: {reason}")
        
        # Mark task as failed due to timeout
        self.base_task_manager.update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=f"Timeout escalation: {reason}"
        )
        
        # If critical medical case, send immediate notification
        if medical_context and medical_context.case_priority == TaskPriority.CRITICAL:
            await self._send_critical_escalation_notification(task_id, reason)
    
    async def _handle_confidence_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle low confidence escalation"""
        logger.info(f"Task {task_id} escalated for human review: {reason}")
        
        # Add to human review queue
        await self._add_to_human_review_queue(task_id, reason)
    
    async def _handle_critical_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle critical medical findings escalation"""
        logger.critical(f"CRITICAL medical escalation for task {task_id}: {reason}")
        
        # Immediate notification to medical team
        await self._send_critical_escalation_notification(task_id, reason)
        
        # Add to high-priority human review
        await self._add_to_human_review_queue(task_id, reason, priority="CRITICAL")
    
    async def _handle_error_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle processing error escalation"""
        logger.error(f"Task {task_id} escalated due to processing error: {reason}")
        
        # Mark task as failed
        self.base_task_manager.update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=f"Processing error: {reason}"
        )
        
        # Update error metrics
        self.processing_metrics['failed_tasks'] += 1
    
    async def _handle_agent_failure_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle agent failure escalation"""
        logger.error(f"Agent failure escalation for task {task_id}: {reason}")
        
        # Try to reassign to backup agent if available
        await self._attempt_task_reassignment(task_id)
    
    async def _handle_manual_escalation(self, task_id: str, reason: str, medical_context: Optional[MedicalTaskContext]):
        """Handle manual escalation request"""
        logger.info(f"Manual escalation requested for task {task_id}: {reason}")
        
        # Add to human review with manual flag
        await self._add_to_human_review_queue(task_id, reason, manual=True)
    
    async def _send_critical_escalation_notification(self, task_id: str, reason: str):
        """Send critical escalation notification"""
        # This would integrate with the CommunicationAgent in production
        logger.critical(f"CRITICAL ESCALATION NOTIFICATION: Task {task_id} - {reason}")
        
        # Mock notification (in production, this would call CommunicationAgent)
        notification_data = {
            'type': 'critical_escalation',
            'task_id': task_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'requires_immediate_attention': True
        }
        
        # Store notification for audit
        await self.audit_service.log_event(
            event_type='critical_escalation_notification',
            session_id=task_id,
            user_id='SYSTEM',
            resource_type='notification',
            action='send_critical',
            details=notification_data
        )
    
    async def _add_to_human_review_queue(self, task_id: str, reason: str, priority: str = "HIGH", manual: bool = False):
        """Add task to human review queue"""
        review_entry = {
            'task_id': task_id,
            'reason': reason,
            'priority': priority,
            'manual_request': manual,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending_review'
        }
        
        # This would integrate with HumanReviewQueue system in production
        logger.info(f"Added task {task_id} to human review queue: {reason}")
        
        # Audit human review request
        await self.audit_service.log_event(
            event_type='human_review_requested',
            session_id=task_id,
            user_id='SYSTEM',
            resource_type='human_review_queue',
            action='add_task',
            details=review_entry
        )
    
    async def _attempt_task_reassignment(self, task_id: str):
        """Attempt to reassign failed task to backup agent"""
        task = self.base_task_manager.get_task(task_id)
        if not task:
            return
        
        # Define backup agents for each task type
        backup_agents = {
            'image_analysis': ['backup_image_analysis_agent'],
            'clinical_assessment': ['backup_clinical_agent'],
            'protocol_lookup': ['backup_protocol_agent']
        }
        
        backups = backup_agents.get(task.task_type, [])
        if backups:
            # Try first available backup
            backup_agent = backups[0]
            
            # Create new task with backup agent
            medical_context = self.task_contexts.get(task_id)
            if medical_context:
                new_task = await self.create_medical_task(
                    agent_from=task.agent_from,
                    agent_to=backup_agent,
                    task_type=task.task_type,
                    payload=task.payload,
                    medical_context=medical_context
                )
                
                logger.info(f"Reassigned task {task_id} to backup agent {backup_agent} as {new_task.task_id}")
    
    async def _record_lifecycle_event(self, task_id: str, event_type: str, stage: TaskStage, 
                                    agent_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Record lifecycle event for task"""
        event = TaskLifecycleEvent(
            event_id=str(uuid.uuid4()),
            task_id=task_id,
            event_type=event_type,
            stage=stage,
            timestamp=datetime.now(),
            agent_id=agent_id,
            details=details
        )
        
        if task_id not in self.task_events:
            self.task_events[task_id] = []
        
        self.task_events[task_id].append(event)
        
        # Also log to audit service
        await self.audit_service.log_event(
            event_type=f'a2a_lifecycle_{event_type}',
            session_id=task_id,
            user_id=agent_id or 'SYSTEM',
            resource_type='a2a_lifecycle',
            action=event_type,
            details={
                'stage': stage.value,
                'agent_id': agent_id,
                'event_details': details
            }
        )
    
    async def _archive_task_lifecycle(self, task_id: str):
        """Archive completed task lifecycle"""
        await self._record_lifecycle_event(
            task_id,
            "task_archived",
            TaskStage.ARCHIVED
        )
        
        # Move to archive storage (in production, this would go to long-term storage)
        logger.info(f"Archived lifecycle for task {task_id}")
    
    def get_task_lifecycle(self, task_id: str) -> List[TaskLifecycleEvent]:
        """Get complete lifecycle for task"""
        return self.task_events.get(task_id, [])
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        total = self.processing_metrics['total_tasks']
        completed = self.processing_metrics['completed_tasks']
        
        metrics = self.processing_metrics.copy()
        metrics.update({
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'escalation_rate': (self.processing_metrics['escalated_tasks'] / total * 100) if total > 0 else 0,
            'failure_rate': (self.processing_metrics['failed_tasks'] / total * 100) if total > 0 else 0,
            'active_timeouts': len(self.task_timeouts),
            'queue_sizes': {
                priority.value: queue.qsize() 
                for priority, queue in self.priority_queues.items()
            }
        })
        
        return metrics
    
    async def shutdown(self):
        """Graceful shutdown of lifecycle manager"""
        logger.info("Shutting down MedicalTaskLifecycleManager...")
        
        # Cancel all timeout tasks
        for timeout_task in self.task_timeouts.values():
            timeout_task.cancel()
        
        # Cancel all processors
        for processor in self.task_processors.values():
            processor.cancel()
        
        # Archive remaining tasks
        for task_id in list(self.task_events.keys()):
            await self._archive_task_lifecycle(task_id)
        
        logger.info("MedicalTaskLifecycleManager shutdown complete")


# Export main classes
__all__ = [
    'MedicalTaskLifecycleManager', 
    'TaskPriority', 
    'TaskStage', 
    'EscalationTrigger',
    'MedicalTaskContext', 
    'TaskDependency', 
    'TaskLifecycleEvent'
]