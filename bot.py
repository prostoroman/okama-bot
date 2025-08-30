import sys
import logging
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import io
import pandas as pd
import matplotlib.pyplot as plt
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
            
            # Create drawdowns chart
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
            
            # Plot drawdowns
            asset_list.drawdowns.plot(ax=ax, linewidth=2.5, alpha=0.9)
            
            # Enhanced chart customization
            ax.set_title(f'История Drawdowns\n{", ".join(symbols)}', 
                       fontsize=16, fontweight='bold', pad=20, color='#2E3440')
            ax.set_xlabel('Дата', fontsize=13, fontweight='semibold', color='#4C566A')
            ax.set_ylabel(f'Drawdown ({currency})', fontsize=13, fontweight='semibold', color='#4C566A')
            
            # Enhanced grid and background
            ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.8)
            ax.set_facecolor('#F8F9FA')
            
            # Enhanced legend
            ax.legend(fontsize=11, frameon=True, fancybox=True, shadow=True, 
                     loc='upper left', bbox_to_anchor=(0.02, 0.98))
            
            # Customize spines
            for spine in ax.spines.values():
                spine.set_color('#D1D5DB')
                spine.set_linewidth(0.8)
            
            # Enhance tick labels
            ax.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
            
            # Add subtle background pattern
            ax.set_alpha(0.95)
            
            # Add copyright signature
            chart_styles.add_copyright(ax)
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(fig)
            plt.clf()
            plt.cla()
            
            # Send drawdowns chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=f"📉 График Drawdowns для {len(symbols)} активов\n\nПоказывает периоды падения активов и их восстановление"
            )
            
            plt.close(fig)
            
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
            
            # Create dividend yield chart
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
            
            # Plot dividend yield
            asset_list.dividend_yield.plot(ax=ax, linewidth=2.5, alpha=0.9)
            
            # Enhanced chart customization
            ax.set_title(f'Дивидендная доходность\n{", ".join(symbols)}', 
                       fontsize=chart_styles.title_config['fontsize'], 
                       fontweight=chart_styles.title_config['fontweight'], 
                       pad=chart_styles.title_config['pad'], 
                       color=chart_styles.title_config['color'])
            ax.set_xlabel('Дата', fontsize=chart_styles.axis_config['label_fontsize'], 
                         fontweight=chart_styles.axis_config['label_fontweight'], 
                         color=chart_styles.axis_config['label_color'])
            ax.set_ylabel(f'Дивидендная доходность (%)', fontsize=chart_styles.axis_config['label_fontsize'], 
                          fontweight=chart_styles.axis_config['label_fontweight'], 
                          color=chart_styles.axis_config['label_color'])
            
            # Enhanced grid and background
            ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.8)
            ax.set_facecolor('#F8F9FA')
            
            # Enhanced legend
            ax.legend(**chart_styles.legend_config)
            
            # Customize spines
            for spine in ax.spines.values():
                spine.set_color('#D1D5DB')
                spine.set_linewidth(0.8)
            
            # Enhance tick labels
            ax.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
            
            # Add subtle background pattern
            ax.set_alpha(0.95)
            
            # Add copyright signature
            chart_styles.add_copyright(ax)
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(fig)
            plt.clf()
            plt.cla()
            
            # Send dividend yield chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=f"💰 График дивидендной доходности для {len(symbols)} активов\n\nПоказывает историю дивидендных выплат и доходность"
            )
            
            plt.close(fig)
            
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
            
            # Create correlation matrix visualization
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            # Use smaller figure size and lower DPI to save memory
            fig, ax = plt.subplots(figsize=(10, 8), facecolor='white', dpi=150)
            
            # Create heatmap
            im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
            
            # Set ticks and labels
            ax.set_xticks(range(len(correlation_matrix.columns)))
            ax.set_yticks(range(len(correlation_matrix.index)))
            ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
            ax.set_yticklabels(correlation_matrix.index)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('Корреляция', rotation=270, labelpad=15)
            
            # Add correlation values as text (only for smaller matrices to save memory)
            if len(correlation_matrix) <= 8:  # Only add text for matrices with 8 or fewer assets
                for i in range(len(correlation_matrix.index)):
                    for j in range(len(correlation_matrix.columns)):
                        value = correlation_matrix.iloc[i, j]
                        # Color text based on correlation value
                        if abs(value) > 0.7:
                            text_color = 'white'
                        else:
                            text_color = 'black'
                        
                        ax.text(j, i, f'{value:.2f}', 
                               ha='center', va='center', 
                               color=text_color, fontsize=9, fontweight='bold')
            
            # Customize chart
            ax.set_title('Корреляционная матрица активов', 
                       fontsize=14, fontweight='bold', pad=15, color='#2E3440')
            ax.set_xlabel('Активы', fontsize=11, fontweight='semibold', color='#4C566A')
            ax.set_ylabel('Активы', fontsize=11, fontweight='semibold', color='#4C566A')
            
            # Enhanced grid
            ax.grid(False)  # No grid for heatmap
            ax.set_facecolor('#F8F9FA')
            
            # Customize spines
            for spine in ax.spines.values():
                spine.set_color('#D1D5DB')
                spine.set_linewidth(0.8)
            
            # Enhance tick labels
            ax.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
            
            # Add subtle background pattern
            ax.set_alpha(0.95)
            
            # Add copyright signature
            chart_styles.add_copyright(ax)
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(fig)
            plt.clf()
            plt.cla()
            
            # Send correlation matrix
            self.logger.info("Sending correlation matrix image...")
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=f"🔗 Корреляционная матрица для {len(symbols)} активов\n\nПоказывает корреляцию между доходностями активов (от -1 до +1)\n\n• +1: полная положительная корреляция\n• 0: отсутствие корреляции\n• -1: полная отрицательная корреляция"
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
        
        welcome_message = f"""🧠 Okama Financial Bot - Полная справка

Привет, {user_name}! Я помогу с анализом рынков и портфелей.

Что умею:
• Анализ одного актива с графиками цен + AI-анализ каждого графика
• Сравнение нескольких активов
• Анализ портфеля (веса, риск/доходность, efficient frontier)
• Макро/товары/валюты
• Анализ инфляции
• Объяснения и рекомендации
• 🆕 AI-анализ изображений графиков - отправьте фото для анализа!

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
    
    async def show_namespace_symbols(self, update: Update, namespace: str):
        """Показать символы в пространстве имен"""
        try:
            import okama as ok
            symbols_df = ok.symbols_in_namespace(namespace)
            
            if symbols_df.empty:
                await self._send_message_safe(update, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                return
            
            # Показываем первые 10 символов
            response = f"📊 Пространство имен: {namespace}\n\n"
            response += f"• Всего символов: {len(symbols_df)}\n\n"
            
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
            
            # Создаем простую таблицу символов
            if first_10:
                response += "Первые 10 символов:\n\n"
                
                # Создаем простую таблицу
                for row in first_10:
                    symbol = row[0]
                    name = row[1]
                    country = row[2]
                    currency = row[3]
                    
                    response += f"• {symbol} - {name} | {country} | {currency}\n"
                
                await self._send_message_safe(update, response)
            else:
                response += f"💡 Используйте `/namespace {namespace}` для полного списка символов"
                await self._send_message_safe(update, response)
            
        except Exception as e:
            await self._send_message_safe(update, f"❌ Ошибка при получении данных для '{namespace}': {str(e)}")
    




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
                
                if daily_chart:
                    # Формируем базовую информацию для подписи
                    caption = f"📊 {symbol} - {asset_info.get('name', 'N/A')}\n\n"
                    caption += f"🏛️ Биржа: {asset_info.get('exchange', 'N/A')}\n"
                    caption += f"🌍 Страна: {asset_info.get('country', 'N/A')}\n"
                    caption += f"💰 Валюта: {asset_info.get('currency', 'N/A')}\n"
                    caption += f"📈 Тип: {asset_info.get('type', 'N/A')}\n"
                    
                    if asset_info.get('current_price') is not None:
                        caption += f"💵 Текущая цена: {asset_info['current_price']:.2f} {asset_info.get('currency', 'N/A')}\n"
                    
                    if asset_info.get('annual_return') != 'N/A':
                        caption += f"📊 Годовая доходность: {asset_info['annual_return']}\n"
                    
                    if asset_info.get('volatility') != 'N/A':
                        caption += f"📉 Волатильность: {asset_info['volatility']}\n"
                    
                    caption += "\n🧠 AI-анализ:\n"
                    
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
                        caption=caption
                    )
                    
                    # Создаем кнопки для дополнительных функций
                    keyboard = [
                        [
                            InlineKeyboardButton("📅 Месячный график (10Y)", callback_data=f"monthly_chart_{symbol}"),
                            InlineKeyboardButton("💵 Дивиденды", callback_data=f"dividends_{symbol}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
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
        """Получить ежедневный график за 1 год с копирайтом"""
        try:
            # Получаем данные для ежедневного графика
            price_history = self.asset_service.get_asset_price_history(symbol, '1Y')
            
            if 'error' in price_history:
                self.logger.error(f"Error in price_history: {price_history['error']}")
                return None
            
            # Ищем ежедневный график
            if 'charts' in price_history and price_history['charts']:
                charts = price_history['charts']
                # Приоритет: adj_close (ежедневные данные), затем fallback
                if 'adj_close' in charts and charts['adj_close']:
                    return charts['adj_close']  # Копирайт уже добавлен в asset_service
                elif 'fallback' in charts and charts['fallback']:
                    return charts['fallback']  # Копирайт уже добавлен в asset_service
                # Если нет ежедневных, берем первый доступный
                for chart_type, chart_data in charts.items():
                    if chart_data:
                        return chart_data  # Копирайт уже добавлен в asset_service
            
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
            
            # Убираем фразы о рекомендациях и заменяем на отказ от ответственности
            analysis_text = analysis_text.replace('рекомендации', 'анализ')
            analysis_text = analysis_text.replace('рекомендуем', 'анализируем')
            analysis_text = analysis_text.replace('рекомендация', 'анализ')
            
            # Добавляем отказ от ответственности
            analysis_text += "\n\n⚠️ Важно: Данный анализ предоставляется исключительно в информационных целях. Для принятия инвестиционных решений обратитесь к опытному финансовому профессионалу."
            
            return analysis_text
            
        except Exception as e:
            self.logger.error(f"Error getting AI analysis for {symbol}: {e}")
            return None

    def _add_copyright_to_chart(self, chart_data: bytes) -> bytes:
        """Добавить копирайт на график"""
        try:
            import matplotlib.pyplot as plt
            import io
            from PIL import Image, ImageDraw, ImageFont
            
            # Конвертируем bytes в PIL Image
            img = Image.open(io.BytesIO(chart_data))
            
            # Создаем объект для рисования
            draw = ImageDraw.Draw(img)
            
            # Получаем размеры изображения
            width, height = img.size
            
            # Добавляем копирайт в правом нижнем углу
            copyright_text = "© Okama Finance Bot"
            
            # Пытаемся использовать системный шрифт
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
                except:
                    font = ImageFont.load_default()
            
            # Получаем размер текста
            bbox = draw.textbbox((0, 0), copyright_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Позиция текста (правый нижний угол с отступом)
            x = width - text_width - 10
            y = height - text_height - 10
            
            # Рисуем фон для текста
            draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], 
                         fill='white', outline='black', width=1)
            
            # Рисуем текст
            draw.text((x, y), copyright_text, fill='black', font=font)
            
            # Конвертируем обратно в bytes
            output = io.BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error adding copyright to chart: {e}")
            # Возвращаем оригинальный график если не удалось добавить копирайт
            return chart_data

    async def namespace_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /namespace command"""
        try:
            import okama as ok
            
            if not context.args:
                # Show available namespaces
                namespaces = ok.namespaces
                
                response = "📚 Доступные пространства имен (namespaces):\n\n"
                response += f"📈 Статистика:\n"
                response += f"• Всего пространств имен: {len(namespaces)}\n\n"
                
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
                
                await self._send_message_safe(update, response)
                
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
                    response = f"📊 Пространство имен: {namespace}\n\n"
                    response += f"📈 Статистика:\n"
                    response += f"• Всего символов: {total_symbols}\n"
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
                    
                    # Создаем простую таблицу символов
                    if first_10:
                        response += "Первые 10 символов:\n\n"
                        
                        # Создаем простую таблицу
                        for row in first_10:
                            symbol = row[0]
                            name = row[1]
                            country = row[2]
                            currency = row[3]
                            
                            response += f"• {symbol} - {name} | {country} | {currency}\n"
                        
                        # Отправляем основное сообщение с таблицей
                        await self._send_message_safe(update, response)
                        
                        # Если есть еще символы, показываем их отдельно
                        if last_10 and total_symbols > 10:
                            last_response = "Последние 10 символов:\n\n"
                            
                            # Создаем таблицу для последних символов
                            for row in last_10:
                                symbol = row[0]
                                name = row[1]
                                country = row[2]
                                currency = row[3]
                                
                                last_response += f"• {symbol} - {name} | {country} | {currency}\n"
                            
                            await self._send_message_safe(update, last_response)
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

    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command for comparing multiple assets"""
        try:
            if not context.args:
                await self._send_message_safe(update, 
                    "📊 Команда /compare - Сравнение активов\n\n"
                    "Использование:\n"
                    "`/compare символ1 символ2 символ3 ...`\n"
                    "или\n"
                    "`/compare символ1,символ2,символ3`\n"
                    "или\n"
                    "`/compare символ1, символ2, символ3`\n\n"
                    "Примеры:\n"
                    "• `/compare SPY.US QQQ.US` - сравнить S&P 500 и NASDAQ (в USD)\n"
                    "• `/compare SBER.MOEX,GAZP.MOEX` - сравнить Сбербанк и Газпром (в RUB)\n"
                    "• `/compare SPY.US, QQQ.US, VOO.US` - сравнить с пробелами после запятых\n"
                    "• `/compare GC.COMM CL.COMM` - сравнить золото и нефть (в USD)\n"
                    "• `/compare VOO.US,BND.US,GC.COMM` - сравнить акции, облигации и золото (в USD)\n\n"
                                                             "Что вы получите:\n"
                    "✅ График накопленной доходности всех активов\n"
                    "✅ Кнопки для дополнительного анализа:\n"
                    "   📉 Drawdowns - график рисков и волатильности\n"
                    "   💰 Dividends - график дивидендной доходности\n"
                    "   🔗 Correlation Matrix - корреляционная матрица\n"
                    "✅ Сравнительный анализ\n"
                    "✅ AI-рекомендации\n\n"
                    "💡 Автоматическое определение валюты:\n"
                    "• Первый актив в списке определяет базовую валюту\n"
                    "• MOEX активы → RUB, US активы → USD, LSE → GBP\n"
                    "• Остальные → USD по умолчанию\n\n"
                    "📅 Период сравнения:\n"
                    "• Используется полный доступный период данных\n"
                    "• Максимальная глубина исторического анализа\n"
                    "• Покрывает все доступные рыночные циклы\n\n"
                    "Поддерживаемые форматы:\n"
                    "• US акции: AAPL.US, VOO.US, SPY.US\n"
                    "• MOEX: SBER.MOEX, GAZP.MOEX\n"
                    "• Индексы: SPX.INDX, IXIC.INDX\n"
                    "• Товары: GC.COMM, CL.COMM, SI.COMM\n"
                    "• Валюты: EURUSD.FX, GBPUSD.FX"
                )
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
                        symbols.append(symbol_part.upper())
                self.logger.info(f"Parsed comma-separated symbols: {symbols}")
            else:
                # Handle space-separated symbols (original behavior)
                symbols = [symbol.upper() for symbol in context.args]
                self.logger.info(f"Parsed space-separated symbols: {symbols}")
            
            # Clean up symbols (remove empty strings and whitespace)
            symbols = [symbol for symbol in symbols if symbol.strip()]
            
            if len(symbols) < 2:
                await self._send_message_safe(update, "❌ Необходимо указать минимум 2 символа для сравнения")
                return
            
            if len(symbols) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 символов для сравнения")
                return

            await self._send_message_safe(update, f"🔄 Сравниваю активы: {', '.join(symbols)}...")

            # Create comparison using okama
            import okama as ok
            
            # Determine base currency from the first asset
            first_symbol = symbols[0]
            currency_info = ""
            try:
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
                # Create AssetList for comparison with detected currency (full period)
                asset_list = ok.AssetList(symbols, ccy=currency)
                
                self.logger.info(f"Created AssetList with full available period")
                
                # Generate beautiful comparison chart
                plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
                
                fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
                
                # Plot with enhanced styling
                asset_list.wealth_indexes.plot(ax=ax, linewidth=2.5, alpha=0.9)
                
                # Enhanced chart customization
                ax.set_title(f'Накопленная доходность\n{", ".join(symbols)}', 
                           fontsize=16, fontweight='bold', pad=20, color='#2E3440')
                ax.set_xlabel('Дата', fontsize=13, fontweight='semibold', color='#4C566A')
                ax.set_ylabel(f'Накопленная доходность ({currency})', fontsize=13, fontweight='semibold', color='#4C566A')
                
                # Enhanced grid and background
                ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.8)
                ax.set_facecolor('#F8F9FA')
                
                # Enhanced legend
                ax.legend(fontsize=11, frameon=True, fancybox=True, shadow=True, 
                         loc='upper left', bbox_to_anchor=(0.02, 0.98))
                
                # Customize spines
                for spine in ax.spines.values():
                    spine.set_color('#D1D5DB')
                    spine.set_linewidth(0.8)
                
                # Enhance tick labels
                ax.tick_params(axis='both', which='major', labelsize=10, colors='#4C566A')
                
                # Add subtle background pattern
                ax.set_alpha(0.95)
                
                # Add copyright signature
                chart_styles.add_copyright(ax)
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                plt.close(fig)
                plt.clf()
                plt.cla()
                
                # Get basic statistics
                stats_text = f"📊 Сравнение: {', '.join(symbols)}\n\n"
                stats_text += f"💰 Базовая валюта: {currency} ({currency_info})\n"
                stats_text += f"📅 Период: {asset_list.first_date} - {asset_list.last_date}\n"
                stats_text += f"⏱️ Длительность: {asset_list.period_length}\n\n"
                
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
                #await self.send_long_message(update, stats_text)
                
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
                    caption=stats_text,
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
                    "✅ AI-анализ и рекомендации"
                )
                return

            # Extract symbols and weights from command arguments
            raw_args = ' '.join(context.args)
            portfolio_data = []
            
            for arg in raw_args.split():
                if ':' in arg:
                    symbol_part, weight_part = arg.split(':', 1)
                    symbol = symbol_part.strip().upper()
                    weight = float(weight_part.strip())
                    
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
                await self._send_message_safe(update, f"❌ Сумма долей должна быть равна 1.0, текущая сумма: {total_weight:.3f}")
                return
            
            if len(portfolio_data) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 активов в портфеле")
                return
            
            symbols = [symbol for symbol, _ in portfolio_data]
            weights = [weight for _, weight in portfolio_data]
            
            await self._send_message_safe(update, f"🔄 Создаю портфель: {', '.join(symbols)}...")
            
            # Create portfolio using okama
            import okama as ok
            
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
                # Create Portfolio with detected currency
                portfolio = ok.Portfolio(symbols, ccy=currency, weights=weights)
                
                self.logger.info(f"Created Portfolio with weights: {weights}")
                
                # Generate beautiful portfolio chart
                fig, ax = chart_styles.create_figure()
                
                # Apply base style
                chart_styles.apply_base_style(fig, ax)
                
                # Plot portfolio wealth index with spline interpolation
                x_data = portfolio.wealth_index.index
                y_data = portfolio.wealth_index.values
                chart_styles.plot_smooth_line(ax, x_data, y_data, color='#2E5BBA', label='Портфель')
                
                # Enhanced chart customization
                ax.set_title(f'Накопленная доходность портфеля\n{", ".join(symbols)}', 
                           fontsize=chart_styles.title_config['fontsize'], 
                           fontweight=chart_styles.title_config['fontweight'], 
                           pad=chart_styles.title_config['pad'], 
                           color=chart_styles.title_config['color'])
                ax.set_xlabel('Дата', fontsize=chart_styles.axis_config['label_fontsize'], 
                             fontweight=chart_styles.axis_config['label_fontweight'], 
                             color=chart_styles.axis_config['label_color'])
                ax.set_ylabel(f'Накопленная доходность ({currency})', fontsize=chart_styles.axis_config['label_fontsize'], 
                              fontweight=chart_styles.axis_config['label_fontweight'], 
                              color=chart_styles.axis_config['label_color'])
                
                # Enhanced legend
                ax.legend(**chart_styles.legend_config)
                
                # Add copyright signature
                chart_styles.add_copyright(ax)
                
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
                portfolio_text += f"📅 Период: {portfolio.first_date} - {portfolio.last_date}\n"
                # Safely get period length
                try:
                    period_length = str(portfolio.period_length)
                    portfolio_text += f"⏱️ Длительность: {period_length}\n\n"
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
                    if hasattr(final_value, '__iter__') and not isinstance(final_value, str):
                        # If it's a Series, get the first value
                        final_value = final_value.iloc[0] if hasattr(final_value, 'iloc') else list(final_value)[0]
                    portfolio_text += f"\n📈 Накопленная доходность портфеля: {float(final_value):.2f} {currency}"
                except Exception as e:
                    self.logger.warning(f"Could not get final portfolio value: {e}")
                    portfolio_text += f"\n📈 Накопленная доходность портфеля: недоступна"
                
                # Send portfolio chart and information
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=portfolio_text
                )
                
                # Store portfolio data in context
                user_id = update.effective_user.id
                self._update_user_context(
                    user_id, 
                    last_assets=symbols,
                    last_analysis_type='portfolio',
                    last_period='MAX',
                    current_symbols=symbols,
                    current_currency=currency,
                    current_currency_info=currency_info,
                    portfolio_weights=weights
                )
                
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
        """Отправить сообщение в callback query"""
        try:
            if update.callback_query:
                # Для callback query используем context.bot.send_message
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=text,
                    parse_mode=parse_mode
                )
            elif update.message:
                # Для обычных сообщений используем _send_message_safe
                await self._send_message_safe(update, text, parse_mode)
            else:
                # Если ни то, ни другое - логируем ошибку
                self.logger.error("Cannot send message: neither callback_query nor message available")
        except Exception as e:
            self.logger.error(f"Error sending callback message: {e}")
            # Fallback: попробуем отправить через context.bot
            try:
                if update.callback_query:
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
            import okama as ok
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
            import okama as ok
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
            import okama as ok
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
                    caption=caption
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
                    # Формируем краткую информацию о дивидендах
                    dividend_response = f"💵 Дивиденды {symbol}\n\n"
                    dividend_response += f"📊 Количество выплат: {len(dividends)}\n"
                    dividend_response += f"💰 Валюта: {currency}\n"
                    dividend_response += f"📈 График содержит таблицу последних выплат"
                    
                    # Получаем график дивидендов с таблицей
                    dividend_chart = await self._get_dividend_chart(symbol)
                    
                    if dividend_chart:
                        await update.callback_query.message.reply_photo(
                            photo=dividend_chart,
                            caption=dividend_response
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
        """Получить месячный график за 10 лет с копирайтом"""
        try:
            # Получаем данные для месячного графика
            price_history = self.asset_service.get_asset_price_history(symbol, '10Y')
            
            if 'error' in price_history:
                self.logger.error(f"Error in price_history: {price_history['error']}")
                return None
            
            # Ищем месячный график
            if 'charts' in price_history and price_history['charts']:
                charts = price_history['charts']
                for chart_data in charts:
                    if chart_data:
                        # Добавляем копирайт на график
                        return self._add_copyright_to_chart(chart_data)
            
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
                # Добавляем копирайт на изображение
                return self._add_copyright_to_chart(dividend_table)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting dividend table image for {symbol}: {e}")
            return None

    def _create_dividend_chart(self, symbol: str, dividends: dict, currency: str) -> Optional[bytes]:
        """Создать график дивидендов с таблицей выплат на графике"""
        try:
            import matplotlib.pyplot as plt
            import io
            import pandas as pd
            from datetime import datetime
            
            # Конвертируем дивиденды в pandas Series
            dividend_series = pd.Series(dividends)
            
            # Сортируем по дате
            dividend_series = dividend_series.sort_index()
            
            # Создаем график с увеличенной высотой для таблицы
            plt.style.use('fivethirtyeight')
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Рисуем столбчатую диаграмму
            dates = [pd.to_datetime(date) for date in dividend_series.index]
            amounts = dividend_series.values
            
            bars = ax.bar(dates, amounts, color='#2E8B57', alpha=0.7, width=20)
            
            # Настройка графика
            ax.set_title(f'Дивиденды {symbol}', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Дата', fontsize=12)
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
            
            # Создаем таблицу дивидендов в правой части графика
            # Берем последние 10 выплат для таблицы
            recent_dividends = dividend_series.tail(10).sort_index(ascending=False)
            
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
            
            # Добавляем таблицу на график
            table = ax.table(cellText=table_data,
                           colLabels=table_headers,
                           cellLoc='center',
                           loc='right',
                           bbox=[0.65, 0.1, 0.3, 0.8])
            
            # Стилизуем таблицу
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)
            
            # Цвета для заголовков и ячеек
            for i in range(len(table_headers)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Цвета для строк данных (чередование)
            for i in range(1, len(table_data) + 1):
                for j in range(len(table_headers)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#F5F5F5')
                    else:
                        table[(i, j)].set_facecolor('#FFFFFF')
                    table[(i, j)].set_text_props(color='black')
            
            # Добавляем заголовок таблицы
            ax.text(0.8, 0.95, 'Последние выплаты', transform=ax.transAxes,
                   fontsize=12, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#4CAF50', alpha=0.8))
            
            # Настраиваем layout
            plt.subplots_adjust(right=0.85)
            
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
            import matplotlib.pyplot as plt
            import io
            import pandas as pd
            from datetime import datetime
            
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
            
            # Создаем фигуру для таблицы
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.axis('tight')
            ax.axis('off')
            
            # Создаем таблицу
            table = ax.table(cellText=table_data,
                           colLabels=table_headers,
                           cellLoc='center',
                           loc='center')
            
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
