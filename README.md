# 🤖 Okama Finance Bot

A powerful **Telegram bot** that combines **YandexGPT AI** with **Okama financial library** to provide comprehensive financial analysis, portfolio optimization, and AI-powered investment advice.

**Deploy as a Render background service for 24/7 availability!** 🚀

## ✨ Features

- 📊 **Portfolio Analysis** - Performance metrics, risk assessment, and optimization
- 📈 **Risk Metrics** - VaR, CVaR, volatility, and correlation analysis
- 🔗 **Correlation Matrix** - Visual asset relationship analysis
- 🎯 **Efficient Frontier** - Portfolio optimization and risk-return analysis
- 📋 **Asset Comparison** - Side-by-side performance comparison
- 💬 **AI Financial Advisor** - YandexGPT-powered financial advice and insights
- 🎯 **Smart Instrument Recognition** - Automatic conversion of common names to Okama format
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

You can also just type naturally - the AI will automatically convert instrument names to the proper Okama format:

- "Analyze my portfolio with Apple and Tesla" → Uses "AAPL.US" and "TSLA.US"
- "What's the risk of gold and oil?" → Uses "XAU.COMM" and "BRENT.COMM"
- "Compare S&P 500 vs Bitcoin" → Uses "SPX.INDX" vs "BTC.CC"
- "Show me Sberbank and Gazprom stocks" → Uses "SBER.MOEX" and "GAZP.MOEX"
- "EUR/USD correlation with GBP/USD" → Uses "EURUSD.FX" and "GBPUSD.FX"
- "How to optimize my portfolio with Google, Microsoft, and Amazon?" → Uses "GOOGL.US", "MSFT.US", "AMZN.US"

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

# YandexGPT chat
/chat What is diversification?

# Natural language (AI automatically formats)
"Покажи анализ портфеля с Apple и Tesla"
"Сравни S&P 500 и Bitcoin"
"Оцени риск по акциям Сбербанка"
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Okama Service  │    │ YandexGPT Service │
│                 │    │                  │    │                 │
│ • Command       │◄──►│ • Portfolio      │    │ • Query         │
│   handlers      │    │   Analysis       │    │   Analysis      │
│ • Message       │    │ • Risk Metrics   │    │ • Financial     │
│   processing    │    │ • Charts         │    │   Advice        │
│ • Image         │    │ • Correlation    │    │ • Insights      │
│   generation    │    │ • Optimization   │    │ • Auto-format   │
│                 │    │                  │    │   Instruments   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   Smart Instrument      │
                    │   Recognition Engine    │
                    │                         │
                    │ • Apple → AAPL.US      │
                    │ • Bitcoin → BTC.CC     │
                    │ • Gold → XAU.COMM      │
                    │ • S&P 500 → SPX.INDX   │
                    │ • Sberbank → SBER.MOEX │
                    └─────────────────────────┘
```

### 🔄 Data Flow

1. **User Input**: Natural language command (e.g., "Show me Apple and Tesla")
2. **AI Processing**: YandexGPT analyzes intent and converts instrument names
3. **Format Conversion**: Common names → Okama format (AAPL.US, TSLA.US)
4. **Analysis Execution**: Okama service performs financial analysis
5. **Result Enhancement**: AI provides insights and interpretation
6. **Response Delivery**: Formatted results with charts and explanations

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

The bot uses **YandexGPT** to:

- **Analyze user intent** from natural language
- **Provide financial insights** and interpretation
- **Answer financial questions** and provide advice
- **Enhance analysis results** with AI-powered insights
- **Suggest portfolio improvements** based on analysis
- **Automatically convert instrument names** to Okama format

### 🎯 Smart Instrument Recognition

The AI automatically converts common financial instrument names to the proper Okama namespace format:

- **Stocks**: "Apple" → "AAPL.US", "Сбербанк" → "SBER.MOEX"
- **Indices**: "S&P 500" → "SPX.INDX", "RTS" → "RTSI.INDX"
- **Commodities**: "Gold" → "XAU.COMM", "Oil" → "BRENT.COMM"
- **Forex**: "EUR/USD" → "EURUSD.FX"
- **Crypto**: "Bitcoin" → "BTC.CC"

### 🌍 Supported Namespaces

The bot supports all Okama platform namespaces:

| Namespace | Description | Examples |
|-----------|-------------|----------|
| `CBR` | Central Banks rates | USD.CBR, EUR.CBR |
| `CC` | Cryptocurrency pairs | BTC.CC, ETH.CC |
| `COMM` | Commodities prices | XAU.COMM, BRENT.COMM |
| `FX` | FOREX currency market | EURUSD.FX, GBPUSD.FX |
| `INDX` | Market indices | SPX.INDX, RTSI.INDX |
| `MOEX` | Moscow Exchange | SBER.MOEX, GAZP.MOEX |
| `US` | US Stock Exchanges | AAPL.US, TSLA.US |
| `PIF` | Russian mutual funds | SBRF.PIF |
| `LSE` | London Stock Exchange | BP.LSE |
| `XAMS` | Euronext Amsterdam | ASML.XAMS |
| `XETR` | XETRA Exchange | SAP.XETR |
| `XFRA` | Frankfurt Exchange | BMW.XFRA |
| `XSTU` | Stuttgart Exchange | DAI.XSTU |
| `XTAE` | Tel Aviv Exchange | TEVA.XTAE |

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

The bot supports various financial instruments through the Okama library and automatically converts common names to the proper format:

### 🏢 **Stocks**
- **US Stocks**: Apple (AAPL.US), Tesla (TSLA.US), Google (GOOGL.US)
- **Russian Stocks**: Sberbank (SBER.MOEX), Gazprom (GAZP.MOEX), Lukoil (LKOH.MOEX)
- **European Stocks**: BP (BP.LSE), SAP (SAP.XETR), BMW (BMW.XFRA)

### 📊 **Indices**
- **US Indices**: S&P 500 (SPX.INDX), NASDAQ (IXIC.INDX)
- **Russian Indices**: RTS (RTSI.INDX), MOEX (IMOEX.INDX)
- **European Indices**: DAX (DAX.INDX), CAC 40 (CAC.INDX)

### 🥇 **Commodities**
- **Precious Metals**: Gold (XAU.COMM), Silver (XAG.COMM)
- **Energy**: Oil (BRENT.COMM), Natural Gas (NG.COMM)
- **Agricultural**: Corn (ZC.COMM), Wheat (ZW.COMM)

### 💱 **Forex**
- **Major Pairs**: EUR/USD (EURUSD.FX), GBP/USD (GBPUSD.FX)
- **Cross Pairs**: EUR/GBP (EURGBP.FX), USD/JPY (USDJPY.FX)

### 🪙 **Cryptocurrency**
- **Major Crypto**: Bitcoin (BTC.CC), Ethereum (ETH.CC)
- **Altcoins**: Litecoin (LTC.CC), Ripple (XRP.CC)

### 🏦 **Bonds & Rates**
- **Government Bonds**: US Treasuries (US10Y.RATE)
- **Central Bank Rates**: USD (USD.CBR), EUR (EUR.CBR)

### 📈 **ETFs & Mutual Funds**
- **US ETFs**: SPY (SPY.US), AGG (AGG.US), QQQ (QQQ.US)
- **Russian Funds**: SBRF (SBRF.PIF), VTBX (VTBX.PIF)

### 🏠 **Real Estate**
- **REITs**: Real estate investment trusts (VNQ.US)
- **Property Indices**: Real estate market indices (RE.INDX)

**Note**: The AI automatically converts common names like "Apple", "Bitcoin", "Gold" to their proper Okama format (AAPL.US, BTC.CC, XAU.COMM).

## 🛠️ Development

### Python Version
This bot is designed to work with Python 3.13+ and uses the latest `python-telegram-bot` library for optimal compatibility.

### Project Structure

```
okama-bot/
├── bot.py                  # Main Telegram bot
├── config.py               # Configuration management
├── okama_service.py        # Okama library integration
├── yandexgpt_service.py    # YandexGPT API integration
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment config
├── build.sh                # Build script for Render
├── config.env.example      # Environment variables template
└── README.md               # This file
```

### Adding New Features

1. **New Analysis Type**: Add method to `OkamaService`
2. **New Command**: Add handler to `bot.py`
3. **New AI Feature**: Extend `YandexGPTService`
4. **New Visualization**: Create chart generation method

### Testing

Run the test suite to verify Okama formatting functionality:

```bash
# Test the new instrument formatting features
python test_okama_formatting.py

# This will test:
# - System prompt content
# - analyze_query method
# - process_freeform_command method
# - fallback analysis with common names
```

The test suite verifies that:
- All Okama namespaces are properly included in prompts
- Common instrument names are correctly converted
- AI responses maintain proper formatting
- Fallback analysis works with pattern matching

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

5. **Instrument name formatting issues**
   - Check YandexGPT API configuration
   - Verify namespace mapping is correct
   - Test with simple instrument names first
   - Check fallback pattern matching

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
- [Yandex Cloud](https://cloud.yandex.com/) - YandexGPT API for AI-powered insights and smart instrument recognition
- [Matplotlib](https://matplotlib.org/) - Chart generation and visualization
- [Render](https://render.com/) - Hosting platform

### 🆕 New Features

**Smart Instrument Recognition**: The bot now automatically converts common financial instrument names to the proper Okama format using AI-powered analysis. This makes it much easier for users to interact with the bot using natural language while ensuring all commands are properly formatted for the Okama platform.

---

**Ready to deploy?** 

1. **Get your Telegram bot token** from [@BotFather](https://t.me/botfather)
2. **Get your OpenAI API key** from [OpenAI Platform](https://platform.openai.com/)
3. **Fork this repository** and connect to Render
4. **Deploy as a background service** for 24/7 availability

**Disclaimer**: This bot provides financial analysis for educational purposes only. It is not financial advice. Always consult with qualified financial professionals before making investment decisions.
