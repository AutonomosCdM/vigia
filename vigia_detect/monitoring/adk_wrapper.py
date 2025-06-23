"""
Google ADK Agent Wrapper with AgentOps Integration
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from datetime import datetime
import asyncio
import traceback

from .agentops_client import AgentOpsClient

logger = logging.getLogger(__name__)

class ADKAgentWrapper:
    """
    Wrapper for Google ADK agents with AgentOps observability
    
    Features:
    - Automatic telemetry for all agent interactions
    - Performance monitoring with timing
    - Error tracking with medical escalation
    - Medical compliance with PHI protection
    - Async support for Celery tasks
    """
    
    def __init__(
        self,
        agent_name: str,
        agentops_client: Optional[AgentOpsClient] = None,
        enable_telemetry: bool = True,
        medical_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ADK agent wrapper
        
        Args:
            agent_name: Name of the ADK agent
            agentops_client: AgentOps client for telemetry
            enable_telemetry: Whether to enable telemetry
            medical_context: Medical context for compliance
        """
        self.agent_name = agent_name
        self.agentops_client = agentops_client
        self.enable_telemetry = enable_telemetry
        self.medical_context = medical_context or {}
        
        # Performance tracking
        self.interaction_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0
        
        # Initialize AgentOps client if not provided
        if self.enable_telemetry and not self.agentops_client:
            try:
                self.agentops_client = AgentOpsClient()
            except Exception as e:
                logger.warning(f"Failed to initialize AgentOps client: {e}")
                self.enable_telemetry = False
    
    def track_interaction(
        self,
        action_name: Optional[str] = None,
        medical_critical: bool = False,
        escalate_on_error: bool = False
    ):
        """
        Decorator to track ADK agent interactions
        
        Args:
            action_name: Name of the action (uses function name if None)
            medical_critical: Whether this is a medical-critical operation
            escalate_on_error: Whether to escalate errors for human review
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_with_tracking(
                    func, args, kwargs, action_name or func.__name__,
                    medical_critical, escalate_on_error, is_async=True
                )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self._execute_with_tracking(
                    func, args, kwargs, action_name or func.__name__,
                    medical_critical, escalate_on_error, is_async=False
                ))
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def _execute_with_tracking(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        action_name: str,
        medical_critical: bool,
        escalate_on_error: bool,
        is_async: bool
    ):
        """Execute function with comprehensive tracking"""
        start_time = time.time()
        self.interaction_count += 1
        
        # Prepare tracking data
        input_data = {
            'args': args,
            'kwargs': kwargs,
            'medical_context': self.medical_context,
            'interaction_count': self.interaction_count
        }
        
        success = True
        error_message = None
        output_data = None
        
        try:
            # Execute the function
            if is_async:
                output_data = await func(*args, **kwargs)
            else:
                output_data = func(*args, **kwargs)
            
            logger.debug(f"ADK agent {self.agent_name}.{action_name} completed successfully")
            
        except Exception as e:
            success = False
            error_message = str(e)
            self.error_count += 1
            
            # Log error appropriately
            if medical_critical:
                logger.error(f"Medical-critical error in {self.agent_name}.{action_name}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"Error in {self.agent_name}.{action_name}: {e}")
            
            # Handle escalation for medical errors
            if escalate_on_error and self.enable_telemetry and self.agentops_client:
                await self._escalate_medical_error(action_name, e, medical_critical)
            
            # Re-raise for normal error handling
            raise
        
        finally:
            # Calculate execution time
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            # Track with AgentOps
            if self.enable_telemetry and self.agentops_client:
                try:
                    self.agentops_client.track_agent_interaction(
                        agent_name=self.agent_name,
                        action=action_name,
                        input_data=input_data,
                        output_data={'result': output_data} if output_data is not None else {},
                        execution_time=execution_time,
                        success=success,
                        error=error_message
                    )
                except Exception as e:
                    logger.warning(f"Failed to track agent interaction: {e}")
        
        return output_data
    
    async def _escalate_medical_error(
        self,
        action_name: str,
        error: Exception,
        medical_critical: bool
    ):
        """Escalate medical errors for human review"""
        try:
            severity = "critical" if medical_critical else "high"
            
            error_context = {
                'agent_name': self.agent_name,
                'action_name': action_name,
                'medical_context': self.medical_context,
                'error_type': type(error).__name__,
                'interaction_count': self.interaction_count,
                'total_errors': self.error_count
            }
            
            self.agentops_client.track_medical_error(
                error_type=f"adk_agent_error",
                error_message=str(error),
                context=error_context,
                severity=severity,
                requires_escalation=True
            )
            
            logger.info(f"Medical error escalated for {self.agent_name}.{action_name}")
            
        except Exception as e:
            logger.error(f"Failed to escalate medical error: {e}")
    
    def track_lpp_analysis(
        self,
        image_path: str,
        detection_results: Dict[str, Any],
        confidence: float,
        session_id: Optional[str] = None
    ):
        """
        Track LPP-specific analysis with medical metadata
        
        Args:
            image_path: Path to analyzed image
            detection_results: LPP detection results
            confidence: Detection confidence
            session_id: Optional session ID
        """
        if not self.enable_telemetry or not self.agentops_client:
            return
        
        try:
            # Extract LPP grade if available
            lpp_grade = detection_results.get('lpp_grade')
            
            # Track LPP detection
            self.agentops_client.track_lpp_detection(
                session_id=session_id or f"adk_{self.agent_name}_{int(time.time())}",
                image_path=image_path,
                detection_results=detection_results,
                confidence=confidence,
                lpp_grade=lpp_grade
            )
            
        except Exception as e:
            logger.warning(f"Failed to track LPP analysis: {e}")
    
    def track_celery_task(
        self,
        task_id: str,
        task_type: str,
        queue: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track Celery async task execution
        
        Args:
            task_id: Celery task ID
            task_type: Type of medical task
            queue: Queue name
            status: Task status
            metadata: Additional task metadata
        """
        if not self.enable_telemetry or not self.agentops_client:
            return
        
        try:
            # Combine metadata with agent context
            full_metadata = {
                'agent_name': self.agent_name,
                'medical_context': self.medical_context,
                **(metadata or {})
            }
            
            self.agentops_client.track_async_task(
                task_id=task_id,
                task_type=task_type,
                queue=queue,
                status=status,
                metadata=full_metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to track Celery task: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the agent"""
        avg_execution_time = (
            self.total_execution_time / self.interaction_count 
            if self.interaction_count > 0 else 0
        )
        
        error_rate = (
            self.error_count / self.interaction_count 
            if self.interaction_count > 0 else 0
        )
        
        return {
            'agent_name': self.agent_name,
            'interaction_count': self.interaction_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': avg_execution_time,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'uptime_ratio': 1 - error_rate,
            'medical_context': self.medical_context
        }
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.interaction_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0
        logger.info(f"Reset metrics for ADK agent: {self.agent_name}")

class ADKMedicalAgent(ADKAgentWrapper):
    """
    Specialized wrapper for medical ADK agents
    
    Provides medical-specific tracking and compliance features
    """
    
    def __init__(
        self,
        agent_name: str,
        medical_specialty: str,
        compliance_level: str = "hipaa",
        **kwargs
    ):
        """
        Initialize medical ADK agent
        
        Args:
            agent_name: Name of the medical agent
            medical_specialty: Medical specialty (e.g., 'lpp_detection', 'triage')
            compliance_level: Compliance requirement level
        """
        super().__init__(agent_name, **kwargs)
        self.medical_specialty = medical_specialty
        self.compliance_level = compliance_level
        
        # Update medical context
        self.medical_context.update({
            'medical_specialty': medical_specialty,
            'compliance_level': compliance_level,
            'agent_type': 'medical_adk'
        })
    
    @property
    def is_medical_critical(self) -> bool:
        """Check if this agent handles medical-critical operations"""
        critical_specialties = ['lpp_detection', 'risk_assessment', 'triage', 'diagnosis']
        return self.medical_specialty in critical_specialties
    
    def track_medical_decision(
        self,
        decision_type: str,
        input_data: Dict[str, Any],
        decision_result: Dict[str, Any],
        confidence: float,
        evidence_level: str,
        session_id: Optional[str] = None
    ):
        """
        Track medical decision-making with evidence
        
        Args:
            decision_type: Type of medical decision
            input_data: Input data for decision
            decision_result: Decision output
            confidence: Decision confidence
            evidence_level: Evidence level (A/B/C)
            session_id: Session identifier
        """
        if not self.enable_telemetry or not self.agentops_client:
            return
        
        try:
            # Create medical decision event
            decision_metadata = {
                'decision_type': decision_type,
                'medical_specialty': self.medical_specialty,
                'confidence': confidence,
                'evidence_level': evidence_level,
                'compliance_level': self.compliance_level,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Track as agent interaction with medical context
            self.agentops_client.track_agent_interaction(
                agent_name=self.agent_name,
                action=f"medical_decision_{decision_type}",
                input_data=input_data,
                output_data=decision_result,
                execution_time=0,  # Instantaneous for decisions
                success=True
            )
            
        except Exception as e:
            logger.warning(f"Failed to track medical decision: {e}")


# Convenience decorator function for quick integration
def adk_agent_wrapper(
    action_name: Optional[str] = None,
    medical_critical: bool = False,
    escalate_on_error: bool = False,
    agent_name: Optional[str] = None
):
    """
    Convenience decorator for wrapping ADK agent functions with AgentOps tracking
    
    Args:
        action_name: Name of the action (uses function name if None)
        medical_critical: Whether this is a medical-critical operation
        escalate_on_error: Whether to escalate errors for human review
        agent_name: Agent name (auto-detected from class if None)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Auto-detect agent name from class
            detected_agent_name = agent_name or getattr(self, 'agent_id', self.__class__.__name__)
            
            # Create wrapper if not exists
            if not hasattr(self, '_adk_wrapper'):
                self._adk_wrapper = ADKAgentWrapper(
                    agent_name=detected_agent_name,
                    enable_telemetry=True,
                    medical_context=getattr(self, 'medical_context', {})
                )
            
            # Execute with tracking
            try:
                start_time = time.time()
                result = await func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                
                # Track successful execution
                if self._adk_wrapper.enable_telemetry and self._adk_wrapper.agentops_client:
                    try:
                        self._adk_wrapper.agentops_client.track_agent_interaction(
                            agent_name=detected_agent_name,
                            action=action_name or func.__name__,
                            input_data={
                                'args_count': len(args),
                                'kwargs_keys': list(kwargs.keys()),
                                'medical_critical': medical_critical
                            },
                            output_data={
                                'success': True,
                                'result_type': type(result).__name__
                            },
                            execution_time=execution_time,
                            success=True
                        )
                    except Exception as tracking_error:
                        logger.warning(f"Failed to track agent interaction: {tracking_error}")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Track error
                if hasattr(self, '_adk_wrapper') and self._adk_wrapper.enable_telemetry:
                    try:
                        severity = "critical" if medical_critical else "medium"
                        self._adk_wrapper.agentops_client.track_medical_error(
                            error_type=f"adk_agent_error_{func.__name__}",
                            error_message=str(e),
                            context={
                                'agent_name': detected_agent_name,
                                'action_name': action_name or func.__name__,
                                'medical_critical': medical_critical,
                                'execution_time': execution_time
                            },
                            severity=severity,
                            requires_escalation=escalate_on_error
                        )
                    except Exception as tracking_error:
                        logger.warning(f"Failed to track error: {tracking_error}")
                
                # Re-raise original exception
                raise
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # For sync functions, just execute normally
            # (AgentOps tracking requires async for proper session management)
            return func(self, *args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator