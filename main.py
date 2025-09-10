#!/usr/bin/env python3
"""
FarnPathBot - Spiritual practice application.
Main entry point for the optimized bot.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bot.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped manually.")
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
