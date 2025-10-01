#!/bin/bash

# Installation script for User Control Bot
set -e

echo "========================================"
echo "  User Control Bot - Installation"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed!${NC}"
    echo "Please install Python 3.10+ first"
    exit 1
fi

python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Setup environment variables
echo "[4/5] Setting up environment variables..."
if [ -f ".env" ]; then
    echo ".env file already exists"
else
    cp env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}[IMPORTANT] Edit .env file and set:${NC}"
    echo "  - BOT_TOKEN (get from @BotFather in Telegram)"
    echo "  - ADMIN_SECRET_KEY (any long random string)"
    echo ""
    read -p "Open .env for editing? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi
echo ""

# Initialize database
echo "[5/5] Initializing database..."
if [ -f "usercontrol.db" ]; then
    echo "Database already exists"
else
    python -m database.init_db
    echo -e "${GREEN}✓ Database initialized${NC}"
fi
echo ""

echo "========================================"
echo "  Installation completed!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure BOT_TOKEN is set in .env"
echo "2. Start the system: ./start_all.sh"
echo "3. Open http://localhost:8000"
echo "4. Login (admin / admin123)"
echo ""
echo "Full guide: QUICKSTART.md"
echo ""

