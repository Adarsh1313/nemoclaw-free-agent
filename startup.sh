#!/bin/bash
# startup.sh — NemoClaw session starter
# Run this once when you open your Codespace.
# Starts the Discord bot + relay server in the background,
# then connects to the NemoClaw sandbox.
#
# Usage: bash startup.sh

set -e

REPO_DIR="/workspaces/nemoclaw-free-agent"
BOT_LOG="$REPO_DIR/bot.log"
RELAY_LOG="$REPO_DIR/relay.log"

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

# ── Step 3: Start Discord relay server on host ─────────────────────────────
echo "→ Starting Discord relay server..."
pkill -f "discord_relay.py" 2>/dev/null || true
sleep 1
nohup python3 discord_relay.py > "$RELAY_LOG" 2>&1 &
RELAY_PID=$!
sleep 2

if kill -0 $RELAY_PID 2>/dev/null; then
    echo "  ✓ Discord relay running on port 9876 (PID $RELAY_PID)"
else
    echo "  ✗ Relay failed to start. Check relay.log:"
    tail -5 "$RELAY_LOG"
    exit 1
fi

# ── Step 4: Start Discord bot ──────────────────────────────────────────────
echo "→ Starting Discord bot..."
pkill -f "discord_bot_runner.py" 2>/dev/null || true
sleep 1
nohup python3 utils/discord_bot_runner.py > "$BOT_LOG" 2>&1 &
BOT_PID=$!
sleep 2

if kill -0 $BOT_PID 2>/dev/null; then
    echo "  ✓ Discord bot running (PID $BOT_PID) — check #general in Discord"
else
    echo "  ✗ Bot failed to start. Check bot.log:"
    tail -5 "$BOT_LOG"
    exit 1
fi

# ── Step 5: Upload sandbox files ───────────────────────────────────────────
echo "→ Uploading files to sandbox..."
openshell sandbox upload claw "$REPO_DIR/GITHUB_PROCESS.md" 2>/dev/null && echo "  ✓ GITHUB_PROCESS.md" || echo "  ✗ GITHUB_PROCESS.md"
openshell sandbox upload claw "$REPO_DIR/README_TEMPLATE.md" 2>/dev/null && echo "  ✓ README_TEMPLATE.md" || echo "  ✗ README_TEMPLATE.md"
openshell sandbox upload claw "$REPO_DIR/discord_sandbox_client.py" 2>/dev/null && echo "  ✓ discord_sandbox_client.py" || echo "  ✗ discord_sandbox_client.py"
openshell sandbox upload claw /workspaces/ds-projects-source/project_list.md 2>/dev/null && echo "  ✓ project_list.md" || echo "  ✗ project_list.md"

# ── Step 6: Connect to sandbox ────────────────────────────────────────────
echo ""
echo "→ Connecting to NemoClaw sandbox..."
echo ""
echo "  Once inside, run: openclaw tui"
echo "  Relay + bot are running — work entirely from Discord after pasting the prompt."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

nemoclaw claw connect
