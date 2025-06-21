#!/usr/bin/env python3
"""
Protocol Agent Cloud Run Entrypoint
===================================
Native ADK LlmAgent for medical protocol search and guidance.
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
from vigia_detect.agents.adk.protocol import ProtocolAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Protocol Agent",
    description="ADK Native LlmAgent for Medical Protocol Search",
    version="1.0.0"
)

# Global agent instance
protocol_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Protocol Agent on startup."""
    global protocol_agent
    try:
        logger.info("Initializing Protocol Agent...")
        protocol_agent = ProtocolAgent()
        logger.info("Protocol Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Protocol Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-protocol-agent",
        "agent_type": "LlmAgent",
        "service": "protocol_search"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if protocol_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-protocol-agent",
        "capabilities": ["protocol_search", "guideline_consultation"]
    }

@app.post("/protocol/search")
async def search_protocols(request: Dict[str, Any]):
    """Search medical protocols using semantic search."""
    if protocol_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        query = request.get("query", "")
        lpp_grade = request.get("lpp_grade")
        location = request.get("location")
        
        result = await protocol_agent.search_protocols(
            query=query,
            lpp_grade=lpp_grade,
            anatomical_location=location
        )
        
        return {
            "protocols": result,
            "agent_id": "vigia-protocol-agent",
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Protocol search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if protocol_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await protocol_agent.handle_message(message)
        return response
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)