#!/usr/bin/env python3
"""
Voice Analysis Agent - Cloud Run Entrypoint
==========================================

FastAPI entrypoint for Voice Analysis Agent on Google Cloud Run.
Provides voice analysis capabilities using Hume AI for medical applications.
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Vigia Voice Analysis Agent",
    description="ADK Voice Analysis Agent for empathic AI voice processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
voice_agent = None

async def initialize_agent():
    """Initialize Voice Analysis Agent"""
    global voice_agent
    try:
        from vigia_detect.agents.adk.voice_analysis import VoiceAnalysisAgent
        
        voice_agent = VoiceAnalysisAgent()
        logger.info("Voice Analysis Agent initialized successfully")
        return voice_agent
    except Exception as e:
        logger.error(f"Failed to initialize Voice Analysis Agent: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting Voice Analysis Agent service...")
    await initialize_agent()
    logger.info("Voice Analysis Agent service ready")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "voice_analysis_agent",
        "timestamp": datetime.now().isoformat(),
        "hume_client": voice_agent.hume_client is not None if voice_agent else False,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voice Analysis Agent",
        "version": "1.0.0",
        "description": "Empathic AI voice analysis for medical applications",
        "endpoints": {
            "health": "/health",
            "analyze_voice": "/analyze/voice",
            "analyze_batch": "/analyze/batch",
            "stream_analysis": "/analyze/stream",
            "patient_history": "/patient/{patient_id}/history",
            "voice_trends": "/patient/{patient_id}/trends"
        }
    }


@app.post("/analyze/voice")
async def analyze_voice_file(
    patient_id: str,
    audio_file: UploadFile = File(...),
    patient_context: Optional[Dict[str, Any]] = None
):
    """
    Analyze voice file for emotional and medical indicators.
    
    Args:
        patient_id: Patient identifier
        audio_file: Audio file for analysis
        patient_context: Optional patient medical context
    """
    if not voice_agent:
        raise HTTPException(status_code=503, detail="Voice Analysis Agent not initialized")
    
    if not voice_agent.hume_client:
        raise HTTPException(status_code=503, detail="Hume AI client not available")
    
    try:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # Perform voice analysis
        result = await voice_agent.process_voice_file(
            audio_file_path=temp_audio_path,
            patient_id=patient_id,
            patient_context=patient_context
        )
        
        # Cleanup temporary file
        os.unlink(temp_audio_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "analysis_result": result,
                "agent_id": "voice_analysis_agent",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Voice analysis failed: {str(e)}")
        # Cleanup temporary file on error
        try:
            os.unlink(temp_audio_path)
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Voice analysis failed: {str(e)}"
        )


@app.post("/analyze/batch")
async def analyze_batch_files(
    patient_id: str,
    audio_files: list[UploadFile] = File(...),
    patient_context: Optional[Dict[str, Any]] = None
):
    """
    Analyze multiple voice files in batch.
    
    Args:
        patient_id: Patient identifier
        audio_files: List of audio files for analysis
        patient_context: Optional patient medical context
    """
    if not voice_agent:
        raise HTTPException(status_code=503, detail="Voice Analysis Agent not initialized")
    
    results = []
    
    for audio_file in audio_files:
        try:
            # Process each file individually
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                content = await audio_file.read()
                temp_file.write(content)
                temp_audio_path = temp_file.name
            
            result = await voice_agent.process_voice_file(
                audio_file_path=temp_audio_path,
                patient_id=patient_id,
                patient_context=patient_context
            )
            
            results.append({
                "filename": audio_file.filename,
                "result": result,
                "success": True
            })
            
            # Cleanup
            os.unlink(temp_audio_path)
            
        except Exception as e:
            logger.error(f"Failed to analyze {audio_file.filename}: {str(e)}")
            results.append({
                "filename": audio_file.filename,
                "error": str(e),
                "success": False
            })
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "batch_results": results,
            "total_files": len(audio_files),
            "successful_analyses": len([r for r in results if r["success"]]),
            "agent_id": "voice_analysis_agent",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.get("/patient/{patient_id}/history")
async def get_patient_voice_history(patient_id: str):
    """Get voice analysis history for patient"""
    if not voice_agent:
        raise HTTPException(status_code=503, detail="Voice Analysis Agent not initialized")
    
    try:
        history = await voice_agent.get_patient_voice_history(patient_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "patient_id": patient_id,
                "voice_history": history,
                "total_analyses": len(history),
                "agent_id": "voice_analysis_agent",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get voice history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voice history: {str(e)}"
        )


@app.get("/patient/{patient_id}/trends")
async def analyze_voice_trends(patient_id: str):
    """Analyze voice pattern trends for patient"""
    if not voice_agent:
        raise HTTPException(status_code=503, detail="Voice Analysis Agent not initialized")
    
    try:
        trends = await voice_agent.analyze_voice_trends(patient_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "trend_analysis": trends,
                "agent_id": "voice_analysis_agent",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze voice trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze voice trends: {str(e)}"
        )


@app.post("/a2a/message")
async def handle_a2a_message(message: Dict[str, Any]):
    """Handle A2A (Agent-to-Agent) messages"""
    if not voice_agent:
        raise HTTPException(status_code=503, detail="Voice Analysis Agent not initialized")
    
    try:
        message_type = message.get("type")
        patient_id = message.get("patient_id")
        
        if message_type == "voice_analysis_request":
            # Handle voice analysis request from other agents
            audio_path = message.get("audio_path")
            patient_context = message.get("patient_context", {})
            
            if not audio_path:
                raise ValueError("audio_path required for voice analysis")
            
            result = await voice_agent.process_voice_file(
                audio_file_path=audio_path,
                patient_id=patient_id,
                patient_context=patient_context
            )
            
            return {
                "success": True,
                "message_type": "voice_analysis_response",
                "analysis_result": result,
                "agent_id": "voice_analysis_agent"
            }
            
        elif message_type == "trend_analysis_request":
            # Handle trend analysis request
            trends = await voice_agent.analyze_voice_trends(patient_id)
            
            return {
                "success": True,
                "message_type": "trend_analysis_response",
                "trend_analysis": trends,
                "agent_id": "voice_analysis_agent"
            }
            
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
            
    except Exception as e:
        logger.error(f"A2A message handling failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "agent_id": "voice_analysis_agent"
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8087))
    uvicorn.run(
        "voice_analysis_agent:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )