@echo off
REM PET - Personal Encryption Tool
REM Windows Registry Setup Batch Wrapper
REM Right-click this file and select "Run as administrator"

setlocal enabledelayedexpansion

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Error: This script requires administrative privileges.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Get the script directory
cd /d "%~dp0"

REM Check for uninstall flag
if "%1"=="--uninstall" (
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -File "setup_registry.ps1" -Uninstall
    if %errorlevel% equ 0 (
        echo.
        echo Press any key to exit...
    ) else (
        echo.
        echo Setup failed. Press any key to exit...
    )
    pause
    exit /b %errorlevel%
)

REM Installation (default)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "setup_registry.ps1"

if %errorlevel% equ 0 (
    echo.
    echo Press any key to exit...
) else (
    echo.
    echo Setup failed. Press any key to exit...
)

pause
exit /b %errorlevel%