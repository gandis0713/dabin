@echo off
chcp 65001 >nul 2>&1
REM uv setup batch file
REM Called by other batch files

echo Setting up uv and dependencies...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    exit /b 1
)

REM Check uv installation
where uv >nul 2>&1
if %errorlevel% == 0 (
    echo uv found! Checking dependencies...
) else (
    echo uv not found. Installing uv...

    REM Install uv via PowerShell
    echo Downloading and installing uv via PowerShell...

    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"

    if %errorlevel% neq 0 (
        echo Failed to install uv! This might be due to:
        echo - Network connection issues
        echo - Windows security settings
        echo - Administrator privileges required
        echo.
        echo Please try running this batch file as Administrator
        echo.
        echo Or install uv manually from:
        echo https://docs.astral.sh/uv/getting-started/installation/
        exit /b 1
    )

    echo uv installed successfully!
    echo.
    echo Refreshing environment variables...

    REM Try to refresh PATH
    call refreshenv >nul 2>&1

    REM Check if uv is immediately available
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        echo uv was installed but not immediately available in PATH
        echo.
        echo Please restart this batch file or open a new command prompt
        echo.
        pause
        exit /b 0
    )
)

REM Install or update dependencies
echo Installing/updating project dependencies...
uv sync

if %errorlevel% == 0 (
    echo Dependencies are ready!
    exit /b 0
) else (
    echo Failed to install dependencies!
    exit /b 1
)