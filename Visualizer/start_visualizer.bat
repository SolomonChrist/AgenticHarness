@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py "%~dp0visualizer_server.py"
) else (
  python "%~dp0visualizer_server.py"
)
