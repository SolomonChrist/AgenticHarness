@echo off
setlocal
cd /d "%~dp0"
py service_manager.py start all
echo.
echo Service startup requested. Runner and Visualizer are core services.
echo Telegram starts only after TelegramBot\.env.telegram has real credentials.
echo.
echo Opening Visualizer at http://127.0.0.1:8787/dashboard.html
start "" "http://127.0.0.1:8787/dashboard.html"
echo.
echo Important: starting services does not daemonize Chief_of_Staff.
echo If you have not already handed Chief_of_Staff to Runner, run configure_chief_daemon.bat next.
echo You can verify production readiness with: py production_check.py
pause
