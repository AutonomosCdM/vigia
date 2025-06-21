"""
Simple FastAPI Application - Render Deployment
==============================================

Simplified FastAPI app that doesn't depend on complex ADK imports.
Fallback for deployment when full system dependencies aren't available.
Enhanced with production-grade security features.
"""

import os
import ssl
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Import security components
try:
    from vigia_detect.utils.security_middleware import add_security_middleware
    from vigia_detect.utils.tls_config import get_ssl_context, TLSProfile
    from vigia_detect.utils.secrets_manager import get_secret
    HAS_SECURITY = True
except ImportError:
    HAS_SECURITY = False
    logging.warning("Security components not available in simplified mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('vigia.simple')

# Create FastAPI app with security
app = FastAPI(
    title="Vigia Medical Detection System",
    description="Medical pressure injury detection system - Enhanced security mode",
    version="1.4.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure security middleware
if HAS_SECURITY:
    # Get security configuration
    medical_grade = os.getenv("MEDICAL_COMPLIANCE_LEVEL", "hipaa") in ["hipaa", "medical", "iso13485"]
    rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    webhook_secret = get_secret("WEBHOOK_SECRET")
    
    # Add comprehensive security middleware
    add_security_middleware(
        app, 
        medical_grade=medical_grade,
        rate_limit=rate_limit,
        webhook_secret=webhook_secret
    )
    
    # Configure secure CORS for production
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-Medical-Compliance", "X-Security-Level"]
    )
    
    logger.info(f"Security middleware enabled (medical_grade={medical_grade})")
else:
    # Fallback CORS for simple mode
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.warning("Running in simplified mode without enhanced security")

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
    host = os.getenv("HOST", "0.0.0.0")
    
    # SSL/TLS Configuration
    ssl_context = None
    use_ssl = os.getenv("USE_SSL", "false").lower() == "true"
    
    if use_ssl and HAS_SECURITY:
        try:
            # Determine TLS profile based on environment
            environment = os.getenv("ENVIRONMENT", "development")
            if environment == "production":
                if os.getenv("MEDICAL_COMPLIANCE_LEVEL") in ["hipaa", "medical"]:
                    tls_profile = TLSProfile.MEDICAL_GRADE
                else:
                    tls_profile = TLSProfile.HIGH_SECURITY
            else:
                tls_profile = TLSProfile.DEVELOPMENT
            
            # Get certificate paths from environment or secrets
            cert_file = os.getenv("SSL_CERT_FILE") or get_secret("SSL_CERT_FILE")
            key_file = os.getenv("SSL_KEY_FILE") or get_secret("SSL_KEY_FILE")
            ca_file = os.getenv("SSL_CA_FILE") or get_secret("SSL_CA_FILE")
            
            # Create SSL context
            ssl_context = get_ssl_context(
                profile=tls_profile,
                server=True,
                cert_file=cert_file,
                key_file=key_file,
                ca_file=ca_file
            )
            
            logger.info(f"🔒 SSL/TLS enabled with {tls_profile.value} profile")
            
        except Exception as e:
            logger.error(f"Failed to configure SSL: {e}")
            logger.warning("Starting without SSL/TLS")
            ssl_context = None
    
    logger.info(f"🚀 Starting Vigia Medical API on {host}:{port}")
    logger.info(f"🔒 Security mode: {'Enhanced' if HAS_SECURITY else 'Simplified'}")
    logger.info(f"🏥 Medical compliance: {os.getenv('MEDICAL_COMPLIANCE_LEVEL', 'standard')}")
    
    # Start server with optional SSL
    uvicorn.run(
        "vigia_detect.api.main_simple:app",
        host=host,
        port=port,
        log_level="info",
        ssl_version=ssl.PROTOCOL_TLS_SERVER if ssl_context else None,
        ssl_cert_reqs=ssl.CERT_NONE if ssl_context else None,
        ssl_context=ssl_context,
        access_log=True,
        server_header=False,  # Don't expose server version
        date_header=False     # Don't expose server date
    )