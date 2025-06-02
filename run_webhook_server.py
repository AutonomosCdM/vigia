#!/usr/bin/env python3
"""Run webhook server locally for testing."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from vigia_detect.webhook.server import WebhookServer

if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 8001))
    api_key = os.getenv('WEBHOOK_API_KEY')
    
    print(f"Starting webhook server on port {port}...")
    server = WebhookServer(port=port, api_key=api_key)
    server.run(port=port)