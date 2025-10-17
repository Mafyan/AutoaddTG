"""Telegram bot message handlers."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import SessionLocal
from database.crud import (
    get_user_by_telegram_id,
    get_user_by_phone,
    create_user,
    get_chats_by_role,
    add_chat_member,
    get_admin_by_telegram_id,
    create_chat,
    get_chat_by_chat_id,
    update_chat
)
from bot.chat_manager import ChatManager
from config import settings
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
    """Handle /mychats command - creates new temporary invite links."""
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
        elif existing_user.status == 'fired':
            await update.message.reply_text(
                "🚫 Ваш доступ к системе был отозван.\n\n"
                "Обратитесь к администратору для получения дополнительной информации.",
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
            # Create new temporary invite links (12 hours, single use)
            from bot.chat_manager import ChatManager
            chat_manager = ChatManager(settings.BOT_TOKEN)
            
            await update.message.reply_text(
                "🔄 Создаю новые временные ссылки...",
                reply_markup=get_remove_keyboard()
            )
            
            temp_links = await chat_manager.get_role_temporary_invite_links(existing_user.role_id, hours=12)
            
            message = (
                f"🔗 Ваши персональные ссылки на чаты:\n"
                f"⏰ Срок действия: 12 часов\n"
                f"👤 Использований: 1 раз\n\n"
            )
            
            # Add links
            for idx, link_info in enumerate(temp_links, 1):
                if link_info['success'] and link_info['invite_link']:
                    message += f"{idx}. {link_info['chat_name']}\n{link_info['invite_link']}\n\n"
                else:
                    message += f"{idx}. {link_info['chat_name']} - ⚠️ Ошибка создания ссылки\n\n"
            
            message += (
                f"⚠️ ВАЖНО:\n"
                f"• Ссылки действуют только 12 часов\n"
                f"• Каждая ссылка одноразовая (1 использование)\n"
                f"• Присоединяйтесь к чатам как можно скорее!"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=get_remove_keyboard(),
                disable_web_page_preview=True
            )
    
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

async def list_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listchats command for admins."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user is admin
        admin = get_admin_by_telegram_id(db, user.id)
        if not admin:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Get all chats where bot is a member
        chat_manager = ChatManager(settings.BOT_TOKEN)
        chats = await chat_manager.get_bot_chats()
        
        if not chats:
            await update.message.reply_text("🤖 Бот не найден ни в одном групповом чате.")
            return
        
        # Format response
        message = "📋 **Список чатов, где находится бот:**\n\n"
        
        for i, chat in enumerate(chats, 1):
            message += f"{i}. **{chat['title']}**\n"
            message += f"   ID: `{chat['id']}`\n"
            message += f"   Тип: {chat['type']}\n"
            if chat['username']:
                message += f"   Username: @{chat['username']}\n"
            if chat['invite_link']:
                message += f"   [Ссылка]({chat['invite_link']})\n"
            message += "\n"
        
        # Split message if too long
        if len(message) > 4000:
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in list_chats_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка чатов.")
    finally:
        db.close()

async def sync_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /syncchats command for admins."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user is admin
        admin = get_admin_by_telegram_id(db, user.id)
        if not admin:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        await update.message.reply_text("🔄 Начинаю синхронизацию чатов...")
        
        # Sync chats to database
        chat_manager = ChatManager(settings.BOT_TOKEN)
        results = await chat_manager.sync_chats_to_database(db)
        
        message = f"✅ **Синхронизация завершена!**\n\n"
        message += f"📊 **Результаты:**\n"
        message += f"• Найдено чатов: {results['total_found']}\n"
        message += f"• Создано: {results['created']}\n"
        message += f"• Обновлено: {results['updated']}\n"
        message += f"• Ошибок: {results['errors']}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in sync_chats_command: {e}")
        await update.message.reply_text("❌ Ошибка при синхронизации чатов.")
    finally:
        db.close()

async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot being added to or removed from chats."""
    db = SessionLocal()
    
    try:
        my_chat_member = update.my_chat_member
        chat = my_chat_member.chat
        old_status = my_chat_member.old_chat_member.status
        new_status = my_chat_member.new_chat_member.status
        
        print(f"DEBUG: Bot status changed in chat {chat.id} ({chat.title})")
        print(f"DEBUG: From {old_status} to {new_status}")
        
        # Only process group chats
        if chat.type not in ['group', 'supergroup']:
            return
        
        # Bot was added to chat
        if old_status in ['left', 'kicked'] and new_status == 'member':
            print(f"DEBUG: Bot added to chat {chat.id}")
            await _add_chat_to_database(db, chat)
            
            # Trigger chat sync to update web panel
            try:
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                await chat_manager.sync_chats_to_database(db)
                print(f"DEBUG: Synced chats to database after bot addition")
            except Exception as e:
                print(f"DEBUG: Error syncing chats: {e}")
            
        # Bot was removed from chat
        elif old_status == 'member' and new_status in ['left', 'kicked']:
            print(f"DEBUG: Bot removed from chat {chat.id}")
            # You can add logic here to mark chat as inactive if needed
            
    except Exception as e:
        logger.error(f"Error in handle_my_chat_member: {e}")
    finally:
        db.close()

async def _add_chat_to_database(db: SessionLocal, chat):
    """Add chat to database when bot is added."""
    try:
        # Check if chat already exists
        existing_chat = get_chat_by_chat_id(db, chat.id)
        
        if existing_chat:
            # Update existing chat
            update_chat(db, existing_chat.id, 
                       chat_name=chat.title,
                       chat_link=None)  # Will be updated later
            print(f"DEBUG: Updated existing chat {chat.title}")
        else:
            # Create new chat
            chat_obj = create_chat(db, 
                                 chat_name=chat.title,
                                 chat_link=None,
                                 chat_id=chat.id,
                                 description=f"Auto-added {chat.type} chat")
            print(f"DEBUG: Created new chat {chat.title} with ID {chat_obj.id}")
            
            # Try to get invite link
            try:
                from telegram import Bot
                bot = Bot(token=settings.BOT_TOKEN)
                invite_link = await bot.export_chat_invite_link(chat.id)
                update_chat(db, chat_obj.id, chat_link=invite_link)
                print(f"DEBUG: Got invite link for {chat.title}")
            except Exception as e:
                print(f"DEBUG: Could not get invite link for {chat.title}: {e}")
                
    except Exception as e:
        logger.error(f"Error adding chat to database: {e}")

async def handle_message_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in groups to track chat activity."""
    db = SessionLocal()
    
    try:
        chat = update.effective_chat
        
        # Only process group chats
        if chat.type not in ['group', 'supergroup']:
            return
            
        # Check if this is a new chat for us
        existing_chat = get_chat_by_chat_id(db, chat.id)
        if not existing_chat:
            print(f"DEBUG: New group chat detected: {chat.title} (ID: {chat.id})")
            await _add_chat_to_database(db, chat)
            
            # Trigger chat sync to update web panel
            try:
                from bot.chat_manager import ChatManager
                chat_manager = ChatManager(settings.BOT_TOKEN)
                await chat_manager.sync_chats_to_database(db)
                print(f"DEBUG: Synced chats to database after new chat detection")
            except Exception as e:
                print(f"DEBUG: Error syncing chats: {e}")
            
    except Exception as e:
        logger.error(f"Error in handle_message_in_group: {e}")
    finally:
        db.close()

async def sync_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /syncmembers command for admins."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user is admin
        admin = get_admin_by_telegram_id(db, user.id)
        if not admin:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Get chat ID from command arguments or current chat
        chat_id = None
        if context.args:
            try:
                chat_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Неверный формат Chat ID. Используйте: /syncmembers <chat_id>")
                return
        else:
            # Use current chat if it's a group
            if update.effective_chat.type in ['group', 'supergroup']:
                chat_id = update.effective_chat.id
            else:
                await update.message.reply_text("❌ Укажите Chat ID: /syncmembers <chat_id>")
                return
        
        await update.message.reply_text(f"🔄 Синхронизирую участников чата {chat_id}...")
        
        # Sync chat members
        chat_manager = ChatManager(settings.BOT_TOKEN)
        results = await chat_manager.sync_chat_members(chat_id, db)
        
        message = f"✅ **Синхронизация участников завершена!**\n\n"
        message += f"📊 **Результаты для чата {chat_id}:**\n"
        message += f"• Всего участников: {results['total_members']}\n"
        message += f"• Авторизованных: {results['authorized_members']}\n"
        message += f"• Удалено неавторизованных: {results['removed_unauthorized']}\n"
        message += f"• Ошибок: {results['errors']}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in sync_members_command: {e}")
        await update.message.reply_text("❌ Ошибка при синхронизации участников.")
    finally:
        db.close()

async def refresh_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /refreshmembers command for admins - force refresh chat members."""
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user is admin
        admin = get_admin_by_telegram_id(db, user.id)
        if not admin:
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Get chat ID from command arguments or current chat
        chat_id = None
        if context.args:
            try:
                chat_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Неверный формат Chat ID. Используйте: /refreshmembers <chat_id>")
                return
        else:
            # Use current chat if it's a group
            if update.effective_chat.type in ['group', 'supergroup']:
                chat_id = update.effective_chat.id
            else:
                await update.message.reply_text("❌ Укажите Chat ID: /refreshmembers <chat_id>")
                return
        
        await update.message.reply_text(f"🔄 Принудительно обновляю список участников чата {chat_id}...")
        
        # Force refresh chat members
        chat_manager = ChatManager(settings.BOT_TOKEN)
        
        # Get all members from recent activity
        members = await chat_manager.get_chat_members_from_telegram(chat_id)
        
        message = f"📋 **Найдено участников в чате {chat_id}:**\n\n"
        
        for i, member in enumerate(members, 1):
            message += f"{i}. **{member.get('first_name', 'Unknown')}**\n"
            message += f"   ID: `{member['id']}`\n"
            if member.get('username'):
                message += f"   Username: @{member['username']}\n"
            message += f"   Admin: {'Да' if member.get('is_admin') else 'Нет'}\n"
            message += f"   Bot: {'Да' if member.get('is_bot') else 'Нет'}\n\n"
        
        # Split message if too long
        if len(message) > 4000:
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in refresh_members_command: {e}")
        await update.message.reply_text("❌ Ошибка при обновлении списка участников.")
    finally:
        db.close()

