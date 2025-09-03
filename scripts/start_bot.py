#!/usr/bin/env python3
"""
Startup script for Okama Finance Bot
This script can be used to start the bot directly or as a fallback
"""

import os
import sys
import time
import signal
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from bot import ShansAi

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def start_bot():
    """Start the bot"""
    try:
        print("🤖 Starting Okama Finance Bot v2.0...")
        
        # Create and start bot
        bot = ShansAi()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Okama Finance Bot Startup Script")
    print(f"🌍 Environment: {'RENDER' if os.getenv('RENDER') else 'LOCAL'}")
    print(f"🐍 Python version: {sys.version}")
    
    # Optional HTTP health server for platforms expecting an open PORT
    port_env = os.getenv('PORT')
    if port_env:
        try:
            bind_port = int(port_env)
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    payload = {
                        "status": "ok",
                        "service": "okama-finance-bot",
                        "environment": "RENDER" if os.getenv('RENDER') else "LOCAL"
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                def log_message(self, format, *args):
                    return
            def serve_health():
                server = HTTPServer(('0.0.0.0', bind_port), HealthHandler)
                print(f"🩺 Health server listening on 0.0.0.0:{bind_port}")
                server.serve_forever()
            threading.Thread(target=serve_health, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Failed to start health server on PORT={port_env}: {e}")
    
    # Start the bot
    start_bot()

if __name__ == "__main__":
    main()
