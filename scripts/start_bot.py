#!/usr/bin/env python3
"""
Startup script for Okama Finance Bot (Local Development Only)
This script is for local development and testing.
For Render deployment, use scripts/web_service.py instead.
"""

import os
import sys
import time
import logging
import threading

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

def main():
    """Main startup function for local development"""
    print("🚀 Okama Finance Bot v2.0 - Local Development Mode")
    print(f"✅ Python version: {sys.version}")
    print("🔒 IMPORTANT: This is for LOCAL DEVELOPMENT only")
    print("🌐 For Render deployment, use: python scripts/web_service.py")
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    # Import and start bot
    try:
        print("📦 Importing bot modules...")
        from bot import OkamaFinanceBotV2
        
        print("🤖 Creating bot instance...")
        bot = OkamaFinanceBotV2()
        
        print("🚀 Starting bot in local development mode...")
        bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
