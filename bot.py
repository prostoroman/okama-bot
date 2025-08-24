import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import io
from typing import Dict, List, Optional

from config import Config
from okama_service import OkamaService
from chatgpt_service import ChatGPTService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OkamaFinanceBot:
    """Main Telegram bot class for financial analysis with Okama and ChatGPT"""
    
    def __init__(self):
        """Initialize the bot with required services"""
        Config.validate()
        
        self.okama_service = OkamaService()
        self.chatgpt_service = ChatGPTService()
        
        # User session storage
        self.user_sessions = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🤖 *Welcome to Okama Finance Bot!* 

Hi {user.first_name}! I'm your AI-powered financial analysis assistant.

*What I can do:*
• 📊 Portfolio analysis and optimization
• 📈 Risk assessment and metrics
• 🔗 Asset correlation analysis
• 🎯 Efficient frontier generation
• 📋 Asset comparison and benchmarking
• 💬 Chat with AI about finance

*Quick Start:*
• Send me stock symbols like "AAPL MSFT GOOGL"
• Ask "Analyze portfolio AAPL MSFT"
• Use commands like /portfolio, /risk, /correlation

*Commands:*
/help - Show all available commands
/portfolio - Portfolio analysis
/risk - Risk metrics
/correlation - Correlation matrix
/efficient_frontier - Efficient frontier
/compare - Asset comparison
/chat - Chat with AI

Ready to analyze your investments? 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Portfolio Analysis", callback_data="portfolio_help")],
            [InlineKeyboardButton("📈 Risk Metrics", callback_data="risk_help")],
            [InlineKeyboardButton("🔗 Correlation", callback_data="correlation_help")],
            [InlineKeyboardButton("💬 Chat with AI", callback_data="chat_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 *Available Commands & Features*

*Core Analysis Commands:*
/portfolio [symbols] - Analyze portfolio performance
/risk [symbols] - Calculate risk metrics (VaR, CVaR, volatility)
/correlation [symbols] - Generate correlation matrix
/efficient_frontier [symbols] - Create efficient frontier plot
/compare [symbols] - Compare multiple assets

*AI Chat:*
/chat [question] - Get financial advice from AI

*Examples:*
• `/portfolio AAPL MSFT GOOGL`
• `/risk SPY QQQ`
• `/correlation AAPL MSFT GOOGL`
• `/compare AAPL MSFT GOOGL TSLA`

*Natural Language:*
You can also just type naturally:
• "Analyze my portfolio AAPL MSFT"
• "What's the risk of SPY?"
• "Compare AAPL vs MSFT"
• "How to optimize my portfolio?"

*Need Help?*
Just type your question or use the commands above!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        if not context.args:
            await update.message.reply_text(
                "📊 *Portfolio Analysis*\n\n"
                "Please provide stock symbols:\n"
                "`/portfolio AAPL MSFT GOOGL`\n\n"
                "Or just send me the symbols directly!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_portfolio(update, symbols)
    
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command"""
        if not context.args:
            await update.message.reply_text(
                "📈 *Risk Analysis*\n\n"
                "Please provide stock symbols:\n"
                "`/risk SPY QQQ`\n\n"
                "Or just send me the symbols directly!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_risk(update, symbols)
    
    async def correlation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /correlation command"""
        if not context.args:
            await update.message.reply_text(
                "🔗 *Correlation Analysis*\n\n"
                "Please provide stock symbols:\n"
                "`/correlation AAPL MSFT GOOGL`\n\n"
                "Or just send me the symbols directly!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._analyze_correlation(update, symbols)
    
    async def efficient_frontier_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /efficient_frontier command"""
        if not context.args:
            await update.message.reply_text(
                "🎯 *Efficient Frontier*\n\n"
                "Please provide stock symbols:\n"
                "`/efficient_frontier AAPL MSFT GOOGL`\n\n"
                "Or just send me the symbols directly!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._generate_efficient_frontier(update, symbols)
    
    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command"""
        if not context.args:
            await update.message.reply_text(
                "📋 *Asset Comparison*\n\n"
                "Please provide stock symbols:\n"
                "`/compare AAPL MSFT GOOGL`\n\n"
                "Or just send me the symbols directly!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        symbols = [s.upper() for s in context.args]
        await self._compare_assets(update, symbols)
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chat command"""
        if not context.args:
            await update.message.reply_text(
                "💬 *AI Chat*\n\n"
                "Ask me anything about finance:\n"
                "`/chat What is diversification?`\n"
                "`/chat How to calculate Sharpe ratio?`\n\n"
                "Or just type your question directly!",
                parse_mode=ParseMode.MARKDOWN
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
            # Analyze user intent using ChatGPT
            analysis = self.chatgpt_service.analyze_query(user_message)
            
            if analysis['is_chat']:
                await self._handle_chat(update, user_message)
            else:
                # Handle analysis requests
                symbols = analysis['symbols']
                intent = analysis['intent']
                
                if not symbols:
                    await update.message.reply_text(
                        "I couldn't identify any stock symbols in your message. "
                        "Please provide stock tickers like AAPL, MSFT, GOOGL, etc."
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
                "📊 *Portfolio Analysis*\n\n"
                "Send me stock symbols to analyze:\n"
                "• `AAPL MSFT GOOGL`\n"
                "• `/portfolio SPY QQQ`\n\n"
                "I'll show you:\n"
                "• Performance metrics\n"
                "• Risk analysis\n"
                "• Charts and insights",
                parse_mode=ParseMode.MARKDOWN
            )
        elif query.data == "risk_help":
            await query.edit_message_text(
                "📈 *Risk Analysis*\n\n"
                "Send me stock symbols to analyze risk:\n"
                "• `SPY QQQ`\n"
                "• `/risk AAPL MSFT`\n\n"
                "I'll show you:\n"
                "• Volatility metrics\n"
                "• VaR and CVaR\n"
                "• Correlation matrix",
                parse_mode=ParseMode.MARKDOWN
            )
        elif query.data == "correlation_help":
            await query.edit_message_text(
                "🔗 *Correlation Analysis*\n\n"
                "Send me stock symbols to see correlations:\n"
                "• `AAPL MSFT GOOGL`\n"
                "• `/correlation SPY QQQ`\n\n"
                "I'll show you:\n"
                "• Correlation heatmap\n"
                "• Relationship insights\n"
                "• Diversification analysis",
                parse_mode=ParseMode.MARKDOWN
            )
        elif query.data == "chat_help":
            await query.edit_message_text(
                "💬 *AI Chat*\n\n"
                "Ask me anything about finance:\n"
                "• `What is diversification?`\n"
                "• `How to calculate Sharpe ratio?`\n"
                "• `Best practices for portfolio rebalancing`\n\n"
                "I'll provide expert financial advice!",
                parse_mode=ParseMode.MARKDOWN
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
            insights = self.chatgpt_service.enhance_analysis_results(
                "portfolio", metrics, f"portfolio analysis for {', '.join(symbols)}"
            )
            
            # Format metrics message
            metrics_text = f"""
📊 *Portfolio Analysis: {', '.join(symbols)}*

*Performance Metrics:*
• Total Return: {metrics.get('total_return', 'N/A')}
• Annual Return: {metrics.get('annual_return', 'N/A')}
• Volatility: {metrics.get('volatility', 'N/A')}
• Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}
• Max Drawdown: {metrics.get('max_drawdown', 'N/A')}
• VaR (95%): {metrics.get('var_95', 'N/A')}
• CVaR (95%): {metrics.get('cvar_95', 'N/A')}

*AI Insights:*
{insights}
            """
            
            # Send chart with caption
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(chart_image),
                caption=metrics_text,
                parse_mode=ParseMode.MARKDOWN
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
            risk_text = f"""
📈 *Risk Analysis: {', '.join(symbols)}*

*Individual Asset Risk:*
"""
            for symbol, data in risk_data.items():
                if 'error' not in data:
                    risk_text += f"""
• *{symbol}:*
  - Volatility: {data.get('volatility', 'N/A')}
  - VaR (95%): {data.get('var_95', 'N/A')}
  - CVaR (95%): {data.get('cvar_95', 'N/A')}
  - Max Drawdown: {data.get('max_drawdown', 'N/A')}
"""
                else:
                    risk_text += f"• *{symbol}:* Error - {data['error']}\n"
            
            risk_text += "\n*Correlation Matrix Below*"
            
            # Send correlation matrix
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(correlation_image),
                caption=risk_text,
                parse_mode=ParseMode.MARKDOWN
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
            insights = self.chatgpt_service.enhance_analysis_results(
                "correlation", {"symbols": symbols}, f"correlation analysis for {', '.join(symbols)}"
            )
            
            caption = f"""
🔗 *Correlation Matrix: {', '.join(symbols)}*

*AI Insights:*
{insights}

*Interpretation:*
• Values closer to 1 = Strong positive correlation
• Values closer to -1 = Strong negative correlation  
• Values closer to 0 = Low correlation
            """
            
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(correlation_image),
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error analyzing correlations: {str(e)}")
    
    async def _generate_efficient_frontier(self, update: Update, symbols: List[str]):
        """Generate efficient frontier plot"""
        try:
            await update.message.reply_text(f"🎯 Generating efficient frontier for: {', '.join(symbols)}...")
            
            # Generate efficient frontier
            frontier_image = self.okama_service.generate_efficient_frontier(symbols)
            
            caption = f"""
🎯 *Efficient Frontier: {', '.join(symbols)}*

*What This Shows:*
• The optimal risk-return combinations
• Each point represents a different portfolio allocation
• Lower left = Lower risk, lower return
• Upper right = Higher risk, higher return
• The curve shows the most efficient portfolios

*Use This To:*
• Find your optimal risk tolerance
• Compare portfolio efficiency
• Optimize asset allocation
            """
            
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(frontier_image),
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
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
            comparison_text = f"""
📋 *Asset Comparison: {', '.join(symbols)}*

*Performance Metrics:*
"""
            for symbol, metrics in comparison_metrics.items():
                if 'error' not in metrics:
                    comparison_text += f"""
• *{symbol}:*
  - Total Return: {metrics.get('total_return', 'N/A'):.2%}
  - Annual Return: {metrics.get('annual_return', 'N/A'):.2%}
  - Volatility: {metrics.get('volatility', 'N/A'):.2%}
  - Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.2f}
  - Max Drawdown: {metrics.get('max_drawdown', 'N/A'):.2%}
"""
                else:
                    comparison_text += f"• *{symbol}:* Error - {metrics['error']}\n"
            
            # Send comparison chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(comparison_image),
                caption=comparison_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error comparing assets: {str(e)}")
    
    async def _handle_chat(self, update: Update, question: str):
        """Handle AI chat requests"""
        try:
            await update.message.reply_text("🤔 Thinking...")
            
            # Get AI response
            response = self.chatgpt_service.get_financial_advice(question)
            
            # Send response
            await update.message.reply_text(
                f"💬 *AI Financial Advisor*\n\n{response}",
                parse_mode=ParseMode.MARKDOWN
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
        application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        application.add_handler(CommandHandler("risk", self.risk_command))
        application.add_handler(CommandHandler("correlation", self.correlation_command))
        application.add_handler(CommandHandler("efficient_frontier", self.efficient_frontier_command))
        application.add_handler(CommandHandler("compare", self.compare_command))
        application.add_handler(CommandHandler("chat", self.chat_command))
        
        # Add message and callback handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Start the bot
        logger.info("Starting Okama Finance Bot...")
        application.run_polling()

if __name__ == "__main__":
    bot = OkamaFinanceBot()
    bot.run()
        