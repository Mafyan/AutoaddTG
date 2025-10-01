#!/bin/bash

# Stop script for User Control Bot

echo "========================================"
echo "  User Control Bot - Stopping System"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check for screen sessions
if command -v screen &> /dev/null; then
    if screen -list | grep -q "usercontrol_bot"; then
        screen -S usercontrol_bot -X quit
        echo -e "${GREEN}✓ Stopped bot screen session${NC}"
    fi
    
    if screen -list | grep -q "usercontrol_admin"; then
        screen -S usercontrol_admin -X quit
        echo -e "${GREEN}✓ Stopped admin panel screen session${NC}"
    fi
fi

# Check for tmux session
if command -v tmux &> /dev/null; then
    if tmux has-session -t usercontrol 2>/dev/null; then
        tmux kill-session -t usercontrol
        echo -e "${GREEN}✓ Stopped tmux session${NC}"
    fi
fi

# Check for PIDs file
if [ -f "pids.txt" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo -e "${GREEN}✓ Stopped process (PID: $pid)${NC}"
        fi
    done < pids.txt
    rm pids.txt
fi

# Kill by process name as fallback
pkill -f "python run_bot.py" && echo -e "${GREEN}✓ Stopped bot process${NC}" || true
pkill -f "python run_admin.py" && echo -e "${GREEN}✓ Stopped admin panel process${NC}" || true

echo ""
echo -e "${GREEN}System stopped successfully!${NC}"
echo ""

