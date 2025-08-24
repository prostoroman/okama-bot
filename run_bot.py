#!/usr/bin/env python3
"""
Simple script to run the Okama Finance Bot locally
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main function to run the bot"""
    print("🚀 Starting Okama Finance Bot...")
    
    # Check if required environment variables are set
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("   Please create a .env file with your bot token")
        sys.exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please create a .env file with your OpenAI API key")
        sys.exit(1)
    
    print("✅ Environment variables loaded successfully")
    print("🤖 Starting Telegram bot...")
    
    try:
        from bot import OkamaFinanceBot
        bot = OkamaFinanceBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
