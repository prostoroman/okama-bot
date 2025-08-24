#!/bin/bash

# Okama Finance Bot Startup Script

echo "🚀 Starting Okama Finance Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one from config.env.example"
    echo "   cp config.env.example .env"
    echo "   Then edit .env with your API keys"
    exit 1
fi

# Check if requirements are installed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Run the bot
echo "🤖 Starting bot..."
python3 bot.py
