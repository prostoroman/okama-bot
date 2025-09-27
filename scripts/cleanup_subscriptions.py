#!/usr/bin/env python3
"""
Script to cleanup expired subscriptions
Run this periodically (e.g., daily) to downgrade expired Pro users to free
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import cleanup_expired_subscriptions

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to cleanup expired subscriptions"""
    try:
        logger.info("Starting cleanup of expired subscriptions...")
        
        cleaned_count = cleanup_expired_subscriptions()
        
        if cleaned_count > 0:
            logger.info(f"Successfully cleaned up {cleaned_count} expired subscriptions")
        else:
            logger.info("No expired subscriptions found")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
