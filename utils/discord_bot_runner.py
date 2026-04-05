"""
discord_bot_runner.py
Runs on the Codespace HOST (outside sandbox).
Two jobs:
  1. Keeps the Discord bot alive to receive commands from #general
  2. Writes every user reply to /workspaces/nemoclaw-free-agent/discord_reply.txt
     so NemoClaw inside the sandbox can read it with:
       cat /workspaces/nemoclaw-free-agent/discord_reply.txt

Reply file format — one line per interaction, newest appended at bottom:
  SELECTION:1,3,5          <- from !process 1 3 5
  SELECTION:all            <- from !process all
  APPROVAL:proceed         <- from !proceed
  APPROVAL:skip            <- from !skip
  APPROVAL:skip:repo-name  <- from !skip repo-name
  LEGACY:approve:repo      <- from !approve repo
  DELETE:confirm           <- from !confirm-delete
  DELETE:cancel            <- from !cancel-delete
  RENAME:old-name:new-name <- from !rename-repo old new
  STATUS:requested         <- from !status

NemoClaw reads the LAST line of the file (most recent reply) with:
  tail -1 /workspaces/nemoclaw-free-agent/discord_reply.txt

After reading, NemoClaw deletes the file with:
  rm /workspaces/nemoclaw-free-agent/discord_reply.txt

Requirements:
  pip install discord.py python-dotenv

.env keys needed:
  DISCORD_BOT_TOKEN=your_bot_token
  DISCORD_CHANNEL_ID=your_channel_id
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN  = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
REPLY_FILE = "/workspaces/nemoclaw-free-agent/discord_reply.txt"

EMOJI_NUMBERS = ["1\ufe0f\u20e3","2\ufe0f\u20e3","3\ufe0f\u20e3","4\ufe0f\u20e3",
                 "5\ufe0f\u20e3","6\ufe0f\u20e3","7\ufe0f\u20e3","8\ufe0f\u20e3",
                 "9\ufe0f\u20e3","\U0001f51f"]

if not BOT_TOKEN:
    print("[ERROR] DISCORD_BOT_TOKEN not set in .env")
    sys.exit(1)

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("[ERROR] discord.py not installed — run: pip install discord.py")
    sys.exit(1)


def write_reply(line: str):
    """Append a reply line to the relay file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = line + "  # " + timestamp + "\n"
    with open(REPLY_FILE, "a") as f:
        f.write(entry)
    print("[Relay] Written: " + line)


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("[NemoClaw Bot] Online as " + str(bot.user))
    print("[NemoClaw Bot] Relay file: " + REPLY_FILE)


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.channel.id != CHANNEL_ID:
        return
    emoji = str(reaction.emoji)
    if emoji in EMOJI_NUMBERS:
        idx = EMOJI_NUMBERS.index(emoji) + 1
        write_reply("SELECTION:" + str(idx))
        await reaction.message.add_reaction("\u2705")


@bot.command(name="process")
async def cmd_process(ctx, *args):
    if ctx.channel.id != CHANNEL_ID:
        return
    if not args:
        await ctx.send("\u274c Usage: `!process 1 3 5` or `!process all`")
        return
    if args[0].lower() == "all":
        write_reply("SELECTION:all")
    else:
        try:
            nums = [int(a) for a in args]
            write_reply("SELECTION:" + ",".join(str(n) for n in nums))
        except ValueError:
            await ctx.send("\u274c Usage: `!process 1 3 5` or `!process all`")
            return
    await ctx.message.add_reaction("\u2705")


@bot.command(name="proceed")
async def cmd_proceed(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return
    write_reply("APPROVAL:proceed")
    await ctx.message.add_reaction("\u2705")


@bot.command(name="skip")
async def cmd_skip(ctx, *, repo_name: str = ""):
    if ctx.channel.id != CHANNEL_ID:
        return
    if repo_name:
        write_reply("APPROVAL:skip:" + repo_name)
    else:
        write_reply("APPROVAL:skip")
    await ctx.message.add_reaction("\u23ed\ufe0f")


@bot.command(name="approve")
async def cmd_approve(ctx, *, repo_name: str = ""):
    if ctx.channel.id != CHANNEL_ID:
        return
    write_reply("LEGACY:approve:" + repo_name)
    await ctx.message.add_reaction("\u2705")


@bot.command(name="rename-repo")
async def cmd_rename_repo(ctx, old_name: str = "", new_name: str = ""):
    if ctx.channel.id != CHANNEL_ID:
        return
    if not old_name or not new_name:
        await ctx.send("\u274c Usage: `!rename-repo old-name new-name`")
        return
    write_reply("RENAME:" + old_name + ":" + new_name)
    await ctx.message.add_reaction("\u270f\ufe0f")
    await ctx.send("\u23f3 Renaming `" + old_name + "` \u2192 `" + new_name + "`...")


@bot.command(name="confirm-delete")
async def cmd_confirm_delete(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return
    write_reply("DELETE:confirm")
    await ctx.message.add_reaction("\U0001f5d1\ufe0f")


@bot.command(name="cancel-delete")
async def cmd_cancel_delete(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return
    write_reply("DELETE:cancel")
    await ctx.message.add_reaction("\U0001f6ab")


@bot.command(name="status")
async def cmd_status(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return
    write_reply("STATUS:requested")
    await ctx.message.add_reaction("\U0001f4ca")


@bot.command(name="help-nemoclaw")
async def cmd_help(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return
    await ctx.send(
        "**NemoClaw Bot \u2014 Commands**\n\n"
        "**Session control:**\n"
        "`!process 1 3 5` or `!process all` \u2014 select folders\n"
        "React 1\ufe0f\u20e3\u20139\ufe0f\u20e3 to select folder by number\n"
        "`!proceed` \u2014 approve current folder, push to GitHub\n"
        "`!skip` \u2014 skip current folder\n"
        "`!status` \u2014 show processing progress\n\n"
        "**Legacy session (old SCMA repos):**\n"
        "`!approve [repo]` \u2014 approve inferred identity\n"
        "`!rename-repo [old] [new]` \u2014 rename repo after merging PR\n\n"
        "**Phase 0 (PDF cleanup):**\n"
        "`!confirm-delete` \u2014 delete all DISCARD_ files\n"
        "`!cancel-delete` \u2014 abort deletion\n\n"
        "\U0001f4be Replies written to `discord_reply.txt` for NemoClaw to read."
    )


if __name__ == "__main__":
    print("[NemoClaw Bot] Starting...")
    asyncio.run(bot.start(BOT_TOKEN))
