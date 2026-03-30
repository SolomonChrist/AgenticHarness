#!/bin/bash
# 🦂 Agentic Harness — Telegram EA Bot Launcher (Mac/Linux)
# Auto-restarts on crash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " 📱 AGENTIC HARNESS — Telegram Executive Assistant"
echo " ─────────────────────────────────────────────────"
echo ""

# Check .env.telegram
if [ ! -f ".env.telegram" ]; then
    echo " ❌ .env.telegram not found."
    echo ""
    echo " Setup steps:"
    echo "   1. cp .env.telegram.template .env.telegram"
    echo "   2. Fill in TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   3. Fill in TELEGRAM_ALLOWED_USER_IDS (from @userinfobot)"
    echo "   4. Fill in HARNESS_PROJECTS_PATH"
    echo "   5. Run this script again"
    exit 1
fi

# Check Python
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done
if [ -z "$PYTHON_CMD" ]; then
    echo " ❌ Python not found."
    exit 1
fi

# Check dependencies
$PYTHON_CMD -c "import requests, dotenv" 2>/dev/null || {
    echo " 📦 Installing dependencies..."
    $PYTHON_CMD -m pip install requests python-dotenv --quiet
}

# Auto-restart loop
RESTARTS=0
MAX_RESTARTS=50

while [ $RESTARTS -lt $MAX_RESTARTS ]; do
    RESTARTS=$((RESTARTS + 1))
    echo ""
    echo " [$(date '+%Y-%m-%d %H:%M:%S')] Starting bot (attempt $RESTARTS)..."
    echo " Press Ctrl+C to stop."
    echo ""

    $PYTHON_CMD telegram_bot.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo " ✅ Bot stopped cleanly."
        exit 0
    fi

    echo " ⚠️  Bot crashed (exit $EXIT_CODE). Restarting in 5s..."
    sleep 5
done

echo " ❌ Max restarts ($MAX_RESTARTS) reached. Giving up."
exit 1
