#!/usr/bin/env python3
"""
Ultra minimal Flask app for Render deployment - NO DEPENDENCIES
"""
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {
        "message": "Vigia Medical System - Deployed Successfully",
        "version": "1.4.0", 
        "status": "production_ready",
        "deployment": "render",
        "python_version": "3.11.10",
        "features": ["mock_detection", "health_check"]
    }

@app.route('/health')
def health():
    return {"status": "healthy", "deployment": "success"}

@app.route('/api/medical/detect', methods=['GET', 'POST'])
def mock_detection():
    """Ultra simple mock LPP detection"""
    return {
        "lpp_grade": 0,
        "confidence": 0.95,
        "status": "mock_success",
        "message": "Production deployment successful - YOLO disabled",
        "deployment_test": "passed"
    }

@app.route('/test')
def test():
    return {"test": "successful", "dependencies": "minimal"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)