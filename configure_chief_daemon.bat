@echo off
setlocal
cd /d "%~dp0"

echo Configure Chief_of_Staff as a daemon-owned CLI role.
echo.
echo Provider examples: claude, opencode, goose, ollama
set /p PROVIDER="Provider: "
set /p MODEL="Model/profile (blank for CLI default): "

if "%PROVIDER%"=="" (
  echo Provider is required.
  pause
  exit /b 1
)

py configure_role_daemon.py --role Chief_of_Staff --provider %PROVIDER% --model "%MODEL%" --interval-minutes 2 --bootstrap-file AGENTIC_HARNESS_TINY.md --start-runner
echo.
echo If this completed successfully, you may close the original desktop Chief_of_Staff window.
pause
