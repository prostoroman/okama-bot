#!/usr/bin/env python3
"""
Web service for Render port scanning that transitions to running the bot
This service uses Flask to bind to a port to satisfy Render's requirements,
then starts the bot as a background process while maintaining the web service.
"""

import os
import sys
import time
import socket
import threading
import subprocess
import signal
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

# Global bot status
bot_status = {
    'running': False,
    'start_time': None,
    'last_error': None
}

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
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>🤖 Okama Finance Bot</h1>
        <p class="status">✅ Web service is running</p>
        <p>This web service exists to satisfy Render's port scanning requirements.</p>
        <p>The Telegram bot is running as a background process.</p>
        <p><a href="/health">Health Check</a></p>
        <p><a href="/status">Bot Status</a></p>
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
        'bot_running': bot_status['running'],
        'uptime': time.time() - bot_status['start_time'] if bot_status['start_time'] else None
    })

@app.route('/status')
def status():
    """Bot status endpoint"""
    return jsonify({
        'bot_status': bot_status,
        'service': 'Okama Finance Bot',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })

def check_port_available(port):
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

def start_bot_background():
    """Start the bot in a background thread"""
    try:
        print("🤖 Starting bot in background...")
        
        # Import and start bot
        from bot import OkamaFinanceBotV2
        
        def run_bot():
            try:
                bot = OkamaFinanceBotV2()
                bot.run()
            except Exception as e:
                print(f"❌ Bot error: {e}")
                bot_status['last_error'] = str(e)
                bot_status['running'] = False
                import traceback
                traceback.print_exc()
        
        # Start bot in background thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Update status
        bot_status['running'] = True
        bot_status['start_time'] = time.time()
        bot_status['last_error'] = None
        
        print("✅ Bot started in background thread")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        bot_status['last_error'] = str(e)
        bot_status['running'] = False
        import traceback
        traceback.print_exc()
        return False

def start_web_service(port=8000):
    """Start web service and bot"""
    try:
        # Check if port is available
        if not check_port_available(port):
            print(f"❌ Port {port} is not available")
            return False
        
        print(f"✅ Port {port} is available")
        print(f"🌐 Starting Flask web service on 0.0.0.0:{port}")
        
        # Start the bot in background (but don't fail if it doesn't start)
        try:
            if start_bot_background():
                print("🚀 Bot is now running alongside web service")
                print("🤖 Bot is active and processing Telegram messages")
            else:
                print("⚠️ Bot failed to start, but web service will continue")
        except Exception as e:
            print(f"⚠️ Bot startup error (non-critical): {e}")
            print("🌐 Web service will continue running without bot")
        
        # Start Flask app - this is the critical part for port binding
        print("🌐 Starting Flask server...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start web service: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🌐 Starting Okama Finance Bot with Flask web service...")
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8000))
    print(f"🚀 Binding to port {port}")
    
    # Ensure we're binding to the correct interface
    print(f"🌐 Binding to 0.0.0.0:{port}")
    
    # Start the web service - this will bind to the port
    start_web_service(port)

if __name__ == "__main__":
    main()
