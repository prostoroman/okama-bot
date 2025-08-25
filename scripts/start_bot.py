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
from bot import OkamaFinanceBotV2

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def start_bot():
    """Start the bot"""
    try:
        print("🤖 Starting Okama Finance Bot v2.0...")
        
        # Create and start bot
        bot = OkamaFinanceBotV2()
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
    
    # Start the bot
    start_bot()

if __name__ == "__main__":
    main()
