# 텔레그램 자동매매 알림 봇

암호화폐 자동매매 시스템을 위한 텔레그램 알림 봇입니다.

## 🚀 주요 기능

### 📊 거래 관리
- **거래 내역 조회** (`/trades`): 최근 거래 내역 및 상세 정보
- **수익률 분석** (`/profit`): 실시간 수익률, 승률, 거래 통계
- **시스템 상태** (`/status`): 거래 시스템 상태 및 모니터링

### 🎛️ 거래 제어
- **거래 시작/중지**: `/start_trading`, `/stop` 명령어로 원격 제어
- **설정 관리** (`/settings`): 리스크, 전략, 알림 설정

### 💬 사용자 인터페이스
- **인라인 키보드**: 버튼 클릭으로 쉬운 조작
- **실시간 업데이트**: 새로고침 기능
- **사용자 친화적 메시지**: 이모지와 포맷팅

## 📁 프로젝트 구조

```
lesson-10/
├── src/telegram_bot/           # 봇 소스 코드
│   ├── core/                   # 핵심 모듈
│   │   ├── bot_initializer.py  # 봇 초기화
│   │   └── __init__.py
│   ├── handlers/               # 명령어 핸들러
│   │   ├── base_handler.py     # 기본 핸들러
│   │   ├── basic_commands.py   # 기본 명령어
│   │   └── __init__.py
│   ├── templates/              # 메시지 템플릿
│   │   ├── base_template.py    # 기본 템플릿
│   │   ├── message_templates.py # 메시지 템플릿
│   │   ├── response_builder.py # 응답 빌더
│   │   └── __init__.py
│   ├── config/                 # 설정 관리
│   │   ├── config_manager.py   # 설정 관리자
│   │   └── __init__.py
│   ├── utils/                  # 유틸리티
│   │   ├── logger.py           # 로깅 시스템
│   │   └── __init__.py
│   └── __init__.py
├── config/                     # 설정 파일
│   └── bot_config.yaml         # 봇 설정
├── logs/                       # 로그 파일 (자동 생성)
├── main.py                     # 메인 실행 파일
├── requirements.txt            # 의존성 목록
└── README.md                   # 프로젝트 문서
```

## 🛠️ 설치 및 설정

### 필수 요구사항
- **Python 3.8 이상** (Python 3.13 권장)
- **python-telegram-bot 21.10** (Python 3.13 호환)
- **텔레그램 봇 토큰** ([@BotFather](https://t.me/botfather)에서 발급)

### 1. 의존성 설치

**방법 1: 직접 설치 (권장)**
```bash
pip install python-telegram-bot[all]==21.10
pip install PyYAML python-dotenv
```

**방법 2: requirements.txt 사용**
```bash
# httpx 충돌 방지를 위해 순서대로 설치
pip install python-telegram-bot[all]==21.10
pip install -r requirements.txt
```

**⚠️ 의존성 충돌 해결:**
만약 httpx 충돌이 발생하면:
```bash
pip uninstall -y httpx
pip install httpx~=0.27
pip install python-telegram-bot[all]==21.10
```

### 2. 환경 변수 설정

**Windows PowerShell:**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

**Windows CMD:**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### 3. 설정 파일 수정

`config/bot_config.yaml` 파일을 수정하여 봇 설정을 구성합니다:

```yaml
bot:
  token: "${TELEGRAM_BOT_TOKEN}"
  username: "your_bot_username"
  
security:
  admin_users: [123456789]  # 관리자 사용자 ID
  chat_whitelist: []        # 허용된 채팅 ID (빈 리스트면 모든 채팅 허용)
```

### 4. 봇 실행

```bash
python main.py
```

## 📱 사용법

### 기본 명령어

- `/start` - 봇 시작 및 환영 메시지
- `/help` - 도움말 표시
- `/status` - 시스템 상태 확인

### 거래 명령어

- `/trades` - 거래 내역 조회
- `/positions` - 포지션 현황 확인
- `/pnl` - 수익률 확인
- `/start_trading` - 자동매매 시작
- `/stop_trading` - 자동매매 중지

### 설정 명령어

- `/settings` - 설정 메뉴 열기
- `/reload_config` - 설정 파일 재로드

## 🔧 설정 옵션

### 봇 설정

```yaml
bot:
  token: "${TELEGRAM_BOT_TOKEN}"  # 봇 토큰
  username: "crypto_auto_trader_bot"
  description: "암호화폐 자동매매 시스템 알림 봇"
```

### 업데이트 방식

```yaml
update:
  use_webhook: false  # 개발 시 false, 운영 시 true
  webhook_url: "https://yourdomain.com/webhook"
  polling_interval: 1.0  # 폴링 간격 (초)
```

### 레이트 리밋

```yaml
rate_limit:
  max_messages_per_minute: 30
  max_commands_per_minute: 10
  burst_limit: 5
```

### 보안 설정

```yaml
security:
  enabled: true
  allowed_users: []        # 허용된 사용자 ID 목록
  admin_users: []          # 관리자 사용자 ID 목록
  chat_whitelist: []       # 허용된 채팅 ID 목록
```

### 알림 설정

```yaml
notifications:
  enabled: true
  trade_execution: true    # 거래 실행 알림
  pnl_alerts: true         # 수익률 알림
  risk_warnings: true      # 리스크 경고
  system_errors: true      # 시스템 오류 알림
  daily_reports: true      # 일일 리포트
```

## 🏗️ 아키텍처

### 핵심 컴포넌트

1. **BotInitializer**: 봇 초기화 및 설정 관리
2. **CommandParser**: 명령어 파싱 및 라우팅
3. **ResponseBuilder**: 메시지 템플릿 및 키보드 생성
4. **NotificationSender**: 알림 전송 및 큐 관리
5. **ConfigManager**: 설정 파일 관리

### 메시지 템플릿

- **WelcomeTemplate**: 환영 메시지
- **HelpTemplate**: 도움말 메시지
- **StatusTemplate**: 상태 메시지
- **TradeTemplate**: 거래 메시지
- **PnLTemplate**: 손익 메시지
- **AlertTemplate**: 알림 메시지

### 핸들러 구조

- **BaseHandler**: 모든 핸들러의 기본 클래스
- **StartCommandHandler**: 시작 명령어 처리
- **HelpCommandHandler**: 도움말 명령어 처리
- **StatusCommandHandler**: 상태 명령어 처리
- **CallbackQueryHandler**: 콜백 쿼리 처리

## 🔒 보안 기능

- **권한 관리**: 사용자별 명령어 실행 권한
- **레이트 리밋**: 명령어 남용 방지
- **감사 로그**: 모든 사용자 액션 기록
- **입력 검증**: 명령어 인자 검증

## 📊 로깅

구조화된 JSON 형태로 로그를 기록합니다:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "logger": "StartCommandHandler",
  "message": "명령어 실행 성공: start",
  "user_id": 123456789,
  "chat_id": 987654321
}
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 전체 테스트
pytest tests/
```

## 🚀 배포

### 개발 환경

```bash
python main.py
```

### 운영 환경 (웹훅 모드)

1. `config/bot_config.yaml`에서 `use_webhook: true` 설정
2. 웹훅 URL 설정
3. SSL 인증서 구성
4. 웹서버에서 봇 실행

## 📝 로그 파일

로그는 `logs/` 디렉토리에 저장됩니다:

- `bot.log`: 일반 로그
- `bot.log.1`, `bot.log.2`: 로테이션된 로그 파일

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**주의**: 이 봇은 교육 및 개발 목적으로 제작되었습니다. 실제 거래에 사용하기 전에 충분한 테스트를 수행하세요.
