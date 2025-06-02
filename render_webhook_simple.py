#!/usr/bin/env python3
"""
Simple webhook server entry point for Render deployment.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Simple FastAPI app
app = FastAPI(title="Vigia Webhook Server", version="1.0.0")

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vigia-webhook"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": "2025-06-02"}

@app.post("/webhook")
async def receive_webhook(data: dict):
    """Receive webhook data."""
    print(f"Received webhook: {data}")
    return {"status": "received", "data": data}

# Render will run this automatically
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)