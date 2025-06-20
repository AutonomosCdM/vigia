"""
Automated Security Monitoring and Alerting System for Vigia Medical AI
Real-time security monitoring with medical-grade compliance alerts
"""

import os
import time
import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
from pathlib import Path

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    HAS_SLACK = True
except ImportError:
    HAS_SLACK = False

try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    HAS_EMAIL = True
except ImportError:
    HAS_EMAIL = False

from vigia_detect.utils.audit_service import AuditService, AuditEventType, AuditLevel
from vigia_detect.utils.secrets_manager import get_secret

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of security alerts"""
    AUTHENTICATION_FAILURE = "auth_failure"
    BRUTE_FORCE_ATTACK = "brute_force"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    SYSTEM_COMPROMISE = "system_compromise"
    MEDICAL_DATA_ACCESS = "medical_data_access"
    COMPLIANCE_VIOLATION = "compliance_violation"
    INFRASTRUCTURE_ISSUE = "infrastructure_issue"
    VULNERABILITY_DETECTED = "vulnerability_detected"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    source: str
    affected_systems: List[str]
    indicators: Dict[str, Any]
    remediation_steps: List[str]
    medical_impact: bool = False
    phi_involved: bool = False
    auto_resolved: bool = False
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data


class SecurityMetrics:
    """Security metrics tracking"""
    
    def __init__(self):
        """Initialize metrics tracking"""
        self.metrics = defaultdict(int)
        self.time_series = defaultdict(lambda: deque(maxlen=1440))  # 24 hours of minutes
        self.last_reset = datetime.utcnow()
    
    def increment(self, metric: str, value: int = 1, timestamp: Optional[datetime] = None):
        """Increment metric counter"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self.metrics[metric] += value
        self.time_series[metric].append((timestamp, value))
    
    def get_metric(self, metric: str) -> int:
        """Get current metric value"""
        return self.metrics[metric]
    
    def get_rate(self, metric: str, window_minutes: int = 60) -> float:
        """Get metric rate per minute over time window"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=window_minutes)
        
        values = [
            value for timestamp, value in self.time_series[metric]
            if timestamp >= cutoff
        ]
        
        return sum(values) / window_minutes if values else 0.0
    
    def reset_daily_metrics(self):
        """Reset daily metrics"""
        now = datetime.utcnow()
        if (now - self.last_reset).days >= 1:
            daily_metrics = [
                "login_attempts", "login_failures", "api_requests",
                "security_events", "alerts_generated"
            ]
            
            for metric in daily_metrics:
                self.metrics[metric] = 0
            
            self.last_reset = now


class SecurityMonitor:
    """Main security monitoring system"""
    
    def __init__(self):
        """Initialize security monitor"""
        self.audit = AuditService()
        self.metrics = SecurityMetrics()
        self.alerts = {}
        self.alert_handlers = []
        self.rules = []
        self.running = False
        self.monitor_thread = None
        
        # Rate limiting for alerts
        self.alert_counts = defaultdict(int)
        self.alert_windows = defaultdict(lambda: datetime.utcnow())
        
        # Configuration
        self.config = {
            "max_alerts_per_hour": 10,
            "brute_force_threshold": 5,
            "brute_force_window": 300,  # 5 minutes
            "suspicious_activity_threshold": 10,
            "medical_alert_priority": True,
            "auto_resolution_enabled": True
        }
        
        # Load monitoring rules
        self._load_monitoring_rules()
        
        # Setup alert handlers
        self._setup_alert_handlers()
    
    def _load_monitoring_rules(self):
        """Load security monitoring rules"""
        
        # Authentication monitoring rules
        self.rules.extend([
            {
                "name": "brute_force_detection",
                "condition": lambda: self.metrics.get_rate("login_failures") > self.config["brute_force_threshold"],
                "alert_type": AlertType.BRUTE_FORCE_ATTACK,
                "severity": AlertSeverity.HIGH,
                "description": "Multiple failed login attempts detected"
            },
            {
                "name": "suspicious_login_pattern",
                "condition": lambda: self.metrics.get_rate("login_attempts") > 50,
                "alert_type": AlertType.SUSPICIOUS_ACTIVITY,
                "severity": AlertSeverity.MEDIUM,
                "description": "Unusual login activity pattern detected"
            },
            {
                "name": "unauthorized_admin_access",
                "condition": lambda: self.metrics.get("unauthorized_admin_attempts") > 0,
                "alert_type": AlertType.UNAUTHORIZED_ACCESS,
                "severity": AlertSeverity.CRITICAL,
                "description": "Unauthorized administrative access attempts"
            }
        ])
        
        # Medical data monitoring rules
        self.rules.extend([
            {
                "name": "excessive_medical_data_access",
                "condition": lambda: self.metrics.get_rate("medical_data_access") > 100,
                "alert_type": AlertType.MEDICAL_DATA_ACCESS,
                "severity": AlertSeverity.HIGH,
                "description": "Excessive medical data access detected",
                "medical_impact": True
            },
            {
                "name": "phi_access_violation",
                "condition": lambda: self.metrics.get("phi_violations") > 0,
                "alert_type": AlertType.COMPLIANCE_VIOLATION,
                "severity": AlertSeverity.CRITICAL,
                "description": "Protected Health Information access violation",
                "medical_impact": True,
                "phi_involved": True
            }
        ])
        
        # Infrastructure monitoring rules
        self.rules.extend([
            {
                "name": "high_error_rate",
                "condition": lambda: self.metrics.get_rate("api_errors") > 10,
                "alert_type": AlertType.INFRASTRUCTURE_ISSUE,
                "severity": AlertSeverity.MEDIUM,
                "description": "High API error rate detected"
            },
            {
                "name": "security_service_down",
                "condition": lambda: self.metrics.get("security_service_down") > 0,
                "alert_type": AlertType.SYSTEM_COMPROMISE,
                "severity": AlertSeverity.CRITICAL,
                "description": "Security service unavailable"
            }
        ])
    
    def _setup_alert_handlers(self):
        """Setup alert notification handlers"""
        
        # Slack handler
        if HAS_SLACK:
            slack_token = get_secret("SLACK_BOT_TOKEN")
            if slack_token:
                self.alert_handlers.append(SlackAlertHandler(slack_token))
        
        # Email handler
        if HAS_EMAIL:
            smtp_config = {
                "host": get_secret("SMTP_HOST"),
                "port": int(get_secret("SMTP_PORT") or "587"),
                "username": get_secret("SMTP_USERNAME"),
                "password": get_secret("SMTP_PASSWORD"),
                "from_email": get_secret("SECURITY_EMAIL_FROM")
            }
            
            if all(smtp_config.values()):
                self.alert_handlers.append(EmailAlertHandler(smtp_config))
        
        # Console handler (always available)
        self.alert_handlers.append(ConsoleAlertHandler())
        
        # Webhook handler
        webhook_url = get_secret("SECURITY_WEBHOOK_URL")
        if webhook_url:
            self.alert_handlers.append(WebhookAlertHandler(webhook_url))
    
    def record_event(self, 
                    event_type: str, 
                    severity: str = "info",
                    details: Optional[Dict[str, Any]] = None):
        """Record security event for monitoring"""
        
        # Update metrics
        self.metrics.increment(f"security_events")
        self.metrics.increment(f"event_{event_type}")
        
        if severity in ["high", "critical"]:
            self.metrics.increment("high_severity_events")
        
        # Check for specific event types
        if event_type == "login_failure":
            self.metrics.increment("login_failures")
            
            # Check for brute force
            if details and details.get("client_ip"):
                ip = details["client_ip"]
                self.metrics.increment(f"login_failures_{ip}")
        
        elif event_type == "login_success":
            self.metrics.increment("login_attempts")
        
        elif event_type == "unauthorized_access":
            self.metrics.increment("unauthorized_attempts")
            
            if details and details.get("admin_access"):
                self.metrics.increment("unauthorized_admin_attempts")
        
        elif event_type == "medical_data_access":
            self.metrics.increment("medical_data_access")
            
            if details and details.get("phi_data"):
                self.metrics.increment("phi_access")
        
        elif event_type == "compliance_violation":
            self.metrics.increment("compliance_violations")
            
            if details and details.get("phi_violation"):
                self.metrics.increment("phi_violations")
        
        elif event_type == "api_error":
            self.metrics.increment("api_errors")
        
        # Evaluate monitoring rules
        self._evaluate_rules()
    
    def _evaluate_rules(self):
        """Evaluate monitoring rules and generate alerts"""
        
        for rule in self.rules:
            try:
                if rule["condition"]():
                    self._generate_alert(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['name']}: {e}")
    
    def _generate_alert(self, rule: Dict[str, Any]):
        """Generate security alert from rule"""
        
        alert_type = rule["alert_type"]
        severity = rule["severity"]
        
        # Check rate limiting
        alert_key = f"{alert_type.value}_{severity.value}"
        now = datetime.utcnow()
        
        # Reset window if needed
        if (now - self.alert_windows[alert_key]).total_seconds() > 3600:  # 1 hour
            self.alert_counts[alert_key] = 0
            self.alert_windows[alert_key] = now
        
        # Check if we've exceeded alert limit
        if self.alert_counts[alert_key] >= self.config["max_alerts_per_hour"]:
            return  # Skip this alert
        
        # Generate alert ID
        alert_id = hashlib.sha256(
            f"{alert_type.value}_{now.isoformat()}_{rule['name']}".encode()
        ).hexdigest()[:16]
        
        # Create alert
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=f"Security Alert: {rule['name'].replace('_', ' ').title()}",
            description=rule["description"],
            timestamp=now,
            source="vigia_security_monitor",
            affected_systems=["vigia_medical_ai"],
            indicators=self._get_current_indicators(),
            remediation_steps=self._get_remediation_steps(alert_type),
            medical_impact=rule.get("medical_impact", False),
            phi_involved=rule.get("phi_involved", False)
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        
        # Update counters
        self.alert_counts[alert_key] += 1
        self.metrics.increment("alerts_generated")
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        # Log to audit system
        self.audit.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            level=AuditLevel.ERROR if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else AuditLevel.WARNING,
            message=f"Security alert generated: {alert.title}",
            context=alert.to_dict()
        )
    
    def _get_current_indicators(self) -> Dict[str, Any]:
        """Get current security indicators"""
        return {
            "login_failure_rate": self.metrics.get_rate("login_failures"),
            "api_error_rate": self.metrics.get_rate("api_errors"),
            "medical_access_rate": self.metrics.get_rate("medical_data_access"),
            "total_events": self.metrics.get("security_events"),
            "high_severity_events": self.metrics.get("high_severity_events")
        }
    
    def _get_remediation_steps(self, alert_type: AlertType) -> List[str]:
        """Get remediation steps for alert type"""
        
        remediation_map = {
            AlertType.BRUTE_FORCE_ATTACK: [
                "Review failed login attempts and source IPs",
                "Consider implementing IP blocking or rate limiting",
                "Notify affected users to change passwords",
                "Enable MFA for targeted accounts"
            ],
            AlertType.UNAUTHORIZED_ACCESS: [
                "Review access logs for the time period",
                "Verify user permissions and roles",
                "Check for compromised accounts",
                "Update access control policies if needed"
            ],
            AlertType.MEDICAL_DATA_ACCESS: [
                "Audit medical data access patterns",
                "Verify legitimate medical use",
                "Check HIPAA compliance requirements",
                "Document access for regulatory audit"
            ],
            AlertType.COMPLIANCE_VIOLATION: [
                "Immediately investigate PHI access",
                "Document incident for compliance team",
                "Notify legal and compliance officers",
                "Implement additional data protection measures"
            ],
            AlertType.INFRASTRUCTURE_ISSUE: [
                "Check system health and resource usage",
                "Review application logs for errors",
                "Verify network connectivity",
                "Scale resources if needed"
            ],
            AlertType.SYSTEM_COMPROMISE: [
                "Immediately isolate affected systems",
                "Preserve logs and evidence", 
                "Activate incident response team",
                "Notify security team and management"
            ]
        }
        
        return remediation_map.get(alert_type, [
            "Investigate the security event",
            "Review relevant logs and metrics",
            "Take appropriate corrective action",
            "Monitor for additional indicators"
        ])
    
    def _send_alert_notifications(self, alert: SecurityAlert):
        """Send alert notifications through all handlers"""
        
        for handler in self.alert_handlers:
            try:
                handler.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {handler.__class__.__name__}: {e}")
    
    def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
            
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.INFO,
                message=f"Security alert acknowledged: {alert.title}",
                context={"alert_id": alert_id, "acknowledged_by": user}
            )
    
    def resolve_alert(self, alert_id: str, user: str, resolution_notes: str = ""):
        """Resolve an alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.resolved = True
            
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.INFO,
                message=f"Security alert resolved: {alert.title}",
                context={
                    "alert_id": alert_id, 
                    "resolved_by": user,
                    "resolution_notes": resolution_notes
                }
            )
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[SecurityAlert]:
        """Get active (unresolved) alerts"""
        alerts = [
            alert for alert in self.alerts.values()
            if not alert.resolved
        ]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        active_alerts = self.get_active_alerts()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "critical" if any(a.severity == AlertSeverity.CRITICAL for a in active_alerts) else "healthy",
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "medical_alerts": len([a for a in active_alerts if a.medical_impact]),
            "phi_alerts": len([a for a in active_alerts if a.phi_involved]),
            "metrics": {
                "login_failures_rate": self.metrics.get_rate("login_failures"),
                "api_errors_rate": self.metrics.get_rate("api_errors"),
                "medical_access_rate": self.metrics.get_rate("medical_data_access"),
                "total_events_today": self.metrics.get("security_events"),
                "alerts_generated_today": self.metrics.get("alerts_generated")
            },
            "recent_alerts": [alert.to_dict() for alert in active_alerts[:10]]
        }
    
    def start_monitoring(self):
        """Start the security monitoring service"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop the security monitoring service"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Security monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Reset daily metrics
                self.metrics.reset_daily_metrics()
                
                # Evaluate rules
                self._evaluate_rules()
                
                # Auto-resolve old alerts if enabled
                if self.config["auto_resolution_enabled"]:
                    self._auto_resolve_alerts()
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _auto_resolve_alerts(self):
        """Auto-resolve alerts that no longer trigger"""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        for alert in self.alerts.values():
            if (not alert.resolved and 
                alert.timestamp < cutoff and
                alert.alert_type not in [AlertType.DATA_BREACH, AlertType.SYSTEM_COMPROMISE]):
                
                # Check if alert condition still exists
                rule = next((r for r in self.rules if r["alert_type"] == alert.alert_type), None)
                if rule and not rule["condition"]():
                    alert.auto_resolved = True
                    alert.resolved = True


# Alert Handlers

class AlertHandler:
    """Base class for alert handlers"""
    
    def send_alert(self, alert: SecurityAlert):
        """Send alert notification"""
        raise NotImplementedError


class ConsoleAlertHandler(AlertHandler):
    """Console alert handler"""
    
    def send_alert(self, alert: SecurityAlert):
        """Print alert to console"""
        severity_icons = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️", 
            AlertSeverity.HIGH: "🚨",
            AlertSeverity.CRITICAL: "🔥",
            AlertSeverity.EMERGENCY: "🚨🔥"
        }
        
        icon = severity_icons.get(alert.severity, "⚠️")
        medical_flag = "🏥" if alert.medical_impact else ""
        phi_flag = "🔒" if alert.phi_involved else ""
        
        print(f"\n{icon} SECURITY ALERT {medical_flag}{phi_flag}")
        print(f"ID: {alert.alert_id}")
        print(f"Type: {alert.alert_type.value}")
        print(f"Severity: {alert.severity.value.upper()}")
        print(f"Title: {alert.title}")
        print(f"Description: {alert.description}")
        print(f"Time: {alert.timestamp.isoformat()}")
        
        if alert.remediation_steps:
            print("Remediation Steps:")
            for i, step in enumerate(alert.remediation_steps, 1):
                print(f"  {i}. {step}")
        
        print("-" * 60)


class SlackAlertHandler(AlertHandler):
    """Slack alert handler"""
    
    def __init__(self, token: str):
        """Initialize Slack handler"""
        if not HAS_SLACK:
            raise ImportError("slack_sdk required for Slack alerts")
        
        self.client = WebClient(token=token)
        self.channel = get_secret("SLACK_SECURITY_CHANNEL") or "#security-alerts"
    
    def send_alert(self, alert: SecurityAlert):
        """Send alert to Slack"""
        
        # Color coding by severity
        colors = {
            AlertSeverity.LOW: "#36a64f",      # Green
            AlertSeverity.MEDIUM: "#ff9500",   # Orange
            AlertSeverity.HIGH: "#ff0000",     # Red
            AlertSeverity.CRITICAL: "#8B0000", # Dark Red
            AlertSeverity.EMERGENCY: "#4B0082" # Indigo
        }
        
        color = colors.get(alert.severity, "#ff9500")
        
        # Medical/PHI flags
        flags = []
        if alert.medical_impact:
            flags.append("🏥 Medical Impact")
        if alert.phi_involved:
            flags.append("🔒 PHI Involved")
        
        # Create Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Security Alert: {alert.severity.value.upper()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Alert ID:*\n{alert.alert_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{alert.alert_type.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{alert.source}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert.description}"
                }
            }
        ]
        
        # Add flags if present
        if flags:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": " | ".join(flags)
                    }
                ]
            })
        
        # Add remediation steps
        if alert.remediation_steps:
            remediation_text = "\n".join([f"• {step}" for step in alert.remediation_steps])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Actions:*\n{remediation_text}"
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Acknowledge"
                    },
                    "value": alert.alert_id,
                    "action_id": "acknowledge_alert",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Resolve"
                    },
                    "value": alert.alert_id,
                    "action_id": "resolve_alert",
                    "style": "danger"
                }
            ]
        })
        
        try:
            self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"Security Alert: {alert.title}"  # Fallback text
            )
        except SlackApiError as e:
            logger.error(f"Failed to send Slack alert: {e}")


class EmailAlertHandler(AlertHandler):
    """Email alert handler"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize email handler"""
        self.smtp_config = smtp_config
        self.recipients = [
            email.strip() for email in 
            (get_secret("SECURITY_EMAIL_RECIPIENTS") or "").split(",")
            if email.strip()
        ]
    
    def send_alert(self, alert: SecurityAlert):
        """Send alert via email"""
        
        if not self.recipients:
            logger.warning("No email recipients configured for security alerts")
            return
        
        # Create email content
        subject = f"[SECURITY ALERT] {alert.severity.value.upper()} - {alert.title}"
        
        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2 style="color: {'red' if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else 'orange'};">
                🚨 Security Alert: {alert.severity.value.upper()}
            </h2>
            
            <table border="1" cellpadding="10" cellspacing="0">
                <tr><td><strong>Alert ID</strong></td><td>{alert.alert_id}</td></tr>
                <tr><td><strong>Type</strong></td><td>{alert.alert_type.value}</td></tr>
                <tr><td><strong>Severity</strong></td><td>{alert.severity.value.upper()}</td></tr>
                <tr><td><strong>Time</strong></td><td>{alert.timestamp.isoformat()}</td></tr>
                <tr><td><strong>Source</strong></td><td>{alert.source}</td></tr>
                <tr><td><strong>Medical Impact</strong></td><td>{'Yes 🏥' if alert.medical_impact else 'No'}</td></tr>
                <tr><td><strong>PHI Involved</strong></td><td>{'Yes 🔒' if alert.phi_involved else 'No'}</td></tr>
            </table>
            
            <h3>Description</h3>
            <p>{alert.description}</p>
            
            <h3>Affected Systems</h3>
            <ul>
                {''.join([f'<li>{system}</li>' for system in alert.affected_systems])}
            </ul>
            
            <h3>Recommended Actions</h3>
            <ol>
                {''.join([f'<li>{step}</li>' for step in alert.remediation_steps])}
            </ol>
            
            <hr>
            <p><em>This is an automated security alert from Vigia Medical AI System</em></p>
        </body>
        </html>
        """
        
        # Send email
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.recipients)
            
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")


class WebhookAlertHandler(AlertHandler):
    """Webhook alert handler"""
    
    def __init__(self, webhook_url: str):
        """Initialize webhook handler"""
        self.webhook_url = webhook_url
    
    def send_alert(self, alert: SecurityAlert):
        """Send alert via webhook"""
        
        payload = {
            "alert": alert.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "vigia_medical_ai_security"
        }
        
        try:
            import requests
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


# Global security monitor instance
_security_monitor = None

def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor instance"""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor()
    return _security_monitor

def record_security_event(event_type: str, severity: str = "info", details: Optional[Dict[str, Any]] = None):
    """Convenience function to record security events"""
    monitor = get_security_monitor()
    monitor.record_event(event_type, severity, details)

def start_security_monitoring():
    """Start security monitoring service"""
    monitor = get_security_monitor()
    monitor.start_monitoring()

def stop_security_monitoring():
    """Stop security monitoring service"""
    monitor = get_security_monitor()
    monitor.stop_monitoring()