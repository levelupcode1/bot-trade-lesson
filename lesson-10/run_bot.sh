#!/bin/bash

# 텔레그램 봇 실행 스크립트

echo "🚀 텔레그램 자동매매 알림 봇 시작 중..."

# 환경 변수 확인
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다."
    echo "환경 변수를 설정하고 다시 실행하세요:"
    echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'"
    exit 1
fi

# Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치
echo "📥 의존성을 설치합니다..."
pip install -r requirements.txt

# 로그 디렉토리 생성
mkdir -p logs

# 봇 실행
echo "🤖 봇을 시작합니다..."
python main.py
