# User Control Bot - Система управления доступом сотрудников

Telegram-бот для автоматического управления доступом сотрудников к различным чатам на основе их ролей.

## 📋 Возможности

### Для сотрудников:
- Простая регистрация через отправку номера телефона
- Автоматическое получение ссылок на чаты после одобрения
- Проверка статуса заявки

### Для администраторов:
- Веб-панель управления
- Обработка заявок на регистрацию
- Управление ролями и чатами
- Привязка чатов к ролям
- Статистика и аналитика

## 🛠 Технологии

- **Python 3.10+**
- **python-telegram-bot** - Telegram Bot API
- **FastAPI** - Веб-панель администрирования
- **SQLAlchemy** - ORM
- **SQLite** - База данных
- **Bootstrap 5** - UI фреймворк

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd UserControlBot
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Отредактируйте `.env` и укажите:
- `BOT_TOKEN` - токен вашего бота от [@BotFather](https://t.me/BotFather)
- `ADMIN_SECRET_KEY` - секретный ключ для JWT (любая длинная строка)

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_SECRET_KEY=your-very-long-secret-key-here-change-me
```

### 5. Инициализация базы данных

```bash
python -m database.init_db
```

Эта команда:
- Создаст все необходимые таблицы
- Создаст администратора по умолчанию (admin/admin123)
- Создаст роли по умолчанию

## 🚀 Запуск

### Запуск бота

```bash
python run_bot.py
```

### Запуск админ-панели

```bash
python run_admin.py
```

Админ-панель будет доступна по адресу: `http://localhost:8000`

**Данные для входа по умолчанию:**
- Логин: `admin`
- Пароль: `admin123`

⚠️ **ВАЖНО:** Смените пароль после первого входа!

## 📁 Структура проекта

```
UserControlBot/
├── bot/                    # Telegram бот
│   ├── handlers.py        # Обработчики сообщений
│   ├── keyboards.py       # Клавиатуры
│   ├── utils.py          # Утилиты
│   └── main.py           # Точка входа бота
├── admin_panel/           # Веб-панель администрирования
│   ├── templates/        # HTML шаблоны
│   ├── auth.py          # Аутентификация
│   ├── routes.py        # API маршруты
│   └── main.py          # FastAPI приложение
├── database/              # База данных
│   ├── models.py         # Модели SQLAlchemy
│   ├── crud.py          # CRUD операции
│   ├── database.py      # Настройка БД
│   └── init_db.py       # Инициализация БД
├── static/               # Статические файлы (создайте при необходимости)
├── config.py            # Конфигурация
├── run_bot.py          # Запуск бота
├── run_admin.py        # Запуск админ-панели
├── requirements.txt    # Зависимости
└── README.md          # Документация
```

## 🔄 Рабочий процесс

### Регистрация нового сотрудника

1. Сотрудник отправляет `/start` боту
2. Бот запрашивает номер телефона
3. Сотрудник отправляет номер телефона
4. Заявка сохраняется со статусом "pending"
5. Администратор обрабатывает заявку через панель управления
6. После одобрения сотрудник получает ссылки на чаты

### Обработка заявки администратором

1. Вход в админ-панель
2. Переход в раздел "Заявки"
3. Выбор роли для пользователя
4. Нажатие кнопки "Одобрить"
5. Бот автоматически отправляет ссылки пользователю

## 🔐 Безопасность

- Пароли хешируются с использованием bcrypt
- API защищен JWT токенами
- Валидация всех входных данных
- HTTPS для продакшена (настраивается через Nginx)

## 📊 База данных

### Таблицы:

- **users** - пользователи системы
- **roles** - роли пользователей
- **chats** - Telegram чаты
- **role_chats** - связь ролей и чатов (many-to-many)
- **admins** - администраторы панели

## 🌐 Деплой на Ubuntu Server 20.04

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3.10 python3.10-venv python3-pip -y

# Установка Nginx
sudo apt install nginx -y

# Установка Supervisor
sudo apt install supervisor -y
```

### 2. Настройка проекта

```bash
# Создание директории для проекта
sudo mkdir -p /opt/usercontrol
sudo chown $USER:$USER /opt/usercontrol

# Клонирование проекта
cd /opt/usercontrol
git clone <your-repo> .

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
cp env.example .env
nano .env  # Укажите токены

# Инициализация БД
python -m database.init_db
```

### 3. Настройка Supervisor

Создайте файл `/etc/supervisor/conf.d/usercontrol.conf`:

```ini
[program:usercontrol_bot]
command=/opt/usercontrol/venv/bin/python /opt/usercontrol/run_bot.py
directory=/opt/usercontrol
user=your-username
autostart=true
autorestart=true
stderr_logfile=/var/log/usercontrol_bot.err.log
stdout_logfile=/var/log/usercontrol_bot.out.log

[program:usercontrol_admin]
command=/opt/usercontrol/venv/bin/python /opt/usercontrol/run_admin.py
directory=/opt/usercontrol
user=your-username
autostart=true
autorestart=true
stderr_logfile=/var/log/usercontrol_admin.err.log
stdout_logfile=/var/log/usercontrol_admin.out.log
```

Запуск:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 4. Настройка Nginx

Создайте файл `/etc/nginx/sites-available/usercontrol`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/usercontrol/static;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/usercontrol /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Настройка SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## 📝 API Документация

После запуска админ-панели, API документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤖 Команды бота

- `/start` - Начать работу с ботом
- `/help` - Справка
- `/status` - Проверить статус заявки
- `/mychats` - Получить ссылки на чаты

## 🔧 Управление

### Проверка статуса

```bash
sudo supervisorctl status
```

### Перезапуск

```bash
sudo supervisorctl restart usercontrol_bot
sudo supervisorctl restart usercontrol_admin
```

### Просмотр логов

```bash
sudo tail -f /var/log/usercontrol_bot.out.log
sudo tail -f /var/log/usercontrol_admin.out.log
```

### Резервное копирование БД

```bash
# Создание бэкапа
cp /opt/usercontrol/usercontrol.db /opt/usercontrol/backups/usercontrol_$(date +%Y%m%d_%H%M%S).db

# Автоматический бэкап (добавьте в crontab)
0 2 * * * cp /opt/usercontrol/usercontrol.db /opt/usercontrol/backups/usercontrol_$(date +\%Y\%m\%d_\%H\%M\%S).db
```

## 🐛 Troubleshooting

### Бот не отвечает
- Проверьте токен в `.env`
- Убедитесь, что процесс запущен: `sudo supervisorctl status`
- Проверьте логи: `sudo tail -f /var/log/usercontrol_bot.err.log`

### Админ-панель недоступна
- Проверьте, что процесс запущен: `sudo supervisorctl status usercontrol_admin`
- Проверьте настройки Nginx: `sudo nginx -t`
- Проверьте логи: `sudo tail -f /var/log/usercontrol_admin.err.log`

### Ошибки БД
- Убедитесь, что БД инициализирована: `python -m database.init_db`
- Проверьте права доступа к файлу БД

## 📞 Поддержка

Если у вас возникли вопросы или проблемы, создайте Issue в репозитории проекта.

## 📄 Лицензия

MIT License

---

**Дата создания:** 01.10.2025  
**Версия:** 1.0.0

