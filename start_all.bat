@echo off
chcp 65001 >nul
echo ========================================
echo   User Control Bot - Запуск системы
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist "venv\" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Пожалуйста, сначала выполните установку:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo   python -m database.init_db
    echo.
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist ".env" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!
    echo Создайте .env на основе env.example
    echo.
    pause
    exit /b 1
)

REM Проверка наличия БД
if not exist "usercontrol.db" (
    echo [ПРЕДУПРЕЖДЕНИЕ] База данных не найдена!
    echo Инициализирую базу данных...
    call venv\Scripts\activate.bat
    python -m database.init_db
    echo.
)

echo Запуск Telegram бота в новом окне...
start "User Control Bot - Telegram Bot" cmd /k "venv\Scripts\activate.bat && python run_bot.py"

timeout /t 2 /nobreak >nul

echo Запуск админ-панели в новом окне...
start "User Control Bot - Admin Panel" cmd /k "venv\Scripts\activate.bat && python run_admin.py"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Система запущена!
echo ========================================
echo.
echo Telegram бот: Запущен
echo Админ-панель: http://localhost:8000
echo.
echo Логин: admin
echo Пароль: admin123
echo.
echo Для остановки закройте окна бота и панели
echo.

REM Открыть браузер с админ-панелью
timeout /t 2 /nobreak >nul
start http://localhost:8000

echo Нажмите любую клавишу для выхода...
pause >nul

