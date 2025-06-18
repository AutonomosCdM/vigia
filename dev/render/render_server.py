#!/usr/bin/env python3
"""
Unified Render Server Entry Point
Production-ready server for Render deployment with multiple service support
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia.render')

def create_app():
    """Create the appropriate app based on service type and available dependencies."""
    service_type = os.environ.get('VIGIA_SERVICE_TYPE', 'webhook').lower()
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"Starting Vigia service: {service_type} on port {port}")
    
    if service_type == 'whatsapp':
        return create_whatsapp_app()
    elif service_type == 'unified':
        return create_unified_app()
    else:  # Default to webhook
        return create_webhook_app()

def create_whatsapp_app():
    """Create WhatsApp service app."""
    try:
        from vigia_detect.messaging.whatsapp.server import app
        logger.info("WhatsApp server created successfully")
        return app
    except ImportError as e:
        logger.error(f"Failed to create WhatsApp app: {e}")
        return create_fallback_app("WhatsApp service unavailable")

def create_unified_app():
    """Create unified server app."""
    try:
        from vigia_detect.web.unified_server import UnifiedServer
        
        port = int(os.environ.get('PORT', 8000))
        redis_available = bool(os.environ.get('REDIS_URL'))
        database_available = bool(os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_URL'))
        
        server = UnifiedServer(
            port=port,
            host="0.0.0.0",
            redis_available=redis_available,
            database_available=database_available
        )
        logger.info("Unified server created successfully")
        return server.app
    except ImportError as e:
        logger.error(f"Failed to create unified app: {e}")
        return create_fallback_app("Unified service unavailable")

def create_webhook_app():
    """Create webhook service app."""
    try:
        from vigia_detect.webhook.server import WebhookServer
        
        port = int(os.environ.get('PORT', 8000))
        api_key = os.environ.get('WEBHOOK_API_KEY')
        
        server = WebhookServer(port=port, api_key=api_key)
        logger.info("Webhook server created successfully")
        return server.get_app()
    except ImportError as e:
        logger.error(f"Failed to create webhook app: {e}")
        return create_fallback_app("Webhook service unavailable")

def create_fallback_app(error_message: str):
    """Create a simple fallback app when main services fail."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(
            title="Vigia Fallback Service",
            description="Minimal service for deployment testing",
            version="1.0.0"
        )
        
        @app.get("/health")
        async def health_check():
            return JSONResponse(
                content={"status": "healthy", "service": "fallback", "error": error_message},
                status_code=200
            )
        
        @app.get("/")
        async def root():
            return JSONResponse(
                content={
                    "service": "Vigia Fallback Service",
                    "status": "running",
                    "error": error_message,
                    "endpoints": ["/health"]
                }
            )
        
        logger.info("Created FastAPI fallback app")
        return app
        
    except ImportError:
        # Final Flask fallback
        try:
            from flask import Flask, jsonify
            
            app = Flask(__name__)
            
            @app.route('/health')
            def health_check():
                return jsonify({"status": "healthy", "service": "fallback", "error": error_message})
            
            @app.route('/')
            def root():
                return jsonify({
                    "service": "Vigia Fallback Service",
                    "status": "running",
                    "error": error_message,
                    "endpoints": ["/health"]
                })
            
            logger.info("Created Flask fallback app")
            return app
            
        except ImportError:
            logger.error("No web framework available")
            raise RuntimeError("No web framework (FastAPI/Flask) available")

# Create the app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    service_type = os.environ.get('VIGIA_SERVICE_TYPE', 'webhook').lower()
    
    if service_type == 'whatsapp':
        # WhatsApp uses Flask, run with built-in server
        logger.info(f"Starting WhatsApp service on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        # Other services prefer uvicorn (FastAPI)
        try:
            import uvicorn
            logger.info(f"Starting with uvicorn on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        except ImportError:
            logger.info(f"Starting with Flask built-in server on port {port}")
            app.run(host="0.0.0.0", port=port, debug=False)