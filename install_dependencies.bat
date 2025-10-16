@echo off
REM uv 기반 의존성 설치 배치 파일
REM Windows에서 더블클릭으로 실행하여 uv와 필요한 패키지들을 설치

echo Installing Dependencies with uv...
echo uv로 의존성을 설치합니다...
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
    pause
    exit /b 1
)

echo Python found. Checking for uv...
echo Python을 찾았습니다. uv를 확인 중...

REM uv가 설치되어 있는지 확인
where uv >nul 2>&1
if %errorlevel% == 0 (
    echo uv found! Installing dependencies...
    echo uv를 찾았습니다! 의존성을 설치합니다...
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
        pause
        exit /b 1
    )

    echo uv installed successfully! Please restart this batch file.
    echo uv 설치 완료! 이 배치 파일을 다시 실행해주세요.
    pause
    exit /b 0
)

REM uv로 의존성 설치
echo Installing project dependencies with uv...
echo uv로 프로젝트 의존성을 설치합니다...
uv sync

if %errorlevel% == 0 (
    echo.
    echo Installation completed successfully!
    echo 설치가 성공적으로 완료되었습니다!
    echo.
    echo You can now run the applications:
    echo 이제 애플리케이션을 실행할 수 있습니다:
    echo - videoConverter.bat (비디오 변환기)
    echo - videoToImage.bat (비디오를 이미지로 변환)
    echo.
    echo Don't forget to install FFmpeg from https://ffmpeg.org
    echo FFmpeg도 https://ffmpeg.org 에서 설치하는 것을 잊지 마세요
) else (
    echo Failed to install dependencies with uv!
    echo uv로 의존성 설치에 실패했습니다!
)

echo.
pause