"""
Medical Telemetry Integration for Vigia LPP Detection System
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio

from .agentops_client import AgentOpsClient
from .adk_wrapper import ADKMedicalAgent

logger = logging.getLogger(__name__)

class MedicalTelemetry:
    """
    Central telemetry system for medical AI operations
    
    Integrates with:
    - Google ADK agents
    - Async Celery pipeline
    - LPP detection system
    - Medical decision engine
    - MINSAL compliance tracking
    """
    
    def __init__(
        self,
        app_id: str = "vigia-lpp-detection",
        environment: str = "production",
        enable_phi_protection: bool = True
    ):
        """
        Initialize medical telemetry system
        
        Args:
            app_id: Application identifier for AgentOps
            environment: Deployment environment
            enable_phi_protection: Enable PHI tokenization
        """
        self.app_id = app_id
        self.environment = environment
        self.enable_phi_protection = enable_phi_protection
        
        # Initialize AgentOps client
        self.agentops_client = AgentOpsClient(
            app_id=app_id,
            environment=environment,
            enable_phi_protection=enable_phi_protection,
            compliance_level="hipaa"
        )
        
        # Track active sessions
        self.active_sessions = {}
        
        # Performance metrics
        self.metrics = {
            'sessions_started': 0,
            'lpp_detections': 0,
            'medical_decisions': 0,
            'errors_escalated': 0,
            'avg_response_time': 0.0
        }
    
    async def start_medical_session(
        self,
        session_id: str,
        patient_context: Dict[str, Any],
        session_type: str = "lpp_analysis",
        medical_team: Optional[str] = None
    ) -> Optional[str]:
        """
        Start a comprehensive medical session
        
        Args:
            session_id: Unique session identifier
            patient_context: Medical context (will be tokenized)
            session_type: Type of medical session
            medical_team: Responsible medical team
            
        Returns:
            AgentOps session ID or None
        """
        try:
            # Enhanced patient context for telemetry
            enhanced_context = {
                **patient_context,
                'medical_team': medical_team,
                'vigia_version': '1.3.1',
                'compliance_frameworks': ['HIPAA', 'MINSAL', 'NPUAP_EPUAP'],
                'session_capabilities': [
                    'lpp_detection',
                    'risk_assessment', 
                    'evidence_based_decisions',
                    'async_pipeline'
                ]
            }
            
            # Start AgentOps session
            agentops_session_id = self.agentops_client.track_medical_session(
                session_id=session_id,
                patient_context=enhanced_context,
                session_type=session_type
            )
            
            # Track locally
            self.active_sessions[session_id] = {
                'agentops_session_id': agentops_session_id,
                'start_time': time.time(),
                'session_type': session_type,
                'medical_team': medical_team,
                'events': []
            }
            
            self.metrics['sessions_started'] += 1
            
            logger.info(f"Started medical session: {session_id} (type: {session_type})")
            return agentops_session_id
            
        except Exception as e:
            logger.error(f"Failed to start medical session {session_id}: {e}")
            return None
    
    def track_lpp_detection_event(
        self,
        session_id: str,
        image_path: str,
        detection_results: Dict[str, Any],
        agent_name: str = "lpp_detector",
        processing_time: Optional[float] = None
    ):
        """
        Track LPP detection with comprehensive metadata
        
        Args:
            session_id: Session identifier
            image_path: Path to analyzed image
            detection_results: Complete detection results
            agent_name: Name of detecting agent
            processing_time: Time taken for detection
        """
        try:
            # Extract key metrics
            confidence = detection_results.get('confidence', 0.0)
            lpp_grade = detection_results.get('lpp_grade')
            anatomical_location = detection_results.get('anatomical_location')
            
            # Track with AgentOps
            self.agentops_client.track_lpp_detection(
                session_id=session_id,
                image_path=image_path,
                detection_results=detection_results,
                confidence=confidence,
                lpp_grade=lpp_grade
            )
            
            # Add to session events
            if session_id in self.active_sessions:
                event = {
                    'event_type': 'lpp_detection',
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent_name': agent_name,
                    'confidence': confidence,
                    'lpp_grade': lpp_grade,
                    'anatomical_location': anatomical_location,
                    'processing_time': processing_time
                }
                self.active_sessions[session_id]['events'].append(event)
            
            self.metrics['lpp_detections'] += 1
            
            logger.debug(f"Tracked LPP detection for session {session_id}: Grade {lpp_grade}, Confidence {confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to track LPP detection: {e}")
    
    def track_medical_decision(
        self,
        session_id: str,
        decision_type: str,
        input_data: Dict[str, Any],
        decision_result: Dict[str, Any],
        evidence_level: str,
        agent_name: str = "medical_decision_engine"
    ):
        """
        Track evidence-based medical decisions
        
        Args:
            session_id: Session identifier
            decision_type: Type of medical decision
            input_data: Decision input data
            decision_result: Decision output
            evidence_level: Evidence level (A/B/C)
            agent_name: Decision-making agent
        """
        try:
            # Extract decision metrics
            confidence = decision_result.get('confidence', 0.0)
            recommendation = decision_result.get('recommendation', '')
            urgency_level = decision_result.get('urgency_level', 'normal')
            
            # Enhanced decision context
            decision_context = {
                'decision_type': decision_type,
                'evidence_level': evidence_level,
                'confidence': confidence,
                'urgency_level': urgency_level,
                'compliance_frameworks': decision_result.get('compliance_frameworks', []),
                'scientific_references': decision_result.get('scientific_references', [])
            }
            
            # Track as agent interaction
            self.agentops_client.track_agent_interaction(
                agent_name=agent_name,
                action=f"medical_decision_{decision_type}",
                input_data=input_data,
                output_data=decision_result,
                execution_time=0,  # Instantaneous for decisions
                success=True
            )
            
            # Add to session events
            if session_id in self.active_sessions:
                event = {
                    'event_type': 'medical_decision',
                    'timestamp': datetime.utcnow().isoformat(),
                    'decision_type': decision_type,
                    'evidence_level': evidence_level,
                    'confidence': confidence,
                    'urgency_level': urgency_level,
                    'agent_name': agent_name
                }
                self.active_sessions[session_id]['events'].append(event)
            
            self.metrics['medical_decisions'] += 1
            
            logger.debug(f"Tracked medical decision for session {session_id}: {decision_type} (Evidence: {evidence_level})")
            
        except Exception as e:
            logger.error(f"Failed to track medical decision: {e}")
    
    def track_async_pipeline_task(
        self,
        task_id: str,
        task_type: str,
        queue: str,
        status: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track Celery async pipeline tasks
        
        Args:
            task_id: Celery task ID
            task_type: Type of medical task
            queue: Queue name
            status: Task status
            session_id: Associated session ID
            metadata: Additional task metadata
        """
        try:
            # Enhanced metadata with session context
            enhanced_metadata = {
                'session_id': session_id,
                'vigia_component': 'async_pipeline',
                **(metadata or {})
            }
            
            # Track with AgentOps
            self.agentops_client.track_async_task(
                task_id=task_id,
                task_type=task_type,
                queue=queue,
                status=status,
                metadata=enhanced_metadata
            )
            
            # Add to session events if session exists
            if session_id and session_id in self.active_sessions:
                event = {
                    'event_type': 'async_task',
                    'timestamp': datetime.utcnow().isoformat(),
                    'task_id': task_id,
                    'task_type': task_type,
                    'queue': queue,
                    'status': status
                }
                self.active_sessions[session_id]['events'].append(event)
            
            logger.debug(f"Tracked async task: {task_type} ({status}) - Task ID: {task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to track async task: {e}")
    
    def track_medical_error_with_escalation(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        requires_human_review: bool = False,
        severity: str = "medium"
    ):
        """
        Track medical errors with automatic escalation
        
        Args:
            error_type: Type of medical error
            error_message: Error description
            context: Error context
            session_id: Associated session ID
            requires_human_review: Whether error needs human review
            severity: Error severity level
        """
        try:
            # Enhanced error context
            enhanced_context = {
                **context,
                'session_id': session_id,
                'vigia_version': '1.3.1',
                'error_timestamp': datetime.utcnow().isoformat()
            }
            
            # Track with AgentOps
            self.agentops_client.track_medical_error(
                error_type=error_type,
                error_message=error_message,
                context=enhanced_context,
                severity=severity,
                requires_escalation=requires_human_review
            )
            
            # Add to session events
            if session_id and session_id in self.active_sessions:
                event = {
                    'event_type': 'medical_error',
                    'timestamp': datetime.utcnow().isoformat(),
                    'error_type': error_type,
                    'severity': severity,
                    'requires_escalation': requires_human_review
                }
                self.active_sessions[session_id]['events'].append(event)
            
            if requires_human_review:
                self.metrics['errors_escalated'] += 1
            
            logger.warning(f"Tracked medical error: {error_type} (Severity: {severity})")
            
        except Exception as e:
            logger.error(f"Failed to track medical error: {e}")
    
    def end_medical_session(
        self,
        session_id: str,
        outcome: str = "completed",
        final_recommendations: Optional[List[str]] = None
    ):
        """
        End medical session with summary
        
        Args:
            session_id: Session to end
            outcome: Session outcome
            final_recommendations: Final medical recommendations
        """
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found in active sessions")
                return
            
            session_data = self.active_sessions[session_id]
            session_duration = time.time() - session_data['start_time']
            
            # Create session summary
            session_summary = {
                'session_id': session_id,
                'duration': session_duration,
                'outcome': outcome,
                'events_count': len(session_data['events']),
                'final_recommendations': final_recommendations or [],
                'medical_team': session_data.get('medical_team'),
                'events': session_data['events']
            }
            
            # End AgentOps session
            self.agentops_client.end_session(session_data.get('agentops_session_id'))
            
            # Update metrics
            self._update_performance_metrics(session_duration)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Ended medical session {session_id}: {outcome} (Duration: {session_duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"Failed to end medical session {session_id}: {e}")
    
    def create_adk_agent(
        self,
        agent_name: str,
        medical_specialty: str,
        enable_tracking: bool = True
    ) -> ADKMedicalAgent:
        """
        Create a tracked ADK medical agent
        
        Args:
            agent_name: Name of the agent
            medical_specialty: Medical specialty
            enable_tracking: Whether to enable telemetry
            
        Returns:
            Tracked ADK medical agent
        """
        return ADKMedicalAgent(
            agent_name=agent_name,
            medical_specialty=medical_specialty,
            agentops_client=self.agentops_client if enable_tracking else None,
            enable_telemetry=enable_tracking,
            compliance_level="hipaa"
        )
    
    @asynccontextmanager
    async def medical_session_context(
        self,
        session_id: str,
        patient_context: Dict[str, Any],
        session_type: str = "lpp_analysis"
    ):
        """
        Async context manager for medical sessions
        
        Usage:
        async with telemetry.medical_session_context(session_id, context) as session:
            # Medical operations here
            pass
        """
        # Start session
        agentops_session_id = await self.start_medical_session(
            session_id=session_id,
            patient_context=patient_context,
            session_type=session_type
        )
        
        try:
            yield {
                'session_id': session_id,
                'agentops_session_id': agentops_session_id,
                'telemetry': self
            }
        except Exception as e:
            # Track error and escalate if needed
            self.track_medical_error_with_escalation(
                error_type="session_error",
                error_message=str(e),
                context={'session_id': session_id},
                session_id=session_id,
                requires_human_review=True,
                severity="high"
            )
            raise
        finally:
            # End session
            self.end_medical_session(session_id, outcome="completed")
    
    def _update_performance_metrics(self, session_duration: float):
        """Update performance metrics with new session data"""
        # Update average response time
        total_sessions = self.metrics['sessions_started']
        current_avg = self.metrics['avg_response_time']
        
        # Weighted average calculation
        new_avg = ((current_avg * (total_sessions - 1)) + session_duration) / total_sessions
        self.metrics['avg_response_time'] = new_avg
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get comprehensive telemetry summary"""
        return {
            'app_id': self.app_id,
            'environment': self.environment,
            'active_sessions': len(self.active_sessions),
            'metrics': self.metrics,
            'agentops_initialized': self.agentops_client.initialized,
            'phi_protection_enabled': self.enable_phi_protection,
            'compliance_level': 'hipaa',
            'timestamp': datetime.utcnow().isoformat()
        }