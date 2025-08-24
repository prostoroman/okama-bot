#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting build process..."

# Ensure pip is available and up to date
echo "📦 Setting up pip..."
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully!"
