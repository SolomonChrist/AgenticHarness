@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py "%~dp0runner_daemon.py"
) else (
  python "%~dp0runner_daemon.py"
)
