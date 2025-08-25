# Render Deployment Guide for Okama Finance Bot

## 🚨 Current Issue: Port Scan Timeout

Your deployment is failing with:
```
Port scan timeout reached, no open ports detected. 
Bind your service to at least one port. 
If you don't need to receive traffic on any port, create a background worker instead.
```

## 🔧 Solution: Web Service + Bot Architecture

The bot now uses a **hybrid approach**:
1. **Web Service**: Binds to port 8000 to satisfy Render's port scanning requirements
2. **Bot Process**: Runs in the background while the web service remains active

## 📁 Updated Files

### 1. `scripts/web_service.py` (NEW)
- Flask-based web service that binds to port 8000
- Provides health check endpoints (`/health`, `/status`)
- Starts the bot in a background thread
- Satisfies Render's port scanning requirements

### 2. `requirements.txt` (UPDATED)
- Added `Flask>=2.3.0` for the web service

### 3. `render.yaml` (UPDATED)
- Configured to use `python scripts/web_service.py` as start command
- Added health check configuration
- Set proper port binding (8000)

## 🚀 Deployment Steps

### Step 1: Commit and Push Changes
```bash
git add .
git commit -m "Fix Render deployment: Add web service for port binding"
git push origin main
```

### Step 2: Verify Render Configuration
1. Go to your Render dashboard
2. Ensure the service is configured as a **Web Service** (not Background Worker)
3. Verify the start command is: `python scripts/web_service.py`
4. Check that environment variables are set correctly

### Step 3: Monitor Deployment
- Watch the build logs for any errors
- The web service should start and bind to port 8000
- The bot should start in the background
- Health checks should pass

## 🧪 Local Testing

Before deploying, test the web service locally:

```bash
# Install Flask
pip install Flask

# Test the web service
python scripts/test_web_service.py
```

This will:
- Start the web service on port 8001
- Test all endpoints
- Verify the service works correctly

## 🔍 Troubleshooting

### If Deployment Still Fails:

1. **Check Build Logs**: Look for Python import errors or missing dependencies
2. **Verify Python Version**: Ensure Python 3.13+ is available
3. **Check Environment Variables**: Ensure all required bot tokens are set
4. **Alternative Start Command**: If web service fails, try:
   ```yaml
   startCommand: python scripts/start_bot.py
   ```

### Common Issues:

- **Port Already in Use**: The web service checks port availability
- **Missing Dependencies**: Flask is now included in requirements.txt
- **Import Errors**: The bot imports are handled gracefully

## 📊 Health Check Endpoints

Once deployed, your service will provide:

- **`/`**: Home page showing bot status
- **`/health`**: Health check endpoint for Render
- **`/status`**: Detailed bot status information

## 🔄 Fallback Options

If the web service approach fails, you can:

1. **Use Background Worker**: Change service type in render.yaml
2. **Direct Bot Start**: Use `python scripts/start_bot.py`
3. **Custom Web Service**: Modify the Flask app as needed

## 📝 Environment Variables

Ensure these are set in Render:
- `TELEGRAM_BOT_TOKEN`
- `YANDEX_API_KEY`
- `YANDEX_FOLDER_ID`
- `OKAMA_API_KEY` (if required)
- `BOT_USERNAME`
- `ADMIN_USER_ID`

## 🎯 Expected Behavior

After successful deployment:
1. ✅ Web service starts and binds to port 8000
2. ✅ Bot starts in background thread
3. ✅ Health checks pass
4. ✅ Bot responds to Telegram messages
5. ✅ Web service remains active for Render monitoring

## 🆘 Need Help?

If deployment still fails:
1. Check the build logs for specific error messages
2. Verify all dependencies are installed
3. Test the web service locally first
4. Consider using the background worker approach

---

**Last Updated**: $(date)
**Status**: Ready for deployment
