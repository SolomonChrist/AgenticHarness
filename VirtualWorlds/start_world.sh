#!/bin/bash
# 🦂 Agentic Harness — World Server Launcher (Mac/Linux)
# Starts the world server for all 4 rendering modes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " 🌍 AGENTIC HARNESS — World Server"
echo " ─────────────────────────────────────────────────"
echo ""

# Check .env
if [ ! -f ".env" ]; then
    echo " ❌ .env not found. Run: python3 install.py"
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
    echo " ❌ Python not found. Install from https://python.org/downloads"
    exit 1
fi

# Check Flask
$PYTHON_CMD -c "import flask" 2>/dev/null || {
    echo " 📦 Installing dependencies..."
    $PYTHON_CMD -m pip install flask flask-cors python-dotenv --quiet
}

# Get local IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "YOUR_LOCAL_IP")

echo " ✅ Starting world server..."
echo ""
echo " Open in browser:"
echo "   2D Map:    http://localhost:8888/"
echo "   3D World:  http://localhost:8888/world3d.html"
echo "   VR:        http://localhost:8888/worldvr.html"
echo "   Unity/C#:  http://localhost:8888/api/world/unity"
echo ""
if [ "$LOCAL_IP" != "YOUR_LOCAL_IP" ]; then
    echo " LAN access (phone / VR headset):"
    echo "   http://$LOCAL_IP:8888/"
    echo ""
fi
echo " Press Ctrl+C to stop."
echo ""

$PYTHON_CMD world_server.py
