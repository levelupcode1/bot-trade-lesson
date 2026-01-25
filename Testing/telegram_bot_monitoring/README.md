# 텔레그램 봇 자동매매 모니터링 시스템

텔레그램 봇을 활용한 자동매매 시스템 모니터링 및 제어 시스템입니다.

## 📁 모듈 구조

```
telegram_bot_monitoring/
├── __init__.py
├── main.py                    # 메인 실행 파일
├── config/                    # 설정 관리
│   ├── __init__.py
│   └── config_manager.py     # 설정 관리자
├── handlers/                  # 명령어 처리
│   ├── __init__.py
│   └── command_handlers.py   # 명령어 핸들러
└── templates/                # 메시지 포맷팅
    ├── __init__.py
    └── message_templates.py  # 메시지 템플릿
```

## 🚀 설치 및 실행

### 1. 필수 패키지 설치

```bash
pip install python-telegram-bot
```

### 2. 환경 변수 설정

텔레그램 봇 토큰을 환경 변수로 설정합니다.

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN='your_bot_token_here'
```

**Windows (CMD):**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
```

### 3. 봇 실행

```bash
python main.py
```

## 📋 지원 명령어

### `/start`
봇을 시작하고 환영 메시지를 표시합니다.

### `/status`
시스템 상태 및 거래 현황을 조회합니다.
- 거래 상태 (실행 중/중지됨)
- 자본 정보
- 거래 통계

### `/profit`
수익률 정보를 조회합니다.
- 총 수익률
- 자본 현황
- 거래 통계

### `/start_trading`
자동매매를 시작합니다.

### `/stop_trading`
자동매매를 중지합니다.

## 🔧 주요 기능

### 1. 모듈화된 구조
- **handlers**: 명령어 처리 로직 분리
- **templates**: 메시지 포맷팅 로직 분리
- **config**: 설정 관리 로직 분리

### 2. 에러 처리
- 모든 핸들러에 try-except 블록 포함
- 오류 발생 시 사용자에게 친화적인 메시지 전송
- 상세한 로깅

### 3. 로깅
- 모든 명령어 실행 로그 기록
- 오류 발생 시 상세한 스택 트레이스 기록

### 4. 타입 힌트
- 모든 함수에 타입 힌트 적용
- 코드 가독성 및 유지보수성 향상

## 📝 사용 예시

### 텔레그램에서 봇 사용

1. 텔레그램에서 봇 검색
2. `/start` 명령어로 봇 시작
3. `/status` 명령어로 시스템 상태 확인
4. `/profit` 명령어로 수익률 조회
5. `/start_trading` 명령어로 자동매매 시작
6. `/stop_trading` 명령어로 자동매매 중지

## ⚠️ 주의사항

1. **봇 토큰 보안**: 봇 토큰은 절대 공유하지 마세요.
2. **환경 변수**: 봇 토큰은 환경 변수로 관리하세요.
3. **테스트**: 실제 자금을 사용하기 전에 충분한 테스트를 진행하세요.

## 🔗 관련 자료

- [python-telegram-bot 공식 문서](https://python-telegram-bot.org/)
- [텔레그램 Bot API](https://core.telegram.org/bots/api)
- [BotFather 가이드](https://core.telegram.org/bots#6-botfather)
