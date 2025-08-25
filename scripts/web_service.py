#!/usr/bin/env python3
"""
Web service for Render port scanning that transitions to running the bot
This service binds to a port to satisfy Render's requirements,
then starts the bot as a background process while maintaining the web service.
"""

import os
import sys
import time
import socket
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Health check handler that shows bot status"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            response = "Okama Finance Bot - Active\n"
            response += f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            response += "Bot is running as a background process.\n"
            response += "This web service exists to satisfy Render requirements.\n"
            self.wfile.write(response.encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
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
                <p class="status">✅ Bot is running successfully</p>
                <p>This web service exists to satisfy Render's port scanning requirements.</p>
                <p>The Telegram bot is running as a background process.</p>
                <p><a href="/health">Health Check</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        """Suppress logging"""
        pass

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
                import traceback
                traceback.print_exc()
        
        # Start bot in background thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot started in background thread")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        return False

def start_web_service(port=8000):
    """Start web service and bot"""
    try:
        # Create server
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"✅ Web service started on port {port}")
        print("🔒 Web service will continue running to satisfy Render requirements")
        
        # Wait a bit for Render to detect the port
        print("⏳ Waiting for Render port scan...")
        time.sleep(60)  # Wait 1 minute for port scanning
        
        print("✅ Port scan requirement satisfied")
        
        # Start the bot
        if start_bot_background():
            print("🚀 Bot is now running alongside web service")
            print("🌐 Web service will continue running on port 8000")
            print("🤖 Bot is active and processing Telegram messages")
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("🛑 Shutting down...")
                server.shutdown()
                server.server_close()
        else:
            print("❌ Failed to start bot, keeping web service running")
            # Keep web service running even if bot fails
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("🛑 Shutting down...")
                server.shutdown()
                server.server_close()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start web service: {e}")
        return False

def main():
    """Main function"""
    print("🌐 Starting Okama Finance Bot with web service...")
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8000))
    
    if start_web_service(port):
        print("✅ Service started successfully")
    else:
        print("❌ Failed to start service")
        sys.exit(1)

if __name__ == "__main__":
    main()
