import os
from dotenv import load_dotenv

# Load environment variables from config.env
load_dotenv('config.env')

class Config:
    """Configuration class for the Okama Finance Bot"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'okama_finance_bot')

    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    
    # YandexGPT Configuration
    YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
    YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
    
    # Okama Configuration
    OKAMA_API_KEY = os.getenv('OKAMA_API_KEY')
    
    # Bot Settings
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    
    # Supported Commands
    SUPPORTED_COMMANDS = {
        '/start': 'Start the bot and get help',
    
        '/info': 'Show detailed information about an asset',
        '/price': 'Show current price for an asset',
        '/dividends': 'Show dividend history for an asset',
        '/chat': 'Chat with YandexGPT about finance',
        '/test': 'Test Okama integration',
        '/testai': 'Test YandexGPT integration'
    }
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        missing = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.YANDEX_API_KEY:
            missing.append('YANDEX_API_KEY')
        if not cls.YANDEX_FOLDER_ID:
            missing.append('YANDEX_FOLDER_ID')
            
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
