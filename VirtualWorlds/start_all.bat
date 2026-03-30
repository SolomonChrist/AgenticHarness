@echo off
:: 🦂 Agentic Harness — Start Everything (Windows)
:: Launches World Server + Telegram EA Bot in separate windows

setlocal enabledelayedexpansion
echo.
echo  🦂 AGENTIC HARNESS — Starting All Services
echo  ─────────────────────────────────────────────────
echo.

:: ── WORLD SERVER ──
if exist "%~dp0VirtualWorlds\start_world.bat" (
    set "WORLD_DIR=%~dp0VirtualWorlds"
) else if exist "%~dp0world_server.py" (
    set "WORLD_DIR=%~dp0"
) else (
    echo  ⚠️  World server not found. Skipping.
    set "WORLD_DIR="
)

if defined WORLD_DIR (
    echo  🌍 Starting World Server...
    start "Harness World Server" cmd /k "cd /d "!WORLD_DIR!" && start_world.bat"
    timeout /t 2 /nobreak >nul
    echo  ✅ World server started in new window
)

:: ── TELEGRAM BOT ──
if exist "%~dp0TelegramBot\start_telegram.bat" (
    set "TG_DIR=%~dp0TelegramBot"
) else if exist "%~dp0telegram_bot.py" (
    set "TG_DIR=%~dp0"
) else (
    echo  ⚠️  Telegram bot not found. Skipping.
    set "TG_DIR="
)

if defined TG_DIR (
    echo  📱 Starting Telegram EA Bot...
    start "Harness Telegram Bot" cmd /k "cd /d "!TG_DIR!" && start_telegram.bat"
    timeout /t 2 /nobreak >nul
    echo  ✅ Telegram bot started in new window
)

echo.
echo  ─────────────────────────────────────────────────
echo  ✅ All services started.
echo.
echo  World Server:
echo    2D: http://localhost:8888/
echo    3D: http://localhost:8888/world3d.html
echo    VR: http://localhost:8888/worldvr.html
echo.
echo  Telegram: Check your bot on your phone
echo.
echo  Close the individual windows to stop each service.
echo  ─────────────────────────────────────────────────
echo.
pause
