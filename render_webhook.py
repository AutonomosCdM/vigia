#!/usr/bin/env python3
"""
Webhook server entry point for Render deployment.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from vigia_detect.webhook.server import WebhookServer

# Get configuration from environment
port = int(os.environ.get('PORT', 8000))
api_key = os.environ.get('WEBHOOK_API_KEY')

# Create and get FastAPI app
server = WebhookServer(port=port, api_key=api_key)
app = server.get_app()

# Render will run this with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)