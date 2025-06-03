#!/usr/bin/env python3
"""
WhatsApp server entry point for Render deployment.
Updated: 2025-06-03 - Force redeploy with real processing
"""

import os
import sys
from pathlib import Path

# Set port from environment variable (Render provides this)
port = int(os.environ.get('PORT', 5000))

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import and run the WhatsApp server
from vigia_detect.messaging.whatsapp.server import app

if __name__ == '__main__':
    print(f"Starting WhatsApp server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)