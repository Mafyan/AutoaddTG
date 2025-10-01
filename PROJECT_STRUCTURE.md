# 📁 Структура проекта User Control Bot

```
UserControlBot/
│
├── 📂 bot/                          # Telegram бот
│   ├── __init__.py                 # Инициализация модуля
│   ├── main.py                     # Точка входа бота
│   ├── handlers.py                 # Обработчики команд и сообщений
│   ├── keyboards.py                # Клавиатуры для бота
│   └── utils.py                    # Вспомогательные функции
│
├── 📂 admin_panel/                  # Веб-панель администрирования
│   ├── __init__.py                 # Инициализация модуля
│   ├── main.py                     # FastAPI приложение
│   ├── routes.py                   # API маршруты
│   ├── auth.py                     # Аутентификация (JWT)
│   └── 📂 templates/               # HTML шаблоны
│       ├── base.html               # Базовый шаблон
│       ├── login.html              # Страница входа
│       ├── dashboard.html          # Главная панель
│       ├── requests.html           # Заявки на регистрацию
│       ├── users.html              # Управление пользователями
│       ├── roles.html              # Управление ролями
│       └── chats.html              # Управление чатами
│
├── 📂 database/                     # База данных
│   ├── __init__.py                 # Инициализация модуля
│   ├── database.py                 # Настройка подключения к БД
│   ├── models.py                   # Модели SQLAlchemy
│   ├── crud.py                     # CRUD операции
│   └── init_db.py                  # Скрипт инициализации БД
│
├── 📂 static/                       # Статические файлы
│   ├── 📂 css/                     # Стили
│   │   └── custom.css              # Пользовательские стили
│   └── 📂 js/                      # JavaScript
│       └── main.js                 # Основной JS файл
│
├── 📂 deploy/                       # Конфигурация для деплоя
│   ├── deploy.sh                   # Автоматический скрипт деплоя
│   ├── supervisor.conf             # Конфигурация Supervisor
│   ├── nginx.conf                  # Конфигурация Nginx
│   └── README.md                   # Инструкции по деплою
│
├── 📄 config.py                     # Конфигурация приложения
├── 📄 run_bot.py                    # Запуск Telegram бота
├── 📄 run_admin.py                  # Запуск админ-панели
│
├── 📄 requirements.txt              # Python зависимости
├── 📄 env.example                   # Пример файла переменных окружения
├── 📄 .gitignore                    # Игнорируемые файлы Git
│
├── 📄 install.bat                   # Установка (Windows)
├── 📄 start_all.bat                 # Запуск всех сервисов (Windows)
├── 📄 install.sh                    # Установка (Linux)
├── 📄 start_all.sh                  # Запуск всех сервисов (Linux)
├── 📄 stop_all.sh                   # Остановка всех сервисов (Linux)
│
├── 📄 README.md                     # Основная документация
├── 📄 QUICKSTART.md                 # Быстрый старт
├── 📄 instruction.md                # План разработки
├── 📄 PROJECT_STRUCTURE.md          # Этот файл
└── 📄 LICENSE                       # Лицензия MIT

📦 Создаваемые файлы (не в Git):
├── 📂 venv/                         # Виртуальное окружение Python
├── 📂 logs/                         # Логи приложения
├── 📂 backups/                      # Резервные копии БД
├── 📄 .env                          # Переменные окружения (секретные)
├── 📄 usercontrol.db                # База данных SQLite
└── 📄 pids.txt                      # PID процессов (Linux)
```

## 📋 Описание компонентов

### 🤖 Telegram Bot (`bot/`)

**Назначение:** Взаимодействие с пользователями через Telegram

**Ключевые файлы:**
- `main.py` - настройка и запуск бота
- `handlers.py` - обработка команд (`/start`, `/help`, `/status`, `/mychats`)
- `keyboards.py` - кнопки для бота
- `utils.py` - форматирование, валидация данных

**Команды бота:**
- `/start` - регистрация нового пользователя
- `/help` - справка
- `/status` - проверка статуса заявки
- `/mychats` - получение ссылок на чаты

### 🖥️ Admin Panel (`admin_panel/`)

**Назначение:** Веб-интерфейс для администраторов

**Ключевые файлы:**
- `main.py` - FastAPI приложение
- `routes.py` - API endpoints и страницы
- `auth.py` - JWT аутентификация
- `templates/` - HTML страницы

**Страницы:**
- `/` - Вход в систему
- `/dashboard` - Статистика и обзор
- `/requests` - Обработка заявок
- `/users` - Управление пользователями
- `/roles` - Управление ролями
- `/chats` - Управление чатами

**API Endpoints:**
- `POST /api/login` - аутентификация
- `GET /api/stats` - статистика
- `GET /api/users` - список пользователей
- `POST /api/requests/{id}/approve` - одобрить заявку
- `POST /api/requests/{id}/reject` - отклонить заявку
- `GET/POST/PUT/DELETE /api/roles` - работа с ролями
- `GET/POST/PUT/DELETE /api/chats` - работа с чатами

### 💾 Database (`database/`)

**Назначение:** Работа с базой данных

**Ключевые файлы:**
- `database.py` - подключение к SQLite
- `models.py` - модели данных (User, Role, Chat, Admin)
- `crud.py` - операции создания, чтения, обновления, удаления
- `init_db.py` - инициализация БД с данными по умолчанию

**Таблицы:**
1. `users` - пользователи системы
2. `roles` - роли (Управляющий, Менеджер и т.д.)
3. `chats` - Telegram чаты
4. `role_chats` - связь ролей и чатов (many-to-many)
5. `admins` - администраторы панели

### 🎨 Static Files (`static/`)

**Назначение:** CSS, JavaScript, изображения

**Файлы:**
- `css/custom.css` - стили для админ-панели
- `js/main.js` - JavaScript функции

### 🚀 Deploy (`deploy/`)

**Назначение:** Конфигурация для развертывания на сервере

**Файлы:**
- `deploy.sh` - автоматическая установка на Ubuntu
- `supervisor.conf` - автозапуск сервисов
- `nginx.conf` - настройка веб-сервера

## 🔄 Потоки данных

### Регистрация пользователя:

```
Пользователь → Telegram Bot → handlers.py → crud.py → Database
                                              ↓
                                    Статус: pending
```

### Одобрение заявки:

```
Админ → Web Panel → routes.py → crud.py → Database
                         ↓
                  Telegram Bot → Уведомление пользователю
```

### Получение чатов:

```
Пользователь → /mychats → handlers.py → crud.py → Database
                                              ↓
                                      Роль → Чаты → Ссылки
```

## 🔐 Безопасность

- **Пароли**: Хешируются с bcrypt (database/crud.py)
- **API**: Защищен JWT токенами (admin_panel/auth.py)
- **Валидация**: Проверка всех входных данных (bot/utils.py)
- **Переменные окружения**: Секреты в .env файле

## 📊 Технологии

| Компонент | Технология | Файл |
|-----------|-----------|------|
| Telegram Bot | python-telegram-bot | bot/main.py |
| Web Framework | FastAPI | admin_panel/main.py |
| ORM | SQLAlchemy | database/models.py |
| Database | SQLite | usercontrol.db |
| Frontend | Bootstrap 5 + Vanilla JS | templates/*.html |
| Authentication | JWT (python-jose) | admin_panel/auth.py |
| Password Hashing | bcrypt (passlib) | database/crud.py |

## 🛠️ Разработка

### Добавление новой команды бота:

1. Создайте обработчик в `bot/handlers.py`
2. Зарегистрируйте в `bot/main.py`
3. Добавьте в `/help` описание

### Добавление новой страницы админ-панели:

1. Создайте HTML шаблон в `admin_panel/templates/`
2. Добавьте route в `admin_panel/routes.py`
3. Добавьте ссылку в sidebar

### Добавление новой таблицы в БД:

1. Создайте модель в `database/models.py`
2. Добавьте CRUD операции в `database/crud.py`
3. Запустите `python -m database.init_db`

## 📞 Полезные ссылки

- [README.md](README.md) - Полная документация
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [instruction.md](instruction.md) - План разработки
- [deploy/README.md](deploy/README.md) - Инструкции по деплою

---

**Версия:** 1.0.0  
**Дата:** 01.10.2025

