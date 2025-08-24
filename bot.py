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
        
        welcome_message = f"""🤖 Welcome to Okama Finance Bot!

Hi {user_name}! I'm your YandexGPT-powered financial analysis assistant.

What I can do:
• 📊 Portfolio analysis and optimization
• 📈 Risk assessment and metrics
• 🔗 Asset correlation analysis
• 🎯 Efficient frontier generation
• 📋 Asset comparison and benchmarking
• 💬 Chat with YandexGPT about finance

Quick Start:
• Send me symbols like "RGBITR.INDX MCFTR.INDX GC.COMM"
• Ask "Analyze portfolio AGG.US SPY.US"
• Use commands like /portfolio, /risk, /correlation

Commands:
/help - Show all available commands
/portfolio - Portfolio analysis
/risk - Risk metrics
/correlation - Correlation matrix
/efficient_frontier - Efficient frontier
/compare - Asset comparison
/chat - Chat with YandexGPT

Ready to analyze your investments? 🚀"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Portfolio Analysis", callback_data="portfolio_help")],
            [InlineKeyboardButton("📈 Risk Metrics", callback_data="risk_help")],
            [InlineKeyboardButton("🔗 Correlation", callback_data="correlation_help")],
            [InlineKeyboardButton("💬 Chat with YandexGPT", callback_data="chat_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """📚 Available Commands & Features

Core Analysis Commands:
/portfolio [symbols] - Analyze portfolio performance
/risk [symbols] - Calculate risk metrics (VaR, CVaR, volatility)
/correlation [symbols] - Generate correlation matrix
/efficient_frontier [symbols] - Create efficient frontier plot
/compare [symbols] - Compare multiple assets
/test [symbols] - Test Okama integration
/testai - Test YandexGPT API connection

YandexGPT Chat:
/chat [question] - Get financial advice from YandexGPT

Examples:
• /portfolio RGBITR.INDX MCFTR.INDX
• /risk AGG.US SPY.US
• /correlation RGBITR.INDX MCFTR.INDX GC.COMM
• /compare AGG.US SPY.US GC.COMM

Natural Language:
You can also just type naturally:
• "Analyze my portfolio AGG.US SPY.US"
• "What's the risk of GC.COMM?"
• "Compare RGBITR.INDX vs MCFTR.INDX"
• "How to optimize my portfolio?"

Need Help?
Just type your question or use the commands above!"""
        
        await update.message.reply_text(help_text)
    
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        if not context.args:
            await update.message.reply_text(
                "📊 Portfolio Analysis\n\n"
                "Please provide symbols:\n"
                "/portfolio RGBITR.INDX MCFTR.INDX\n\n"
                "Or just send me the symbols directly!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_portfolio(update, symbols)
    
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command"""
        if not context.args:
            await update.message.reply_text(
                "📈 Risk Analysis\n\n"
                "Please provide symbols:\n"
                "/risk AGG.US SPY.US\n\n"
                "Or just send me the symbols directly!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_risk(update, symbols)
    
    async def correlation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /correlation command"""
        if not context.args:
            await update.message.reply_text(
                "🔗 Correlation Analysis\n\n"
                "Please provide symbols:\n"
                "/correlation RGBITR.INDX MCFTR.INDX GC.COMM\n\n"
                "Or just send me the symbols directly!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_correlation(update, symbols)
    
    async def efficient_frontier_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /efficient_frontier command"""
        if not context.args:
            await update.message.reply_text(
                "🎯 Efficient Frontier\n\n"
                "Please provide symbols:\n"
                "/efficient_frontier RGBITR.INDX MCFTR.INDX\n\n"
                "Or just send me the symbols directly!"
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._generate_efficient_frontier(update, symbols)
    
    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command"""
        if not context.args:
            await update.message.reply_text(
                "📋 Asset Comparison\n\n"
                "Please provide symbols:\n"
                "/compare AGG.US SPY.US GC.COMM\n\n"
                "Or just send me the symbols directly!"
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
                "📊 Portfolio Analysis\n\n"
                "Send me symbols to analyze:\n"
                "• RGBITR.INDX MCFTR.INDX\n"
                "• /portfolio AGG.US SPY.US\n\n"
                "I'll show you:\n"
                "• Performance metrics\n"
                "• Risk analysis\n"
                "• Charts and insights"
            )
        elif query.data == "risk_help":
            await query.edit_message_text(
                "📈 Risk Analysis\n\n"
                "Send me symbols to analyze risk:\n"
                "• AGG.US SPY.US\n"
                "• /risk GC.COMM\n\n"
                "I'll show you:\n"
                "• Volatility metrics\n"
                "• VaR and CVaR\n"
                "• Correlation matrix"
            )
        elif query.data == "correlation_help":
            await query.edit_message_text(
                "🔗 Correlation Analysis\n\n"
                "Send me symbols to see correlations:\n"
                "• RGBITR.INDX MCFTR.INDX GC.COMM\n"
                "• /correlation AGG.US SPY.US\n\n"
                "I'll show you:\n"
                "• Correlation heatmap\n"
                "• Relationship insights\n"
                "• Diversification analysis"
            )
        elif query.data == "chat_help":
            await query.edit_message_text(
                "💬 YandexGPT Chat\n\n"
                "Ask me anything about finance:\n"
                "• What is diversification?\n"
                "• How to calculate Sharpe ratio?\n"
                "• Best practices for portfolio rebalancing\n\n"
                "I'll provide expert financial advice powered by YandexGPT!"
            )
    
    async def _analyze_portfolio(self, update: Update, symbols: List[str]):
        """Analyze portfolio performance"""
        try:
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
            await update.message.reply_text(f"❌ Error analyzing portfolio: {str(e)}")
    
    async def _analyze_risk(self, update: Update, symbols: List[str]):
        """Analyze risk metrics"""
        try:
            await update.message.reply_text(f"📈 Analyzing risk for: {', '.join(symbols)}...")
            
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
                    "🧪 Test Command\n\n"
                    "Please provide symbols to test:\n"
                    "/test RGBITR.INDX MCFTR.INDX\n\n"
                    "This will test the Okama integration and show available attributes."
                )
                return
            
            symbols = [s.upper() for s in context.args]
            await update.message.reply_text(f"🧪 Testing Okama integration with symbols: {', '.join(symbols)}...")
            
            # Run the test
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
            await update.message.reply_text("🧪 Testing YandexGPT API connection...")
            
            # Test the API connection
            test_results = self.yandexgpt_service.test_api_connection()
            
            # Format results
            result_text = f"🧪 YandexGPT API Test Results\n\n"
            result_text += f"Status: {test_results.get('status', 'Unknown')}\n"
            result_text += f"Message: {test_results.get('message', 'No message')}\n\n"
            
            if 'config' in test_results:
                config = test_results['config']
                result_text += "Configuration:\n"
                result_text += f"• API Key: {'✓ Set' if config.get('api_key_set') else '✗ NOT SET'}\n"
                result_text += f"• Folder ID: {'✓ Set' if config.get('folder_id_set') else '✗ NOT SET'}\n"
                result_text += f"• Base URL: {config.get('base_url', 'Unknown')}\n\n"
            
            if 'response' in test_results:
                result_text += f"API Response: {test_results['response']}\n\n"
            
            if test_results.get('status') == 'error':
                result_text += "❌ API test failed. Check your configuration."
            elif test_results.get('status') == 'success':
                result_text += "✅ API test successful!"
            else:
                result_text += "⚠️ API test had issues."
            
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
        