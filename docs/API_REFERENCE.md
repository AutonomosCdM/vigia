# Vigia API Reference

Complete API reference for the medical-grade LPP detection system with ADK architecture.

## Table of Contents

- [CLI Module API](#cli-module-api)
- [CV Pipeline API](#cv-pipeline-api)
- [Messaging API](#messaging-api)
- [ADK Agents API](#adk-agents-api)
- [Medical Decision Engine API](#medical-decision-engine-api)
- [Database API](#database-api)
- [Data Structures](#data-structures)

## CLI Module API

**Location**: `vigia_detect/cli/process_images_refactored.py`

### Functions

#### `parse_args()`
```python
def parse_args() -> argparse.Namespace
```
Parses command line arguments for medical image processing.

**Returns:**  
Parsed arguments namespace with:
- `input`: Input directory path for medical images
- `output`: Output directory path for results
- `patient_code`: Optional patient identifier for medical records
- `confidence`: Detection confidence threshold (0.0-1.0)
- `save_db`: Boolean flag for Supabase medical database storage
- `model`: YOLOv5 model variant for LPP detection
- `webhook`: Enable webhook integration for real-time processing

#### `process_directory()`
```python
def process_directory(
    input_dir: str,
    output_dir: str,
    detector: LPPDetector,
    preprocessor: ImagePreprocessor,
    patient_code: Optional[str] = None,
    save_to_db: bool = False,
    db_client: Optional[SupabaseClient] = None,
    webhook_enabled: bool = False
) -> Dict[str, Union[int, List[Dict]]]
```
Processes all medical images in input directory with LPP detection.

**Parameters:**
- `input_dir`: Path to input medical images
- `output_dir`: Path to save detection results and processed images
- `detector`: Initialized LPPDetector instance for medical analysis
- `preprocessor`: Initialized ImagePreprocessor for medical image preparation
- `patient_code`: Optional patient identifier for medical records
- `save_to_db`: Save medical results to Supabase database
- `db_client`: SupabaseClient instance for medical data storage
- `webhook_enabled`: Enable real-time webhook notifications

**Returns:**  
Medical processing statistics dictionary:
```python
{
    "processed": int,           # Total medical images processed
    "detected": int,            # Images with LPP detections
    "detections": List[Dict],   # Detailed medical detection results
    "medical_escalations": int, # Cases requiring medical review
    "confidence_scores": List[float] # Detection confidence scores
}
```

#### `main()`
```python
def main() -> None
```
Entry point for CLI medical image processing with ADK integration.

## CV Pipeline API

**Location**: `vigia_detect/cv_pipeline/`

### Classes

#### `LPPDetector`
Medical-grade wrapper for YOLOv5 pressure injury detection model.

```python
class LPPDetector:
    def __init__(
        self, 
        model_type: str = 'yolov5s', 
        conf_threshold: float = 0.25, 
        model_path: Optional[str] = None,
        medical_mode: bool = True
    ):
        """
        Initializes medical-grade LPP detector.

        Args:
            model_type: YOLOv5 model variant ('yolov5s', 'yolov5m', 'yolov5l')
            conf_threshold: Medical confidence threshold (0.0-1.0)
            model_path: Path to custom medical model weights
            medical_mode: Enable medical-specific processing and validation
        """
```

**Methods:**

##### `detect()`
```python
def detect(self, image: Union[np.ndarray, str, Path]) -> Dict[str, Any]:
    """
    Detects pressure injuries in medical image.

    Args:
        image: Medical image as NumPy array (BGR) or file path

    Returns:
        Medical detection results:
        {
            'detections': [
                {
                    'bbox': [x1, y1, x2, y2],      # Bounding box coordinates
                    'confidence': float,            # Detection confidence (0-1)
                    'stage': int,                   # LPP stage (0-4)
                    'class_name': str,              # Medical class (e.g., 'LPP-Stage2')
                    'anatomical_location': str,     # Body location if detected
                    'medical_urgency': str          # low/moderate/high/emergency
                }
            ],
            'processing_time_ms': float,            # Inference time
            'medical_metadata': {
                'requires_review': bool,            # Needs medical professional review
                'confidence_level': str,            # low/medium/high
                'escalation_reason': Optional[str]  # Why escalation is needed
            }
        }
    """
```

##### `get_model_info()`
```python
def get_model_info(self) -> Dict[str, Any]:
    """
    Returns medical model information.

    Returns:
        {
            "type": str,                    # Model type
            "device": str,                  # Processing device
            "conf_threshold": float,        # Medical confidence threshold
            "classes": List[str],           # LPP stage classes
            "medical_validation": bool,     # Medical mode enabled
            "model_version": str           # Medical model version
        }
    """
```

#### `ImagePreprocessor`
Medical image preprocessing for LPP detection with privacy protection.

```python
class ImagePreprocessor:
    def __init__(
        self, 
        target_size: Tuple[int, int] = (640, 640), 
        normalize: bool = True, 
        face_detection: bool = True,
        enhance_contrast: bool = True, 
        remove_exif: bool = True,
        medical_privacy: bool = True
    ):
        """
        Initializes medical image preprocessor.

        Args:
            target_size: Target dimensions for medical analysis
            normalize: Normalize pixel values for medical AI
            face_detection: Enable face detection and blurring for privacy
            enhance_contrast: Enhance contrast for erythema detection
            remove_exif: Remove EXIF metadata for privacy compliance
            medical_privacy: Enable additional medical privacy protections
        """
```

**Methods:**

##### `preprocess()`
```python
def preprocess(self, image_path: Union[str, Path, np.ndarray]) -> np.ndarray:
    """
    Preprocesses medical image with privacy protection.

    Args:
        image_path: Medical image file path or NumPy array

    Returns:
        Preprocessed medical image as NumPy array (BGR format)
        with privacy protections applied
    """
```

## Messaging API

**Location**: `vigia_detect/messaging/`

### Classes

#### `TwilioClient`
Medical WhatsApp communication client with HIPAA considerations.

```python
class TwilioClient:
    def __init__(self, medical_mode: bool = True):
        """
        Initializes medical-grade Twilio client.
        
        Requires environment variables:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN  
        - TWILIO_WHATSAPP_FROM
        
        Args:
            medical_mode: Enable medical data protection features
        """
```

**Methods:**

##### `send_whatsapp()`
```python
def send_whatsapp(self, to_number: str, message: str, patient_context: Optional[Dict] = None) -> str:
    """
    Sends medical WhatsApp message with audit logging.

    Args:
        to_number: Destination number in E.164 format
        message: Medical message content (PHI-protected)
        patient_context: Optional patient context for audit

    Returns:
        str: Twilio message SID for audit trail

    Raises:
        MedicalMessagingError: If medical message delivery fails
    """
```

##### `send_whatsapp_template()`
```python
def send_whatsapp_template(
    self, 
    to_number: str, 
    template_sid: str, 
    params: Dict[str, Any],
    medical_urgency: str = "routine"
) -> str:
    """
    Sends medical WhatsApp template with urgency classification.

    Args:
        to_number: Destination number in E.164 format
        template_sid: Approved medical template SID
        params: Template parameters (PHI-protected)
        medical_urgency: Medical urgency (routine/urgent/emergency)

    Returns:
        str: Twilio message SID for medical audit trail
    """
```

##### `handle_incoming_webhook()`
```python
def handle_incoming_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes incoming medical webhook with PHI protection.

    Args:
        data: Raw webhook data from Twilio

    Returns:
        Processed medical webhook data:
        {
            'sender': str,              # Patient phone number (masked)
            'body': str,                # Message content
            'num_media': int,           # Number of medical images
            'media_urls': List[str],    # Secure medical image URLs
            'media_types': List[str],   # Image content types
            'medical_session_id': str,  # Session for PHI tracking
            'timestamp': datetime       # For medical audit
        }
    """
```

### Medical Message Templates

#### WhatsApp Medical Response Templates by LPP Stage

| LPP Stage | Template Type | Medical Urgency | Response Content |
|-----------|---------------|-----------------|------------------|
| **No LPP** | `NO_LPP_DETECTED` | routine | Informational with prevention guidance |
| **Stage 1** | `LPP_STAGE_1_LOW` | routine | Low risk with monitoring recommendations |
| **Stage 2** | `LPP_STAGE_2_MODERATE` | urgent | Moderate risk requiring medical consultation |
| **Stage 3** | `LPP_STAGE_3_HIGH` | emergency | High risk requiring immediate medical attention |
| **Stage 4** | `LPP_STAGE_4_CRITICAL` | emergency | Critical requiring emergency medical care |
| **Unclear** | `IMAGE_UNCLEAR` | routine | Request for clearer medical image |

## ADK Agents API

**Location**: `vigia_detect/agents/`

All medical agents inherit from `BaseAgent` and use standardized message patterns.

### Base Agent Pattern

```python
from vigia_detect.agents.base_agent import BaseAgent, AgentMessage, AgentResponse

class MedicalAgent(BaseAgent):
    def process_message(self, message: AgentMessage) -> AgentResponse:
        """
        Process medical message with evidence-based logic.
        
        Args:
            message: Standardized agent message with medical context
            
        Returns:
            AgentResponse with medical decision and evidence
        """
```

### Core Medical Agents

#### `ImageAnalysisAgent`
```python
class ImageAnalysisAgent(BaseAgent):
    """YOLOv5 integration for medical LPP detection with clinical validation."""
    
    def analyze_medical_image(
        self, 
        image_path: str, 
        patient_context: Optional[Dict] = None
    ) -> AgentResponse:
        """
        Analyzes medical image for pressure injuries.
        
        Returns medical analysis with:
        - LPP stage classification (0-4)
        - Anatomical location detection
        - Confidence assessment
        - Medical escalation recommendations
        """
```

#### `ClinicalAssessmentAgent`
```python
class ClinicalAssessmentAgent(BaseAgent):
    """Evidence-based NPUAP/EPUAP medical decision making."""
    
    def assess_clinical_urgency(
        self, 
        lpp_grade: int, 
        confidence: float,
        patient_risk_factors: Dict[str, bool]
    ) -> AgentResponse:
        """
        Makes evidence-based clinical assessment.
        
        Returns assessment with:
        - Medical urgency classification
        - NPUAP/EPUAP evidence references
        - Treatment recommendations
        - Escalation protocols
        """
```

#### `ProtocolAgent`
```python
class ProtocolAgent(BaseAgent):
    """Medical protocol consultation with vector search."""
    
    def search_medical_protocols(
        self, 
        clinical_query: str,
        lpp_stage: Optional[int] = None
    ) -> AgentResponse:
        """
        Searches medical protocols using Redis vector storage.
        
        Returns protocol recommendations with:
        - Evidence-based treatment protocols
        - Clinical practice guidelines
        - Medical references and citations
        """
```

## Medical Decision Engine API

**Location**: `vigia_detect/systems/`

### International Medical Decisions

```python
from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine

engine = MedicalDecisionEngine()

def make_clinical_decision(
    lpp_grade: int,
    confidence: float,
    anatomical_location: str,
    patient_context: Optional[Dict] = None
) -> MedicalDecision:
    """
    Makes evidence-based clinical decision using NPUAP/EPUAP guidelines.
    
    Args:
        lpp_grade: Detected LPP stage (0-4)
        confidence: AI detection confidence (0.0-1.0)
        anatomical_location: Body location (sacrum, heel, etc.)
        patient_context: Patient risk factors and medical history
        
    Returns:
        MedicalDecision with:
        - urgency_level: str (low/moderate/high/emergency)
        - evidence_level: str (A/B/C)
        - clinical_recommendations: List[str]
        - escalation_required: bool
        - scientific_references: List[str]
        - medical_justification: str
    """
```

### Chilean Regulatory Compliance (MINSAL)

```python
from vigia_detect.systems.minsal_medical_decision_engine import make_minsal_clinical_decision

def make_minsal_clinical_decision(
    lpp_grade: int,
    confidence: float,
    patient_context: Dict[str, Union[str, bool]]
) -> MinsalMedicalDecision:
    """
    Makes clinical decision compliant with Chilean Ministry of Health regulations.
    
    Args:
        lpp_grade: Detected LPP stage
        confidence: Detection confidence
        patient_context: Chilean healthcare context (public/private, diabetes, etc.)
        
    Returns:
        MinsalMedicalDecision with regulatory compliance metadata
    """
```

## Database API

**Location**: `vigia_detect/db/`

### Supabase Medical Database Integration

```python
from supabase import create_client, Client
import os

# Medical database connection
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)
```

### Medical Data Operations

#### Patient Management
```python
# Insert medical patient record
patient_data = {
    "patient_code": "CD-2025-001",
    "age_range": "61-80", 
    "risk_factors": {"diabetes": True, "mobility_impaired": True},
    "medical_facility": "Hospital Central"
}

response = supabase.table("clinical_data.patients").insert(patient_data).execute()
```

#### Medical Image Storage
```python
# Store medical image with LPP detection results
image_data = {
    "patient_id": patient_uuid,
    "file_path": "/secure/medical/images/patient_001_lpp.jpg",
    "lpp_detections": detection_results,
    "medical_metadata": {
        "detected_stage": 2,
        "confidence": 0.85,
        "requires_review": True
    }
}

response = supabase.table("ml_operations.lpp_images").insert(image_data).execute()
```

#### Medical Audit Logging
```python
# Log medical system access for compliance
audit_entry = {
    "user_id": medical_staff_id,
    "action": "lpp_detection_analysis",
    "patient_code": "CD-2025-001", 
    "medical_details": {
        "detected_lpp_stage": 2,
        "confidence_score": 0.85,
        "escalated_to_physician": True
    },
    "compliance_flags": ["HIPAA", "MINSAL"]
}

response = supabase.table("audit_logs.medical_access").insert(audit_entry).execute()
```

## Data Structures

### Medical Detection Result
```python
MedicalDetectionResult = {
    'detections': [
        {
            'bbox': List[float],                # [x1, y1, x2, y2] coordinates
            'confidence': float,                # Detection confidence (0.0-1.0)
            'stage': int,                       # LPP stage (0-4)
            'class_name': str,                  # Medical class name
            'anatomical_location': Optional[str], # Body location
            'medical_urgency': str,             # Medical urgency level
            'evidence_level': str,              # Medical evidence quality (A/B/C)
            'requires_escalation': bool         # Needs medical professional review
        }
    ],
    'processing_time_ms': float,                # Analysis processing time
    'medical_metadata': {
        'patient_context_considered': bool,     # Patient history factored in
        'confidence_level': str,                # Overall confidence assessment
        'escalation_reason': Optional[str],     # Why escalation recommended
        'medical_references': List[str]         # Clinical guideline references
    },
    'audit_trail': {
        'session_id': str,                      # Medical session identifier
        'timestamp': datetime,                  # Analysis timestamp
        'compliance_flags': List[str]           # Regulatory compliance markers
    }
}
```

### Medical Decision Structure
```python
MedicalDecision = {
    'urgency_level': str,                       # low/moderate/high/emergency
    'evidence_level': str,                      # A/B/C (medical evidence quality)
    'clinical_recommendations': List[str],       # Treatment recommendations
    'escalation_required': bool,                # Needs physician review
    'escalation_timeline': str,                 # immediate/within_hours/within_days
    'scientific_references': List[str],         # NPUAP/EPUAP/PPPIA citations
    'medical_justification': str,               # Clinical reasoning
    'patient_education': Optional[str],         # Patient guidance content
    'follow_up_required': bool,                 # Needs follow-up assessment
    'compliance_notes': List[str]               # Regulatory compliance notes
}
```

### Medical Audit Entry
```python
MedicalAuditEntry = {
    'session_id': str,                          # Unique medical session
    'timestamp': datetime,                      # Action timestamp
    'user_id': str,                            # Medical staff identifier
    'patient_code': str,                       # De-identified patient code
    'action_type': str,                        # Type of medical action
    'medical_details': Dict[str, Any],         # Medical action specifics
    'phi_accessed': bool,                      # PHI data accessed flag
    'compliance_frameworks': List[str],         # HIPAA, MINSAL, etc.
    'access_justification': str,               # Medical reason for access
    'outcome': str,                            # Action outcome/result
    'escalation_performed': bool               # Whether case was escalated
}
```

## Error Handling

### Medical Exception Classes
```python
class MedicalProcessingError(Exception):
    """Base exception for medical processing errors."""
    pass

class LPPDetectionError(MedicalProcessingError):
    """LPP detection analysis failed."""
    pass

class MedicalMessagingError(Exception):
    """Medical messaging/communication error."""
    pass

class ComplianceViolationError(Exception):
    """Medical compliance or privacy violation."""
    pass
```

### Medical Error Response Format
```python
MedicalErrorResponse = {
    'error_type': str,                          # Error classification
    'error_message': str,                       # Human-readable error
    'medical_context': Dict[str, Any],          # Medical context when error occurred
    'patient_impact': str,                      # Impact on patient care
    'escalation_required': bool,                # Needs medical staff attention
    'compliance_review_needed': bool,           # Requires compliance review
    'audit_logged': bool,                       # Error logged for audit
    'timestamp': datetime,                      # Error occurrence time
    'session_id': str                          # Medical session identifier
}
```

For detailed implementation examples and usage patterns, see the [Developer Guide](DEVELOPER_GUIDE.md).