import sys
import logging
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import io
from typing import Dict, List, Optional

# Check Python version compatibility
if sys.version_info < (3, 7):
    print("ERROR: Python 3.7+ required. Current version:", sys.version)
    raise RuntimeError("Python 3.7+ required")

from config import Config
from services.asset_service import AssetService
from yandexgpt_service import YandexGPTService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health check for deployment
def health_check():
    """Simple health check for deployment"""
    logger.info("✅ Health check: Okama Finance Bot is running")
    logger.info(f"✅ Environment: {'PRODUCTION' if os.getenv('PRODUCTION') else 'LOCAL'}")
    logger.info(f"✅ Python version: {sys.version}")
    logger.info(f"✅ Bot token configured: {'Yes' if Config.TELEGRAM_BOT_TOKEN else 'No'}")
    return True

class OkamaFinanceBot:
    """Simple Telegram bot class for financial analysis with Okama library"""
    
    def __init__(self):
        """Initialize the bot with required services"""
        Config.validate()
        
        self.asset_service = AssetService()
        self.yandexgpt_service = YandexGPTService()
        
        # User session storage
        self.user_sessions = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""Добро пожаловать в Okama Finance Bot!

Привет {user_name}! Я ваш помощник по финансовому анализу на базе библиотеки Okama.

Что я умею:
• Получение информации об активах
• Текущие цены активов
• История дивидендов
• Базовые метрики производительности
• Чат с YandexGPT о финансах

Быстрый старт:
• Отправьте мне символ актива как "VOO.US"
• Спросите "Информация об SPY.US"
• Используйте команды /asset, /price, /dividends

Популярные активы:
• VOO.US, SPY.US, QQQ.US (ETF)
• RGBITR.INDX, MCFTR.INDX (Индексы)
• GC.COMM, BRENT.COMM (Товары)
• EURUSD.FX (Валюты)

Команды:
/help - Показать все доступные команды
/asset [symbol] - Информация об активе
/price [symbol] - Текущая цена актива
/dividends [symbol] - История дивидендов
/chat - Чат с YandexGPT

Готовы анализировать ваши инвестиции?"""
        
        keyboard = [
            [InlineKeyboardButton("Информация об активе", callback_data="asset_help")],
            [InlineKeyboardButton("Текущая цена", callback_data="price_help")],
            [InlineKeyboardButton("История дивидендов", callback_data="dividends_help")],
            [InlineKeyboardButton("Чат с YandexGPT", callback_data="chat_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """Доступные команды и функции

Основные команды анализа активов:
/asset [symbol] - Получить полную информацию об активе
/price [symbol] - Получить текущую цену актива
/dividends [symbol] - Получить историю дивидендов
/test [symbol] - Тест подключения к Okama API
/testai - Тест подключения к YandexGPT API
/debug [symbols] - Отладка данных портфеля

Чат с YandexGPT:
/chat [question] - Получить финансовый совет от YandexGPT

Примеры:
• /asset VOO.US
• /price SPY.US
• /dividends AGG.US
• /test VOO.US

Естественный язык:
Вы также можете просто написать естественным языком:
• "Информация об VOO.US"
• "Цена SPY.US"
• "Дивиденды AGG.US"

Нужна помощь?
Просто напишите ваш вопрос или используйте команды выше!"""
        
        await update.message.reply_text(help_text)
    
    async def asset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /asset command"""
        if not context.args:
            await update.message.reply_text(
                "Информация об активе\n\n"
                "Пожалуйста, укажите символ:\n"
                "/asset VOO.US\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        await self._get_asset_info(update, symbol)
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        if not context.args:
            await update.message.reply_text(
                "Текущая цена актива\n\n"
                "Пожалуйста, укажите символ:\n"
                "/price VOO.US\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        await self._get_asset_price(update, symbol)
    
    async def dividends_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dividends command"""
        if not context.args:
            await update.message.reply_text(
                "История дивидендов\n\n"
                "Пожалуйста, укажите символ:\n"
                "/dividends VOO.US\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        await self._get_asset_dividends(update, symbol)
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chat command"""
        if not context.args:
            await update.message.reply_text(
                "💬 AI Chat\n\n"
                "Ask me anything about finance:\n"
                "/chat What is diversification?\n"
                "/chat How to calculate Sharpe ratio?\n\n"
                "Or just type your question directly!"
            )
            return
        
        question = " ".join(context.args)
        await self._handle_chat(update, question)
    
    async def _get_asset_info(self, update: Update, symbol: str):
        """Get comprehensive asset information"""
        try:
            await update.message.reply_text(f"🔍 Получаю информацию об активе {symbol}...")
            
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await update.message.reply_text(f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Format the response
            response = f"📊 **Информация об активе {symbol}**\n\n"
            response += f"**Название:** {asset_info.get('name', 'N/A')}\n"
            response += f"**Страна:** {asset_info.get('country', 'N/A')}\n"
            response += f"**Биржа:** {asset_info.get('exchange', 'N/A')}\n"
            response += f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
            response += f"**Тип:** {asset_info.get('type', 'N/A')}\n"
            response += f"**ISIN:** {asset_info.get('isin', 'N/A')}\n"
            response += f"**Первый день:** {asset_info.get('first_date', 'N/A')}\n"
            response += f"**Последний день:** {asset_info.get('last_date', 'N/A')}\n"
            response += f"**Длина периода:** {asset_info.get('period_length', 'N/A')} лет\n\n"
            
            # Add performance metrics
            if asset_info.get('current_price'):
                response += f"**Текущая цена:** {asset_info.get('current_price')} {asset_info.get('currency', '')}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"**Годовая доходность:** {asset_info.get('annual_return')}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"**Общая доходность:** {asset_info.get('total_return')}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"**Волатильность:** {asset_info.get('volatility')}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении информации об активе: {str(e)}")
    
    async def _get_asset_info(self, update: Update, symbol: str):
        """Get comprehensive asset information"""
        try:
            await update.message.reply_text(f"📊 Получаю информацию об активе {symbol}...")
            
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                # Check if we have suggestions
                if 'suggestions' in asset_info:
                    await update.message.reply_text(
                        f"❌ {asset_info['error']}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Build response message
            response = f"📊 **Информация об активе {symbol}**\n\n"
            response += f"**Название:** {asset_info.get('name', 'N/A')}\n"
            response += f"**Страна:** {asset_info.get('country', 'N/A')}\n"
            response += f"**Биржа:** {asset_info.get('exchange', 'N/A')}\n"
            response += f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
            response += f"**Тип:** {asset_info.get('type', 'N/A')}\n"
            response += f"**ISIN:** {asset_info.get('isin', 'N/A')}\n"
            response += f"**Первый день:** {asset_info.get('first_date', 'N/A')}\n"
            response += f"**Последний день:** {asset_info.get('last_date', 'N/A')}\n"
            response += f"**Длина периода:** {asset_info.get('period_length', 'N/A')} лет\n\n"
            
            # Add performance metrics
            if asset_info.get('current_price'):
                response += f"**Текущая цена:** {asset_info.get('current_price')} {asset_info.get('currency', '')}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"**Годовая доходность:** {asset_info.get('annual_return')}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"**Общая доходность:** {asset_info.get('total_return')}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"**Волатильность:** {asset_info.get('volatility')}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении информации об активе: {str(e)}")
    
    async def _get_asset_price(self, update: Update, symbol: str):
        """Get current asset price"""
        try:
            await update.message.reply_text(f"💰 Получаю текущую цену {symbol}...")
            
            price_info = self.asset_service.get_asset_price(symbol)
            
            if 'error' in price_info:
                # Check if we have suggestions
                if 'suggestions' in price_info:
                    await update.message.reply_text(
                        f"❌ {price_info['error']}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"❌ Ошибка: {price_info['error']}")
                return
            
            response = f"💰 **Цена актива {symbol}**\n\n"
            response += f"**Текущая цена:** {price_info.get('price', 'N/A')} {price_info.get('currency', '')}\n"
            response += f"**Время:** {price_info.get('timestamp', 'N/A')}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении цены: {str(e)}")
    
    async def _get_asset_dividends(self, update: Update, symbol: str):
        """Get asset dividend history"""
        try:
            await update.message.reply_text(f"💵 Получаю историю дивидендов {symbol}...")
            
            dividend_info = self.asset_service.get_asset_dividends(symbol)
            
            if 'error' in dividend_info:
                # Check if we have suggestions
                if 'suggestions' in dividend_info:
                    await update.message.reply_text(
                        f"❌ {dividend_info['error']}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"❌ Ошибка: {dividend_info['error']}")
                return
            
            response = f"💵 **История дивидендов {symbol}**\n\n"
            response += f"**Валюта:** {dividend_info.get('currency', 'N/A')}\n"
            response += f"**Количество периодов:** {dividend_info.get('total_periods', 'N/A')}\n\n"
            
            # Add recent dividends
            dividends = dividend_info.get('dividends', {})
            if dividends:
                response += "**Последние дивиденды:**\n"
                for date, amount in list(dividends.items())[-5:]:  # Last 5
                    if amount > 0:
                        response += f"• {date}: {amount:.4f}\n"
                    else:
                        response += f"• {date}: Нет дивидендов\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении дивидендов: {str(e)}")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test command to verify Okama integration"""
        if not context.args:
            await update.message.reply_text(
                "Тест подключения к Okama\n\n"
                "Пожалуйста, укажите символ для тестирования:\n"
                "/test VOO.US\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"🧪 Тестирую подключение к Okama для {symbol}...")
        
        try:
            # Test basic asset creation
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await update.message.reply_text(f"❌ Тест не прошел: {asset_info['error']}")
                return
            
            await update.message.reply_text(
                f"✅ Тест прошел успешно!\n\n"
                f"**Символ:** {symbol}\n"
                f"**Название:** {asset_info.get('name', 'N/A')}\n"
                f"**Тип:** {asset_info.get('type', 'N/A')}\n"
                f"**Валюта:** {asset_info.get('currency', 'N/A')}\n\n"
                f"Okama API работает корректно!"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Тест не прошел: {str(e)}")
    
    async def test_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test command to verify YandexGPT integration"""
        await update.message.reply_text("🧪 Тестирую подключение к YandexGPT...")
        
        try:
            # Test with a simple question
            test_question = "What is diversification in finance?"
            response = self.yandexgpt_service.ask_question(test_question)
            
            if response and 'error' not in response:
                await update.message.reply_text(
                    f"✅ Тест YandexGPT прошел успешно!\n\n"
                    f"**Вопрос:** {test_question}\n"
                    f"**Ответ:** {response[:200]}..."
                )
            else:
                await update.message.reply_text(f"❌ Тест YandexGPT не прошел: {response}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Тест YandexGPT не прошел: {str(e)}")



    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user_message = update.message.text.strip()
        
        if not user_message:
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Analyze user intent using YandexGPT
            analysis = self.yandexgpt_service.analyze_query(user_message)
            
            if analysis['is_chat']:
                await self._handle_chat(update, user_message)
            else:
                # Handle analysis requests
                symbols = analysis['symbols']
                intent = analysis['intent']
                
                if not symbols:
                    await update.message.reply_text(
                        "I couldn't identify any symbols in your message. "
                        "Please provide symbols like RGBITR.INDX, MCFTR.INDX, GC.COMM, AGG.US, SPY.US, etc."
                    )
                    return
                
                # Route to appropriate analysis method
                if intent == 'asset':
                    await self._get_asset_info(update, symbols[0])
                elif intent == 'price':
                    await self._get_asset_price(update, symbols[0])
                elif intent == 'dividends':
                    await self._get_asset_dividends(update, symbols[0])
                else:
                    await self._handle_chat(update, user_message)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your request. "
                "Please try again or use /help for available commands."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "asset_help":
            await query.edit_message_text(
                "Информация об активе\n\n"
                "Отправьте мне символ для получения информации:\n"
                "• VOO.US\n"
                "• /asset SPY.US\n\n"
                "Я покажу вам:\n"
                "• Основную информацию об активе\n"
                "• Текущую цену\n"
                "• Метрики производительности"
            )
        elif query.data == "price_help":
            await query.edit_message_text(
                "Анализ рисков\n\n"
                "Отправьте мне символы для анализа рисков:\n"
                "• AGG.US SPY.US\n"
                "• /risk GC.COMM\n\n"
                "Я покажу вам:\n"
                "• Текущую цену (20 мин задержка)\n"
                "• Валюту актива"
            )
        elif query.data == "dividends_help":
            await query.edit_message_text(
                "История дивидендов\n\n"
                "Отправьте мне символ для получения дивидендов:\n"
                "• AGG.US\n"
                "• /dividends VOO.US\n\n"
                "Я покажу вам:\n"
                "• Историю дивидендов\n"
                "• Последние выплаты"
            )
        elif query.data == "chat_help":
            await query.edit_message_text(
                "Чат с YandexGPT\n\n"
                "Спросите меня о чем угодно по финансам:\n"
                "• Что такое диверсификация?\n"
                "• Как рассчитать коэффициент Шарпа?\n"
                "• Лучшие практики ребалансировки портфеля\n\n"
                "Я предоставлю экспертную финансовую консультацию на базе YandexGPT!"
            )
    

    

    

    async def _handle_chat(self, update: Update, question: str):
        """Handle AI chat requests"""
        try:
            await update.message.reply_text("🤔 Thinking...")
            
            # Get AI response
            response = self.yandexgpt_service.ask_question(question)
            
            # Send response
            await update.message.reply_text(
                f"💬 AI Financial Advisor\n\n{response}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting AI response: {str(e)}")
    
    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("asset", self.asset_command))
        application.add_handler(CommandHandler("price", self.price_command))
        application.add_handler(CommandHandler("dividends", self.dividends_command))
        application.add_handler(CommandHandler("chat", self.chat_command))
        application.add_handler(CommandHandler("test", self.test_command))
        application.add_handler(CommandHandler("testai", self.test_ai_command))
        
        # Add message and callback handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Start the bot
        logger.info("Starting Okama Finance Bot...")
        application.run_polling()

if __name__ == "__main__":
    try:
        logger.info(f"Starting Okama Finance Bot with Python {sys.version}")
        logger.info(f"Python version info: {sys.version_info}")
        
        # Perform health check
        health_check()
        
        # Optional HTTP health server for platforms expecting an open PORT
        port_env = os.getenv('PORT')
        if port_env:
            try:
                bind_port = int(port_env)
                class HealthHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        payload = {
                            "status": "ok",
                            "service": "okama-finance-bot",
                            "environment": "RENDER" if os.getenv('RENDER') else "LOCAL"
                        }
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(payload).encode('utf-8'))
                    def log_message(self, format, *args):
                        return
                def serve_health():
                    server = HTTPServer(('0.0.0.0', bind_port), HealthHandler)
                    logger.info(f"Health server listening on 0.0.0.0:{bind_port}")
                    server.serve_forever()
                threading.Thread(target=serve_health, daemon=True).start()
            except Exception as e:
                logger.warning(f"Failed to start health server on PORT={port_env}: {e}")
        
        if sys.version_info >= (3, 13):
            logger.info("✅ Running on Python 3.13+ with latest python-telegram-bot")
        elif sys.version_info >= (3, 12):
            logger.info("✅ Running on Python 3.12+ with latest python-telegram-bot")
        
        logger.info("🚀 Initializing bot services...")
        bot = OkamaFinanceBot()
        logger.info("✅ Bot services initialized successfully")
        logger.info("🤖 Starting Telegram bot...")
        bot.run()
    except Exception as e:
        logger.error(f"❌ Fatal error starting bot: {e}")
        logger.error(f"Python version: {sys.version}")
        logger.error(f"Python executable: {sys.executable}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
