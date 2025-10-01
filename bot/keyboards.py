"""Telegram bot keyboards."""
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_phone_keyboard():
    """Get keyboard for requesting phone number."""
    keyboard = [
        [KeyboardButton("📱 Поделиться номером телефона", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_remove_keyboard():
    """Get keyboard removal markup."""
    return ReplyKeyboardRemove()

