"""Chat management utilities for Telegram bot."""
import logging
from typing import List, Optional
from telegram import Bot, Update
from telegram.error import TelegramError, BadRequest
from database.database import SessionLocal
from database.crud import (
    get_chats_by_role, add_chat_member, remove_chat_member,
    get_user_chats, fire_user, get_user_by_telegram_id
)
from database.models import Chat

logger = logging.getLogger(__name__)

class ChatManager:
    """Manages bot's interaction with Telegram chats."""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
    
    async def join_chat_by_link(self, chat_link: str) -> Optional[dict]:
        """
        Join chat using invite link.
        
        Args:
            chat_link: Telegram invite link
            
        Returns:
            dict with chat info or None if failed
        """
        try:
            # Extract chat ID from link (this is a simplified approach)
            # In real implementation, you might need to handle different link formats
            if "t.me/joinchat/" in chat_link:
                # Handle invite links
                invite_hash = chat_link.split("/")[-1]
                # This would require special handling for invite links
                logger.warning("Invite links require special handling")
                return None
            elif "t.me/+" in chat_link:
                # Handle public group links
                username = chat_link.split("/")[-1]
                chat = await self.bot.get_chat(f"@{username}")
                return {
                    "id": chat.id,
                    "title": chat.title,
                    "type": chat.type,
                    "username": chat.username
                }
            else:
                logger.error(f"Unsupported chat link format: {chat_link}")
                return None
                
        except TelegramError as e:
            logger.error(f"Failed to join chat {chat_link}: {e}")
            return None
    
    async def add_user_to_chat(self, chat_id: int, user_telegram_id: int, 
                              username: str = None, first_name: str = None, 
                              last_name: str = None) -> bool:
        """
        Add user to chat and track in database.
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User's Telegram ID
            username: User's username
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to database first
            db = SessionLocal()
            try:
                add_chat_member(
                    db, chat_id, user_telegram_id, 
                    username, first_name, last_name
                )
            finally:
                db.close()
            
            # Try to add user to chat (this might fail if bot doesn't have permissions)
            try:
                await self.bot.unban_chat_member(chat_id, user_telegram_id)
                logger.info(f"Added user {user_telegram_id} to chat {chat_id}")
                return True
            except BadRequest as e:
                if "USER_NOT_PARTICIPANT" in str(e):
                    # User is not in chat, try to invite
                    try:
                        await self.bot.send_message(
                            chat_id=user_telegram_id,
                            text=f"Вы были добавлены в чат. Перейдите по ссылке для вступления."
                        )
                        logger.info(f"Sent invitation to user {user_telegram_id}")
                        return True
                    except TelegramError:
                        logger.error(f"Failed to send invitation to user {user_telegram_id}")
                        return False
                else:
                    logger.error(f"Failed to add user to chat: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error adding user to chat: {e}")
            return False
    
    async def remove_user_from_chat(self, chat_id: int, user_telegram_id: int) -> bool:
        """
        Remove user from chat (without banning).
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User's Telegram ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database
            db = SessionLocal()
            try:
                remove_chat_member(db, chat_id, user_telegram_id)
            finally:
                db.close()
            
            # Try to remove user from chat
            try:
                await self.bot.ban_chat_member(chat_id, user_telegram_id)
                # Immediately unban to avoid permanent ban
                await self.bot.unban_chat_member(chat_id, user_telegram_id)
                logger.info(f"Removed user {user_telegram_id} from chat {chat_id}")
                return True
            except TelegramError as e:
                logger.error(f"Failed to remove user from chat: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing user from chat: {e}")
            return False
    
    async def add_user_to_role_chats(self, user_telegram_id: int, role_id: int,
                                   username: str = None, first_name: str = None,
                                   last_name: str = None) -> List[dict]:
        """
        Add user to all chats assigned to a role.
        
        Args:
            user_telegram_id: User's Telegram ID
            role_id: Role ID
            username: User's username
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            List of results for each chat
        """
        db = SessionLocal()
        try:
            chats = get_chats_by_role(db, role_id)
            results = []
            
            for chat in chats:
                if chat.chat_id:  # Only process chats with known chat_id
                    success = await self.add_user_to_chat(
                        chat.chat_id, user_telegram_id,
                        username, first_name, last_name
                    )
                    results.append({
                        "chat_name": chat.chat_name,
                        "chat_id": chat.chat_id,
                        "success": success
                    })
                else:
                    results.append({
                        "chat_name": chat.chat_name,
                        "chat_id": None,
                        "success": False,
                        "error": "Chat ID not set"
                    })
            
            return results
            
        finally:
            db.close()
    
    async def remove_user_from_all_chats(self, user_telegram_id: int) -> List[dict]:
        """
        Remove user from all chats they are a member of.
        
        Args:
            user_telegram_id: User's Telegram ID
            
        Returns:
            List of results for each chat
        """
        db = SessionLocal()
        try:
            user_chats = get_user_chats(db, user_telegram_id)
            results = []
            
            for chat_member in user_chats:
                success = await self.remove_user_from_chat(
                    chat_member.chat_id, user_telegram_id
                )
                results.append({
                    "chat_id": chat_member.chat_id,
                    "success": success
                })
            
            return results
            
        finally:
            db.close()
    
    async def fire_user_and_remove_from_chats(self, user_id: int) -> dict:
        """
        Fire user and remove from all chats.
        
        Args:
            user_id: User ID in database
            
        Returns:
            dict with results
        """
        db = SessionLocal()
        try:
            user = get_user_by_telegram_id(db, user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Fire user
            fire_user(db, user.id)
            
            # Remove from all chats
            removal_results = await self.remove_user_from_all_chats(user.telegram_id)
            
            return {
                "success": True,
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "removal_results": removal_results
            }
            
        finally:
            db.close()
    
    async def get_chat_member_count(self, chat_id: int) -> int:
        """
        Get number of members in chat.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Number of members
        """
        try:
            chat = await self.bot.get_chat(chat_id)
            return chat.member_count if hasattr(chat, 'member_count') else 0
        except TelegramError as e:
            logger.error(f"Failed to get chat member count: {e}")
            return 0
    
    async def remove_user_from_chat(self, chat_id: int, user_telegram_id: int) -> bool:
        """
        Remove user from specific chat.
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User's Telegram ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to kick user from chat
            await self.bot.ban_chat_member(chat_id, user_telegram_id)
            logger.info(f"Successfully removed user {user_telegram_id} from chat {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to remove user {user_telegram_id} from chat {chat_id}: {e}")
            return False
    
    async def remove_user_from_all_chats(self, user_telegram_id: int, chat_ids: List[int]) -> dict:
        """
        Remove user from all specified chats.
        
        Args:
            user_telegram_id: User's Telegram ID
            chat_ids: List of chat IDs to remove user from
            
        Returns:
            Dictionary with results for each chat
        """
        results = {}
        
        for chat_id in chat_ids:
            try:
                success = await self.remove_user_from_chat(chat_id, user_telegram_id)
                results[chat_id] = {
                    'success': success,
                    'error': None if success else 'Failed to remove user'
                }
            except Exception as e:
                results[chat_id] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Error removing user {user_telegram_id} from chat {chat_id}: {e}")
        
        return results
    
    async def get_bot_chats(self) -> List[dict]:
        """
        Get all chats where bot is a member.
        
        Returns:
            List of chat information dictionaries
        """
        try:
            # Get bot information
            bot_info = await self.bot.get_me()
            print(f"Bot info: {bot_info.username}")
            
            # Get updates to find chats
            updates = await self.bot.get_updates(limit=100)
            chats = []
            
            for update in updates:
                if update.message and update.message.chat:
                    chat = update.message.chat
                    if chat.type in ['group', 'supergroup']:
                        chat_info = {
                            'id': chat.id,
                            'title': chat.title,
                            'type': chat.type,
                            'username': chat.username,
                            'invite_link': None
                        }
                        
                        # Try to get invite link
                        try:
                            invite_link = await self.bot.export_chat_invite_link(chat.id)
                            chat_info['invite_link'] = invite_link
                        except:
                            pass
                        
                        # Avoid duplicates
                        if not any(c['id'] == chat.id for c in chats):
                            chats.append(chat_info)
            
            print(f"Found {len(chats)} chats")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get bot chats: {e}")
            return []
    
    async def sync_chats_to_database(self, db: Session) -> dict:
        """
        Sync bot chats to database.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with sync results
        """
        try:
            from database.crud import create_chat, get_chat_by_chat_id, update_chat
            
            # Get all chats where bot is a member
            bot_chats = await self.get_bot_chats()
            
            results = {
                'total_found': len(bot_chats),
                'created': 0,
                'updated': 0,
                'errors': 0
            }
            
            for chat_data in bot_chats:
                try:
                    # Check if chat already exists
                    existing_chat = get_chat_by_chat_id(db, chat_data['id'])
                    
                    if existing_chat:
                        # Update existing chat
                        update_chat(db, existing_chat.id, 
                                  chat_name=chat_data['title'],
                                  chat_link=chat_data['invite_link'])
                        results['updated'] += 1
                    else:
                        # Create new chat
                        create_chat(db, 
                                  chat_name=chat_data['title'],
                                  chat_link=chat_data['invite_link'],
                                  chat_id=chat_data['id'],
                                  description=f"Auto-synced {chat_data['type']} chat")
                        results['created'] += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing chat {chat_data['id']}: {e}")
                    results['errors'] += 1
            
            db.commit()
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync chats to database: {e}")
            return {'error': str(e)}
