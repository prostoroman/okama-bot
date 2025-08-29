import sys
import logging
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import io
import pandas as pd
try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    print("Warning: tabulate library not available. Using simple text formatting.")
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
        
        # User history management
        self.user_history: Dict[int, List[dict]] = {}       # chat_id -> list[{"role": "...", "parts": [str]}]
        self.context_enabled: Dict[int, bool] = {}          # chat_id -> bool
        self.MAX_HISTORY_MESSAGES = 20
        self.MAX_TELEGRAM_CHUNK = 4000
        
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
        
        if context['last_period']:
            summary.append(f"Период: {context['last_period']}")
        
        return "; ".join(summary) if summary else "Новый пользователь"
    
    # =======================
    # Вспомогательные функции для истории
    # =======================
    def _init_chat(self, chat_id: int):
        if chat_id not in self.user_history:
            self.user_history[chat_id] = []
        if chat_id not in self.context_enabled:
            self.context_enabled[chat_id] = True

    def _history_trim(self, chat_id: int):
        if len(self.user_history[chat_id]) > self.MAX_HISTORY_MESSAGES:
            self.user_history[chat_id] = self.user_history[chat_id][-self.MAX_HISTORY_MESSAGES:]

    def history_append(self, chat_id: int, role: str, text: str):
        if not self.context_enabled.get(chat_id, True):
            return
        self.user_history[chat_id].append({"role": role, "parts": [text]})
        self._history_trim(chat_id)

    def _split_text(self, text: str):
        for i in range(0, len(text), self.MAX_TELEGRAM_CHUNK):
            yield text[i:i + self.MAX_TELEGRAM_CHUNK]

    async def send_long_message(self, update: Update, text: str):
        if not text:
            text = "Пустой ответ."
        for chunk in self._split_text(text):
            await update.message.reply_text(chunk)
    
    async def _send_message_safe(self, update: Update, text: str, parse_mode: str = None, reply_markup = None):
        """Безопасная отправка сообщения с автоматическим разбиением на части"""
        try:
            # Проверяем, что text действительно является строкой
            if not isinstance(text, str):
                self.logger.warning(f"_send_message_safe received non-string data: {type(text)}")
                text = str(text)
            
            # Проверяем длину строки
            if len(text) <= 4000:
                await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                # Для длинных сообщений с кнопками отправляем первую часть с кнопками
                if reply_markup:
                    first_part = text[:4000]
                    await update.message.reply_text(first_part, parse_mode=parse_mode, reply_markup=reply_markup)
                    # Остальную часть отправляем без кнопок
                    remaining_text = text[4000:]
                    if remaining_text:
                        await self.send_long_message(update, remaining_text)
                else:
                    await self.send_long_message(update, text)
        except Exception as e:
            self.logger.error(f"Error in _send_message_safe: {e}")
            # Fallback: попробуем отправить как обычный текст
            try:
                await update.message.reply_text(f"Ошибка форматирования: {str(text)[:1000]}...")
            except:
                await update.message.reply_text("Произошла ошибка при отправке сообщения")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with full help"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        # Проверяем параметр start из URL
        start_param = None
        if context.args:
            start_param = context.args[0]
        
        # Если есть параметр start, обрабатываем его
        if start_param:
            if start_param == "info":
                await self.show_info_help(update)
                return
            elif start_param == "namespace":
                await self.show_namespace_help(update)
                return
            elif start_param.startswith("namespace_"):
                namespace = start_param.replace("namespace_", "")
                await self.show_namespace_symbols(update, namespace)
                return
            elif start_param.startswith("info_"):
                symbol = start_param.replace("info_", "")
                # Устанавливаем символ в контекст и вызываем команду info
                context.args = [symbol]
                await self.info_command(update, context)
                return
        
        welcome_message = f"""🧠 Okama Financial Brain - Полная справка

Привет, {user_name}! Я помогу с анализом рынков и портфелей.

Что умею:
• Анализ одного актива с графиками цен + AI-анализ каждого графика
• Сравнение нескольких активов
• Анализ портфеля (веса, риск/доходность, efficient frontier)
• Макро/товары/валюты
• Анализ инфляции
• Объяснения и рекомендации
• **🆕 AI-анализ изображений графиков** - отправьте фото для анализа!

Основные команды:
/start — эта справка
/info [тикер] [период] — базовая информация об активе с графиком и анализом
/namespace [название] — список пространств имен или символы в пространстве

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
✅ **🆕 AI-анализ изображений графиков** - отправьте фото для анализа!
✅ **🆕 Автоматический анализ каждого графика в подписях**

Поддержка:
Если у вас возникли вопросы или проблемы, попробуйте:
1. Переформулировать запрос
2. Использовать более простые названия активов
3. Проверить доступность данных (MOEX может быть временно недоступен)

Начните с простого запроса или используйте команды выше!"""

        # Создаем кнопки для быстрого доступа к основным командам
        keyboard = [
            [
                InlineKeyboardButton("📊 Информация об активе", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=info"),
                InlineKeyboardButton("📚 Пространства имен", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_message_safe(update, welcome_message, reply_markup=reply_markup)
    
    async def show_info_help(self, update: Update):
        """Показать справку по команде /info"""
        help_text = """📊 **Команда /info - Информация об активе**

Используйте команду `/info [тикер] [период]` для получения полной информации об активе.

**Примеры:**
• `/info AAPL.US` - информация об Apple
• `/info SBER.MOEX` - информация о Сбербанке
• `/info GC.COMM 5Y` - золото за 5 лет
• `/info SPX.INDX 10Y` - S&P 500 за 10 лет

**Поддерживаемые периоды:**
• 1Y, 2Y, 5Y, 10Y, MAX
• По умолчанию: 10Y для акций, 5Y для макро

**Что вы получите:**
✅ График цены актива
✅ Основные метрики
✅ AI-анализ графика
✅ Рекомендации

Просто введите команду в чат!"""
        
        # Кнопка возврата к главному меню
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_message_safe(update, help_text, reply_markup=reply_markup)
    
    async def show_namespace_help(self, update: Update):
        """Показать справку по команде /namespace"""
        help_text = """📚 **Команда /namespace - Пространства имен**

Используйте команду `/namespace` для просмотра всех доступных пространств имен.

**Популярные пространства:**
• `/namespace US` - американские акции
• `/namespace MOEX` - российские акции
• `/namespace INDX` - мировые индексы
• `/namespace FX` - валютные пары
• `/namespace COMM` - товарные активы

**Что вы получите:**
✅ Список всех пространств имен
✅ Категоризация по типам
✅ Количество символов в каждом
✅ Быстрые кнопки для популярных

Просто введите `/namespace` в чат!"""
        
        # Кнопка возврата к главному меню
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_message_safe(update, help_text, reply_markup=reply_markup)
    
    async def show_namespace_symbols(self, update: Update, namespace: str):
        """Показать символы в пространстве имен"""
        try:
            import okama as ok
            symbols_df = ok.symbols_in_namespace(namespace)
            
            if symbols_df.empty:
                await self._send_message_safe(update, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                return
            
            # Показываем первые 10 символов
            response = f"📊 **Пространство имен: {namespace}**\n\n"
            response += f"📈 **Статистика:**\n"
            response += f"• Всего символов: **{len(symbols_df)}**\n\n"
            
            # Подготавливаем данные для таблицы
            headers = ["Символ", "Название", "Страна", "Валюта"]
            
            # Получаем первые 10 строк
            first_10 = []
            for _, row in symbols_df.head(10).iterrows():
                symbol = row['symbol'] if pd.notna(row['symbol']) else 'N/A'
                name = row['name'] if pd.notna(row['name']) else 'N/A'
                country = row['country'] if pd.notna(row['country']) else 'N/A'
                currency = row['currency'] if pd.notna(row['currency']) else 'N/A'
                
                # Обрезаем длинные названия для читаемости
                if len(name) > 40:
                    name = name[:37] + "..."
                
                first_10.append([symbol, name, country, currency])
            
            # Создаем таблицу с кликабельными ссылками в названиях символов
            if first_10:
                response += "**Первые 10 символов:**\n\n"
                
                # Создаем таблицу с кликабельными ссылками
                for row in first_10:
                    symbol = row[0]
                    name = row[1]
                    country = row[2]
                    currency = row[3]
                    
                    # Создаем кликабельную ссылку в названии символа
                    symbol_link = f"[{symbol}](https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=info_{symbol})"
                    response += f"• **{symbol_link}** - {name} | {country} | {currency}\n"
                
                # Добавляем кнопку возврата
                keyboard = [[InlineKeyboardButton("🔙 К списку пространств", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self._send_message_safe(update, response, parse_mode="MarkdownV2", reply_markup=reply_markup)
            else:
                response += f"💡 Используйте `/namespace {namespace}` для полного списка символов"
                
                # Кнопка возврата к списку пространств имен
                keyboard = [[InlineKeyboardButton("🔙 К списку пространств", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self._send_message_safe(update, response, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении данных для '{namespace}': {str(e)}")
    

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command with detailed help"""
        await self._send_message_safe(update, 
            """📚 **Подробная справка по командам**

**📊 Анализ активов:**
• `/info <тикер>` - Полная информация об активе + AI-анализ графиков

**📚 Пространства имен:**
• `/namespace` - Список доступных пространств имен
• `/namespace <название>` - Символы в конкретном пространстве

**🤖 AI-помощник:**
• **🆕 Отправьте фото графика** - AI-анализ изображения!

**💡 Дополнительные возможности:**
• Анализ активов через текстовые запросы
• AI-консультации по финансам
• **🆕 Автоматический анализ графиков в подписях**

**📈 Поддерживаемые биржи:**
• MOEX (Московская биржа)
• US (NYSE, NASDAQ)
• LSE (Лондонская биржа)
• FX (Валютный рынок)
• COMM (Товарные рынки)

**💡 Примеры тикеров:**
• `SBER.MOEX` - Сбербанк
• `AAPL.US` - Apple
• `TSLA.US` - Tesla
• `XAU.COMM` - Золото
• `EURUSD.FX` - EUR/USD

**🆕 Новые возможности:**
• **Vision AI** - анализ графиков с помощью YandexGPT
• **🆕 Автоматический анализ каждого графика в подписи**
• Автоматический анализ трендов и паттернов
• Определение уровней поддержки/сопротивления
• Оценка волатильности и рисков

**💡 Как работает анализ графиков:**
• Каждый график автоматически анализируется AI
• Анализ включается в подпись к графику
• Общий анализ учитывает выводы по графикам
• Анализ трендов, уровней поддержки/сопротивления, волатильности

Отправьте фото любого финансового графика для получения профессионального AI-анализа!"""
        )


    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /info AAPL.US или /info SBER.MOEX")
            return
        
        symbol = context.args[0].upper()
        period = context.args[1] if len(context.args) > 1 else '10Y'
        
        # Update user context
        user_id = update.effective_user.id
        self._update_user_context(user_id, 
                                last_assets=[symbol] + self._get_user_context(user_id).get('last_assets', []),
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
                response += f"Текущая цена: {asset_info['current_price']:.2f} {asset_info.get('currency', 'N/A')}\n"
            
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
                            dividend_response += f"Количество выплат: {len(dividends)}\n\n"
                            
                            # Show last 5 dividends with yield calculation
                            sorted_dividends = sorted(dividends.items(), key=lambda x: x[0], reverse=True)[:10]
                            
                            for date, amount in sorted_dividends:
                                dividend_response += f"{date}: {amount:.2f} {currency}\n"
                                
                            
                            await self._send_message_safe(update, dividend_response)
                        else:
                            await self._send_message_safe(update, "💵 Дивиденды не выплачивались в указанный период")
                    else:
                        await self._send_message_safe(update, "💵 Информация о дивидендах недоступна")
                        
                except Exception as div_error:
                    self.logger.error(f"Error getting dividends for {symbol}: {div_error}")
                    await self._send_message_safe(update, f"⚠️ Ошибка при получении дивидендов: {str(div_error)}")
            
            # Get charts for analysis
            await self._send_message_safe(update, "📈 Получаю графики цен...")
            
            try:
                self.logger.info(f"Getting price history for {symbol} with period {period}")
                price_history = self.asset_service.get_asset_price_history(symbol, period)
                
                if 'error' in price_history:
                    self.logger.error(f"Error in price_history: {price_history['error']}")
                    await self._send_message_safe(update, f"❌ Ошибка при получении истории цен: {price_history['error']}")
                    return
                
                # Display charts from price history
                if 'charts' in price_history and price_history['charts']:
                    charts = price_history['charts']
                    for i, chart_data in enumerate(charts):
                        if chart_data:  # Check if chart data exists
                            await update.message.reply_photo(
                                photo=chart_data,
                                caption=f"📈 График цен {symbol} за период {period}"
                            )
                        else:
                            await self._send_message_safe(update, f"⚠️ График {i+1} не удалось отобразить")
                else:
                    await self._send_message_safe(update, "❌ Не удалось получить графики цен")
                
                # Get AI analysis
                await self._send_message_safe(update, "🧠 Получаю AI-анализ...")
                
                try:
                    analysis = self.analysis_engine.analyze_asset(symbol, price_history, period)
                    
                    if 'error' in analysis:
                        await self._send_message_safe(update, f"⚠️ AI-анализ недоступен: {analysis['error']}")
                    else:
                        await self._send_message_safe(update, f"🧠 **AI-анализ {symbol}**\n\n{analysis['analysis']}")
                        
                except Exception as analysis_error:
                    self.logger.error(f"Error in AI analysis for {symbol}: {analysis_error}")
                    await self._send_message_safe(update, "⚠️ AI-анализ временно недоступен")
                
            except Exception as chart_error:
                self.logger.error(f"Error creating chart for {symbol}: {chart_error}")
                await self._send_message_safe(update, f"❌ Ошибка при создании графика: {str(chart_error)}")
                
        except Exception as e:
            self.logger.error(f"Error in info command for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def namespace_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /namespace command"""
        try:
            import okama as ok
            
            if not context.args:
                # Show available namespaces
                namespaces = ok.namespaces
                
                response = "📚 **Доступные пространства имен (namespaces):**\n\n"
                response += f"📈 **Статистика:**\n"
                response += f"• Всего пространств имен: **{len(namespaces)}**\n\n"
                
                # Prepare data for tabulate
                headers = ["Код", "Описание", "Категория"]
                namespace_data = []
                
                # Categorize namespaces for better organization
                categories = {
                    'Биржи': ['MOEX', 'US', 'LSE', 'XAMS', 'XETR', 'XFRA', 'XSTU', 'XTAE'],
                    'Индексы': ['INDX'],
                    'Валюты': ['FX', 'CBR'],
                    'Товары': ['COMM'],
                    'Криптовалюты': ['CC'],
                    'Инфляция': ['INFL'],
                    'Недвижимость': ['RE'],
                    'Портфели': ['PF', 'PIF'],
                    'Депозиты': ['RATE'],
                    'Коэффициенты': ['RATIO']
                }
                
                # Create categorized data
                for namespace, description in namespaces.items():
                    category = "Другое"
                    for cat_name, cat_namespaces in categories.items():
                        if namespace in cat_namespaces:
                            category = cat_name
                            break
                    
                    namespace_data.append([namespace, description, category])
                
                # Sort by category and then by namespace
                namespace_data.sort(key=lambda x: (x[2], x[0]))
                
                # Create table using tabulate or fallback to simple format
                if TABULATE_AVAILABLE:
                    # Use plain format for best Telegram display
                    table = tabulate.tabulate(namespace_data, headers=headers, tablefmt="plain")
                    response += f"```\n{table}\n```\n\n"
                else:
                    # Fallback to simple text format
                    response += "**Код | Описание | Категория**\n"
                    response += "--- | --- | ---\n"
                    for row in namespace_data:
                        response += f"`{row[0]}` | {row[1]} | {row[2]}\n"
                    response += "\n"
                
                response += "💡 Используйте `/namespace <код>` для просмотра символов в конкретном пространстве"
                
                # Создаем кнопки для быстрого доступа к популярным пространствам имен
                keyboard = [
                    [
                        InlineKeyboardButton("🇺🇸 US акции", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_US"),
                        InlineKeyboardButton("🇷🇺 MOEX", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_MOEX")
                    ],
                    [
                        InlineKeyboardButton("📈 Индексы", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_INDX"),
                        InlineKeyboardButton("💱 Валюты", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_FX")
                    ],
                    [
                        InlineKeyboardButton("🪙 Товары", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_COMM"),
                        InlineKeyboardButton("🏦 CBR", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_CBR")
                    ],
                    [
                        InlineKeyboardButton("🇬🇧 LSE", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_LSE"),
                        InlineKeyboardButton("🇩🇪 XETR", url=f"https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=namespace_XETR")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self._send_message_safe(update, response, reply_markup=reply_markup)
                
            else:
                # Show symbols in specific namespace
                namespace = context.args[0].upper()
                
                try:
                    symbols_df = ok.symbols_in_namespace(namespace)
                    
                    # Check if DataFrame is empty
                    if symbols_df.empty:
                        await self._send_message_safe(update, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                        return
                    
                    # Convert DataFrame to list of symbols
                    # The DataFrame has 'symbol' column with full names like 'AAPL.US'
                    # We want to extract just the ticker part
                    if 'symbol' in symbols_df.columns:
                        # Extract ticker part (before the dot)
                        symbols = []
                        for full_symbol in symbols_df['symbol'].tolist():
                            if pd.isna(full_symbol) or full_symbol is None:
                                continue
                            symbol_str = str(full_symbol).strip()
                            if '.' in symbol_str:
                                ticker = symbol_str.split('.')[0]
                                symbols.append(ticker)
                            else:
                                symbols.append(symbol_str)
                    elif 'ticker' in symbols_df.columns:
                        symbols = symbols_df['ticker'].tolist()
                    else:
                        # If no clear column, try to get the first column
                        symbols = symbols_df.iloc[:, 0].tolist()
                    
                    if not symbols:
                        await self._send_message_safe(update, f"❌ Пространство имен '{namespace}' не содержит символов")
                        return
                    
                    # Show statistics first
                    total_symbols = len(symbols_df)
                    response = f"📊 **Пространство имен: {namespace}**\n\n"
                    response += f"📈 **Статистика:**\n"
                    response += f"• Всего символов: **{total_symbols}**\n"
                    response += f"• Колонки данных: {', '.join(symbols_df.columns)}\n\n"
                    
                    # Prepare data for tabulate
                    headers = ["Символ", "Название", "Страна", "Валюта"]
                    
                    # Get first 10 rows
                    first_10 = []
                    for _, row in symbols_df.head(10).iterrows():
                        symbol = row['symbol'] if pd.notna(row['symbol']) else 'N/A'
                        name = row['name'] if pd.notna(row['name']) else 'N/A'
                        country = row['country'] if pd.notna(row['country']) else 'N/A'
                        currency = row['currency'] if pd.notna(row['currency']) else 'N/A'
                        
                        # Truncate long names for readability
                        if len(name) > 40:
                            name = name[:37] + "..."
                        
                        first_10.append([symbol, name, country, currency])
                    
                    # Get last 10 rows
                    last_10 = []
                    for _, row in symbols_df.tail(10).iterrows():
                        symbol = row['symbol'] if pd.notna(row['symbol']) else 'N/A'
                        name = row['name'] if pd.notna(row['name']) else 'N/A'
                        country = row['country'] if pd.notna(row['country']) else 'N/A'
                        currency = row['currency'] if pd.notna(row['currency']) else 'N/A'
                        
                        # Truncate long names for readability
                        if len(name) > 40:
                            name = name[:37] + "..."
                        
                        last_10.append([symbol, name, country, currency])
                    
                    # Создаем таблицу с кликабельными ссылками в названиях символов
                    if first_10:
                        response += "**Первые 10 символов:**\n\n"
                        
                        # Создаем таблицу с кликабельными ссылками
                        for row in first_10:
                            symbol = row[0]
                            name = row[1]
                            country = row[2]
                            currency = row[3]
                            
                            # Создаем кликабельную ссылку в названии символа
                            symbol_link = f"[{symbol}](https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=info_{symbol})"
                            response += f"• **{symbol_link}** - {name} | {country} | {currency}\n"
                        
                        # Отправляем основное сообщение с таблицей
                        await self._send_message_safe(update, response, parse_mode="MarkdownV2")
                        
                        # Если есть еще символы, показываем их отдельно
                        if last_10 and total_symbols > 10:
                            last_response = "**Последние 10 символов:**\n\n"
                            
                            # Создаем таблицу для последних символов
                            for row in last_10:
                                symbol = row[0]
                                name = row[1]
                                country = row[2]
                                currency = row[3]
                                
                                # Создаем кликабельную ссылку в названии символа
                                symbol_link = f"[{symbol}](https://t.me/{Config.BOT_FULL_NAME.replace('@', '')}?start=info_{symbol})"
                                last_response += f"• **{symbol_link}** - {name} | {country} | {currency}\n"
                            
                            await self._send_message_safe(update, last_response, parse_mode="MarkdownV2")
                    else:
                        response += f"💡 Используйте `/info <символ>` для получения подробной информации об активе"
                        await self._send_message_safe(update, response)
                    
                    # Send Excel file with full list of symbols
                    try:
                        await self._send_message_safe(update, "📊 Создаю Excel файл со всеми символами...")
                        
                        # Create Excel file in memory
                        excel_buffer = io.BytesIO()
                        symbols_df.to_excel(excel_buffer, index=False, sheet_name=f'{namespace}_Symbols')
                        excel_buffer.seek(0)
                        
                        # Send Excel file
                        await update.message.reply_document(
                            document=excel_buffer,
                            filename=f"{namespace}_symbols.xlsx",
                            caption=f"📊 Полный список символов в пространстве {namespace} ({total_symbols} символов)"
                        )
                        
                        excel_buffer.close()
                        
                    except Exception as excel_error:
                        self.logger.error(f"Error creating Excel file for {namespace}: {excel_error}")
                        await self._send_message_safe(update, f"⚠️ Не удалось создать Excel файл: {str(excel_error)}")
                    
                except Exception as e:
                    await self._send_message_safe(update, f"❌ Ошибка при получении символов для '{namespace}': {str(e)}")
                    
        except ImportError:
            await self._send_message_safe(update, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in namespace command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")


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
            await self.send_long_message(update, final_response)
            
            # Отправляем графики с AI-анализом в подписях
            for i, img_bytes in enumerate(result.charts):
                try:
                    # Создаем подпись с анализом, если доступен
                    if hasattr(result, 'chart_analyses') and result.chart_analyses and i < len(result.chart_analyses):
                        caption = f"📊 График анализа\n\n🧠 AI-анализ:\n{result.chart_analyses[i]}"
                    else:
                        caption = f"📊 График анализа {i+1}"
                    
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=io.BytesIO(img_bytes),
                        caption=caption
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

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photo messages for chart analysis"""
        try:
            # Get the largest photo size
            photo = update.message.photo[-1]
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Download the photo
            file = await context.bot.get_file(photo.file_id)
            photo_bytes = await file.download_as_bytearray()
            
            # Create analysis prompt
            analysis_prompt = """Проанализируй финансовый график.

Задача: Опиши конкретно:
1. Тренд (восходящий/нисходящий/боковой)
2. Ключевые уровни поддержки и сопротивления
3. Волатильность

Ответ должен быть кратким и конкретным на русском языке."""
            
            # Analyze the photo with vision
            await self._send_message_safe(update, "🧠 Анализирую график...")
            
            ai_response = self.yandexgpt_service.ask_question_with_vision(
                analysis_prompt,
                bytes(photo_bytes),
                "Финансовый график, отправленный пользователем"
            )
            
            if ai_response and not ai_response.startswith("Ошибка") and not ai_response.startswith("Не удалось"):
                await self._send_message_safe(update, "🧠 Анализ графиков:")
                await self.send_long_message(update, ai_response)
            else:
                # Fallback: try regular analysis with photo description
                self.logger.info("Vision API failed, trying fallback analysis")
                try:
                    fallback_prompt = """Проанализируй финансовый график.

Задача: Опиши кратко:
1. Основные принципы анализа графиков
2. Типичные паттерны
3. Ключевые факторы цены

Ответ должен быть кратким и конкретным на русском языке."""
                    
                    fallback_response = self.yandexgpt_service.ask_question(fallback_prompt)
                    if fallback_response:
                        await self._send_message_safe(update, "🧠 Общий анализ принципов работы с графиками:")
                        await self.send_long_message(update, fallback_response)
                    else:
                        await self._send_message_safe(update, "⚠️ Не удалось проанализировать график. Попробуйте отправить более четкое изображение.")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback analysis also failed: {fallback_error}")
                    await self._send_message_safe(update, "⚠️ Не удалось проанализировать график. Попробуйте отправить более четкое изображение.")
                
        except Exception as e:
            self.logger.error(f"Error handling photo: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при анализе изображения: {str(e)}")

    async def _handle_message_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
        """Fallback метод для обработки сообщений (старая логика)"""
        try:
            # Старая логика обработки
            parsed = self.intent_parser.parse(user_message)

            # Chat fallback
            if parsed.intent == 'chat':
                # Simple AI response using YandexGPT
                try:
                    ai_response = self.yandexgpt_service.ask_question(user_message)
                    if ai_response:
                        await self.send_long_message(update, f"🤖 AI-ответ:\n\n{ai_response}")
                    else:
                        await self._send_message_safe(update, "Извините, не удалось получить AI-ответ. Попробуйте переформулировать вопрос.")
                except Exception as e:
                    self.logger.error(f"Error in AI chat: {e}")
                    await self._send_message_safe(update, "Извините, произошла ошибка при обработке AI-запроса.")
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
                # Use existing info command logic for single assets
                await self.info_command(update, context)
                return

            elif parsed.intent == 'asset_compare' or (parsed.intent == 'macro'):
                if len(valid_tickers) < 2:
                    # If only one valid, treat as single asset with chart
                    if len(valid_tickers) == 1:
                        await self.info_command(update, context)
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
                try:
                    ai_response = self.yandexgpt_service.ask_question(user_message)
                    if ai_response:
                        await self.send_long_message(update, f"🤖 AI-ответ:\n\n{ai_response}")
                    else:
                        await self._send_message_safe(update, "Извините, не удалось получить AI-ответ. Попробуйте переформулировать вопрос.")
                except Exception as e:
                    self.logger.error(f"Error in AI chat: {e}")
                    await self._send_message_safe(update, "Извините, произошла ошибка при обработке AI-запроса.")
                return

            # Send text and AI summary
            final_text = report_text or ""
            if ai_summary:
                final_text = f"{final_text}\n\nВыводы:\n{ai_summary}"
            await self.send_long_message(update, final_text)

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
        # Удаляем старые callback-обработчики, так как теперь используем прямые ссылки
        # Оставляем только базовые обработчики для других функций
        pass
    

    

    

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("info", self.info_command))
        application.add_handler(CommandHandler("namespace", self.namespace_command))
        
        # Add message and callback handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
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
