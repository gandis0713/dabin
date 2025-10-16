@echo off
REM Video to Images 실행 배치 파일 (uv 전용)
REM Windows에서 더블클릭으로 실행 가능

echo Starting Video to Images Application with uv...
echo uv로 비디오를 이미지로 변환하는 애플리케이션을 시작합니다...
echo.

REM 현재 디렉토리를 스크립트가 있는 위치로 변경
cd /d "%~dp0"

REM uv가 설치되어 있는지 확인
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv is not installed!
    echo 오류: uv가 설치되지 않았습니다!
    echo Please run install_dependencies.bat first
    echo 먼저 install_dependencies.bat을 실행해주세요
    pause
    exit /b 1
)

REM uv로 애플리케이션 실행
uv run python video_to_images/video_frame_extractor.py

REM 오류가 발생한 경우 창을 열어둠
if %errorlevel% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    echo 오류가 발생했습니다. 아무 키나 눌러 종료하세요...
    pause >nul
)