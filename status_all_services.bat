@echo off
setlocal
cd /d "%~dp0"
py service_manager.py status all
echo.
pause
