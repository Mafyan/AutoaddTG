#!/usr/bin/env python3
"""Script to run the Telegram bot."""
import sys
from bot.main import main

if __name__ == "__main__":
    try:
        print("="*60)
        print("Starting User Control Bot...")
        print("="*60)
        main()
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)

