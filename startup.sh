#!/bin/bash
# startup.sh — NemoClaw session starter
# Run once when you open your Codespace.
# Starts Discord bot + relay, uploads sandbox files, connects to sandbox.
# Chat logs saved automatically to logs/YYYY-MM-DD.log
#
# Usage: bash startup.sh

set -e

REPO_DIR="/workspaces/nemoclaw-free-agent"
BOT_LOG="$REPO_DIR/bot.log"
RELAY_FILE="$REPO_DIR/discord_reply.txt"
LOG_DIR="$REPO_DIR/logs"
TODAY=$(date +%Y-%m-%d)
SESSION_TIME=$(date +%H%M%S)
CHAT_LOG="$LOG_DIR/${TODAY}.log"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       NemoClaw Session Starting      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Step 1: Pull latest context files ──────────────────────────────────────
echo "→ Pulling latest context files..."
cd "$REPO_DIR"
git pull origin main --quiet
echo "  ✓ Context files up to date"

# ── Step 2: Sync ds-projects-source ────────────────────────────────────────
echo "→ Syncing ds-projects-source..."
cd /workspaces/ds-projects-source
git pull origin main --quiet
echo "  ✓ Project folders up to date"
cd "$REPO_DIR"

# ── Step 3: Set up logs directory ──────────────────────────────────────────
echo "→ Setting up chat logs..."
mkdir -p "$LOG_DIR"
# Ensure logs/ is in .gitignore
if ! grep -q "^logs/" "$REPO_DIR/.gitignore" 2>/dev/null; then
    echo "logs/" >> "$REPO_DIR/.gitignore"
    echo "discord_reply.txt" >> "$REPO_DIR/.gitignore"
fi
echo "  ✓ Logs directory ready: $LOG_DIR"
echo "  ✓ Today's log: $CHAT_LOG"

# ── Step 4: Clear stale reply file ─────────────────────────────────────────
echo "→ Clearing stale Discord reply file..."
rm -f "$RELAY_FILE"
echo "  ✓ discord_reply.txt cleared"

# ── Step 5: Start Discord bot ──────────────────────────────────────────────
echo "→ Starting Discord bot..."
pkill -f "discord_bot_runner.py" 2>/dev/null || true
sleep 1
nohup python3 utils/discord_bot_runner.py > "$BOT_LOG" 2>&1 &
BOT_PID=$!
sleep 2

if kill -0 $BOT_PID 2>/dev/null; then
    echo "  ✓ Discord bot running (PID $BOT_PID)"
    echo "  ✓ Replies will be written to: $RELAY_FILE"
else
    echo "  ✗ Bot failed to start. Check bot.log:"
    tail -5 "$BOT_LOG"
    exit 1
fi

# ── Step 6: Upload files to sandbox ────────────────────────────────────────
echo "→ Uploading files to sandbox..."
openshell sandbox upload claw "$REPO_DIR/GITHUB_PROCESS.md"       2>/dev/null && echo "  ✓ GITHUB_PROCESS.md"       || echo "  ✗ GITHUB_PROCESS.md (sandbox may not be ready yet)"
openshell sandbox upload claw "$REPO_DIR/README_TEMPLATE.md"      2>/dev/null && echo "  ✓ README_TEMPLATE.md"      || echo "  ✗ README_TEMPLATE.md"
openshell sandbox upload claw "$REPO_DIR/discord_sandbox_client.py" 2>/dev/null && echo "  ✓ discord_sandbox_client.py" || echo "  ✗ discord_sandbox_client.py"
openshell sandbox upload claw /workspaces/ds-projects-source/project_list.md 2>/dev/null && echo "  ✓ project_list.md" || echo "  ✗ project_list.md"

# ── Step 7: Connect to sandbox ────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Discord bot running — #general is live"
echo "  Reply file: $RELAY_FILE"
echo "  Chat log:   $CHAT_LOG"
echo ""
echo "  Inside sandbox:"
echo "    1. script -q -a $CHAT_LOG -c 'openclaw tui --session s$SESSION_TIME'"
echo "       (this opens TUI AND saves chat log automatically)"
echo ""
echo "    OR just open TUI without logging:"
echo "    2. openclaw tui --session s$SESSION_TIME"
echo ""
echo "  Keep Codespace alive in a second terminal:"
echo "    while true; do echo \"alive \$(date)\"; sleep 600; done"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

nemoclaw claw connect
