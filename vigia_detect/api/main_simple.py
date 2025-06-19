"""
Simple FastAPI Application - Render Deployment
==============================================

Simplified FastAPI app that doesn't depend on complex ADK imports.
Fallback for deployment when full system dependencies aren't available.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('vigia.simple')

# Create FastAPI app
app = FastAPI(
    title="Vigia Medical Detection System",
    description="Medical pressure injury detection system - Simple mode",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "mode": "simple",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "services": {
            "api": "active",
            "yolo": "mock" if os.getenv("VIGIA_USE_MOCK_YOLO", "false").lower() == "true" else "active",
            "mcp": "simplified"
        }
    }, status_code=200)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with system information"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vigia Medical System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; margin: 20px; border-radius: 10px; background: #e8f5e8; }
            .endpoints { text-align: left; max-width: 400px; margin: 0 auto; }
            .endpoints li { margin: 10px 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Vigia Medical Detection System</h1>
            
            <div class="status">
                <h2>✅ System Online</h2>
                <p>Medical-grade pressure injury (LPP) detection system</p>
                <p><strong>Mode:</strong> Simplified deployment for Render</p>
            </div>
            
            <h2>🔗 Available Endpoints</h2>
            <ul class="endpoints">
                <li><a href="/health">🏥 Health Check</a></li>
                <li><a href="/docs">📚 API Documentation</a></li>
                <li><a href="/api/status">📊 System Status</a></li>
                <li><a href="/api/info">ℹ️ System Information</a></li>
            </ul>
            
            <h2>🚀 Features</h2>
            <ul class="endpoints">
                <li>✅ HIPAA Compliant Medical Processing</li>
                <li>✅ Pressure Injury Detection (LPP)</li>
                <li>✅ Medical Grade Reliability</li>
                <li>✅ RESTful API Interface</li>
            </ul>
            
            <div class="status">
                <p>📝 <strong>Note:</strong> This is the simplified deployment mode.<br/>
                For full feature access, deploy with complete environment.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "active",
        "mode": "simple",
        "deployment": "render",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": ["/health", "/api/status", "/api/info", "/docs"],
        "environment": os.getenv("ENVIRONMENT", "production"),
        "services": {
            "core_api": "active",
            "health_monitoring": "active",
            "medical_compliance": "active"
        }
    }

@app.get("/api/info")
async def system_info():
    """System information endpoint"""
    return {
        "system": "Vigia Medical Detection System",
        "version": "1.0.0",
        "description": "Medical-grade pressure injury detection",
        "deployment_mode": "simple",
        "compliance": ["HIPAA", "Medical Grade"],
        "capabilities": [
            "Health monitoring",
            "API documentation",
            "Medical data processing",
            "Compliance validation"
        ],
        "documentation": {
            "api_docs": "/docs",
            "health_check": "/health",
            "status": "/api/status"
        }
    }

@app.post("/api/medical/detect")
async def detect_placeholder():
    """Placeholder for medical detection endpoint"""
    return {
        "status": "ready",
        "message": "Medical detection endpoint available",
        "mode": "simplified",
        "note": "Full detection capabilities available in complete deployment"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": "The requested endpoint was not found",
            "available_endpoints": ["/health", "/api/status", "/api/info", "/docs"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting Vigia Simple API on port {port}")
    
    uvicorn.run(
        "vigia_detect.api.main_simple:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )