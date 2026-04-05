#!/bin/bash
# chat_logs.sh — NemoClaw chat log manager
# Manages TUI session logs stored in /workspaces/nemoclaw-free-agent/logs/
#
# Usage:
#   bash chat_logs.sh              — show today's log
#   bash chat_logs.sh list         — list all log files
#   bash chat_logs.sh show [date]  — show log for specific date (e.g. 2026-03-30)
#   bash chat_logs.sh search [term] — search all logs for a term
#   bash chat_logs.sh clear        — delete all logs (asks confirmation)
#   bash chat_logs.sh backup       — copy logs to ds-projects-source (private)

LOG_DIR="/workspaces/nemoclaw-free-agent/logs"
BACKUP_DIR="/workspaces/ds-projects-source/chat_logs"
TODAY=$(date +%Y-%m-%d)

# Ensure log dir exists
mkdir -p "$LOG_DIR"

case "${1:-today}" in

  today)
    LOG_FILE="$LOG_DIR/${TODAY}.log"
    if [ -f "$LOG_FILE" ]; then
      echo "═══════════════════════════════════════"
      echo " Chat Log — $TODAY"
      echo "═══════════════════════════════════════"
      cat "$LOG_FILE"
    else
      echo "No log file found for today ($TODAY)."
      echo "Run a TUI session with logging first:"
      echo "  script -q -a $LOG_FILE -c 'openclaw tui --session s1'"
    fi
    ;;

  list)
    echo "═══════════════════════════════════════"
    echo " All Chat Logs"
    echo "═══════════════════════════════════════"
    if ls "$LOG_DIR"/*.log 2>/dev/null | head -1 > /dev/null; then
      ls -lh "$LOG_DIR"/*.log | awk '{print $5, $9}' | sed "s|$LOG_DIR/||"
    else
      echo "No log files found in $LOG_DIR"
    fi
    ;;

  show)
    DATE="${2:-$TODAY}"
    LOG_FILE="$LOG_DIR/${DATE}.log"
    if [ -f "$LOG_FILE" ]; then
      echo "═══════════════════════════════════════"
      echo " Chat Log — $DATE"
      echo "═══════════════════════════════════════"
      cat "$LOG_FILE"
    else
      echo "No log file found for $DATE"
      echo "Available logs:"
      ls "$LOG_DIR"/*.log 2>/dev/null | sed "s|$LOG_DIR/||g" | sed 's/.log//'
    fi
    ;;

  search)
    TERM="${2}"
    if [ -z "$TERM" ]; then
      echo "Usage: bash chat_logs.sh search [term]"
      exit 1
    fi
    echo "═══════════════════════════════════════"
    echo " Searching logs for: $TERM"
    echo "═══════════════════════════════════════"
    grep -rn --color=always "$TERM" "$LOG_DIR"/*.log 2>/dev/null || echo "No matches found."
    ;;

  clear)
    echo "This will delete ALL log files in $LOG_DIR"
    read -p "Are you sure? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
      rm -f "$LOG_DIR"/*.log
      echo "All logs deleted."
    else
      echo "Aborted."
    fi
    ;;

  backup)
    echo "→ Backing up logs to ds-projects-source (private repo)..."
    mkdir -p "$BACKUP_DIR"
    # Add chat_logs to ds-projects-source .gitignore if not already there
    # (keeps logs private even within the private repo — optional)
    cp "$LOG_DIR"/*.log "$BACKUP_DIR/" 2>/dev/null || echo "No logs to backup."
    cd /workspaces/ds-projects-source
    git add chat_logs/
    git commit -m "Backup chat logs $(date +%Y-%m-%d)" --allow-empty
    git push origin main
    echo "  ✓ Logs backed up to ds-projects-source/chat_logs/"
    ;;

  *)
    echo "Usage:"
    echo "  bash chat_logs.sh              — show today's log"
    echo "  bash chat_logs.sh list         — list all log files"
    echo "  bash chat_logs.sh show [date]  — show specific date"
    echo "  bash chat_logs.sh search [term] — search all logs"
    echo "  bash chat_logs.sh clear        — delete all logs"
    echo "  bash chat_logs.sh backup       — backup to ds-projects-source"
    ;;

esac
