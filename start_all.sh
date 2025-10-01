#!/bin/bash

# Startup script for User Control Bot
set -e

echo "========================================"
echo "  User Control Bot - Starting System"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
    echo "Please run installation first:"
    echo "  bash install.sh"
    exit 1
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}[WARNING] .env file not found!${NC}"
    echo "Create .env based on env.example"
    exit 1
fi

# Check database
if [ ! -f "usercontrol.db" ]; then
    echo -e "${YELLOW}[WARNING] Database not found!${NC}"
    echo "Initializing database..."
    source venv/bin/activate
    python -m database.init_db
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Check if running in screen/tmux or directly
if [ -n "$STY" ] || [ -n "$TMUX" ]; then
    # Running in screen or tmux
    echo "Starting in current session..."
    
    # Start bot in background
    python run_bot.py > logs/bot.log 2>&1 &
    BOT_PID=$!
    echo -e "${GREEN}✓ Bot started (PID: $BOT_PID)${NC}"
    
    # Start admin panel in background
    python run_admin.py > logs/admin.log 2>&1 &
    ADMIN_PID=$!
    echo -e "${GREEN}✓ Admin panel started (PID: $ADMIN_PID)${NC}"
    
    echo ""
    echo "PIDs saved to pids.txt"
    echo "$BOT_PID" > pids.txt
    echo "$ADMIN_PID" >> pids.txt
    
else
    # Not in screen/tmux, suggest using them
    if command -v screen &> /dev/null; then
        echo "Starting with screen..."
        mkdir -p logs
        
        # Start bot in screen
        screen -dmS usercontrol_bot bash -c "source venv/bin/activate && python run_bot.py"
        echo -e "${GREEN}✓ Bot started in screen session 'usercontrol_bot'${NC}"
        
        # Start admin in screen
        screen -dmS usercontrol_admin bash -c "source venv/bin/activate && python run_admin.py"
        echo -e "${GREEN}✓ Admin panel started in screen session 'usercontrol_admin'${NC}"
        
        echo ""
        echo "To view logs:"
        echo "  screen -r usercontrol_bot    - view bot"
        echo "  screen -r usercontrol_admin  - view admin panel"
        echo ""
        echo "To detach from screen: Press Ctrl+A, then D"
        echo "To stop:"
        echo "  screen -S usercontrol_bot -X quit"
        echo "  screen -S usercontrol_admin -X quit"
        
    elif command -v tmux &> /dev/null; then
        echo "Starting with tmux..."
        mkdir -p logs
        
        # Create new tmux session
        tmux new-session -d -s usercontrol
        
        # Split window
        tmux split-window -h -t usercontrol
        
        # Start bot in first pane
        tmux send-keys -t usercontrol:0.0 "source venv/bin/activate && python run_bot.py" C-m
        
        # Start admin in second pane
        tmux send-keys -t usercontrol:0.1 "source venv/bin/activate && python run_admin.py" C-m
        
        echo -e "${GREEN}✓ System started in tmux session 'usercontrol'${NC}"
        echo ""
        echo "To view:"
        echo "  tmux attach -t usercontrol"
        echo ""
        echo "To detach from tmux: Press Ctrl+B, then D"
        echo "To stop:"
        echo "  tmux kill-session -t usercontrol"
        
    else
        echo -e "${YELLOW}Warning: screen/tmux not found${NC}"
        echo "Installing screen is recommended for background execution"
        echo ""
        echo "Starting in foreground mode..."
        echo "Press Ctrl+C to stop"
        echo ""
        
        # Create logs directory
        mkdir -p logs
        
        # Start both in background
        python run_bot.py > logs/bot.log 2>&1 &
        BOT_PID=$!
        
        python run_admin.py > logs/admin.log 2>&1 &
        ADMIN_PID=$!
        
        echo "$BOT_PID" > pids.txt
        echo "$ADMIN_PID" >> pids.txt
        
        echo -e "${GREEN}✓ Bot started (PID: $BOT_PID)${NC}"
        echo -e "${GREEN}✓ Admin panel started (PID: $ADMIN_PID)${NC}"
        
        echo ""
        echo "To stop, run: ./stop_all.sh"
    fi
fi

sleep 2

echo ""
echo "========================================"
echo "  System started!"
echo "========================================"
echo ""
echo "Telegram Bot: Running"
echo "Admin Panel: http://localhost:8000"
echo ""
echo "Login: admin"
echo "Password: admin123"
echo ""
echo "Logs:"
echo "  Bot: logs/bot.log"
echo "  Admin: logs/admin.log"
echo ""

