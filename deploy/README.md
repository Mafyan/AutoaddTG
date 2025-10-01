# Инструкция по деплою на Ubuntu 20.04

Этот каталог содержит файлы конфигурации для развертывания User Control Bot на Ubuntu 20.04.

## 📋 Файлы

- `deploy.sh` - автоматический скрипт развертывания
- `supervisor.conf` - конфигурация Supervisor для автозапуска
- `nginx.conf` - конфигурация Nginx для веб-панели

## 🚀 Быстрый старт

### Автоматическая установка

```bash
# Скачайте проект на сервер
git clone <your-repo-url> /opt/usercontrol
cd /opt/usercontrol

# Запустите скрипт развертывания
sudo bash deploy/deploy.sh
```

Скрипт автоматически:
1. Обновит систему
2. Установит все необходимые пакеты
3. Создаст виртуальное окружение
4. Установит зависимости Python
5. Настроит переменные окружения
6. Инициализирует базу данных
7. Настроит Supervisor для автозапуска
8. Настроит Nginx
9. Настроит автоматическое резервное копирование
10. Запустит все сервисы

### Ручная установка

Если вы предпочитаете ручную установку, следуйте инструкциям в главном README.md.

## ⚙️ Конфигурация

### Supervisor

Файл: `/etc/supervisor/conf.d/usercontrol.conf`

Управление:
```bash
# Проверка статуса
sudo supervisorctl status

# Запуск
sudo supervisorctl start all

# Остановка
sudo supervisorctl stop all

# Перезапуск
sudo supervisorctl restart all

# Перечитать конфигурацию
sudo supervisorctl reread
sudo supervisorctl update
```

### Nginx

Файл: `/etc/nginx/sites-available/usercontrol`

Управление:
```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск
sudo systemctl restart nginx

# Просмотр логов
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔒 SSL/HTTPS

### Установка Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot автоматически:
- Получит сертификат
- Обновит конфигурацию Nginx
- Настроит автоматическое обновление

### Проверка автообновления

```bash
sudo certbot renew --dry-run
```

## 📊 Мониторинг

### Просмотр логов

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

### Статус сервисов

```bash
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status supervisor
```

## 💾 Резервное копирование

### Автоматическое

Скрипт `backup.sh` автоматически создает резервные копии БД каждый день в 2:00 AM.

Копии хранятся в `/opt/usercontrol/backups/` и автоматически удаляются через 7 дней.

### Ручное

```bash
# Создать бэкап
cp /opt/usercontrol/usercontrol.db /opt/usercontrol/backups/usercontrol_manual_$(date +%Y%m%d_%H%M%S).db

# Восстановить из бэкапа
cp /opt/usercontrol/backups/usercontrol_20231001_120000.db /opt/usercontrol/usercontrol.db
sudo supervisorctl restart all
```

## 🔄 Обновление проекта

```bash
cd /opt/usercontrol

# Остановить сервисы
sudo supervisorctl stop all

# Создать бэкап
cp usercontrol.db backups/usercontrol_before_update_$(date +%Y%m%d_%H%M%S).db

# Получить обновления
git pull

# Активировать виртуальное окружение
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt

# Применить миграции (если есть)
# python -m database.migrate

# Перезапустить сервисы
sudo supervisorctl start all

# Проверить статус
sudo supervisorctl status
```

## 🐛 Устранение неполадок

### Бот не запускается

1. Проверьте логи:
   ```bash
   sudo tail -f /var/log/usercontrol_bot.err.log
   ```

2. Проверьте .env файл:
   ```bash
   cat /opt/usercontrol/.env
   ```

3. Проверьте статус:
   ```bash
   sudo supervisorctl status usercontrol_bot
   ```

4. Перезапустите:
   ```bash
   sudo supervisorctl restart usercontrol_bot
   ```

### Админ-панель недоступна

1. Проверьте логи:
   ```bash
   sudo tail -f /var/log/usercontrol_admin.err.log
   sudo tail -f /var/log/nginx/error.log
   ```

2. Проверьте статус:
   ```bash
   sudo supervisorctl status usercontrol_admin
   sudo systemctl status nginx
   ```

3. Проверьте порт:
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

4. Проверьте конфигурацию Nginx:
   ```bash
   sudo nginx -t
   ```

### Ошибки базы данных

1. Проверьте права доступа:
   ```bash
   ls -la /opt/usercontrol/usercontrol.db
   ```

2. Исправьте права:
   ```bash
   sudo chown ubuntu:ubuntu /opt/usercontrol/usercontrol.db
   ```

3. Переинициализируйте (⚠️ удалит все данные):
   ```bash
   cd /opt/usercontrol
   source venv/bin/activate
   rm usercontrol.db
   python -m database.init_db
   ```

## 🔐 Безопасность

### Рекомендации

1. **Смените пароль администратора** сразу после установки
2. **Используйте HTTPS** для продакшена
3. **Настройте файрвол** (ufw)
4. **Регулярно обновляйте** систему и зависимости
5. **Делайте резервные копии** базы данных
6. **Ограничьте SSH доступ** (смените порт, используйте ключи)

### Настройка файрвола (UFW)

```bash
# Включить UFW
sudo ufw enable

# Разрешить SSH (ВАЖНО: сделайте это первым!)
sudo ufw allow 22

# Разрешить HTTP и HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Проверить статус
sudo ufw status
```

### Изменение порта SSH (опционально)

```bash
sudo nano /etc/ssh/sshd_config
# Измените Port 22 на другой порт, например Port 2222

sudo systemctl restart sshd

# Разрешите новый порт в файрволе
sudo ufw allow 2222
```

## 📞 Поддержка

Если у вас возникли проблемы при развертывании:

1. Проверьте логи всех сервисов
2. Убедитесь, что все зависимости установлены
3. Проверьте конфигурационные файлы
4. Создайте Issue в репозитории проекта

---

**Важно:** Всегда делайте резервные копии перед обновлением или изменением конфигурации!

