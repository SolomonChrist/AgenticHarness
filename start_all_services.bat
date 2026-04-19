@echo off
setlocal
cd /d "%~dp0"
py service_manager.py start all
echo.
echo Service startup requested. Check Runner\runner.log, TelegramBot\telegram.log, and Visualizer\visualizer.log if something did not come up.
pause
