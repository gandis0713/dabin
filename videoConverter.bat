@echo off
chcp 65001 >nul 2>&1
REM Video Converter launcher

echo Starting Video Converter Application...
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
echo Launching Video Converter...
uv run python video_converter/video_converter.py

REM Keep window open if error occurred
if %errorlevel% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    pause >nul
)