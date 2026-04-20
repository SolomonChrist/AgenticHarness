@echo off
setlocal
cd /d "%~dp0"
py service_manager.py start all
echo.
echo Service startup requested. Check Runner\runner.log, TelegramBot\telegram.log, and Visualizer\visualizer.log if something did not come up.
echo.
echo Important: starting services does not daemonize Chief_of_Staff.
echo If you have not already handed Chief_of_Staff to Runner, run configure_chief_daemon.bat next.
echo You can verify production readiness with: py production_check.py
pause
