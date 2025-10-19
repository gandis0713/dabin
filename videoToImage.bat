@echo off
chcp 65001 >nul 2>&1

REM Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Video to Images launcher
echo Starting Video to Images Application...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo uv is not installed. Setting up uv and dependencies...
    echo.

    call setup.bat
    if %errorlevel% neq 0 (
        echo Setup failed!
        pause
        exit /b 1
    )
    echo.
)

REM Run application with uv
echo Launching Video to Images...
uv run python video_to_images/video_frame_extractor.py

REM Keep window open if error occurred
if %errorlevel% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    pause >nul
)