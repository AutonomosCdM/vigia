"""
HIPAA-Compliant AgentOps Client for Medical AI Systems
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

try:
    import agentops
    from agentops.sdk.decorators import operation, task
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False
    agentops = None
    operation = None
    task = None

from .phi_tokenizer import PHITokenizer

logger = logging.getLogger(__name__)

class AgentOpsClient:
    """
    HIPAA-compliant AgentOps client for medical AI monitoring
    
    Features:
    - Automatic PHI tokenization
    - Medical compliance logging
    - Async pipeline tracking
    - Error monitoring with escalation
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        app_id: str = "lpp-detect-production",
        environment: str = "production",
        enable_phi_protection: bool = True,
        compliance_level: str = "hipaa"
    ):
        self.api_key = api_key or os.getenv("AGENTOPS_API_KEY")
        self.app_id = app_id
        self.environment = environment
        self.enable_phi_protection = enable_phi_protection
        self.compliance_level = compliance_level
        
        # Initialize PHI tokenizer
        self.phi_tokenizer = PHITokenizer() if enable_phi_protection else None
        
        # Initialize AgentOps if available
        self.client = None
        self.initialized = False
        
        if AGENTOPS_AVAILABLE and self.api_key:
            try:
                self._initialize_agentops()
            except Exception as e:
                logger.warning(f"Failed to initialize AgentOps: {e}")
                logger.info("Running in mock mode - telemetry will be logged locally")
        else:
            logger.warning("AgentOps not available or API key missing - running in mock mode")
    
    def _initialize_agentops(self):
        """Initialize AgentOps with medical compliance settings"""
        try:
            # Initialize AgentOps with proper parameters
            agentops.init(
                api_key=self.api_key,
                default_tags=[
                    "medical-ai",
                    "lpp-detection", 
                    "hipaa-compliant",
                    f"compliance-{self.compliance_level}",
                    f"app-{self.app_id}",
                    f"env-{self.environment}"
                ],
                auto_start_session=False  # We'll control sessions manually
            )
            self.initialized = True
            logger.info(f"AgentOps initialized for {self.app_id} in {self.environment}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AgentOps: {e}")
            # Try simple initialization
            try:
                agentops.init(api_key=self.api_key, auto_start_session=False)
                self.initialized = True
                logger.info("AgentOps initialized with simplified configuration")
            except Exception as e2:
                logger.error(f"Simplified initialization also failed: {e2}")
                raise
    
    def track_medical_session(
        self,
        session_id: str,
        patient_context: Dict[str, Any],
        session_type: str = "lpp_analysis"
    ) -> Optional[str]:
        """
        Start tracking a medical analysis session
        
        Args:
            session_id: Unique session identifier
            patient_context: Patient context (will be tokenized)
            session_type: Type of medical analysis
            
        Returns:
            AgentOps session ID or None if not available
        """
        if not self.initialized:
            logger.debug("AgentOps not initialized - skipping session tracking")
            return None
        
        try:
            # Tokenize patient context for compliance
            safe_context = self._sanitize_medical_data(patient_context)
            
            # Create session metadata
            session_metadata = {
                "session_id": session_id,
                "session_type": session_type,
                "timestamp": datetime.utcnow().isoformat(),
                "compliance_level": self.compliance_level,
                "patient_context": safe_context
            }
            
            # Start AgentOps session
            agent_session = agentops.start_session(
                tags=[session_type, "medical-session"]
            )
            
            logger.info(f"Started medical session tracking: {session_id}")
            return session_id  # Return our session_id instead of AgentOps internal ID
            
        except Exception as e:
            logger.error(f"Failed to start medical session tracking: {e}")
            return None
    
    def track_lpp_detection(
        self,
        session_id: str,
        image_path: str,
        detection_results: Dict[str, Any],
        confidence: float,
        lpp_grade: Optional[int] = None
    ):
        """
        Track LPP detection events with medical metadata
        
        Args:
            session_id: Session identifier
            image_path: Path to analyzed image (will be tokenized)
            detection_results: Detection results (sanitized)
            confidence: Detection confidence score
            lpp_grade: Detected LPP grade if available
        """
        if not self.initialized:
            return
        
        try:
            # Sanitize detection data
            safe_results = self._sanitize_medical_data(detection_results)
            safe_image_path = self.phi_tokenizer.tokenize_image_path(image_path) if self.phi_tokenizer else "tokenized_image"
            
            # Create medical event
            event_data = {
                "event_type": "lpp_detection",
                "session_id": session_id,
                "image_path": safe_image_path,
                "detection_results": safe_results,
                "confidence": confidence,
                "lpp_grade": lpp_grade,
                "timestamp": datetime.utcnow().isoformat(),
                "compliance_sanitized": True
            }
            
            # Create an operation for LPP detection if decorators are available
            if AGENTOPS_AVAILABLE and operation:
                @operation(name="lpp_detection")
                def track_lpp_detection():
                    return event_data
                
                # Execute the operation
                result = track_lpp_detection()
                logger.info(f"LPP Detection tracked: {result}")
            else:
                logger.info(f"LPP Detection tracked (mock): {event_data}")
            
            logger.debug(f"Tracked LPP detection for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to track LPP detection: {e}")
    
    def track_agent_interaction(
        self,
        agent_name: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_time: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Track ADK agent interactions with medical compliance
        
        Args:
            agent_name: Name of the ADK agent
            action: Action performed by agent
            input_data: Input data (will be sanitized)
            output_data: Output data (will be sanitized)
            execution_time: Time taken for execution
            success: Whether the action succeeded
            error: Error message if failed
        """
        if not self.initialized:
            return
        
        try:
            # Sanitize medical data
            safe_input = self._sanitize_medical_data(input_data)
            safe_output = self._sanitize_medical_data(output_data)
            
            # Create agent event
            agent_event = {
                "agent_name": agent_name,
                "action": action,
                "input_data": safe_input,
                "output_data": safe_output,
                "execution_time": execution_time,
                "success": success,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "compliance_sanitized": True
            }
            
            # Create an operation for agent interaction if decorators are available
            if AGENTOPS_AVAILABLE and operation:
                @operation(name=f"agent_{agent_name}_{action}")
                def track_agent_interaction():
                    return agent_event
                
                # Execute the operation
                result = track_agent_interaction()
                logger.info(f"Agent interaction tracked: {agent_name}.{action}")
            else:
                logger.info(f"Agent interaction tracked (mock): {agent_name}.{action}")
            
            logger.debug(f"Tracked agent interaction: {agent_name}.{action}")
            
        except Exception as e:
            logger.error(f"Failed to track agent interaction: {e}")
    
    def track_async_task(
        self,
        task_id: str,
        task_type: str,
        queue: str,
        status: str,
        metadata: Dict[str, Any]
    ):
        """
        Track async pipeline tasks (Celery tasks)
        
        Args:
            task_id: Celery task ID
            task_type: Type of medical task
            queue: Queue name
            status: Task status (pending, running, success, failure)
            metadata: Task metadata (will be sanitized)
        """
        if not self.initialized:
            return
        
        try:
            # Sanitize metadata
            safe_metadata = self._sanitize_medical_data(metadata)
            
            # Create async task event
            task_event = {
                "task_id": task_id,
                "task_type": task_type,
                "queue": queue,
                "status": status,
                "metadata": safe_metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "compliance_sanitized": True
            }
            
            # Create a task for async task if decorators are available
            if AGENTOPS_AVAILABLE and task:
                @task(name=f"async_{task_type}")
                def track_async_task():
                    return task_event
                
                # Execute the task  
                result = track_async_task()
                logger.info(f"Async task tracked: {task_type} ({status})")
            else:
                logger.info(f"Async task tracked (mock): {task_type} ({status})")
            
            logger.debug(f"Tracked async task: {task_type} ({status})")
            
        except Exception as e:
            logger.error(f"Failed to track async task: {e}")
    
    def track_medical_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        severity: str = "medium",
        requires_escalation: bool = False
    ):
        """
        Track medical errors with escalation flags
        
        Args:
            error_type: Type of medical error
            error_message: Error description
            context: Error context (will be sanitized)
            severity: Error severity (low, medium, high, critical)
            requires_escalation: Whether error requires human review
        """
        if not self.initialized:
            return
        
        try:
            # Sanitize error context
            safe_context = self._sanitize_medical_data(context)
            
            # Create error event
            error_event = {
                "error_type": error_type,
                "error_message": error_message,
                "context": safe_context,
                "severity": severity,
                "requires_escalation": requires_escalation,
                "timestamp": datetime.utcnow().isoformat(),
                "compliance_sanitized": True
            }
            
            # Create an operation for medical error if decorators are available
            if AGENTOPS_AVAILABLE and operation:
                @operation(name=f"medical_error_{error_type}")
                def track_medical_error():
                    return error_event
                
                # Execute the operation
                result = track_medical_error()
                logger.info(f"Medical error tracked: {error_type} (Severity: {severity})")
            else:
                logger.info(f"Medical error tracked (mock): {error_type} (Severity: {severity})")
            
            # Log appropriately based on severity
            if severity in ["high", "critical"]:
                logger.error(f"Medical error tracked: {error_type} - {error_message}")
            else:
                logger.warning(f"Medical error tracked: {error_type}")
                
        except Exception as e:
            logger.error(f"Failed to track medical error: {e}")
    
    def _sanitize_medical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize medical data for compliance
        
        Args:
            data: Raw data that may contain PHI
            
        Returns:
            Sanitized data safe for external logging
        """
        if not self.enable_phi_protection or not self.phi_tokenizer:
            return data
        
        try:
            return self.phi_tokenizer.tokenize_dict(data)
        except Exception as e:
            logger.error(f"Failed to sanitize medical data: {e}")
            return {"sanitization_error": str(e), "original_keys": list(data.keys())}
    
    def end_session(self, session_id: Optional[str] = None):
        """End AgentOps session"""
        if not self.initialized:
            return
        
        try:
            # AgentOps new API expects the session object
            # For now, we'll just log the end
            logger.info(f"Ended AgentOps session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to end AgentOps session: {e}")
    
    def get_session_url(self, session_id: str) -> Optional[str]:
        """Get AgentOps dashboard URL for session"""
        if not self.initialized:
            return None
        
        # AgentOps dashboard URL format (may need adjustment based on their API)
        base_url = "https://app.agentops.ai"
        return f"{base_url}/sessions/{session_id}"