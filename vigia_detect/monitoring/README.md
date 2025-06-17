# AgentOps Medical AI Monitoring

Complete AgentOps integration for Vigia LPP detection system with HIPAA-compliant observability.

## 🎯 Overview

This module provides comprehensive monitoring and telemetry for medical AI operations using AgentOps, specifically designed for the Vigia pressure ulcer detection system.

### Key Features

- **HIPAA-Compliant Monitoring**: Automatic PHI tokenization for medical data protection
- **Google ADK Integration**: Native support for Google Agent Development Kit
- **Medical Telemetry**: Specialized tracking for medical AI operations
- **Async Pipeline Support**: Integration with Celery-based medical workflows
- **Error Escalation**: Automatic escalation for medical-critical errors
- **Performance Metrics**: Real-time monitoring of medical AI performance

## 🏥 Medical Compliance

### HIPAA Compliance Features

- **PHI Tokenization**: Automatic identification and tokenization of Protected Health Information
- **Medical Context Preservation**: Maintains clinical relevance while protecting patient data
- **Audit Trail**: Complete logging for regulatory compliance
- **Access Control**: Role-based access to telemetry data

### Supported Medical Workflows

- LPP detection and grading
- Risk assessment and triage
- Evidence-based medical decisions
- Async medical task processing
- Medical team notifications

## 🔧 Quick Setup

### 1. Install Dependencies

```bash
pip install agentops
```

### 2. Configure API Key

```bash
export AGENTOPS_API_KEY="your-agentops-api-key"
```

### 3. Basic Usage

```python
from vigia_detect.monitoring import MedicalTelemetry

# Initialize telemetry
telemetry = MedicalTelemetry(
    app_id="vigia-lpp-production",
    environment="production",
    enable_phi_protection=True
)

# Track medical session
async with telemetry.medical_session_context(
    session_id="patient_session_001",
    patient_context={"lpp_grade": 2, "location": "sacrum"}
) as session:
    # Your medical AI operations here
    pass
```

## 📊 Core Components

### AgentOpsClient

HIPAA-compliant AgentOps client with medical data protection.

```python
from vigia_detect.monitoring import AgentOpsClient

client = AgentOpsClient(
    api_key="your-api-key",
    app_id="vigia-lpp",
    environment="production",
    enable_phi_protection=True,
    compliance_level="hipaa"
)

# Track LPP detection
client.track_lpp_detection(
    session_id="session_001",
    image_path="/path/to/image.jpg",
    detection_results={"lpp_grade": 2, "confidence": 0.89},
    confidence=0.89,
    lpp_grade=2
)
```

### PHITokenizer

Automatic tokenization of Protected Health Information.

```python
from vigia_detect.monitoring import PHITokenizer

tokenizer = PHITokenizer()

# Tokenize patient data
safe_data = tokenizer.tokenize_patient_context({
    "patient_id": "12345",  # Will be tokenized
    "name": "John Doe",     # Will be tokenized
    "lpp_grade": 2,         # Preserved for medical context
    "location": "sacrum"    # Preserved for medical context
})
```

### ADKMedicalAgent

Wrapper for Google ADK agents with medical telemetry.

```python
from vigia_detect.monitoring import MedicalTelemetry

telemetry = MedicalTelemetry()

# Create tracked medical agent
lpp_agent = telemetry.create_adk_agent(
    agent_name="lpp_detector",
    medical_specialty="lpp_detection",
    enable_tracking=True
)

# Use tracking decorator
@lpp_agent.track_interaction(
    action_name="analyze_pressure_ulcer",
    medical_critical=True,
    escalate_on_error=True
)
async def analyze_lpp(image_path, patient_context):
    # Your ADK agent code here
    return detection_results
```

### MedicalTelemetry

Central telemetry system for comprehensive medical AI monitoring.

```python
from vigia_detect.monitoring import MedicalTelemetry

telemetry = MedicalTelemetry(
    app_id="vigia-lpp-production",
    environment="production"
)

# Track medical decision
telemetry.track_medical_decision(
    session_id="session_001",
    decision_type="treatment_recommendation",
    input_data={"lpp_grade": 2, "location": "sacrum"},
    decision_result={
        "recommendation": "Stage 2 treatment protocol",
        "evidence_level": "A",
        "confidence": 0.89
    },
    evidence_level="A"
)

# Track async pipeline task
telemetry.track_async_pipeline_task(
    task_id="celery_task_123",
    task_type="medical_image_analysis",
    queue="medical_priority",
    status="success",
    session_id="session_001"
)
```

## 🔍 Medical Use Cases

### LPP Detection Workflow

```python
async def lpp_detection_workflow(image_path, patient_context):
    async with telemetry.medical_session_context(
        session_id=f"lpp_{patient_context['patient_id']}",
        patient_context=patient_context,
        session_type="lpp_analysis"
    ) as session:
        
        # Track LPP detection
        detection_results = await lpp_detector.analyze(image_path)
        
        telemetry.track_lpp_detection_event(
            session_id=session['session_id'],
            image_path=image_path,
            detection_results=detection_results,
            agent_name="yolov5_lpp_detector"
        )
        
        # Track medical decision
        if detection_results['confidence'] > 0.8:
            treatment_plan = await medical_decision_engine.recommend_treatment(
                detection_results
            )
            
            telemetry.track_medical_decision(
                session_id=session['session_id'],
                decision_type="treatment_recommendation",
                input_data=detection_results,
                decision_result=treatment_plan,
                evidence_level=treatment_plan['evidence_level']
            )
        else:
            # Low confidence - escalate for human review
            telemetry.track_medical_error_with_escalation(
                error_type="low_confidence_detection",
                error_message=f"Detection confidence {detection_results['confidence']} below threshold",
                context={"detection_results": detection_results},
                session_id=session['session_id'],
                requires_human_review=True,
                severity="medium"
            )
```

### Async Pipeline Integration

```python
from celery import Celery
from vigia_detect.monitoring import MedicalTelemetry

app = Celery('vigia_medical_tasks')
telemetry = MedicalTelemetry()

@app.task(bind=True)
def medical_image_analysis_task(self, image_path, patient_context):
    task_id = self.request.id
    
    # Track task start
    telemetry.track_async_pipeline_task(
        task_id=task_id,
        task_type="medical_image_analysis",
        queue="medical_priority",
        status="running",
        metadata={"image_path": image_path}
    )
    
    try:
        # Perform analysis
        results = perform_lpp_analysis(image_path, patient_context)
        
        # Track success
        telemetry.track_async_pipeline_task(
            task_id=task_id,
            task_type="medical_image_analysis",
            queue="medical_priority",
            status="success",
            metadata={"results": results}
        )
        
        return results
        
    except Exception as e:
        # Track failure
        telemetry.track_async_pipeline_task(
            task_id=task_id,
            task_type="medical_image_analysis",
            queue="medical_priority",
            status="failure",
            metadata={"error": str(e)}
        )
        
        # Escalate medical errors
        telemetry.track_medical_error_with_escalation(
            error_type="async_task_failure",
            error_message=str(e),
            context={"task_id": task_id, "image_path": image_path},
            requires_human_review=True,
            severity="high"
        )
        
        raise
```

## 📈 Performance Monitoring

### Agent Performance Metrics

```python
# Get ADK agent performance
lpp_agent = telemetry.create_adk_agent("lpp_detector", "lpp_detection")

# After some operations...
metrics = lpp_agent.get_performance_metrics()
print(f"Agent: {metrics['agent_name']}")
print(f"Interactions: {metrics['interaction_count']}")
print(f"Average execution time: {metrics['average_execution_time']:.3f}s")
print(f"Error rate: {metrics['error_rate']:.1%}")
```

### System Telemetry Summary

```python
# Get comprehensive telemetry summary
summary = telemetry.get_telemetry_summary()
print(f"Active sessions: {summary['active_sessions']}")
print(f"LPP detections: {summary['metrics']['lpp_detections']}")
print(f"Medical decisions: {summary['metrics']['medical_decisions']}")
print(f"Errors escalated: {summary['metrics']['errors_escalated']}")
```

## 🔒 Security and Compliance

### PHI Protection

The system automatically identifies and tokenizes PHI patterns:

- Patient identifiers (MRN, SSN, Patient IDs)
- Personal information (names, addresses, phone numbers)
- Medical record numbers
- File paths containing patient data
- Free text with potential PHI

Medical terminology is preserved for clinical context while sensitive data is tokenized.

### Compliance Features

- **HIPAA Safe Harbor**: Follows HIPAA Safe Harbor de-identification standards
- **Audit Trail**: Complete logging for regulatory compliance
- **Access Control**: Role-based access to telemetry data
- **Data Retention**: Configurable retention policies for medical data

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Basic tests (mock mode)
python test_agentops_integration.py

# Full integration tests (requires API key)
AGENTOPS_API_KEY=your-api-key python test_agentops_integration.py
```

### Test Coverage

- ✅ PHI tokenization with medical data preservation
- ✅ Medical session tracking and management
- ✅ ADK agent wrapper functionality
- ✅ Medical error escalation
- ✅ Async pipeline integration
- ✅ Telemetry summary generation

## 🔧 Configuration

### Environment Variables

```bash
# Required for full functionality
AGENTOPS_API_KEY=your-agentops-api-key

# Optional configuration
AGENTOPS_ENVIRONMENT=production  # or staging, development
MEDICAL_COMPLIANCE_LEVEL=hipaa   # or soc2, iso13485
PHI_PROTECTION_ENABLED=true
```

### Integration with Existing Vigia Components

The monitoring system integrates seamlessly with existing Vigia components:

- **Async Pipeline**: `vigia_detect/core/async_pipeline.py`
- **Medical Decision Engine**: `vigia_detect/systems/medical_decision_engine.py`
- **LPP Detection**: `vigia_detect/cv_pipeline/`
- **ADK Agents**: `vigia_detect/agents/`

## 📋 API Reference

### AgentOpsClient Methods

- `track_medical_session()` - Start medical session tracking
- `track_lpp_detection()` - Track LPP detection events
- `track_agent_interaction()` - Track ADK agent interactions
- `track_async_task()` - Track Celery async tasks
- `track_medical_error()` - Track medical errors with escalation
- `end_session()` - End tracking session

### PHITokenizer Methods

- `tokenize_string()` - Tokenize PHI in text
- `tokenize_dict()` - Tokenize PHI in dictionaries
- `tokenize_patient_context()` - Specialized patient data tokenization
- `validate_tokenization()` - Validate tokenization effectiveness

### MedicalTelemetry Methods

- `start_medical_session()` - Start comprehensive medical session
- `track_lpp_detection_event()` - Track LPP detection with metadata
- `track_medical_decision()` - Track evidence-based medical decisions
- `track_async_pipeline_task()` - Track Celery async tasks
- `track_medical_error_with_escalation()` - Track errors with escalation
- `end_medical_session()` - End medical session with summary
- `create_adk_agent()` - Create tracked ADK medical agent
- `medical_session_context()` - Async context manager for sessions

## 🎯 Best Practices

### Medical AI Monitoring

1. **Always Use Session Context**: Wrap medical operations in session contexts for proper tracking
2. **Escalate Critical Errors**: Set `medical_critical=True` for life-critical operations
3. **Preserve Medical Context**: Use PHI tokenization while preserving clinical relevance
4. **Monitor Performance**: Regular performance metrics review for medical safety
5. **Compliance First**: Ensure all telemetry meets medical compliance requirements

### Error Handling

1. **Automatic Escalation**: Configure automatic escalation for medical-critical errors
2. **Human Review Queue**: Set up human review processes for escalated errors
3. **Severity Classification**: Properly classify error severity for appropriate response
4. **Context Preservation**: Include sufficient context for medical error investigation

### Performance Optimization

1. **Async Operations**: Use async contexts for non-blocking medical operations
2. **Batch Processing**: Group related medical operations for efficiency
3. **Metric Monitoring**: Regular monitoring of response times and error rates
4. **Resource Management**: Proper cleanup of medical sessions and resources

---

**Medical AI monitoring ready for production deployment with full HIPAA compliance and AgentOps integration.**