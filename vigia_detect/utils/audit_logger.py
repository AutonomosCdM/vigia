"""
Audit Logger for Medical Communications
======================================

HIPAA-compliant audit logging for patient communications and medical data access.
Provides comprehensive tracking for regulatory compliance and security monitoring.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid


@dataclass
class AuditEvent:
    """Standardized audit event structure"""
    event_id: str
    timestamp: str
    event_type: str
    agent_id: str
    patient_token: Optional[str]
    action: str
    success: bool
    details: Dict[str, Any]
    phi_involved: bool
    compliance_level: str


class AuditLogger:
    """
    HIPAA-compliant audit logger for medical communications.
    
    Features:
    - Structured audit events
    - PHI protection tracking
    - Compliance level categorization
    - Secure log rotation
    - Export capabilities for regulatory review
    """
    
    def __init__(self, component_name: str, log_dir: Optional[str] = None):
        """
        Initialize audit logger for a specific component.
        
        Args:
            component_name: Name of the component being audited
            log_dir: Directory for audit logs (default: vigia_detect/logs/audit)
        """
        self.component_name = component_name
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent / "logs" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure audit logger
        self.logger = logging.getLogger(f"audit.{component_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log file handler
        log_file = self.log_dir / f"{component_name}_audit.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # JSON audit log for structured data
        self.json_log_file = self.log_dir / f"{component_name}_audit.jsonl"
        
        self.logger.info(f"Audit logger initialized for {component_name}")
    
    def _create_event(self, 
                     event_type: str,
                     action: str,
                     success: bool,
                     details: Dict[str, Any],
                     patient_token: Optional[str] = None,
                     phi_involved: bool = False,
                     compliance_level: str = "standard") -> AuditEvent:
        """Create standardized audit event"""
        return AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            agent_id=self.component_name,
            patient_token=patient_token,
            action=action,
            success=success,
            details=details,
            phi_involved=phi_involved,
            compliance_level=compliance_level
        )
    
    def _log_event(self, event: AuditEvent):
        """Log audit event to both text and JSON logs"""
        # Text log
        log_message = (
            f"EVENT:{event.event_type} | ACTION:{event.action} | "
            f"SUCCESS:{event.success} | PHI:{event.phi_involved} | "
            f"PATIENT:{event.patient_token or 'N/A'}"
        )
        
        if event.success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
        
        # JSON log for structured querying
        with open(self.json_log_file, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
    
    def log_patient_message(self,
                           patient_token: str,
                           message_type: str,
                           ref_number: str,
                           success: bool,
                           approved_data: Optional[Dict[str, Any]] = None):
        """
        Log patient communication event.
        
        Args:
            patient_token: Tokenized patient identifier
            message_type: Type of message sent
            ref_number: Medical reference number
            success: Whether message was sent successfully
            approved_data: Pre-approved medical data (if applicable)
        """
        details = {
            "message_type": message_type,
            "ref_number": ref_number,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if approved_data:
            # Log approved data summary (without PHI)
            details["approved_data_summary"] = {
                "data_validated": approved_data.get("medical_validation_passed"),
                "phi_tokenized": approved_data.get("phi_tokenized"),
                "system_approved": approved_data.get("approved_by_system"),
                "lpp_grade": approved_data.get("lpp_grade"),
                "confidence": approved_data.get("confidence")
            }
        
        event = self._create_event(
            event_type="patient_communication",
            action=f"send_{message_type}",
            success=success,
            details=details,
            patient_token=patient_token,
            phi_involved=True,
            compliance_level="hipaa"
        )
        
        self._log_event(event)
    
    def log_incoming_patient_message(self,
                                   patient_token: str,
                                   message_body: str):
        """
        Log incoming patient message (for compliance tracking).
        
        Args:
            patient_token: Tokenized patient identifier
            message_body: Content of patient message (anonymized)
        """
        # Anonymize message content for logging
        anonymized_body = self._anonymize_message_content(message_body)
        
        details = {
            "message_direction": "incoming",
            "message_length": len(message_body),
            "anonymized_content": anonymized_body,
            "contains_medical_keywords": self._contains_medical_keywords(message_body),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = self._create_event(
            event_type="patient_communication",
            action="receive_message",
            success=True,
            details=details,
            patient_token=patient_token,
            phi_involved=True,
            compliance_level="hipaa"
        )
        
        self._log_event(event)
    
    def log_medical_data_access(self,
                              data_type: str,
                              access_purpose: str,
                              patient_token: Optional[str] = None,
                              success: bool = True,
                              validation_status: Dict[str, Any] = None):
        """
        Log access to medical data for compliance tracking.
        
        Args:
            data_type: Type of medical data accessed
            access_purpose: Purpose of data access
            patient_token: Patient identifier (if applicable)
            success: Whether access was successful
            validation_status: Data validation results
        """
        details = {
            "data_type": data_type,
            "access_purpose": access_purpose,
            "validation_status": validation_status or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = self._create_event(
            event_type="medical_data_access",
            action=f"access_{data_type}",
            success=success,
            details=details,
            patient_token=patient_token,
            phi_involved=patient_token is not None,
            compliance_level="hipaa"
        )
        
        self._log_event(event)
    
    def log_security_event(self,
                          security_type: str,
                          description: str,
                          severity: str = "info",
                          patient_token: Optional[str] = None):
        """
        Log security-related events.
        
        Args:
            security_type: Type of security event
            description: Event description
            severity: Event severity (info, warning, error, critical)
            patient_token: Patient involved (if applicable)
        """
        details = {
            "security_type": security_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = self._create_event(
            event_type="security_event",
            action=security_type,
            success=severity not in ["error", "critical"],
            details=details,
            patient_token=patient_token,
            phi_involved=patient_token is not None,
            compliance_level="security"
        )
        
        self._log_event(event)
    
    def log_agent_action(self,
                        action_type: str,
                        action_details: Dict[str, Any],
                        success: bool = True,
                        patient_token: Optional[str] = None):
        """
        Log agent actions for accountability tracking.
        
        Args:
            action_type: Type of action performed
            action_details: Details about the action
            success: Whether action was successful
            patient_token: Patient involved (if applicable)
        """
        details = {
            "action_type": action_type,
            "action_details": action_details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = self._create_event(
            event_type="agent_action",
            action=action_type,
            success=success,
            details=details,
            patient_token=patient_token,
            phi_involved=patient_token is not None,
            compliance_level="standard"
        )
        
        self._log_event(event)
    
    def log_rate_limit_event(self,
                           patient_token: str,
                           limit_type: str,
                           current_count: int,
                           limit_threshold: int):
        """
        Log rate limiting events for compliance monitoring.
        
        Args:
            patient_token: Patient identifier
            limit_type: Type of rate limit applied
            current_count: Current usage count
            limit_threshold: Rate limit threshold
        """
        details = {
            "limit_type": limit_type,
            "current_count": current_count,
            "limit_threshold": limit_threshold,
            "exceeded": current_count >= limit_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = self._create_event(
            event_type="rate_limit",
            action=f"check_{limit_type}",
            success=current_count < limit_threshold,
            details=details,
            patient_token=patient_token,
            phi_involved=True,
            compliance_level="security"
        )
        
        self._log_event(event)
    
    def _anonymize_message_content(self, content: str, max_length: int = 50) -> str:
        """Anonymize message content for logging"""
        # Remove potential PHI and truncate
        anonymized = content.lower()
        
        # Replace potential identifying information
        replacements = {
            r'\b\d{4,}\b': '[NUMBER]',  # Long numbers
            r'\b[a-zA-Z]+@[a-zA-Z]+\.[a-zA-Z]+\b': '[EMAIL]',  # Emails
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b': '[DATE]',  # Dates
        }
        
        import re
        for pattern, replacement in replacements.items():
            anonymized = re.sub(pattern, replacement, anonymized)
        
        # Truncate for logging
        if len(anonymized) > max_length:
            anonymized = anonymized[:max_length] + "..."
        
        return anonymized
    
    def _contains_medical_keywords(self, content: str) -> bool:
        """Check if message contains medical keywords"""
        medical_keywords = [
            "dolor", "pain", "duele", "hurt", "herida", "wound",
            "medicina", "medicine", "tratamiento", "treatment",
            "doctor", "médico", "enfermera", "nurse",
            "hospital", "clínica", "clinic", "lesión", "lesion",
            "úlcera", "ulcer", "presión", "pressure"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in medical_keywords)
    
    def get_audit_summary(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate audit summary for compliance reporting.
        
        Args:
            start_date: Start date for summary period
            end_date: End date for summary period
            
        Returns:
            Dictionary with audit statistics
        """
        try:
            events = []
            
            # Read JSON log file
            if self.json_log_file.exists():
                with open(self.json_log_file, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            event_time = datetime.fromisoformat(event['timestamp'])
                            
                            # Filter by date range if provided
                            if start_date and event_time < start_date:
                                continue
                            if end_date and event_time > end_date:
                                continue
                            
                            events.append(event)
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            # Generate summary statistics
            total_events = len(events)
            event_types = {}
            success_count = 0
            phi_events = 0
            
            for event in events:
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                
                if event.get('success', False):
                    success_count += 1
                
                if event.get('phi_involved', False):
                    phi_events += 1
            
            return {
                "component": self.component_name,
                "summary_period": {
                    "start": start_date.isoformat() if start_date else "all_time",
                    "end": end_date.isoformat() if end_date else "all_time"
                },
                "total_events": total_events,
                "success_rate": (success_count / total_events * 100) if total_events > 0 else 0,
                "phi_events": phi_events,
                "event_types": event_types,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating audit summary: {e}")
            return {"error": str(e)}
    
    def export_audit_logs(self, 
                         output_file: str,
                         format_type: str = "json",
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None):
        """
        Export audit logs for regulatory compliance review.
        
        Args:
            output_file: Output file path
            format_type: Export format (json, csv)
            start_date: Start date filter
            end_date: End date filter
        """
        try:
            events = []
            
            # Read and filter events
            if self.json_log_file.exists():
                with open(self.json_log_file, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            event_time = datetime.fromisoformat(event['timestamp'])
                            
                            if start_date and event_time < start_date:
                                continue
                            if end_date and event_time > end_date:
                                continue
                            
                            events.append(event)
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            # Export based on format
            if format_type.lower() == "json":
                with open(output_file, 'w') as f:
                    json.dump(events, f, indent=2)
            
            elif format_type.lower() == "csv":
                import csv
                if events:
                    with open(output_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=events[0].keys())
                        writer.writeheader()
                        writer.writerows(events)
            
            self.logger.info(f"Exported {len(events)} audit events to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting audit logs: {e}")
            raise


# Factory function for easy instantiation
def get_audit_logger(component_name: str, log_dir: Optional[str] = None) -> AuditLogger:
    """Get audit logger instance for a component"""
    return AuditLogger(component_name, log_dir)