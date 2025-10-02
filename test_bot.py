#!/usr/bin/env python3
"""
Simple test script to check if bot can start without errors.
"""

import asyncio
import logging
from config import settings
from bot.main import application

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test if bot can initialize without errors."""
    try:
        print("Testing bot initialization...")
        
        # Test if application can be created
        print("✓ Application created successfully")
        
        # Test if we can get bot info
        bot = application.bot
        bot_info = await bot.get_me()
        print(f"✓ Bot info: {bot_info.first_name} (@{bot_info.username})")
        
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        logger.error(f"Bot test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    exit(0 if result else 1)
