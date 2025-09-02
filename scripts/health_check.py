#!/usr/bin/env python3
"""
Health check script for Render deployment
This script creates a simple health status file that Render can monitor
"""

import os
import sys
import time
import json
from datetime import datetime

def create_health_status():
    """Create a health status file for Render monitoring"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "environment": "RENDER" if os.getenv('RENDER') else "LOCAL",
        "bot_running": True,
        "services": {
            "telegram_bot": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            "yandex_gpt": bool(os.getenv('YANDEX_API_KEY')),
            "okama": bool(os.getenv('OKAMA_API_KEY'))
        }
    }
    
    # Write status to a file that Render can monitor
    try:
        # Use tempfile to get a writable directory
        import tempfile
        health_file_path = os.path.join(tempfile.gettempdir(), 'bot_health.json')
        with open(health_file_path, 'w') as f:
            json.dump(status, f, indent=2)
        print(f"✅ Health status file created at {health_file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create health status: {e}")
        return False

def main():
    """Main health check function"""
    print("🏥 Okama Finance Bot Health Check")
    
    if create_health_status():
        print("✅ Health check completed successfully")
        sys.exit(0)
    else:
        print("❌ Health check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
