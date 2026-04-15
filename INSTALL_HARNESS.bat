@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     Agentic Harness Installer
echo ===================================================
echo.
echo Checking for Python...

:: Check for python or py
set PY_CMD=
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=py
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PY_CMD=python
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Check version 3.10+
%PY_CMD% -c "import sys; v=sys.version_info; sys.exit(0 if v.major >= 3 and v.minor >= 10 else 1)"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.10+ is required. Found:
    %PY_CMD% --version
    pause
    exit /b 1
)

echo Python version valid.
echo.

:: Install dependencies
echo Installing required dependencies (openai, flask, psutil, python-telegram-bot)...
%PY_CMD% -m pip install openai flask psutil python-telegram-bot --quiet
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo Dependencies installed successfully.
echo.

:: Target directory wrapper
:ASK_TARGET
set DEFAULT_TARGET=..\AgenticHarnessWork
set /p TARGET_DIR="Enter target workspace directory [default: %DEFAULT_TARGET%]: "
if "%TARGET_DIR%"=="" set TARGET_DIR=%DEFAULT_TARGET%

echo.
set SETUP_FLAGS=

if exist "%TARGET_DIR%\System\SYSTEM_STATUS.md" (
    echo [WARNING] An existing Agentic Harness workspace was detected at:
    echo %TARGET_DIR%
    echo.
    echo Please select an action:
    echo 1. Open Workspace [Safe Mode] - Do not modify existing files
    echo 2. Repair Workspace - Generate missing system files only
    echo 3. Overwrite Workspace [DANGER] - Resets system files to defaults
    echo 4. Choose a different path
    echo 5. Exit
    set /p EXIST_CHOICE="Your choice [1]: "
    if "!EXIST_CHOICE!"=="" set EXIST_CHOICE=1
    
    if "!EXIST_CHOICE!"=="1" (
        echo Opening existing workspace securely...
        set SETUP_FLAGS=--repair
    ) else if "!EXIST_CHOICE!"=="2" (
        echo Repairing missing files securely...
        set SETUP_FLAGS=--repair
    ) else if "!EXIST_CHOICE!"=="3" (
        echo OVERWRITING workspace...
        set SETUP_FLAGS=--overwrite
    ) else if "!EXIST_CHOICE!"=="4" (
        echo.
        goto ASK_TARGET
    ) else (
        echo Exiting...
        exit /b 0
    )
)

echo.
echo Executing Agentic Harness Setup...
%PY_CMD% setup.py --target "%TARGET_DIR%" %SETUP_FLAGS%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAILURE] Setup failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Workspace generation complete!
echo.
echo Would you like to start the Onboarding Wizard?
echo 1. Start Dashboard Server (Recommended)
echo 2. Start CLI Onboarding
echo 3. Exit
set /p START_CHOICE="Your choice [1]: "
if "%START_CHOICE%"=="" set START_CHOICE=1

echo.
if "%START_CHOICE%"=="1" (
    echo [Dashboard Server] Starting in background...
    echo.
    echo Your Agentic Harness workspace has been set up at:
    echo -^> %TARGET_DIR%
    echo.
    echo You can now close this window or leave it open as a reference.
    
    start "Agentic Harness Dashboard" %PY_CMD% core\dashboard_server.py --workspace "%TARGET_DIR%"
    
    :: Give the server a moment to bind to the port
    timeout /t 2 /nobreak >nul
    
    echo Launching http://localhost:5000 in your browser...
    start http://localhost:5000
) else if "%START_CHOICE%"=="2" (
    echo Launching CLI Onboarding...
    %PY_CMD% core\onboarding_cli.py --workspace "%TARGET_DIR%"
) else (
    echo Setup complete. Exiting.
)

pause
