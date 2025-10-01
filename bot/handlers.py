"""Telegram bot message handlers."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import SessionLocal
from database.crud import (
    get_user_by_telegram_id,
    get_user_by_phone,
    create_user,
    get_chats_by_role
)
from bot.keyboards import get_phone_keyboard, get_remove_keyboard
from bot.utils import normalize_phone, validate_phone, format_chat_links

logger = logging.getLogger(__name__)

# User states
AWAITING_PHONE = 1

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = get_user_by_telegram_id(db, user.id)
        
        if existing_user:
            if existing_user.status == 'pending':
                await update.message.reply_text(
                    "⏳ Ваша заявка уже отправлена и ожидает одобрения администратором.\n\n"
                    "Используйте команду /status для проверки статуса.",
                    reply_markup=get_remove_keyboard()
                )
            elif existing_user.status == 'approved':
                await update.message.reply_text(
                    "✅ Вы уже зарегистрированы в системе!\n\n"
                    "Используйте команду /mychats чтобы получить ссылки на ваши чаты.",
                    reply_markup=get_remove_keyboard()
                )
            elif existing_user.status == 'rejected':
                await update.message.reply_text(
                    "❌ Ваша заявка была отклонена.\n\n"
                    "Обратитесь к администратору для получения дополнительной информации.",
                    reply_markup=get_remove_keyboard()
                )
        else:
            # New user - request phone number
            await update.message.reply_text(
                f"👋 Добро пожаловать, {user.first_name}!\n\n"
                "Я бот для управления доступом сотрудников к чатам компании.\n\n"
                "📱 Для начала работы, пожалуйста, поделитесь вашим номером телефона, "
                "нажав на кнопку ниже, или отправьте его вручную.",
                reply_markup=get_phone_keyboard()
            )
            context.user_data['state'] = AWAITING_PHONE
    
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📚 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/status - Проверить статус заявки\n"
        "/mychats - Получить ссылки на ваши чаты\n"
        "/help - Показать эту справку\n\n"
        "ℹ️ Если у вас возникли вопросы, обратитесь к администратору."
    )
    await update.message.reply_text(help_text, reply_markup=get_remove_keyboard())

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        existing_user = get_user_by_telegram_id(db, user.id)
        
        if not existing_user:
            await update.message.reply_text(
                "❓ Вы еще не зарегистрированы.\n\n"
                "Используйте команду /start для начала работы.",
                reply_markup=get_remove_keyboard()
            )
        else:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }
            status_text = {
                'pending': 'Ожидает одобрения',
                'approved': 'Одобрена',
                'rejected': 'Отклонена'
            }
            
            message = (
                f"{status_emoji.get(existing_user.status, '❓')} Статус вашей заявки: "
                f"{status_text.get(existing_user.status, 'Неизвестно')}\n\n"
            )
            
            if existing_user.role:
                message += f"👤 Роль: {existing_user.role.name}\n"
            
            if existing_user.status == 'approved':
                message += "\nИспользуйте команду /mychats чтобы получить ссылки на ваши чаты."
            
            await update.message.reply_text(message, reply_markup=get_remove_keyboard())
    
    finally:
        db.close()

async def mychats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mychats command."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        existing_user = get_user_by_telegram_id(db, user.id)
        
        if not existing_user:
            await update.message.reply_text(
                "❓ Вы еще не зарегистрированы.\n\n"
                "Используйте команду /start для начала работы.",
                reply_markup=get_remove_keyboard()
            )
        elif existing_user.status != 'approved':
            await update.message.reply_text(
                "⏳ Ваша заявка еще не одобрена.\n\n"
                "Дождитесь одобрения администратора.",
                reply_markup=get_remove_keyboard()
            )
        elif not existing_user.role:
            await update.message.reply_text(
                "⚠️ Вам еще не назначена роль.\n\n"
                "Обратитесь к администратору.",
                reply_markup=get_remove_keyboard()
            )
        else:
            chats = get_chats_by_role(db, existing_user.role_id)
            message = format_chat_links(chats)
            await update.message.reply_text(message, reply_markup=get_remove_keyboard())
    
    finally:
        db.close()

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact (phone number) sharing."""
    user = update.effective_user
    contact = update.message.contact
    
    # Verify that the contact is from the user themselves
    if contact.user_id != user.id:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте ваш собственный номер телефона.",
            reply_markup=get_phone_keyboard()
        )
        return
    
    phone = normalize_phone(contact.phone_number)
    db = SessionLocal()
    
    try:
        # Check if phone already exists
        existing_user = get_user_by_phone(db, phone)
        
        if existing_user:
            if existing_user.telegram_id == user.id:
                await update.message.reply_text(
                    "ℹ️ Вы уже зарегистрированы с этим номером телефона.",
                    reply_markup=get_remove_keyboard()
                )
            else:
                # Update telegram_id if phone exists but with different telegram_id
                existing_user.telegram_id = user.id
                existing_user.username = user.username
                existing_user.first_name = user.first_name
                existing_user.last_name = user.last_name
                db.commit()
                
                await update.message.reply_text(
                    "✅ Ваш Telegram ID обновлен.\n\n"
                    "Используйте команду /status для проверки статуса.",
                    reply_markup=get_remove_keyboard()
                )
        else:
            # Create new user
            create_user(
                db,
                phone_number=phone,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            await update.message.reply_text(
                "✅ Ваша заявка успешно отправлена!\n\n"
                "Администратор рассмотрит ее в ближайшее время.\n"
                "Вы получите уведомление, когда заявка будет обработана.\n\n"
                "Используйте команду /status для проверки статуса заявки.",
                reply_markup=get_remove_keyboard()
            )
            
            logger.info(f"New user request: {phone} (Telegram ID: {user.id})")
        
        context.user_data.pop('state', None)
    
    finally:
        db.close()

async def handle_text_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number sent as text."""
    user = update.effective_user
    phone_text = update.message.text
    
    # Check if user is in phone input state
    if context.user_data.get('state') != AWAITING_PHONE:
        return
    
    # Validate phone
    if not validate_phone(phone_text):
        await update.message.reply_text(
            "❌ Неверный формат номера телефона.\n\n"
            "Пожалуйста, отправьте корректный номер телефона или "
            "воспользуйтесь кнопкой для автоматической отправки.",
            reply_markup=get_phone_keyboard()
        )
        return
    
    phone = normalize_phone(phone_text)
    db = SessionLocal()
    
    try:
        # Check if phone already exists
        existing_user = get_user_by_phone(db, phone)
        
        if existing_user:
            if existing_user.telegram_id == user.id:
                await update.message.reply_text(
                    "ℹ️ Вы уже зарегистрированы с этим номером телефона.",
                    reply_markup=get_remove_keyboard()
                )
            else:
                # Update telegram_id if phone exists but with different telegram_id
                existing_user.telegram_id = user.id
                existing_user.username = user.username
                existing_user.first_name = user.first_name
                existing_user.last_name = user.last_name
                db.commit()
                
                await update.message.reply_text(
                    "✅ Ваш Telegram ID обновлен.\n\n"
                    "Используйте команду /status для проверки статуса.",
                    reply_markup=get_remove_keyboard()
                )
        else:
            # Create new user
            create_user(
                db,
                phone_number=phone,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            await update.message.reply_text(
                "✅ Ваша заявка успешно отправлена!\n\n"
                "Администратор рассмотрит ее в ближайшее время.\n"
                "Вы получите уведомление, когда заявка будет обработана.\n\n"
                "Используйте команду /status для проверки статуса заявки.",
                reply_markup=get_remove_keyboard()
            )
            
            logger.info(f"New user request: {phone} (Telegram ID: {user.id})")
        
        context.user_data.pop('state', None)
    
    finally:
        db.close()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

