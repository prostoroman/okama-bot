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
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
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
        
    async def _send_message_safe(self, update: Update, text: str, parse_mode: str = 'Markdown'):
        """Безопасная отправка сообщения с автоматическим разбиением на части"""
        if len(text) <= 4000:
            await update.message.reply_text(text, parse_mode=parse_mode)
        else:
            await self._send_long_text(update, text, parse_mode)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""🧠 Okama Financial Brain

Привет, {user_name}! Я помогу с анализом рынков и портфелей.

**Что умею:**
- Анализ одного актива с графиками цен
- Сравнение нескольких активов
- Анализ портфеля (веса, риск/доходность, efficient frontier)
- Макро/товары/валюты
- Анализ инфляции
- AI‑объяснения и рекомендации

**Как обращаться (просто текстом):**
- "Проанализируй Apple"
- "Сравни золото и нефть"
- "Портфель VOO.US 60% и AGG.US 40%"
- "Инфляция в США за 5 лет"
- "Сравни S&P 500 и NASDAQ в рублях"

**Команды:**
/help — список команд
/asset [тикер] [период] — информация об активе с графиком цен
/chart [тикер] [период] — график цен актива
/price [тикер] — текущая цена
/dividends [тикер] — дивиденды
/chat [вопрос] — вопрос AI‑советнику
/test [тикер] — тест Okama
/testai — тест YandexGPT
/test_split — тест разбивки длинных сообщений

**Примеры запросов:**
• "Проанализируй SBER.MOEX за 2 года"
• "Сравни VOO.US и QQQ.US"
• "Портфель: 70% VOO.US, 20% AGG.US, 10% GC.COMM"
• "Инфляция в России за 10 лет"
• "Динамика нефти и золота в рублях"

Начните с простого запроса или используйте /help для подробностей!"""

        await self._send_message_safe(update, welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🧠 **Okama Financial Brain - Справка**

**Основные команды:**
/start — приветствие и краткая справка
/help — эта справка
/asset [тикер] [период] — информация об активе с графиком цен
/chart [тикер] [период] — график цен актива
/price [тикер] — текущая цена
/dividends [тикер] — дивиденды
/chat [вопрос] — вопрос AI‑советнику
/test [тикер] — тест Okama
/testai — тест YandexGPT
/test_split — тест разбивки длинных сообщений

**Поддерживаемые форматы тикеров:**
• **US акции:** AAPL.US, VOO.US, SPY.US, QQQ.US
• **MOEX:** SBER.MOEX, GAZP.MOEX, LKOH.MOEX
• **Индексы:** SPX.INDX, IXIC.INDX, RGBITR.INDX
• **Товары:** GC.COMM (золото), CL.COMM (нефть), SI.COMM (серебро)
• **Валюты:** EURUSD.FX, GBPUSD.FX, USDJPY.FX
• **LSE:** VOD.LSE, HSBA.LSE, BP.LSE

**Периоды анализа:**
• 1Y, 2Y, 5Y, 10Y, MAX
• По умолчанию: 10Y для акций, 5Y для макро

**Примеры запросов:**
• "Проанализируй Apple за 5 лет"
• "Сравни золото и нефть"
• "Портфель: 60% VOO.US, 30% AGG.US, 10% GC.COMM"
• "Инфляция в США за 10 лет"
• "Динамика SBER.MOEX в рублях"

**Особенности:**
✅ Автоматическое распознавание намерений
✅ Нормализация названий активов
✅ Построение аналитических отчетов
✅ Генерация графиков
✅ AI-выводы и рекомендации
✅ Поддержка конвертации валют
✅ Автоматическое разбиение длинных сообщений

**Поддержка:**
Если у вас возникли вопросы или проблемы, попробуйте:
1. Переформулировать запрос
2. Использовать более простые названия активов
3. Проверить доступность данных (MOEX может быть временно недоступен)"

        await self._send_message_safe(update, help_text)
    
    async def asset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /asset command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /asset AAPL.US или /asset SBER.MOEX")
            return
        
        symbol = context.args[0].upper()
        period = context.args[1] if len(context.args) > 1 else '10Y'
        
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol}...")
        
        try:
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await self._send_message_safe(update, f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Format asset info
            response = f"📊 **Информация об активе: {symbol}**\n\n"
            response += f"**Название:** {asset_info.get('name', 'N/A')}\n"
            response += f"**Страна:** {asset_info.get('country', 'N/A')}\n"
            response += f"**Биржа:** {asset_info.get('exchange', 'N/A')}\n"
            response += f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
            response += f"**Тип:** {asset_info.get('type', 'N/A')}\n"
            response += f"**ISIN:** {asset_info.get('isin', 'N/A')}\n"
            response += f"**Период данных:** {asset_info.get('period_length', 'N/A')}\n"
            
            if asset_info.get('current_price') is not None:
                response += f"**Текущая цена:** {asset_info['current_price']:.2f}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"**Годовая доходность:** {asset_info['annual_return']}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"**Общая доходность:** {asset_info['total_return']}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"**Волатильность:** {asset_info['volatility']}\n"
            
            await self._send_message_safe(update, response, parse_mode='Markdown')
            
            # Send chart if available
            if 'chart' in asset_info:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(asset_info['chart']),
                    caption=f"📊 График цен {symbol}"
                )
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении информации об активе: {str(e)}")
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /price AAPL.US или /price SBER.MOEX")
            return
        
        symbol = context.args[0].upper()
        
        await self._send_message_safe(update, f"💰 Получаю текущую цену {symbol}...")
        
        try:
            price_info = self.asset_service.get_asset_price(symbol)
            
            if 'error' in price_info:
                await self._send_message_safe(update, f"❌ Ошибка: {price_info['error']}")
                return
            
            response = f"💰 **Текущая цена {symbol}**\n\n"
            response += f"**Цена:** {price_info.get('price', 'N/A')}\n"
            response += f"**Валюта:** {price_info.get('currency', 'N/A')}\n"
            response += f"**Дата:** {price_info.get('date', 'N/A')}\n"
            
            await self._send_message_safe(update, response, parse_mode='Markdown')
            
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении цены: {str(e)}")
    
    async def dividends_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dividends command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /dividends AAPL.US или /dividends SBER.MOEX")
            return
        
        symbol = context.args[0].upper()
        
        await self._send_message_safe(update, f"💵 Получаю историю дивидендов {symbol}...")
        
        try:
            dividend_info = self.asset_service.get_asset_dividends(symbol)
            
            if 'error' in dividend_info:
                await self._send_message_safe(update, f"❌ Ошибка: {dividend_info['error']}")
                return
            
            response = f"💵 **Дивиденды {symbol}**\n\n"
            response += f"**Валюта:** {dividend_info.get('currency', 'N/A')}\n"
            response += f"**Количество периодов:** {dividend_info.get('total_periods', 'N/A')}\n\n"
            
            if dividend_info.get('dividends'):
                response += "**История дивидендов:**\n"
                dividends = dividend_info['dividends']
                # Show last 10 dividends
                sorted_dates = sorted(dividends.keys(), reverse=True)[:10]
                for date in sorted_dates:
                    amount = dividends[date]
                    response += f"• {date}: {amount:.2f}\n"
            
            await self._send_message_safe(update, response, parse_mode='Markdown')
            
            # Send chart if available
            if 'chart' in dividend_info:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(dividend_info['chart']),
                    caption=f"💵 График дивидендов {symbol}"
                )
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении дивидендов: {str(e)}")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер для тестирования. Пример: /test AAPL.US")
            return
        
        symbol = context.args[0].upper()
        
        await self._send_message_safe(update, f"🧪 Тестирую подключение к Okama для {symbol}...")
        
        try:
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await self._send_message_safe(update, f"❌ Тест не прошел: {asset_info['error']}")
                return
            
            await self._send_message_safe(update, 
                f"✅ Тест Okama прошел успешно!\n\n"
                f"**Актив:** {symbol}\n"
                f"**Название:** {asset_info.get('name', 'N/A')}\n"
                f"**Страна:** {asset_info.get('country', 'N/A')}\n"
                f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
                f"**Тип:** {asset_info.get('type', 'N/A')}")
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Тест не прошел: {str(e)}")
    
    async def testai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /testai command"""
        await self._send_message_safe(update, "🧪 Тестирую подключение к YandexGPT...")
        
        try:
            response = self.yandexgpt_service.get_response("Привет! Это тест подключения. Ответь кратко.")
            
            if response and response.strip():
                await self._send_message_safe(update, 
                    f"✅ Тест YandexGPT прошел успешно!\n\n"
                    f"**Ответ AI:**\n{response}")
            else:
                await self._send_message_safe(update, 
                    f"❌ Тест YandexGPT не прошел: {response}")
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Тест YandexGPT не прошел: {str(e)}")
    
    async def test_split_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test_split command - test message splitting functionality"""
        await self._send_message_safe(update, "📝 Тестирую разбивку длинных сообщений...")
        
        try:
            # Create a very long message to test splitting
            long_message = "🧪 **Тест разбивки длинных сообщений**\n\n"
            long_message += "Это сообщение специально создано для тестирования механизма автоматического разбиения длинных сообщений на части.\n\n"
            
            # Add many paragraphs to make it long
            for i in range(1, 101):
                long_message += f"**Параграф {i}:**\n"
                long_message += f"Это тестовый параграф номер {i} для проверки работы механизма разбиения сообщений. "
                long_message += f"Каждый параграф содержит достаточно текста, чтобы в совокупности превысить лимит Telegram в 4000 символов. "
                long_message += f"Механизм должен автоматически разбить это сообщение на несколько частей и отправить их последовательно.\n\n"
            
            long_message += "**Конец тестового сообщения**\n\n"
            long_message += "Если вы видите это сообщение разбитым на несколько частей, значит механизм работает корректно! 🎉"
            
            await self._send_message_safe(update, long_message)
            
        except Exception as e:
            await self._send_message_safe(update, f"❌ Тест разбивки не прошел: {str(e)}")
    
    async def _handle_chat(self, update: Update, user_message: str):
        """Handle AI chat requests"""
        try:
            await self._send_message_safe(update, "🤔 Thinking...")
            
            response = self.yandexgpt_service.get_response(user_message)
            
            if response and response.strip():
                await self._send_message_safe(update, response, parse_mode='Markdown')
            else:
                await self._send_message_safe(update, "❌ Не удалось получить ответ от AI. Попробуйте переформулировать вопрос.")
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Error getting AI response: {str(e)}")
    
    async def _get_asset_info_with_chart(self, update: Update, symbol: str, period: str = '10Y'):
        """Get asset info with price history chart"""
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol} и историю цен...")
        
        try:
            # Get asset info
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await self._send_message_safe(update, f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Get price history
            price_history = self.asset_service.get_asset_price_history(symbol, period)
            
            if 'error' in price_history:
                await self._send_message_safe(update, f"❌ Ошибка при получении истории цен: {price_history['error']}")
                return
            
            # Format response
            response = f"📊 **Анализ актива: {symbol}**\n\n"
            response += f"**Название:** {asset_info.get('name', 'N/A')}\n"
            response += f"**Страна:** {asset_info.get('country', 'N/A')}\n"
            response += f"**Биржа:** {asset_info.get('exchange', 'N/A')}\n"
            response += f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
            response += f"**Тип:** {asset_info.get('type', 'N/A')}\n"
            response += f"**Период анализа:** {period}\n"
            
            if asset_info.get('current_price') is not None:
                response += f"**Текущая цена:** {asset_info['current_price']:.2f}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"**Годовая доходность:** {asset_info['annual_return']}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"**Общая доходность:** {asset_info['total_return']}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"**Волатильность:** {asset_info['volatility']}\n"
            
            response += "\n**📈 История цен:**\n"
            if price_history.get('data') is not None:
                data = price_history['data']
                if hasattr(data, 'tail'):
                    recent_data = data.tail(5)
                    response += "Последние 5 значений:\n"
                    for date, price in recent_data.items():
                        response += f"• {date}: {price:.2f}\n"
                else:
                    response += "Данные доступны, но формат не поддерживается для отображения\n"
            else:
                response += "Данные по ценам недоступны\n"
            
            await self._send_message_safe(update, response, parse_mode='Markdown')
            
            # Send charts
            charts = price_history.get('charts', [])
            if charts:
                for i, img_bytes in enumerate(charts):
                    try:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=io.BytesIO(img_bytes),
                            caption=f"📊 График {i+1}: {symbol}"
                        )
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error sending chart {i+1}: {error_msg}")
                        await self._send_message_safe(update, f"❌ Ошибка при отправке графика {i+1}: {error_msg}")
            else:
                await self._send_message_safe(update, "⚠️ Не удалось создать графики цен")
            
            # Get AI analysis if available
            try:
                await self._send_message_safe(update, "🧠 Получаю AI анализ графиков...")
                ai_response = self.yandexgpt_service.get_response(
                    f"Проанализируй график цен актива {symbol} за период {period}. "
                    f"Опиши основные тренды, волатильность и дай краткие рекомендации."
                )
                
                if ai_response and ai_response.strip():
                    await self._send_message_safe(update, 
                        f"🤖 **AI Анализ графика {symbol}:**\n\n{ai_response}")
                else:
                    await self._send_message_safe(update, "❌ Не удалось получить AI анализ графика")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error getting AI analysis: {error_msg}")
                await self._send_message_safe(update, f"❌ Ошибка при получении AI анализа: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in _get_asset_info_with_chart: {error_msg}")
            await self._send_message_safe(update, f"❌ Ошибка при получении информации: {error_msg}")
    
    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chart command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер и период. Пример: /chart AAPL.US 5Y или /chart SBER.MOEX 2Y")
            return
        
        symbol = context.args[0].upper()
        period = context.args[1] if len(context.args) > 1 else '10Y'
        
        await self._send_message_safe(update, f"📈 Получаю графики цен для {symbol} за период {period}...")
        
        try:
            price_history = self.asset_service.get_asset_price_history(symbol, period)
            
            if 'error' in price_history:
                await self._send_message_safe(update, f"❌ Ошибка: {price_history['error']}")
                return
            
            # Send charts
            charts = price_history.get('charts', [])
            if charts:
                for i, img_bytes in enumerate(charts):
                    try:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=io.BytesIO(img_bytes),
                            caption=f"📈 График {i+1}: {symbol} ({period})"
                        )
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error sending chart {i+1}: {error_msg}")
                        await self._send_message_safe(update, f"❌ Ошибка при отправке графика {i+1}: {error_msg}")
            else:
                await self._send_message_safe(update, "⚠️ Не удалось создать графики цен")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting charts: {error_msg}")
            await self._send_message_safe(update, f"❌ Ошибка при получении графиков: {error_msg}")
    
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
            logger.exception(f"Error in Enhanced Financial Brain processing: {e}")
            
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
                    await self._send_message_safe(update, "Не удалось распознать актив. Укажите тикер, например AAPL.US, SBER.MOEX, GC.COMM")
                    return
                # Use new enhanced asset info with chart for single assets
                await self._get_asset_info_with_chart(update, valid_tickers[0], '10Y')
                return

            elif parsed.intent == 'asset_compare' or (parsed.intent == 'macro'):
                if len(valid_tickers) < 2:
                    # If only one valid, treat as single asset with chart
                    if len(valid_tickers) == 1:
                        await self._get_asset_info_with_chart(update, valid_tickers[0], '10Y')
                        return
                    else:
                        await self._send_message_safe(update, "Для сравнения укажите как минимум два актива.")
                        return
                else:
                    result = self.okama_handler.get_multiple_assets(valid_tickers)
                    report_text, images = self.report_builder.build_multi_asset_report(result)
                    ai_summary = self.analysis_engine.summarize('asset_compare', {"metrics": result.get("metrics", {}), "correlation": result.get("correlation", {})}, user_message)

            elif parsed.intent == 'portfolio':
                if len(valid_tickers) < 2:
                    await self._send_message_safe(update, "Для анализа портфеля укажите как минимум два актива.")
                    return
                result = self.okama_handler.get_portfolio(valid_tickers)
                report_text, images = self.report_builder.build_portfolio_report(result)
                ai_summary = self.analysis_engine.summarize('portfolio', {"metrics": result.get("metrics", {})}, user_message)

            elif parsed.intent == 'inflation_data':
                # Получаем параметры для инфляции
                country = getattr(parsed, 'country', 'US')
                period = getattr(parsed, 'period', '5Y')
                result = self.okama_handler.get_inflation(country=country, period=period)
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
            logger.exception(f"Error in fallback message handling: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Попробуйте переформулировать вопрос или используйте /help для доступных команд. "
                "Если вы запрашиваете данные по MOEX (например, SBER.MOEX), они могут быть временно недоступны."
            )

    async def _send_long_text(self, update: Update, text: str, parse_mode: str = 'Markdown'):
        """Send long text by splitting it into multiple messages if needed"""
        # Base Telegram hard limit is 4096 chars for text messages.
        # We use configured limit if available and keep a safety margin
        # to account for continuation prefixes and potential formatting.
        try:
            max_length = getattr(Config, 'MAX_MESSAGE_LENGTH', 4096)
        except Exception:
            max_length = 4096
        safety_margin = 64
        per_part_limit = max_length - safety_margin
        if per_part_limit < 100:
            per_part_limit = max(100, max_length - 10)
        
        self.logger.info(f"_send_long_text called with text length: {len(text)}")
        
        if len(text) <= max_length:
            # Single message is fine
            self.logger.info(f"Text fits in single message, sending directly")
            try:
                await update.message.reply_text(text, parse_mode=parse_mode)
            except Exception as e:
                # Fallback if Markdown parsing fails
                self.logger.warning(f"Failed to send single message with parse_mode={parse_mode}: {e}. Retrying without parse mode.")
                await update.message.reply_text(text)
        else:
            # Split into multiple messages
            self.logger.info(f"Text too long, splitting into parts")
            parts = self._split_text_into_parts(text, per_part_limit)
            self.logger.info(f"Split into {len(parts)} parts with lengths: {[len(part) for part in parts]}")
            
            for i, part in enumerate(parts, 1):
                if i == 1:
                    # First part
                    self.logger.info(f"Sending part {i}/{len(parts)} (length: {len(part)})")
                    try:
                        await update.message.reply_text(part, parse_mode=parse_mode)
                    except Exception as e:
                        self.logger.warning(f"Failed to send part {i} with parse_mode={parse_mode}: {e}. Retrying without parse mode.")
                        await update.message.reply_text(part)
                else:
                    # Subsequent parts
                    continuation_prefix = f"📄 Продолжение ({i}/{len(parts)}):\n\n"
                    continuation_text = f"{continuation_prefix}{part}"
                    self.logger.info(f"Sending continuation part {i}/{len(parts)} (total length: {len(continuation_text)})")
                    # Ensure we never exceed the hard max length
                    if len(continuation_text) > max_length:
                        # Further split this part conservatively
                        sub_parts = self._split_text_into_parts(part, per_part_limit - len(continuation_prefix))
                        self.logger.info(f"Continuation part {i} too long after prefix, further split into {len(sub_parts)} sub-parts")
                        for j, sub in enumerate(sub_parts, 1):
                            sub_prefix = f"📄 Продолжение ({i}.{j}/{len(parts)}):\n\n"
                            sub_text = f"{sub_prefix}{sub}"
                            try:
                                await update.message.reply_text(sub_text, parse_mode=parse_mode)
                            except Exception as e:
                                self.logger.warning(f"Failed to send sub-part {i}.{j} with parse_mode={parse_mode}: {e}. Retrying without parse mode.")
                                await update.message.reply_text(sub_text)
                    else:
                        try:
                            await update.message.reply_text(continuation_text, parse_mode=parse_mode)
                        except Exception as e:
                            self.logger.warning(f"Failed to send continuation part {i} with parse_mode={parse_mode}: {e}. Retrying without parse mode.")
                            await update.message.reply_text(continuation_text)
    
    def _split_text_into_parts(self, text: str, max_length: int) -> List[str]:
        """Split text into parts that fit within max_length"""
        parts = []
        current_part = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max_length
            if len(current_part) + len(paragraph) + 2 > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = paragraph
                else:
                    # Single paragraph is too long, split by sentences
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 2 > max_length:
                            if current_part:
                                parts.append(current_part.strip())
                                current_part = sentence
                            else:
                                # Single sentence is too long, split by words
                                words = sentence.split(' ')
                                for word in words:
                                    if len(current_part) + len(word) + 1 > max_length:
                                        if current_part:
                                            parts.append(current_part.strip())
                                            current_part = word
                                        else:
                                            # Single word is too long, truncate
                                            parts.append(word[:max_length-3] + "...")
                                    else:
                                        current_part += " " + word if current_part else word
                        else:
                            current_part += ". " + sentence if current_part else sentence
            else:
                current_part += "\n\n" + paragraph if current_part else paragraph
        
        # Add the last part
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts

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
        application.add_handler(CommandHandler("chart", self.chart_command))
        application.add_handler(CommandHandler("chat", self.chat_command))
        application.add_handler(CommandHandler("test", self.test_command))
        application.add_handler(CommandHandler("testai", self.testai_command))
        application.add_handler(CommandHandler("test_split", self.test_split_command))
        
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
