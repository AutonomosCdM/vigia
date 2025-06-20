#!/usr/bin/env python3
"""
Clinical Assessment Agent Cloud Run Entrypoint
==============================================
Native ADK LlmAgent with Gemini for evidence-based clinical decisions.
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
from vigia_detect.agents.adk.clinical_assessment import ClinicalAssessmentAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Clinical Assessment Agent",
    description="ADK Native LlmAgent for Evidence-Based Clinical Decisions",
    version="1.0.0"
)

# Global agent instance
clinical_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Clinical Assessment Agent on startup."""
    global clinical_agent
    try:
        logger.info("Initializing Clinical Assessment Agent...")
        clinical_agent = ClinicalAssessmentAgent()
        logger.info("Clinical Assessment Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Clinical Assessment Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-clinical-assessment",
        "agent_type": "LlmAgent",
        "llm_model": "gemini-1.5-pro",
        "service": "clinical_decision_making"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-clinical-assessment",
        "capabilities": ["npuap_assessment", "minsal_compliance", "evidence_based_decisions"]
    }

@app.post("/assess/lpp_detection")
async def assess_lpp_detection(request: Dict[str, Any]):
    """Perform clinical assessment of LPP detection results."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        lpp_grade = request.get("lpp_grade", 0)
        confidence = request.get("confidence", 0.0)
        anatomical_location = request.get("anatomical_location", "unknown")
        patient_context = request.get("patient_context", {})
        
        assessment = await clinical_agent.assess_lpp_detection(
            lpp_grade=lpp_grade,
            confidence=confidence,
            anatomical_location=anatomical_location,
            patient_context=patient_context
        )
        
        return {
            "clinical_assessment": assessment.get("assessment"),
            "evidence_level": assessment.get("evidence_level"),
            "recommendations": assessment.get("recommendations", []),
            "escalation_required": assessment.get("escalation_required", False),
            "compliance_notes": assessment.get("compliance_notes"),
            "agent_id": "vigia-clinical-assessment",
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Clinical assessment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/npuap_classification")
async def npuap_classification(request: Dict[str, Any]):
    """Perform NPUAP/EPUAP classification assessment."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        detection_data = request.get("detection_data", {})
        patient_risk_factors = request.get("patient_risk_factors", {})
        
        classification = await clinical_agent.npuap_classification(
            detection_data=detection_data,
            patient_risk_factors=patient_risk_factors
        )
        
        return classification
        
    except Exception as e:
        logger.error(f"NPUAP classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess/minsal_compliance")
async def minsal_compliance_check(request: Dict[str, Any]):
    """Check MINSAL compliance for Chilean healthcare."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        clinical_data = request.get("clinical_data", {})
        hospital_context = request.get("hospital_context", {})
        
        compliance = await clinical_agent.check_minsal_compliance(
            clinical_data=clinical_data,
            hospital_context=hospital_context
        )
        
        return compliance
        
    except Exception as e:
        logger.error(f"MINSAL compliance check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend/interventions")
async def recommend_interventions(request: Dict[str, Any]):
    """Recommend evidence-based interventions."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        lpp_assessment = request.get("lpp_assessment", {})
        patient_profile = request.get("patient_profile", {})
        
        interventions = await clinical_agent.recommend_interventions(
            lpp_assessment=lpp_assessment,
            patient_profile=patient_profile
        )
        
        return {
            "interventions": interventions,
            "evidence_based": True,
            "guidelines_reference": "NPUAP/EPUAP/PPPIA 2019",
            "agent_id": "vigia-clinical-assessment"
        }
        
    except Exception as e:
        logger.error(f"Intervention recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if clinical_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await clinical_agent.handle_message(message)
        return response
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)