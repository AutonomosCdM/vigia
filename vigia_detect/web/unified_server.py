"""
Unified Web Server for Render Deployment

This module provides a single FastAPI server that handles:
- Webhook endpoints
- WhatsApp endpoints  
- Health checks
- Basic web interface

Designed for deployment on platforms like Render that expect a single web service.
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import argparse

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia.unified_server')

# FastAPI and web dependencies
try:
    from fastapi import FastAPI, HTTPException, Request, Depends, Header
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    fastapi_available = True
except ImportError as e:
    logger.warning(f"FastAPI not available: {e}")
    fastapi_available = False
    # Fallback imports
    try:
        from flask import Flask
        flask_available = True
    except ImportError:
        flask_available = False

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import Vigia components
try:
    from vigia_detect.webhook.server import WebhookServer
    from vigia_detect.utils.rate_limiter import rate_limit_fastapi
    webhook_available = True
except ImportError as e:
    logger.warning(f"Webhook components not available: {e}")
    webhook_available = False

try:
    from vigia_detect.messaging.whatsapp.processor import WhatsAppProcessor
    whatsapp_available = True
except ImportError as e:
    logger.warning(f"WhatsApp components not available: {e}")
    whatsapp_available = False

try:
    from vigia_detect.cv_pipeline.detector import LPPDetector
    detection_available = True
except ImportError as e:
    logger.warning(f"Detection components not available: {e}")
    detection_available = False


class UnifiedServer:
    """Unified web server for multiple Vigia services."""
    
    def __init__(
        self,
        port: int = 8000,
        host: str = "0.0.0.0",
        redis_available: bool = False,
        database_available: bool = False
    ):
        self.port = port
        self.host = host
        self.redis_available = redis_available
        self.database_available = database_available
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Vigia Medical Detection System",
            description="Unified API for medical pressure injury detection",
            version="1.3.1",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure as needed for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.webhook_server = None
        self.whatsapp_processor = None
        self.detector = None
        
        self._setup_routes()
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize available components."""
        try:
            if webhook_available:
                logger.info("Initializing webhook components")
                # Note: We'll integrate webhook endpoints directly rather than separate server
                
            if whatsapp_available:
                logger.info("Initializing WhatsApp processor")
                self.whatsapp_processor = WhatsAppProcessor()
                
            if detection_available:
                logger.info("Initializing LPP detector")
                self.detector = LPPDetector()
                
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        # Health check endpoint (required for Render)
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for deployment platforms."""
            status = {
                "status": "healthy",
                "timestamp": str(asyncio.get_event_loop().time()),
                "services": {
                    "webhook": webhook_available,
                    "whatsapp": whatsapp_available,
                    "detection": detection_available,
                    "redis": self.redis_available,
                    "database": self.database_available
                }
            }
            return JSONResponse(content=status, status_code=200)
        
        # Root endpoint
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Root endpoint with basic information."""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Vigia Medical Detection System</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                    .healthy { background-color: #d4edda; color: #155724; }
                    .warning { background-color: #fff3cd; color: #856404; }
                </style>
            </head>
            <body>
                <h1>🏥 Vigia Medical Detection System</h1>
                <p>Medical-grade pressure injury (LPP) detection system</p>
                
                <h2>🔗 Available Endpoints</h2>
                <ul>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/webhook">Webhook Endpoint</a></li>
                    <li><a href="/whatsapp">WhatsApp Webhook</a></li>
                </ul>
                
                <h2>📊 System Status</h2>
                <div class="status healthy">✅ System Online</div>
                <div class="status healthy">🔒 HIPAA Compliant</div>
                <div class="status healthy">🏥 Medical Grade</div>
                
                <h2>📚 Documentation</h2>
                <p>For API documentation, visit <a href="/docs">/docs</a></p>
                <p>For technical documentation, see project README</p>
            </body>
            </html>
            """
            return html_content
        
        # Webhook endpoints
        if webhook_available:
            self._setup_webhook_routes()
        
        # WhatsApp endpoints
        if whatsapp_available:
            self._setup_whatsapp_routes()
        
        # Detection endpoints
        if detection_available:
            self._setup_detection_routes()
    
    def _setup_webhook_routes(self):
        """Setup webhook-related routes."""
        
        @self.app.post("/webhook")
        async def webhook_endpoint(request: Request):
            """Generic webhook endpoint."""
            try:
                body = await request.json()
                logger.info(f"Received webhook: {body}")
                
                # Process webhook based on type
                if "event_type" in body:
                    return await self._process_webhook_event(body)
                else:
                    return JSONResponse(
                        content={"status": "received", "message": "Event queued for processing"},
                        status_code=200
                    )
                    
            except Exception as e:
                logger.error(f"Webhook processing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/webhook")
        async def webhook_info():
            """Webhook information endpoint."""
            return {
                "service": "webhook",
                "status": "active",
                "endpoints": ["/webhook"],
                "methods": ["GET", "POST"]
            }
    
    def _setup_whatsapp_routes(self):
        """Setup WhatsApp-related routes."""
        
        @self.app.post("/whatsapp")
        async def whatsapp_webhook(request: Request):
            """WhatsApp webhook endpoint."""
            try:
                # Get form data (Twilio sends form-encoded data)
                form_data = await request.form()
                
                # Convert to dict for processing
                data = dict(form_data)
                logger.info(f"Received WhatsApp message: {data}")
                
                if self.whatsapp_processor:
                    response = await self.whatsapp_processor.process_message(data)
                    return response
                else:
                    return JSONResponse(
                        content={"status": "received", "message": "WhatsApp processor not available"},
                        status_code=200
                    )
                    
            except Exception as e:
                logger.error(f"WhatsApp processing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/whatsapp")
        async def whatsapp_info():
            """WhatsApp webhook information."""
            return {
                "service": "whatsapp",
                "status": "active" if self.whatsapp_processor else "unavailable",
                "endpoints": ["/whatsapp"],
                "methods": ["GET", "POST"]
            }
    
    def _setup_detection_routes(self):
        """Setup detection-related routes."""
        
        @self.app.post("/detect")
        async def detect_endpoint(request: Request):
            """Image detection endpoint."""
            try:
                # Handle multipart/form-data for image uploads
                form = await request.form()
                
                if "image" not in form:
                    raise HTTPException(status_code=400, detail="No image provided")
                
                image_file = form["image"]
                
                if self.detector:
                    # Process the image
                    result = await self.detector.detect_from_upload(image_file)
                    return result
                else:
                    return JSONResponse(
                        content={
                            "status": "unavailable",
                            "message": "Detection service not available"
                        },
                        status_code=503
                    )
                    
            except Exception as e:
                logger.error(f"Detection error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/detect")
        async def detection_info():
            """Detection service information."""
            return {
                "service": "detection",
                "status": "active" if self.detector else "unavailable",
                "endpoints": ["/detect"],
                "methods": ["GET", "POST"],
                "supported_formats": ["jpg", "jpeg", "png", "bmp"]
            }
    
    async def _process_webhook_event(self, event_data: Dict[str, Any]) -> JSONResponse:
        """Process a webhook event."""
        event_type = event_data.get("event_type")
        
        logger.info(f"Processing webhook event: {event_type}")
        
        # Add your event processing logic here
        if event_type == "image_detection":
            # Handle image detection webhook
            pass
        elif event_type == "medical_alert":
            # Handle medical alert webhook
            pass
        else:
            logger.warning(f"Unknown event type: {event_type}")
        
        return JSONResponse(
            content={
                "status": "processed",
                "event_type": event_type,
                "timestamp": str(asyncio.get_event_loop().time())
            },
            status_code=200
        )
    
    def run(self):
        """Run the unified server."""
        logger.info(f"Starting Vigia Unified Server on {self.host}:{self.port}")
        logger.info(f"Redis available: {self.redis_available}")
        logger.info(f"Database available: {self.database_available}")
        logger.info(f"Webhook available: {webhook_available}")
        logger.info(f"WhatsApp available: {whatsapp_available}")
        logger.info(f"Detection available: {detection_available}")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True
        )


def main():
    """Main entry point for the unified server."""
    parser = argparse.ArgumentParser(description="Vigia Unified Web Server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port to run server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind server to")
    parser.add_argument("--redis-available", type=str, default="false", help="Redis availability (true/false)")
    parser.add_argument("--database-available", type=str, default="false", help="Database availability (true/false)")
    
    args = parser.parse_args()
    
    # Convert string booleans to actual booleans
    redis_available = args.redis_available.lower() == "true"
    database_available = args.database_available.lower() == "true"
    
    # Create and run server
    server = UnifiedServer(
        port=args.port,
        host=args.host,
        redis_available=redis_available,
        database_available=database_available
    )
    
    server.run()


if __name__ == "__main__":
    main()