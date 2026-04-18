@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py telegram_bot.py
) else (
  python telegram_bot.py
)
