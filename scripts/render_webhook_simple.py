#!/usr/bin/env python3
"""
Render Webhook Simple Entry Point
Lightweight webhook service for Render deployment with graceful fallbacks
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia.render_webhook')

def create_simple_app():
    """Create a simple webhook app with fallbacks for missing dependencies."""
    try:
        # Try to import and use the unified server
        from vigia_detect.web.unified_server import UnifiedServer
        
        port = int(os.environ.get('PORT', 8000))
        redis_available = bool(os.environ.get('REDIS_URL'))
        database_available = bool(os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_URL'))
        
        logger.info(f"Creating UnifiedServer on port {port}")
        server = UnifiedServer(
            port=port,
            host="0.0.0.0",
            redis_available=redis_available,
            database_available=database_available
        )
        return server.app
        
    except ImportError as e:
        logger.warning(f"UnifiedServer not available: {e}")
        
        # Fallback to simple FastAPI app
        try:
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse
            
            app = FastAPI(
                title="Vigia Webhook Simple",
                description="Lightweight webhook service for Render deployment",
                version="1.0.0"
            )
            
            @app.get("/health")
            async def health_check():
                return JSONResponse(
                    content={"status": "healthy", "service": "webhook-simple"},
                    status_code=200
                )
            
            @app.get("/")
            async def root():
                return JSONResponse(
                    content={
                        "service": "Vigia Webhook Simple",
                        "status": "running",
                        "endpoints": ["/health", "/webhook"]
                    }
                )
            
            @app.post("/webhook")
            async def webhook_endpoint():
                return JSONResponse(
                    content={"status": "received", "message": "Webhook processing"},
                    status_code=200
                )
            
            logger.info("Created simple FastAPI fallback app")
            return app
            
        except ImportError:
            logger.error("FastAPI not available, creating minimal Flask app")
            
            # Final fallback to Flask
            try:
                from flask import Flask, jsonify
                
                app = Flask(__name__)
                
                @app.route('/health')
                def health_check():
                    return jsonify({"status": "healthy", "service": "webhook-simple"})
                
                @app.route('/')
                def root():
                    return jsonify({
                        "service": "Vigia Webhook Simple",
                        "status": "running",
                        "endpoints": ["/health", "/webhook"]
                    })
                
                @app.route('/webhook', methods=['POST'])
                def webhook_endpoint():
                    return jsonify({"status": "received", "message": "Webhook processing"})
                
                logger.info("Created Flask fallback app")
                return app
                
            except ImportError:
                logger.error("No web framework available")
                raise RuntimeError("No web framework (FastAPI/Flask) available")

# Create the app instance
app = create_simple_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    
    # Try to run with uvicorn first (FastAPI), then fallback to built-in server
    try:
        import uvicorn
        logger.info(f"Starting with uvicorn on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except ImportError:
        # If uvicorn not available, assume Flask app
        logger.info(f"Starting with Flask built-in server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)