@echo off
:: 🦂 Agentic Harness — World Server Launcher (Windows)
:: Starts the world server for all 4 rendering modes
:: 2D: http://localhost:8888/
:: 3D: http://localhost:8888/world3d.html
:: VR: http://localhost:8888/worldvr.html
:: C#: http://localhost:8888/api/world/unity

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  🌍 AGENTIC HARNESS — World Server
echo  ─────────────────────────────────────────────────
echo.

:: Check .env exists
if not exist ".env" (
    echo  ❌ .env not found. Run install.bat first.
    pause
    exit /b 1
)

:: Check Python
set "PYTHON_CMD="
for %%P in (python py python3) do (
    if "!PYTHON_CMD!"=="" (
        %%P --version >nul 2>&1 && set "PYTHON_CMD=%%P"
    )
)
if "!PYTHON_CMD!"=="" (
    echo  ❌ Python not found. Download from https://python.org/downloads
    pause
    exit /b 1
)

:: Check Flask
!PYTHON_CMD! -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo  📦 Installing dependencies...
    !PYTHON_CMD! -m pip install flask flask-cors python-dotenv --quiet
)

:: Get local IP for LAN access
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /R "IPv4"') do (
    set "LOCAL_IP=%%i"
    set "LOCAL_IP=!LOCAL_IP: =!"
    goto :found_ip
)
:found_ip

echo  ✅ Starting world server...
echo.
echo  Open in browser:
echo    2D Map:     http://localhost:8888/
echo    3D World:   http://localhost:8888/world3d.html
echo    VR:         http://localhost:8888/worldvr.html
echo    Unity/C#:   http://localhost:8888/api/world/unity
echo.
if defined LOCAL_IP (
    echo  LAN access (phone / VR headset):
    echo    http://!LOCAL_IP!:8888/
    echo    http://!LOCAL_IP!:8888/world3d.html
    echo.
)
echo  Press Ctrl+C to stop.
echo.

!PYTHON_CMD! world_server.py

if %errorlevel% neq 0 (
    echo.
    echo  ❌ Server stopped with error. Check terminal output above.
    pause
)
