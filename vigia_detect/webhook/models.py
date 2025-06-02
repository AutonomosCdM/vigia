"""
Data models for webhook payloads.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Types of webhook events."""
    DETECTION_COMPLETED = "detection.completed"
    DETECTION_FAILED = "detection.failed"
    PATIENT_UPDATED = "patient.updated"
    PROTOCOL_TRIGGERED = "protocol.triggered"
    ANALYSIS_READY = "analysis.ready"


class Severity(Enum):
    """Severity levels for medical findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Detection:
    """Individual detection result."""
    stage: int
    confidence: float
    bbox: List[int]
    area: float
    severity: Severity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'severity': self.severity.value
        }


@dataclass
class PatientInfo:
    """Patient information."""
    code: str
    name: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DetectionPayload:
    """Payload for detection results."""
    patient_code: str
    timestamp: datetime
    image_path: str
    detections: List[Detection]
    risk_level: str
    patient_info: Optional[PatientInfo] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'patient_code': self.patient_code,
            'timestamp': self.timestamp.isoformat(),
            'image_path': self.image_path,
            'detections': [d.to_dict() for d in self.detections],
            'risk_level': self.risk_level,
        }
        if self.patient_info:
            result['patient_info'] = self.patient_info.to_dict()
        if self.processing_time is not None:
            result['processing_time'] = self.processing_time
        if self.metadata:
            result['metadata'] = self.metadata
        return result


@dataclass
class WebhookEvent:
    """Standard webhook event structure."""
    event_type: EventType
    timestamp: datetime
    payload: Any
    source: str
    version: str = "1.0"
    webhook_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        payload_data = self.payload
        if hasattr(self.payload, 'to_dict'):
            payload_data = self.payload.to_dict()
            
        result = {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'payload': payload_data,
            'source': self.source,
            'version': self.version
        }
        if self.webhook_id:
            result['webhook_id'] = self.webhook_id
        return result


@dataclass
class WebhookResponse:
    """Response from webhook endpoint."""
    success: bool
    status_code: int
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None