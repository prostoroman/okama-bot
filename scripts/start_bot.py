#!/usr/bin/env python3
"""
Startup script for Okama Finance Bot on Render
This script ensures proper initialization and health checks
"""

import os
import sys
import time
import logging
import threading
import subprocess

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'YANDEX_API_KEY', 
        'YANDEX_FOLDER_ID'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def run_health_check():
    """Run health check script"""
    try:
        result = subprocess.run([sys.executable, 'scripts/health_check.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info("✅ Health check completed successfully")
        else:
            logger.warning(f"⚠️ Health check returned code {result.returncode}")
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")

def health_check_worker():
    """Background worker for periodic health checks"""
    while True:
        try:
            time.sleep(300)  # Run every 5 minutes
            run_health_check()
        except Exception as e:
            logger.error(f"Health check worker error: {e}")

def main():
    """Main startup function"""
    print("🚀 Okama Finance Bot v2.0 - Render Startup")
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Environment: {'RENDER' if os.getenv('RENDER') else 'LOCAL'}")
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    # Start health check worker in background
    if os.getenv('RENDER'):
        print("🏥 Starting health check worker...")
        health_thread = threading.Thread(target=health_check_worker, daemon=True)
        health_thread.start()
        print("✅ Health check worker started")
    
    # Import and start bot
    try:
        print("📦 Importing bot modules...")
        from bot import OkamaFinanceBotV2
        
        print("🤖 Creating bot instance...")
        bot = OkamaFinanceBotV2()
        
        print("🚀 Starting bot...")
        bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
