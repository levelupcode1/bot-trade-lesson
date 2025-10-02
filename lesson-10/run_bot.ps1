# 텔레그램 봇 실행 스크립트 (PowerShell)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 텔레그램 자동매매 알림 봇 시작 중..." -ForegroundColor Green

# 환경 변수 설정 (실제 토큰으로 교체하세요)
$env:TELEGRAM_BOT_TOKEN = "your_actual_bot_token_here"

# 환경 변수 확인
if ($env:TELEGRAM_BOT_TOKEN -eq "your_actual_bot_token_here") {
    Write-Host "❌ TELEGRAM_BOT_TOKEN을 실제 봇 토큰으로 교체해주세요." -ForegroundColor Red
    Write-Host "run_bot.ps1 파일을 편집하여 토큰을 설정하세요." -ForegroundColor Yellow
    Read-Host "아무 키나 누르세요..."
    exit 1
}

# 로그 디렉토리 생성
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# 봇 실행
Write-Host "🤖 봇을 시작합니다..." -ForegroundColor Cyan
python main.py

Read-Host "아무 키나 누르세요..."


