@echo off
title 🦂 Agentic Harness — Installer
echo.
echo  🦂 AGENTIC HARNESS — INSTALLER
echo  ================================
echo.

REM Try py launcher first (most reliable on Windows)
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Found: py launcher
    py install.py
    goto done
)

REM Try python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Found: python
    python install.py
    goto done
)

REM Try python3
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Found: python3
    python3 install.py
    goto done
)

REM Nothing found
echo  ERROR: Python not found.
echo.
echo  Please install Python 3.9+ from:
echo  https://www.python.org/downloads/
echo.
echo  IMPORTANT: During install, check:
echo  [x] Add Python to PATH
echo.
echo  Then re-run this file.
echo.

:done
pause
