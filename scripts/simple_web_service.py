#!/usr/bin/env python3
"""
Simple web service for Render port scanning
This service focuses solely on binding to a port to satisfy Render's requirements.
"""

import os
import time
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Okama Finance Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🤖 Okama Finance Bot</h1>
        <p class="status">✅ Web service is running</p>
        <p>This web service exists to satisfy Render's port scanning requirements.</p>
        <p><a href="/health">Health Check</a></p>
        <p><a href="/status">Status</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Okama Finance Bot Web Service',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'port': os.getenv('PORT', '8000')
    })

@app.route('/status')
def status():
    """Status endpoint"""
    return jsonify({
        'service': 'Okama Finance Bot Web Service',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'port': os.getenv('PORT', '8000'),
        'environment': 'Render'
    })

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    print(f"🌐 Starting simple web service on port {port}")
    print(f"🌐 Binding to 0.0.0.0:{port}")
    
    # Start Flask app - this will bind to the port
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
