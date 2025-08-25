# Okama Finance Bot - Deployment Guide

## Overview
This guide provides instructions for deploying the Okama Finance Bot on various hosting platforms.

## Prerequisites
- Python 3.7+ environment
- Telegram Bot Token
- YandexGPT API credentials
- Hosting platform account

## Environment Variables
Create a `.env` file with the following variables:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=your_yandex_folder_id_here

# Optional
BOT_USERNAME=your_bot_username
ADMIN_USER_ID=your_telegram_user_id
PRODUCTION=true  # Set to true for production deployment
```

## Deployment Options

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

### 2. VPS/Cloud Server
```bash
# Clone repository
git clone <your-repo-url>
cd okama-bot

# Install Python and dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp config_files/config.env.example .env
# Edit .env with your credentials

# Run as background service
nohup python3 bot.py > bot.log 2>&1 &
```

### 3. Docker Deployment
Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t okama-bot .
docker run -d --env-file .env okama-bot
```

### 4. Heroku
Create `Procfile`:
```
worker: python bot.py
```

Deploy:
```bash
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set YANDEX_API_KEY=your_key
heroku config:set YANDEX_FOLDER_ID=your_folder_id
git push heroku main
```

### 5. Railway
Deploy directly from GitHub:
1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically

## Health Monitoring

### Built-in Health Check
The bot includes a health check system:
```python
# Check bot status
python -c "from bot import health_check; health_check()"
```

### Logging
- All operations are logged with proper levels
- Check logs for errors and performance metrics
- Use structured logging for production monitoring

## Performance Optimization

### Memory Usage
- The bot is optimized for minimal memory usage
- Automatic cleanup of matplotlib figures
- Efficient data processing

### Response Time
- Optimized for fast response times
- Reduced I/O operations
- Streamlined error handling

## Troubleshooting

### Common Issues
1. **Missing API keys**: Ensure all environment variables are set
2. **Dependencies**: Use the optimized requirements.txt
3. **Memory issues**: Check for matplotlib memory leaks
4. **Network issues**: Verify internet connectivity

### Debug Mode
For debugging, set logging level to DEBUG:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use secure environment variable management
3. **Access Control**: Implement admin user restrictions if needed
4. **Rate Limiting**: Consider implementing rate limiting for production

## Scaling Considerations

1. **Multiple Instances**: Run multiple bot instances behind a load balancer
2. **Database**: Consider adding database for user sessions
3. **Caching**: Implement caching for frequently accessed data
4. **Monitoring**: Add comprehensive monitoring and alerting

## Support

For deployment issues:
1. Check the logs for detailed error information
2. Verify environment configuration
3. Ensure all dependencies are properly installed
4. Test locally before deploying

---

**Note**: This deployment guide covers general hosting platforms. The bot is optimized for production use and includes comprehensive error handling and logging.
