#!/usr/bin/env python3
"""
Minimal web service for Render port scanning
This service binds to a port briefly to satisfy Render's requirements,
then exits gracefully, allowing the background worker to take over.
"""

import os
import sys
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            response = "Okama Finance Bot - Background Worker Active\n"
            response += f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            response += "This is a background worker, not a web service.\n"
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        """Suppress logging"""
        pass

def start_web_service(port=8000):
    """Start a minimal web service on the specified port"""
    try:
        # Create server
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"✅ Web service started on port {port}")
        print("🔒 This service will exit after Render port scan")
        
        # Wait a bit for Render to detect the port
        time.sleep(30)
        
        # Shutdown gracefully
        server.shutdown()
        server.server_close()
        print("✅ Web service shutdown complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start web service: {e}")
        return False

def main():
    """Main function"""
    print("🌐 Starting minimal web service for Render port scan...")
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8000))
    
    if start_web_service(port):
        print("✅ Port scan requirement satisfied")
        print("🚀 Now starting background worker...")
        sys.exit(0)
    else:
        print("❌ Failed to satisfy port scan requirement")
        sys.exit(1)

if __name__ == "__main__":
    main()
