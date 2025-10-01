"""Utility functions for the bot."""
import re
from typing import Optional

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to standard format.
    
    Args:
        phone: Phone number string
        
    Returns:
        Normalized phone number
    """
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Add + if not present
    if not phone.startswith('+'):
        phone = '+' + phone
    
    return phone

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number string
        
    Returns:
        True if valid, False otherwise
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if length is reasonable (7-15 digits)
    return 7 <= len(digits) <= 15

def format_chat_links(chats: list) -> str:
    """
    Format chat links for sending to user.
    
    Args:
        chats: List of chat objects
        
    Returns:
        Formatted string with chat links
    """
    if not chats:
        return "Нет доступных чатов для вашей роли."
    
    message = "🔗 Ваши чаты:\n\n"
    for i, chat in enumerate(chats, 1):
        chat_link = chat.chat_link if chat.chat_link else "Ссылка не указана"
        message += f"{i}. {chat.chat_name}\n"
        if chat.description:
            message += f"   📝 {chat.description}\n"
        message += f"   🔗 {chat_link}\n\n"
    
    return message

