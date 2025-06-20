#!/usr/bin/env python3
"""
Workflow Orchestration Agent Cloud Run Entrypoint
=================================================
Native ADK Master WorkflowAgent for medical workflow coordination.
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
from vigia_detect.agents.adk.workflow_orchestration import WorkflowOrchestrationAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Workflow Orchestration Agent",
    description="ADK Native Master WorkflowAgent for Medical Coordination",
    version="1.0.0"
)

# Global agent instance
orchestration_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Workflow Orchestration Agent on startup."""
    global orchestration_agent
    try:
        logger.info("Initializing Workflow Orchestration Agent...")
        orchestration_agent = WorkflowOrchestrationAgent()
        logger.info("Workflow Orchestration Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Workflow Orchestration Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-workflow-orchestration",
        "agent_type": "WorkflowAgent",
        "orchestrator_mode": "master",
        "service": "medical_workflow_coordination"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-workflow-orchestration",
        "capabilities": ["workflow_coordination", "agent_discovery", "medical_pipeline"]
    }

@app.post("/workflow/process_medical_image")
async def process_medical_image(request: Dict[str, Any]):
    """Main entry point for medical image processing workflow."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        image_data = request.get("image_data")
        patient_context = request.get("patient_context", {})
        workflow_priority = request.get("priority", "normal")
        
        result = await orchestration_agent.process_medical_image(
            image_data=image_data,
            patient_context=patient_context,
            priority=workflow_priority
        )
        
        return {
            "workflow_id": result.get("workflow_id"),
            "lpp_detection": result.get("lpp_detection"),
            "clinical_assessment": result.get("clinical_assessment"),
            "protocol_recommendations": result.get("protocol_recommendations"),
            "notifications_sent": result.get("notifications_sent"),
            "agent_id": "vigia-workflow-orchestration",
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Medical workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/coordinate_agents")
async def coordinate_agents(request: Dict[str, Any]):
    """Coordinate multiple agents for complex medical workflows."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        workflow_type = request.get("workflow_type", "lpp_detection")
        agent_sequence = request.get("agent_sequence", [])
        workflow_data = request.get("workflow_data", {})
        
        result = await orchestration_agent.coordinate_agents(
            workflow_type=workflow_type,
            agent_sequence=agent_sequence,
            workflow_data=workflow_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Agent coordination failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/agent_discovery")
async def agent_discovery():
    """Discover available agents in the A2A network."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        agents = await orchestration_agent.discover_agents()
        return {
            "available_agents": agents,
            "discovery_endpoint": os.environ.get("A2A_REGISTRY_ENDPOINT"),
            "timestamp": "2025-01-20T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await orchestration_agent.handle_message(message)
        return response
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/metrics")
async def get_workflow_metrics():
    """Get workflow performance metrics."""
    if orchestration_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        metrics = await orchestration_agent.get_workflow_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)