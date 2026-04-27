@echo off
setlocal
cd /d "%~dp0"
py service_manager.py start all
echo.
echo Service startup requested. ChiefChat and Runner are core services.
echo Telegram starts only after TelegramBot\.env.telegram has real credentials.
echo.
echo Opening Visualizer at http://127.0.0.1:8787/dashboard.html
start "" "http://127.0.0.1:8787/dashboard.html"
echo.
echo Important: ChiefChat handles fast Telegram chat. Runner handles deeper scheduled role work.
echo If you have not already configured deeper Chief_of_Staff role work, run configure_chief_daemon.bat later.
echo You can verify production readiness with: py production_check.py
pause
