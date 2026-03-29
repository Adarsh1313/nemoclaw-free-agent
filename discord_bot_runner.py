"""
discord_bot_runner.py
Keeps the NemoClaw Discord bot alive during a session.
Start this once via startup.sh — you never need to touch it again.
Logs to bot.log in the same directory.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    print("[ERROR] DISCORD_BOT_TOKEN not set in .env — bot cannot start.")
    sys.exit(1)

try:
    from discord_alerts import bot
except ImportError as e:
    print(f"[ERROR] Could not import discord_alerts: {e}")
    print("Make sure discord.py is installed: pip install discord.py")
    sys.exit(1)

print("[NemoClaw Bot] Starting...")

if __name__ == "__main__":
    asyncio.run(bot.start(token))
