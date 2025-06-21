"""
FastAPI Main Application - Render Deployment Entry Point
========================================================

Main FastAPI application for Render deployment.
Combines all Vigia services into a single deployable app.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('vigia.main')

# Import the unified server
try:
    from vigia_detect.web.unified_server import UnifiedServer
    logger.info("✅ Unified server imported successfully")
    unified_server_available = True
except ImportError as e:
    logger.error(f"❌ Failed to import unified server: {e}")
    logger.info("🔄 Falling back to simple API mode")
    unified_server_available = False

# Check if we can use the unified server
if unified_server_available:
    try:
        # Determine service availability
        redis_available = bool(os.getenv("REDIS_URL"))
        database_available = bool(os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL"))
        
        logger.info(f"🔍 Environment check:")
        logger.info(f"   Redis available: {redis_available}")
        logger.info(f"   Database available: {database_available}")
        logger.info(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
        
        # Create unified server instance
        unified_server = UnifiedServer(
            port=int(os.getenv("PORT", 8000)),
            host="0.0.0.0",
            redis_available=redis_available,
            database_available=database_available
        )
        
        # Get the FastAPI app instance
        app = unified_server.app
        
        logger.info("✅ Vigia FastAPI app initialized successfully")
        logger.info(f"🚀 Ready for deployment on port {os.getenv('PORT', 8000)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize unified server: {e}")
        unified_server_available = False

# Fallback to simple mode if unified server fails
if not unified_server_available:
    logger.info("🔄 Creating simple FastAPI app")
    
    # Import simple app
    from .main_simple import app
    
    logger.info("✅ Simple Vigia API initialized")
    logger.info("📝 Running in simplified mode for deployment compatibility")

# Export the app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting Vigia server on port {port}")
    
    uvicorn.run(
        "vigia_detect.api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )