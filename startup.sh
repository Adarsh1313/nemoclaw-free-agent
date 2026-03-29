#!/bin/bash
# startup.sh — NemoClaw session starter
# Run this once when you open your Codespace.
# It starts the Discord bot in the background, then drops you into OpenClaw TUI.
#
# Usage: bash startup.sh
# Or make it executable once: chmod +x startup.sh
# Then just run: ./startup.sh

set -e

REPO_DIR="/workspaces/nemoclaw-free-agent"   # adjust if your setup repo has a different name
BOT_LOG="$REPO_DIR/bot.log"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       NemoClaw Session Starting      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Step 1: Pull latest context files from setup repo ──────────────────────
echo "→ Pulling latest context files..."
cd "$REPO_DIR"
git pull origin main --quiet
echo "  ✓ Context files up to date"

# ── Step 2: Pull latest project folders from ds-projects-source ────────────
echo "→ Syncing ds-projects-source..."
cd /workspaces/ds-projects-source
git pull origin main --quiet
echo "  ✓ Project folders up to date"

# ── Step 3: Start Discord bot in background ────────────────────────────────
echo "→ Starting Discord bot..."
cd "$REPO_DIR"

# Kill any existing bot process so we don't double-start
pkill -f "discord_bot_runner.py" 2>/dev/null || true
sleep 1

# Start bot in background, log output to bot.log
nohup python3 discord_bot_runner.py > "$BOT_LOG" 2>&1 &
BOT_PID=$!
sleep 2

# Verify it started
if kill -0 $BOT_PID 2>/dev/null; then
    echo "  ✓ Discord bot running (PID $BOT_PID) — check #general in Discord"
else
    echo "  ✗ Bot failed to start. Check bot.log:"
    tail -5 "$BOT_LOG"
    echo ""
    echo "  Fix the error above, then re-run: bash startup.sh"
    exit 1
fi

# ── Step 4: Connect to NemoClaw sandbox ────────────────────────────────────
echo ""
echo "→ Connecting to NemoClaw sandbox..."
echo ""
echo "  Once inside the sandbox, paste your session prompt."
echo "  The Discord bot is already running — you don't need another terminal."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

nemoclaw claw connect
