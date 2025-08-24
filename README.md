# 🤖 Okama Finance Bot

A powerful **Telegram bot** that combines **ChatGPT AI** with **Okama financial library** to provide comprehensive financial analysis, portfolio optimization, and AI-powered investment advice.

**Deploy as a Render background service for 24/7 availability!** 🚀

## ✨ Features

- 📊 **Portfolio Analysis** - Performance metrics, risk assessment, and optimization
- 📈 **Risk Metrics** - VaR, CVaR, volatility, and correlation analysis
- 🔗 **Correlation Matrix** - Visual asset relationship analysis
- 🎯 **Efficient Frontier** - Portfolio optimization and risk-return analysis
- 📋 **Asset Comparison** - Side-by-side performance comparison
- 💬 **AI Financial Advisor** - ChatGPT-powered financial advice and insights
- 🖼️ **Rich Visualizations** - Charts, graphs, and heatmaps for all analyses
- 📱 **Telegram Bot** - Chat-based financial analysis
- 🌐 **Render Service** - 24/7 availability as background service

## 🚀 Quick Start

### 🌐 Deploy to Render (Recommended)

1. **Fork this repository** to your GitHub account
2. **Connect to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Background Service"
   - Connect your GitHub repository
3. **Configure the service:**
   - **Name:** `okama-finance-bot`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Starter (free tier available)
4. **Set Environment Variables:**
   - `TELEGRAM_BOT_TOKEN` (required)
   - `OPENAI_API_KEY` (required)
5. **Deploy!** 🎉

**Your bot will run continuously as a background service!**

### 🐍 Local Development

```bash
# Clone and setup
git clone <your-repo-url>
cd okama-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.env.example .env
# Edit .env with your API keys

# Run the bot
python bot.py
```

## 📱 Usage

### 📱 Telegram Bot Commands

- `/start` - Welcome message and main menu
- `/help` - Show all available commands
- `/portfolio [symbols]` - Analyze portfolio performance
- `/risk [symbols]` - Calculate risk metrics
- `/correlation [symbols]` - Generate correlation matrix
- `/efficient_frontier [symbols]` - Create efficient frontier plot
- `/compare [symbols]` - Compare multiple assets
- `/chat [question]` - Get financial advice from AI

### 💬 Natural Language

You can also just type naturally:

- "Analyze my portfolio AGG.US SPY.US"
- "What's the risk of GC.COMM?"
- "Compare RGBITR.INDX vs MCFTR.INDX"
- "How to optimize my portfolio?"

### 📊 Examples

```
# Portfolio analysis
/portfolio RGBITR.INDX MCFTR.INDX

# Risk analysis
/risk AGG.US SPY.US

# Correlation analysis
/correlation RGBITR.INDX MCFTR.INDX GC.COMM

# Asset comparison
/compare AGG.US SPY.US GC.COMM

# AI chat
/chat What is diversification?
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Okama Service  │    │ ChatGPT Service │
│                 │    │                  │    │                 │
│ • Command       │◄──►│ • Portfolio      │    │ • Query         │
│   handlers      │    │   Analysis       │    │   Analysis      │
│ • Message       │    │ • Risk Metrics   │    │ • Financial     │
│   processing    │    │ • Charts         │    │   Advice        │
│ • Image         │    │ • Correlation    │    │ • Insights      │
│   generation    │    │ • Optimization   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Analysis Features

### Portfolio Analysis
- Total and annual returns
- Volatility and Sharpe ratio
- Maximum drawdown
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- Performance charts

### Risk Metrics
- Individual asset risk profiles
- Portfolio-level risk assessment
- Correlation analysis
- Risk visualization

### Efficient Frontier
- Optimal portfolio combinations
- Risk-return trade-offs
- Asset allocation optimization
- Visual frontier plots

### Asset Comparison
- Performance benchmarking
- Risk-adjusted returns
- Visual comparison charts
- Statistical analysis

## 🤖 AI Integration

The bot uses **ChatGPT** to:

- **Analyze user intent** from natural language
- **Provide financial insights** and interpretation
- **Answer financial questions** and provide advice
- **Enhance analysis results** with AI-powered insights
- **Suggest portfolio improvements** based on analysis

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | ✅ | - |
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ | - |
| `BOT_USERNAME` | Bot username for display | ❌ | okama_finance_bot |
| `ADMIN_USER_ID` | Admin user ID for special features | ❌ | - |

### Bot Settings

- Maximum message length: 4096 characters
- Maximum caption length: 1024 characters
- Chart DPI: 300
- Chart format: PNG

## 📈 Supported Assets

The bot supports various financial instruments through the Okama library:

- **Indices** (e.g., RGBITR.INDX, MCFTR.INDX)
- **ETFs** (e.g., AGG.US, SPY.US)
- **Commodities** (e.g., GC.COMM)
- **Stocks** (if supported by data source)
- **Crypto** (if available)

## 🛠️ Development

### Python Version
This bot is designed to work with Python 3.13+ and uses the latest `python-telegram-bot` library for optimal compatibility.

### Project Structure

```
okama-bot/
├── bot.py                  # Main Telegram bot
├── config.py               # Configuration management
├── okama_service.py        # Okama library integration
├── chatgpt_service.py      # ChatGPT API integration
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment config
├── build.sh                # Build script for Render
├── config.env.example      # Environment variables template
└── README.md               # This file
```

### Adding New Features

1. **New Analysis Type**: Add method to `OkamaService`
2. **New Command**: Add handler to `bot.py`
3. **New AI Feature**: Extend `ChatGPTService`
4. **New Visualization**: Create chart generation method

## 🚀 Deployment Options

### 🌐 Render (Recommended)
The bot is configured to run as a Render background service using Python 3.13.
- **Free tier available**
- **24/7 background service**
- **Automatic deployments**
- **Easy scaling**

### 🐍 Local Development
- **Full development environment**
- **Easy debugging**
- **Fast iteration**

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check Telegram bot token
   - Verify bot is not blocked
   - Check internet connection

2. **Analysis errors**
   - Verify stock symbols are valid
   - Check Okama library installation
   - Ensure sufficient data availability

3. **AI responses failing**
   - Verify OpenAI API key
   - Check API quota and billing
   - Test API connectivity

4. **Chart generation issues**
   - Install matplotlib dependencies
   - Check available memory
   - Verify image format support

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- **Issues**: Create a GitHub issue
- **Questions**: Open a discussion
- **Feature Requests**: Submit via issues

## 🙏 Acknowledgments

- [Okama Library](https://github.com/mbk-dev/okama) - Financial analysis and portfolio optimization
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot API wrapper
- [OpenAI](https://openai.com/) - ChatGPT API for AI-powered insights
- [Matplotlib](https://matplotlib.org/) - Chart generation and visualization
- [Render](https://render.com/) - Hosting platform

---

**Ready to deploy?** 

1. **Get your Telegram bot token** from [@BotFather](https://t.me/botfather)
2. **Get your OpenAI API key** from [OpenAI Platform](https://platform.openai.com/)
3. **Fork this repository** and connect to Render
4. **Deploy as a background service** for 24/7 availability

**Disclaimer**: This bot provides financial analysis for educational purposes only. It is not financial advice. Always consult with qualified financial professionals before making investment decisions.
