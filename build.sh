#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting build process..."

# Check Python version
echo "🐍 Python version:"
python --version
python3 --version

# Try to use python3.11 specifically if available
if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 found, using it for installation"
    PYTHON_CMD="python3.11"
    PIP_CMD="pip3.11"
elif command -v python3 &> /dev/null; then
    echo "✅ Python 3 found, using it for installation"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    echo "⚠️  Python 3 not found, using default python"
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

# Ensure pip is available and up to date
echo "📦 Setting up pip..."
$PYTHON_CMD -m ensurepip --upgrade
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📚 Installing dependencies..."
$PIP_CMD install -r requirements.txt

# Verify installation
echo "✅ Verifying installations..."
$PIP_CMD list | grep -E "(telegram|openai|okama)"

echo "✅ Build completed successfully!"
