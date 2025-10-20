# 📱 Настройка мобильного поддомена m.phgcontrol.ru (Исправленная инструкция)

## ✅ Шаг 1: Проверка DNS

Убедись, что DNS настроен правильно:
```bash
nslookup m.phgcontrol.ru
```

Должен вернуть IP сервера: `89.208.117.150`

## 🔧 Шаг 2: Создание временной конфигурации nginx (без SSL)

Сначала создадим конфигурацию **БЕЗ SSL** для получения сертификата:

```bash
sudo nano /etc/nginx/sites-available/m.phgcontrol.ru
```

Вставь следующую конфигурацию:

```nginx
# Temporary configuration for m.phgcontrol.ru (HTTP only for certbot)
server {
    listen 80;
    listen [::]:80;
    server_name m.phgcontrol.ru;

    # Root directory
    root /opt/usercontrol;

    # Allow certbot to verify domain
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/usercontrol/static/;
        expires 30d;
    }

    # Uploaded files
    location /uploads/ {
        alias /opt/usercontrol/uploads/;
        expires 7d;
    }
}
```

## 🔗 Шаг 3: Активировать конфигурацию

```bash
# Создать симлинк
sudo ln -s /etc/nginx/sites-available/m.phgcontrol.ru /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Если всё OK, перезагрузить nginx
sudo systemctl reload nginx
```

## 🔐 Шаг 4: Получить SSL сертификат

Теперь получим сертификат:

```bash
sudo certbot certonly --nginx -d m.phgcontrol.ru
```

Или если это не сработает, используй webroot метод:

```bash
sudo certbot certonly --webroot -w /var/www/html -d m.phgcontrol.ru
```

Certbot должен успешно получить сертификат!

## ✨ Шаг 5: Обновить конфигурацию с SSL

Теперь обновим конфигурацию, добавив SSL:

```bash
sudo nano /etc/nginx/sites-available/m.phgcontrol.ru
```

Замени весь файл на:

```nginx
# Mobile subdomain configuration for m.phgcontrol.ru with SSL
server {
    listen 80;
    listen [::]:80;
    server_name m.phgcontrol.ru;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name m.phgcontrol.ru;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/m.phgcontrol.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/m.phgcontrol.ru/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root directory
    root /opt/usercontrol;

    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Mobile-Access "true";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /opt/usercontrol/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Uploaded files (chat photos)
    location /uploads/ {
        alias /opt/usercontrol/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Favicon
    location /favicon.ico {
        alias /opt/usercontrol/static/favicon.ico;
        access_log off;
        log_not_found off;
    }

    # Logs
    access_log /var/log/nginx/m.phgcontrol.ru.access.log;
    error_log /var/log/nginx/m.phgcontrol.ru.error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
    gzip_disable "msie6";
}
```

## 🔄 Шаг 6: Проверить и перезагрузить

```bash
# Проверить конфигурацию
sudo nginx -t

# Если всё OK, перезагрузить nginx
sudo systemctl reload nginx
```

## ✅ Шаг 7: Проверка работы

### На компьютере
Открой в браузере: `https://m.phgcontrol.ru`

### На мобильном
1. Открой `https://m.phgcontrol.ru` на телефоне
2. Увидишь кнопку ☰ для открытия меню
3. Весь интерфейс адаптирован под мобильные устройства

## 🔧 Автоматическое обновление сертификата

Certbot автоматически настроил обновление. Проверь:

```bash
# Проверить таймер
sudo systemctl status certbot.timer

# Тест обновления (dry-run)
sudo certbot renew --dry-run
```

## 🎯 Итог

Теперь у тебя работают:
- ✅ `https://phgcontrol.ru` - основной домен
- ✅ `https://m.phgcontrol.ru` - мобильный поддомен

Оба используют один backend, но интерфейс автоматически адаптируется!

## 🆘 Troubleshooting

### Ошибка "502 Bad Gateway"
Проверь, что FastAPI запущен:
```bash
sudo systemctl status usercontrol-admin
sudo journalctl -u usercontrol-admin -n 50
```

### Ошибка SSL
Проверь сертификаты:
```bash
sudo certbot certificates
ls -la /etc/letsencrypt/live/m.phgcontrol.ru/
```

### Не открывается сайт
Проверь nginx логи:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/m.phgcontrol.ru.error.log
```

### Firewall
Убедись, что порты открыты:
```bash
sudo ufw status
sudo ufw allow 'Nginx Full'
```

## 📱 Проверка адаптивности

### Chrome DevTools
1. F12 → Toggle device toolbar (Ctrl+Shift+M)
2. Выбери устройство (iPhone, iPad, Galaxy)
3. Обнови страницу

### Реальное тестирование
- iPhone/iPad - Safari
- Android - Chrome
- Планшеты

## 🎉 Всё готово!

Мобильная версия полностью функциональна со всеми возможностями десктопной версии:
- 📊 Дашборд
- 👥 Управление пользователями
- 📋 Заявки на регистрацию
- 🎭 Роли и группы ролей
- 💬 Управление чатами
- 🔐 Безопасность и авторизация

**Адаптивный дизайн работает на ВСЕХ устройствах!** 📱💻🖥️

