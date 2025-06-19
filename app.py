#!/usr/bin/env python3
"""
Minimal Flask app for Render deployment
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Vigia Medical API - Production Ready",
        "version": "1.4.0",
        "status": "healthy",
        "deployment": "render"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/medical/detect', methods=['POST'])
def mock_detection():
    """Mock LPP detection endpoint"""
    return jsonify({
        "lpp_grade": 0,
        "confidence": 0.95,
        "status": "mock_detection",
        "message": "YOLO model disabled in production"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)