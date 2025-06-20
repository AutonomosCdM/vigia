#!/usr/bin/env python3
"""
Communication Agent Cloud Run Entrypoint
========================================
Native ADK WorkflowAgent for multi-platform medical messaging.
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
from vigia_detect.agents.adk.communication import CommunicationAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Communication Agent",
    description="ADK Native WorkflowAgent for Medical Messaging",
    version="1.0.0"
)

# Global agent instance
communication_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Communication Agent on startup."""
    global communication_agent
    try:
        logger.info("Initializing Communication Agent...")
        communication_agent = CommunicationAgent()
        logger.info("Communication Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Communication Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-communication-agent",
        "agent_type": "WorkflowAgent",
        "service": "medical_messaging"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if communication_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-communication-agent",
        "capabilities": ["whatsapp", "slack", "email", "sms"]
    }

@app.post("/notify/lpp_detection")
async def notify_lpp_detection(request: Dict[str, Any]):
    """Send LPP detection notifications across platforms."""
    if communication_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        lpp_grade = request.get("lpp_grade", 0)
        confidence = request.get("confidence", 0.0)
        patient_context = request.get("patient_context", {})
        platform = request.get("platform", "slack")
        
        result = await communication_agent.notify_lpp_detection(
            lpp_grade=lpp_grade,
            confidence=confidence,
            patient_context=patient_context,
            platform=platform
        )
        
        return {
            "notification_sent": True,
            "platform": platform,
            "message_id": result.get("message_id"),
            "agent_id": "vigia-communication-agent",
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"LPP notification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/whatsapp")
async def send_whatsapp_message(request: Dict[str, Any]):
    """Send WhatsApp message via Twilio."""
    if communication_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await communication_agent.send_whatsapp_message(
            to=request.get("to"),
            message=request.get("message"),
            patient_context=request.get("patient_context", {})
        )
        return result
    except Exception as e:
        logger.error(f"WhatsApp message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/slack")
async def send_slack_message(request: Dict[str, Any]):
    """Send Slack message with Block Kit."""
    if communication_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await communication_agent.send_slack_message(
            channel=request.get("channel"),
            message=request.get("message"),
            blocks=request.get("blocks"),
            patient_context=request.get("patient_context", {})
        )
        return result
    except Exception as e:
        logger.error(f"Slack message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if communication_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await communication_agent.handle_message(message)
        return response
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)