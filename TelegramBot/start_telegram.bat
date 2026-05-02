@echo off
setlocal
cd /d "%~dp0\.."
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py service_manager.py start telegram
) else (
  python service_manager.py start telegram
)
