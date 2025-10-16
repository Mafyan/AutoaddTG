"""Chat management utilities for Telegram bot."""
import logging
import asyncio
from typing import List, Optional
from telegram import Bot, Update
from telegram.error import TelegramError, BadRequest
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.crud import (
    get_chats_by_role, add_chat_member, remove_chat_member,
    get_user_chats, fire_user, get_user_by_telegram_id, get_chats
)
from database.models import Chat, User

logger = logging.getLogger(__name__)

class ChatManager:
    """Manages bot's interaction with Telegram chats."""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self._sync_task = None
        self._running = False
    
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
    
    async def kick_user_from_chat(self, chat_id: int, user_telegram_id: int) -> bool:
        """
        Kick user from specific chat (ban and immediately unban).
        This removes the user but allows them to rejoin if they have a link.
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User's Telegram ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if bot is admin in the chat
            try:
                bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
                if bot_member.status not in ['administrator', 'creator']:
                    logger.warning(f"Bot is not admin in chat {chat_id}, cannot remove user {user_telegram_id}")
                    return False
            except TelegramError as e:
                logger.error(f"Failed to check bot status in chat {chat_id}: {e}")
                return False
            
            # Try to kick user from chat (ban then unban)
            try:
                await self.bot.ban_chat_member(chat_id, user_telegram_id)
                # ВАЖНО: сразу разбанить, чтобы пользователь мог вернуться позже
                await self.bot.unban_chat_member(chat_id, user_telegram_id)
                logger.info(f"Successfully kicked user {user_telegram_id} from chat {chat_id}")
                return True
            except TelegramError as e:
                logger.error(f"Failed to kick user {user_telegram_id} from chat {chat_id}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error kicking user {user_telegram_id} from chat {chat_id}: {e}")
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
                # Use kick_user_from_chat which properly unbans after kicking
                success = await self.kick_user_from_chat(chat_id, user_telegram_id)
                results[chat_id] = {
                    'success': success,
                    'error': None if success else 'Failed to remove user (bot may not be admin)'
                }
                
                # Also update database to mark user as left
                db = SessionLocal()
                try:
                    remove_chat_member(db, chat_id, user_telegram_id)
                finally:
                    db.close()
                    
            except Exception as e:
                results[chat_id] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Error removing user {user_telegram_id} from chat {chat_id}: {e}")
        
        return results
    
    async def sync_chat_members(self, chat_id: int, db: Session) -> dict:
        """
        Sync chat members with database - collect all members and remove unauthorized ones.
        
        Args:
            chat_id: Telegram chat ID
            db: Database session
            
        Returns:
            Dictionary with sync results
        """
        try:
            from database.crud import get_user_by_telegram_id, add_chat_member, remove_chat_member
            
            # Check if bot has admin rights in chat
            try:
                bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
                print(f"DEBUG: Bot status in chat {chat_id}: {bot_member.status}")
                if bot_member.status not in ['administrator', 'creator']:
                    print(f"DEBUG: Bot is not admin in chat {chat_id}, skipping...")
                    return {'error': 'Bot is not admin in chat'}
            except Exception as e:
                print(f"DEBUG: Could not check bot status in chat {chat_id}: {e}")
                return {'error': f'Could not access chat: {e}'}
            
            # Get all chat members from Telegram
            chat_members = await self.get_chat_members_from_telegram(chat_id)
            print(f"DEBUG: Found {len(chat_members)} members in chat {chat_id}")
            
            # Get authorized users from database
            authorized_users = db.query(User).filter(User.status == 'approved').all()
            authorized_telegram_ids = {user.telegram_id for user in authorized_users if user.telegram_id}
            print(f"DEBUG: Found {len(authorized_telegram_ids)} authorized users in database")
            
            results = {
                'total_members': len(chat_members),
                'authorized_members': 0,
                'removed_unauthorized': 0,
                'errors': 0
            }
            
            for member in chat_members:
                try:
                    user_telegram_id = member['id']
                    
                    # Skip bots
                    if member.get('is_bot', False):
                        print(f"DEBUG: Skipping bot {user_telegram_id}")
                        continue
                    
                    # Check if user is authorized
                    if user_telegram_id in authorized_telegram_ids:
                        # User is authorized - add/update in database
                        add_chat_member(db, chat_id, user_telegram_id, 
                                      member.get('username'), member.get('first_name'), member.get('last_name'))
                        results['authorized_members'] += 1
                        print(f"DEBUG: Authorized user {user_telegram_id} ({member.get('first_name')}) in chat {chat_id}")
                    else:
                        # User is not authorized - remove from chat
                        print(f"DEBUG: User {user_telegram_id} ({member.get('first_name')}) is NOT authorized, attempting to remove...")
                        try:
                            # First try to ban the user
                            await self.bot.ban_chat_member(chat_id, user_telegram_id)
                            print(f"DEBUG: Successfully banned unauthorized user {user_telegram_id} from chat {chat_id}")
                            results['removed_unauthorized'] += 1
                        except Exception as e:
                            print(f"DEBUG: Could not ban user {user_telegram_id}: {e}")
                            # Try to kick instead
                            try:
                                await self.bot.kick_chat_member(chat_id, user_telegram_id)
                                print(f"DEBUG: Successfully kicked unauthorized user {user_telegram_id} from chat {chat_id}")
                                results['removed_unauthorized'] += 1
                            except Exception as e2:
                                print(f"DEBUG: Could not kick user {user_telegram_id}: {e2}")
                                results['errors'] += 1
                            
                except Exception as e:
                    print(f"DEBUG: Error processing member {member}: {e}")
                    results['errors'] += 1
            
            db.commit()
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync chat members: {e}")
            return {'error': str(e)}
    
    async def get_chat_members_from_telegram(self, chat_id: int) -> List[dict]:
        """
        Get all members from a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            List of member information dictionaries
        """
        try:
            members = []
            
            # Get chat administrators first
            try:
                administrators = await self.bot.get_chat_administrators(chat_id)
                for admin in administrators:
                    # Skip bots
                    if admin.user.is_bot:
                        continue
                        
                    member_info = {
                        'id': admin.user.id,
                        'username': admin.user.username,
                        'first_name': admin.user.first_name,
                        'last_name': admin.user.last_name,
                        'is_admin': True,
                        'is_bot': admin.user.is_bot
                    }
                    members.append(member_info)
                    print(f"DEBUG: Found admin {admin.user.id} ({admin.user.first_name})")
            except Exception as e:
                print(f"DEBUG: Could not get administrators: {e}")
            
            # Try to get all members using get_chat_member_count and iterate
            try:
                # Get chat member count
                member_count = await self.bot.get_chat_member_count(chat_id)
                print(f"DEBUG: Chat {chat_id} has {member_count} members")
                
                # For now, we'll use a different approach - get members from recent activity
                # This is a limitation of Telegram API - we can't get all members directly
                
            except Exception as e:
                print(f"DEBUG: Could not get member count: {e}")
            
            # Get members from recent messages (this is our main method)
            try:
                # Get more updates to find more members
                updates = await self.bot.get_updates(limit=500, timeout=30)
                print(f"DEBUG: Got {len(updates)} updates")
                
                for update in updates:
                    if (update.message and 
                        update.message.chat and 
                        update.message.chat.id == chat_id and 
                        update.message.from_user):
                        
                        user = update.message.from_user
                        
                        # Skip bots
                        if user.is_bot:
                            continue
                            
                        # Check if we already have this user
                        if not any(m['id'] == user.id for m in members):
                            member_info = {
                                'id': user.id,
                                'username': user.username,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'is_admin': False,
                                'is_bot': user.is_bot
                            }
                            members.append(member_info)
                            print(f"DEBUG: Found member {user.id} ({user.first_name}) from messages")
                    
                    # Also check for new chat members
                    if (update.message and 
                        update.message.chat and 
                        update.message.chat.id == chat_id and 
                        update.message.new_chat_members):
                        
                        for user in update.message.new_chat_members:
                            if user.is_bot:
                                continue
                                
                            if not any(m['id'] == user.id for m in members):
                                member_info = {
                                    'id': user.id,
                                    'username': user.username,
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'is_admin': False,
                                    'is_bot': user.is_bot
                                }
                                members.append(member_info)
                                print(f"DEBUG: Found new member {user.id} ({user.first_name}) from new_chat_members")
                    
                    # Check for left chat members
                    if (update.message and 
                        update.message.chat and 
                        update.message.chat.id == chat_id and 
                        update.message.left_chat_member):
                        
                        user = update.message.left_chat_member
                        if user.is_bot:
                            continue
                            
                        # Remove from our list if present
                        members = [m for m in members if m['id'] != user.id]
                        print(f"DEBUG: Removed left member {user.id} ({user.first_name})")
                        
            except Exception as e:
                print(f"DEBUG: Could not get members from messages: {e}")
            
            print(f"DEBUG: Total members found: {len(members)}")
            return members
            
        except Exception as e:
            logger.error(f"Failed to get chat members from Telegram: {e}")
            return []
    
    async def start_auto_sync(self):
        """Start automatic member synchronization every hour."""
        if self._running:
            return
        
        self._running = True
        self._sync_task = asyncio.create_task(self._auto_sync_loop())
        logger.info("Started automatic member synchronization")
    
    async def stop_auto_sync(self):
        """Stop automatic member synchronization."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped automatic member synchronization")
    
    async def _auto_sync_loop(self):
        """Background task for automatic member synchronization."""
        while self._running:
            try:
                await self.sync_all_chat_members()
                # Wait 1 hour (3600 seconds)
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto sync loop: {e}")
                # Wait 5 minutes before retrying
                await asyncio.sleep(300)
    
    async def sync_all_chat_members(self):
        """Sync members for all chats in database."""
        db = SessionLocal()
        try:
            # Get all chats with Telegram IDs
            chats = get_chats(db)
            telegram_chats = [chat for chat in chats if chat.chat_id]
            
            logger.info(f"Starting auto-sync for {len(telegram_chats)} chats")
            
            total_results = {
                'total_members': 0,
                'authorized_members': 0,
                'removed_unauthorized': 0,
                'errors': 0
            }
            
            for chat in telegram_chats:
                try:
                    results = await self.sync_chat_members(chat.chat_id, db)
                    if 'error' not in results:
                        total_results['total_members'] += results['total_members']
                        total_results['authorized_members'] += results['authorized_members']
                        total_results['removed_unauthorized'] += results['removed_unauthorized']
                        total_results['errors'] += results['errors']
                except Exception as e:
                    logger.error(f"Error syncing chat {chat.chat_id}: {e}")
                    total_results['errors'] += 1
            
            logger.info(f"Auto-sync completed: {total_results}")
            
        except Exception as e:
            logger.error(f"Error in sync_all_chat_members: {e}")
        finally:
            db.close()
    
    async def add_user_to_chat(self, chat_id: int, user_telegram_id: int) -> bool:
        """
        Add user to specific chat.
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User's Telegram ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to add user to chat
            await self.bot.unban_chat_member(chat_id, user_telegram_id)
            logger.info(f"Successfully added user {user_telegram_id} to chat {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to add user {user_telegram_id} to chat {chat_id}: {e}")
            return False
    
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
            
            chats = []
            chat_ids = set()
            
            # Method 1: Get updates to find chats
            print("DEBUG: Searching chats via updates...")
            updates = await self.bot.get_updates(limit=100)
            
            for update in updates:
                if update.message and update.message.chat:
                    chat = update.message.chat
                    if chat.type in ['group', 'supergroup'] and chat.id not in chat_ids:
                        chat_info = await self._get_chat_info(chat.id, chat.title, chat.type, chat.username)
                        if chat_info:
                            chats.append(chat_info)
                            chat_ids.add(chat.id)
            
            print(f"DEBUG: Found {len(chats)} chats via updates")
            
            # Method 2: Try to get more updates with different offsets
            print("DEBUG: Searching chats via multiple update batches...")
            for offset in range(100, 1000, 100):
                try:
                    more_updates = await self.bot.get_updates(limit=100, offset=offset)
                    if not more_updates:
                        break
                        
                    for update in more_updates:
                        if update.message and update.message.chat:
                            chat = update.message.chat
                            if chat.type in ['group', 'supergroup'] and chat.id not in chat_ids:
                                chat_info = await self._get_chat_info(chat.id, chat.title, chat.type, chat.username)
                                if chat_info:
                                    chats.append(chat_info)
                                    chat_ids.add(chat.id)
                except Exception as e:
                    print(f"DEBUG: Error getting updates at offset {offset}: {e}")
                    break
            
            print(f"DEBUG: Total found {len(chats)} chats after multiple batches")
            
            # Method 3: Try to get chat by known chat IDs from database
            print("DEBUG: Checking known chat IDs from database...")
            try:
                from database.database import SessionLocal
                db = SessionLocal()
                from database.crud import get_chats
                known_chats = get_chats(db)
                db.close()
                
                for known_chat in known_chats:
                    if known_chat.chat_id and known_chat.chat_id not in chat_ids:
                        try:
                            # Try to get chat info
                            chat_info = await self.bot.get_chat(known_chat.chat_id)
                            if chat_info.type in ['group', 'supergroup']:
                                chat_info_dict = await self._get_chat_info(
                                    chat_info.id, 
                                    chat_info.title, 
                                    chat_info.type, 
                                    getattr(chat_info, 'username', None)
                                )
                                if chat_info_dict:
                                    chats.append(chat_info_dict)
                                    chat_ids.add(chat_info.id)
                                    print(f"DEBUG: Found known chat: {chat_info.title}")
                        except Exception as e:
                            print(f"DEBUG: Could not access known chat {known_chat.chat_id}: {e}")
            except Exception as e:
                print(f"DEBUG: Error checking known chats: {e}")
            
            print(f"DEBUG: Final result: {len(chats)} chats found")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get bot chats: {e}")
            return []
    
    async def _get_chat_info(self, chat_id: int, title: str, chat_type: str, username: str = None) -> dict:
        """
        Get detailed chat information.
        
        Args:
            chat_id: Chat ID
            title: Chat title
            chat_type: Chat type
            username: Chat username
            
        Returns:
            Chat information dictionary or None if error
        """
        try:
            chat_info = {
                'id': chat_id,
                'title': title,
                'type': chat_type,
                'username': username,
                'invite_link': None
            }
            
            # Try to get invite link
            try:
                invite_link = await self.bot.export_chat_invite_link(chat_id)
                chat_info['invite_link'] = invite_link
            except Exception as e:
                print(f"DEBUG: Could not get invite link for chat {chat_id}: {e}")
            
            return chat_info
            
        except Exception as e:
            print(f"DEBUG: Error getting chat info for {chat_id}: {e}")
            return None
    
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
