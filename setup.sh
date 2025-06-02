#!/bin/bash

# Agricultural Advisor Bot Setup Script
# This script helps set up the bot environment

echo "🌾 Agricultural Advisor Bot - Setup Script 🌾"
echo "============================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
echo "🔍 Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python $PYTHON_VERSION found"
    
    # Check if version is 3.9 or higher
    REQUIRED_VERSION="3.9"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        echo "✅ Python version is compatible"
    else
        echo "❌ Python 3.9 or higher is required"
        exit 1
    fi
else
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.9 or higher from https://www.python.org"
    exit 1
fi

# Check PostgreSQL installation
echo ""
echo "🔍 Checking PostgreSQL installation..."
if command_exists psql; then
    echo "✅ PostgreSQL found"
else
    echo "⚠️ PostgreSQL not found in PATH"
    echo "Make sure PostgreSQL is installed and added to your PATH"
    echo "Download from: https://www.postgresql.org/download/"
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️ Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo "⚠️ .env file already exists"
else
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️ IMPORTANT: Edit .env file and add your API keys:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - OPENAI_API_KEY"
    echo "   - GOOGLE_API_KEY"
    echo "   - GOOGLE_CSE_ID"
    echo "   - DATABASE_URL"
fi

# Create local database
echo ""
echo "🗄️ Setting up local database..."
read -p "Do you want to create a local PostgreSQL database? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter PostgreSQL username (default: postgres): " PG_USER
    PG_USER=${PG_USER:-postgres}
    
    echo "Creating database 'agri_bot'..."
    createdb -U $PG_USER agri_bot
    
    if [ $? -eq 0 ]; then
        echo "✅ Database created successfully"
        echo ""
        echo "📝 Update your .env file with:"
        echo "DATABASE_URL=postgresql://$PG_USER:your_password@localhost:5432/agri_bot"
    else
        echo "⚠️ Failed to create database. You may need to create it manually."
    fi
fi

# Run tests
echo ""
echo "🧪 Running system tests..."
python test_bot.py

# Final instructions
echo ""
echo "============================================"
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and tokens"
echo "2. Run 'python test_bot.py' to verify everything is working"
echo "3. Run 'python main.py' to start the bot"
echo ""
echo "For detailed instructions, see README.md"
echo "============================================" 