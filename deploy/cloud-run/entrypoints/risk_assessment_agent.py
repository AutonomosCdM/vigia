#!/usr/bin/env python3
"""
Risk Assessment Agent Cloud Run Entrypoint
===========================================
Native ADK LlmAgent for comprehensive medical risk assessment.
"""

import os
import logging
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ADK agent
from vigia_detect.agents.adk.risk_assessment import RiskAssessmentAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Risk Assessment Agent",
    description="ADK Native LlmAgent for Comprehensive Medical Risk Assessment",
    version="1.0.0"
)

# Global agent instance
risk_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Risk Assessment Agent on startup."""
    global risk_agent
    try:
        logger.info("Initializing Risk Assessment Agent...")
        risk_agent = RiskAssessmentAgent()
        logger.info("Risk Assessment Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Risk Assessment Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-risk-assessment",
        "agent_type": "LlmAgent",
        "assessment_scales": ["braden", "norton", "stratify", "must"],
        "service": "comprehensive_risk_assessment"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-risk-assessment",
        "capabilities": [
            "braden_scale_assessment",
            "fall_risk_evaluation",
            "infection_risk_scoring", 
            "nutritional_risk_assessment",
            "multi_scale_correlation"
        ]
    }

@app.post("/assess/braden_scale")
async def assess_braden_scale(request: Dict[str, Any]):
    """Perform Braden Scale assessment for pressure injury risk."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        patient_data = request.get("patient_data", {})
        patient_context = request.get("patient_context", {})
        
        assessment = await risk_agent.assess_braden_scale(
            patient_data=patient_data,
            patient_context=patient_context
        )
        
        return {
            "assessment_type": "braden_scale",
            "patient_id": assessment.patient_id,
            "total_score": assessment.total_score,
            "risk_level": assessment.risk_level.value,
            "escalation_required": assessment.escalation_required,
            "recommendations": assessment.recommendations,
            "evidence_summary": assessment.evidence_summary,
            "confidence_score": assessment.confidence_score,
            "agent_id": "vigia-risk-assessment",
            "timestamp": assessment.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Braden Scale assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/fall_risk")
async def assess_fall_risk(request: Dict[str, Any]):
    """Perform fall risk assessment using STRATIFY scale."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        patient_data = request.get("patient_data", {})
        patient_context = request.get("patient_context", {})
        
        assessment = await risk_agent.assess_fall_risk(
            patient_data=patient_data,
            patient_context=patient_context
        )
        
        return {
            "assessment_type": "fall_risk",
            "patient_id": assessment.patient_id,
            "stratify_score": assessment.total_score,
            "risk_level": assessment.risk_level.value,
            "escalation_required": assessment.escalation_required,
            "recommendations": assessment.recommendations,
            "evidence_summary": assessment.evidence_summary,
            "confidence_score": assessment.confidence_score,
            "agent_id": "vigia-risk-assessment",
            "timestamp": assessment.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fall risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/infection_risk") 
async def assess_infection_risk(request: Dict[str, Any]):
    """Perform infection risk assessment using evidence-based factors."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        patient_data = request.get("patient_data", {})
        patient_context = request.get("patient_context", {})
        
        assessment = await risk_agent.assess_infection_risk(
            patient_data=patient_data,
            patient_context=patient_context
        )
        
        return {
            "assessment_type": "infection_risk",
            "patient_id": assessment.patient_id,
            "infection_score": assessment.total_score,
            "risk_level": assessment.risk_level.value,
            "escalation_required": assessment.escalation_required,
            "recommendations": assessment.recommendations,
            "evidence_summary": assessment.evidence_summary,
            "confidence_score": assessment.confidence_score,
            "agent_id": "vigia-risk-assessment",
            "timestamp": assessment.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Infection risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/nutritional_risk")
async def assess_nutritional_risk(request: Dict[str, Any]):
    """Perform nutritional risk assessment using MUST scale."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        patient_data = request.get("patient_data", {})
        patient_context = request.get("patient_context", {})
        
        assessment = await risk_agent.assess_nutritional_risk(
            patient_data=patient_data,
            patient_context=patient_context
        )
        
        return {
            "assessment_type": "nutritional_risk",
            "patient_id": assessment.patient_id,
            "must_score": assessment.total_score,
            "risk_level": assessment.risk_level.value,
            "escalation_required": assessment.escalation_required,
            "recommendations": assessment.recommendations,
            "evidence_summary": assessment.evidence_summary,
            "confidence_score": assessment.confidence_score,
            "agent_id": "vigia-risk-assessment",
            "timestamp": assessment.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Nutritional risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/comprehensive")
async def comprehensive_risk_assessment(request: Dict[str, Any]):
    """Perform comprehensive multi-scale risk assessment."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        patient_data = request.get("patient_data", {})
        patient_context = request.get("patient_context", {})
        
        assessment = await risk_agent.perform_comprehensive_risk_assessment(
            patient_data=patient_data,
            patient_context=patient_context
        )
        
        return assessment
        
    except Exception as e:
        logger.error(f"Comprehensive risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if risk_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Extract patient data from A2A message
        content = message.get("content", {})
        case_id = content.get("case_id") or content.get("patient_id", "unknown")
        
        # Process as medical case
        response = await risk_agent.process_medical_case(
            case_id=case_id,
            patient_data=content,
            context=message.get("metadata", {})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)