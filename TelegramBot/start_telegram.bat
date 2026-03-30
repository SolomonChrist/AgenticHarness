@echo off
:: 🦂 Agentic Harness — Telegram EA Bot Launcher (Windows)
:: Double-click this file to start your Personal Executive Assistant

setlocal enabledelayedexpansion
set "ScriptDir=%~dp0"
cd /d "%ScriptDir%"

echo.
echo  🦂 AGENTIC HARNESS — Telegram Executive Assistant
echo  ─────────────────────────────────────────────────
echo.

:: Check .env.telegram exists
if not exist ".env.telegram" (
    echo  ❌ .env.telegram not found.
    echo.
    echo  Setup steps:
    echo    1. Copy .env.telegram.template to .env.telegram
    echo    2. Fill in your TELEGRAM_BOT_TOKEN
    echo    3. Fill in your TELEGRAM_ALLOWED_USER_IDS
    echo    4. Fill in your HARNESS_PROJECTS_PATH
    echo    5. Double-click this file again
    echo.
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
    echo  ❌ Python not found.
    echo  Download from https://python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  ✅ Python found: !PYTHON_CMD!

:: Install dependencies if needed
!PYTHON_CMD! -c "import requests, dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo  📦 Installing dependencies...
    !PYTHON_CMD! -m pip install requests python-dotenv --quiet
    if %errorlevel% neq 0 (
        echo  ❌ Failed to install dependencies.
        pause
        exit /b 1
    )
    echo  ✅ Dependencies installed
)

:: Auto-restart loop
set /a RESTARTS=0
set /a MAX_RESTARTS=50

:restart_loop
if %RESTARTS% geq %MAX_RESTARTS% (
    echo  ❌ Too many restarts (%MAX_RESTARTS%). Giving up.
    pause
    exit /b 1
)

set /a RESTARTS+=1
echo.
echo  [%date% %time%] Starting bot (attempt %RESTARTS%)...
echo  Press Ctrl+C to stop.
echo.

!PYTHON_CMD! telegram_bot.py

set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 0 (
    echo.
    echo  ✅ Bot stopped cleanly.
    pause
    exit /b 0
)

echo  ⚠️  Bot crashed (exit code: %EXIT_CODE%). Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto restart_loop
