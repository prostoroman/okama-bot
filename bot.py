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
from services.intent_parser_enhanced import EnhancedIntentParser
from services.asset_resolver_enhanced import EnhancedAssetResolver
from services.okama_handler_enhanced import EnhancedOkamaHandler
from services.report_builder_enhanced import EnhancedReportBuilder
from services.analysis_engine_enhanced import EnhancedAnalysisEngine
from services.financial_brain_enhanced import EnhancedOkamaFinancialBrain

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
        self.intent_parser = EnhancedIntentParser()
        self.asset_resolver = EnhancedAssetResolver()
        self.okama_handler = EnhancedOkamaHandler()
        self.report_builder = EnhancedReportBuilder()
        self.analysis_engine = EnhancedAnalysisEngine()
        self.financial_brain = EnhancedOkamaFinancialBrain()
        
        # User session storage
        self.user_sessions = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""Добро пожаловать в Okama Financial Brain! 🧠

Привет {user_name}! Я - "Okama Financial Brain", ядро интеллектуальной системы для финансового анализа.

🚀 **Что я умею:**
• **Анализ активов** - полная информация по одному активу
• **Сравнение активов** - сопоставление нескольких инструментов
• **Анализ портфеля** - оптимизация и оценка рисков
• **Макроэкономический анализ** - валюты, сырье, индексы
• **Анализ инфляции** - данные по инфляции в разных странах
• **AI-аналитика** - интеллектуальные выводы и рекомендации

💡 **Просто напишите естественным языком:**
• "Проанализируй Apple и Tesla"
• "Сравни золото и нефть"
• "Портфель из VOO.US и AGG.US с весами 60% и 40%"
• "Анализ инфляции в США за последние 5 лет"
• "Сравни S&P 500 и NASDAQ в рублях"

📊 **Популярные активы:**
• **ETF:** VOO.US, SPY.US, QQQ.US
• **Индексы:** SPX.INDX, RTSI.INDX, DAX.INDX
• **Товары:** GC.COMM, BRENT.COMM, SILVER.COMM
• **Валюты:** EURUSD.FX, GBPUSD.FX
• **Акции:** AAPL.US, TSLA.US, SBER.MOEX

🔧 **Команды:**
/help - Все доступные команды
/asset [symbol] - Информация об активе
/price [symbol] - Текущая цена
/dividends [symbol] - История дивидендов
/chat - Чат с AI-советником

Я автоматически:
✅ Распознаю ваши намерения
✅ Нормализую названия активов
✅ Строю аналитические отчеты
✅ Генерирую графики
✅ Предоставляю AI-выводы
✅ Даю практические рекомендации

Готовы к интеллектуальному финансовому анализу? 🚀"""
        
        keyboard = [
            [InlineKeyboardButton("🧠 Финансовый анализ", callback_data="analysis_help")],
            [InlineKeyboardButton("📊 Анализ портфеля", callback_data="portfolio_help")],
            [InlineKeyboardButton("⚖️ Сравнение активов", callback_data="compare_help")],
            [InlineKeyboardButton("💬 AI-советник", callback_data="chat_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🧠 **Okama Financial Brain - Помощь**

🚀 **Основные команды:**
/asset [symbol] - Полная информация об активе
/price [symbol] - Текущая цена актива
/dividends [symbol] - История дивидендов
/test [symbol] - Тест подключения к Okama API
/testai - Тест подключения к YandexGPT API

💬 **AI-советник:**
/chat [question] - Получить финансовый совет от AI

📊 **Примеры команд:**
• /asset VOO.US
• /price SPY.US
• /dividends AGG.US
• /test VOO.US

💡 **Естественный язык (рекомендуется!):**
Просто напишите ваш запрос естественным языком:

**Анализ активов:**
• "Проанализируй Apple"
• "Информация о Tesla"
• "Покажи данные по SBER.MOEX"

**Сравнение активов:**
• "Сравни Apple и Microsoft"
• "Что лучше: VOO.US или SPY.US?"
• "Сопоставь золото и серебро"

**Анализ портфеля:**
• "Портфель из VOO.US и AGG.US"
• "Оптимизируй портфель с весами 60% акции, 40% облигации"
• "Анализ рисков портфеля"

**Макроэкономический анализ:**
• "Сравни S&P 500 и NASDAQ"
• "Анализ валютных пар"
• "Динамика цен на нефть и золото"

**Анализ инфляции:**
• "Инфляция в США за последние 5 лет"
• "CPI данные по России"
• "Тренды инфляции в Европе"

**Специфические запросы:**
• "Анализ в рублях"
• "За период 2020-2024"
• "Сравни доходность к риску"

🎯 **Что происходит автоматически:**
1. **Распознавание намерения** - понимаю, что вы хотите
2. **Нормализация активов** - перевожу названия в тикеры Okama
3. **Получение данных** - загружаю актуальную информацию
4. **Построение отчетов** - создаю аналитические таблицы
5. **Генерация графиков** - визуализирую данные
6. **AI-анализ** - предоставляю интеллектуальные выводы
7. **Рекомендации** - даю практические советы

🔧 **Нужна помощь?**
Просто напишите ваш вопрос естественным языком или используйте команды выше!"""
        
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
        """Handle incoming text messages using Okama Financial Brain"""
        user_message = update.message.text.strip()
        
        if not user_message:
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Используем Enhanced Okama Financial Brain для полного цикла анализа
            result = self.financial_brain.process_query(user_message)
            
            # Формируем финальный ответ
            final_response = self.financial_brain.format_final_response(result)
            
            # Отправляем текстовый ответ
            await self._send_long_text(update, final_response)
            
            # Отправляем графики
            for img_bytes in result.charts:
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=io.BytesIO(img_bytes),
                        caption="📊 График анализа"
                    )
                except Exception as e:
                    logger.error(f"Error sending chart: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Enhanced Financial Brain processing: {e}")
            
            # Fallback к старому методу для совместимости
            try:
                await self._handle_message_fallback(update, context, user_message)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                await update.message.reply_text(
                    "Извините, произошла ошибка при обработке вашего запроса. "
                    "Попробуйте переформулировать вопрос или используйте /help для доступных команд. "
                    "Если вы запрашиваете данные по MOEX (например, SBER.MOEX), они могут быть временно недоступны."
                )

    async def _handle_message_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
        """Fallback метод для обработки сообщений (старая логика)"""
        try:
            # Старая логика обработки
            parsed = self.intent_parser.parse(user_message)

            # Chat fallback
            if parsed.intent == 'chat':
                await self._handle_chat(update, user_message)
                return

            # Resolve assets as needed
            resolved = self.asset_resolver.resolve(parsed.raw_assets) if parsed.raw_assets else []
            valid_tickers = [r.ticker for r in resolved if r.valid]

            # Dispatch by intent
            report_text = None
            images = []
            ai_summary = None

            if parsed.intent == 'asset_single':
                if not valid_tickers:
                    await update.message.reply_text("Не удалось распознать актив. Укажите тикер, например AAPL.US, SBER.MOEX, GC.COMM")
                    return
                result = self.okama_handler.get_single_asset(valid_tickers[0], base_currency=parsed.options.get('base_currency'))
                report_text, images = self.report_builder.build_single_asset_report(result)
                ai_summary = self.analysis_engine.summarize('single_asset', {"metrics": result.get("metrics", {})}, user_message)

            elif parsed.intent == 'asset_compare' or (parsed.intent == 'macro'):
                if len(valid_tickers) < 2:
                    # If only one valid, treat as single asset
                    if len(valid_tickers) == 1:
                        result = self.okama_handler.get_single_asset(valid_tickers[0], base_currency=parsed.options.get('base_currency'))
                        report_text, images = self.report_builder.build_single_asset_report(result)
                        ai_summary = self.analysis_engine.summarize('single_asset', {"metrics": result.get("metrics", {})}, user_message)
                    else:
                        await update.message.reply_text("Для сравнения укажите как минимум два актива.")
                        return
                else:
                    result = self.okama_handler.get_multiple_assets(valid_tickers)
                    report_text, images = self.report_builder.build_multi_asset_report(result)
                    ai_summary = self.analysis_engine.summarize('asset_compare', {"metrics": result.get("metrics", {}), "correlation": result.get("correlation", {})}, user_message)

            elif parsed.intent == 'portfolio':
                if len(valid_tickers) < 2:
                    await update.message.reply_text("Для анализа портфеля укажите как минимум два актива.")
                    return
                result = self.okama_handler.get_portfolio(valid_tickers)
                report_text, images = self.report_builder.build_portfolio_report(result)
                ai_summary = self.analysis_engine.summarize('portfolio', {"metrics": result.get("metrics", {})}, user_message)

            elif parsed.intent == 'inflation':
                result = self.okama_handler.get_inflation()
                report_text, images = self.report_builder.build_inflation_report(result)
                ai_summary = self.analysis_engine.summarize('inflation', {}, user_message)

            else:
                # Fallback to AI chat if intent not recognized
                await self._handle_chat(update, user_message)
                return

            # Send text and AI summary
            final_text = report_text or ""
            if ai_summary:
                final_text = f"{final_text}\n\nВыводы AI:\n{ai_summary}"
            await self._send_long_text(update, final_text)

            # Send images
            for img_bytes in images:
                try:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(img_bytes))
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in fallback message handling: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Попробуйте переформулировать вопрос или используйте /help для доступных команд. "
                "Если вы запрашиваете данные по MOEX (например, SBER.MOEX), они могут быть временно недоступны."
            )

    async def _send_long_text(self, update: Update, text: str):
        if not text:
            return
        max_len = getattr(Config, 'MAX_MESSAGE_LENGTH', 4000)
        start = 0
        while start < len(text):
            chunk = text[start:start + max_len]
            await update.message.reply_text(chunk)
            start += max_len
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "analysis_help":
            await query.edit_message_text(
                "🧠 **Финансовый анализ**\n\n"
                "Просто напишите ваш запрос естественным языком:\n\n"
                "**Анализ одного актива:**\n"
                "• \"Проанализируй Apple\"\n"
                "• \"Информация о Tesla\"\n"
                "• \"Покажи данные по SBER.MOEX\"\n\n"
                "**Макроэкономический анализ:**\n"
                "• \"Анализ золота\"\n"
                "• \"Динамика нефти\"\n"
                "• \"Тренды валютных пар\"\n\n"
                "**Анализ инфляции:**\n"
                "• \"Инфляция в США\"\n"
                "• \"CPI данные по России\"\n\n"
                "Я автоматически:\n"
                "✅ Распознаю ваши намерения\n"
                "✅ Нормализую названия активов\n"
                "✅ Строю аналитические отчеты\n"
                "✅ Генерирую графики\n"
                "✅ Предоставляю AI-выводы"
            )
        elif query.data == "portfolio_help":
            await query.edit_message_text(
                "📊 **Анализ портфеля**\n\n"
                "Просто напишите ваш запрос естественным языком:\n\n"
                "**Базовый анализ:**\n"
                "• \"Портфель из VOO.US и AGG.US\"\n"
                "• \"Анализ рисков портфеля\"\n\n"
                "**С весами:**\n"
                "• \"Портфель 60% акции, 40% облигации\"\n"
                "• \"Оптимизируй портфель с весами 70% и 30%\"\n\n"
                "**Специфические запросы:**\n"
                "• \"Анализ в рублях\"\n"
                "• \"За период 2020-2024\"\n\n"
                "Я автоматически:\n"
                "✅ Оптимизирую веса (если не указаны)\n"
                "✅ Рассчитываю метрики риска\n"
                "✅ Строю efficient frontier\n"
                "✅ Предоставляю рекомендации"
            )
        elif query.data == "compare_help":
            await query.edit_message_text(
                "⚖️ **Сравнение активов**\n\n"
                "Просто напишите ваш запрос естественным языком:\n\n"
                "**Сравнение акций:**\n"
                "• \"Сравни Apple и Microsoft\"\n"
                "• \"Что лучше: VOO.US или SPY.US?\"\n\n"
                "**Сравнение классов активов:**\n"
                "• \"Сопоставь золото и серебро\"\n"
                "• \"Сравни S&P 500 и NASDAQ\"\n\n"
                "**Сравнение валют:**\n"
                "• \"EUR/USD vs GBP/USD\"\n"
                "• \"Анализ валютных пар\"\n\n"
                "Я автоматически:\n"
                "✅ Сравниваю доходность\n"
                "✅ Анализирую корреляции\n"
                "✅ Строю сравнительные графики\n"
                "✅ Предоставляю AI-выводы"
            )
        elif query.data == "chat_help":
            await query.edit_message_text(
                "💬 **AI-советник**\n\n"
                "Спросите меня о чем угодно по финансам:\n\n"
                "**Теория:**\n"
                "• \"Что такое диверсификация?\"\n"
                "• \"Как рассчитать коэффициент Шарпа?\"\n"
                "• \"Объясни efficient frontier\"\n\n"
                "**Практика:**\n"
                "• \"Лучшие практики ребалансировки\"\n"
                "• \"Как управлять рисками?\"\n"
                "• \"Стратегии долгосрочного инвестирования\"\n\n"
                "**Анализ:**\n"
                "• \"Интерпретируй эти метрики\"\n"
                "• \"Что означают эти данные?\"\n\n"
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
