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

**Периоды для графиков:** 1Y (год), 2Y (2 года), 5Y (5 лет), MAX (весь период)

Также можно просто прислать тикер (например, AAPL.US) — я пойму и покажу график.

**Популярные тикеры:**
- ETF: VOO.US, SPY.US, QQQ.US
- Индексы: SPX.INDX, RTSI.INDX, DAX.INDX
- Товары: XAU.COMM, BRENT.COMM, SILVER.COMM
- Валюты: EURUSD.FX, GBPUSD.FX
- Акции: AAPL.US, TSLA.US, SBER.MOEX

Готовы начать? 🚀"""
        
        keyboard = [
            [InlineKeyboardButton("🧠 Финансовый анализ", callback_data="analysis_help")],
            [InlineKeyboardButton("📊 Анализ портфеля", callback_data="portfolio_help")],
            [InlineKeyboardButton("⚖️ Сравнение активов", callback_data="compare_help")],
            [InlineKeyboardButton("💬 AI-советник", callback_data="chat_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🧠 **Okama Financial Brain - Помощь**

🚀 **Основные команды:**
/asset [symbol] [period] - Полная информация об активе с графиком цен
/price [symbol] - Текущая цена актива
/chart [symbol] [period] - График цен актива
/dividends [symbol] - История дивидендов
/test [symbol] - Тест подключения к Okama API
/testai - Тест подключения к YandexGPT API

💬 **AI-советник:**
/chat [question] - Получить финансовый совет от AI

📊 **Примеры команд:**
• /asset VOO.US 1Y
• /chart SPY.US 2Y
• /price AGG.US
• /dividends VOO.US
• /test VOO.US

📈 **Доступные периоды для графиков:**
• 1Y - 1 год (по умолчанию)
• 2Y - 2 года
• 5Y - 5 лет
• MAX - весь доступный период"""
        
        await update.message.reply_text(help_text)
    
    async def asset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /asset command"""
        if not context.args:
            await update.message.reply_text(
                "📊 Информация об активе и история цен\n\n"
                "Пожалуйста, укажите символ:\n"
                "/asset VOO.US\n\n"
                "Доступные периоды для графика:\n"
                "/asset VOO.US 1Y (1 год)\n"
                "/asset VOO.US 2Y (2 года)\n"
                "/asset VOO.US 5Y (5 лет)\n"
                "/asset VOO.US MAX (весь период)\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        
        # Check if period is specified
        period = '1Y'  # Default period
        if len(context.args) > 1:
            period = context.args[1].upper()
        
        await self._get_asset_info_with_chart(update, symbol, period)
    
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
    
    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chart command"""
        if not context.args:
            await update.message.reply_text(
                "📈 График цен актива\n\n"
                "Пожалуйста, укажите символ и период:\n"
                "/chart VOO.US 1Y\n\n"
                "Доступные периоды:\n"
                "/chart VOO.US 1Y (1 год)\n"
                "/chart VOO.US 2Y (2 года)\n"
                "/chart VOO.US 5Y (5 лет)\n"
                "/chart VOO.US MAX (весь период)\n\n"
                "Или просто отправьте мне символ напрямую!"
            )
            return
        
        symbol = context.args[0].upper()
        
        # Check if period is specified
        period = '1Y'  # Default period
        if len(context.args) > 1:
            period = context.args[1].upper()
        
        await self._get_asset_price_chart(update, symbol, period)
    
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
            response += f"**Длина периода:** {asset_info.get('period_length', 'N/A')}\n\n"
            
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
            # Send chart if provided
            chart_bytes = asset_info.get('chart')
            if chart_bytes:
                try:
                    await update.message.reply_photo(
                        photo=io.BytesIO(chart_bytes),
                        caption="📈 Месячная динамика цены"
                    )
                except Exception:
                    pass
            
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
            price_value = price_info.get('price', 'N/A')
            currency = price_info.get('currency', '')
            # Format numeric price with up to 6 significant digits
            if isinstance(price_value, (int, float)):
                price_str = f"{price_value:.6g}"
            else:
                price_str = str(price_value)
            response += f"**Текущая цена:** {price_str} {currency}\n"
            response += f"**Время:** {price_info.get('timestamp', 'N/A')}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            # Send chart if provided
            chart_bytes = price_info.get('chart')
            if chart_bytes:
                try:
                    await update.message.reply_photo(
                        photo=io.BytesIO(chart_bytes),
                        caption="📈 Историческая цена"
                    )
                except Exception:
                    pass
            
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
            response += f"**Количество выплат:** {dividend_info.get('total_periods', 'N/A')}\n\n"
            
            # Add recent dividends
            dividends = dividend_info.get('dividends', {})
            if dividends:
                response += "**Последние дивиденды:**\n"
                for date, amount in list(dividends.items())[-5:]:  # Last 5
                    response += f"• {date}: {amount:.4f}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            # Send chart if provided
            chart_bytes = dividend_info.get('chart')
            if chart_bytes:
                try:
                    await update.message.reply_photo(
                        photo=io.BytesIO(chart_bytes),
                        caption="💵 Дивиденды"
                    )
                except Exception:
                    pass
            
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
                    await update.message.reply_text("Не удалось распознать актив. Укажите тикер, например AAPL.US, SBER.MOEX, GC.COMM")
                    return
                # Use new enhanced asset info with chart for single assets
                await self._get_asset_info_with_chart(update, valid_tickers[0], '1Y')
                return

            elif parsed.intent == 'asset_compare' or (parsed.intent == 'macro'):
                if len(valid_tickers) < 2:
                    # If only one valid, treat as single asset with chart
                    if len(valid_tickers) == 1:
                        await self._get_asset_info_with_chart(update, valid_tickers[0], '1Y')
                        return
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
    
    async def _get_asset_info_with_chart(self, update: Update, symbol: str, period: str = '1Y'):
        """Get comprehensive asset information with price history charts and AI analysis"""
        try:
            await update.message.reply_text(f"📊 Получаю информацию об активе {symbol} и историю цен...")
            
            # Get basic asset info
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
            
            # Get price history and charts
            price_history = self.asset_service.get_asset_price_history(symbol, period)
            
            if 'error' in price_history:
                # If we can't get the charts, still show basic info
                await update.message.reply_text(
                    f"⚠️ Удалось получить информацию об активе, но не удалось построить график: {price_history['error']}"
                )
                await self._get_asset_info(update, symbol)
                return
            
            # Build response message with enhanced information
            response = f"📊 **Информация об активе {symbol}**\n\n"
            response += f"**Название:** {asset_info.get('name', 'N/A')}\n"
            response += f"**Страна:** {asset_info.get('country', 'N/A')}\n"
            response += f"**Биржа:** {asset_info.get('exchange', 'N/A')}\n"
            response += f"**Валюта:** {asset_info.get('currency', 'N/A')}\n"
            response += f"**Тип:** {asset_info.get('type', 'N/A')}\n"
            response += f"**ISIN:** {asset_info.get('isin', 'N/A')}\n"
            response += f"**Первый день:** {asset_info.get('first_date', 'N/A')}\n"
            response += f"**Последний день:** {asset_info.get('last_date', 'N/A')}\n"
            response += f"**Длина периода:** {asset_info.get('period_length', 'N/A')}\n\n"
            
            # Add performance metrics
            if asset_info.get('current_price'):
                response += f"**Текущая цена:** {asset_info.get('current_price')} {asset_info.get('currency', '')}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"**Годовая доходность:** {asset_info.get('annual_return')}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"**Общая доходность:** {asset_info.get('total_return')}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"**Волатильность:** {asset_info.get('volatility')}\n"
            
            # Add price history statistics for each chart type
            charts_info = price_history.get('charts', {})
            price_data_info = price_history.get('price_data_info', {})
            
            if 'adj_close' in charts_info:
                adj_info = price_data_info.get('adj_close', {})
                response += f"\n📈 **Дневные цены (скорректированные):**\n"
                response += f"**Текущая цена:** {adj_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Начальная цена:** {adj_info.get('start_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Мин/Макс:** {adj_info.get('min_price', 'N/A')} / {adj_info.get('max_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Период:** {adj_info.get('start_date', 'N/A')} - {adj_info.get('end_date', 'N/A')}\n"
                response += f"**Точки данных:** {adj_info.get('data_points', 'N/A')}\n"
            
            if 'close_monthly' in charts_info:
                monthly_info = price_data_info.get('close_monthly', {})
                response += f"\n📊 **Месячные цены:**\n"
                response += f"**Текущая цена:** {monthly_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Начальная цена:** {monthly_info.get('start_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Мин/Макс:** {monthly_info.get('min_price', 'N/A')} / {monthly_info.get('max_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Период:** {monthly_info.get('start_date', 'N/A')} - {monthly_info.get('end_date', 'N/A')}\n"
                response += f"**Точки данных:** {monthly_info.get('data_points', 'N/A')}\n"
            
            if 'fallback' in charts_info:
                fallback_info = price_data_info.get('fallback', {})
                response += f"\n📊 **История цен:**\n"
                response += f"**Текущая цена:** {fallback_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Начальная цена:** {fallback_info.get('start_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Мин/Макс:** {fallback_info.get('min_price', 'N/A')} / {fallback_info.get('max_price', 'N/A')} {price_history.get('currency', '')}\n"
                response += f"**Период:** {fallback_info.get('start_date', 'N/A')} - {fallback_info.get('end_date', 'N/A')}\n"
                response += f"**Точки данных:** {fallback_info.get('data_points', 'N/A')}\n"
            
            # Send text response first
            await update.message.reply_text(response, parse_mode='Markdown')
            
            # Send charts and get AI analysis
            await self._send_charts_with_ai_analysis(update, symbol, period, charts_info, price_data_info)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in _get_asset_info_with_chart: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка при получении информации: {error_msg}")
    
    async def _send_charts_with_ai_analysis(self, update: Update, symbol: str, period: str, charts: Dict, price_data_info: Dict):
        """Send charts and get AI analysis from YandexGPT"""
        try:
            # Send charts first
            charts_sent = []
            
            if 'adj_close' in charts:
                caption = f"📈 Дневные цены (скорректированные): {symbol} за период {period}"
                await update.message.reply_photo(
                    photo=charts['adj_close'],
                    caption=caption
                )
                charts_sent.append('adj_close')
            
            if 'close_monthly' in charts:
                caption = f"📊 Месячные цены: {symbol} за период {period}"
                await update.message.reply_photo(
                    photo=charts['close_monthly'],
                    caption=caption
                )
                charts_sent.append('close_monthly')
            
            if 'fallback' in charts:
                caption = f"📊 История цен: {symbol} за период {period}"
                await update.message.reply_photo(
                    photo=charts['fallback'],
                    caption=caption
                )
                charts_sent.append('fallback')
            
            # Get AI analysis if we have charts
            if charts_sent:
                await self._get_ai_analysis_for_charts(update, symbol, period, charts_sent, price_data_info)
            else:
                await update.message.reply_text("⚠️ Не удалось создать графики цен")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in _send_charts_with_ai_analysis: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка при отправке графиков: {error_msg}")
    
    async def _get_ai_analysis_for_charts(self, update: Update, symbol: str, period: str, charts_sent: List[str], price_data_info: Dict):
        """Get AI analysis for the charts from YandexGPT"""
        try:
            await update.message.reply_text("🧠 Получаю AI анализ графиков...")
            
            # Prepare data for AI analysis
            analysis_data = {
                'symbol': symbol,
                'period': period,
                'charts_available': charts_sent,
                'price_data': price_data_info
            }
            
            # Create analysis prompt
            prompt = self._create_chart_analysis_prompt(analysis_data)
            
            # Get AI response
            ai_response = await self._get_yandexgpt_analysis(prompt)
            
            if ai_response:
                await update.message.reply_text(
                    f"🧠 **AI анализ {symbol}**\n\n{ai_response}",
                    parse_mode='Markdown'
                )
            else:
                # Fallback: provide basic analysis based on available data
                fallback_analysis = self._create_fallback_analysis(analysis_data)
                await update.message.reply_text(
                    f"🧠 **Анализ {symbol}** (базовый)\n\n{fallback_analysis}",
                    parse_mode='Markdown'
                )
                await update.message.reply_text(
                    "⚠️ AI анализ недоступен. Показан базовый анализ на основе данных."
                )
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error in _get_ai_analysis_for_charts: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка при получении AI анализа: {error_msg}")
    
    def _create_chart_analysis_prompt(self, analysis_data: Dict) -> str:
        """Create a prompt for chart analysis"""
        symbol = analysis_data['symbol']
        period = analysis_data['period']
        charts_available = analysis_data['charts_available']
        price_data = analysis_data['price_data']
        
        prompt = f"""Проанализируй графики цен для актива {symbol} за период {period}.

Доступные графики: {', '.join(charts_available)}

Данные по ценам:"""

        for chart_type, info in price_data.items():
            if chart_type == 'adj_close':
                prompt += f"\n\n📈 Дневные цены (скорректированные):"
            elif chart_type == 'close_monthly':
                prompt += f"\n\n📊 Месячные цены:"
            else:
                prompt += f"\n\n📊 История цен:"
            
            prompt += f"\n- Текущая цена: {info.get('current_price', 'N/A')}"
            prompt += f"\n- Начальная цена: {info.get('start_price', 'N/A')}"
            prompt += f"\n- Минимальная цена: {info.get('min_price', 'N/A')}"
            prompt += f"\n- Максимальная цена: {info.get('max_price', 'N/A')}"
            prompt += f"\n- Период: {info.get('start_date', 'N/A')} - {info.get('end_date', 'N/A')}"
            prompt += f"\n- Количество точек данных: {info.get('data_points', 'N/A')}"
        
        prompt += f"""

Пожалуйста, предоставь:
1. Краткий анализ динамики цен
2. Основные тренды и паттерны
3. Ключевые уровни поддержки и сопротивления
4. Оценку волатильности
5. Краткосрочные и долгосрочные перспективы
6. Рекомендации для инвесторов

Анализ должен быть на русском языке, профессиональным, но понятным для обычных инвесторов."""

        return prompt
    
    async def _get_yandexgpt_analysis(self, prompt: str) -> Optional[str]:
        """Get AI analysis from YandexGPT"""
        try:
            self.logger.info(f"Requesting YandexGPT analysis for prompt length: {len(prompt)}")
            
            # Use the existing YandexGPT service
            response = await self.yandexgpt_service.get_response(prompt)
            
            if response:
                self.logger.info(f"YandexGPT response received, length: {len(response)}")
                return response
            else:
                self.logger.warning("YandexGPT returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting YandexGPT analysis: {e}")
            self.logger.exception("Full traceback:")
            return None

    def _create_fallback_analysis(self, analysis_data: Dict) -> str:
        """Create a basic fallback analysis if YandexGPT is not available"""
        symbol = analysis_data['symbol']
        period = analysis_data['period']
        charts_available = analysis_data['charts_available']
        price_data = analysis_data['price_data']

        fallback_text = f"🧠 **Анализ {symbol}** (базовый)\n\n"
        fallback_text += f"**Период:** {period}\n"
        fallback_text += f"**Доступные графики:** {', '.join(charts_available)}\n\n"

        if 'adj_close' in price_data:
            adj_info = price_data['adj_close']
            fallback_text += f"📈 **Дневные цены (скорректированные):**\n"
            fallback_text += f"Текущая цена: {adj_info.get('current_price', 'N/A')}\n"
            fallback_text += f"Начальная цена: {adj_info.get('start_price', 'N/A')}\n"
            fallback_text += f"Мин/Макс: {adj_info.get('min_price', 'N/A')} / {adj_info.get('max_price', 'N/A')}\n"
            fallback_text += f"Период: {adj_info.get('start_date', 'N/A')} - {adj_info.get('end_date', 'N/A')}\n"
            fallback_text += f"Точки данных: {adj_info.get('data_points', 'N/A')}\n"

        if 'close_monthly' in price_data:
            monthly_info = price_data['close_monthly']
            fallback_text += f"\n📊 **Месячные цены:**\n"
            fallback_text += f"Текущая цена: {monthly_info.get('current_price', 'N/A')}\n"
            fallback_text += f"Начальная цена: {monthly_info.get('start_price', 'N/A')}\n"
            fallback_text += f"Мин/Макс: {monthly_info.get('min_price', 'N/A')} / {monthly_info.get('max_price', 'N/A')}\n"
            fallback_text += f"Период: {monthly_info.get('start_date', 'N/A')} - {monthly_info.get('end_date', 'N/A')}\n"
            fallback_text += f"Точки данных: {monthly_info.get('data_points', 'N/A')}\n"

        if 'fallback' in price_data:
            fallback_info = price_data['fallback']
            fallback_text += f"\n📊 **История цен:**\n"
            fallback_text += f"Текущая цена: {fallback_info.get('current_price', 'N/A')}\n"
            fallback_text += f"Начальная цена: {fallback_info.get('start_price', 'N/A')}\n"
            fallback_text += f"Мин/Макс: {fallback_info.get('min_price', 'N/A')} / {fallback_info.get('max_price', 'N/A')}\n"
            fallback_text += f"Период: {fallback_info.get('start_date', 'N/A')} - {fallback_info.get('end_date', 'N/A')}\n"
            fallback_text += f"Точки данных: {fallback_info.get('data_points', 'N/A')}\n"

        fallback_text += "\n⚠️ AI анализ недоступен. Показан базовый анализ на основе данных."
        return fallback_text

    async def _get_asset_price_chart(self, update: Update, symbol: str, period: str = '1Y'):
        """Get only the price charts for an asset"""
        try:
            await update.message.reply_text(f"📈 Получаю графики цен для {symbol} за период {period}...")
            
            # Get price history and charts
            price_history = self.asset_service.get_asset_price_history(symbol, period)
            
            if 'error' in price_history:
                await update.message.reply_text(f"❌ Ошибка: {price_history['error']}")
                return
            
            # Send charts
            charts = price_history.get('charts', {})
            price_data_info = price_history.get('price_data_info', {})
            
            charts_sent = []
            
            if 'adj_close' in charts:
                caption = f"📈 Дневные цены (скорректированные): {symbol} за период {period}\n\n"
                adj_info = price_data_info.get('adj_close', {})
                caption += f"Текущая цена: {adj_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                caption += f"Период: {adj_info.get('start_date', 'N/A')} - {adj_info.get('end_date', 'N/A')}"
                
                await update.message.reply_photo(
                    photo=charts['adj_close'],
                    caption=caption
                )
                charts_sent.append('adj_close')
            
            if 'close_monthly' in charts:
                caption = f"📊 Месячные цены: {symbol} за период {period}\n\n"
                monthly_info = price_data_info.get('close_monthly', {})
                caption += f"Текущая цена: {monthly_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                caption += f"Период: {monthly_info.get('start_date', 'N/A')} - {monthly_info.get('end_date', 'N/A')}"
                
                await update.message.reply_photo(
                    photo=charts['close_monthly'],
                    caption=caption
                )
                charts_sent.append('close_monthly')
            
            if 'fallback' in charts:
                caption = f"📊 История цен: {symbol} за период {period}\n\n"
                fallback_info = price_data_info.get('fallback', {})
                caption += f"Текущая цена: {fallback_info.get('current_price', 'N/A')} {price_history.get('currency', '')}\n"
                caption += f"Период: {fallback_info.get('start_date', 'N/A')} - {fallback_info.get('end_date', 'N/A')}"
                
                await update.message.reply_photo(
                    photo=charts['fallback'],
                    caption=caption
                )
                charts_sent.append('fallback')
            
            if not charts_sent:
                await update.message.reply_text("⚠️ Не удалось создать графики цен")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in _get_asset_price_chart: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка при получении графиков: {error_msg}")

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
