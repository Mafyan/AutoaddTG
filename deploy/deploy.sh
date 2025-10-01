#!/bin/bash

# Deployment script for User Control Bot on Ubuntu 20.04
# Run as: sudo bash deploy.sh

set -e

echo "======================================"
echo "User Control Bot Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Configuration
PROJECT_DIR="/opt/usercontrol"
REPO_URL=""  # Add your repo URL here
DOMAIN=""    # Add your domain here

# Get user input if not set
if [ -z "$REPO_URL" ]; then
    read -p "Enter your Git repository URL: " REPO_URL
fi

if [ -z "$DOMAIN" ]; then
    read -p "Enter your domain (or press Enter for localhost): " DOMAIN
fi

echo ""
echo "==> Step 1: Update system packages"
apt update && apt upgrade -y

echo ""
echo "==> Step 2: Install required packages"
apt install -y python3.10 python3.10-venv python3-pip nginx supervisor git

echo ""
echo "==> Step 3: Create project directory"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/backups

echo ""
echo "==> Step 4: Clone or update project"
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Project already exists, pulling latest changes..."
    cd $PROJECT_DIR
    git pull
else
    echo "Cloning project..."
    if [ -n "$REPO_URL" ]; then
        git clone $REPO_URL $PROJECT_DIR
    else
        echo -e "${YELLOW}No repository URL provided, skipping clone.${NC}"
        echo -e "${YELLOW}Please manually copy your project files to $PROJECT_DIR${NC}"
    fi
fi

cd $PROJECT_DIR

echo ""
echo "==> Step 5: Create virtual environment"
python3 -m venv venv

echo ""
echo "==> Step 6: Install Python dependencies"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "==> Step 7: Setup environment variables"
if [ ! -f .env ]; then
    cp env.example .env
    echo -e "${YELLOW}Please edit .env file and add your tokens:${NC}"
    echo "  BOT_TOKEN - from @BotFather"
    echo "  ADMIN_SECRET_KEY - any long random string"
    read -p "Press Enter to edit .env file..." 
    nano .env
else
    echo ".env file already exists"
fi

echo ""
echo "==> Step 8: Initialize database"
python -m database.init_db

echo ""
echo "==> Step 9: Setup Supervisor"
cp deploy/supervisor.conf /etc/supervisor/conf.d/usercontrol.conf

# Update user in supervisor config
CURRENT_USER=${SUDO_USER:-ubuntu}
sed -i "s/user=ubuntu/user=$CURRENT_USER/g" /etc/supervisor/conf.d/usercontrol.conf

supervisorctl reread
supervisorctl update

echo ""
echo "==> Step 10: Setup Nginx"
if [ -n "$DOMAIN" ]; then
    sed -i "s/your-domain.com/$DOMAIN/g" deploy/nginx.conf
fi

cp deploy/nginx.conf /etc/nginx/sites-available/usercontrol
ln -sf /etc/nginx/sites-available/usercontrol /etc/nginx/sites-enabled/

# Remove default nginx site
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx

echo ""
echo "==> Step 11: Setup firewall (if ufw is available)"
if command -v ufw &> /dev/null; then
    ufw allow 22
    ufw allow 80
    ufw allow 443
    echo "Firewall rules added (22, 80, 443)"
fi

echo ""
echo "==> Step 12: Setup SSL (optional)"
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
    read -p "Do you want to setup SSL with Let's Encrypt? (y/n): " setup_ssl
    if [ "$setup_ssl" = "y" ]; then
        apt install -y certbot python3-certbot-nginx
        certbot --nginx -d $DOMAIN
    fi
fi

echo ""
echo "==> Step 13: Setup automatic backups"
BACKUP_SCRIPT="#!/bin/bash
cp $PROJECT_DIR/usercontrol.db $PROJECT_DIR/backups/usercontrol_\$(date +%Y%m%d_%H%M%S).db
find $PROJECT_DIR/backups/ -name '*.db' -mtime +7 -delete
"
echo "$BACKUP_SCRIPT" > /opt/usercontrol/backup.sh
chmod +x /opt/usercontrol/backup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/usercontrol/backup.sh") | crontab -

echo ""
echo "==> Step 14: Set permissions"
chown -R $CURRENT_USER:$CURRENT_USER $PROJECT_DIR

echo ""
echo "==> Step 15: Start services"
supervisorctl start all
systemctl enable supervisor
systemctl enable nginx

echo ""
echo -e "${GREEN}======================================"
echo "Deployment completed successfully!"
echo "======================================${NC}"
echo ""
echo "Service Status:"
supervisorctl status

echo ""
echo "Next Steps:"
echo "1. Check logs:"
echo "   sudo tail -f /var/log/usercontrol_bot.out.log"
echo "   sudo tail -f /var/log/usercontrol_admin.out.log"
echo ""
echo "2. Access admin panel:"
if [ -n "$DOMAIN" ]; then
    echo "   http://$DOMAIN"
else
    echo "   http://$(hostname -I | awk '{print $1}')"
fi
echo ""
echo "3. Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE PASSWORD IMMEDIATELY!"
echo ""
echo "4. Useful commands:"
echo "   sudo supervisorctl status          - Check service status"
echo "   sudo supervisorctl restart all     - Restart all services"
echo "   sudo supervisorctl stop all        - Stop all services"
echo "   sudo tail -f /var/log/usercontrol_bot.err.log  - View bot errors"
echo ""
echo -e "${GREEN}Deployment complete!${NC}"

