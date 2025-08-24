import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Okama Finance Bot"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'okama_finance_bot')
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Okama Configuration
    OKAMA_API_KEY = os.getenv('OKAMA_API_KEY')
    
    # Bot Settings
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    
    # Supported Commands
    SUPPORTED_COMMANDS = {
        '/start': 'Start the bot and get help',
        '/help': 'Show available commands and features',
        '/portfolio': 'Analyze portfolio performance',
        '/risk': 'Calculate portfolio risk metrics',
        '/correlation': 'Show asset correlation matrix',
        '/efficient_frontier': 'Generate efficient frontier plot',
        '/compare': 'Compare multiple assets',
        '/chat': 'Chat with ChatGPT about finance'
    }
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        missing = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.OPENAI_API_KEY:
            missing.append('OPENAI_API_KEY')
            
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
