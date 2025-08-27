import sys
import logging
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import io
from typing import Dict, List, Optional, Any
from datetime import datetime

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
        
    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Получить контекст пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'last_assets': [],  # Последние анализируемые активы
                'last_analysis_type': None,  # Тип последнего анализа
                'last_period': None,  # Последний период анализа
                'conversation_history': [],  # История разговора
                'preferences': {}  # Предпочтения пользователя
            }
        return self.user_sessions[user_id]
    
    def _update_user_context(self, user_id: int, **kwargs):
        """Обновить контекст пользователя"""
        context = self._get_user_context(user_id)
        context.update(kwargs)
        
        # Ограничиваем историю разговора
        if 'conversation_history' in context and len(context['conversation_history']) > 10:
            context['conversation_history'] = context['conversation_history'][-10:]
    
    def _add_to_conversation_history(self, user_id: int, message: str, response: str):
        """Добавить сообщение в историю разговора"""
        context = self._get_user_context(user_id)
        context['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response[:200]  # Ограничиваем длину ответа
        })
    
    def _get_context_summary(self, user_id: int) -> str:
        """Получить краткое резюме контекста пользователя"""
        context = self._get_user_context(user_id)
        summary = []
        
        if context['last_assets']:
            summary.append(f"Последние активы: {', '.join(context['last_assets'][-3:])}")
        
        if context['last_analysis_type']:
            summary.append(f"Последний анализ: {context['last_analysis_type']}")
        
        if context['last_period']:
            summary.append(f"Период: {context['last_period']}")
        
        return "; ".join(summary) if summary else "Новый пользователь"
    
    async def _send_message_safe(self, update: Update, text: str, parse_mode: str = 'MarkdownV2'):
        """Безопасная отправка сообщения с автоматическим разбиением на части"""
        try:
            # Проверяем, что text действительно является строкой
            if not isinstance(text, str):
                self.logger.warning(f"_send_message_safe received non-string data: {type(text)}")
                text = str(text)
            
            # Экранируем специальные символы для MarkdownV2
            if parse_mode == 'MarkdownV2':
                text = self._escape_markdown_v2(text)
            
            # Проверяем длину строки
            if len(text) <= 4000:
                await update.message.reply_text(text, parse_mode=parse_mode)
            else:
                await self._send_long_text(update, text, parse_mode)
        except Exception as e:
            self.logger.error(f"Error in _send_message_safe: {e}")
            # Fallback: попробуем отправить как обычный текст
            try:
                await update.message.reply_text(f"Ошибка форматирования: {str(text)[:1000]}...")
            except:
                await update.message.reply_text("Произошла ошибка при отправке сообщения")
    
    def _escape_markdown_v2(self, text: str) -> str:
        """Экранирование специальных символов для MarkdownV2"""
        # Убираем экранирование, возвращаем текст как есть
        return text
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with full help"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""🧠 Okama Financial Brain - Полная справка

Привет, {user_name}! Я помогу с анализом рынков и портфелей.

Что умею:
• Анализ одного актива с графиками цен
• Сравнение нескольких активов
• Анализ портфеля (веса, риск/доходность, efficient frontier)
• Макро/товары/валюты
• Анализ инфляции
• Объяснения и рекомендации

Основные команды:
/start — эта справка
/asset [тикер] [период] — базовая информация об активе с графиком и анализом

Поддерживаемые форматы тикеров:
• US акции: AAPL.US, VOO.US, SPY.US, QQQ.US
• MOEX: SBER.MOEX, GAZP.MOEX, LKOH.MOEX
• Индексы: SPX.INDX, IXIC.INDX, RGBITR.INDX
• Товары: GC.COMM (золото), CL.COMM (нефть), SI.COMM (серебро)
• Валюты: EURUSD.FX, GBPUSD.FX, USDJPY.FX
• LSE: VOD.LSE, HSBA.LSE, BP.LSE

Периоды анализа:
• 1Y, 2Y, 5Y, 10Y, MAX
• По умолчанию: 10Y для акций, 5Y для макро

Как обращаться (просто текстом):
• "Проанализируй Apple"
• "Сравни золото и нефть"
• "Портфель VOO.US 60% и AGG.US 40%"
• "Инфляция в США за 5 лет"
• "Сравни S&P 500 и NASDAQ в рублях"

Примеры запросов:
• "Проанализируй SBER.MOEX за 2 года"
• "Сравни VOO.US и QQQ.US"
• "Портфель: 70% VOO.US, 20% AGG.US, 10% GC.COMM"
• "Инфляция в России за 10 лет"
• "Динамика нефти и золота в рублях"

Особенности:
✅ Автоматическое распознавание намерений
✅ Нормализация названий активов
✅ Построение аналитических отчетов
✅ Генерация графиков
✅ Выводы и рекомендации
✅ Поддержка конвертации валют
✅ Автоматическое разбиение длинных сообщений
✅ Контекстная память для лучшего понимания

Поддержка:
Если у вас возникли вопросы или проблемы, попробуйте:
1. Переформулировать запрос
2. Использовать более простые названия активов
3. Проверить доступность данных (MOEX может быть временно недоступен)

Начните с простого запроса или используйте команды выше!"""

        await self._send_message_safe(update, welcome_message)
    

    async def asset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /asset command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /asset AAPL.US или /asset SBER.MOEX", parse_mode='MarkdownV2')
            return
        
        symbol = context.args[0].upper()
        period = context.args[1] if len(context.args) > 1 else '10Y'
        
        # Update user context
        user_id = update.effective_user.id
        self._update_user_context(user_id, 
                                last_assets=[symbol] + self._get_user_context(user_id).get('last_assets', []),
                                last_analysis_type='asset',
                                last_period=period)
        
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol}...")
        
        try:
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await self._send_message_safe(update, f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Format asset info
            response = f"📊 Информация об активе: {symbol}\n\n"
            response += f"Название: {asset_info.get('name', 'N/A')}\n"
            response += f"Страна: {asset_info.get('country', 'N/A')}\n"
            response += f"Биржа: {asset_info.get('exchange', 'N/A')}\n"
            response += f"Валюта: {asset_info.get('currency', 'N/A')}\n"
            response += f"Тип: {asset_info.get('type', 'N/A')}\n"
            response += f"ISIN: {asset_info.get('isin', 'N/A')}\n"
            response += f"Период данных: {asset_info.get('period_length', 'N/A')}\n"
            
            if asset_info.get('current_price') is not None:
                response += f"Текущая цена: {asset_info['current_price']:.2f}\n"
            
            if asset_info.get('annual_return') != 'N/A':
                response += f"Годовая доходность: {asset_info['annual_return']}\n"
            
            if asset_info.get('total_return') != 'N/A':
                response += f"Общая доходность: {asset_info['total_return']}\n"
            
            if asset_info.get('volatility') != 'N/A':
                response += f"Волатильность: {asset_info['volatility']}\n"
            
            await self._send_message_safe(update, response)
            
            # Check if asset type suggests dividends and add dividend information
            asset_type = asset_info.get('type', '').lower()
            if any(keyword in asset_type for keyword in ['stock', 'акция', 'share', 'equity']):
                await self._send_message_safe(update, "💵 Получаю информацию о дивидендах...")
                
                try:
                    dividend_info = self.asset_service.get_asset_dividends(symbol)
                    
                    if 'error' not in dividend_info and dividend_info.get('dividends'):
                        dividends = dividend_info['dividends']
                        currency = dividend_info.get('currency', '')
                        
                        if dividends:
                            # Get current price for yield calculation
                            current_price = asset_info.get('current_price')
                            
                            dividend_response = f"💵 Дивиденды {symbol}\n\n"
                            dividend_response += f"Валюта: {currency}\n"
                            dividend_response += f"Количество выплат: {len(dividends)}\n\n"
                            
                            # Show last 5 dividends with yield calculation
                            sorted_dividends = sorted(dividends.items(), key=lambda x: x[0], reverse=True)[:5]
                            
                            for date, amount in sorted_dividends:
                                dividend_response += f"{date}: {amount:.2f} {currency}"
                                
                                # Calculate yield if we have current price
                                if current_price and current_price > 0:
                                    yield_pct = (amount / current_price) * 100
                                    dividend_response += f" (доходность: {yield_pct:.2f}%)"
                                
                                dividend_response += "\n"
                            
                            await self._send_message_safe(update, dividend_response)
                        else:
                            await self._send_message_safe(update, "💵 Дивиденды не выплачивались в указанный период")
                    else:
                        await self._send_message_safe(update, "💵 Информация о дивидендах недоступна")
                        
                except Exception as div_error:
                    self.logger.error(f"Error getting dividends for {symbol}: {div_error}")
                    await self._send_message_safe(update, f"⚠️ Ошибка при получении дивидендов: {str(div_error)}")
            
            # Get and send charts
            await self._send_message_safe(update, "📈 Получаю графики цен...")
            
            try:
                self.logger.info(f"Getting price history for {symbol} with period {period}")
                price_history = self.asset_service.get_asset_price_history(symbol, period)
                
                if 'error' in price_history:
                    self.logger.error(f"Error in price_history: {price_history['error']}")
                    await self._send_message_safe(update, f"⚠️ {price_history['error']}")
                else:
                    self.logger.info(f"Price history received successfully, charts count: {len(price_history.get('charts', []))}")
                    # Send charts
                    charts = price_history.get('charts', [])
                    if charts:
                        self.logger.info(f"Found {len(charts)} charts, sending them...")
                        for i, img_bytes in enumerate(charts):
                            try:
                                # Determine chart type based on index
                                if i == 0:
                                    chart_caption = f"📈 Ежедневный график 1Y: {symbol}"
                                elif i == 1:
                                    chart_caption = f"📊 Месячный график 10Y: {symbol}"
                                else:
                                    chart_caption = f"📈 График {i+1}: {symbol}"
                                
                                await context.bot.send_photo(
                                    chat_id=update.effective_chat.id, 
                                    photo=io.BytesIO(img_bytes),
                                    caption=chart_caption
                                )
                            except Exception as chart_error:
                                self.logger.error(f"Error sending chart {i+1}: {chart_error}")
                                await self._send_message_safe(update, f"⚠️ Не удалось отправить график {i+1}: {str(chart_error)}")
                    else:
                        await self._send_message_safe(update, "⚠️ Не удалось создать графики цен")
                        
            except Exception as chart_error:
                self.logger.error(f"Error getting charts for {symbol}: {chart_error}")
                await self._send_message_safe(update, f"⚠️ Ошибка при получении графиков: {str(chart_error)}")
            
            # Get AI analysis of charts
            if 'charts' in locals() and charts and len(charts) > 0:
                await self._send_message_safe(update, "🧠 Получаю AI-анализ графиков цен...", parse_mode='MarkdownV2')
                
                try:
                    # Create prompt for chart analysis
                    chart_analysis_prompt = f"""Проанализируй графики цен для актива {symbol} на основе следующих данных:

Основная информация:
• Актив: {symbol} ({asset_info.get('name', 'N/A')})
• Страна: {asset_info.get('country', 'N/A')}
• Биржа: {asset_info.get('exchange', 'N/A')}
• Валюта: {asset_info.get('currency', 'N/A')}
• Текущая цена: {asset_info.get('current_price', 'N/A')}

Доступные графики:
• Ежедневный график за 1 год (детальный анализ)
• Месячный график за 10 лет (долгосрочные тренды)

Задача: Предоставь краткий, но информативный анализ графиков, включая:
1. Основные тренды и паттерны
2. Ключевые уровни поддержки и сопротивления
3. Оценка волатильности
4. Краткосрочные и долгосрочные перспективы
5. Основные риски и возможности

Анализ должен быть на русском языке, профессиональным, но понятным для обычных инвесторов."""

                    chart_ai_response = self.yandexgpt_service.ask_question(chart_analysis_prompt)
                    
                    if chart_ai_response:
                        self.logger.info(f"Chart AI response received, length: {len(chart_ai_response)}")
                        # Split response if it's too long
                        if len(chart_ai_response) > 4000:
                            self.logger.info(f"Chart AI response is long ({len(chart_ai_response)} chars), using _send_long_text")
                            await self._send_message_safe(update, "🧠 AI-анализ графиков:")
                            await self._send_long_text(update, chart_ai_response)
                        else:
                            self.logger.info(f"Chart AI response is short ({len(chart_ai_response)} chars), sending directly")
                            await self._send_message_safe(update, f"🧠 AI-анализ графиков:\n\n{chart_ai_response}")
                    else:
                        self.logger.warning("Chart AI response is empty")
                        await self._send_message_safe(update, "⚠️ AI-анализ графиков недоступен. Попробуйте позже.")
                        
                except Exception as chart_ai_error:
                    self.logger.error(f"Error getting chart analysis for {symbol}: {chart_ai_error}")
                    await self._send_message_safe(update, f"⚠️ Ошибка при получении AI-анализа графиков: {str(chart_ai_error)}")
            
            # Get analysis
            await self._send_message_safe(update, "🧠 Получаю анализ актива...")
            
            try:
                self.logger.info(f"Starting AI analysis for {symbol}")
                
                # Create prompt for analysis
                ai_prompt = f"""Проанализируй актив {symbol} ({asset_info.get('name', 'N/A')}) на основе следующей информации:

Основные характеристики:
• Страна: {asset_info.get('country', 'N/A')}
• Биржа: {asset_info.get('exchange', 'N/A')}
• Валюта: {asset_info.get('currency', 'N/A')}
• Тип: {asset_info.get('type', 'N/A')}
• Текущая цена: {asset_info.get('current_price', 'N/A')}
• Годовая доходность: {asset_info.get('annual_return', 'N/A')}
• Общая доходность: {asset_info.get('total_return', 'N/A')}
• Волатильность: {asset_info.get('volatility', 'N/A')}

Задача: Предоставь краткий, но информативный анализ актива, включая:
1. Краткую справку о бизнесе компании и отрасли (2-3 предложения)
2. Основные факторы, влияющие на его стоимость
3. Краткосрочные и долгосрочные перспективы
4. Основные риски
5. Рекомендации для инвесторов

Анализ должен быть на русском языке, профессиональным, но понятным для обычных инвесторов."""

                self.logger.info(f"AI prompt created, length: {len(ai_prompt)}")
                self.logger.info(f"Calling yandexgpt_service.ask_question...")
                
                ai_response = self.yandexgpt_service.ask_question(ai_prompt)
                
                if ai_response:
                    self.logger.info(f"AI response received, length: {len(ai_response)}")
                    # Split response if it's too long
                    if len(ai_response) > 4000:
                        self.logger.info(f"AI response is long ({len(ai_response)} chars), using _send_long_text")
                        await self._send_message_safe(update, "🧠 Анализ актива:")
                        await self._send_long_text(update, ai_response)
                    else:
                        self.logger.info(f"AI response is short ({len(ai_response)} chars), sending directly")
                        await self._send_message_safe(update, f"🧠 Анализ актива:\n\n{ai_response}")
                else:
                    self.logger.warning("AI response is empty")
                    await self._send_message_safe(update, "⚠️ Анализ недоступен. Попробуйте позже.")
                    
            except Exception as ai_error:
                self.logger.error(f"Error getting analysis for {symbol}: {ai_error}")
                await self._send_message_safe(update, f"⚠️ Ошибка при получении анализа: {str(ai_error)}")
            
            # Update conversation history
            self._add_to_conversation_history(user_id, f"/asset {symbol} {period}", 
                                           f"Asset analysis completed for {symbol}")
                
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении информации об активе: {str(e)}")
    

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

    async def _send_long_text(self, update: Update, text: str, parse_mode: str = None):
        """Send long text by splitting it into multiple messages if needed"""
        # Base Telegram hard limit is 4096 chars for text messages.
        # We use configured limit if available and keep a safety margin
        try:
            max_length = getattr(Config, 'MAX_MESSAGE_LENGTH', 4000)
        except Exception:
            max_length = 4000
        
        self.logger.info(f"_send_long_text called with text length: {len(text)}")
        
        if len(text) <= max_length:
            # Single message is fine
            self.logger.info(f"Text fits in single message, sending directly")
            await update.message.reply_text(text)
        else:
            # Split into multiple messages
            self.logger.info(f"Text too long ({len(text)} chars), splitting into parts")
            parts = self._split_text_into_parts(text, max_length)
            self.logger.info(f"Split into {len(parts)} parts")
            
            # Log each part for debugging
            for i, part in enumerate(parts):
                self.logger.info(f"Part {i+1}: {len(part)} chars, starts with: {part[:50]}...")
            
            for i, part in enumerate(parts, 1):
                self.logger.info(f"Sending part {i}/{len(parts)}, length: {len(part)}")
                try:
                    if i == 1:
                        # First part
                        self.logger.info(f"Sending first part")
                        await update.message.reply_text(part)
                    else:
                        # Subsequent parts
                        continuation_prefix = f"📄 Продолжение ({i}/{len(parts)}):\n\n"
                        continuation_text = f"{continuation_prefix}{part}"
                        self.logger.info(f"Sending continuation part {i}")
                        await update.message.reply_text(continuation_text)
                        
                        # Add small delay between messages to avoid rate limiting
                        if i < len(parts):
                            import asyncio
                            await asyncio.sleep(0.5)
                            
                except Exception as e:
                    self.logger.error(f"Failed to send part {i}: {e}")
                    # Send as plain text as last resort
                    await update.message.reply_text(f"Часть {i} из {len(parts)}: {part[:1000]}...")
    
    def _split_text_into_parts(self, text: str, max_length: int) -> List[str]:
        """Split text into parts that fit within max_length"""
        parts = []
        
        # Simple approach: split by paragraphs first, then by sentences
        paragraphs = text.split('\n\n')
        
        current_part = ""
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
                        # Add period back to sentence
                        full_sentence = sentence + ('. ' if sentence != sentences[-1] else '.')
                        
                        # Check if adding this sentence would exceed max_length
                        if len(current_part) + len(full_sentence) > max_length:
                            if current_part:
                                parts.append(current_part.strip())
                                current_part = full_sentence
                            else:
                                # Single sentence is too long, split by words
                                words = full_sentence.split(' ')
                                temp_part = ""
                                for word in words:
                                    if len(temp_part) + len(word) + 1 > max_length:
                                        if temp_part:
                                            parts.append(temp_part.strip())
                                            temp_part = word
                                        else:
                                            # Single word is too long, truncate
                                            parts.append(word[:max_length-3] + "...")
                                    else:
                                        temp_part += " " + word if temp_part else word
                                if temp_part.strip():
                                    current_part = temp_part.strip()
                        else:
                            current_part += full_sentence
            else:
                current_part += "\n\n" + paragraph if current_part else paragraph
        
        # Add the last part
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Ensure we have at least one part
        if not parts:
            parts.append(text[:max_length-3] + "...")
        
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
                """⚖️ **Сравнение активов**

Просто напишите ваш запрос естественным языком:

**Сравнение акций:**
• "Сравни Apple и Microsoft"
• "Что лучше: VOO.US или SPY.US?"

**Сравнение классов активов:**
• "Сопоставь золото и серебро"
• "Сравни S&P 500 и NASDAQ"

**Сравнение валют:**
• "EUR/USD vs GBP/USD"
• "Анализ валютных пар"

Я автоматически:
✅ Сравниваю доходность
✅ Анализирую корреляции
✅ Строю сравнительные графики
✅ Предоставляю AI-выводы"""
            )
        elif query.data == "chat_help":
            await query.edit_message_text(
                """💬 **AI-советник**

Спросите меня о чем угодно по финансам:

**Теория:**
• "Что такое диверсификация?"
• "Как рассчитать коэффициент Шарпа?"
• "Объясни efficient frontier"

**Практика:**
• "Лучшие практики ребалансировки"
• "Как управлять рисками?"
• "Стратегии долгосрочного инвестирования"

**Анализ:**
• "Интерпретируй эти метрики"
• "Что означают эти данные?"

Я предоставлю экспертную финансовую консультацию на базе YandexGPT!"""
            )
    

    

    

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        
        application.add_handler(CommandHandler("asset", self.asset_command))
        
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
