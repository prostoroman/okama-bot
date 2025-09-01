# Standard library imports
import sys
import logging
import os
import json
import threading
import re
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Any
import io
from datetime import datetime

# Third-party imports
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import okama as ok

# Configure matplotlib backend for headless environments (CI/CD)
if os.getenv('DISPLAY') is None and os.getenv('MPLBACKEND') is None:
    matplotlib.use('Agg')

# Optional imports
try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    print("Warning: tabulate library not available. Using simple text formatting.")

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Check Python version compatibility
if sys.version_info < (3, 7):
    print("ERROR: Python 3.7+ required. Current version:", sys.version)
    raise RuntimeError("Python 3.7+ required")

# Local imports
from config import Config
from services.asset_service import AssetService
from yandexgpt_service import YandexGPTService
from services.intent_parser_enhanced import EnhancedIntentParser
from services.asset_resolver_enhanced import EnhancedAssetResolver
from services.okama_handler_enhanced import EnhancedOkamaHandler
from services.report_builder_enhanced import EnhancedReportBuilder
from services.analysis_engine_enhanced import EnhancedAnalysisEngine
from services.financial_brain_enhanced import EnhancedOkamaFinancialBrain
from services.chart_styles import chart_styles

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health check for deployment
def health_check():
    """Simple health check for deployment"""
    logger.info(f"✅ Environment: {'PRODUCTION' if os.getenv('PRODUCTION') else 'LOCAL'}")
    logger.info(f"✅ Python version: {sys.version}")
    logger.info(f"✅ Bot token configured: {'Yes' if Config.TELEGRAM_BOT_TOKEN else 'No'}")
    return True

class OkamaFinanceBot:
    """Enhanced Telegram bot for financial analysis with Okama library"""
    
    def __init__(self):
        """Initialize the bot with required services"""
        Config.validate()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
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
        
    async def _handle_error(self, update: Update, error: Exception, context: str = "Unknown operation") -> None:
        """Общая функция для обработки ошибок"""
        error_msg = f"❌ Ошибка в {context}: {str(error)}"
        self.logger.error(f"{error_msg} - {traceback.format_exc()}")
        
        try:
            await self._send_message_safe(update, error_msg)
        except Exception as send_error:
            self.logger.error(f"Failed to send error message: {send_error}")
            # Try to send a simple error message
            try:
                if hasattr(update, 'message') and update.message is not None:
                    await update.message.reply_text("Произошла ошибка при обработке запроса")
            except Exception as final_error:
                self.logger.error(f"Final error message sending failed: {final_error}")
        
    def _parse_portfolio_data(self, portfolio_data_str: str) -> tuple[list, list]:
        """Parse portfolio data string with weights (symbol:weight,symbol:weight)"""
        try:
            if not portfolio_data_str or not portfolio_data_str.strip():
                return [], []
                
            symbols = []
            weights = []
            
            for item in portfolio_data_str.split(','):
                item = item.strip()
                if not item:  # Skip empty items
                    continue
                    
                if ':' in item:
                    symbol, weight_str = item.split(':', 1)
                    symbol = symbol.strip()
                    if symbol:  # Only add non-empty symbols
                        symbols.append(symbol)
                        weights.append(float(weight_str.strip()))
                else:
                    # Fallback: treat as symbol without weight
                    symbols.append(item)
                    weights.append(1.0 / len([x for x in portfolio_data_str.split(',') if x.strip()]))
            
            return symbols, weights
        except Exception as e:
            self.logger.error(f"Error parsing portfolio data: {e}")
            return [], []

    def _normalize_or_equalize_weights(self, symbols: list, weights: list) -> list:
        """Return valid weights for okama: normalize if close to 1, else equal weights.

        - If weights list is empty or length mismatch with symbols, fallback to equal weights.
        - If any weight is non-positive, fallback to equal weights.
        - If sum differs from 1.0 beyond small epsilon, normalize to sum=1.0.
        """
        try:
            if not symbols:
                return []

            num_assets = len(symbols)

            # Fallback to equal weights when missing or invalid length
            if not weights or len(weights) != num_assets:
                return [1.0 / num_assets] * num_assets

            # Validate positivity
            if any((w is None) or (w <= 0) for w in weights):
                return [1.0 / num_assets] * num_assets

            total = sum(weights)
            if total <= 0:
                return [1.0 / num_assets] * num_assets

            # If already ~1 within tolerance, keep; else normalize precisely
            if abs(total - 1.0) <= 1e-6:
                return [float(w) for w in weights]

            normalized = [float(w) / total for w in weights]

            # Guard against numerical drift
            norm_total = sum(normalized)
            if abs(norm_total - 1.0) > 1e-9:
                # Final correction by scaling the first element
                diff = 1.0 - norm_total
                normalized[0] += diff
            return normalized
        except Exception:
            # Safe fallback
            return [1.0 / len(symbols)] * len(symbols) if symbols else []

    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Получить контекст пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'last_assets': [],  # Последние анализируемые активы
                'last_analysis_type': None,  # Тип последнего анализа
                'last_period': None,  # Последний период анализа
                'conversation_history': [],  # История разговора
                'preferences': {},  # Предпочтения пользователя
                'portfolio_count': 0,  # Счетчик созданных портфелей
                'saved_portfolios': {}  # Сохраненные портфели {symbol: {symbols, weights, currency, created_at, description}}
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
        if hasattr(update, 'message') and update.message is not None:
            for chunk in self._split_text(text):
                await update.message.reply_text(chunk)
    
    async def _send_message_safe(self, update: Update, text: str, parse_mode: str = None, reply_markup=None):
        """Безопасная отправка сообщения с автоматическим разбиением на части - исправлено для обработки None"""
        try:
            # Проверяем, что update и message не None
            if update is None:
                self.logger.error("Cannot send message: update is None")
                return
            
            if not hasattr(update, 'message') or update.message is None:
                self.logger.error("Cannot send message: update.message is None")
                return
            
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
                if hasattr(update, 'message') and update.message is not None:
                    await update.message.reply_text(f"Ошибка форматирования: {str(text)[:1000]}...")
            except Exception as fallback_error:
                self.logger.error(f"Fallback message sending failed: {fallback_error}")
                try:
                    if hasattr(update, 'message') and update.message is not None:
                        await update.message.reply_text("Произошла ошибка при отправке сообщения")
                except Exception as final_error:
                    self.logger.error(f"Final fallback message sending failed: {final_error}")
    
    def _truncate_caption(self, text: Any) -> str:
        """Обрезать подпись до допустимой длины Telegram.
        Гарантирует, что длина не превышает Config.MAX_CAPTION_LENGTH.
        """
        try:
            if text is None:
                return ""
            if not isinstance(text, str):
                text = str(text)
            max_len = getattr(Config, 'MAX_CAPTION_LENGTH', 1024)
            if len(text) <= max_len:
                return text
            ellipsis = "…"
            if max_len > len(ellipsis):
                return text[: max_len - len(ellipsis)] + ellipsis
            return text[:max_len]
        except Exception as e:
            self.logger.error(f"Error truncating caption: {e}")
            safe_text = "" if text is None else str(text)
            return safe_text[:1024]
    
    async def _send_additional_charts(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Отправить дополнительные графики анализа (drawdowns, dividend yield)"""
        try:
            # Send typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Create drawdowns chart
            await self._create_drawdowns_chart(update, context, asset_list, symbols, currency)
            
            # Create dividend yield chart if available
            await self._create_dividend_yield_chart(update, context, asset_list, symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error creating additional charts: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать дополнительные графики: {str(e)}")
    

    
    async def _create_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Создать график drawdowns"""
        try:
            # Check if drawdowns data is available
            if not hasattr(asset_list, 'drawdowns') or asset_list.drawdowns.empty:
                await self._send_message_safe(update, "ℹ️ Данные о drawdowns недоступны для выбранных активов")
                return
            
            # Create drawdowns chart using chart_styles
            fig, ax = chart_styles.create_drawdowns_chart(
                asset_list.drawdowns, symbols, currency
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send drawdowns chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"📉 График Drawdowns для {len(symbols)} активов\n\nПоказывает периоды падения активов и их восстановление")
            )
            
        except Exception as e:
            self.logger.error(f"Error creating drawdowns chart: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать график drawdowns: {str(e)}")
    
    async def _create_dividend_yield_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Создать график dividend yield"""
        try:
            # Check if dividend yield data is available
            if not hasattr(asset_list, 'dividend_yield') or asset_list.dividend_yield.empty:
                await self._send_message_safe(update, "ℹ️ Данные о дивидендной доходности недоступны для выбранных активов")
                return
            
            # Create dividend yield chart using chart_styles
            fig, ax = chart_styles.create_dividend_yield_chart(
                asset_list.dividend_yield, symbols
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send dividend yield chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"💰 График дивидендной доходности для {len(symbols)} активов\n\nПоказывает историю дивидендных выплат и доходность")
            )
            
        except Exception as e:
            self.logger.error(f"Error creating dividend yield chart: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать график дивидендной доходности: {str(e)}")
    
    async def _create_correlation_matrix(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list):
        """Создать корреляционную матрицу активов"""
        try:
            self.logger.info(f"Starting correlation matrix creation for symbols: {symbols}")
            
            # Check if assets_ror data is available
            if not hasattr(asset_list, 'assets_ror'):
                self.logger.warning("assets_ror attribute does not exist")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
                
            if asset_list.assets_ror is None:
                self.logger.warning("assets_ror is None")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
                
            if asset_list.assets_ror.empty:
                self.logger.warning("assets_ror is empty")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
            
            # Get correlation matrix
            correlation_matrix = asset_list.assets_ror.corr()
            
            self.logger.info(f"Correlation matrix created successfully, shape: {correlation_matrix.shape}")
            
            if correlation_matrix.empty:
                self.logger.warning("Correlation matrix is empty")
                await self._send_message_safe(update, "ℹ️ Не удалось вычислить корреляционную матрицу")
                return
            
            # Create correlation matrix visualization using chart_styles
            fig, ax = chart_styles.create_correlation_matrix_chart(
                correlation_matrix
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send correlation matrix
            self.logger.info("Sending correlation matrix image...")
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"🔗 Корреляционная матрица для {len(symbols)} активов\n\nПоказывает корреляцию между доходностями активов (от -1 до +1)\n\n• +1: полная положительная корреляция\n• 0: отсутствие корреляции\n• -1: полная отрицательная корреляция")
            )
            self.logger.info("Correlation matrix image sent successfully")
            
            plt.close(fig)
            
        except Exception as e:
            self.logger.error(f"Error creating correlation matrix: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать корреляционную матрицу: {str(e)}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with full help"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""
• Анализ активов (акции, облигации, товары, индексы, валюты) с графиками цен
• Сравнение нескольких активов с графиками накопленной доходности и учетом инфляции
• Анализ портфеля (веса, риски, доходность, прогнозы)

Основные команды:
/start — эта справка
/info [тикер] [период] — базовая информация об активе с графиком и анализом
/compare [символ1] [символ2] ... — сравнение активов с графиком накопленной доходности
/portfolio [символ1:доля1] [символ2:доля2] ... — создание портфеля с указанными весами
/namespace [название] — список пространств имен или символы в пространстве

Поддерживаемые форматы тикеров:
• US акции: AAPL.US, VOO.US, SPY.US, QQQ.US
• MOEX: SBER.MOEX, GAZP.MOEX, LKOH.MOEX
• Индексы: SPX.INDX, IXIC.INDX, RGBITR.INDX
• Товары: GC.COMM (золото), CL.COMM (нефть), SI.COMM (серебро)
• Валюты: EURUSD.FX, GBPUSD.FX, USDJPY.FX
• LSE: VOD.LSE, HSBA.LSE, BP.LSE

Примеры команд:
• `/compare SPY.US QQQ.US` - сравнить S&P 500 и NASDAQ
• `/compare SBER.MOEX,GAZP.MOEX` - сравнить Сбербанк и Газпром
• `/compare SPY.US, QQQ.US, VOO.US` - сравнить с пробелами после запятых
• `/compare GC.COMM CL.COMM` - сравнить золото и нефть
• `/compare VOO.US,BND.US,GC.COMM` - сравнить акции, облигации и золото

• `/portfolio SPY.US:0.5 QQQ.US:0.3 BND.US:0.2` - портфель 50% S&P 500, 30% NASDAQ, 20% облигации
• `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3` - российский портфель
Базовая валюта опрелеляется по первому символу в списке.

⚠️ Вся информация предоставляется исключительно в информационных целях и не является инвестиционными рекомендациями.

"""

        await self._send_message_safe(update, welcome_message)
    
    async def show_info_help(self, update: Update):
        """Показать справку по команде /info"""
        help_text = """📊 Команда /info - Информация об активе

Используйте команду `/info [тикер] [период]` для получения полной информации об активе.

Примеры:
• `/info AAPL.US` - информация об Apple
• `/info SBER.MOEX` - информация о Сбербанке
• `/info GC.COMM 5Y` - золото за 5 лет
• `/info SPX.INDX 10Y` - S&P 500 за 10 лет

Поддерживаемые периоды:
• 1Y, 2Y, 5Y, 10Y, MAX
• По умолчанию: 10Y для акций, 5Y для макро
"""
        
        await self._send_message_safe(update, help_text)
    
    async def show_namespace_help(self, update: Update):
        """Показать справку по команде /namespace"""
        help_text = """📚 Команда /namespace - Пространства имен

Используйте команду `/namespace` для просмотра всех доступных пространств имен.

• `/namespace US` - американские акции
• `/namespace MOEX` - российские акции
• `/namespace INDX` - мировые индексы
• `/namespace FX` - валютные пары
• `/namespace COMM` - товарные активы

"""
        
        await self._send_message_safe(update, help_text)
    
    async def _show_namespace_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str, is_callback: bool = False):
        """Единый метод для показа символов в пространстве имен"""
        try:
            symbols_df = ok.symbols_in_namespace(namespace)
            
            if symbols_df.empty:
                error_msg = f"❌ Пространство имен '{namespace}' не найдено или пусто"
                if is_callback:
                    # Для callback сообщений отправляем через context.bot
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=error_msg
                    )
                else:
                    await self._send_message_safe(update, error_msg)
                return
            
            # Show statistics first
            total_symbols = len(symbols_df)
            response = f"📊 Пространство имен: {namespace}\n\n"
            response += f"📈 Статистика:\n"
            response += f"• Всего символов: {total_symbols}\n"
            response += f"• Колонки данных: {', '.join(symbols_df.columns)}\n\n"
            
            # Prepare data for display - show top 30 or all if less than 30
            display_count = min(30, total_symbols)
            response += f"📋 Показываю первые {display_count}:\n\n"
            
            # Get top symbols (first 30 or all if less than 30)
            top_symbols = []
            for _, row in symbols_df.head(display_count).iterrows():
                symbol = row['symbol'] if pd.notna(row['symbol']) else 'N/A'
                name = row['name'] if pd.notna(row['name']) else 'N/A'
                country = row['country'] if pd.notna(row['country']) else 'N/A'
                currency = row['currency'] if pd.notna(row['currency']) else 'N/A'
                
                # Truncate long names for readability
                if len(name) > 40:
                    name = name[:37] + "..."
                
                top_symbols.append([symbol, name, country, currency])
            
            # Создаем простую таблицу символов
            if top_symbols:
                for row in top_symbols:
                    symbol = row[0]
                    name = row[1]
                    country = row[2]
                    currency = row[3]
                    
                    response += f"• {symbol} - {name} | {country} | {currency}\n"
                
                # Добавляем кнопку для выгрузки Excel
                keyboard = [[
                    InlineKeyboardButton(
                        f"📊 Полный список в Excel ({total_symbols})", 
                        callback_data=f"excel_namespace_{namespace}"
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Отправляем сообщение с таблицей и кнопкой
                if is_callback:
                    # Для callback сообщений отправляем через context.bot с кнопками
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=response,
                        reply_markup=reply_markup
                    )
                else:
                    await self._send_message_safe(update, response, reply_markup=reply_markup)
            else:
                response += f"💡 Используйте `/info <символ>` для получения подробной информации об активе"
                if is_callback:
                    # Для callback сообщений отправляем через context.bot
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=response
                    )
                else:
                    await self._send_message_safe(update, response)
            
        except Exception as e:
            error_msg = f"❌ Ошибка при получении данных для '{namespace}': {str(e)}"
            if is_callback:
                # Для callback сообщений отправляем через context.bot
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=error_msg
                )
            else:
                await self._send_message_safe(update, error_msg)
    




    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command - показывает ежедневный график с базовой информацией и AI анализом"""
        if not context.args:
            await self._send_message_safe(update, 
                "Укажите тикер актива. Пример: /info AAPL.US или /info SBER.MOEX")
            return
        
        symbol = context.args[0].upper()
        
        # Update user context
        user_id = update.effective_user.id
        self._update_user_context(user_id, 
                                last_assets=[symbol] + self._get_user_context(user_id).get('last_assets', []))
        
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol}...")
        
        try:
            # Получаем базовую информацию об активе
            asset_info = self.asset_service.get_asset_info(symbol)
            
            if 'error' in asset_info:
                await self._send_message_safe(update, f"❌ Ошибка: {asset_info['error']}")
                return
            
            # Получаем ежедневный график (1Y)
            await self._send_message_safe(update, "📈 Получаю ежедневный график...")
            
            try:
                daily_chart = await self._get_daily_chart(symbol)
                
                self.logger.info(f"Daily chart result for {symbol}: {type(daily_chart)}")
                if daily_chart:
                    self.logger.info(f"Daily chart size: {len(daily_chart)} bytes")
                    # Формируем базовую информацию для подписи
                    caption = f"📊 {symbol} - {asset_info.get('name', 'N/A')}\n\n"
                    caption += f"🏛️: {asset_info.get('exchange', 'N/A')}\n"
                    caption += f"🌍: {asset_info.get('country', 'N/A')}\n"
                    caption += f"💰: {asset_info.get('currency', 'N/A')}\n"
                    caption += f"📈: {asset_info.get('type', 'N/A')}\n"
                    
                    if asset_info.get('current_price') is not None:
                        caption += f"💵 Текущая цена: {asset_info['current_price']:.2f} {asset_info.get('currency', 'N/A')}\n"
                    
                    if asset_info.get('annual_return') != 'N/A':
                        caption += f"📊 Годовая доходность: {asset_info['annual_return']}\n"
                    
                    if asset_info.get('volatility') != 'N/A':
                        caption += f"📉 Волатильность: {asset_info['volatility']}\n"
                    
                    # Получаем AI анализ
                    try:
                        analysis = await self._get_ai_analysis(symbol)
                        if analysis:
                            caption += analysis
                        else:
                            caption += "AI-анализ временно недоступен"
                    except Exception as analysis_error:
                        self.logger.error(f"Error in AI analysis for {symbol}: {analysis_error}")
                        caption += "AI-анализ временно недоступен"
                    
                    # Отправляем график с информацией
                    await update.message.reply_photo(
                        photo=daily_chart,
                        caption=self._truncate_caption(caption)
                    )
                    
                    # Создаем кнопки для дополнительных функций
                    keyboard = [
                        [
                            InlineKeyboardButton("📅 Месячный график (10Y)", callback_data=f"monthly_chart_{symbol}"),
                            InlineKeyboardButton("💵 Дивиденды", callback_data=f"dividends_{symbol}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    if hasattr(update, 'message') and update.message is not None:
                        await update.message.reply_text(
                            "Выберите дополнительную информацию:",
                            reply_markup=reply_markup
                        )
                    
                else:
                    await self._send_message_safe(update, "❌ Не удалось получить ежедневный график")
                    
            except Exception as chart_error:
                self.logger.error(f"Error creating daily chart for {symbol}: {chart_error}")
                await self._send_message_safe(update, f"❌ Ошибка при создании графика: {str(chart_error)}")
                
        except Exception as e:
            self.logger.error(f"Error in info command for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def _get_daily_chart(self, symbol: str) -> Optional[bytes]:
        """Получить ежедневный график за 1 год"""
        try:
            # Получаем данные для ежедневного графика
            self.logger.info(f"Getting daily chart for {symbol}")
            price_history = self.asset_service.get_asset_price_history(symbol, '1Y')
            
            if 'error' in price_history:
                self.logger.error(f"Error in price_history: {price_history['error']}")
                return None
            
            # Получаем данные о ценах
            if 'prices' in price_history and price_history['prices'] is not None:
                prices = price_history['prices']
                currency = price_history.get('currency', 'USD')
                
                # Создаем график с использованием централизованных стилей
                return self._create_daily_chart_with_styles(symbol, prices, currency)
            
            # Fallback к старому методу если нет данных о ценах
            if 'charts' in price_history and price_history['charts']:
                charts = price_history['charts']
                if 'adj_close' in charts and charts['adj_close']:
                    self.logger.info(f"Found adj_close chart for {symbol}")
                    return charts['adj_close']
                elif 'fallback' in charts and charts['fallback']:
                    self.logger.info(f"Found fallback chart for {symbol}")
                    return charts['fallback']
                
                for chart_type, chart_data in charts.items():
                    if chart_data:
                        self.logger.info(f"Using {chart_type} chart for {symbol}")
                        return chart_data
            
            self.logger.warning(f"No charts found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting daily chart for {symbol}: {e}")
            return None

    async def _get_ai_analysis(self, symbol: str) -> Optional[str]:
        """Получить AI анализ актива без рекомендаций"""
        try:
            # Получаем базовые данные для анализа
            price_history = self.asset_service.get_asset_price_history(symbol, '1Y')
            
            if 'error' in price_history:
                return None
            
            # Получаем анализ
            analysis = self.analysis_engine.analyze_asset(symbol, price_history, '1Y')
            
            if 'error' in analysis:
                return None
            
            # Модифицируем анализ, убирая рекомендации
            analysis_text = analysis['analysis']
            
            
            return analysis_text
            
        except Exception as e:
            self.logger.error(f"Error getting AI analysis for {symbol}: {e}")
            return None



    def _create_daily_chart_with_styles(self, symbol: str, prices, currency: str) -> Optional[bytes]:
        """Создать ежедневный график с централизованными стилями"""
        try:
            # Подготавливаем данные для графика
            if hasattr(prices, 'index') and hasattr(prices, 'values'):
                dates = prices.index
                values = prices.values
            else:
                # Fallback для других типов данных
                dates = list(prices.keys()) if isinstance(prices, dict) else range(len(prices))
                values = list(prices.values()) if isinstance(prices, dict) else list(prices)
            
            # Конвертируем даты если нужно
            try:
                if hasattr(dates, 'to_timestamp'):
                    dates = dates.to_timestamp()
                elif hasattr(dates, 'astype'):
                    dates = dates.astype('datetime64[ns]')
            except Exception:
                pass
            
            # Используем универсальный метод создания графика
            return chart_styles.create_price_chart(
                symbol=symbol,
                dates=dates,
                values=values,
                currency=currency,
                chart_type='daily',
                title_suffix='(1 год)'
            )
            
        except Exception as e:
            self.logger.error(f"Error creating daily chart with styles for {symbol}: {e}")
            return None

    def _create_monthly_chart_with_styles(self, symbol: str, prices, currency: str) -> Optional[bytes]:
        """Создать месячный график с централизованными стилями"""
        try:
            # Подготавливаем данные для графика
            if hasattr(prices, 'index') and hasattr(prices, 'values'):
                dates = prices.index
                values = prices.values
            else:
                # Fallback для других типов данных
                dates = list(prices.keys()) if isinstance(prices, dict) else range(len(prices))
                values = list(prices.values()) if isinstance(prices, dict) else list(prices)
            
            # Конвертируем даты если нужно
            try:
                if hasattr(dates, 'to_timestamp'):
                    dates = dates.to_timestamp()
                elif hasattr(dates, 'astype'):
                    dates = dates.astype('datetime64[ns]')
            except Exception:
                pass
            
            # Используем универсальный метод создания графика
            return chart_styles.create_price_chart(
                symbol=symbol,
                dates=dates,
                values=values,
                currency=currency,
                chart_type='monthly',
                title_suffix='(10 лет)'
            )
            
        except Exception as e:
            self.logger.error(f"Error creating monthly chart with styles for {symbol}: {e}")
            return None

    async def namespace_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /namespace command"""
        try:
            
            if not context.args:
                # Show available namespaces
                namespaces = ok.namespaces
                
                response = "📚 Доступные пространства имен (namespaces):\n\n"
                response += f"• Всего: {len(namespaces)}\n\n"
                
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
                    response += "Код | Описание | Категория\n"
                    response += "--- | --- | ---\n"
                    for row in namespace_data:
                        response += f"`{row[0]}` | {row[1]} | {row[2]}\n"
                    response += "\n"
                
                response += "💡 Используйте `/namespace <код>` для просмотра символов в конкретном пространстве"
                
                # Создаем кнопки для основных пространств имен
                keyboard = []
                
                # Основные биржи
                keyboard.append([
                    InlineKeyboardButton("🇺🇸 US", callback_data="namespace_US"),
                    InlineKeyboardButton("🇷🇺 MOEX", callback_data="namespace_MOEX"),
                    InlineKeyboardButton("🇬🇧 LSE", callback_data="namespace_LSE")
                ])
                
                # Европейские биржи
                keyboard.append([
                    InlineKeyboardButton("🇩🇪 XETR", callback_data="namespace_XETR"),
                    InlineKeyboardButton("🇫🇷 XFRA", callback_data="namespace_XFRA"),
                    InlineKeyboardButton("🇳🇱 XAMS", callback_data="namespace_XAMS")
                ])
                
                # Индексы и валюты
                keyboard.append([
                    InlineKeyboardButton("📊 INDX", callback_data="namespace_INDX"),
                    InlineKeyboardButton("💱 FX", callback_data="namespace_FX"),
                    InlineKeyboardButton("🏦 CBR", callback_data="namespace_CBR")
                ])
                
                # Товары и криптовалюты
                keyboard.append([
                    InlineKeyboardButton("🛢️ COMM", callback_data="namespace_COMM"),
                    InlineKeyboardButton("₿ CC", callback_data="namespace_CC"),
                    InlineKeyboardButton("🏠 RE", callback_data="namespace_RE")
                ])
                
                # Портфели и депозиты
                keyboard.append([
                    InlineKeyboardButton("💼 PF", callback_data="namespace_PF"),
                    InlineKeyboardButton("💰 PIF", callback_data="namespace_PIF"),
                    InlineKeyboardButton("🏦 RATE", callback_data="namespace_RATE")
                ])
                
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
                    
                    # Используем единый метод для показа символов
                    await self._show_namespace_symbols(update, context, namespace, is_callback=False)
                    
                except Exception as e:
                    await self._send_message_safe(update, f"❌ Ошибка при получении символов для '{namespace}': {str(e)}")
                    
        except ImportError:
            await self._send_message_safe(update, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in namespace command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command for comparing multiple assets"""
        try:
            if not context.args:
                # Get user's saved portfolios for help message
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                saved_portfolios = user_context.get('saved_portfolios', {})
                
                help_text = "📊 Команда /compare - Сравнение активов\n\n"
                help_text += "Использование:\n"
                help_text += "`/compare символ1 символ2 символ3 ...`\n"
                help_text += "или\n"
                help_text += "`/compare символ1,символ2,символ3`\n"
                help_text += "или\n"
                help_text += "`/compare символ1, символ2, символ3`\n\n"
                
                # Add saved portfolios information
                if saved_portfolios:
                    help_text += "💾 Ваши сохраненные портфели:\n"
                    for portfolio_symbol, portfolio_info in saved_portfolios.items():
                        symbols_str = ', '.join(portfolio_info['symbols'])
                        help_text += f"• `{portfolio_symbol}` - {symbols_str}\n"
                    
                    help_text += "\n💡 Вы можете использовать символы портфелей в сравнении:\n"
                    help_text += "`/compare PF_1 SPY.US` - сравнить ваш портфель с S&P 500\n"
                    help_text += "`/compare PF_1 PF_2` - сравнить два ваших портфеля\n"
                    help_text += "`/compare portfolio_123.PF SPY.US` - сравнить портфель с активом\n\n"
                    help_text += "📋 Для просмотра всех портфелей используйте команду `/my`\n\n"
                
                help_text += "Примеры:\n"
                help_text += "• `/compare SPY.US QQQ.US` - сравнить S&P 500 и NASDAQ (в USD)\n"
                help_text += "• `/compare SBER.MOEX,GAZP.MOEX` - сравнить Сбербанк и Газпром (в RUB)\n"
                help_text += "• `/compare SPY.US, QQQ.US, VOO.US` - сравнить с пробелами после запятых\n"
                help_text += "• `/compare GC.COMM CL.COMM` - сравнить золото и нефть (в USD)\n"
                help_text += "• `/compare VOO.US,BND.US,GC.COMM` - сравнить акции, облигации и золото (в USD)\n\n"
                help_text += "Что вы получите:\n"
                help_text += "✅ График накопленной доходности всех активов\n"
                help_text += "✅ Кнопки для дополнительного анализа:\n"
                help_text += "   📉 Drawdowns - график рисков и волатильности\n"
                help_text += "   💰 Dividends - график дивидендной доходности\n"
                help_text += "   🔗 Correlation Matrix - корреляционная матрица\n"
                help_text += "✅ Сравнительный анализ\n"
                help_text += "✅ AI-рекомендации\n\n"
                help_text += "💡 Автоматическое определение валюты:\n"
                help_text += "• Первый актив в списке определяет базовую валюту\n"
                help_text += "• MOEX активы → RUB, US активы → USD, LSE → GBP\n"
                help_text += "• Остальные → USD по умолчанию\n\n"
                help_text += "📅 Период сравнения:\n"
                help_text += "• Используется полный доступный период данных\n"
                help_text += "• Максимальная глубина исторического анализа\n"
                help_text += "• Покрывает все доступные рыночные циклы\n\n"
                help_text += "Поддерживаемые форматы:\n"
                help_text += "• US акции: AAPL.US, VOO.US, SPY.US\n"
                help_text += "• MOEX: SBER.MOEX, GAZP.MOEX\n"
                help_text += "• Индексы: SPX.INDX, IXIC.INDX\n"
                help_text += "• Товары: GC.COMM, CL.COMM, SI.COMM\n"
                help_text += "• Валюты: EURUSD.FX, GBPUSD.FX"
                
                await self._send_message_safe(update, help_text)
                return

            # Extract symbols from command arguments
            # Support multiple formats: space-separated, comma-separated, and comma+space
            raw_args = ' '.join(context.args)  # Join all arguments into one string
            
            # Enhanced parsing logic for multiple formats
            if ',' in raw_args:
                # Handle comma-separated symbols (with or without spaces)
                # Split by comma and clean each symbol
                symbols = []
                for symbol_part in raw_args.split(','):
                    # Handle cases like "SPY.US, QQQ.US" (comma + space)
                    symbol_part = symbol_part.strip()
                    if symbol_part:  # Only add non-empty symbols
                        # Preserve original case for portfolio symbols, uppercase for regular assets
                        if any(portfolio_indicator in symbol_part.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                            symbols.append(symbol_part)  # Keep original case for portfolios
                        else:
                            symbols.append(symbol_part.upper())  # Uppercase for regular assets
                self.logger.info(f"Parsed comma-separated symbols: {symbols}")
            else:
                # Handle space-separated symbols (original behavior)
                symbols = []
                for symbol in context.args:
                    # Preserve original case for portfolio symbols, uppercase for regular assets
                    if any(portfolio_indicator in symbol.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        symbols.append(symbol)  # Keep original case for portfolios
                    else:
                        symbols.append(symbol.upper())  # Uppercase for regular assets
                self.logger.info(f"Parsed space-separated symbols: {symbols}")
            
            # Clean up symbols (remove empty strings and whitespace)
            symbols = [symbol for symbol in symbols if symbol.strip()]
            
            if len(symbols) < 2:
                await self._send_message_safe(update, "❌ Необходимо указать минимум 2 символа для сравнения")
                return
            
            if len(symbols) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 символов для сравнения")
                return

            # Process portfolio symbols and expand them
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            # Log saved portfolios for debugging
            self.logger.info(f"User {user_id} has {len(saved_portfolios)} saved portfolios: {list(saved_portfolios.keys())}")
            
            expanded_symbols = []
            portfolio_descriptions = []
            
            for symbol in symbols:
                # Log symbol being processed for debugging
                self.logger.info(f"Processing symbol: '{symbol}'")
                
                # Check if this is a saved portfolio symbol (various formats)
                is_portfolio = (
                    (symbol.startswith('PORTFOLIO_') or 
                     symbol.startswith('PF_') or 
                     symbol.startswith('portfolio_') or
                     symbol.endswith('.PF') or
                     symbol.endswith('.pf')) and 
                    symbol in saved_portfolios
                )
                
                self.logger.info(f"Symbol '{symbol}' is_portfolio: {is_portfolio}, in saved_portfolios: {symbol in saved_portfolios}")
                
                if is_portfolio:
                    # This is a saved portfolio, expand it
                    portfolio_info = saved_portfolios[symbol]
                    
                    # Ensure we have the correct portfolio symbol from context
                    portfolio_symbol = portfolio_info.get('portfolio_symbol', symbol)
                    portfolio_symbols = portfolio_info['symbols']
                    portfolio_weights = portfolio_info['weights']
                    portfolio_currency = portfolio_info['currency']
                    
                    # Validate portfolio data
                    if not portfolio_symbols or not portfolio_weights:
                        self.logger.error(f"Invalid portfolio data for {symbol}: missing symbols or weights")
                        await self._send_message_safe(update, f"❌ Ошибка: неполные данные портфеля {symbol}")
                        return
                    
                    if len(portfolio_symbols) != len(portfolio_weights):
                        self.logger.error(f"Portfolio {symbol} has mismatched symbols and weights")
                        await self._send_message_safe(update, f"❌ Ошибка: несоответствие символов и весов в портфеле {symbol}")
                        return
                    
                    # Create portfolio using okama
                    try:
                        portfolio = ok.Portfolio(portfolio_symbols, ccy=portfolio_currency, weights=portfolio_weights)
                        
                        # Add portfolio wealth index to expanded symbols
                        expanded_symbols.append(portfolio.wealth_index)
                        
                        # Use the original symbol for description to maintain consistency
                        portfolio_descriptions.append(f"{symbol} ({', '.join(portfolio_symbols)})")
                        
                        self.logger.info(f"Expanded portfolio {symbol} with {len(portfolio_symbols)} assets")
                        self.logger.info(f"Portfolio currency: {portfolio_currency}, weights: {portfolio_weights}")
                        self.logger.info(f"DEBUG: Added portfolio description: '{symbol} ({', '.join(portfolio_symbols)})'")
                        
                    except Exception as e:
                        self.logger.error(f"Error expanding portfolio {symbol}: {e}")
                        await self._send_message_safe(update, f"❌ Ошибка при обработке портфеля {symbol}: {str(e)}")
                        return
                else:
                    # Regular asset symbol
                    expanded_symbols.append(symbol)
                    portfolio_descriptions.append(symbol)
            
            # Update symbols list with expanded portfolio descriptions
            symbols = portfolio_descriptions
            
            # Debug logging for symbols and expanded_symbols
            self.logger.info(f"DEBUG: portfolio_descriptions: {portfolio_descriptions}")
            self.logger.info(f"DEBUG: symbols after update: {symbols}")
            self.logger.info(f"DEBUG: expanded_symbols types: {[type(s) for s in expanded_symbols]}")
            self.logger.info(f"DEBUG: expanded_symbols values: {expanded_symbols}")
            
            # Additional debug: check for any problematic symbols
            for i, desc in enumerate(portfolio_descriptions):
                self.logger.info(f"DEBUG: portfolio_descriptions[{i}]: '{desc}'")
            for i, exp_sym in enumerate(expanded_symbols):
                self.logger.info(f"DEBUG: expanded_symbols[{i}]: '{exp_sym}' (type: {type(exp_sym)})")
            
            await self._send_message_safe(update, f"🔄 Сравниваю активы: {', '.join(symbols)}...")

            # Create comparison using okama
            
            # Determine base currency from the first asset
            first_symbol = symbols[0]
            currency_info = ""
            try:
                # Extract the original symbol from the description (remove the asset list part)
                original_first_symbol = first_symbol.split(' (')[0] if ' (' in first_symbol else first_symbol
                
                # Check if first symbol is a portfolio symbol
                is_first_portfolio = (
                    (original_first_symbol.startswith('PORTFOLIO_') or 
                     original_first_symbol.startswith('PF_') or 
                     original_first_symbol.startswith('portfolio_') or
                     original_first_symbol.endswith('.PF') or
                     original_first_symbol.endswith('.pf')) and 
                    original_first_symbol in saved_portfolios
                )
                
                if is_first_portfolio:
                    # First symbol is a portfolio, use its currency
                    portfolio_info = saved_portfolios[original_first_symbol]
                    currency = portfolio_info.get('currency', 'USD')
                    currency_info = f"автоматически определена по портфелю ({original_first_symbol})"
                    self.logger.info(f"Using portfolio currency for {original_first_symbol}: {currency}")
                else:
                    # Try to get currency info for the first asset
                    if '.' in first_symbol:
                        namespace = first_symbol.split('.')[1]
                        if namespace == 'MOEX':
                            currency = "RUB"  # Russian assets in RUB
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        elif namespace == 'US':
                            currency = "USD"  # US assets in USD
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        elif namespace == 'LSE':
                            currency = "GBP"  # London assets in GBP
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        elif namespace == 'FX':
                            currency = "USD"  # Forex pairs in USD
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        elif namespace == 'COMM':
                            currency = "USD"  # Commodities in USD
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        elif namespace == 'INDX':
                            currency = "USD"  # Indices in USD
                            currency_info = f"автоматически определена по первому активу ({first_symbol})"
                        else:
                            currency = "USD"  # Default to USD
                            currency_info = "по умолчанию (USD)"
                    else:
                        currency = "USD"  # Default to USD
                        currency_info = "по умолчанию (USD)"
                    
                    self.logger.info(f"Auto-detected currency for {first_symbol}: {currency}")
                
            except Exception as e:
                self.logger.warning(f"Could not auto-detect currency, using USD: {e}")
                currency = "USD"
                currency_info = "по умолчанию (USD)"
            
            try:
                # Check if we have portfolios in the comparison (wealth indexes can be Series or single-column DataFrames)
                has_portfolios = any(isinstance(symbol, (pd.Series, pd.DataFrame)) for symbol in expanded_symbols)
                
                if has_portfolios:
                    # We have portfolios, need to create custom comparison
                    self.logger.info("Creating custom comparison with portfolios")
                    
                    # Get the first regular asset to determine currency if no portfolios
                    first_regular_symbol = None
                    for symbol in expanded_symbols:
                        if not isinstance(symbol, (pd.Series, pd.DataFrame)):
                            first_regular_symbol = symbol
                            break
                    
                    # Determine currency from first regular asset or portfolio
                    if first_regular_symbol:
                        if '.' in first_regular_symbol:
                            namespace = first_regular_symbol.split('.')[1]
                            if namespace == 'MOEX':
                                currency = "RUB"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            elif namespace == 'US':
                                currency = "USD"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            elif namespace == 'LSE':
                                currency = "GBP"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            elif namespace == 'FX':
                                currency = "USD"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            elif namespace == 'COMM':
                                currency = "USD"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            elif namespace == 'INDX':
                                currency = "USD"
                                currency_info = f"автоматически определена по первому активу ({first_regular_symbol})"
                            else:
                                currency = "USD"
                                currency_info = "по умолчанию (USD)"
                        else:
                            currency = "USD"
                            currency_info = "по умолчанию (USD)"
                    else:
                        # All are portfolios, use USD as default
                        currency = "USD"
                        currency_info = "по умолчанию (USD)"
                    
                    # Create custom wealth index DataFrame
                    wealth_data = {}
                    
                    # Debug logging for expanded_symbols
                    self.logger.info(f"DEBUG: Processing expanded_symbols: {expanded_symbols}")
                    self.logger.info(f"DEBUG: expanded_symbols types: {[type(s) for s in expanded_symbols]}")
                    
                    for i, symbol in enumerate(expanded_symbols):
                        self.logger.info(f"DEBUG: Processing index {i}: symbol='{symbol}' (type: {type(symbol)})")
                        
                        if isinstance(symbol, (pd.Series, pd.DataFrame)):
                            # Portfolio wealth index (Series or single-column DataFrame)
                            self.logger.info(f"DEBUG: Found portfolio pandas object at index {i}")
                            try:
                                if isinstance(symbol, pd.DataFrame):
                                    self.logger.info(f"DEBUG: Portfolio wealth index is DataFrame with shape {symbol.shape}")
                                    squeezed = symbol.squeeze()
                                    if isinstance(squeezed, pd.DataFrame):
                                        # Fallback: take the first column explicitly
                                        squeezed = symbol.iloc[:, 0]
                                    wealth_series = squeezed
                                else:
                                    wealth_series = symbol
                                wealth_data[symbols[i]] = wealth_series
                            except Exception as conv_err:
                                self.logger.error(f"Failed to convert portfolio wealth index to Series: {conv_err}")
                                await self._send_message_safe(update, f"❌ Ошибка при обработке портфеля {symbols[i]}: {str(conv_err)}")
                                return
                        else:
                            # Regular asset, need to get its wealth index
                            self.logger.info(f"DEBUG: Found regular asset at index {i}: '{symbol}'")
                            try:
                                # Log the current symbol being processed
                                self.logger.info(f"Processing regular asset: '{symbol}' from symbols[{i}] = '{symbols[i]}'")
                                self.logger.info(f"DEBUG: symbol type: {type(symbol)}, symbol value: '{symbol}'")
                                self.logger.info(f"DEBUG: symbols[{i}] type: {type(symbols[i])}, symbols[{i}] value: '{symbols[i]}'")
                                
                                # Use the currency from the portfolio if available, otherwise use detected currency
                                asset_currency = currency
                                
                                # Check if we have any portfolios in the comparison
                                has_portfolios_in_comparison = any(isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols)
                                
                                if has_portfolios_in_comparison:
                                    # Find the first portfolio symbol to use its currency
                                    portfolio_symbol = None
                                    for j, orig_symbol in enumerate(symbols):
                                        if isinstance(expanded_symbols[j], (pd.Series, pd.DataFrame)):
                                            # Extract the original symbol from the description
                                            original_symbol = orig_symbol.split(' (')[0] if ' (' in orig_symbol else orig_symbol
                                            portfolio_symbol = original_symbol
                                            self.logger.info(f"Found portfolio symbol: '{portfolio_symbol}' from description: '{orig_symbol}'")
                                            break
                                    
                                    if portfolio_symbol and portfolio_symbol in saved_portfolios:
                                        portfolio_info = saved_portfolios[portfolio_symbol]
                                        asset_currency = portfolio_info.get('currency', currency)
                                        self.logger.info(f"Using portfolio currency {asset_currency} for asset {symbol}")
                                    else:
                                        # Fallback to detected currency
                                        asset_currency = currency
                                        self.logger.info(f"Using detected currency {asset_currency} for asset {symbol}")
                                else:
                                    # No portfolios, use detected currency
                                    asset_currency = currency
                                
                                # Log the symbol being processed for debugging
                                self.logger.info(f"Processing asset symbol: '{symbol}' with currency: {asset_currency}")
                                self.logger.info(f"DEBUG: About to create Asset with symbol: '{symbol}'")
                                
                                # Validate symbol format before creating Asset
                                if not symbol or symbol.strip() == '':
                                    self.logger.error(f"Empty or invalid symbol: '{symbol}'")
                                    await self._send_message_safe(update, f"❌ Ошибка: неверный символ актива '{symbol}'")
                                    return
                                
                                # Check for invalid characters that indicate extraction error
                                invalid_chars = ['(', ')', ',']
                                if any(char in symbol for char in invalid_chars):
                                    self.logger.error(f"Symbol contains invalid characters: '{symbol}' - extraction error detected")
                                    await self._send_message_safe(update, f"❌ Ошибка: символ содержит недопустимые символы '{symbol}' - ошибка извлечения")
                                    return
                                
                                # Check for proper symbol format (must contain namespace separator)
                                if '.' not in symbol:
                                    self.logger.error(f"Symbol missing namespace separator: '{symbol}'")
                                    await self._send_message_safe(update, f"❌ Ошибка: символ не содержит разделитель пространства имен '{symbol}'")
                                    return
                                
                                self.logger.info(f"DEBUG: Symbol validation passed, creating Asset with: '{symbol}'")
                                self.logger.info(f"DEBUG: About to call ok.Asset('{symbol}', ccy='{asset_currency}')")
                                try:
                                    asset = ok.Asset(symbol, ccy=asset_currency)
                                    self.logger.info(f"DEBUG: Successfully created Asset for '{symbol}'")
                                except Exception as asset_error:
                                    self.logger.error(f"DEBUG: Failed to create Asset for '{symbol}': {asset_error}")
                                    raise asset_error
                                wealth_data[symbols[i]] = asset.wealth_index
                            except Exception as e:
                                self.logger.error(f"Error getting wealth index for {symbol}: {e}")
                                await self._send_message_safe(update, f"❌ Ошибка при получении данных для {symbol}: {str(e)}")
                                return
                    
                    # Create DataFrame from wealth data
                    wealth_df = pd.DataFrame(wealth_data)
                    
                    # Generate beautiful comparison chart using chart_styles
                    fig, ax = chart_styles.create_comparison_chart(
                        data=wealth_df,
                        symbols=symbols,
                        currency=currency
                    )
                    
                else:
                    # Regular assets only, use AssetList
                    # Use raw parsed tickers (expanded_symbols) for okama, not display descriptions
                    asset_list = ok.AssetList(expanded_symbols, ccy=currency)
                    self.logger.info("Created AssetList with full available period")
                    
                    # Generate beautiful comparison chart using chart_styles
                    fig, ax = chart_styles.create_comparison_chart(
                        data=asset_list.wealth_indexes,
                        symbols=symbols,
                        currency=currency
                    )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Get basic statistics
                stats_text = f"📊 Сравнение: {', '.join(symbols)}\n\n"
                stats_text += f"💰 Базовая валюта: {currency} ({currency_info})\n"
                
                if has_portfolios:
                    # Get statistics from wealth_df for portfolios
                    try:
                        first_date = wealth_df.index[0]
                        last_date = wealth_df.index[-1]
                        period_length = last_date - first_date
                        
                        stats_text += f"📅 Период: {first_date} - {last_date}\n"
                        stats_text += f"⏱️ Длительность: {period_length}\n\n"
                        
                        # Calculate and show final returns
                        final_values = wealth_df.iloc[-1]
                        stats_text += f"📈 Накопленная доходность ({currency}):\n"
                        for symbol in symbols:
                            if symbol in final_values:
                                value = final_values[symbol]
                                stats_text += f"• {symbol}: {value:.2f}\n"
                    except Exception as e:
                        self.logger.warning(f"Could not get portfolio statistics: {e}")
                        stats_text += "📅 Период: недоступен\n⏱️ Длительность: недоступна\n\n"
                else:
                    # Regular assets, use asset_list
                    stats_text += f"📅 Период: {asset_list.first_date} - {asset_list.last_date}\n"
                    
                    # Safely handle period_length which might be a Period object
                    try:
                        period_length = asset_list.period_length
                        if hasattr(period_length, 'strftime'):
                            # If it's a datetime-like object
                            period_length_str = str(period_length)
                        elif hasattr(period_length, 'days'):
                            # If it's a timedelta-like object
                            period_length_str = str(period_length)
                        elif hasattr(period_length, 'to_timestamp'):
                            # If it's a Period object
                            period_length_str = str(period_length)
                        else:
                            # Try to convert to string directly
                            period_length_str = str(period_length)
                        stats_text += f"⏱️ Длительность: {period_length_str}\n\n"
                    except Exception as e:
                        self.logger.warning(f"Could not get period length: {e}")
                        stats_text += "⏱️ Длительность: недоступна\n\n"
                    
                    # Get asset names
                    if hasattr(asset_list, 'names') and asset_list.names:
                        stats_text += "📋 Названия активов:\n"
                        for symbol, name in asset_list.names.items():
                            stats_text += f"• {symbol} - {name}\n"
                        stats_text += "\n"
                    
                    # Calculate and show final returns
                    try:
                        final_values = asset_list.wealth_indexes.iloc[-1]
                        stats_text += f"📈 Накопленная доходность ({currency}):\n"
                        for symbol in symbols:
                            if symbol in final_values:
                                value = final_values[symbol]
                                stats_text += f"• {symbol}: {value:.2f}\n"
                    except Exception as e:
                        self.logger.warning(f"Could not get final values: {e}")
                
                # Send text report
                # await self.send_long_message(update, stats_text)
                
                # Send chart image with buttons
                keyboard = [
                    [
                        InlineKeyboardButton("📉 Drawdowns", callback_data=f"drawdowns_{','.join(symbols)}"),
                        InlineKeyboardButton("💰 Dividends", callback_data=f"dividends_{','.join(symbols)}")
                    ],
                    [
                        InlineKeyboardButton("🔗 Correlation Matrix", callback_data=f"correlation_{','.join(symbols)}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(stats_text),
                    reply_markup=reply_markup
                )
                
                # Store asset_list in context for button callbacks
                user_id = update.effective_user.id
                self._update_user_context(
                    user_id, 
                    last_assets=symbols,
                    last_analysis_type='comparison',
                    last_period='MAX',
                    current_symbols=symbols,
                    current_currency=currency,
                    current_currency_info=currency_info
                )
                
            except Exception as e:
                self.logger.error(f"Error creating comparison: {e}")
                await self._send_message_safe(update, 
                    f"❌ Ошибка при создании сравнения: {str(e)}\n\n"
                    "💡 Возможные причины:\n"
                    "• Один из символов недоступен\n"
                    "• Проблемы с данными MOEX\n"
                    "• Неверный формат символа\n\n"
                    "Проверьте:\n"
                    "• Правильность написания символов\n"
                    "• Доступность данных для указанных активов"
                )
                
        except Exception as e:
            self.logger.error(f"Error in compare command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при выполнении команды сравнения: {str(e)}")

    async def my_portfolios_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /my command for displaying saved portfolios"""
        try:
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if not saved_portfolios:
                await self._send_message_safe(update, 
                    "💼 У вас пока нет сохраненных портфелей\n\n"
                    "Создайте портфель командой:\n"
                    "`/portfolio символ1:доля1 символ2:доля2 ...`\n\n"
                    "Пример:\n"
                    "`/portfolio SPY.US:0.6 QQQ.US:0.4`"
                )
                return
            
            # Create comprehensive portfolio list
            portfolio_list = "💼 Ваши сохраненные портфели:\n\n"
            
            for portfolio_symbol, portfolio_info in saved_portfolios.items():
                portfolio_list += f"🏷️ **{portfolio_symbol}**\n"
                
                # Basic info
                symbols = portfolio_info.get('symbols', [])
                weights = portfolio_info.get('weights', [])
                currency = portfolio_info.get('currency', 'N/A')
                created_at = portfolio_info.get('created_at', 'N/A')
                
                portfolio_list += f"📊 Состав: {', '.join(symbols)}\n"
                
                # Weights breakdown
                if symbols and weights and len(symbols) == len(weights):
                    portfolio_list += "💰 Доли:\n"
                    for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                        portfolio_list += f"   • {symbol}: {weight:.1%}\n"
                
                portfolio_list += f"💱 Валюта: {currency}\n"
                
                # Performance metrics if available
                if 'mean_return_annual' in portfolio_info:
                    portfolio_list += f"📈 Годовая доходность: {portfolio_info['mean_return_annual']:.2%}\n"
                if 'volatility_annual' in portfolio_info:
                    portfolio_list += f"📉 Годовая волатильность: {portfolio_info['volatility_annual']:.2%}\n"
                if 'sharpe_ratio' in portfolio_info:
                    portfolio_list += f"⚡ Коэффициент Шарпа: {portfolio_info['sharpe_ratio']:.2f}\n"
                
                # Dates if available
                if 'first_date' in portfolio_info and 'last_date' in portfolio_info:
                    portfolio_list += f"📅 Период: {portfolio_info['first_date']} - {portfolio_info['last_date']}\n"
                
                # Final value if available
                if 'final_value' in portfolio_info and portfolio_info['final_value'] is not None:
                    portfolio_list += f"💵 Финальная стоимость: {portfolio_info['final_value']:.2f} {currency}\n"
                
                portfolio_list += f"🕐 Создан: {created_at}\n"
                portfolio_list += "\n" + "─" * 40 + "\n\n"
            
                            # Add usage instructions
                portfolio_list += "💡 **Использование в сравнении:**\n"
                portfolio_list += "• `/compare PF_1 SPY.US` - сравнить портфель с активом\n"
                portfolio_list += "• `/compare PF_1 PF_2` - сравнить два портфеля\n"
                portfolio_list += "• `/compare PF_1 SPY.US QQQ.US` - смешанное сравнение\n"
                portfolio_list += "• `/compare portfolio_123.PF SPY.US` - сравнить портфель с активом\n\n"
                
                portfolio_list += "🔧 **Управление:**\n"
                portfolio_list += "• Портфели автоматически сохраняются при создании\n"
                portfolio_list += "• Используйте символы для сравнения и анализа\n"
                portfolio_list += "• Все данные сохраняются в контексте сессии\n\n"
                
                # Create keyboard with clear portfolios button
                keyboard = [
                    [InlineKeyboardButton("🗑️ Очистить все портфели", callback_data="clear_all_portfolios")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send the portfolio list with clear button
                await self._send_message_safe(update, portfolio_list, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            self.logger.error(f"Error in my portfolios command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при получении списка портфелей: {str(e)}")

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command for creating portfolio with weights"""
        try:
            if not context.args:
                await self._send_message_safe(update, 
                    "📊 Команда /portfolio - Создание портфеля\n\n"
                    "Использование:\n"
                    "`/portfolio символ1:доля1 символ2:доля2 символ3:доля3 ...`\n\n"
                    "Примеры:\n"
                    "• `/portfolio SPY.US:0.5 QQQ.US:0.3 BND.US:0.2` - портфель 50% S&P 500, 30% NASDAQ, 20% облигации\n"
                    "• `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3` - российский портфель\n"
                    "• `/portfolio VOO.US:0.6 GC.COMM:0.2 BND.US:0.2` - портфель с золотом\n\n"
                    "💡 Важные моменты:\n"
                    "• Доли должны суммироваться в 1.0 (100%)\n"
                    "• Базовая валюта определяется по первому символу\n"
                    "• Поддерживаются все типы активов: акции, облигации, товары, индексы\n\n"
                    "Что вы получите:\n"
                    "✅ График накопленной доходности портфеля\n"
                    "✅ Таблица активов с весами\n"
                    "✅ Основные характеристики портфеля\n"
                )
                return

            # Extract symbols and weights from command arguments
            raw_args = ' '.join(context.args)
            portfolio_data = []
            
            for arg in raw_args.split():
                if ':' in arg:
                    symbol_part, weight_part = arg.split(':', 1)
                    original_symbol = symbol_part.strip()
                    # Преобразуем символ в верхний регистр
                    symbol = original_symbol.upper()
                    
                    try:
                        weight_str = weight_part.strip()
                        self.logger.info(f"DEBUG: Converting weight '{weight_str}' to float for symbol '{symbol}'")
                        weight = float(weight_str)
                    except Exception as e:
                        self.logger.error(f"Error converting weight '{weight_part.strip()}' to float: {e}")
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: '{weight_part.strip()}'. Доля должна быть числом от 0 до 1")
                        return
                    
                    if weight <= 0 or weight > 1:
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: {weight}. Доля должна быть от 0 до 1")
                        return
                    
                    portfolio_data.append((symbol, weight))
                    
                else:
                    await self._send_message_safe(update, f"❌ Некорректный формат: {arg}. Используйте формат символ:доля")
                    return
            
            if not portfolio_data:
                await self._send_message_safe(update, "❌ Не указаны активы для портфеля")
                return
            
            # Check if weights sum to approximately 1.0
            total_weight = sum(weight for _, weight in portfolio_data)
            if abs(total_weight - 1.0) > 0.01:
                # Предлагаем исправление, если сумма близка к 1
                if abs(total_weight - 1.0) <= 0.1:
                    corrected_weights = []
                    for symbol, weight in portfolio_data:
                        corrected_weight = weight / total_weight
                        corrected_weights.append((symbol, corrected_weight))
                    
                    await self._send_message_safe(update, 
                        f"⚠️ Сумма долей ({total_weight:.3f}) не равна 1.0\n\n"
                        f"Исправленные доли:\n"
                        f"{chr(10).join([f'• {symbol}: {weight:.3f}' for symbol, weight in corrected_weights])}\n\n"
                        f"Попробуйте команду:\n"
                        f"`/portfolio {' '.join([f'{symbol}:{weight:.3f}' for symbol, weight in corrected_weights])}`"
                    )
                else:
                    await self._send_message_safe(update, 
                        f"❌ Сумма долей должна быть равна 1.0, текущая сумма: {total_weight:.3f}\n\n"
                        f"Пример правильной команды:\n"
                        f"`/portfolio LQDT.MOEX:0.78 OBLG.MOEX:0.16 GOLD.MOEX:0.06`"
                    )
                return
            
            if len(portfolio_data) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 активов в портфеле")
                return
            
            symbols = [symbol for symbol, _ in portfolio_data]
            weights = [weight for _, weight in portfolio_data]
            
            await self._send_message_safe(update, f"🔄 Создаю портфель: {', '.join(symbols)}...")
            
            # Create portfolio using okama
            
            self.logger.info(f"DEBUG: About to create portfolio with symbols: {symbols}, weights: {weights}")
            self.logger.info(f"DEBUG: Symbols types: {[type(s) for s in symbols]}")
            self.logger.info(f"DEBUG: Weights types: {[type(w) for w in weights]}")
            
            # Determine base currency from the first asset
            first_symbol = symbols[0]
            currency_info = ""
            try:
                if '.' in first_symbol:
                    namespace = first_symbol.split('.')[1]
                    if namespace == 'MOEX':
                        currency = "RUB"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'US':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'LSE':
                        currency = "GBP"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'FX':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'COMM':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'INDX':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    else:
                        currency = "USD"
                        currency_info = "по умолчанию (USD)"
                else:
                    currency = "USD"
                    currency_info = "по умолчанию (USD)"
                
                self.logger.info(f"Auto-detected currency for portfolio {first_symbol}: {currency}")
                
            except Exception as e:
                self.logger.warning(f"Could not auto-detect currency, using USD: {e}")
                currency = "USD"
                currency_info = "по умолчанию (USD)"
            
            try:
                # Final validation of weights before creating portfolio
                final_total = sum(weights)
                if abs(final_total - 1.0) > 0.001:
                    await self._send_message_safe(update, 
                        f"❌ Ошибка валидации весов: сумма {final_total:.6f} не равна 1.0\n"
                        f"Веса: {', '.join([f'{w:.6f}' for w in weights])}"
                    )
                    return
                
                # Create Portfolio with detected currency
                try:
                    self.logger.info(f"DEBUG: About to create ok.Portfolio with symbols={symbols}, ccy={currency}, weights={weights}")
                    self.logger.info(f"DEBUG: Symbols types: {[type(s) for s in symbols]}")
                    self.logger.info(f"DEBUG: Weights types: {[type(w) for w in weights]}")
                    portfolio = ok.Portfolio(symbols, ccy=currency, weights=weights)
                    self.logger.info(f"DEBUG: Successfully created portfolio")
                except Exception as e:
                    self.logger.error(f"DEBUG: Error creating portfolio: {e}")
                    self.logger.error(f"DEBUG: Error type: {type(e)}")
                    raise e
                
                self.logger.info(f"Created Portfolio with weights: {weights}, total: {sum(weights):.6f}")
                
                # Generate beautiful portfolio chart using chart_styles
                wealth_index = portfolio.wealth_index
                
                # Create portfolio chart with chart_styles using optimized method
                fig, ax = chart_styles.create_portfolio_wealth_chart(
                    data=wealth_index, symbols=symbols, currency=currency
                )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Get portfolio information
                portfolio_text = f"📊 Портфель: {', '.join(symbols)}\n\n"
                portfolio_text += f"💰 Базовая валюта: {currency} ({currency_info})\n"
                
                # Safely get first and last dates
                try:
                    first_date = portfolio.first_date
                    last_date = portfolio.last_date
                    
                    # Handle Period objects and other date types
                    if hasattr(first_date, 'strftime'):
                        first_date_str = first_date.strftime('%Y-%m-%d')
                    elif hasattr(first_date, 'to_timestamp'):
                        first_date_str = first_date.to_timestamp().strftime('%Y-%m-%d')
                    else:
                        first_date_str = str(first_date)
                    
                    if hasattr(last_date, 'strftime'):
                        last_date_str = last_date.strftime('%Y-%m-%d')
                    elif hasattr(last_date, 'to_timestamp'):
                        last_date_str = last_date.to_timestamp().strftime('%Y-%m-%d')
                    else:
                        last_date_str = str(last_date)
                    
                    portfolio_text += f"📅 Период: {first_date_str} - {last_date_str}\n"
                except Exception as e:
                    self.logger.warning(f"Could not get portfolio dates: {e}")
                    portfolio_text += "📅 Период: недоступен\n"
                
                # Safely get period length
                try:
                    period_length = portfolio.period_length
                    
                    if hasattr(period_length, 'strftime'):
                        # If it's a datetime-like object
                        period_length_str = str(period_length)
                    elif hasattr(period_length, 'days'):
                        # If it's a timedelta-like object
                        period_length_str = str(period_length)
                    elif hasattr(period_length, 'to_timestamp'):
                        # If it's a Period object
                        period_length_str = str(period_length)
                    else:
                        # Try to convert to string directly
                        period_length_str = str(period_length)
                    
                    portfolio_text += f"⏱️ Длительность: {period_length_str}\n\n"
                except Exception as e:
                    self.logger.warning(f"Could not get period length: {e}")
                    portfolio_text += "⏱️ Длительность: недоступна\n\n"
                
                # Show portfolio table
                portfolio_text += "📋 Состав портфеля:\n"
                if hasattr(portfolio, 'table') and not portfolio.table.empty:
                    for _, row in portfolio.table.iterrows():
                        symbol = row['ticker']
                        weight = weights[symbols.index(symbol)]
                        name = row.get('asset name', symbol)
                        portfolio_text += f"• {symbol} ({name}): {weight:.1%}\n"
                else:
                    # Fallback if table is not available
                    for symbol, weight in portfolio_data:
                        portfolio_text += f"• {symbol}: {weight:.1%}\n"
                
                # Get final portfolio value safely
                try:
                    final_value = portfolio.wealth_index.iloc[-1]
                    self.logger.info(f"Final value type: {type(final_value)}, value: {final_value}")
                    
                    # Log wealth_index info for debugging
                    self.logger.info(f"Wealth index type: {type(portfolio.wealth_index)}")
                    self.logger.info(f"Wealth index shape: {portfolio.wealth_index.shape if hasattr(portfolio.wealth_index, 'shape') else 'No shape'}")
                    self.logger.info(f"Wealth index last few values: {portfolio.wealth_index.tail(3).tolist() if hasattr(portfolio.wealth_index, 'tail') else 'No tail method'}")
                    
                    # Handle different types of final_value
                    if hasattr(final_value, '__iter__') and not isinstance(final_value, str):
                        # If it's a Series or array-like, get the first value
                        if hasattr(final_value, 'iloc'):
                            final_value = final_value.iloc[0]
                        elif hasattr(final_value, '__getitem__'):
                            final_value = final_value[0]
                        else:
                            final_value = list(final_value)[0]
                    
                    # Handle Period objects and other special types
                    if hasattr(final_value, 'to_timestamp'):
                        # If it's a Period object, convert to timestamp first
                        try:
                            final_value = final_value.to_timestamp()
                        except Exception:
                            # If to_timestamp fails, try to convert to string first
                            if hasattr(final_value, 'strftime'):
                                final_value = str(final_value)
                            else:
                                final_value = str(final_value)
                    
                    # Handle Timestamp objects and other datetime-like objects
                    if hasattr(final_value, 'timestamp'):
                        try:
                            final_value = final_value.timestamp()
                        except Exception:
                            final_value = str(final_value)
                    
                    # Convert to float safely
                    if isinstance(final_value, (int, float)):
                        final_value = float(final_value)
                    else:
                        # Try to convert to string first, then to float
                        final_value_str = str(final_value)
                        try:
                            final_value = float(final_value_str)
                        except (ValueError, TypeError):
                            import re
                            numeric_match = re.search(r'[\d.]+', final_value_str)
                            if numeric_match:
                                final_value = float(numeric_match.group())
                            else:
                                raise ValueError(f"Cannot convert {final_value} to float")
                    
                    portfolio_text += f"\n📈 Накопленная доходность портфеля: {final_value:.2f} {currency}"
                except Exception as e:
                    self.logger.warning(f"Could not get final portfolio value: {e}")
                    # Try to get mean annual return instead
                    try:
                        mean_return_annual = portfolio.mean_return_annual
                        portfolio_text += f"\n📈 Средняя годовая доходность: {mean_return_annual:.2%}"
                    except Exception as e2:
                        self.logger.warning(f"Could not get mean annual return: {e2}")
                        portfolio_text += f"\n📈 Накопленная доходность портфеля: недоступна"
                
                # Generate portfolio symbol using PF namespace and okama's assigned symbol
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                
                # Count existing portfolios for this user
                portfolio_count = user_context.get('portfolio_count', 0) + 1
                
                # Use PF namespace with okama's assigned symbol
                try:
                    # Get the portfolio symbol that okama assigned
                    if hasattr(portfolio, 'symbol'):
                        portfolio_symbol = portfolio.symbol
                    else:
                        # Fallback to custom symbol if okama doesn't provide one
                        portfolio_symbol = f"PF_{portfolio_count}"
                except Exception as e:
                    self.logger.warning(f"Could not get okama portfolio symbol: {e}")
                    portfolio_symbol = f"PF_{portfolio_count}"
                
                # Create compact portfolio data string for callback (only symbols to avoid Button_data_invalid)
                portfolio_data_str = ','.join(symbols)
                
                # Add portfolio symbol display under the chart
                portfolio_text += f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}` (namespace PF)\n"
                portfolio_text += f"💾 Портфель сохранен в контексте для использования в /compare"
                
                # Add risk metrics, Monte Carlo, forecast, and drawdowns buttons
                keyboard = [
                    [InlineKeyboardButton("💰 Доходность", callback_data=f"returns_{portfolio_data_str}")],
                    [InlineKeyboardButton("📉 Просадки", callback_data=f"drawdowns_{portfolio_data_str}")],
                    [InlineKeyboardButton("📊 Риск метрики", callback_data=f"risk_metrics_{portfolio_data_str}")],
                    [InlineKeyboardButton("🎲 Монте Карло", callback_data=f"monte_carlo_{portfolio_data_str}")],
                    [InlineKeyboardButton("📈 Процентили 10, 50, 90", callback_data=f"forecast_{portfolio_data_str}")],
                    [InlineKeyboardButton("📊 Портфель vs Активы", callback_data=f"compare_assets_{portfolio_data_str}")],
                    [InlineKeyboardButton("📈 Rolling CAGR", callback_data=f"rolling_cagr_{portfolio_data_str}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send portfolio chart and information with buttons
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(portfolio_text),
                    reply_markup=reply_markup
                )
                
                # Store portfolio data in context
                user_id = update.effective_user.id
                self.logger.info(f"Storing portfolio data in context for user {user_id}")
                self.logger.info(f"Symbols: {symbols}")
                self.logger.info(f"Currency: {currency}")
                self.logger.info(f"Weights: {weights}")
                self.logger.info(f"Portfolio symbol: {portfolio_symbol}")
                
                # Store portfolio information in user context
                self._update_user_context(
                    user_id, 
                    last_assets=symbols,
                    last_analysis_type='portfolio',
                    last_period='MAX',
                    current_symbols=symbols,
                    current_currency=currency,
                    current_currency_info=currency_info,
                    portfolio_weights=weights,
                    portfolio_count=portfolio_count,
                    saved_portfolios=user_context.get('saved_portfolios', {})
                )
                
                # Add current portfolio to saved portfolios with comprehensive data
                saved_portfolios = user_context.get('saved_portfolios', {})
                
                # Get additional portfolio attributes for comprehensive storage
                portfolio_attributes = {}
                try:
                    # Basic portfolio info
                    portfolio_attributes.update({
                        'symbols': symbols,
                        'weights': weights,
                        'currency': currency,
                        'created_at': datetime.now().isoformat(),
                        'description': f"Портфель: {', '.join(symbols)}",
                        'portfolio_symbol': portfolio_symbol,  # Ensure symbol is preserved
                        'total_weight': sum(weights),
                        'asset_count': len(symbols)
                    })
                    
                    # Portfolio performance metrics
                    if hasattr(portfolio, 'mean_return_annual'):
                        try:
                            value = portfolio.mean_return_annual
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['mean_return_annual'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert mean_return_annual to float: {e}")
                            portfolio_attributes['mean_return_annual'] = None
                    
                    if hasattr(portfolio, 'volatility_annual'):
                        try:
                            value = portfolio.volatility_annual
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['volatility_annual'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert volatility_annual to float: {e}")
                            portfolio_attributes['volatility_annual'] = None
                    
                    if hasattr(portfolio, 'sharpe_ratio'):
                        try:
                            value = portfolio.sharpe_ratio
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['sharpe_ratio'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert sharpe_ratio to float: {e}")
                            portfolio_attributes['sharpe_ratio'] = None
                    
                    # Portfolio dates
                    if hasattr(portfolio, 'first_date'):
                        portfolio_attributes['first_date'] = str(portfolio.first_date)
                    if hasattr(portfolio, 'last_date'):
                        portfolio_attributes['last_date'] = str(portfolio.last_date)
                    if hasattr(portfolio, 'period_length'):
                        portfolio_attributes['period_length'] = str(portfolio.period_length)
                    
                    # Final portfolio value
                    try:
                        final_value = portfolio.wealth_index.iloc[-1]
                        if hasattr(final_value, '__iter__') and not isinstance(final_value, str):
                            if hasattr(final_value, 'iloc'):
                                final_value = final_value.iloc[0]
                            elif hasattr(final_value, '__getitem__'):
                                final_value = final_value[0]
                            else:
                                final_value = list(final_value)[0]
                        
                        # Handle Period objects and other non-numeric types
                        if hasattr(final_value, 'to_timestamp'):
                            try:
                                final_value = final_value.to_timestamp()
                            except Exception:
                                # If to_timestamp fails, try to convert to string first
                                if hasattr(final_value, 'strftime'):
                                    final_value = str(final_value)
                                else:
                                    final_value = str(final_value)
                        
                        # Handle Timestamp objects and other datetime-like objects
                        if hasattr(final_value, 'timestamp'):
                            try:
                                final_value = final_value.timestamp()
                            except Exception:
                                final_value = str(final_value)
                        elif not isinstance(final_value, (int, float)):
                            # Try to convert non-numeric values
                            final_value_str = str(final_value)
                            import re
                            match = re.search(r'[\d.-]+', final_value_str)
                            if match:
                                final_value = float(match.group())
                            else:
                                final_value = 0.0
                        
                        portfolio_attributes['final_value'] = float(final_value)
                    except Exception as e:
                        self.logger.warning(f"Could not get final value for storage: {e}")
                        portfolio_attributes['final_value'] = None
                    
                    # Store as JSON string for better compatibility
                    portfolio_json = json.dumps(portfolio_attributes, ensure_ascii=False, default=str)
                    portfolio_attributes['json_data'] = portfolio_json
                    
                except Exception as e:
                    self.logger.warning(f"Could not get all portfolio attributes: {e}")
                    # Fallback to basic storage
                    portfolio_attributes = {
                        'symbols': symbols,
                        'weights': weights,
                        'currency': currency,
                        'created_at': datetime.now().isoformat(),
                        'description': f"Портфель: {', '.join(symbols)}",
                        'portfolio_symbol': portfolio_symbol,
                        'total_weight': sum(weights),
                        'asset_count': len(symbols),
                        'json_data': json.dumps({
                            'symbols': symbols,
                            'weights': weights,
                            'currency': currency,
                            'portfolio_symbol': portfolio_symbol
                        }, ensure_ascii=False)
                    }
                
                saved_portfolios[portfolio_symbol] = portfolio_attributes
                
                # Update saved portfolios in context
                self._update_user_context(
                    user_id,
                    saved_portfolios=saved_portfolios
                )
                
                # Verify context was saved
                saved_context = self._get_user_context(user_id)
                self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
                self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
                self.logger.info(f"Saved last_assets: {saved_context.get('last_assets')}")
                self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
                
            except Exception as e:
                self.logger.error(f"Error creating portfolio: {e}")
                await self._send_message_safe(update, 
                    f"❌ Ошибка при создании портфеля: {str(e)}\n\n"
                    "💡 Возможные причины:\n"
                    "• Один из символов недоступен\n"
                    "• Проблемы с данными\n"
                    "• Неверный формат символа\n\n"
                    "Проверьте:\n"
                    "• Правильность написания символов\n"
                    "• Доступность данных для указанных активов"
                )
                
        except Exception as e:
            self.logger.error(f"Error in portfolio command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при выполнении команды портфеля: {str(e)}")

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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        try:
            user_message = update.message.text
            user_id = update.effective_user.id
            
            # Update user context
            self._update_user_context(user_id, conversation_history=user_message)
            
            # Parse intent
            parsed = self.intent_parser.parse_intent(user_message)
            
            # Process based on intent
            if parsed.intent == 'asset_analysis':
                # Handle asset analysis
                symbol = parsed.symbol
                period = getattr(parsed, 'period', '10Y')
                
                # Get asset info
                result = self.okama_handler.get_asset_info(symbol, period)
                report_text, images = self.report_builder.build_asset_report(result)
                ai_summary = self.analysis_engine.summarize('asset', result, user_message)
                
                # Send report
                await self.send_long_message(update, report_text)
                
                # Send images with analysis
                for img_bytes in images:
                    try:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=io.BytesIO(img_bytes)
                        )
                    except Exception:
                        pass
                        
            elif parsed.intent == 'portfolio_analysis':
                # Handle portfolio analysis
                portfolio_data = parsed.portfolio
                result = self.okama_handler.analyze_portfolio(portfolio_data)
                report_text, images = self.report_builder.build_portfolio_report(result)
                ai_summary = self.analysis_engine.summarize('portfolio', result, user_message)
                
                # Send report
                await self.send_long_message(update, report_text)
                
                # Send images
                for img_bytes in images:
                    try:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=io.BytesIO(img_bytes)
                        )
                    except Exception:
                        pass

            elif parsed.intent == 'inflation_data':
                # Handle inflation data
                country = getattr(parsed, 'country', 'US')
                period = getattr(parsed, 'period', '5Y')
                result = self.okama_handler.get_inflation(country=country, period=period)
                report_text, images = self.report_builder.build_inflation_report(result)
                ai_summary = self.analysis_engine.summarize('inflation', result, user_message)
                
                # Send report
                await self.send_long_message(update, report_text)
                
                # Send images
                for img_bytes in images:
                    try:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=io.BytesIO(img_bytes)
                        )
                    except Exception:
                        pass

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
                    
        except Exception as e:
            self.logger.error(f"Error in handle_message: {e}")
            await self._send_message_safe(update, 
                "Извините, произошла ошибка при обработке вашего запроса. "
                                    "Попробуйте переформулировать вопрос или используйте доступные команды. "
                "Если вы запрашиваете данные по MOEX (например, SBER.MOEX), они могут быть временно недоступно."
            )

    async def _send_callback_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: str = None):
        """Отправить сообщение в callback query - исправлено для обработки None"""
        try:
            # Проверяем, что update и context не None
            if update is None or context is None:
                self.logger.error("Cannot send message: update or context is None")
                return
            
            if hasattr(update, 'callback_query') and update.callback_query is not None:
                # Для callback query используем context.bot.send_message
                try:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=text,
                        parse_mode=parse_mode
                    )
                except Exception as callback_error:
                    self.logger.error(f"Error sending callback message: {callback_error}")
                    # Fallback: попробуем отправить через _send_message_safe
                    await self._send_message_safe(update, text, parse_mode)
            elif hasattr(update, 'message') and update.message is not None:
                # Для обычных сообщений используем _send_message_safe
                await self._send_message_safe(update, text, parse_mode)
            else:
                # Если ни то, ни другое - логируем ошибку
                self.logger.error("Cannot send message: neither callback_query nor message available")
                self.logger.error(f"Update type: {type(update)}")
                self.logger.error(f"Update attributes: {dir(update) if update else 'None'}")
        except Exception as e:
            self.logger.error(f"Error sending callback message: {e}")
            # Fallback: попробуем отправить через context.bot
            try:
                if hasattr(update, 'callback_query') and update.callback_query is not None:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=f"❌ Ошибка отправки: {text[:500]}..."
                    )
            except Exception as fallback_error:
                self.logger.error(f"Fallback message sending also failed: {fallback_error}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks for additional analysis"""
        query = update.callback_query
        await query.answer()
        
        self.logger.info(f"Button callback received: {query.data}")
        
        try:
            # Parse callback data
            callback_data = query.data
            self.logger.info(f"Processing callback data: {callback_data}")
            
            if callback_data.startswith('drawdowns_'):
                symbols = callback_data.replace('drawdowns_', '').split(',')
                self.logger.info(f"Drawdowns button clicked for symbols: {symbols}")
                
                # Check user context to determine which type of analysis this is
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                last_analysis_type = user_context.get('last_analysis_type')
                
                self.logger.info(f"Last analysis type: {last_analysis_type}")
                
                if last_analysis_type == 'portfolio':
                    await self._handle_portfolio_drawdowns_button(update, context, symbols)
                else:
                    await self._handle_drawdowns_button(update, context, symbols)
            elif callback_data.startswith('dividends_') and ',' in callback_data:
                # Для сравнения активов (dividends_AAA,BBB)
                symbols = callback_data.replace('dividends_', '').split(',')
                self.logger.info(f"Dividends button clicked for symbols: {symbols}")
                await self._handle_dividends_button(update, context, symbols)
            elif callback_data.startswith('correlation_'):
                symbols = callback_data.replace('correlation_', '').split(',')
                self.logger.info(f"Correlation button clicked for symbols: {symbols}")
                await self._handle_correlation_button(update, context, symbols)
            elif callback_data.startswith('monthly_chart_'):
                symbol = callback_data.replace('monthly_chart_', '')
                self.logger.info(f"Monthly chart button clicked for symbol: {symbol}")
                await self._handle_monthly_chart_button(update, context, symbol)
            elif callback_data.startswith('dividends_') and ',' not in callback_data:
                # Для одиночного актива (dividends_AAA)
                symbol = callback_data.replace('dividends_', '')
                self.logger.info(f"Dividends button clicked for symbol: {symbol}")
                await self._handle_single_dividends_button(update, context, symbol)
            elif callback_data.startswith('risk_metrics_'):
                symbols = callback_data.replace('risk_metrics_', '').split(',')
                self.logger.info(f"Risk metrics button clicked for symbols: {symbols}")
                await self._handle_risk_metrics_button(update, context, symbols)
            elif callback_data.startswith('monte_carlo_'):
                symbols = callback_data.replace('monte_carlo_', '').split(',')
                self.logger.info(f"Monte Carlo button clicked for symbols: {symbols}")
                await self._handle_monte_carlo_button(update, context, symbols)
            elif callback_data.startswith('forecast_'):
                symbols = callback_data.replace('forecast_', '').split(',')
                self.logger.info(f"Forecast button clicked for symbols: {symbols}")
                await self._handle_forecast_button(update, context, symbols)

            elif callback_data.startswith('returns_'):
                symbols = callback_data.replace('returns_', '').split(',')
                self.logger.info(f"Returns button clicked for symbols: {symbols}")
                await self._handle_portfolio_returns_button(update, context, symbols)
            elif callback_data.startswith('rolling_cagr_'):
                symbols = callback_data.replace('rolling_cagr_', '').split(',')
                self.logger.info(f"Rolling CAGR button clicked for symbols: {symbols}")
                await self._handle_portfolio_rolling_cagr_button(update, context, symbols)
            elif callback_data.startswith('compare_assets_'):
                symbols = callback_data.replace('compare_assets_', '').split(',')
                self.logger.info(f"Compare assets button clicked for symbols: {symbols}")
                await self._handle_portfolio_compare_assets_button(update, context, symbols)
            elif callback_data.startswith('namespace_'):
                namespace = callback_data.replace('namespace_', '')
                self.logger.info(f"Namespace button clicked for: {namespace}")
                await self._handle_namespace_button(update, context, namespace)
            elif callback_data.startswith('excel_namespace_'):
                namespace = callback_data.replace('excel_namespace_', '')
                self.logger.info(f"Excel namespace button clicked for: {namespace}")
                await self._handle_excel_namespace_button(update, context, namespace)
            elif callback_data == 'clear_all_portfolios':
                self.logger.info("Clear all portfolios button clicked")
                await self._handle_clear_all_portfolios_button(update, context)
            else:
                self.logger.warning(f"Unknown button callback: {callback_data}")
                await self._send_callback_message(update, context, "❌ Неизвестная кнопка")
                
        except Exception as e:
            self.logger.error(f"Error in button callback: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при обработке кнопки: {str(e)}")

    async def _handle_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle drawdowns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling drawdowns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating drawdowns chart for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "📉 Создаю график drawdowns...")
            
            # Create AssetList again
            asset_list = ok.AssetList(symbols, ccy=currency)
            
            await self._create_drawdowns_chart(update, context, asset_list, symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling drawdowns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика drawdowns: {str(e)}")

    async def _handle_dividends_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle dividends button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling dividends button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating dividends chart for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "💰 Создаю график дивидендной доходности...")
            
            # Create AssetList again
            asset_list = ok.AssetList(symbols, ccy=currency)
            
            await self._create_dividend_yield_chart(update, context, asset_list, symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling dividends button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика дивидендной доходности: {str(e)}")

    async def _handle_correlation_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle correlation matrix button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling correlation button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating correlation matrix for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "🔗 Создаю корреляционную матрицу...")
            
            # Create AssetList again
            asset_list = ok.AssetList(symbols, ccy=currency)
            
            await self._create_correlation_matrix(update, context, asset_list, symbols)
            
        except Exception as e:
            self.logger.error(f"Error handling correlation button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании корреляционной матрицы: {str(e)}")

    async def _handle_monthly_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle monthly chart button click for single asset"""
        try:
            await self._send_callback_message(update, context, "📅 Получаю месячный график за 10 лет...")
            
            # Получаем месячный график за 10 лет
            monthly_chart = await self._get_monthly_chart(symbol)
            
            if monthly_chart:
                caption = f"📅 Месячный график {symbol} за 10 лет\n\n"
                caption += "Показывает долгосрочные тренды и сезонность"
                
                await update.callback_query.message.reply_photo(
                    photo=monthly_chart,
                    caption=self._truncate_caption(caption)
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось получить месячный график")
                
        except Exception as e:
            self.logger.error(f"Error handling monthly chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании месячного графика: {str(e)}")

    async def _handle_single_dividends_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle dividends button click for single asset"""
        try:
            await self._send_callback_message(update, context, "💵 Получаю информацию о дивидендах...")
            
            # Получаем информацию о дивидендах
            dividend_info = self.asset_service.get_asset_dividends(symbol)
            
            if 'error' not in dividend_info and dividend_info.get('dividends'):
                dividends = dividend_info['dividends']
                currency = dividend_info.get('currency', '')
                
                if dividends:
                    # Формируем краткую информацию о дивидендах + текст последних выплат
                    try:
                        dividend_series = pd.Series(dividends)
                        recent = dividend_series.sort_index(ascending=False).head(10)
                        payouts_lines = []
                        for date, amount in recent.items():
                            if hasattr(date, 'strftime'):
                                formatted_date = date.strftime('%Y-%m-%d')
                            else:
                                formatted_date = str(date)[:10]
                            try:
                                amount_value = float(amount)
                            except Exception:
                                amount_value = amount
                            payouts_lines.append(f"{formatted_date} — {amount_value:.2f} {currency}")
                        payouts_text = "\n".join(payouts_lines)
                    except Exception:
                        # Fallback без pandas
                        items = list(dividends.items())[-10:][::-1]
                        payouts_lines = []
                        for date, amount in items:
                            formatted_date = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
                            try:
                                amount_value = float(amount)
                            except Exception:
                                amount_value = amount
                            payouts_lines.append(f"{formatted_date} — {amount_value:.2f} {currency}")
                        payouts_text = "\n".join(payouts_lines)

                    dividend_response = (
                        f"💵 Дивиденды {symbol}\n\n"
                        f"📊 Количество выплат: {len(dividends)}\n"
                        f"💰 Валюта: {currency}\n\n"
                        f"🗓️ Последние выплаты:\n{payouts_text}"
                    )
                    
                    # Получаем график дивидендов (без встроенной таблицы)
                    dividend_chart = await self._get_dividend_chart(symbol)
                    
                    if dividend_chart:
                        await update.callback_query.message.reply_photo(
                            photo=dividend_chart,
                            caption=self._truncate_caption(dividend_response)
                        )
                    else:
                        await self._send_callback_message(update, context, dividend_response)
                else:
                    await self._send_callback_message(update, context, "💵 Дивиденды не выплачивались в указанный период")
            else:
                await self._send_callback_message(update, context, "💵 Информация о дивидендах недоступна")
                
        except Exception as e:
            self.logger.error(f"Error handling dividends button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при получении дивидендов: {str(e)}")

    async def _get_monthly_chart(self, symbol: str) -> Optional[bytes]:
        """Получить месячный график за 10 лет с централизованными стилями и копирайтом"""
        try:
            # Получаем данные для месячного графика
            price_history = self.asset_service.get_asset_price_history(symbol, '10Y')
            
            if 'error' in price_history:
                self.logger.error(f"Error in price_history: {price_history['error']}")
                return None
            
            # Получаем данные о ценах
            if 'prices' in price_history and price_history['prices'] is not None:
                prices = price_history['prices']
                currency = price_history.get('currency', 'USD')
                
                # Создаем график с использованием централизованных стилей
                return self._create_monthly_chart_with_styles(symbol, prices, currency)
            
            # Fallback к старому методу если нет данных о ценах
            if 'charts' in price_history and price_history['charts']:
                charts = price_history['charts']
                if 'close_monthly' in charts and charts['close_monthly']:
                    chart_data = charts['close_monthly']
                    if isinstance(chart_data, bytes) and len(chart_data) > 0:
                        # Копирайт уже добавлен в готовом изображении
                        return chart_data
                
                for chart_key, chart_data in charts.items():
                    if chart_data and isinstance(chart_data, bytes) and len(chart_data) > 0:
                        self.logger.info(f"Using fallback chart: {chart_key} for {symbol}")
                        # Копирайт уже добавлен в готовом изображении
                        return chart_data
            
            self.logger.warning(f"No valid charts found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting monthly chart for {symbol}: {e}")
            return None

    async def _get_dividend_chart(self, symbol: str) -> Optional[bytes]:
        """Получить график дивидендов с копирайтом"""
        try:
            # Получаем данные о дивидендах
            dividend_info = self.asset_service.get_asset_dividends(symbol)
            
            if 'error' in dividend_info or not dividend_info.get('dividends'):
                return None
            
            # Создаем график дивидендов
            dividend_chart = self._create_dividend_chart(symbol, dividend_info['dividends'], dividend_info.get('currency', ''))
            
            if dividend_chart:
                # Копирайт уже добавлен в _create_dividend_chart
                return dividend_chart
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting dividend chart for {symbol}: {e}")
            return None

    async def _get_dividend_table_image(self, symbol: str) -> Optional[bytes]:
        """Получить изображение таблицы дивидендов с копирайтом"""
        try:
            # Получаем данные о дивидендах
            dividend_info = self.asset_service.get_asset_dividends(symbol)
            
            if 'error' in dividend_info or not dividend_info.get('dividends'):
                return None
            
            # Создаем изображение таблицы дивидендов
            dividend_table = self._create_dividend_table_image(symbol, dividend_info['dividends'], dividend_info.get('currency', ''))
            
            if dividend_table:
                # Копирайт уже добавлен в _create_dividend_table_image
                return dividend_table
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting dividend table image for {symbol}: {e}")
            return None

    def _create_dividend_chart(self, symbol: str, dividends: dict, currency: str) -> Optional[bytes]:
        """Создать график дивидендов"""
        try:
            
            # Конвертируем дивиденды в pandas Series
            dividend_series = pd.Series(dividends)
            
            # Сортируем по дате
            dividend_series = dividend_series.sort_index()
            
            # Создаем график с увеличенной высотой для таблицы
            fig, ax = chart_styles.create_dividends_chart_enhanced(
                data=dividend_series,
                symbol=symbol,
                currency=currency
            )
            
            # Рисуем столбчатую диаграмму
            dates = [pd.to_datetime(date) for date in dividend_series.index]
            amounts = dividend_series.values
            
            bars = ax.bar(dates, amounts, color='#2E8B57', alpha=0.7, width=20)
            
            # Настройка графика
            ax.set_title(f'Дивиденды {symbol}', fontsize=16, fontweight='bold', pad=20)

            ax.set_ylabel(f'Сумма ({currency})', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # Форматирование оси X
            fig.autofmt_xdate()
            
            # Добавляем статистику в левом верхнем углу
            total_dividends = dividend_series.sum()
            avg_dividend = dividend_series.mean()
            max_dividend = dividend_series.max()
            
            stats_text = f'Общая сумма: {total_dividends:.2f} {currency}\n'
            stats_text += f'Средняя выплата: {avg_dividend:.2f} {currency}\n'
            stats_text += f'Максимальная выплата: {max_dividend:.2f} {currency}'
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            # Убираем таблицу с графика и используем стандартные отступы
            plt.subplots_adjust(right=0.95)
            
            # Добавляем копирайт к axes
            chart_styles.add_copyright(ax)
            
            # Сохраняем в bytes
            output = io.BytesIO()
            fig.savefig(output, format='PNG', dpi=300, bbox_inches='tight')
            output.seek(0)
            plt.close(fig)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating dividend chart: {e}")
            return None

    def _create_dividend_table_image(self, symbol: str, dividends: dict, currency: str) -> Optional[bytes]:
        """Создать отдельное изображение с таблицей дивидендов"""
        try:
            
            # Конвертируем дивиденды в pandas Series
            dividend_series = pd.Series(dividends)
            
            # Сортируем по дате (новые сверху)
            dividend_series = dividend_series.sort_index(ascending=False)
            
            # Берем последние 15 выплат для таблицы
            recent_dividends = dividend_series.head(15)
            
            # Создаем таблицу
            table_data = []
            table_headers = ['Дата', f'Сумма ({currency})']
            
            for date, amount in recent_dividends.items():
                # Форматируем дату для лучшей читаемости
                if hasattr(date, 'strftime'):
                    formatted_date = date.strftime('%Y-%m-%d')
                else:
                    formatted_date = str(date)[:10]
                table_data.append([formatted_date, f'{amount:.2f}'])
            
            # Создаем фигуру для таблицы используя chart_styles
            fig, ax, table = chart_styles.create_dividend_table_chart(
                table_data=table_data,
                headers=table_headers
            )
            
            # Стилизуем таблицу
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2.0)
            
            # Цвета для заголовков
            for i in range(len(table_headers)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
                table[(0, i)].set_height(0.12)
            
            # Цвета для строк данных (чередование)
            for i in range(1, len(table_data) + 1):
                for j in range(len(table_headers)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#F5F5F5')
                    else:
                        table[(i, j)].set_facecolor('#FFFFFF')
                    table[(i, j)].set_text_props(color='black')
                    table[(i, j)].set_height(0.08)
            
            # Добавляем заголовок таблицы
            ax.set_title(f'Таблица дивидендов {symbol}\nПоследние {len(table_data)} выплат', 
                        fontsize=16, fontweight='bold', pad=20, color='#2E3440')
            
            # Добавляем общую статистику внизу
            total_dividends = dividend_series.sum()
            avg_dividend = dividend_series.mean()
            max_dividend = dividend_series.max()
            
            stats_text = f'Общая сумма: {total_dividends:.2f} {currency} | '
            stats_text += f'Средняя выплата: {avg_dividend:.2f} {currency} | '
            stats_text += f'Максимальная выплата: {max_dividend:.2f} {currency}'
            
            ax.text(0.5, 0.02, stats_text, transform=ax.transAxes, 
                   fontsize=10, ha='center', color='#4C566A',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', alpha=0.8))
            
            # Сохраняем в bytes
            output = io.BytesIO()
            fig.savefig(output, format='PNG', dpi=300, bbox_inches='tight', facecolor='white')
            output.seek(0)
            plt.close(fig)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating dividend table image: {e}")
            return None

    async def _handle_risk_metrics_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle risk metrics button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling risk metrics button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating risk metrics for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📊 Анализирую риски портфеля...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_risk_metrics_report(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling risk metrics button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при анализе рисков: {str(e)}")

    async def _handle_monte_carlo_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle Monte Carlo button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling Monte Carlo button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating Monte Carlo forecast for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "🎲 Создаю прогноз Monte Carlo...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_monte_carlo_forecast(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling Monte Carlo button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза Monte Carlo: {str(e)}")

    async def _handle_forecast_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle forecast button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling forecast button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating forecast for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📈 Создаю прогноз с процентилями...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_forecast_chart(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling forecast button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза: {str(e)}")

    async def _create_risk_metrics_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send risk metrics report for portfolio"""
        try:
            # Get portfolio description
            portfolio_description = portfolio.describe()
            
            # Create header
            risk_text = f"📊 **Анализ риск метрик портфеля**\n\n"
            risk_text += f"🎯 **Активы:** {', '.join(symbols)}\n"
            risk_text += f"💰 **Валюта:** {currency}\n\n"
            risk_text += "─" * 50 + "\n\n"
            
            # Parse and explain each metric
            metrics_explained = self._explain_risk_metrics(portfolio_description, portfolio)
            
            # Add metrics with better formatting
            for metric_name, explanation in metrics_explained.items():
                risk_text += f"{metric_name}\n"
                risk_text += f"{explanation}\n\n"
                risk_text += "─" * 30 + "\n\n"
            
            # Add general risk assessment
            risk_text += "🎯 **ОБЩАЯ ОЦЕНКА РИСКА**\n"
            risk_text += "─" * 50 + "\n\n"
            risk_text += self._assess_portfolio_risk(portfolio_description, portfolio)
            
            # Send text report
            await self._send_callback_message(update, context, risk_text)
            
        except Exception as e:
            self.logger.error(f"Error creating risk metrics report: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании отчета о рисках: {str(e)}")

    def _explain_risk_metrics(self, portfolio_description, portfolio) -> dict:
        """Explain each risk metric in detail"""
        explanations = {}
        
        try:
            # 1. Годовая волатильность
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    # Определяем уровень волатильности
                    if risk_pct <= 5:
                        volatility_level = "Очень низкая"
                        volatility_emoji = "🟢"
                        asset_type = "Типично для облигаций и депозитов"
                    elif risk_pct <= 10:
                        volatility_level = "Низкая"
                        volatility_emoji = "🟢"
                        asset_type = "Типично для консервативных портфелей"
                    elif risk_pct <= 15:
                        volatility_level = "Умеренная"
                        volatility_emoji = "🟡"
                        asset_type = "Типично для сбалансированных портфелей"
                    elif risk_pct <= 25:
                        volatility_level = "Высокая"
                        volatility_emoji = "🟠"
                        asset_type = "Типично для акций"
                    else:
                        volatility_level = "Очень высокая"
                        volatility_emoji = "🔴"
                        asset_type = "Типично для спекулятивных активов"
                    
                    explanations["1. Годовая волатильность"] = (
                        f"{volatility_emoji} **{volatility_level}** ({risk_pct:.1f}% годовых)\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• Портфель может колебаться в пределах ±{risk_pct:.1f}% в год\n"
                        f"• {asset_type}\n\n"
                        f"💡 **Как использовать:**\n"
                        f"• Сравнивайте с другими портфелями\n"
                        f"• При одинаковой доходности выбирайте с меньшей волатильностью\n"
                        f"• Учитывайте свой риск-профиль"
                    )
            
            # 2. Полуотклонение (риск только вниз)
            if hasattr(portfolio, 'semideviation_annual'):
                semidev = portfolio.semideviation_annual
                if hasattr(semidev, 'iloc'):
                    semidev_value = semidev.iloc[-1] if not semidev.empty else None
                else:
                    semidev_value = semidev
                
                if semidev_value is not None:
                    semidev_pct = float(semidev_value) * 100
                    # Сравниваем с общей волатильностью
                    if hasattr(portfolio, 'risk_annual'):
                        risk_annual = portfolio.risk_annual
                        if hasattr(risk_annual, 'tail'):
                            risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                        else:
                            risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                        
                        if risk_value is not None:
                            risk_pct = float(risk_value) * 100
                            ratio = semidev_pct / risk_pct if risk_pct > 0 else 1
                            
                            if ratio < 0.7:
                                downside_characteristic = "Портфель 'гладкий' вниз, но может резко расти"
                            elif ratio > 0.9:
                                downside_characteristic = "Портфель одинаково колеблется вверх и вниз"
                            else:
                                downside_characteristic = "Сбалансированное поведение портфеля"
                        else:
                            downside_characteristic = "Стандартное поведение"
                    else:
                        downside_characteristic = "Стандартное поведение"
                    
                    explanations["2. Риск просадок (полуотклонение)"] = (
                        f"📉 **{semidev_pct:.1f}%** годовых\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• Учитывает только отрицательные колебания\n"
                        f"• Более точно отражает страх инвестора\n\n"
                        f"💡 **Характеристика:**\n"
                        f"• {downside_characteristic}\n"
                        f"• Помогает понять, насколько 'комфортно' падать портфелю"
                    )
            
            # 3. VaR (Value at Risk)
            try:
                var_1 = portfolio.get_var_historic(level=1)
                var_5 = portfolio.get_var_historic(level=5)
                
                if var_1 is not None and var_5 is not None:
                    var_1_pct = float(var_1) * 100
                    var_5_pct = float(var_5) * 100
                    
                    # Оценка риска по VaR
                    if abs(var_5_pct) <= 3:
                        var_assessment = "Очень низкий риск потерь"
                        var_emoji = "🟢"
                    elif abs(var_5_pct) <= 8:
                        var_assessment = "Низкий риск потерь"
                        var_emoji = "🟢"
                    elif abs(var_5_pct) <= 15:
                        var_assessment = "Умеренный риск потерь"
                        var_emoji = "🟡"
                    elif abs(var_5_pct) <= 25:
                        var_assessment = "Высокий риск потерь"
                        var_emoji = "🟠"
                    else:
                        var_assessment = "Очень высокий риск потерь"
                        var_emoji = "🔴"
                    
                    explanations["3. VaR (риск потерь)"] = (
                        f"{var_emoji} **{var_assessment}**\n\n"
                        f"📊 **Значения:**\n"
                        f"• 1% VaR: {var_1_pct:.1f}% (99% вероятность, что потери не превысят)\n"
                        f"• 5% VaR: {var_5_pct:.1f}% (95% вероятность, что потери не превысят)\n\n"
                        f"💡 **Как использовать:**\n"
                        f"• Оцените, готовы ли потерять {abs(var_5_pct):.1f}% в месяц\n"
                        f"• Если нет — портфель слишком агрессивный для вас"
                    )
            except Exception as e:
                self.logger.warning(f"Could not get VaR: {e}")
            
            # 4. CVaR (Conditional Value at Risk)
            try:
                cvar_5 = portfolio.get_cvar_historic(level=5)
                
                if cvar_5 is not None:
                    cvar_5_pct = float(cvar_5) * 100
                    
                    # Оценка по CVaR
                    if abs(cvar_5_pct) <= 5:
                        cvar_assessment = "Очень низкие ожидаемые потери в кризис"
                        cvar_emoji = "🟢"
                    elif abs(cvar_5_pct) <= 12:
                        cvar_assessment = "Низкие ожидаемые потери в кризис"
                        cvar_emoji = "🟢"
                    elif abs(cvar_5_pct) <= 20:
                        cvar_assessment = "Умеренные ожидаемые потери в кризис"
                        cvar_emoji = "🟡"
                    elif abs(cvar_5_pct) <= 30:
                        cvar_assessment = "Высокие ожидаемые потери в кризис"
                        cvar_emoji = "🟠"
                    else:
                        cvar_assessment = "Очень высокие ожидаемые потери в кризис"
                        cvar_emoji = "🔴"
                    
                    explanations["4. CVaR (ожидаемые потери в кризис)"] = (
                        f"{cvar_emoji} **{cvar_assessment}**\n\n"
                        f"📊 **Значение:** {cvar_5_pct:.1f}%\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• В худших 5% месяцев ожидайте потери около {abs(cvar_5_pct):.1f}%\n"
                        f"• Более консервативный показатель, чем VaR\n"
                        f"• Помогает понять глубину возможного 'провала'"
                    )
            except Exception as e:
                self.logger.warning(f"Could not get CVaR: {e}")
            
            # 5. Максимальная просадка
            if hasattr(portfolio, 'drawdowns'):
                drawdowns = portfolio.drawdowns
                if hasattr(drawdowns, 'min'):
                    max_dd = drawdowns.min()
                    if max_dd is not None:
                        max_dd_pct = float(max_dd) * 100
                        
                        # Оценка просадки
                        if max_dd_pct <= 5:
                            dd_assessment = "Очень низкая просадка"
                            dd_emoji = "🟢"
                            dd_advice = "Портфель очень стабильный, подходит для консервативных инвесторов"
                        elif max_dd_pct <= 15:
                            dd_assessment = "Низкая просадка"
                            dd_emoji = "🟢"
                            dd_advice = "Портфель стабильный, подходит для большинства инвесторов"
                        elif max_dd_pct <= 30:
                            dd_assessment = "Умеренная просадка"
                            dd_emoji = "🟡"
                            dd_advice = "Требует психологической устойчивости"
                        elif max_dd_pct <= 50:
                            dd_assessment = "Высокая просадка"
                            dd_emoji = "🟠"
                            dd_advice = "Убедитесь, что готовы к таким потерям"
                        else:
                            dd_assessment = "Очень высокая просадка"
                            dd_emoji = "🔴"
                            dd_advice = "Портфель очень агрессивный"
                        
                        explanations["5. Максимальная просадка"] = (
                            f"{dd_emoji} **{dd_assessment}** ({max_dd_pct:.1f}%)\n\n"
                            f"💡 **Что это значит:**\n"
                            f"• Самая большая потеря от пика до дна\n"
                            f"• Критично для психологической устойчивости\n\n"
                            f"💡 **Рекомендация:**\n"
                            f"• {dd_advice}\n"
                            f"• Если не выдержите просадку в {max_dd_pct:.1f}%, пересмотрите состав"
                        )
            
            # 6. Период восстановления
            if hasattr(portfolio, 'recovery_period'):
                recovery = portfolio.recovery_period
                if hasattr(recovery, 'max'):
                    max_recovery = recovery.max()
                    if max_recovery is not None:
                        recovery_years = float(max_recovery) / 12  # в годах
                        
                        # Оценка периода восстановления
                        if recovery_years <= 0.5:
                            recovery_assessment = "Очень быстрое восстановление"
                            recovery_emoji = "🟢"
                        elif recovery_years <= 1:
                            recovery_assessment = "Быстрое восстановление"
                            recovery_emoji = "🟢"
                        elif recovery_years <= 2:
                            recovery_assessment = "Умеренное восстановление"
                            recovery_emoji = "🟡"
                        elif recovery_years <= 4:
                            recovery_assessment = "Медленное восстановление"
                            recovery_emoji = "🟠"
                        else:
                            recovery_assessment = "Очень медленное восстановление"
                            recovery_emoji = "🔴"
                        
                        explanations["6. Период восстановления"] = (
                            f"{recovery_emoji} **{recovery_assessment}** ({recovery_years:.1f} года)\n\n"
                            f"💡 **Что это значит:**\n"
                            f"• Время возврата к предыдущему максимуму\n"
                            f"• Критично при планировании снятия денег\n\n"
                            f"💡 **Как использовать:**\n"
                            f"• Если планируете снимать деньги, убедитесь, что период восстановления приемлем\n"
                            f"• Иначе есть риск 'обнулиться' в неподходящий момент"
                        )
            
        except Exception as e:
            self.logger.error(f"Error explaining risk metrics: {e}")
            explanations["Ошибка анализа"] = f"Не удалось проанализировать метрики риска: {str(e)}"
        
        return explanations

    def _assess_portfolio_risk(self, portfolio_description, portfolio) -> str:
        """Assess overall portfolio risk level with improved logic for conservative assets"""
        try:
            risk_level = "Средний"
            risk_color = "🟡"
            risk_score = 0
            recommendations = []
            
            # Check volatility (weight: 40%)
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    
                    if risk_pct <= 5:
                        risk_score += 0  # Очень низкий риск
                        volatility_assessment = "Очень низкая"
                        volatility_emoji = "🟢"
                    elif risk_pct <= 10:
                        risk_score += 1  # Низкий риск
                        volatility_assessment = "Низкая"
                        volatility_emoji = "🟢"
                    elif risk_pct <= 15:
                        risk_score += 2  # Умеренный риск
                        volatility_assessment = "Умеренная"
                        volatility_emoji = "🟡"
                    elif risk_pct <= 25:
                        risk_score += 3  # Высокий риск
                        volatility_assessment = "Высокая"
                        volatility_emoji = "🟠"
                    else:
                        risk_score += 4  # Очень высокий риск
                        volatility_assessment = "Очень высокая"
                        volatility_emoji = "🔴"
                    
                    # Добавляем рекомендации по волатильности
                    if risk_pct <= 5:
                        recommendations.append("• Портфель очень консервативный, идеален для сохранения капитала")
                        recommendations.append("• Подходит для инвесторов с низкой толерантностью к риску")
                    elif risk_pct <= 10:
                        recommendations.append("• Портфель консервативный, подходит для большинства инвесторов")
                        recommendations.append("• Рассмотрите добавление акций для роста доходности")
                    elif risk_pct <= 15:
                        recommendations.append("• Портфель сбалансированный, подходит для долгосрочных целей")
                    elif risk_pct <= 25:
                        recommendations.append("• Портфель агрессивный, требует психологической устойчивости")
                        recommendations.append("• Рассмотрите добавление облигаций для снижения волатильности")
                    else:
                        recommendations.append("• Портфель очень агрессивный, подходит только для опытных инвесторов")
                        recommendations.append("• Увеличьте долю защитных активов (облигации, золото)")
            
            # Check max drawdown (weight: 30%)
            if hasattr(portfolio, 'drawdowns'):
                drawdowns = portfolio.drawdowns
                if hasattr(drawdowns, 'min'):
                    max_dd = drawdowns.min()
                    if max_dd is not None:
                        max_dd_pct = abs(float(max_dd) * 100)
                        
                        if max_dd_pct <= 5:
                            risk_score += 0  # Очень низкий риск
                            dd_assessment = "Очень низкая"
                        elif max_dd_pct <= 15:
                            risk_score += 1  # Низкий риск
                            dd_assessment = "Низкая"
                        elif max_dd_pct <= 30:
                            risk_score += 2  # Умеренный риск
                            dd_assessment = "Умеренная"
                        elif max_dd_pct <= 50:
                            risk_score += 3  # Высокий риск
                            dd_assessment = "Высокая"
                        else:
                            risk_score += 4  # Очень высокий риск
                            dd_assessment = "Очень высокая"
                        
                        # Добавляем рекомендации по просадке
                        if max_dd_pct <= 5:
                            recommendations.append("• Просадка очень низкая, портфель очень стабильный")
                        elif max_dd_pct <= 15:
                            recommendations.append("• Просадка низкая, подходит для большинства инвесторов")
                        elif max_dd_pct <= 30:
                            recommendations.append("• Просадка умеренная, требует психологической устойчивости")
                        else:
                            recommendations.append("• Просадка высокая, убедитесь, что готовы к таким потерям")
            
            # Check VaR (weight: 20%)
            try:
                var_5 = portfolio.get_var_historic(level=5)
                if var_5 is not None:
                    var_5_pct = abs(float(var_5) * 100)
                    
                    if var_5_pct <= 3:
                        risk_score += 0  # Очень низкий риск
                    elif var_5_pct <= 8:
                        risk_score += 1  # Низкий риск
                    elif var_5_pct <= 15:
                        risk_score += 2  # Умеренный риск
                    elif var_5_pct <= 25:
                        risk_score += 3  # Высокий риск
                    else:
                        risk_score += 4  # Очень высокий риск
            except Exception:
                pass
            
            # Check CVaR (weight: 10%)
            try:
                cvar_5 = portfolio.get_cvar_historic(level=5)
                if cvar_5 is not None:
                    cvar_5_pct = abs(float(cvar_5) * 100)
                    
                    if cvar_5_pct <= 5:
                        risk_score += 0  # Очень низкий риск
                    elif cvar_5_pct <= 12:
                        risk_score += 1  # Низкий риск
                    elif cvar_5_pct <= 20:
                        risk_score += 2  # Умеренный риск
                    elif cvar_5_pct <= 30:
                        risk_score += 3  # Высокий риск
                    else:
                        risk_score += 4  # Очень высокий риск
            except Exception:
                pass
            
            # Определяем общий уровень риска на основе score
            max_possible_score = 4  # Максимальный score для одного показателя
            normalized_score = risk_score / max_possible_score
            
            if normalized_score <= 0.25:
                risk_level = "Очень низкий"
                risk_color = "🟢"
            elif normalized_score <= 0.5:
                risk_level = "Низкий"
                risk_color = "🟢"
            elif normalized_score <= 0.75:
                risk_level = "Умеренный"
                risk_color = "🟡"
            elif normalized_score <= 1.0:
                risk_level = "Высокий"
                risk_color = "🟠"
            else:
                risk_level = "Очень высокий"
                risk_color = "🔴"
            
            # Формируем итоговую оценку
            assessment = f"{risk_color} **Уровень риска: {risk_level}**\n\n"
            
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    assessment += f"📊 **Ключевые показатели:**\n"
                    assessment += f"• Волатильность: {volatility_emoji} {volatility_assessment} ({risk_pct:.1f}%)\n"
                    
                    if hasattr(portfolio, 'drawdowns'):
                        drawdowns = portfolio.drawdowns
                        if hasattr(drawdowns, 'min'):
                            max_dd = drawdowns.min()
                            if max_dd is not None:
                                max_dd_pct = abs(float(max_dd) * 100)
                                assessment += f"• Макс. просадка: {dd_assessment} ({max_dd_pct:.1f}%)\n"
            
            assessment += f"\n📋 **Рекомендации:**\n"
            if recommendations:
                for rec in recommendations:
                    assessment += f"{rec}\n"
            else:
                assessment += "• Портфель сбалансированный, специальных рекомендаций не требуется."
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {e}")
            return "Не удалось оценить общий уровень риска портфеля."

    async def _create_monte_carlo_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send Monte Carlo forecast chart for portfolio"""
        try:
            self.logger.info(f"Creating Monte Carlo forecast chart for portfolio: {symbols}")
            
            # Generate Monte Carlo forecast (okama creates the figure)
            forecast_data = portfolio.plot_forecast_monte_carlo(distr="norm", years=10, n=20)

            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()

            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                # Apply Monte Carlo specific styles to make lines thinner
                chart_styles.apply_monte_carlo_style(ax)
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_standard_chart_styling(
                    ax,
                    title=f'Прогноз Monte Carlo\n{", ".join(symbols)}',
                    ylabel='Накопленная доходность',
                    grid=True,
                    legend=True,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            current_fig.savefig(img_buffer, format='PNG', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(current_fig)
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(
                    f"🎲 Прогноз Monte Carlo для портфеля: {', '.join(symbols)}\n\n"
                    f"📊 Параметры:\n"
                    f"• Распределение: Нормальное (norm)\n"
                    f"• Период: 10 лет\n"
                    f"• Количество симуляций: 20\n"
                    f"• Валюта: {currency}\n\n"
                    f"💡 График показывает возможные траектории роста портфеля на основе исторической волатильности и доходности."
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error creating Monte Carlo forecast chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Monte Carlo: {str(e)}")

    async def _create_forecast_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send forecast chart with percentiles for portfolio"""
        try:
            self.logger.info(f"Creating forecast chart with percentiles for portfolio: {symbols}")
            
            # Generate forecast chart using okama
            # y.plot_forecast(years=10, today_value=1000, percentiles=[10, 50, 90])
            forecast_data = portfolio.plot_forecast(
                years=10, 
                today_value=1000, 
                percentiles=[10, 50, 90]
            )
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]  # Get the first (and usually only) axes
                
                # Apply percentile specific styles to ensure colors match legend
                chart_styles.apply_percentile_style(ax)
                
                # Force legend update to match the new colors
                if ax.get_legend():
                    ax.get_legend().remove()
                ax.legend(**chart_styles.legend_config)
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_standard_chart_styling(
                    ax,
                    title=f'Прогноз с процентилями\n{", ".join(symbols)}',
                    ylabel='Накопленная доходность',
                    grid=True,
                    legend=True,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            current_fig.savefig(img_buffer, format='PNG', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(current_fig)
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(
                    f"📈 Прогноз с процентилями для портфеля: {', '.join(symbols)}\n\n"
                    f"📊 Параметры:\n"
                    f"• Период: 10 лет\n"
                    f"• Начальная стоимость: 1000 {currency}\n"
                    f"• процентили: 10%, 50%, 90%\n\n"
                    f"💡 График показывает:\n"
                    f"• 10% процентиль: пессимистичный сценарий\n"
                    f"• 50% процентиль: средний сценарий\n"
                    f"• 90% процентиль: оптимистичный сценарий"
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error creating forecast chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика прогноза: {str(e)}")

    async def _handle_portfolio_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio drawdowns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio drawdowns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            self.logger.info(f"Button symbols: {button_symbols}")
            self.logger.info(f"Final symbols: {final_symbols}")
            self.logger.info(f"Current symbols from context: {user_context.get('current_symbols')}")
            self.logger.info(f"Last assets from context: {user_context.get('last_assets')}")
            
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating drawdowns chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📉 Создаю график просадок...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_portfolio_drawdowns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio drawdowns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _create_portfolio_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio drawdowns chart"""
        try:
            self.logger.info(f"Creating portfolio drawdowns chart for portfolio: {symbols}")
            
            # Generate drawdowns chart using okama
            # portfolio.drawdowns.plot()
            drawdowns_data = portfolio.drawdowns.plot()
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_standard_chart_styling(
                    ax,
                    title=f'Просадки портфеля\n{", ".join(symbols)}',
                    ylabel='Просадка (%)',
                    grid=True,
                    legend=False,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            chart_styles.save_figure(current_fig, img_buffer)
            img_buffer.seek(0)
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(current_fig)
            
            # Get drawdowns statistics
            try:
                # Get 5 largest drawdowns
                largest_drawdowns = portfolio.drawdowns.nsmallest(5)
                
                # Get longest recovery periods (convert to years)
                longest_recoveries = portfolio.recovery_period.nlargest(5) / 12
                
                # Build enhanced caption
                caption = f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add largest drawdowns
                caption += f"📉 5 самых больших просадок:\n"
                for i, (date, drawdown) in enumerate(largest_drawdowns.items(), 1):
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    drawdown_pct = drawdown * 100
                    caption += f"{i}. {date_str}: {drawdown_pct:.2f}%\n"
                
                caption += f"\n⏱️ Самые долгие периоды восстановления:\n"
                for i, (date, recovery_years) in enumerate(longest_recoveries.items(), 1):
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    caption += f"{i}. {date_str}: {recovery_years:.1f} лет\n"
                
                caption += f"\n💡 График показывает:\n"
                caption += f"• Максимальную просадку портфеля\n"
                caption += f"• Периоды восстановления\n"
                caption += f"• Волатильность доходности"
                
            except Exception as e:
                self.logger.warning(f"Could not get drawdowns statistics: {e}")
                # Fallback to basic caption
                caption = f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Максимальную просадку портфеля\n"
                caption += f"• Периоды восстановления\n"
                caption += f"• Волатильность доходности"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio drawdowns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _handle_portfolio_returns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio returns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio returns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating returns chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "💰 Создаю график доходности...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_portfolio_returns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio returns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика доходности: {str(e)}")

    async def _create_portfolio_returns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio returns chart"""
        try:
            self.logger.info(f"Creating portfolio returns chart for portfolio: {symbols}")
            
            # Generate annual returns chart using okama
            # portfolio.annual_return_ts.plot(kind="bar")
            returns_data = portfolio.annual_return_ts.plot(kind="bar")
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_standard_chart_styling(
                    ax,
                    title=f'Годовая доходность портфеля\n{", ".join(symbols)}',
                    ylabel='Доходность (%)',
                    grid=True,
                    legend=False,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            chart_styles.save_figure(current_fig, img_buffer)
            img_buffer.seek(0)
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(current_fig)
            
            # Get returns statistics
            try:
                # Get returns statistics
                mean_return_monthly = portfolio.mean_return_monthly
                mean_return_annual = portfolio.mean_return_annual
                cagr = portfolio.get_cagr()
                
                # Handle CAGR which might be a Series
                if hasattr(cagr, '__iter__') and not isinstance(cagr, str):
                    # If it's a Series or array-like, get the first value
                    if hasattr(cagr, 'iloc'):
                        cagr_value = cagr.iloc[0]
                    elif hasattr(cagr, '__getitem__'):
                        cagr_value = cagr[0]
                    else:
                        cagr_value = list(cagr)[0]
                else:
                    cagr_value = cagr
                
                # Build enhanced caption
                caption = f"💰 Годовая доходность портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add returns statistics
                caption += f"📈 Статистика доходности:\n"
                caption += f"• Средняя месячная доходность: {mean_return_monthly:.2%}\n"
                caption += f"• Средняя годовая доходность: {mean_return_annual:.2%}\n"
                caption += f"• CAGR (Compound Annual Growth Rate): {cagr_value:.2%}\n\n"
                
                caption += f"💡 График показывает:\n"
                caption += f"• Годовую доходность по годам\n"
                caption += f"• Волатильность доходности\n"
                caption += f"• Тренды доходности портфеля"
                
            except Exception as e:
                self.logger.warning(f"Could not get returns statistics: {e}")
                # Fallback to basic caption
                caption = f"💰 Годовая доходность портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Годовую доходность по годам\n"
                caption += f"• Волатильность доходности\n"
                caption += f"• Тренды доходности портфеля"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio returns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика доходности: {str(e)}")

    async def _handle_portfolio_rolling_cagr_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio rolling CAGR button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio rolling CAGR button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating rolling CAGR chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📈 Создаю график Rolling CAGR...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_portfolio_rolling_cagr_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio rolling CAGR button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Rolling CAGR: {str(e)}")

    async def _create_portfolio_rolling_cagr_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio rolling CAGR chart"""
        try:
            self.logger.info(f"Creating portfolio rolling CAGR chart for portfolio: {symbols}")
            
            # Get rolling CAGR data
            rolling_cagr_data = portfolio.get_rolling_cagr()
            
            # Create standardized rolling CAGR chart using chart_styles
            fig, ax = chart_styles.create_portfolio_rolling_cagr_chart(
                data=rolling_cagr_data, symbols=symbols, currency=currency
            )
            
            # Save the figure using standardized method
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            chart_styles.cleanup_figure(fig)
            img_buffer.seek(0)
            
            # Get rolling CAGR statistics
            try:
                # Get rolling CAGR data for statistics
                rolling_cagr_series = portfolio.get_rolling_cagr()
                
                # Calculate statistics
                mean_rolling_cagr = rolling_cagr_series.mean()
                std_rolling_cagr = rolling_cagr_series.std()
                min_rolling_cagr = rolling_cagr_series.min()
                max_rolling_cagr = rolling_cagr_series.max()
                current_rolling_cagr = rolling_cagr_series.iloc[-1] if not rolling_cagr_series.empty else None
                
                # Build enhanced caption
                caption = f"📈 Rolling CAGR (MAX период) портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n"
                caption += f"• Окно: MAX период (весь доступный период)\n\n"
                
                # Add rolling CAGR statistics
                caption += f"📈 Статистика Rolling CAGR:\n"
                if current_rolling_cagr is not None:
                    caption += f"• Текущий Rolling CAGR: {current_rolling_cagr:.2%}\n"
                caption += f"• Средний Rolling CAGR: {mean_rolling_cagr:.2%}\n"
                caption += f"• Стандартное отклонение: {std_rolling_cagr:.2%}\n"
                caption += f"• Минимальный: {min_rolling_cagr:.2%}\n"
                caption += f"• Максимальный: {max_rolling_cagr:.2%}\n\n"
                
                caption += f"💡 График показывает:\n"
                caption += f"• Rolling CAGR за весь доступный период\n"
                caption += f"• Динамику изменения CAGR во времени\n"
                caption += f"• Стабильность доходности портфеля"
                
            except Exception as e:
                self.logger.warning(f"Could not get rolling CAGR statistics: {e}")
                # Fallback to basic caption
                caption = f"📈 Rolling CAGR (MAX период) портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n"
                caption += f"• Окно: MAX период (весь доступный период)\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Rolling CAGR за весь доступный период\n"
                caption += f"• Динамику изменения CAGR во времени\n"
                caption += f"• Стабильность доходности портфеля"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio rolling CAGR chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Rolling CAGR: {str(e)}")

    async def _handle_portfolio_compare_assets_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio compare assets button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio compare assets button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            self.logger.info(f"Button symbols: {button_symbols}")
            self.logger.info(f"Final symbols: {final_symbols}")
            self.logger.info(f"Current symbols from context: {user_context.get('current_symbols')}")
            self.logger.info(f"Last assets from context: {user_context.get('last_assets')}")
            
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating compare assets chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📊 Создаю график сравнения с активами...")
            
            # Create Portfolio again
            portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
            
            await self._create_portfolio_compare_assets_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio compare assets button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика сравнения: {str(e)}")

    async def _create_portfolio_compare_assets_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio compare assets chart"""
        try:
            self.logger.info(f"Creating portfolio compare assets chart for portfolio: {symbols}")
            
            # Get wealth index with assets data
            compare_data = portfolio.wealth_index_with_assets
            
            # Create standardized comparison chart using chart_styles
            fig, ax = chart_styles.create_portfolio_compare_assets_chart(
                data=compare_data, symbols=symbols, currency=currency
            )
            
            # Save the figure using standardized method
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            chart_styles.cleanup_figure(fig)
            img_buffer.seek(0)
            
            # Get portfolio comparison statistics
            try:
                # Build enhanced caption
                caption = f"📊 Портфель vs Активы: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add portfolio performance vs individual assets
                portfolio_final = portfolio.wealth_index.iloc[-1]
                caption += f"📈 Итоговые значения (накопленная доходность):\n"
                caption += f"• Портфель: {portfolio_final:.2f}\n"
                
                # Get individual asset final values
                for symbol in symbols:
                    try:
                        # Validate symbol before creating Asset
                        if not symbol or symbol.strip() == '':
                            self.logger.warning(f"Empty symbol: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Check for invalid characters
                        invalid_chars = ['(', ')', ',']
                        if any(char in symbol for char in invalid_chars):
                            self.logger.warning(f"Invalid symbol contains brackets: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Check for proper format
                        if '.' not in symbol:
                            self.logger.warning(f"Symbol missing namespace separator: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Get individual asset
                        asset = ok.Asset(symbol, ccy=currency)
                        asset_final = asset.wealth_index.iloc[-1]
                        caption += f"• {symbol}: {asset_final:.2f}\n"
                    except Exception as e:
                        self.logger.warning(f"Could not get final value for {symbol}: {e}")
                        caption += f"• {symbol}: недоступно\n"
                
                caption += f"\n💡 График показывает:\n"
                caption += f"• Накопленную доходность портфеля vs отдельных активов\n"
                caption += f"• Эффект диверсификации\n"
                caption += f"• Сравнение рисков и доходности"
                
            except Exception as e:
                self.logger.warning(f"Could not get comparison statistics: {e}")
                # Fallback to basic caption
                caption = f"📊 Портфель vs Активы: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Накопленную доходность портфеля vs отдельных активов\n"
                caption += f"• Эффект диверсификации\n"
                caption += f"• Сравнение рисков и доходности"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio compare assets chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика сравнения: {str(e)}")

    async def _handle_namespace_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str):
        """Handle namespace button click - show symbols in specific namespace"""
        try:
            
            self.logger.info(f"Handling namespace button for: {namespace}")
            
            # Show symbols in specific namespace (same logic as namespace_command)
            try:
                symbols_df = ok.symbols_in_namespace(namespace)
                
                # Check if DataFrame is empty
                if symbols_df.empty:
                    await self._send_callback_message(update, context, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                    return
                
                # Convert DataFrame to list of symbols
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
                    await self._send_callback_message(update, context, f"❌ Пространство имен '{namespace}' не содержит символов")
                    return
                
                # Используем единый метод для показа символов
                await self._show_namespace_symbols(update, context, namespace, is_callback=True)
                
            except Exception as e:
                await self._send_callback_message(update, context, f"❌ Ошибка при получении символов для '{namespace}': {str(e)}")
                
        except ImportError:
            await self._send_callback_message(update, context, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in namespace button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка: {str(e)}")

    async def _handle_excel_namespace_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str):
        """Handle Excel export button click for namespace"""
        try:
            
            self.logger.info(f"Handling Excel export for namespace: {namespace}")
            
            # Get symbols in namespace
            try:
                symbols_df = ok.symbols_in_namespace(namespace)
                
                # Check if DataFrame is empty
                if symbols_df.empty:
                    await self._send_callback_message(update, context, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                    return
                
                total_symbols = len(symbols_df)
                
                # Show progress message
                await self._send_callback_message(update, context, f"📊 Создаю Excel файл...")
                
                # Create Excel file in memory
                excel_buffer = io.BytesIO()
                symbols_df.to_excel(excel_buffer, index=False, sheet_name=f'{namespace}_Symbols')
                excel_buffer.seek(0)
                
                # Send Excel file
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=excel_buffer,
                    filename=f"{namespace}_symbols.xlsx",
                    caption=self._truncate_caption(f"📊 Полный список символов в пространстве {namespace} ({total_symbols})")
                )
                
                excel_buffer.close()
                
            except Exception as e:
                await self._send_callback_message(update, context, f"❌ Ошибка при получении символов для '{namespace}': {str(e)}")
                
        except ImportError:
            await self._send_callback_message(update, context, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in Excel namespace button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка: {str(e)}")

    async def _handle_clear_all_portfolios_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle clear all portfolios button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling clear all portfolios button for user {user_id}")
            
            # Get user context
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if not saved_portfolios:
                await self._send_callback_message(update, context, "💼 У вас нет сохраненных портфелей для очистки")
                return
            
            # Count portfolios before clearing
            portfolio_count = len(saved_portfolios)
            
            # Clear all portfolios
            user_context['saved_portfolios'] = {}
            user_context['portfolio_count'] = 0
            
            # Update context
            self._update_user_context(user_id, **user_context)
            
            # Send confirmation message
            await self._send_callback_message(
                update, 
                context, 
                f"🗑️ **Очистка завершена!**\n\n"
                f"✅ Удалено портфелей: {portfolio_count}\n"
                f"✅ Счетчик портфелей сброшен\n\n"
                f"💡 Для создания новых портфелей используйте команду `/portfolio`"
            )
            
            self.logger.info(f"Successfully cleared {portfolio_count} portfolios for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error in clear all portfolios button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при очистке портфелей: {str(e)}")

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("info", self.info_command))
        application.add_handler(CommandHandler("namespace", self.namespace_command))
        application.add_handler(CommandHandler("compare", self.compare_command))
        application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        application.add_handler(CommandHandler("my", self.my_portfolios_command))
        
        # Add callback query handler for buttons
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
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
        traceback.print_exc()
        sys.exit(1)
