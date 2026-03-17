"""Main Telegram bot module."""
import logging
import time
from telegram import Update
from telegram.error import TimedOut, NetworkError
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Add group message handler for auto-detecting chats
    application.add_handler(MessageHandler(filters.ChatType.GROUPS, handle_message_in_group))
    
    # Add my_chat_member handler for bot add/remove events
    # Use a custom filter for my_chat_member updates
    def my_chat_member_filter(update):
        return update.my_chat_member is not None
    
    application.add_handler(MessageHandler(my_chat_member_filter, handle_my_chat_member))
    
    # Add error handler
    application.add_error_handler(error_handler)

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
    while True:
        application = build_application()
        try:
            logger.info("Starting bot...")
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                close_loop=False,
            )
            backoff_s = 2
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram network error during polling: %s. Retrying in %ss", e, backoff_s)
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 60)
        except Exception:
            logger.exception("Fatal error in bot polling loop")
            raise

if __name__ == "__main__":
    main()

