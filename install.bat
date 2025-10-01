@echo off
chcp 65001 >nul
echo ========================================
echo   User Control Bot - Установка
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не установлен!
    echo Скачайте Python 3.10+ с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Проверка Python...
python --version
echo.

echo [2/5] Создание виртуального окружения...
if exist "venv\" (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    echo ✓ Виртуальное окружение создано
)
echo.

echo [3/5] Установка зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✓ Зависимости установлены
echo.

echo [4/5] Настройка переменных окружения...
if exist ".env" (
    echo Файл .env уже существует
) else (
    copy env.example .env
    echo ✓ Создан файл .env
    echo.
    echo [ВАЖНО] Отредактируйте файл .env и укажите:
    echo   - BOT_TOKEN (получите у @BotFather в Telegram)
    echo   - ADMIN_SECRET_KEY (любая длинная строка)
    echo.
    echo Открыть .env для редактирования? (Y/N)
    set /p edit_env=
    if /i "%edit_env%"=="Y" (
        notepad .env
    )
)
echo.

echo [5/5] Инициализация базы данных...
if exist "usercontrol.db" (
    echo База данных уже существует
) else (
    python -m database.init_db
    echo ✓ База данных инициализирована
)
echo.

echo ========================================
echo   Установка завершена!
echo ========================================
echo.
echo Следующие шаги:
echo.
echo 1. Убедитесь, что в .env указан BOT_TOKEN
echo 2. Запустите систему: start_all.bat
echo 3. Откройте http://localhost:8000
echo 4. Войдите (admin / admin123)
echo.
echo Полная инструкция: QUICKSTART.md
echo.
pause

