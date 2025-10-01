# 🚀 Инструкция по установке на Linux сервер

## 📋 Требования

- **ОС:** Ubuntu 20.04 LTS или выше (рекомендуется Ubuntu 22.04)
- **Доступ:** SSH доступ с правами sudo
- **Память:** Минимум 512 MB RAM (рекомендуется 1 GB)
- **Место:** Минимум 1 GB свободного места
- **Домен:** Опционально (для HTTPS)

---

## 🔧 Шаг 1: Подключение к серверу

```bash
ssh root@your-server-ip
# или
ssh username@your-server-ip
```

---

## 📦 Шаг 2: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 🐍 Шаг 3: Установка необходимых пакетов

```bash
sudo apt install -y python3.10 python3.10-venv python3-pip git nginx supervisor
```

Проверьте версию Python:
```bash
python3 --version
# Должно быть Python 3.10 или выше
```

---

## 📥 Шаг 4: Клонирование проекта

```bash
# Создайте директорию для проекта
sudo mkdir -p /opt/usercontrol
sudo chown $USER:$USER /opt/usercontrol

# Клонируйте репозиторий
cd /opt/usercontrol
git clone https://github.com/Mafyan/AutoaddTG.git .
```

---

## 🔐 Шаг 5: Настройка переменных окружения

Создайте файл `.env`:

```bash
nano .env
```

Вставьте следующее содержимое:

```env
# Telegram Bot Configuration
BOT_TOKEN=8455013739:AAFHQoURGP1HBBqIhfzQNMGRDOLndFQpiYc

# Admin Panel Configuration
ADMIN_SECRET_KEY=your-super-secret-key-change-this-to-random-string-min-32-chars
ADMIN_PANEL_HOST=0.0.0.0
ADMIN_PANEL_PORT=8000

# Database Configuration
DATABASE_URL=sqlite:///./usercontrol.db

# Default Admin Credentials (ОБЯЗАТЕЛЬНО СМЕНИТЕ ПОСЛЕ ПЕРВОГО ВХОДА!)
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_TELEGRAM_ID=0

# Security
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

**ВАЖНО:** Замените `ADMIN_SECRET_KEY` на свою длинную случайную строку!

Сгенерируйте секретный ключ:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Скопируйте результат и вставьте в `ADMIN_SECRET_KEY`.

Сохраните файл: `Ctrl+X`, затем `Y`, затем `Enter`

---

## 🐍 Шаг 6: Создание виртуального окружения

```bash
cd /opt/usercontrol
python3 -m venv venv
source venv/bin/activate
```

---

## 📚 Шаг 7: Установка зависимостей Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Это займет 1-2 минуты.

---

## 💾 Шаг 8: Инициализация базы данных

```bash
python -m database.init_db
```

Вы должны увидеть:
```
Creating database tables...
✓ Tables created successfully

Creating default admin...
✓ Default admin created: admin
  Password: admin123
  ⚠️  ВАЖНО: Смените пароль после первого входа!

Creating default roles...
✓ Created 8 default roles
```

---

## 🔧 Шаг 9: Настройка Supervisor (автозапуск)

Создайте конфигурационный файл:

```bash
sudo nano /etc/supervisor/conf.d/usercontrol.conf
```

Вставьте следующее (замените `username` на ваше имя пользователя):

```ini
[program:usercontrol_bot]
command=/opt/usercontrol/venv/bin/python /opt/usercontrol/run_bot.py
directory=/opt/usercontrol
user=YOUR_USERNAME
autostart=true
autorestart=true
stderr_logfile=/var/log/usercontrol_bot.err.log
stdout_logfile=/var/log/usercontrol_bot.out.log
environment=PATH="/opt/usercontrol/venv/bin"

[program:usercontrol_admin]
command=/opt/usercontrol/venv/bin/python /opt/usercontrol/run_admin.py
directory=/opt/usercontrol
user=YOUR_USERNAME
autostart=true
autorestart=true
stderr_logfile=/var/log/usercontrol_admin.err.log
stdout_logfile=/var/log/usercontrol_admin.out.log
environment=PATH="/opt/usercontrol/venv/bin"
```

Замените `YOUR_USERNAME` на ваше имя пользователя (узнать командой `whoami`).

Сохраните: `Ctrl+X`, `Y`, `Enter`

Обновите конфигурацию Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

Проверьте статус:
```bash
sudo supervisorctl status
```

Должно быть:
```
usercontrol_admin                RUNNING   pid 12345, uptime 0:00:05
usercontrol_bot                  RUNNING   pid 12346, uptime 0:00:05
```

---

## 🌐 Шаг 10: Настройка Nginx

Создайте конфигурацию Nginx:

```bash
sudo nano /etc/nginx/sites-available/usercontrol
```

Вставьте (замените `your-domain.com` на ваш домен или IP):

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен или IP
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /opt/usercontrol/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Сохраните: `Ctrl+X`, `Y`, `Enter`

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/usercontrol /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Удалите дефолтный сайт
```

Проверьте конфигурацию:
```bash
sudo nginx -t
```

Должно быть: `syntax is ok` и `test is successful`

Перезапустите Nginx:
```bash
sudo systemctl restart nginx
```

---

## 🔥 Шаг 11: Настройка файрвола (опционально)

```bash
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS (для SSL)
sudo ufw enable
sudo ufw status
```

---

## 🔒 Шаг 12: Настройка SSL/HTTPS (опционально, но рекомендуется)

Если у вас есть доменное имя:

```bash
# Установите Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получите SSL сертификат
sudo certbot --nginx -d your-domain.com

# Certbot автоматически настроит Nginx для HTTPS
```

Сертификат будет автоматически обновляться.

---

## ✅ Шаг 13: Проверка работы

### Проверка Telegram бота:

1. Откройте Telegram
2. Найдите вашего бота (по имени, которое вы указали в BotFather)
3. Отправьте `/start`
4. Бот должен ответить

### Проверка админ-панели:

Откройте в браузере:
- HTTP: `http://your-server-ip` или `http://your-domain.com`
- HTTPS: `https://your-domain.com` (если настроили SSL)

**Данные для входа:**
- Логин: `admin`
- Пароль: `admin123`

⚠️ **ВАЖНО:** Сразу смените пароль после входа!

---

## 📊 Шаг 14: Настройка автоматического резервного копирования

Создайте скрипт бэкапа:

```bash
sudo nano /opt/usercontrol/backup.sh
```

Вставьте:

```bash
#!/bin/bash
BACKUP_DIR="/opt/usercontrol/backups"
DB_FILE="/opt/usercontrol/usercontrol.db"

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/usercontrol_$(date +%Y%m%d_%H%M%S).db

# Удалить бэкапы старше 7 дней
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed at $(date)"
```

Сохраните и сделайте исполняемым:

```bash
sudo chmod +x /opt/usercontrol/backup.sh
```

Добавьте в crontab (ежедневный бэкап в 2:00 AM):

```bash
crontab -e
```

Добавьте строку:
```
0 2 * * * /opt/usercontrol/backup.sh >> /var/log/usercontrol_backup.log 2>&1
```

---

## 🔍 Управление и мониторинг

### Просмотр логов:

```bash
# Логи бота
sudo tail -f /var/log/usercontrol_bot.out.log
sudo tail -f /var/log/usercontrol_bot.err.log

# Логи админ-панели
sudo tail -f /var/log/usercontrol_admin.out.log
sudo tail -f /var/log/usercontrol_admin.err.log

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Управление сервисами:

```bash
# Проверка статуса
sudo supervisorctl status

# Перезапуск всех сервисов
sudo supervisorctl restart all

# Перезапуск только бота
sudo supervisorctl restart usercontrol_bot

# Перезапуск только админ-панели
sudo supervisorctl restart usercontrol_admin

# Остановка
sudo supervisorctl stop all

# Запуск
sudo supervisorctl start all
```

### Обновление проекта:

```bash
cd /opt/usercontrol
sudo supervisorctl stop all

# Создайте бэкап БД
cp usercontrol.db backups/usercontrol_before_update_$(date +%Y%m%d).db

# Обновите код
git pull

# Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt

# Перезапустите
sudo supervisorctl start all
```

---

## 🎯 Первоначальная настройка через панель управления

1. **Войдите в панель**: `http://your-domain.com`
   - Логин: `admin`
   - Пароль: `admin123`

2. **Смените пароль** (через базу данных пока нет интерфейса):
   ```bash
   cd /opt/usercontrol
   source venv/bin/activate
   python -c "
   from database.database import SessionLocal
   from database.crud import update_admin_password, get_admin_by_username
   db = SessionLocal()
   admin = get_admin_by_username(db, 'admin')
   update_admin_password(db, admin.id, 'YOUR_NEW_STRONG_PASSWORD')
   print('Password updated!')
   "
   ```

3. **Добавьте чаты:**
   - Перейдите в раздел "Чаты"
   - Нажмите "Добавить чат"
   - Укажите название, ссылку на чат, описание
   - Сохраните

4. **Настройте роли:**
   - Перейдите в раздел "Роли"
   - Выберите роль (уже созданы по умолчанию)
   - Нажмите "Редактировать"
   - Привяжите нужные чаты к этой роли
   - Сохраните

5. **Протестируйте:**
   - Найдите бота в Telegram
   - Отправьте `/start`
   - Поделитесь номером телефона
   - В панели обработайте заявку
   - Проверьте, что бот отправил ссылки

---

## 🐛 Решение проблем

### Бот не отвечает:

```bash
# Проверьте логи
sudo tail -n 50 /var/log/usercontrol_bot.err.log

# Проверьте статус
sudo supervisorctl status usercontrol_bot

# Перезапустите
sudo supervisorctl restart usercontrol_bot

# Проверьте токен в .env
cat /opt/usercontrol/.env | grep BOT_TOKEN
```

### Админ-панель недоступна:

```bash
# Проверьте логи
sudo tail -n 50 /var/log/usercontrol_admin.err.log

# Проверьте Nginx
sudo nginx -t
sudo systemctl status nginx

# Проверьте, работает ли панель
curl http://localhost:8000/health

# Должно вернуть: {"status":"healthy"}
```

### Ошибка базы данных:

```bash
# Проверьте права
ls -la /opt/usercontrol/usercontrol.db

# Исправьте права
sudo chown $USER:$USER /opt/usercontrol/usercontrol.db

# Переинициализируйте (⚠️ удалит данные)
cd /opt/usercontrol
source venv/bin/activate
rm usercontrol.db
python -m database.init_db
```

---

## 📞 Полезные команды

```bash
# Узнать IP сервера
curl ifconfig.me

# Узнать использование ресурсов
htop

# Проверить открытые порты
sudo netstat -tulpn

# Проверить место на диске
df -h

# Размер базы данных
du -h /opt/usercontrol/usercontrol.db

# Количество пользователей в БД
cd /opt/usercontrol && source venv/bin/activate
python -c "
from database.database import SessionLocal
from database.models import User
db = SessionLocal()
print(f'Total users: {db.query(User).count()}')
print(f'Pending: {db.query(User).filter(User.status==\"pending\").count()}')
print(f'Approved: {db.query(User).filter(User.status==\"approved\").count()}')
"
```

---

## 🎉 Готово!

Ваш User Control Bot успешно установлен и работает!

### 📋 Чек-лист:
- ✅ Бот работает (проверьте в Telegram)
- ✅ Админ-панель доступна
- ✅ Пароль администратора изменен
- ✅ Чаты добавлены
- ✅ Роли настроены
- ✅ Резервное копирование настроено

### 🔗 Ваши ссылки:
- **Админ-панель:** http://your-domain.com (или http://your-server-ip)
- **Telegram бот:** @YourBotName (имя из BotFather)
- **Репозиторий:** https://github.com/Mafyan/AutoaddTG

---

## 📚 Дополнительная информация

- **Полная документация:** [README.md](README.md)
- **Быстрый старт:** [QUICKSTART.md](QUICKSTART.md)
- **Структура проекта:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

**Удачи в использовании! 🚀**

Если возникнут вопросы - проверьте логи или создайте Issue на GitHub.

