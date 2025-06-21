"""
Agent Health Monitoring System - Distributed Health Tracking
==========================================================

Sistema avanzado de monitoreo de salud para agentes médicos distribuidos
con detección proactiva de fallos y recuperación automática.

Features:
- Real-time health monitoring
- Proactive failure detection
- Automatic recovery mechanisms
- Medical compliance monitoring
- Performance trend analysis
- Alert system integration
- Detailed health reporting
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import aiohttp
import psutil
import json

from .protocol_layer import A2AMessage, MessagePriority
from .agent_discovery_service import AgentDiscoveryService, AgentRegistration, AgentStatus
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("health_monitoring")


class HealthMetricType(Enum):
    """Types of health metrics"""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"
    QUEUE_LENGTH = "queue_length"
    CONNECTION_COUNT = "connection_count"
    MEDICAL_COMPLIANCE = "medical_compliance"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Overall health status"""
    EXCELLENT = "excellent"    # All metrics green
    GOOD = "good"             # Most metrics good
    WARNING = "warning"       # Some concerning metrics
    CRITICAL = "critical"     # Major issues detected
    FAILED = "failed"         # Agent not responding


@dataclass
class HealthMetric:
    """Individual health metric"""
    metric_type: HealthMetricType
    value: float
    timestamp: datetime
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    unit: str = ""
    description: str = ""


@dataclass
class HealthAlert:
    """Health monitoring alert"""
    alert_id: str
    agent_id: str
    severity: AlertSeverity
    metric_type: HealthMetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class AgentHealthProfile:
    """Comprehensive health profile for an agent"""
    agent_id: str
    agent_type: str
    status: HealthStatus
    last_check: datetime
    
    # Current metrics
    current_metrics: Dict[HealthMetricType, HealthMetric] = field(default_factory=dict)
    
    # Historical data (last 100 readings per metric)
    metric_history: Dict[HealthMetricType, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    
    # Alerts
    active_alerts: List[HealthAlert] = field(default_factory=list)
    alert_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    # Health trends
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Medical-specific metrics
    medical_compliance_score: float = 1.0
    phi_access_violations: int = 0
    audit_trail_completeness: float = 1.0
    encryption_status: bool = True


class HealthThresholds:
    """Default health thresholds for medical agents"""
    
    DEFAULT_THRESHOLDS = {
        HealthMetricType.RESPONSE_TIME: {
            "warning": 2.0,    # 2 seconds
            "critical": 5.0    # 5 seconds
        },
        HealthMetricType.ERROR_RATE: {
            "warning": 0.05,   # 5%
            "critical": 0.15   # 15%
        },
        HealthMetricType.CPU_USAGE: {
            "warning": 0.8,    # 80%
            "critical": 0.95   # 95%
        },
        HealthMetricType.MEMORY_USAGE: {
            "warning": 0.85,   # 85%
            "critical": 0.95   # 95%
        },
        HealthMetricType.DISK_USAGE: {
            "warning": 0.9,    # 90%
            "critical": 0.98   # 98%
        },
        HealthMetricType.QUEUE_LENGTH: {
            "warning": 100,
            "critical": 500
        },
        HealthMetricType.MEDICAL_COMPLIANCE: {
            "warning": 0.95,   # 95%
            "critical": 0.90   # 90%
        }
    }


class AgentHealthMonitor:
    """
    Comprehensive health monitoring system for medical agents
    """
    
    def __init__(self,
                 discovery_service: AgentDiscoveryService,
                 check_interval: int = 30,
                 detailed_check_interval: int = 300):
        
        self.discovery_service = discovery_service
        self.check_interval = check_interval  # Basic health check interval
        self.detailed_check_interval = detailed_check_interval  # Detailed metrics interval
        
        # Health data storage
        self.agent_profiles: Dict[str, AgentHealthProfile] = {}
        self.global_alerts: deque = deque(maxlen=10000)
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Statistics
        self.monitoring_stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "alerts_generated": 0,
            "agents_monitored": 0
        }
        
        # Audit service
        self.audit_service = AuditService()
        
        logger.info("Agent Health Monitor initialized")
    
    async def initialize(self):
        """Initialize health monitoring system"""
        # Start basic health check loop
        basic_task = asyncio.create_task(self._basic_health_check_loop())
        self.background_tasks.add(basic_task)
        basic_task.add_done_callback(self.background_tasks.discard)
        
        # Start detailed metrics loop
        detailed_task = asyncio.create_task(self._detailed_metrics_loop())
        self.background_tasks.add(detailed_task)
        detailed_task.add_done_callback(self.background_tasks.discard)
        
        # Start alert processing loop
        alert_task = asyncio.create_task(self._alert_processing_loop())
        self.background_tasks.add(alert_task)
        alert_task.add_done_callback(self.background_tasks.discard)
        
        # Start trend analysis loop
        trend_task = asyncio.create_task(self._trend_analysis_loop())
        self.background_tasks.add(trend_task)
        trend_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Health monitoring system initialized")
    
    async def _basic_health_check_loop(self):
        """Basic health check loop for all agents"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self._perform_basic_health_checks()
            except Exception as e:
                logger.error(f"Basic health check loop error: {e}")
    
    async def _detailed_metrics_loop(self):
        """Detailed metrics collection loop"""
        while True:
            try:
                await asyncio.sleep(self.detailed_check_interval)
                await self._collect_detailed_metrics()
            except Exception as e:
                logger.error(f"Detailed metrics loop error: {e}")
    
    async def _alert_processing_loop(self):
        """Process and dispatch alerts"""
        while True:
            try:
                await asyncio.sleep(60)  # Process alerts every minute
                await self._process_alerts()
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
    
    async def _trend_analysis_loop(self):
        """Analyze health trends"""
        while True:
            try:
                await asyncio.sleep(600)  # Analyze trends every 10 minutes
                await self._analyze_trends()
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")
    
    async def _perform_basic_health_checks(self):
        """Perform basic health checks on all registered agents"""
        agents = await self.discovery_service.list_agents()
        
        for agent in agents:
            try:
                await self._check_agent_basic_health(agent)
                self.monitoring_stats["successful_checks"] += 1
            except Exception as e:
                logger.error(f"Basic health check failed for {agent.agent_id}: {e}")
                self.monitoring_stats["failed_checks"] += 1
                await self._handle_health_check_failure(agent, str(e))
            
            self.monitoring_stats["total_checks"] += 1
        
        self.monitoring_stats["agents_monitored"] = len(agents)
    
    async def _check_agent_basic_health(self, agent: AgentRegistration):
        """Perform basic health check on single agent"""
        profile = self._get_or_create_profile(agent)
        
        # Ping test
        start_time = time.time()
        is_responsive = await self._ping_agent(agent)
        response_time = time.time() - start_time
        
        if is_responsive:
            # Update response time metric
            metric = HealthMetric(
                metric_type=HealthMetricType.RESPONSE_TIME,
                value=response_time,
                timestamp=datetime.now(timezone.utc),
                threshold_warning=HealthThresholds.DEFAULT_THRESHOLDS[HealthMetricType.RESPONSE_TIME]["warning"],
                threshold_critical=HealthThresholds.DEFAULT_THRESHOLDS[HealthMetricType.RESPONSE_TIME]["critical"],
                unit="seconds"
            )
            
            await self._update_metric(profile, metric)
            
            # Update agent status in discovery service
            await self.discovery_service.update_agent_health(
                agent.agent_id, 
                AgentStatus.HEALTHY,
                {"response_time": response_time}
            )
        else:
            # Agent not responsive
            await self._handle_unresponsive_agent(agent, profile)
    
    async def _collect_detailed_metrics(self):
        """Collect detailed metrics from all agents"""
        agents = await self.discovery_service.list_agents()
        
        for agent in agents:
            if agent.status in [AgentStatus.HEALTHY, AgentStatus.DEGRADED]:
                try:
                    await self._collect_agent_detailed_metrics(agent)
                except Exception as e:
                    logger.error(f"Detailed metrics collection failed for {agent.agent_id}: {e}")
    
    async def _collect_agent_detailed_metrics(self, agent: AgentRegistration):
        """Collect detailed metrics from single agent"""
        profile = self._get_or_create_profile(agent)
        
        try:
            # Get metrics from agent
            metrics_data = await self._fetch_agent_metrics(agent)
            
            if metrics_data:
                # Process each metric
                for metric_name, metric_value in metrics_data.items():
                    metric_type = self._map_metric_name_to_type(metric_name)
                    if metric_type:
                        thresholds = HealthThresholds.DEFAULT_THRESHOLDS.get(metric_type, {})
                        
                        metric = HealthMetric(
                            metric_type=metric_type,
                            value=metric_value,
                            timestamp=datetime.now(timezone.utc),
                            threshold_warning=thresholds.get("warning"),
                            threshold_critical=thresholds.get("critical")
                        )
                        
                        await self._update_metric(profile, metric)
                
                # Update medical compliance metrics
                await self._check_medical_compliance(agent, profile, metrics_data)
        
        except Exception as e:
            logger.error(f"Error collecting detailed metrics for {agent.agent_id}: {e}")
    
    async def _fetch_agent_metrics(self, agent: AgentRegistration) -> Optional[Dict[str, Any]]:
        """Fetch metrics from agent endpoint"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{agent.endpoint}/a2a/stats") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch metrics from {agent.agent_id}: {e}")
        
        return None
    
    async def _ping_agent(self, agent: AgentRegistration) -> bool:
        """Ping agent health endpoint"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{agent.endpoint}/a2a/health") as response:
                    return response.status == 200
        except Exception:
            return False
    
    def _get_or_create_profile(self, agent: AgentRegistration) -> AgentHealthProfile:
        """Get or create health profile for agent"""
        if agent.agent_id not in self.agent_profiles:
            self.agent_profiles[agent.agent_id] = AgentHealthProfile(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type.value,
                status=HealthStatus.GOOD,
                last_check=datetime.now(timezone.utc)
            )
        
        return self.agent_profiles[agent.agent_id]
    
    async def _update_metric(self, profile: AgentHealthProfile, metric: HealthMetric):
        """Update metric in agent profile"""
        # Store current metric
        profile.current_metrics[metric.metric_type] = metric
        
        # Add to history
        profile.metric_history[metric.metric_type].append({
            "value": metric.value,
            "timestamp": metric.timestamp
        })
        
        # Check thresholds and generate alerts
        await self._check_metric_thresholds(profile, metric)
        
        # Update overall health status
        await self._update_agent_health_status(profile)
        
        profile.last_check = datetime.now(timezone.utc)
    
    async def _check_metric_thresholds(self, profile: AgentHealthProfile, metric: HealthMetric):
        """Check if metric exceeds thresholds and generate alerts"""
        alert_severity = None
        threshold_exceeded = None
        
        # Check critical threshold
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            alert_severity = AlertSeverity.CRITICAL
            threshold_exceeded = metric.threshold_critical
        # Check warning threshold
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            alert_severity = AlertSeverity.WARNING
            threshold_exceeded = metric.threshold_warning
        
        if alert_severity:
            # Check if we already have an active alert for this metric
            existing_alert = next(
                (alert for alert in profile.active_alerts 
                 if alert.metric_type == metric.metric_type and not alert.resolved),
                None
            )
            
            if not existing_alert:
                # Create new alert
                alert = HealthAlert(
                    alert_id=f"{profile.agent_id}_{metric.metric_type.value}_{int(time.time())}",
                    agent_id=profile.agent_id,
                    severity=alert_severity,
                    metric_type=metric.metric_type,
                    message=f"{metric.metric_type.value} exceeded {alert_severity.value} threshold",
                    value=metric.value,
                    threshold=threshold_exceeded,
                    timestamp=metric.timestamp
                )
                
                profile.active_alerts.append(alert)
                profile.alert_history.append(alert)
                self.global_alerts.append(alert)
                
                self.monitoring_stats["alerts_generated"] += 1
                
                # Notify callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")
                
                # Log to audit
                await self.audit_service.log_event(
                    AuditEventType.ALERT_GENERATED,
                    {
                        "alert_id": alert.alert_id,
                        "agent_id": alert.agent_id,
                        "severity": alert.severity.value,
                        "metric_type": alert.metric_type.value,
                        "value": alert.value,
                        "threshold": alert.threshold
                    },
                    session_id="health_monitoring"
                )
        
        else:
            # Check if we can resolve existing alerts
            for alert in profile.active_alerts:
                if (alert.metric_type == metric.metric_type and 
                    not alert.resolved and
                    alert.severity == AlertSeverity.WARNING):
                    
                    # Resolve warning if below warning threshold
                    if (metric.threshold_warning and 
                        metric.value < metric.threshold_warning * 0.9):  # 10% hysteresis
                        
                        alert.resolved = True
                        alert.resolved_at = datetime.now(timezone.utc)
    
    async def _update_agent_health_status(self, profile: AgentHealthProfile):
        """Update overall health status for agent"""
        critical_alerts = [a for a in profile.active_alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved]
        warning_alerts = [a for a in profile.active_alerts if a.severity == AlertSeverity.WARNING and not a.resolved]
        
        if critical_alerts:
            profile.status = HealthStatus.CRITICAL
        elif warning_alerts:
            profile.status = HealthStatus.WARNING
        elif profile.current_metrics:
            # Calculate health score based on current metrics
            health_score = self._calculate_health_score(profile)
            
            if health_score >= 0.9:
                profile.status = HealthStatus.EXCELLENT
            elif health_score >= 0.7:
                profile.status = HealthStatus.GOOD
            elif health_score >= 0.5:
                profile.status = HealthStatus.WARNING
            else:
                profile.status = HealthStatus.CRITICAL
        else:
            profile.status = HealthStatus.GOOD  # No metrics yet
    
    def _calculate_health_score(self, profile: AgentHealthProfile) -> float:
        """Calculate overall health score (0-1) for agent"""
        scores = []
        
        for metric_type, metric in profile.current_metrics.items():
            if metric.threshold_critical and metric.threshold_warning:
                if metric.value >= metric.threshold_critical:
                    scores.append(0.0)  # Critical
                elif metric.value >= metric.threshold_warning:
                    # Scale between warning and critical
                    ratio = (metric.value - metric.threshold_warning) / (metric.threshold_critical - metric.threshold_warning)
                    scores.append(0.5 * (1 - ratio))  # 0.5 to 0.0
                else:
                    # Scale from 0.5 to 1.0 based on how close to warning
                    ratio = metric.value / metric.threshold_warning if metric.threshold_warning > 0 else 0
                    scores.append(0.5 + 0.5 * (1 - min(1.0, ratio)))  # 0.5 to 1.0
        
        return statistics.mean(scores) if scores else 1.0
    
    async def _check_medical_compliance(self, agent: AgentRegistration, profile: AgentHealthProfile, metrics_data: Dict[str, Any]):
        """Check medical compliance metrics"""
        compliance_score = 1.0
        
        # Check HIPAA compliance
        if not agent.hipaa_compliant:
            compliance_score -= 0.3
        
        # Check encryption status
        if not agent.encryption_enabled:
            compliance_score -= 0.2
        
        # Check audit trail
        if not agent.audit_enabled:
            compliance_score -= 0.3
        
        # Check PHI access violations (from metrics)
        phi_violations = metrics_data.get("phi_access_violations", 0)
        if phi_violations > 0:
            compliance_score -= min(0.2, phi_violations * 0.05)
        
        profile.medical_compliance_score = max(0.0, compliance_score)
        profile.phi_access_violations = phi_violations
        
        # Create compliance metric
        compliance_metric = HealthMetric(
            metric_type=HealthMetricType.MEDICAL_COMPLIANCE,
            value=profile.medical_compliance_score,
            timestamp=datetime.now(timezone.utc),
            threshold_warning=HealthThresholds.DEFAULT_THRESHOLDS[HealthMetricType.MEDICAL_COMPLIANCE]["warning"],
            threshold_critical=HealthThresholds.DEFAULT_THRESHOLDS[HealthMetricType.MEDICAL_COMPLIANCE]["critical"],
            unit="score"
        )
        
        await self._update_metric(profile, compliance_metric)
    
    async def _handle_unresponsive_agent(self, agent: AgentRegistration, profile: AgentHealthProfile):
        """Handle agent that's not responding"""
        profile.status = HealthStatus.FAILED
        
        # Create critical alert
        alert = HealthAlert(
            alert_id=f"{agent.agent_id}_unresponsive_{int(time.time())}",
            agent_id=agent.agent_id,
            severity=AlertSeverity.CRITICAL,
            metric_type=HealthMetricType.RESPONSE_TIME,
            message="Agent not responding to health checks",
            value=999.0,  # Placeholder for timeout
            threshold=5.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        profile.active_alerts.append(alert)
        self.global_alerts.append(alert)
        
        # Update discovery service
        await self.discovery_service.update_agent_health(agent.agent_id, AgentStatus.UNREACHABLE)
    
    async def _handle_health_check_failure(self, agent: AgentRegistration, error: str):
        """Handle health check failure"""
        profile = self._get_or_create_profile(agent)
        profile.status = HealthStatus.FAILED
        
        # Log the failure
        logger.warning(f"Health check failed for {agent.agent_id}: {error}")
    
    def _map_metric_name_to_type(self, metric_name: str) -> Optional[HealthMetricType]:
        """Map metric name from agent to HealthMetricType"""
        mapping = {
            "response_time": HealthMetricType.RESPONSE_TIME,
            "error_rate": HealthMetricType.ERROR_RATE,
            "throughput": HealthMetricType.THROUGHPUT,
            "cpu_usage": HealthMetricType.CPU_USAGE,
            "memory_usage": HealthMetricType.MEMORY_USAGE,
            "disk_usage": HealthMetricType.DISK_USAGE,
            "queue_length": HealthMetricType.QUEUE_LENGTH,
            "connection_count": HealthMetricType.CONNECTION_COUNT
        }
        
        return mapping.get(metric_name.lower())
    
    async def _process_alerts(self):
        """Process and manage alerts"""
        # Auto-resolve old alerts
        for profile in self.agent_profiles.values():
            for alert in profile.active_alerts:
                if not alert.resolved and alert.severity == AlertSeverity.WARNING:
                    # Auto-resolve warnings older than 30 minutes if no recent threshold breach
                    if (datetime.now(timezone.utc) - alert.timestamp).total_seconds() > 1800:
                        recent_metrics = profile.metric_history[alert.metric_type]
                        if recent_metrics:
                            recent_values = [m["value"] for m in list(recent_metrics)[-5:]]  # Last 5 readings
                            threshold = HealthThresholds.DEFAULT_THRESHOLDS.get(alert.metric_type, {}).get("warning")
                            
                            if threshold and all(v < threshold * 0.9 for v in recent_values):
                                alert.resolved = True
                                alert.resolved_at = datetime.now(timezone.utc)
    
    async def _analyze_trends(self):
        """Analyze health trends for all agents"""
        for profile in self.agent_profiles.values():
            await self._analyze_agent_trends(profile)
    
    async def _analyze_agent_trends(self, profile: AgentHealthProfile):
        """Analyze trends for specific agent"""
        trends = {}
        
        for metric_type, history in profile.metric_history.items():
            if len(history) >= 10:  # Need at least 10 data points
                values = [h["value"] for h in history]
                
                # Calculate trend
                trend = self._calculate_trend(values)
                trends[metric_type.value] = {
                    "direction": "increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable",
                    "slope": trend,
                    "volatility": statistics.stdev(values) if len(values) > 1 else 0
                }
        
        profile.trend_analysis = trends
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope using linear regression"""
        n = len(values)
        if n < 2:
            return 0.0
        
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def add_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """Remove alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_agent_health(self, agent_id: str) -> Optional[AgentHealthProfile]:
        """Get health profile for specific agent"""
        return self.agent_profiles.get(agent_id)
    
    def get_all_agents_health(self) -> Dict[str, AgentHealthProfile]:
        """Get health profiles for all agents"""
        return self.agent_profiles.copy()
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[HealthAlert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = []
        for profile in self.agent_profiles.values():
            for alert in profile.active_alerts:
                if not alert.resolved and (not severity or alert.severity == severity):
                    alerts.append(alert)
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        total_agents = len(self.agent_profiles)
        if total_agents == 0:
            return {"status": "no_agents", "agents": 0}
        
        status_counts = defaultdict(int)
        for profile in self.agent_profiles.values():
            status_counts[profile.status.value] += 1
        
        critical_alerts = len(self.get_active_alerts(AlertSeverity.CRITICAL))
        warning_alerts = len(self.get_active_alerts(AlertSeverity.WARNING))
        
        overall_status = "healthy"
        if critical_alerts > 0:
            overall_status = "critical"
        elif warning_alerts > 0:
            overall_status = "warning"
        elif status_counts["critical"] > 0:
            overall_status = "critical"
        elif status_counts["warning"] > 0:
            overall_status = "warning"
        
        return {
            "overall_status": overall_status,
            "total_agents": total_agents,
            "status_distribution": dict(status_counts),
            "active_alerts": {
                "critical": critical_alerts,
                "warning": warning_alerts
            },
            "monitoring_stats": self.monitoring_stats
        }
    
    async def shutdown(self):
        """Shutdown health monitoring system"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        logger.info("Agent Health Monitor shutdown complete")


# Factory function
def create_health_monitor(discovery_service: AgentDiscoveryService) -> AgentHealthMonitor:
    """Factory function to create health monitor"""
    return AgentHealthMonitor(discovery_service=discovery_service)


__all__ = [
    'AgentHealthMonitor',
    'AgentHealthProfile',
    'HealthAlert',
    'HealthMetric',
    'HealthMetricType',
    'AlertSeverity',
    'HealthStatus',
    'HealthThresholds',
    'create_health_monitor'
]