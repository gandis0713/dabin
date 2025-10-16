@echo off
REM uv 설치 및 의존성 설치 공통 배치 파일
REM 다른 배치 파일에서 호출하여 사용

echo Setting up uv and dependencies...
echo uv와 의존성을 설정합니다...
echo.

REM 현재 디렉토리를 스크립트가 있는 위치로 변경
cd /d "%~dp0"

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo 오류: Python이 설치되지 않았거나 PATH에 없습니다
    echo Please install Python from https://python.org
    echo https://python.org 에서 Python을 설치해주세요
    exit /b 1
)

REM uv가 설치되어 있는지 확인
where uv >nul 2>&1
if %errorlevel% == 0 (
    echo uv found! Checking dependencies...
    echo uv를 찾았습니다! 의존성을 확인합니다...
) else (
    echo uv not found. Installing uv...
    echo uv를 찾을 수 없습니다. uv를 설치합니다...

    REM PowerShell을 통해 uv 설치
    echo Downloading and installing uv via PowerShell...
    echo PowerShell을 통해 uv를 다운로드하고 설치합니다...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    if %errorlevel% neq 0 (
        echo Failed to install uv!
        echo uv 설치에 실패했습니다!
        exit /b 1
    )

    echo uv installed successfully!
    echo uv 설치가 완료되었습니다!
)

REM 의존성 설치 또는 업데이트
echo Installing/updating project dependencies...
echo 프로젝트 의존성을 설치/업데이트합니다...
uv sync

if %errorlevel% == 0 (
    echo Dependencies are ready!
    echo 의존성이 준비되었습니다!
    exit /b 0
) else (
    echo Failed to install dependencies!
    echo 의존성 설치에 실패했습니다!
    exit /b 1
)