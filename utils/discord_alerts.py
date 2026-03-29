"""
discord_alerts.py — NemoClaw Discord Integration v2
Supports:
  - Webhook: one-way push notifications (alerts, summaries, status)
  - Bot:     two-way interaction (folder selection, approvals, PR merge, deletions)

Requirements:
  pip install requests python-dotenv discord.py

.env keys needed:
  DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
  DISCORD_BOT_TOKEN=your_bot_token_here
  DISCORD_CHANNEL_ID=your_channel_id_here   (numeric ID of #general)
"""

import os
import asyncio
import threading
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK")
BOT_TOKEN    = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID   = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# Embed colors
COLOR_SUCCESS = 5814783   # teal
COLOR_ERROR   = 16711680  # red
COLOR_WARNING = 16776960  # yellow
COLOR_INFO    = 8311585   # purple
COLOR_PENDING = 10197915  # grey
COLOR_PR      = 3447003   # blue (PR notifications)

# Emoji numbers for folder selection (up to 10)
EMOJI_NUMBERS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — WEBHOOK (one-way push, no bot token needed)
# ══════════════════════════════════════════════════════════════════════════════

def _send_webhook(title: str, description: str, color: int = COLOR_SUCCESS,
                  fields: list = None):
    """Base webhook sender. fields = [{"name": str, "value": str, "inline": bool}]"""
    embed = {"title": title, "description": description, "color": color}
    if fields:
        embed["fields"] = fields
    resp = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    resp.raise_for_status()


# ── New project notifications ──────────────────────────────────────────────────

def send_github_alert(repo_name: str, repo_url: str, description: str = None,
                      prefix_type: str = None):
    """Called after a successful gh repo push for new project folders."""
    prefix_legend = {
        "()" : "🔄 Force-pushed to existing repo",
        "."  : "📄 Report + code + data",
        ";"  : "🖨️ Code with printed outputs",
        "`"  : "📑 Two PDFs + code + data",
    }
    push_type = prefix_legend.get(prefix_type, "🚀 New repo created")
    _send_webhook(
        "✅ NemoClaw Project Pushed",
        f"**{repo_name}**\n\n🔗 {repo_url}\n\n"
        f"📝 {description or 'No description'}\n\n{push_type}",
        color=COLOR_SUCCESS
    )


def send_error_alert(error_msg: str):
    """Called on any unhandled error."""
    _send_webhook("❌ Error", error_msg, color=COLOR_ERROR)


# ── Phase 0 — PDF audit ────────────────────────────────────────────────────────

def send_pdf_audit_report(folder_results: list):
    """
    Phase 0 step 0.1. Sends classification table after NemoClaw scans all PDFs.
    folder_results: list of dicts — folder, filename, classification, confidence, reason
    LOW confidence rows are flagged for your manual review.
    """
    low = [r for r in folder_results if r.get("confidence","").upper() == "LOW"]
    rows = []
    for r in folder_results:
        flag = " ⚠️" if r.get("confidence","").upper() == "LOW" else ""
        rows.append(
            f"`{r['folder']}`  →  {r['filename']}  [{r['classification']}]{flag}"
        )
    description = "\n".join(rows) or "No PDFs found."
    summary = (
        f"\n\n**{len(low)} item(s) flagged — check these manually before confirming.**"
        if low else "\n\n✅ All classifications high-confidence."
    )
    _send_webhook(
        "📋 PDF Audit Report — Phase 0",
        description + summary,
        color=COLOR_WARNING if low else COLOR_SUCCESS
    )


def send_discard_ready_notice(folders_with_discards: list):
    """
    Phase 0 step 0.3. Lists DISCARD_ files pending deletion.
    folders_with_discards: list of {"folder": str, "files": [str]}
    You reply with !confirm-delete or !cancel-delete via the bot.
    """
    lines = []
    for item in folders_with_discards:
        lines.append(f"**{item['folder']}**")
        for f in item["files"]:
            lines.append(f"  🗑️ `{f}`")
    description = "\n".join(lines) or "No DISCARD_ files found."
    _send_webhook(
        "🗑️ DISCARD Files Ready for Deletion",
        description + "\n\n**Reply:**\n"
        "`!confirm-delete` — delete all listed files from ds-projects-source\n"
        "`!cancel-delete` — abort, I'll handle manually",
        color=COLOR_WARNING
    )


# ── Phase 2 — Session start ────────────────────────────────────────────────────

def send_session_status(remaining_folders: list):
    """
    Start of every session. Sends numbered list of remaining folders.
    You reply with !process or emoji reactions to select which to run.
    """
    lines = []
    for i, folder in enumerate(remaining_folders[:10]):
        emoji = EMOJI_NUMBERS[i] if i < len(EMOJI_NUMBERS) else f"{i+1}."
        lines.append(f"{emoji} `{folder}`")
    if len(remaining_folders) > 10:
        lines.append(
            f"\n_...and {len(remaining_folders) - 10} more. "
            f"Type `!process 11 12` etc. for those._"
        )
    _send_webhook(
        "📂 NemoClaw Session Started — Remaining Folders",
        "\n".join(lines) + "\n\n"
        "**Select folders to process this session:**\n"
        "• React with emoji numbers (up to 10 shown)\n"
        "• Or type: `!process 1 3 5` for specific folders\n"
        "• Or type: `!process all` to run everything",
        color=COLOR_INFO
    )


# ── Phase 3 — Per-folder summary ──────────────────────────────────────────────

def send_folder_summary(folder_name: str, repo_name: str, renamed_files: list,
                         metrics_source: str, warnings: list = None):
    """
    After NemoClaw finishes processing one folder (Step 5 output).
    Asks for your approval before the folder is pushed to GitHub.
    renamed_files: list of (old_name, new_name) tuples
    """
    renames = "\n".join([f"  `{old}` → `{new}`" for old, new in renamed_files]) \
              or "  No renames."
    warn_text = (
        "\n\n⚠️ **Needs manual review:**\n" +
        "\n".join(f"• {w}" for w in warnings)
    ) if warnings else ""
    _send_webhook(
        f"📦 Ready to Push: `{repo_name}`",
        f"**Source folder:** `{folder_name}`\n\n"
        f"**File renames:**\n{renames}\n\n"
        f"**Metrics found in:** {metrics_source}"
        f"{warn_text}\n\n"
        "**Reply:** `!proceed` to push to GitHub  |  `!skip` to skip",
        color=COLOR_PENDING
    )


# ── Phase 5 — Session complete ────────────────────────────────────────────────

def send_session_complete(pushed: list, skipped: list, errors: list):
    """
    End-of-session summary.
    pushed:  list of (repo_name, url) tuples
    skipped: list of repo_name strings
    errors:  list of (repo_name, error_message) tuples
    """
    pushed_text  = "\n".join([f"✅ [{r}]({u})" for r, u in pushed]) or "None"
    skipped_text = "\n".join([f"⏭️ {r}" for r in skipped])          or "None"
    error_text   = "\n".join([f"❌ {r}: {e}" for r, e in errors])   or "None"
    _send_webhook(
        "🏁 Session Complete",
        f"**Pushed ({len(pushed)}):**\n{pushed_text}\n\n"
        f"**Skipped ({len(skipped)}):**\n{skipped_text}\n\n"
        f"**Errors ({len(errors)}):**\n{error_text}",
        color=COLOR_SUCCESS if not errors else COLOR_WARNING
    )


# ── Legacy session — inference + PR ───────────────────────────────────────────

def send_old_repo_inference(repo_name: str, inferred_title: str,
                             inferred_description: str, file_list: list):
    """
    Legacy session: NemoClaw cloned the repo, inferred what the project is.
    Asks you to approve before it creates the restructure branch + PR.
    """
    files = "\n".join([f"  • `{f}`" for f in file_list]) or "  No files found."
    _send_webhook(
        f"🔍 Inferred: `{repo_name}`",
        f"**Inferred title:** {inferred_title}\n\n"
        f"**Inferred description:** {inferred_description}\n\n"
        f"**Files found:**\n{files}\n\n"
        "**Reply:**\n"
        f"`!approve {repo_name}` — create `restructure` branch + PR\n"
        f"`!skip {repo_name}` — skip this repo",
        color=COLOR_INFO
    )


def send_pr_ready(repo_name: str, new_repo_name: str, pr_url: str,
                  branch: str = "restructure", changes_summary: str = ""):
    """
    Called after NemoClaw pushes the restructure branch and opens a PR.
    The PR contains: renamed files, README.md, requirements.txt, .gitignore.
    Repo rename happens ONLY after you merge and send !rename-repo.
    This keeps main branch and original repo name safe until you're satisfied.
    """
    _send_webhook(
        f"🔀 PR Ready — `{repo_name}`",
        f"**Branch:** `{branch}` → `main`\n\n"
        f"**Pull Request:** {pr_url}\n\n"
        f"**Changes on this branch:**\n"
        f"{changes_summary or '• File renames to snake_case\n• README.md added\n• requirements.txt added\n• .gitignore added'}\n\n"
        "**Your steps:**\n"
        "1️⃣ Open the PR link above and review the changes\n"
        "2️⃣ Merge the PR on GitHub when satisfied\n"
        f"3️⃣ Then reply here: `!rename-repo {repo_name} {new_repo_name}`\n"
        "   -> This triggers the GitHub repo rename",
        color=COLOR_PR
    )


def send_repo_renamed(old_name: str, new_name: str, new_url: str):
    """Confirmation after gh repo rename completes."""
    _send_webhook(
        "✏️ Repo Renamed",
        f"`{old_name}` → **`{new_name}`**\n\n🔗 {new_url}",
        color=COLOR_SUCCESS
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — BOT (two-way, requires DISCORD_BOT_TOKEN + DISCORD_CHANNEL_ID)
# ══════════════════════════════════════════════════════════════════════════════
# Full setup guide: see DISCORD_BOT_SETUP.md

try:
    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions       = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    # ── Shared state ───────────────────────────────────────────────────────────
    _pending: dict = {}
    _response_event = threading.Event()

    def _wait(timeout: float = 300.0):
        _response_event.clear()
        got = _response_event.wait(timeout=timeout)
        return _pending.copy() if got else None

    def _set(rtype: str, value):
        _pending["type"]  = rtype
        _pending["value"] = value
        _response_event.set()


    # ── Bot events ─────────────────────────────────────────────────────────────

    @bot.event
    async def on_ready():
        print(f"[NemoClaw Bot] Online as {bot.user} | Channel: {CHANNEL_ID}")

    @bot.event
    async def on_reaction_add(reaction, user):
        if user.bot or reaction.message.channel.id != CHANNEL_ID:
            return
        emoji = str(reaction.emoji)
        if emoji in EMOJI_NUMBERS:
            _set("folder_reaction", EMOJI_NUMBERS.index(emoji) + 1)


    # ── Commands ───────────────────────────────────────────────────────────────

    @bot.command(name="process")
    async def cmd_process(ctx, *args):
        """!process 1 3 5  OR  !process all"""
        if ctx.channel.id != CHANNEL_ID:
            return
        if args and args[0].lower() == "all":
            _set("folder_selection", "all")
            await ctx.message.add_reaction("✅")
        else:
            try:
                _set("folder_selection", [int(a) for a in args])
                await ctx.message.add_reaction("✅")
            except ValueError:
                await ctx.send("❌ Usage: `!process 1 3 5` or `!process all`")

    @bot.command(name="proceed")
    async def cmd_proceed(ctx):
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("approval", "proceed")
        await ctx.message.add_reaction("✅")

    @bot.command(name="skip")
    async def cmd_skip(ctx, *, repo_name: str = ""):
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("approval", f"skip:{repo_name}".rstrip(":"))
        await ctx.message.add_reaction("⏭️")

    @bot.command(name="approve")
    async def cmd_approve(ctx, *, repo_name: str = ""):
        """Legacy session: approve inferred identity, triggers branch + PR creation."""
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("legacy_approval", f"approve:{repo_name}")
        await ctx.message.add_reaction("✅")

    @bot.command(name="rename-repo")
    async def cmd_rename_repo(ctx, old_name: str = "", new_name: str = ""):
        """
        !rename-repo SCMA-A2 supply-chain-dea-analysis
        Send this AFTER you've merged the PR on GitHub.
        NemoClaw will then run: gh repo rename [new_name] --repo Adarsh1313/[old_name]
        """
        if ctx.channel.id != CHANNEL_ID:
            return
        if not old_name or not new_name:
            await ctx.send(
                "❌ Usage: `!rename-repo old-name new-name`\n"
                "Example: `!rename-repo SCMA-A2 supply-chain-dea-analysis`\n"
                "⚠️ Only send this AFTER merging the PR on GitHub."
            )
            return
        _set("repo_rename", {"old": old_name, "new": new_name})
        await ctx.message.add_reaction("✏️")
        await ctx.send(f"⏳ Renaming `{old_name}` → `{new_name}` on GitHub...")

    @bot.command(name="confirm-delete")
    async def cmd_confirm_delete(ctx):
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("delete_confirmation", "confirm")
        await ctx.message.add_reaction("🗑️")

    @bot.command(name="cancel-delete")
    async def cmd_cancel_delete(ctx):
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("delete_confirmation", "cancel")
        await ctx.message.add_reaction("🚫")

    @bot.command(name="status")
    async def cmd_status(ctx):
        """!status — NemoClaw reads project_list.md and posts progress."""
        if ctx.channel.id != CHANNEL_ID:
            return
        _set("status_request", True)
        await ctx.message.add_reaction("📊")

    @bot.command(name="help-nemoclaw")
    async def cmd_help(ctx):
        if ctx.channel.id != CHANNEL_ID:
            return
        await ctx.send(
            "**NemoClaw Bot — All Commands**\n\n"
            "**Session control:**\n"
            "`!process 1 3 5` or `!process all` — select folders to process\n"
            "React with 1️⃣–🔟 to select folders from the list\n"
            "`!proceed` — approve current folder, push to GitHub\n"
            "`!skip` — skip current folder\n"
            "`!status` — show project_list.md progress\n\n"
            "**Legacy session (old SCMA repos):**\n"
            "`!approve [repo]` — approve inferred identity, create branch + PR\n"
            "`!skip [repo]` — skip this repo\n"
            "`!rename-repo [old] [new]` — rename repo AFTER merging PR on GitHub\n\n"
            "**Phase 0 (PDF cleanup):**\n"
            "`!confirm-delete` — delete all DISCARD_ files\n"
            "`!cancel-delete` — abort deletion\n"
        )


    # ── Public helpers ─────────────────────────────────────────────────────────

    def start_bot_background():
        """Run bot in background thread (alternative: use discord_bot_runner.py)."""
        def _run():
            asyncio.run(bot.start(BOT_TOKEN))
        threading.Thread(target=_run, daemon=True).start()

    def wait_for_folder_selection(timeout: float = 600.0):
        resp = _wait(timeout)
        if resp is None: return None
        if resp["type"] == "folder_selection": return resp["value"]
        if resp["type"] == "folder_reaction":  return [resp["value"]]
        return None

    def wait_for_approval(timeout: float = 3600.0):
        resp = _wait(timeout)
        return resp.get("value") if resp else None

    def wait_for_delete_confirmation(timeout: float = 600.0):
        resp = _wait(timeout)
        return resp.get("value") if resp else None

    def wait_for_legacy_approval(timeout: float = 3600.0):
        resp = _wait(timeout)
        return resp.get("value") if resp else None

    def wait_for_repo_rename(timeout: float = 3600.0):
        """Returns {"old": str, "new": str} after !rename-repo command."""
        resp = _wait(timeout)
        return resp["value"] if resp and resp["type"] == "repo_rename" else None

    def wait_for_status_request(timeout: float = 0.1):
        resp = _wait(timeout)
        return resp is not None and resp.get("type") == "status_request"

    BOT_AVAILABLE = True


except ImportError:
    BOT_AVAILABLE = False

    def start_bot_background():
        print("[discord_alerts] discord.py not installed — run: pip install discord.py")

    def wait_for_folder_selection(timeout=600.0):    return None
    def wait_for_approval(timeout=3600.0):           return None
    def wait_for_delete_confirmation(timeout=600.0): return None
    def wait_for_legacy_approval(timeout=3600.0):    return None
    def wait_for_repo_rename(timeout=3600.0):        return None
    def wait_for_status_request(timeout=0.1):        return False
