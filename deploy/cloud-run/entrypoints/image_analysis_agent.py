#!/usr/bin/env python3
"""
Image Analysis Agent Cloud Run Entrypoint
=========================================
Native ADK BaseAgent with YOLOv5 for LPP detection.
"""

import os
import logging
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ADK agent
from vigia_detect.agents.adk.image_analysis import ImageAnalysisAgent

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Image Analysis Agent",
    description="ADK Native BaseAgent with YOLOv5 for LPP Detection",
    version="1.0.0"
)

# Global agent instance
image_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Image Analysis Agent on startup."""
    global image_agent
    try:
        logger.info("Initializing Image Analysis Agent...")
        image_agent = ImageAnalysisAgent()
        logger.info("Image Analysis Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Image Analysis Agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": "vigia-image-analysis",
        "agent_type": "BaseAgent",
        "service": "lpp_detection"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if image_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {
        "status": "ready",
        "agent_id": "vigia-image-analysis",
        "capabilities": ["yolo_detection", "lpp_classification", "image_preprocessing"]
    }

@app.post("/analyze/image")
async def analyze_image(request: Dict[str, Any]):
    """Analyze medical image for LPP detection."""
    if image_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        image_data = request.get("image_data")  # base64 encoded
        patient_context = request.get("patient_context", {})
        detection_threshold = request.get("threshold", 0.5)
        
        result = await image_agent.detect_lpp(
            image_data=image_data,
            patient_context=patient_context,
            threshold=detection_threshold
        )
        
        return {
            "lpp_grade": result.get("lpp_grade", 0),
            "confidence": result.get("confidence", 0.0),
            "anatomical_location": result.get("anatomical_location"),
            "bounding_boxes": result.get("bounding_boxes", []),
            "recommendations": result.get("recommendations", []),
            "agent_id": "vigia-image-analysis",
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/upload")
async def analyze_uploaded_image(file: UploadFile = File(...)):
    """Analyze uploaded image file for LPP detection."""
    if image_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Read and encode image
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        result = await image_agent.detect_lpp(
            image_data=image_b64,
            patient_context={},
            threshold=0.5
        )
        
        return {
            "filename": file.filename,
            "lpp_grade": result.get("lpp_grade", 0),
            "confidence": result.get("confidence", 0.0),
            "anatomical_location": result.get("anatomical_location"),
            "agent_id": "vigia-image-analysis"
        }
        
    except Exception as e:
        logger.error(f"Image upload analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/message")
async def handle_agent_message(message: Dict[str, Any]):
    """Handle A2A agent messages."""
    if image_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await image_agent.handle_message(message)
        return response
    except Exception as e:
        logger.error(f"A2A message handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model/info")
async def model_info():
    """Get YOLO model information."""
    if image_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        info = await image_agent.get_model_info()
        return info
    except Exception as e:
        logger.error(f"Model info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)