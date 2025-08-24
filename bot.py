import sys
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import io
from typing import Dict, List, Optional

# Check Python version compatibility
if sys.version_info < (3, 8):
    print("ERROR: Python 3.8+ required. Current version:", sys.version)
    sys.exit(1)

from config import Config
from okama_service import OkamaService
from yandexgpt_service import YandexGPTService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OkamaFinanceBot:
    """Main Telegram bot class for financial analysis with Okama and YandexGPT"""
    
    def __init__(self):
        """Initialize the bot with required services"""
        Config.validate()
        
        self.okama_service = OkamaService()
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

Привет {user_name}! Я ваш помощник по финансовому анализу на базе YandexGPT.

Что я умею:
• Анализ и оптимизация портфеля
• Оценка рисков и метрики
• Анализ корреляции активов
• Генерация эффективной границы
• Сравнение активов
• Чат с YandexGPT о финансах

Быстрый старт:
• Отправьте мне символы как "RGBITR.INDX MCFTR.INDX GC.COMM"
• Спросите "Проанализируй портфель AGG.US SPY.US"
• Используйте команды /portfolio, /risk, /correlation

Команды:
/help - Показать все доступные команды
/portfolio - Анализ портфеля
/risk - Метрики риска
/correlation - Матрица корреляции
/efficient_frontier - Эффективная граница
/compare - Сравнение активов
/chat - Чат с YandexGPT

Готовы анализировать ваши инвестиции?"""
        
        keyboard = [
            [InlineKeyboardButton("Анализ портфеля", callback_data="portfolio_help")],
            [InlineKeyboardButton("Метрики риска", callback_data="risk_help")],
            [InlineKeyboardButton("Корреляция", callback_data="correlation_help")],
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

Основные команды анализа:
/portfolio [symbols] - Анализ производительности портфеля
/risk [symbols] - Расчет метрик риска (VaR, CVaR, волатильность)
/correlation [symbols] - Генерация матрицы корреляции
/efficient_frontier [symbols] - Создание графика эффективной границы
/compare [symbols] - Сравнение нескольких активов
/pension [symbols] [weights] [amount] [cashflow] [rebalancing] - Пенсионный портфель
/monte_carlo [symbols] [years] [scenarios] [distribution] - Прогнозирование Монте-Карло
/allocation [symbols] - Детальный анализ распределения активов
/test [symbols] - Тест интеграции Okama
/testai - Тест подключения к YandexGPT API

Чат с YandexGPT:
/chat [question] - Получить финансовый совет от YandexGPT

Примеры:
• /portfolio RGBITR.INDX MCFTR.INDX
• /risk AGG.US SPY.US
• /correlation RGBITR.INDX MCFTR.INDX GC.COMM
• /compare AGG.US SPY.US GC.COMM
• /pension RGBITR.INDX MCFTR.INDX 0.6 0.4 1000000 -50000 year
• /monte_carlo AGG.US SPY.US 20 100 norm
• /allocation RGBITR.INDX MCFTR.INDX GC.COMM

Естественный язык:
Вы также можете просто написать естественным языком:
• "Проанализируй мой портфель AGG.US SPY.US"
• "Какой риск у GC.COMM?"
• "Сравни RGBITR.INDX с MCFTR.INDX"
• "Как оптимизировать мой портфель?"

Нужна помощь?
Просто напишите ваш вопрос или используйте команды выше!"""
        
        await update.message.reply_text(help_text)
    
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        if not context.args:
            await update.message.reply_text(
                "Анализ портфеля\n\n"
                "Пожалуйста, укажите символы:\n"
                "/portfolio RGBITR.INDX MCFTR.INDX\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_portfolio(update, symbols)
    
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command"""
        if not context.args:
            await update.message.reply_text(
                "Анализ рисков\n\n"
                "Пожалуйста, укажите символы:\n"
                "/risk AGG.US SPY.US\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_risk(update, symbols)
    
    async def correlation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /correlation command"""
        if not context.args:
            await update.message.reply_text(
                "Анализ корреляции\n\n"
                "Пожалуйста, укажите символы:\n"
                "/correlation RGBITR.INDX MCFTR.INDX GC.COMM\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_correlation(update, symbols)
    
    async def efficient_frontier_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /efficient_frontier command"""
        if not context.args:
            await update.message.reply_text(
                "Эффективная граница\n\n"
                "Пожалуйста, укажите символы:\n"
                "/efficient_frontier RGBITR.INDX MCFTR.INDX\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._generate_efficient_frontier(update, symbols)
    
    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command"""
        if not context.args:
            await update.message.reply_text(
                "Сравнение активов\n\n"
                "Пожалуйста, укажите символы:\n"
                "/compare AGG.US SPY.US GC.COMM\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._compare_assets(update, symbols)
    
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

    async def pension_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pension command for pension portfolio analysis"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Пенсионный портфель\n\n"
                "Пожалуйста, укажите символы, веса и параметры:\n"
                "/pension RGBITR.INDX MCFTR.INDX GC.COMM 0.6 0.3 0.1 1000000 -50000 year\n\n"
                "Формат: /pension [символы] [веса] [начальная_сумма] [ежемесячный_поток] [период_ребалансировки]\n"
                "Пример: /pension RGBITR.INDX MCFTR.INDX 0.6 0.4 1000000 -50000 year"
            )
            return
        
        try:
            # Parse arguments
            args = context.args
            if len(args) >= 6:  # Full format with weights
                symbols = args[:3]  # First 3 are symbols
                weights = [float(w) for w in args[3:6]]  # Next 3 are weights
                initial_amount = float(args[6]) if len(args) > 6 else 1000000
                cashflow = float(args[7]) if len(args) > 7 else -50000
                rebalancing = args[8] if len(args) > 8 else 'year'
            else:
                # Simple format: symbols only
                symbols = args
                weights = None  # Equal weights
                initial_amount = 1000000
                cashflow = -50000
                rebalancing = 'year'
            
            symbols = [s.upper() for s in symbols]
            await self._analyze_pension_portfolio(update, symbols, weights, initial_amount, cashflow, rebalancing)
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка в параметрах: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка создания пенсионного портфеля: {str(e)}")

    async def monte_carlo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monte_carlo command for portfolio forecasting"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Прогнозирование методом Монте-Карло\n\n"
                "Пожалуйста, укажите символы и параметры:\n"
                "/monte_carlo RGBITR.INDX MCFTR.INDX 30 50 norm\n\n"
                "Формат: /monte_carlo [символы] [годы] [сценарии] [распределение]\n"
                "Пример: /monte_carlo AGG.US SPY.US 20 100 norm\n"
                "Распределения: norm (нормальное), lognorm (логарифмически нормальное)"
            )
            return
        
        try:
            # Parse arguments
            args = context.args
            symbols = args[:-3]  # All but last 3 are symbols
            years = int(args[-3])
            n_scenarios = int(args[-2])
            distribution = args[-1]
            
            symbols = [s.upper() for s in symbols]
            
            # Validate parameters
            if years <= 0 or years > 50:
                await update.message.reply_text("❌ Годы должны быть от 1 до 50")
                return
            if n_scenarios <= 0 or n_scenarios > 1000:
                await update.message.reply_text("❌ Количество сценариев должно быть от 1 до 1000")
                return
            if distribution not in ['norm', 'lognorm']:
                await update.message.reply_text("❌ Поддерживаемые распределения: norm, lognorm")
                return
            
            await self._generate_monte_carlo_forecast(update, symbols, years, n_scenarios, distribution)
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка в параметрах: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка прогнозирования: {str(e)}")

    async def allocation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /allocation command for detailed asset allocation analysis"""
        if not context.args:
            await update.message.reply_text(
                "Анализ распределения активов\n\n"
                "Пожалуйста, укажите символы:\n"
                "/allocation RGBITR.INDX MCFTR.INDX GC.COMM\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_asset_allocation(update, symbols)

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
                if intent == 'portfolio':
                    await self._analyze_portfolio(update, symbols)
                elif intent == 'risk':
                    await self._analyze_risk(update, symbols)
                elif intent == 'correlation':
                    await self._analyze_correlation(update, symbols)
                elif intent == 'efficient_frontier':
                    await self._generate_efficient_frontier(update, symbols)
                elif intent == 'compare':
                    await self._compare_assets(update, symbols)
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
        
        if query.data == "portfolio_help":
            await query.edit_message_text(
                "Анализ портфеля\n\n"
                "Отправьте мне символы для анализа:\n"
                "• RGBITR.INDX MCFTR.INDX\n"
                "• /portfolio AGG.US SPY.US\n\n"
                "Я покажу вам:\n"
                "• Метрики производительности\n"
                "• Анализ рисков\n"
                "• Графики и выводы"
            )
        elif query.data == "risk_help":
            await query.edit_message_text(
                "Анализ рисков\n\n"
                "Отправьте мне символы для анализа рисков:\n"
                "• AGG.US SPY.US\n"
                "• /risk GC.COMM\n\n"
                "Я покажу вам:\n"
                "• Метрики волатильности\n"
                "• VaR и CVaR\n"
                "• Матрицу корреляции"
            )
        elif query.data == "correlation_help":
            await query.edit_message_text(
                "Анализ корреляции\n\n"
                "Отправьте мне символы для просмотра корреляций:\n"
                "• RGBITR.INDX MCFTR.INDX GC.COMM\n"
                "• /correlation AGG.US SPY.US\n\n"
                "Я покажу вам:\n"
                "• Тепловую карту корреляции\n"
                "• Выводы о взаимосвязях\n"
                "• Анализ диверсификации"
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
    
    async def _analyze_portfolio(self, update: Update, symbols: List[str]):
        """Analyze portfolio performance"""
        try:
            # Filter out empty strings and validate symbols
            symbols = [s.strip() for s in symbols if s.strip()]
            if not symbols:
                await update.message.reply_text("❌ Ошибка: Не указаны символы для анализа")
                return
                
            await update.message.reply_text(f"📊 Analyzing portfolio: {', '.join(symbols)}...")
            
            # Create portfolio
            portfolio = self.okama_service.create_portfolio(symbols)
            
            # Get performance metrics
            metrics = self.okama_service.get_portfolio_performance(portfolio)
            
            # Generate performance chart
            chart_image = self.okama_service.generate_performance_chart(portfolio)
            
            # Get AI insights
            insights = self.yandexgpt_service.enhance_analysis_results(
                "portfolio", metrics, f"portfolio analysis for {', '.join(symbols)}"
            )
            
            # Format metrics message
            metrics_text = f"""📊 Portfolio Analysis: {', '.join(symbols)}

Performance Metrics:
• Total Return: {metrics.get('total_return', 'N/A')}
• Annual Return: {metrics.get('annual_return', 'N/A')}
• Volatility: {metrics.get('volatility', 'N/A')}
• Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}
• Max Drawdown: {metrics.get('max_drawdown', 'N/A')}
• VaR (95%): {metrics.get('var_95', 'N/A')}
• CVaR (95%): {metrics.get('cvar_95', 'N/A')}

AI Insights:
{insights}"""
            
            # Send chart with caption
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(chart_image),
                caption=metrics_text
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа портфеля: {str(e)}")
    
    async def _analyze_risk(self, update: Update, symbols: List[str]):
        """Analyze risk metrics"""
        try:
            # Filter out empty strings and validate symbols
            symbols = [s.strip() for s in symbols if s.strip()]
            if not symbols:
                await update.message.reply_text("❌ Ошибка: Не указаны символы для анализа")
                return
                
            await update.message.reply_text(f"Анализ рисков для: {', '.join(symbols)}...")
            
            # Get individual asset risk metrics
            risk_data = {}
            for symbol in symbols:
                risk_data[symbol] = self.okama_service.get_asset_info(symbol)
            
            # Generate correlation matrix
            correlation_image = self.okama_service.generate_correlation_matrix(symbols)
            
            # Format risk metrics
            risk_text = f"""📈 Risk Analysis: {', '.join(symbols)}

Individual Asset Risk:
"""
            for symbol, data in risk_data.items():
                if 'error' not in data:
                    risk_text += f"""
• {symbol}:
  - Volatility: {data.get('volatility', 'N/A')}
  - VaR (95%): {data.get('var_95', 'N/A')}
  - CVaR (95%): {data.get('cvar_95', 'N/A')}
  - Max Drawdown: {data.get('max_drawdown', 'N/A')}
"""
                else:
                    risk_text += f"• {symbol}: Error - {data['error']}\n"
            
            risk_text += "\nCorrelation Matrix Below"
            
            # Send correlation matrix
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(correlation_image),
                caption=risk_text
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error analyzing risk: {str(e)}")
    
    async def _analyze_correlation(self, update: Update, symbols: List[str]):
        """Analyze asset correlations"""
        try:
            # Filter out empty strings and validate symbols
            symbols = [s.strip() for s in symbols if s.strip()]
            if not symbols:
                await update.message.reply_text("❌ Ошибка: Не указаны символы для анализа")
                return
                
            await update.message.reply_text(f"🔗 Analyzing correlations for: {', '.join(symbols)}...")
            
            # Generate correlation matrix
            correlation_image = self.okama_service.generate_correlation_matrix(symbols)
            
            # Get AI insights
            insights = self.yandexgpt_service.enhance_analysis_results(
                "correlation", {"symbols": symbols}, f"correlation analysis for {', '.join(symbols)}"
            )
            
            caption = f"""🔗 Correlation Matrix: {', '.join(symbols)}

AI Insights:
{insights}

Interpretation:
• Values closer to 1 = Strong positive correlation
• Values closer to -1 = Strong negative correlation  
• Values closer to 0 = Low correlation"""
            
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(correlation_image),
                caption=caption
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error analyzing correlations: {str(e)}")
    
    async def _generate_efficient_frontier(self, update: Update, symbols: List[str]):
        """Generate efficient frontier plot"""
        try:
            # Filter out empty strings and validate symbols
            symbols = [s.strip() for s in symbols if s.strip()]
            if not symbols:
                await update.message.reply_text("❌ Ошибка: Не указаны символы для анализа")
                return
                
            await update.message.reply_text(f"🎯 Generating efficient frontier for: {', '.join(symbols)}...")
            
            # Generate efficient frontier
            frontier_image = self.okama_service.generate_efficient_frontier(symbols)
            
            caption = f"""🎯 Efficient Frontier: {', '.join(symbols)}

What This Shows:
• The optimal risk-return combinations
• Each point represents a different portfolio allocation
• Lower left = Lower risk, lower return
• Upper right = Higher risk, higher return
• The curve shows the most efficient portfolios

Use This To:
• Find your optimal risk tolerance
• Compare portfolio efficiency
• Optimize asset allocation"""
            
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(frontier_image),
                caption=caption
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating efficient frontier: {str(e)}")
    
    async def _compare_assets(self, update: Update, symbols: List[str]):
        """Compare multiple assets"""
        try:
            # Filter out empty strings and validate symbols
            symbols = [s.strip() for s in symbols if s.strip()]
            if not symbols:
                await update.message.reply_text("❌ Ошибка: Не указаны символы для анализа")
                return
                
            await update.message.reply_text(f"📋 Comparing assets: {', '.join(symbols)}...")
            
            # Compare assets
            comparison_metrics, comparison_image = self.okama_service.compare_assets(symbols)
            
            # Format comparison text
            comparison_text = f"""📋 Asset Comparison: {', '.join(symbols)}

Performance Metrics:
"""
            for symbol, metrics in comparison_metrics.items():
                if 'error' not in metrics:
                    comparison_text += f"""
• {symbol}:
  - Total Return: {metrics.get('total_return', 'N/A'):.2%}
  - Annual Return: {metrics.get('annual_return', 'N/A'):.2%}
  - Volatility: {metrics.get('volatility', 'N/A'):.2%}
  - Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.2f}
  - Max Drawdown: {metrics.get('max_drawdown', 'N/A'):.2%}
"""
                else:
                    comparison_text += f"• {symbol}: Error - {metrics['error']}\n"
            
            # Send comparison chart
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(comparison_image),
                caption=comparison_text
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error comparing assets: {str(e)}")

    async def _analyze_pension_portfolio(self, update: Update, symbols: List[str], weights: Optional[List[float]], 
                                       initial_amount: float, cashflow: float, rebalancing: str):
        """Analyze pension portfolio with cash flows"""
        try:
            await update.message.reply_text(
                f"🏦 Создание пенсионного портфеля: {', '.join(symbols)}...\n"
                f"Начальная сумма: {initial_amount:,.0f}\n"
                f"Ежемесячный поток: {cashflow:+,.0f}\n"
                f"Ребалансировка: {rebalancing}"
            )
            
            # Create pension portfolio
            portfolio = self.okama_service.create_pension_portfolio(
                symbols, weights, 'RUB', initial_amount, cashflow, rebalancing
            )
            
            # Get portfolio metrics
            metrics = self.okama_service.get_portfolio_performance(portfolio)
            
            # Get inflation analysis
            inflation_metrics, inflation_chart = self.okama_service.get_inflation_analysis(portfolio)
            
            # Format metrics message
            weights_text = f"[{', '.join([f'{w:.1%}' for w in (weights or [1/len(symbols)]*len(symbols))])}]"
            
            metrics_text = f"""🏦 Пенсионный портфель: {', '.join(symbols)}

Конфигурация:
• Веса: {weights_text}
• Начальная сумма: {initial_amount:,.0f}
• Ежемесячный поток: {cashflow:+,.0f}
• Ребалансировка: {rebalancing}

Метрики производительности:
• Общая доходность: {metrics.get('total_return', 'N/A')}
• Годовая доходность: {metrics.get('annual_return', 'N/A')}
• Волатильность: {metrics.get('volatility', 'N/A')}
• Коэффициент Шарпа: {metrics.get('sharpe_ratio', 'N/A')}
• Максимальная просадка: {metrics.get('max_drawdown', 'N/A')}

Анализ с учетом инфляции:
• Текущая стоимость: {inflation_metrics.get('current_value', 'N/A')}
• Доходность с учетом инфляции: {inflation_metrics.get('inflation_adjusted_return', 'N/A')}"""
            
            # Send inflation chart with caption
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(inflation_chart),
                caption=metrics_text
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа пенсионного портфеля: {str(e)}")

    async def _generate_monte_carlo_forecast(self, update: Update, symbols: List[str], years: int, n_scenarios: int, distribution: str):
        """Generate Monte Carlo portfolio forecasting"""
        try:
            await update.message.reply_text(
                f"🔮 Прогнозирование портфеля методом Монте-Карло для: {', '.join(symbols)}...\n"
                f"Период: {years} лет\n"
                f"Сценарии: {n_scenarios}\n"
                f"Распределение: {distribution}"
            )
            
            # Generate Monte Carlo forecast
            forecast_image = self.okama_service.generate_monte_carlo_forecast(symbols, years, n_scenarios, distribution)
            
            caption = f"""🔮 Monte Carlo Forecast: {', '.join(symbols)}

What This Shows:
• Probability of achieving a specific future value
• Distribution of potential returns
• Risk and return trade-offs
• Simulate future market conditions

Use This To:
• Forecast portfolio performance
• Assess risk tolerance
• Plan for future investments"""
            
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(forecast_image),
                caption=caption
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating Monte Carlo forecast: {str(e)}")

    async def allocation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /allocation command for detailed asset allocation analysis"""
        if not context.args:
            await update.message.reply_text(
                "Анализ распределения активов\n\n"
                "Пожалуйста, укажите символы:\n"
                "/allocation RGBITR.INDX MCFTR.INDX GC.COMM\n\n"
                "Или просто отправьте мне символы напрямую!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_asset_allocation(update, symbols)

    async def _analyze_asset_allocation(self, update: Update, symbols: List[str]):
        """Analyze detailed asset allocation"""
        try:
            await update.message.reply_text(f"📊 Анализ распределения активов для: {', '.join(symbols)}...")
            
            # Create portfolio for analysis
            portfolio = self.okama_service.create_portfolio(symbols)
            
            # Get asset allocation analysis
            allocation_metrics, allocation_chart = self.okama_service.get_asset_allocation_analysis(portfolio)
            
            # Format allocation message
            allocation_text = f"""📊 Анализ распределения активов: {', '.join(symbols)}

Общая информация:
• Количество активов: {allocation_metrics.get('total_assets', 'N/A')}
• Валюта портфеля: {allocation_metrics.get('currency', 'N/A')}
• Общая стоимость: {allocation_metrics.get('total_value', 'N/A')}

Распределение весов:
• {', '.join([f'{symbol}: {weight:.1%}' for symbol, weight in zip(allocation_metrics.get('symbols', []), allocation_metrics.get('weights', []))])}

Детальный анализ показывает:
• Индивидуальные характеристики активов
• Сравнение метрик производительности
• Анализ рисков по каждому активу
• Рекомендации по оптимизации"""
            
            # Send allocation chart with caption
            await update.get_bot().send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(allocation_chart),
                caption=allocation_text
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа распределения активов: {str(e)}")

    async def _handle_chat(self, update: Update, question: str):
        """Handle AI chat requests"""
        try:
            await update.message.reply_text("🤔 Thinking...")
            
            # Get AI response
            response = self.yandexgpt_service.get_financial_advice(question)
            
            # Send response
            await update.message.reply_text(
                f"💬 AI Financial Advisor\n\n{response}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting AI response: {str(e)}")

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command to debug Okama integration"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "Тестовая команда\n\n"
                    "Пожалуйста, укажите символы для тестирования:\n"
                    "/test RGBITR.INDX MCFTR.INDX\n\n"
                    "Это протестирует интеграцию с Okama и покажет доступные атрибуты."
                )
                return
            
            symbols = [s.upper() for s in context.args]
            await update.message.reply_text(f"🧪 Testing Okama integration with symbols: {', '.join(symbols)}...")
            
            # Test individual assets
            results = []
            for symbol in symbols:
                result = self.okama_service.test_asset_data(symbol)
                results.append(result)
            
            # Format results
            test_text = "🧪 Asset Data Test Results:\n\n"
            for result in results:
                if result['status'] == 'success':
                    test_text += f"✅ {result['symbol']}:\n"
                    test_text += f"   Data sources: {', '.join([f'{k}: {v}' for k, v in result['data_sources'].items()])}\n"
                    test_text += f"   Metrics: {', '.join([f'{k}: {v}' for k, v in result['metrics'].items()])}\n\n"
                else:
                    test_text += f"❌ {result['symbol']}: {result['error']}\n\n"
            
            await update.message.reply_text(test_text)
            
            # Run the original test
            test_results = self.okama_service.test_okama_integration(symbols)
            
            # Format results
            result_text = f"🧪 Okama Integration Test Results\n\n"
            result_text += f"Symbols tested: {', '.join(symbols)}\n"
            result_text += f"Okama version: {test_results.get('okama_version', 'Unknown')}\n\n"
            
            if 'assets' in test_results:
                result_text += "Asset Tests:\n"
                for symbol, status in test_results['assets'].items():
                    result_text += f"• {symbol}: {status}\n"
            
            result_text += f"\nPortfolio Test: {test_results.get('portfolio', 'N/A')}"
            
            if 'error' in test_results:
                result_text += f"\n\n❌ Test Error: {test_results['error']}"
            
            await update.message.reply_text(result_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error running test: {str(e)}")
    
    async def test_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /testai command to test YandexGPT API connection"""
        try:
            await update.message.reply_text("Тестирование подключения к YandexGPT API...")
            
            # Test the API connection
            test_results = self.yandexgpt_service.test_api_connection()
            
            # Format results
            result_text = f"Результаты теста YandexGPT API\n\n"
            result_text += f"Статус: {test_results.get('status', 'Неизвестно')}\n"
            result_text += f"Сообщение: {test_results.get('message', 'Нет сообщения')}\n\n"
            
            if 'config' in test_results:
                config = test_results['config']
                result_text += "Конфигурация:\n"
                result_text += f"• API ключ: {'✓ Установлен' if config.get('api_key_set') else '✗ НЕ УСТАНОВЛЕН'}\n"
                result_text += f"• ID папки: {'✓ Установлен' if config.get('folder_id_set') else '✗ НЕ УСТАНОВЛЕН'}\n"
                result_text += f"• Базовый URL: {config.get('base_url', 'Неизвестно')}\n\n"
            
            if 'response' in test_results:
                result_text += f"Ответ API: {test_results['response']}\n\n"
            
            if test_results.get('status') == 'error':
                result_text += "❌ Тест API не удался. Проверьте конфигурацию."
            elif test_results.get('status') == 'success':
                result_text += "✅ Тест API успешен!"
            else:
                result_text += "⚠️ Тест API имел проблемы."
            
            await update.message.reply_text(result_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error testing AI: {str(e)}")
        
    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        application.add_handler(CommandHandler("risk", self.risk_command))
        application.add_handler(CommandHandler("correlation", self.correlation_command))
        application.add_handler(CommandHandler("efficient_frontier", self.efficient_frontier_command))
        application.add_handler(CommandHandler("compare", self.compare_command))
        application.add_handler(CommandHandler("chat", self.chat_command))
        application.add_handler(CommandHandler("pension", self.pension_command))
        application.add_handler(CommandHandler("monte_carlo", self.monte_carlo_command))
        application.add_handler(CommandHandler("allocation", self.allocation_command))
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
        print(f"Starting Okama Finance Bot with Python {sys.version}")
        print(f"Python version info: {sys.version_info}")
        
        if sys.version_info >= (3, 13):
            print("✅ Running on Python 3.13+ with latest python-telegram-bot")
        elif sys.version_info >= (3, 12):
            print("✅ Running on Python 3.12+ with latest python-telegram-bot")
        
        bot = OkamaFinanceBot()
        bot.run()
    except Exception as e:
        print(f"❌ Fatal error starting bot: {e}")
        print(f"Python version: {sys.version}")
        print(f"Python executable: {sys.executable}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        