"""
Fault Tolerance and Recovery System - Medical-Grade Resilience
============================================================

Sistema de tolerancia a fallos y recuperación para agentes médicos distribuidos
con mecanismos de failover automático y continuidad de servicio crítico.

Features:
- Circuit breaker patterns
- Automatic failover and recovery
- Health-based routing
- Medical data protection during failures
- Cascading failure prevention
- Service mesh resilience
- Disaster recovery protocols
"""

import asyncio
import time
import logging
import json
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import random
import aiohttp

from .protocol_layer import A2AMessage, MessagePriority, AuthLevel
from .agent_discovery_service import (
    AgentDiscoveryService, AgentRegistration, AgentStatus, ServiceQuery
)
from .load_balancer import MedicalLoadBalancer, RequestContext
from .health_monitoring import AgentHealthMonitor, HealthAlert, AlertSeverity
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("fault_tolerance")


class FailureType(Enum):
    """Types of system failures"""
    AGENT_UNRESPONSIVE = "agent_unresponsive"
    AGENT_OVERLOADED = "agent_overloaded"
    NETWORK_TIMEOUT = "network_timeout"
    PROCESSING_ERROR = "processing_error"
    MEDICAL_COMPLIANCE_VIOLATION = "medical_compliance_violation"
    DATA_CORRUPTION = "data_corruption"
    CASCADING_FAILURE = "cascading_failure"
    PARTIAL_OUTAGE = "partial_outage"
    TOTAL_OUTAGE = "total_outage"


class RecoveryStrategy(Enum):
    """Recovery strategies for different failure types"""
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER_TO_BACKUP = "failover_to_backup"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    EMERGENCY_PROTOCOL = "emergency_protocol"
    MANUAL_INTERVENTION = "manual_intervention"


class SystemMode(Enum):
    """System operational modes"""
    NORMAL = "normal"              # All systems operational
    DEGRADED = "degraded"          # Some services unavailable
    EMERGENCY = "emergency"        # Critical services only
    MAINTENANCE = "maintenance"    # Planned downtime
    RECOVERY = "recovery"          # Recovering from failure


@dataclass
class FailureEvent:
    """Record of a system failure"""
    failure_id: str
    failure_type: FailureType
    affected_agents: List[str]
    impact_level: str  # low, medium, high, critical
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Failure details
    error_message: str = ""
    stack_trace: Optional[str] = None
    medical_impact: bool = False
    patient_safety_risk: bool = False
    
    # Recovery information
    recovery_strategy: Optional[RecoveryStrategy] = None
    recovery_actions: List[str] = field(default_factory=list)
    recovery_time: Optional[float] = None
    
    # Medical context
    ongoing_medical_cases: List[str] = field(default_factory=list)
    phi_data_at_risk: bool = False
    compliance_implications: List[str] = field(default_factory=list)


@dataclass
class RecoveryAction:
    """Automated recovery action"""
    action_id: str
    action_type: str
    target_agents: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Execution
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    
    # Medical considerations
    requires_medical_approval: bool = False
    patient_safety_verified: bool = False


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker for individual agents/services"""
    service_id: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    
    # Thresholds
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    test_request_timeout: int = 5
    
    # Counters
    failure_count: int = 0
    success_count: int = 0
    
    # Timing
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Medical considerations
    medical_critical: bool = False
    emergency_override: bool = False
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker"""
        current_time = datetime.now(timezone.utc)
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if (self.last_failure_time and 
                (current_time - self.last_failure_time).total_seconds() > self.recovery_timeout):
                self.state = CircuitBreakerState.HALF_OPEN
                self.state_changed_at = current_time
                return True
            
            # Allow emergency override for medical critical services
            return self.emergency_override and self.medical_critical
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.failure_count = 0  # Reset failure count
        self.last_success_time = datetime.now(timezone.utc)
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Transition back to closed
            self.state = CircuitBreakerState.CLOSED
            self.state_changed_at = datetime.now(timezone.utc)
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if (self.state == CircuitBreakerState.CLOSED and 
            self.failure_count >= self.failure_threshold):
            # Transition to open
            self.state = CircuitBreakerState.OPEN
            self.state_changed_at = datetime.now(timezone.utc)
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Go back to open
            self.state = CircuitBreakerState.OPEN
            self.state_changed_at = datetime.now(timezone.utc)


class FaultToleranceManager:
    """
    Comprehensive fault tolerance and recovery system for medical agents
    """
    
    def __init__(self,
                 discovery_service: AgentDiscoveryService,
                 health_monitor: AgentHealthMonitor,
                 load_balancer: MedicalLoadBalancer):
        
        self.discovery_service = discovery_service
        self.health_monitor = health_monitor
        self.load_balancer = load_balancer
        
        # System state
        self.system_mode = SystemMode.NORMAL
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Failure tracking
        self.failure_history: deque = deque(maxlen=10000)
        self.active_failures: Dict[str, FailureEvent] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        
        # Configuration
        self.max_cascade_depth = 3
        self.emergency_fallback_agents = set()
        self.critical_services = set()
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Recovery callbacks
        self.recovery_callbacks: List[Callable[[FailureEvent], None]] = []
        
        # Statistics
        self.stats = {
            "total_failures": 0,
            "total_recoveries": 0,
            "mean_recovery_time": 0.0,
            "cascading_failures_prevented": 0,
            "medical_continuity_maintained": 0
        }
        
        # Audit service
        self.audit_service = AuditService()
        
        logger.info("Fault Tolerance Manager initialized")
    
    async def initialize(self):
        """Initialize fault tolerance system"""
        # Register for health alerts
        self.health_monitor.add_alert_callback(self._handle_health_alert)
        
        # Start background monitoring
        await self._start_background_tasks()
        
        # Initialize circuit breakers for known agents
        agents = await self.discovery_service.list_agents()
        for agent in agents:
            await self._create_circuit_breaker(agent.agent_id, agent.agent_type.value)
        
        logger.info("Fault tolerance system initialized")
    
    async def _start_background_tasks(self):
        """Start background monitoring and recovery tasks"""
        # System health monitoring
        health_task = asyncio.create_task(self._system_health_loop())
        self.background_tasks.add(health_task)
        health_task.add_done_callback(self.background_tasks.discard)
        
        # Failure detection
        detection_task = asyncio.create_task(self._failure_detection_loop())
        self.background_tasks.add(detection_task)
        detection_task.add_done_callback(self.background_tasks.discard)
        
        # Recovery execution
        recovery_task = asyncio.create_task(self._recovery_execution_loop())
        self.background_tasks.add(recovery_task)
        recovery_task.add_done_callback(self.background_tasks.discard)
        
        # Circuit breaker management
        circuit_task = asyncio.create_task(self._circuit_breaker_loop())
        self.background_tasks.add(circuit_task)
        circuit_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Fault tolerance background tasks started")
    
    async def _handle_health_alert(self, alert: HealthAlert):
        """Handle health alerts from monitoring system"""
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR]:
            await self._process_potential_failure(alert)
    
    async def _process_potential_failure(self, alert: HealthAlert):
        """Process potential failure from health alert"""
        failure_type = self._classify_failure_from_alert(alert)
        
        # Check if this is already a known failure
        failure_key = f"{alert.agent_id}_{failure_type.value}"
        if failure_key in self.active_failures:
            return  # Already handling this failure
        
        # Create failure event
        failure = FailureEvent(
            failure_id=failure_key,
            failure_type=failure_type,
            affected_agents=[alert.agent_id],
            impact_level=self._assess_impact_level(alert),
            detected_at=alert.timestamp,
            error_message=alert.message,
            medical_impact=self._assess_medical_impact(alert),
            patient_safety_risk=self._assess_patient_safety_risk(alert)
        )
        
        self.active_failures[failure_key] = failure
        self.failure_history.append(failure)
        self.stats["total_failures"] += 1
        
        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(failure)
        failure.recovery_strategy = recovery_strategy
        
        # Execute recovery
        await self._execute_recovery(failure)
        
        # Audit log
        await self.audit_service.log_event(
            AuditEventType.SYSTEM_FAILURE_DETECTED,
            {
                "failure_id": failure.failure_id,
                "failure_type": failure.failure_type.value,
                "affected_agents": failure.affected_agents,
                "impact_level": failure.impact_level,
                "medical_impact": failure.medical_impact
            },
            session_id="fault_tolerance"
        )
        
        logger.warning(f"Failure detected: {failure.failure_id} ({failure.failure_type.value})")
    
    def _classify_failure_from_alert(self, alert: HealthAlert) -> FailureType:
        """Classify failure type from health alert"""
        if "timeout" in alert.message.lower() or "unresponsive" in alert.message.lower():
            return FailureType.AGENT_UNRESPONSIVE
        elif "overload" in alert.message.lower() or "capacity" in alert.message.lower():
            return FailureType.AGENT_OVERLOADED
        elif "network" in alert.message.lower():
            return FailureType.NETWORK_TIMEOUT
        elif "compliance" in alert.message.lower():
            return FailureType.MEDICAL_COMPLIANCE_VIOLATION
        else:
            return FailureType.PROCESSING_ERROR
    
    def _assess_impact_level(self, alert: HealthAlert) -> str:
        """Assess impact level of failure"""
        if alert.severity == AlertSeverity.CRITICAL:
            return "critical"
        elif alert.severity == AlertSeverity.ERROR:
            return "high"
        elif alert.severity == AlertSeverity.WARNING:
            return "medium"
        else:
            return "low"
    
    def _assess_medical_impact(self, alert: HealthAlert) -> bool:
        """Assess if failure has medical impact"""
        # Check if agent handles medical data
        agent_profile = self.health_monitor.get_agent_health(alert.agent_id)
        if agent_profile:
            return (agent_profile.medical_compliance_score < 1.0 or
                    "medical" in agent_profile.agent_type.lower())
        return False
    
    def _assess_patient_safety_risk(self, alert: HealthAlert) -> bool:
        """Assess if failure poses patient safety risk"""
        # Critical alerts from medical agents pose patient safety risk
        return (alert.severity == AlertSeverity.CRITICAL and
                self._assess_medical_impact(alert))
    
    def _determine_recovery_strategy(self, failure: FailureEvent) -> RecoveryStrategy:
        """Determine appropriate recovery strategy for failure"""
        if failure.patient_safety_risk:
            return RecoveryStrategy.EMERGENCY_PROTOCOL
        
        elif failure.failure_type == FailureType.AGENT_UNRESPONSIVE:
            return RecoveryStrategy.FAILOVER_TO_BACKUP
        
        elif failure.failure_type == FailureType.AGENT_OVERLOADED:
            return RecoveryStrategy.GRACEFUL_DEGRADATION
        
        elif failure.failure_type == FailureType.NETWORK_TIMEOUT:
            return RecoveryStrategy.EXPONENTIAL_BACKOFF
        
        elif failure.failure_type == FailureType.MEDICAL_COMPLIANCE_VIOLATION:
            return RecoveryStrategy.MANUAL_INTERVENTION
        
        else:
            return RecoveryStrategy.CIRCUIT_BREAKER
    
    async def _execute_recovery(self, failure: FailureEvent):
        """Execute recovery strategy for failure"""
        strategy = failure.recovery_strategy
        
        if strategy == RecoveryStrategy.EMERGENCY_PROTOCOL:
            await self._execute_emergency_protocol(failure)
        
        elif strategy == RecoveryStrategy.FAILOVER_TO_BACKUP:
            await self._execute_failover(failure)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            await self._execute_graceful_degradation(failure)
        
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            await self._execute_exponential_backoff(failure)
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            await self._execute_circuit_breaker(failure)
        
        elif strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            await self._request_manual_intervention(failure)
        
        else:
            await self._execute_immediate_retry(failure)
    
    async def _execute_emergency_protocol(self, failure: FailureEvent):
        """Execute emergency protocol for patient safety"""
        logger.critical(f"Executing emergency protocol for failure: {failure.failure_id}")
        
        # Switch to emergency mode
        self.system_mode = SystemMode.EMERGENCY
        
        # Activate all fallback agents
        for agent_id in self.emergency_fallback_agents:
            await self._activate_fallback_agent(agent_id)
        
        # Reroute all critical medical traffic
        await self._reroute_critical_traffic(failure.affected_agents)
        
        # Create recovery action
        action = RecoveryAction(
            action_id=f"emergency_{failure.failure_id}",
            action_type="emergency_protocol",
            target_agents=failure.affected_agents,
            requires_medical_approval=True
        )
        
        self.recovery_actions[action.action_id] = action
        failure.recovery_actions.append("emergency_protocol_activated")
        
        # Notify medical staff
        await self._notify_medical_staff(failure)
    
    async def _execute_failover(self, failure: FailureEvent):
        """Execute failover to backup agents"""
        logger.warning(f"Executing failover for failure: {failure.failure_id}")
        
        for agent_id in failure.affected_agents:
            # Find backup agents
            backup_agents = await self._find_backup_agents(agent_id)
            
            if backup_agents:
                # Activate backup
                selected_backup = backup_agents[0]
                await self._activate_backup_agent(selected_backup, agent_id)
                
                # Update circuit breaker
                circuit_breaker = await self._get_circuit_breaker(agent_id)
                circuit_breaker.record_failure()
                
                failure.recovery_actions.append(f"failed_over_to_{selected_backup.agent_id}")
            else:
                logger.error(f"No backup agents available for {agent_id}")
                failure.recovery_actions.append(f"no_backup_available_for_{agent_id}")
    
    async def _execute_graceful_degradation(self, failure: FailureEvent):
        """Execute graceful degradation"""
        logger.info(f"Executing graceful degradation for failure: {failure.failure_id}")
        
        # Reduce load on affected agents
        for agent_id in failure.affected_agents:
            await self._reduce_agent_load(agent_id)
        
        # Switch to degraded mode if necessary
        if len(failure.affected_agents) > 1:
            self.system_mode = SystemMode.DEGRADED
        
        failure.recovery_actions.append("graceful_degradation_activated")
    
    async def _execute_exponential_backoff(self, failure: FailureEvent):
        """Execute exponential backoff retry"""
        logger.info(f"Executing exponential backoff for failure: {failure.failure_id}")
        
        # Schedule retry with exponential backoff
        retry_delay = 2 ** min(failure.affected_agents.__len__(), 5)  # Max 32 seconds
        
        action = RecoveryAction(
            action_id=f"retry_{failure.failure_id}",
            action_type="exponential_backoff_retry",
            target_agents=failure.affected_agents,
            parameters={"retry_delay": retry_delay},
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
        )
        
        self.recovery_actions[action.action_id] = action
        failure.recovery_actions.append(f"scheduled_retry_in_{retry_delay}s")
    
    async def _execute_circuit_breaker(self, failure: FailureEvent):
        """Execute circuit breaker pattern"""
        logger.info(f"Executing circuit breaker for failure: {failure.failure_id}")
        
        for agent_id in failure.affected_agents:
            circuit_breaker = await self._get_circuit_breaker(agent_id)
            circuit_breaker.record_failure()
            
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                failure.recovery_actions.append(f"circuit_breaker_opened_for_{agent_id}")
    
    async def _request_manual_intervention(self, failure: FailureEvent):
        """Request manual intervention for complex failures"""
        logger.warning(f"Requesting manual intervention for failure: {failure.failure_id}")
        
        # Create high-priority alert
        await self._create_intervention_alert(failure)
        
        failure.recovery_actions.append("manual_intervention_requested")
    
    async def _execute_immediate_retry(self, failure: FailureEvent):
        """Execute immediate retry"""
        logger.info(f"Executing immediate retry for failure: {failure.failure_id}")
        
        for agent_id in failure.affected_agents:
            # Test agent health
            agent_status = await self.discovery_service.get_agent_status(agent_id)
            if agent_status and agent_status.status == AgentStatus.HEALTHY:
                failure.recovery_actions.append(f"immediate_retry_successful_for_{agent_id}")
            else:
                failure.recovery_actions.append(f"immediate_retry_failed_for_{agent_id}")
    
    async def _find_backup_agents(self, failed_agent_id: str) -> List[AgentRegistration]:
        """Find suitable backup agents for failed agent"""
        # Get failed agent info
        failed_agent = await self.discovery_service.get_agent_status(failed_agent_id)
        if not failed_agent:
            return []
        
        # Find agents of same type
        query = ServiceQuery(
            agent_type=failed_agent.agent_type,
            exclude_agents=[failed_agent_id],
            medical_compliant_only=True
        )
        
        suitable_agents = await self.discovery_service.discover_agents(query)
        return suitable_agents
    
    async def _activate_backup_agent(self, backup_agent: AgentRegistration, failed_agent_id: str):
        """Activate backup agent to replace failed agent"""
        # Update routing to use backup agent
        # This would integrate with the load balancer to redirect traffic
        logger.info(f"Activated backup agent {backup_agent.agent_id} for {failed_agent_id}")
    
    async def _activate_fallback_agent(self, agent_id: str):
        """Activate emergency fallback agent"""
        logger.info(f"Activating emergency fallback agent: {agent_id}")
        # Implementation would activate standby agents
    
    async def _reroute_critical_traffic(self, failed_agents: List[str]):
        """Reroute critical medical traffic away from failed agents"""
        logger.info(f"Rerouting critical traffic away from: {failed_agents}")
        # Implementation would update load balancer routing rules
    
    async def _reduce_agent_load(self, agent_id: str):
        """Reduce load on overloaded agent"""
        logger.info(f"Reducing load on agent: {agent_id}")
        # Implementation would adjust load balancer weights
    
    async def _notify_medical_staff(self, failure: FailureEvent):
        """Notify medical staff of critical failure"""
        logger.critical(f"Notifying medical staff of critical failure: {failure.failure_id}")
        # Implementation would send alerts to medical team
    
    async def _create_intervention_alert(self, failure: FailureEvent):
        """Create alert for manual intervention"""
        logger.warning(f"Creating intervention alert for: {failure.failure_id}")
        # Implementation would create high-priority alert
    
    async def _create_circuit_breaker(self, agent_id: str, agent_type: str):
        """Create circuit breaker for agent"""
        if agent_id not in self.circuit_breakers:
            is_medical_critical = "medical" in agent_type.lower() or "clinical" in agent_type.lower()
            
            self.circuit_breakers[agent_id] = CircuitBreaker(
                service_id=agent_id,
                medical_critical=is_medical_critical,
                failure_threshold=3 if is_medical_critical else 5,
                recovery_timeout=30 if is_medical_critical else 60
            )
    
    async def _get_circuit_breaker(self, agent_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent"""
        if agent_id not in self.circuit_breakers:
            await self._create_circuit_breaker(agent_id, "unknown")
        return self.circuit_breakers[agent_id]
    
    async def _system_health_loop(self):
        """Monitor overall system health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._assess_system_health()
            except Exception as e:
                logger.error(f"System health monitoring error: {e}")
    
    async def _assess_system_health(self):
        """Assess overall system health and adjust mode"""
        health_summary = self.health_monitor.get_health_summary()
        
        critical_alerts = health_summary.get("active_alerts", {}).get("critical", 0)
        total_agents = health_summary.get("total_agents", 0)
        healthy_agents = health_summary.get("status_distribution", {}).get("excellent", 0)
        healthy_agents += health_summary.get("status_distribution", {}).get("good", 0)
        
        if total_agents == 0:
            return
        
        health_ratio = healthy_agents / total_agents
        
        # Determine system mode
        new_mode = self.system_mode
        
        if critical_alerts > 0 or health_ratio < 0.3:
            new_mode = SystemMode.EMERGENCY
        elif health_ratio < 0.7:
            new_mode = SystemMode.DEGRADED
        elif health_ratio > 0.9 and critical_alerts == 0:
            new_mode = SystemMode.NORMAL
        
        if new_mode != self.system_mode:
            logger.info(f"System mode changed: {self.system_mode.value} -> {new_mode.value}")
            self.system_mode = new_mode
    
    async def _failure_detection_loop(self):
        """Proactive failure detection"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._detect_potential_failures()
            except Exception as e:
                logger.error(f"Failure detection error: {e}")
    
    async def _detect_potential_failures(self):
        """Detect potential failures before they occur"""
        # Analyze trends and patterns to predict failures
        agents_health = self.health_monitor.get_all_agents_health()
        
        for agent_id, profile in agents_health.items():
            # Check for degrading trends
            if self._is_degrading_trend(profile):
                logger.warning(f"Degrading trend detected for agent {agent_id}")
                # Could trigger proactive recovery actions
    
    def _is_degrading_trend(self, profile) -> bool:
        """Check if agent shows degrading performance trend"""
        # Simplified trend analysis
        return (profile.status.value in ["warning", "critical"] or
                profile.medical_compliance_score < 0.95)
    
    async def _recovery_execution_loop(self):
        """Execute scheduled recovery actions"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._execute_scheduled_actions()
            except Exception as e:
                logger.error(f"Recovery execution error: {e}")
    
    async def _execute_scheduled_actions(self):
        """Execute scheduled recovery actions"""
        current_time = datetime.now(timezone.utc)
        
        for action_id, action in list(self.recovery_actions.items()):
            if (action.executed_at is None and 
                action.scheduled_at <= current_time):
                
                try:
                    await self._execute_recovery_action(action)
                    action.executed_at = current_time
                    action.success = True
                except Exception as e:
                    action.error_message = str(e)
                    action.success = False
                    logger.error(f"Recovery action {action_id} failed: {e}")
    
    async def _execute_recovery_action(self, action: RecoveryAction):
        """Execute specific recovery action"""
        if action.action_type == "exponential_backoff_retry":
            # Retry failed operations
            for agent_id in action.target_agents:
                # Test agent health
                agent_status = await self.discovery_service.get_agent_status(agent_id)
                if agent_status and agent_status.status == AgentStatus.HEALTHY:
                    circuit_breaker = await self._get_circuit_breaker(agent_id)
                    circuit_breaker.record_success()
    
    async def _circuit_breaker_loop(self):
        """Manage circuit breaker states"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._update_circuit_breakers()
            except Exception as e:
                logger.error(f"Circuit breaker management error: {e}")
    
    async def _update_circuit_breakers(self):
        """Update circuit breaker states based on current health"""
        for agent_id, circuit_breaker in self.circuit_breakers.items():
            # Check current agent health
            agent_profile = self.health_monitor.get_agent_health(agent_id)
            
            if agent_profile:
                if (agent_profile.status.value in ["excellent", "good"] and
                    circuit_breaker.state == CircuitBreakerState.OPEN):
                    
                    # Agent recovered, test it
                    if await self._test_agent_recovery(agent_id):
                        circuit_breaker.record_success()
                        logger.info(f"Circuit breaker closed for recovered agent {agent_id}")
    
    async def _test_agent_recovery(self, agent_id: str) -> bool:
        """Test if agent has recovered"""
        try:
            agent_status = await self.discovery_service.get_agent_status(agent_id)
            return agent_status and agent_status.status == AgentStatus.HEALTHY
        except Exception:
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "system_mode": self.system_mode.value,
            "active_failures": len(self.active_failures),
            "circuit_breakers": {
                agent_id: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "medical_critical": cb.medical_critical
                }
                for agent_id, cb in self.circuit_breakers.items()
            },
            "stats": self.stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_failure_history(self, limit: int = 100) -> List[FailureEvent]:
        """Get recent failure history"""
        return list(self.failure_history)[-limit:]
    
    async def shutdown(self):
        """Shutdown fault tolerance system"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        logger.info("Fault Tolerance Manager shutdown complete")


# Factory function
def create_fault_tolerance_manager(discovery_service: AgentDiscoveryService,
                                  health_monitor: AgentHealthMonitor,
                                  load_balancer: MedicalLoadBalancer) -> FaultToleranceManager:
    """Factory function to create fault tolerance manager"""
    return FaultToleranceManager(
        discovery_service=discovery_service,
        health_monitor=health_monitor,
        load_balancer=load_balancer
    )


__all__ = [
    'FaultToleranceManager',
    'FailureEvent',
    'RecoveryAction',
    'CircuitBreaker',
    'FailureType',
    'RecoveryStrategy',
    'SystemMode',
    'CircuitBreakerState',
    'create_fault_tolerance_manager'
]