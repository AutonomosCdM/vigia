"""
Event handlers for webhook processing.

This module provides pre-built handlers for different webhook event types
that can be registered with the WebhookServer.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from .models import EventType, Severity

# Optional imports - these may not be available in all environments
try:
    from ..messaging.slack_notifier_refactored import SlackNotifier
except ImportError:
    SlackNotifier = None

try:
    from ..messaging.twilio_client_refactored import TwilioClient
except ImportError:
    TwilioClient = None

try:
    from ..db.supabase_client_refactored import SupabaseClient
except ImportError:
    SupabaseClient = None

try:
    from ..redis_layer.client_v2 import MedicalRedisClient as RedisClient
except ImportError:
    RedisClient = None

logger = logging.getLogger(__name__)


class WebhookHandlers:
    """Collection of webhook event handlers."""
    
    def __init__(self, 
                 slack_notifier: Optional[SlackNotifier] = None,
                 twilio_client: Optional[TwilioClient] = None,
                 db_client: Optional[SupabaseClient] = None,
                 redis_client: Optional[RedisClient] = None):
        """
        Initialize webhook handlers with optional integrations.
        
        Args:
            slack_notifier: Slack notification client
            twilio_client: WhatsApp/SMS client
            db_client: Database client
            redis_client: Redis cache client
        """
        self.slack = slack_notifier
        self.twilio = twilio_client
        self.db = db_client
        self.redis = redis_client
    
    async def handle_detection_completed(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle detection completed events.
        
        Actions:
        - Log detection results
        - Send notifications based on severity
        - Store in database
        - Update cache
        """
        patient_code = payload.get('patient_code', 'UNKNOWN')
        risk_level = payload.get('risk_level', 'LOW')
        detections = payload.get('detections', [])
        
        logger.info(f"Detection completed for patient {patient_code}")
        logger.info(f"Risk level: {risk_level}, Detections: {len(detections)}")
        
        # Send notifications for high-risk cases
        if risk_level in ['HIGH', 'CRITICAL']:
            await self._send_urgent_notifications(patient_code, risk_level, detections)
        
        # Store in database
        if self.db:
            try:
                await self._store_detection_results(payload)
            except Exception as e:
                logger.error(f"Failed to store detection results: {e}")
        
        # Update cache
        if self.redis:
            try:
                await self._update_detection_cache(patient_code, payload)
            except Exception as e:
                logger.error(f"Failed to update cache: {e}")
        
        return {
            "status": "processed",
            "actions_taken": {
                "notifications_sent": risk_level in ['HIGH', 'CRITICAL'],
                "stored_in_db": self.db is not None,
                "cached": self.redis is not None
            }
        }
    
    async def handle_detection_failed(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle detection failure events.
        
        Actions:
        - Log error details
        - Notify technical team
        - Track failure metrics
        """
        patient_code = payload.get('patient_code', 'UNKNOWN')
        error = payload.get('error', 'Unknown error')
        image_path = payload.get('image_path', 'N/A')
        
        logger.error(f"Detection failed for patient {patient_code}: {error}")
        
        # Send technical notification
        if self.slack:
            try:
                await self.slack.send_error_notification(
                    title="Detection Failure",
                    error_message=error,
                    context={
                        "patient_code": patient_code,
                        "image_path": image_path,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send error notification: {e}")
        
        # Track failure in database
        if self.db:
            try:
                await self._track_failure(patient_code, error, payload)
            except Exception as e:
                logger.error(f"Failed to track failure: {e}")
        
        return {
            "status": "acknowledged",
            "error_logged": True,
            "notifications_sent": self.slack is not None
        }
    
    async def handle_patient_updated(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle patient update events.
        
        Actions:
        - Update patient records
        - Notify care team
        - Update patient history
        """
        patient_code = payload.get('patient_code')
        update_type = payload.get('update_type')
        changes = payload.get('changes', {})
        
        logger.info(f"Patient {patient_code} updated: {update_type}")
        
        # Update database
        if self.db and patient_code:
            try:
                await self._update_patient_record(patient_code, changes)
            except Exception as e:
                logger.error(f"Failed to update patient record: {e}")
        
        # Send notifications for significant changes
        if update_type in ['status_change', 'risk_escalation']:
            await self._notify_care_team(patient_code, update_type, changes)
        
        # Update cache
        if self.redis and patient_code:
            try:
                await self._invalidate_patient_cache(patient_code)
            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")
        
        return {
            "status": "processed",
            "update_type": update_type,
            "notifications_sent": update_type in ['status_change', 'risk_escalation']
        }
    
    async def handle_protocol_triggered(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle medical protocol trigger events.
        
        Actions:
        - Execute protocol actions
        - Notify medical team
        - Create protocol tasks
        - Log protocol activation
        """
        protocol_name = payload.get('protocol_name')
        patient_code = payload.get('patient_code')
        trigger_reason = payload.get('trigger_reason')
        actions = payload.get('actions', [])
        
        logger.warning(f"Protocol triggered: {protocol_name} for patient {patient_code}")
        logger.warning(f"Reason: {trigger_reason}")
        
        # Send urgent notifications
        await self._send_protocol_notifications(protocol_name, patient_code, trigger_reason)
        
        # Create tasks for each protocol action
        tasks_created = []
        for action in actions:
            task_id = await self._create_protocol_task(patient_code, protocol_name, action)
            if task_id:
                tasks_created.append(task_id)
        
        # Log protocol activation
        if self.db:
            try:
                await self._log_protocol_activation(
                    patient_code, protocol_name, trigger_reason, actions
                )
            except Exception as e:
                logger.error(f"Failed to log protocol activation: {e}")
        
        return {
            "status": "activated",
            "protocol": protocol_name,
            "tasks_created": len(tasks_created),
            "notifications_sent": True
        }
    
    async def handle_analysis_ready(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle analysis ready events.
        
        Actions:
        - Notify requesting user/system
        - Update analysis status
        - Trigger dependent workflows
        """
        analysis_id = payload.get('analysis_id')
        patient_code = payload.get('patient_code')
        analysis_type = payload.get('analysis_type')
        results_url = payload.get('results_url')
        
        logger.info(f"Analysis ready: {analysis_type} for patient {patient_code}")
        
        # Update analysis status
        if self.db and analysis_id:
            try:
                await self._update_analysis_status(analysis_id, 'completed', results_url)
            except Exception as e:
                logger.error(f"Failed to update analysis status: {e}")
        
        # Send notification
        if self.slack:
            try:
                await self.slack.send_analysis_ready_notification(
                    patient_code, analysis_type, results_url
                )
            except Exception as e:
                logger.error(f"Failed to send analysis notification: {e}")
        
        # Trigger dependent workflows
        dependent_analyses = payload.get('triggers_analyses', [])
        for dependent in dependent_analyses:
            await self._trigger_dependent_analysis(patient_code, dependent)
        
        return {
            "status": "processed",
            "analysis_id": analysis_id,
            "notifications_sent": self.slack is not None,
            "triggered_workflows": len(dependent_analyses)
        }
    
    # Helper methods
    
    async def _send_urgent_notifications(self, patient_code: str, risk_level: str, detections: list):
        """Send urgent notifications for high-risk detections."""
        # Slack notification
        if self.slack:
            message = f"⚠️ {risk_level} risk detection for patient {patient_code}"
            details = f"Found {len(detections)} pressure injuries"
            
            # Add stage information
            stages = [d.get('stage', 0) for d in detections]
            if stages:
                details += f"\nStages detected: {', '.join(map(str, sorted(set(stages))))}"
            
            await self.slack.send_notification(message, details)
        
        # Log critical cases for audit trail
        if risk_level == 'CRITICAL':
            logger.audit("critical_medical_alert", {
                "patient_code": patient_code[:8] + "***",  # Anonymized
                "risk_level": risk_level,
                "alert_type": "critical_pressure_injury_detection",
                "requires_immediate_attention": True,
                "escalation_required": True,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _store_detection_results(self, payload: Dict[str, Any]):
        """Store detection results in database."""
        # Implementation depends on your database schema
        pass
    
    async def _update_detection_cache(self, patient_code: str, payload: Dict[str, Any]):
        """Update detection cache in Redis."""
        if self.redis:
            cache_key = f"detection:latest:{patient_code}"
            await self.redis.set(cache_key, payload, ttl=3600)  # 1 hour TTL
    
    async def _track_failure(self, patient_code: str, error: str, payload: Dict[str, Any]):
        """Track detection failure in database."""
        # Implementation depends on your database schema
        pass
    
    async def _update_patient_record(self, patient_code: str, changes: Dict[str, Any]):
        """Update patient record with changes."""
        # Implementation depends on your database schema
        pass
    
    async def _notify_care_team(self, patient_code: str, update_type: str, changes: Dict[str, Any]):
        """Log care team notifications for audit trail."""
        # Anonymize patient code for logging
        anonymized_patient = patient_code[:8] + "***"
        
        logger.audit("care_team_notification", {
            "anonymized_patient": anonymized_patient,
            "update_type": update_type,
            "changes_count": len(changes) if isinstance(changes, dict) else 1,
            "notification_type": "patient_update",
            "timestamp": datetime.now().isoformat()
        })
        
        # Also log to slack if available (audit purposes)
        if self.slack:
            try:
                message = f"Patient {anonymized_patient} - {update_type.replace('_', ' ').title()}"
                await self.slack.send_notification(message, str(changes))
            except Exception as e:
                logger.error("slack_care_team_notification_failed", {
                    "update_type": update_type,
                    "error": str(e)
                })
    
    async def _invalidate_patient_cache(self, patient_code: str):
        """Invalidate patient cache entries."""
        if self.redis:
            pattern = f"patient:{patient_code}:*"
            await self.redis.delete_pattern(pattern)
    
    async def _send_protocol_notifications(self, protocol_name: str, patient_code: str, reason: str):
        """Log protocol activation for audit trail."""
        # Log protocol activation with anonymized patient data
        anonymized_patient = patient_code[:8] + "***"
        
        logger.audit("medical_protocol_activated", {
            "protocol_name": protocol_name,
            "anonymized_patient": anonymized_patient,
            "activation_reason": reason,
            "urgency_level": "high",
            "requires_immediate_response": True,
            "escalation_triggered": True,
            "timestamp": datetime.now().isoformat()
        })
        
        # Also log to slack if available (audit purposes)
        if self.slack:
            try:
                message = f"🚨 Medical Protocol Activated: {protocol_name}"
                details = f"Patient: {anonymized_patient}\nReason: {reason}"
                await self.slack.send_urgent_notification(message, details)
            except Exception as e:
                logger.error("slack_notification_failed", {
                    "protocol": protocol_name,
                    "error": str(e)
                })
    
    async def _create_protocol_task(self, patient_code: str, protocol_name: str, action: str) -> Optional[str]:
        """Create a task for protocol action."""
        # Implementation depends on your task management system
        logger.info(f"Creating task: {action} for {patient_code} ({protocol_name})")
        return f"task-{datetime.now().timestamp()}"
    
    async def _log_protocol_activation(self, patient_code: str, protocol_name: str, 
                                     reason: str, actions: list):
        """Log protocol activation in database."""
        # Implementation depends on your database schema
        pass
    
    async def _update_analysis_status(self, analysis_id: str, status: str, results_url: str):
        """Update analysis status in database."""
        # Implementation depends on your database schema
        pass
    
    async def _trigger_dependent_analysis(self, patient_code: str, analysis_type: str):
        """Trigger dependent analysis workflow."""
        logger.info(f"Triggering {analysis_type} analysis for {patient_code}")
        # Implementation depends on your workflow system


def create_default_handlers(config: Optional[Dict[str, Any]] = None) -> WebhookHandlers:
    """
    Create webhook handlers with default configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured WebhookHandlers instance
    """
    config = config or {}
    
    # Initialize integrations based on config
    slack = None
    twilio = None
    db = None
    redis = None
    
    if config.get('enable_slack') and SlackNotifier:
        try:
            slack = SlackNotifier()
        except Exception as e:
            logger.warning(f"Failed to initialize Slack: {e}")
    
    # Twilio/WhatsApp integration removed for MCP compliance
    # All notifications now go through audit logging
    logger.info("Twilio/WhatsApp integration disabled for MCP compliance")
    
    if config.get('enable_db') and SupabaseClient:
        try:
            db = SupabaseClient()
        except Exception as e:
            logger.warning(f"Failed to initialize database: {e}")
    
    if config.get('enable_redis') and RedisClient:
        try:
            redis = RedisClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}")
    
    return WebhookHandlers(
        slack_notifier=slack,
        twilio_client=twilio,
        db_client=db,
        redis_client=redis
    )