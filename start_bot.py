#!/usr/bin/env python3
"""
Robust startup script for Okama Finance Bot
Handles Python version compatibility and provides better error handling
"""

import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 11:
        logger.error(f"Python 3.11+ required, got {version.major}.{version.minor}.{version.micro}")
        return False
    
    if version.minor >= 13:
        logger.warning(f"Python 3.13+ may have compatibility issues. Consider using Python 3.11")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'telegram',
        'openai', 
        'okama',
        'matplotlib',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} imported successfully")
        except ImportError as e:
            logger.error(f"❌ {package} import failed: {e}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def main():
    """Main startup function"""
    logger.info("🚀 Starting Okama Finance Bot...")
    
    # Check Python version
    if not check_python_version():
        logger.error("Python version check failed")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        sys.exit(1)
    
    # Check environment variables
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("   Please create a .env file with your bot token")
        sys.exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("❌ OPENAI_API_KEY not found in environment variables")
        logger.error("   Please create a .env file with your OpenAI API key")
        sys.exit(1)
    
    logger.info("✅ Environment variables loaded successfully")
    logger.info("🤖 Starting Telegram bot...")
    
    try:
        from bot import OkamaFinanceBot
        bot = OkamaFinanceBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        logger.error("Full traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
