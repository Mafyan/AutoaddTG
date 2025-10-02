#!/usr/bin/env python3
"""
Auto-sync script for chat members.
This script runs separately from the main bot.
"""

import asyncio
import logging
import signal
import sys
from config import settings
from bot.chat_manager import ChatManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AutoSyncManager:
    def __init__(self):
        self.chat_manager = None
        self.running = False
        
    async def start(self):
        """Start auto-sync manager."""
        try:
            logger.info("Starting Auto-Sync Manager...")
            
            # Initialize chat manager
            self.chat_manager = ChatManager(settings.BOT_TOKEN)
            
            # Start auto sync
            await self.chat_manager.start_auto_sync()
            self.running = True
            
            logger.info("Auto-Sync Manager started successfully")
            
            # Keep running
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Auto-Sync Manager error: {e}")
            raise
    
    def stop(self):
        """Stop auto-sync manager."""
        logger.info("Stopping Auto-Sync Manager...")
        self.running = False
        if self.chat_manager:
            asyncio.create_task(self.chat_manager.stop_auto_sync())

async def main():
    """Main function."""
    manager = AutoSyncManager()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        manager.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        manager.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
