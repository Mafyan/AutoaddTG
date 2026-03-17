"""Main Telegram bot module."""
import logging
import time
from telegram import Update
from telegram.error import TimedOut, NetworkError
from telegram.ext import (
    CommandHandler,
    ChatMemberHandler,
    MessageHandler,
    TypeHandler,
    filters,
    ContextTypes,
)
from config import settings
from bot.telegram_client import get_application
from bot.handlers import (
    start_command,
    help_command,
    status_command,
    mychats_command,
    handle_contact,
    handle_text_message,
    error_handler,
    list_chats_command,
    sync_chats_command,
    handle_my_chat_member,
    handle_message_in_group,
    sync_members_command,
    refresh_members_command
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def log_update_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verbose runtime logging for incoming Telegram updates."""
    if update.message:
        message = update.message
        text = (message.text or message.caption or "").replace("\n", " ").strip()
        if len(text) > 120:
            text = text[:117] + "..."
        logger.info(
            "Update message: update_id=%s chat_id=%s chat_type=%s user_id=%s text=%r",
            update.update_id,
            getattr(message.chat, "id", None),
            getattr(message.chat, "type", None),
            getattr(message.from_user, "id", None),
            text,
        )
    elif update.my_chat_member:
        member = update.my_chat_member
        logger.info(
            "Update my_chat_member: update_id=%s chat_id=%s old_status=%s new_status=%s",
            update.update_id,
            getattr(member.chat, "id", None),
            getattr(member.old_chat_member, "status", None),
            getattr(member.new_chat_member, "status", None),
        )
    elif update.callback_query:
        query = update.callback_query
        logger.info(
            "Update callback_query: update_id=%s chat_id=%s user_id=%s data=%r",
            update.update_id,
            getattr(getattr(query.message, "chat", None), "id", None),
            getattr(query.from_user, "id", None),
            query.data,
        )
    else:
        logger.info("Update received: update_id=%s type=other", update.update_id)

def build_application():
    """Create and configure the Telegram application."""
    application = get_application(settings.BOT_TOKEN)

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("mychats", mychats_command))
    application.add_handler(CommandHandler("listchats", list_chats_command))
    application.add_handler(CommandHandler("syncchats", sync_chats_command))
    application.add_handler(CommandHandler("syncmembers", sync_members_command))
    application.add_handler(CommandHandler("refreshmembers", refresh_members_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    # Universal text handler - handles all states (AWAITING_PHONE, AWAITING_NAME, AWAITING_POSITION)
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Track when the bot is added to/removed from chats via the proper update type.
    application.add_handler(
        ChatMemberHandler(handle_my_chat_member, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER)
    )
    
    # Add error handler
    application.add_error_handler(error_handler)

    if settings.TELEGRAM_VERBOSE_LOGGING:
        application.add_handler(TypeHandler(Update, log_update_activity), group=-1)
        logger.info("Verbose Telegram update logging is enabled")

    return application


def main():
    """Start the bot."""
    # Validate token
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in environment variables!")
        return

    # Start the bot. Network timeouts can happen with proxies/ISP issues.
    # Keep the process alive and retry polling instead of exiting and letting Supervisor thrash.
    backoff_s = 2
    drop_pending_updates = True
    while True:
        application = build_application()
        try:
            logger.info("Starting bot...")
            application.run_polling(
                allowed_updates=["message", "my_chat_member"],
                close_loop=False,
                drop_pending_updates=drop_pending_updates,
                timeout=settings.TELEGRAM_GET_UPDATES_TIMEOUT,
            )
            backoff_s = 2
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram network error during polling: %s. Retrying in %ss", e, backoff_s)
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 60)
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.warning("Polling hit closed event loop. Retrying in %ss", backoff_s)
                time.sleep(backoff_s)
                backoff_s = min(backoff_s * 2, 60)
                continue
            logger.exception("Fatal runtime error in bot polling loop")
            raise
        except Exception:
            logger.exception("Fatal error in bot polling loop")
            raise
        finally:
            # Only drop stale updates on the first process start.
            drop_pending_updates = False

if __name__ == "__main__":
    main()

