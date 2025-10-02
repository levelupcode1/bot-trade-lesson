@echo off
REM UTF-8 코드페이지 설정
chcp 65001 >nul 2>&1

REM 텔레그램 봇 실행 스크립트 (Windows)

echo 🚀 텔레그램 자동매매 알림 봇 시작 중...

REM 환경 변수 설정 (실제 토큰으로 교체하세요)
if "%TELEGRAM_BOT_TOKEN%"=="your_actual_bot_token_here" (
set TELEGRAM_BOT_TOKEN=
set PYTHONIOENCODING=utf-8


REM 환경 변수 확인
if "%TELEGRAM_BOT_TOKEN%"=="your_actual_bot_token_here" (
    echo ❌ TELEGRAM_BOT_TOKEN을 실제 봇 토큰으로 교체해주세요.
    echo run_bot.bat 파일을 편집하여 토큰을 설정하세요.
    pause
    exit /b 1
)

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 봇 실행
echo 🤖 봇을 시작합니다...
python main.py

pause
