#!/usr/bin/env python3
"""
Simple webhook server for Render deployment testing
"""
import os
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "service": "vigia-webhook",
        "status": "running",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Simple webhook receiver"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook: {data}")
        
        return jsonify({
            "status": "success",
            "message": "Webhook received",
            "data": data
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port)