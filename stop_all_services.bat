@echo off
setlocal
cd /d "%~dp0"
py service_manager.py stop all
echo.
echo Stop request complete.
pause
