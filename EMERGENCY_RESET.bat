@echo off
echo ===================================================
echo     AGENTIC HARNESS EMERGENCY RESET SCRIPT
echo ===================================================
echo.
echo WARNING: This will immediately hard-terminate EVERY BACKGROUND PYTHON PROCESS currently running on this computer.
echo This includes the Dashboard Server, MasterBot, Worker Bots, and any other Python script.
echo.
pause

echo.
echo Killing python.exe via taskkill...
taskkill /F /IM python.exe 2>NUL

echo.
echo Sweeping remaining python locks via PowerShell...
powershell -Command "Get-Process py, python, python3 -ErrorAction SilentlyContinue | Stop-Process -Force"

echo.
echo System Reset Complete. All python locks have been purged.
echo You may now safely delete workspace folders or launch INSTALL_HARNESS.bat to begin again.
echo.
pause
