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
        token_id = payload.get('token_id', payload.get('patient_code', 'UNKNOWN'))  # Batman token
        risk_level = payload.get('risk_level', 'LOW')
        detections = payload.get('detections', [])
        
        logger.info(f"Detection completed for token {token_id}")
        logger.info(f"Risk level: {risk_level}, Detections: {len(detections)}")
        
        # Send notifications for high-risk cases
        if risk_level in ['HIGH', 'CRITICAL']:
            await self._send_urgent_notifications(token_id, risk_level, detections)
        
        # Store in database
        if self.db:
            try:
                await self._store_detection_results(payload)
            except Exception as e:
                logger.error(f"Failed to store detection results: {e}")
        
        # Update cache
        if self.redis:
            try:
                await self._update_detection_cache(token_id, payload)
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
        token_id = payload.get('token_id', payload.get('patient_code', 'UNKNOWN'))  # Batman token
        error = payload.get('error', 'Unknown error')
        image_path = payload.get('image_path', 'N/A')
        
        logger.error(f"Detection failed for token {token_id}: {error}")
        
        # Send technical notification
        if self.slack:
            try:
                await self.slack.send_error_notification(
                    title="Detection Failure",
                    error_message=error,
                    context={
                        "token_id": token_id,  # Batman token (HIPAA compliant)
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
        token_id = payload.get('token_id', payload.get('patient_code'))  # Batman token
        update_type = payload.get('update_type')
        changes = payload.get('changes', {})
        
        logger.info(f"Token {token_id} updated: {update_type}")
        
        # Update database
        if self.db and token_id:
            try:
                await self._update_patient_record(token_id, changes)
            except Exception as e:
                logger.error(f"Failed to update patient record: {e}")
        
        # Send notifications for significant changes
        if update_type in ['status_change', 'risk_escalation']:
            await self._notify_care_team(token_id, update_type, changes)
        
        # Update cache
        if self.redis and token_id:
            try:
                await self._invalidate_patient_cache(token_id)
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
        token_id = payload.get('token_id', payload.get('patient_code'))  # Batman token
        trigger_reason = payload.get('trigger_reason')
        actions = payload.get('actions', [])
        
        logger.warning(f"Protocol triggered: {protocol_name} for token {token_id}")
        logger.warning(f"Reason: {trigger_reason}")
        
        # Send urgent notifications
        await self._send_protocol_notifications(protocol_name, token_id, trigger_reason)
        
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
        
        # WhatsApp notification for critical cases
        if self.twilio and risk_level == 'CRITICAL':
            message = f"🚨 CRITICAL: Patient {patient_code} requires immediate attention. Multiple stage 3+ pressure injuries detected."
            await self.twilio.send_whatsapp_alert(message)
    
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
        """Notify care team about patient updates."""
        if self.slack:
            message = f"Patient {patient_code} - {update_type.replace('_', ' ').title()}"
            await self.slack.send_notification(message, str(changes))
    
    async def _invalidate_patient_cache(self, patient_code: str):
        """Invalidate patient cache entries."""
        if self.redis:
            pattern = f"patient:{patient_code}:*"
            await self.redis.delete_pattern(pattern)
    
    async def _send_protocol_notifications(self, protocol_name: str, patient_code: str, reason: str):
        """Send notifications about protocol activation."""
        message = f"🚨 Medical Protocol Activated: {protocol_name}"
        details = f"Patient: {patient_code}\nReason: {reason}"
        
        # Send to all channels
        tasks = []
        
        if self.slack:
            tasks.append(self.slack.send_urgent_notification(message, details))
        
        if self.twilio:
            sms_message = f"URGENT: {protocol_name} activated for patient {patient_code}. {reason}"
            tasks.append(self.twilio.send_sms_alert(sms_message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
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

    async def handle_fase2_completion(self, event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle FASE 2 completion events (Image + Voice analysis complete).
        
        Actions:
        - Process multimodal analysis results
        - Generate comprehensive medical assessment
        - Send enhanced notifications with combined insights
        - Trigger FASE 3 (medical team notifications)
        - Store multimodal results in Processing Database
        """
        token_id = payload.get('token_id', 'UNKNOWN')  # Batman token
        image_analysis = payload.get('image_analysis', {})
        voice_analysis = payload.get('voice_analysis', {})
        enhanced_assessment = payload.get('enhanced_assessment', {})
        
        logger.info(f"FASE 2 completed for token {token_id} - Multimodal analysis ready")
        
        # Extract key metrics from combined analysis
        combined_confidence = enhanced_assessment.get('confidence', 0)
        urgency_level = enhanced_assessment.get('urgency_level', 'normal')
        multimodal_available = enhanced_assessment.get('multimodal_available', False)
        primary_concerns = enhanced_assessment.get('primary_concerns', [])
        
        # Log multimodal completion
        analysis_type = "multimodal" if multimodal_available else "image_only"
        logger.info(f"Analysis type: {analysis_type}, Confidence: {combined_confidence:.2f}, Urgency: {urgency_level}")
        
        # Assess combined risk level for notifications
        combined_risk = self._assess_combined_risk(image_analysis, voice_analysis, enhanced_assessment)
        
        # Send enhanced notifications if high-risk
        notifications_sent = False
        if combined_risk in ['HIGH', 'CRITICAL']:
            await self._send_multimodal_urgent_notifications(
                token_id, combined_risk, image_analysis, voice_analysis, enhanced_assessment
            )
            notifications_sent = True
            logger.info(f"Urgent notifications sent for {token_id} - Risk level: {combined_risk}")
        
        # Store multimodal results in Processing Database (Batman tokens only)
        if self.db:
            try:
                await self._store_multimodal_results(payload)
                logger.info(f"Multimodal results stored for token {token_id}")
            except Exception as e:
                logger.error(f"Failed to store multimodal results: {e}")
        
        # Update cache with enhanced assessment
        if self.redis:
            try:
                await self._cache_multimodal_assessment(token_id, enhanced_assessment)
            except Exception as e:
                logger.error(f"Failed to cache multimodal assessment: {e}")
        
        # Trigger FASE 3 (medical team notifications) if criteria met
        fase3_triggered = False
        if self._should_trigger_fase3(combined_risk, enhanced_assessment):
            await self._trigger_fase3_notifications(token_id, enhanced_assessment)
            fase3_triggered = True
            logger.info(f"FASE 3 triggered for token {token_id}")
        
        return {
            "status": "fase2_completed",
            "token_id": token_id,
            "analysis_type": analysis_type,
            "combined_risk_level": combined_risk,
            "combined_confidence": combined_confidence,
            "urgency_level": urgency_level,
            "multimodal_analysis": multimodal_available,
            "notifications_sent": notifications_sent,
            "fase3_triggered": fase3_triggered,
            "primary_concerns_count": len(primary_concerns),
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _assess_combined_risk(self, image_analysis: Dict[str, Any], 
                            voice_analysis: Dict[str, Any], 
                            enhanced_assessment: Dict[str, Any]) -> str:
        """Assess combined risk level from multimodal analysis"""
        urgency_level = enhanced_assessment.get('urgency_level', 'normal')
        confidence = enhanced_assessment.get('confidence', 0)
        
        # Map urgency levels to risk levels
        urgency_to_risk = {
            'critical': 'CRITICAL',
            'high': 'HIGH', 
            'elevated': 'MEDIUM',
            'normal': 'LOW'
        }
        
        base_risk = urgency_to_risk.get(urgency_level, 'LOW')
        
        # Enhance risk assessment with confidence
        if confidence >= 0.9 and base_risk in ['MEDIUM', 'HIGH']:
            if base_risk == 'MEDIUM':
                return 'HIGH'
            elif base_risk == 'HIGH':
                return 'CRITICAL'
        
        # Check for specific voice indicators that elevate risk
        if voice_analysis.get('voice_available'):
            medical_assessment = voice_analysis.get('medical_assessment', {})
            if medical_assessment.get('follow_up_required') and base_risk == 'LOW':
                return 'MEDIUM'
        
        return base_risk
    
    async def _send_multimodal_urgent_notifications(self, token_id: str, risk_level: str,
                                                  image_analysis: Dict[str, Any],
                                                  voice_analysis: Dict[str, Any],
                                                  enhanced_assessment: Dict[str, Any]):
        """Send urgent notifications with multimodal context"""
        if not self.slack:
            logger.warning("Slack not configured, skipping multimodal notifications")
            return
        
        # Prepare enhanced notification message
        message = f"🚨 FASE 2 COMPLETED - MULTIMODAL ANALYSIS\n"
        message += f"Patient Token: {token_id}\n"
        message += f"Risk Level: {risk_level}\n"
        message += f"Analysis Type: {'Multimodal (Image + Voice)' if voice_analysis.get('voice_available') else 'Image Only'}\n"
        message += f"Confidence: {enhanced_assessment.get('confidence', 0):.2f}\n"
        message += f"Urgency: {enhanced_assessment.get('urgency_level', 'normal').upper()}\n"
        
        # Add primary concerns
        concerns = enhanced_assessment.get('primary_concerns', [])
        if concerns:
            message += f"\nPrimary Concerns:\n"
            for concern in concerns[:3]:  # Limit to top 3
                message += f"• {concern}\n"
        
        # Add medical recommendations
        recommendations = enhanced_assessment.get('medical_recommendations', [])
        if recommendations:
            message += f"\nRecommendations:\n"
            for rec in recommendations[:3]:  # Limit to top 3
                message += f"• {rec}\n"
        
        try:
            await self.slack.send_urgent_alert(
                message=message,
                patient_id=token_id,
                priority=risk_level
            )
        except Exception as e:
            logger.error(f"Failed to send multimodal Slack notification: {e}")
    
    async def _store_multimodal_results(self, payload: Dict[str, Any]):
        """Store multimodal analysis results in Processing Database"""
        token_id = payload.get('token_id')
        
        # Prepare multimodal record for storage
        multimodal_record = {
            'token_id': token_id,  # Batman token (NO PHI)
            'analysis_type': 'multimodal',
            'image_analysis': payload.get('image_analysis', {}),
            'voice_analysis': payload.get('voice_analysis', {}),
            'enhanced_assessment': payload.get('enhanced_assessment', {}),
            'fase2_completed': True,
            'processing_timestamp': datetime.now().isoformat(),
            'hipaa_compliant': True,
            'tokenization_method': 'batman'
        }
        
        # Store in multimodal_analyses table
        await self.db.insert('multimodal_analyses', multimodal_record)
    
    async def _cache_multimodal_assessment(self, token_id: str, enhanced_assessment: Dict[str, Any]):
        """Cache enhanced assessment for quick access"""
        cache_key = f"enhanced_assessment:{token_id}"
        await self.redis.set(cache_key, enhanced_assessment, expire=3600)  # 1 hour cache
    
    def _should_trigger_fase3(self, risk_level: str, enhanced_assessment: Dict[str, Any]) -> bool:
        """Determine if FASE 3 should be triggered"""
        # Trigger FASE 3 for high-risk cases or when follow-up is explicitly required
        if risk_level in ['HIGH', 'CRITICAL']:
            return True
        
        if enhanced_assessment.get('follow_up_required', False):
            return True
        
        # Trigger if confidence is high and there are concerns
        confidence = enhanced_assessment.get('confidence', 0)
        concerns = enhanced_assessment.get('primary_concerns', [])
        
        return confidence >= 0.8 and len(concerns) >= 2
    
    async def _trigger_fase3_notifications(self, token_id: str, enhanced_assessment: Dict[str, Any]):
        """Trigger FASE 3 medical team notifications"""
        logger.info(f"Triggering FASE 3 notifications for token {token_id}")
        
        # This would integrate with the medical team notification system
        # For now, log the trigger event
        urgency = enhanced_assessment.get('urgency_level', 'normal')
        confidence = enhanced_assessment.get('confidence', 0)
        
        logger.info(f"FASE 3 triggered - Token: {token_id}, Urgency: {urgency}, Confidence: {confidence:.2f}")
        
        # TODO: Integrate with actual FASE 3 notification system
        # This could trigger:
        # - Medical team Slack notifications
        # - Assignment to on-call physician
        # - Integration with hospital systems
        # - Escalation protocols


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
    
    if config.get('enable_twilio') and TwilioClient:
        try:
            twilio = TwilioClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Twilio: {e}")
    
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