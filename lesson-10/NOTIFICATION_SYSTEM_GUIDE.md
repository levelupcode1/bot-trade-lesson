# 🔔 자동매매 알림 시스템 가이드

## 📋 개요

자동매매 시스템을 위한 종합적인 알림 관리 시스템입니다. 실시간 거래 알림, 수익률 달성 알림, 시스템 오류 알림 등을 효율적으로 관리하고 사용자별 맞춤 설정을 제공합니다.

## 🏗️ 시스템 아키텍처

### 핵심 컴포넌트

```
📦 알림 시스템
├── 🔧 NotificationManager      # 알림 관리자 (큐, 우선순위, 전송)
├── 📝 NotificationTemplates    # 메시지 템플릿 시스템
├── ⚙️ UserSettingsManager      # 사용자 설정 관리
├── 🔄 NotificationService      # 통합 서비스
└── 📊 NotificationHistory      # 알림 히스토리 관리
```

### 알림 타입 및 우선순위

| 우선순위 | 타입 | 설명 | 즉시 전송 |
|---------|------|------|----------|
| 🔴 CRITICAL | 시스템 오류, 손실 한계 | 즉시 대응 필요 | ✅ |
| 🟠 HIGH | 거래 실행, 리스크 경고 | 중요한 상태 변화 | ✅ |
| 🟡 MEDIUM | 수익률 달성, 설정 변경 | 일반적인 알림 | ⏰ |
| 🟢 LOW | 정기 보고, 상태 업데이트 | 정보성 알림 | 📦 |

## 🚀 시작하기

### 1. 기본 설정

```python
from src.telegram_bot.notifications import NotificationService

# 알림 서비스 초기화
notification_service = NotificationService(
    telegram_bot=your_telegram_bot,
    settings_dir="data/user_settings"
)

# 서비스 시작
await notification_service.start()
```

### 2. 환경 변수 설정

```bash
# 텔레그램 봇 토큰 설정
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### 3. 텔레그램 봇 통합

```python
# bot_initializer.py에서 자동으로 통합됨
from src.telegram_bot.core.bot_initializer import BotInitializer

bot_initializer = BotInitializer("config")
await bot_initializer.initialize()
await bot_initializer.run()  # 알림 서비스가 자동으로 시작됨
```

## 📨 알림 전송 방법

### 1. 거래 실행 알림

```python
# 매수 알림
trade_data = {
    "id": "TRD001",
    "symbol": "KRW-BTC",
    "amount": 0.001,
    "currency": "BTC",
    "price": 52000000,
    "total": 52000,
    "strategy": "Volatility Breakout"
}

await notification_service.send_trade_execution_notification(
    user_id="user123",
    action="buy",
    trade_data=trade_data
)

# 매도 알림 (수익률 포함)
trade_data.update({
    "profit_rate": 3.2,
    "profit_amount": 1664
})

await notification_service.send_trade_execution_notification(
    user_id="user123",
    action="sell",
    trade_data=trade_data
)
```

### 2. 수익률 달성 알림

```python
profit_data = {
    "daily_return": 8.5,
    "realized_pnl": 850000,
    "total_return": 15.2,
    "win_rate": 72.0,
    "daily_trades": 12
}

await notification_service.send_profit_achievement_notification(
    user_id="user123",
    achievement_type="daily_target",
    profit_data=profit_data
)
```

### 3. 손실 한계 알림

```python
loss_data = {
    "daily_loss": -3.2,
    "loss_amount": -320000,
    "daily_trades": 8
}

await notification_service.send_loss_limit_notification(
    user_id="user123",
    loss_type="daily_loss",
    loss_data=loss_data
)
```

### 4. 시스템 오류 알림

```python
error_data = {
    "error_type": "Connection Timeout",
    "impact_scope": "거래 중단",
    "retry_count": 2,
    "max_retries": 3,
    "estimated_recovery": "5분 내"
}

await notification_service.send_system_error_notification(
    user_id="user123",
    error_type="api_error",
    error_data=error_data
)
```

## ⚙️ 사용자 설정 관리

### 1. 기본 설정 조회

```python
# 사용자 설정 조회
settings = notification_service.get_user_notification_settings("user123")

print(f"활성화된 알림 타입: {settings.enabled_types}")
print(f"우선순위 임계값: {settings.priority_threshold}")
print(f"배치 모드: {settings.batch_mode}")
```

### 2. 설정 업데이트

```python
# 설정 업데이트
updates = {
    "enabled_types": ["trade_execution", "profit_achievement"],
    "priority_threshold": 2,  # HIGH 이상만 받기
    "batch_mode": True,
    "quiet_hours": {
        "enabled": True,
        "start_time": "22:00",
        "end_time": "08:00"
    }
}

success = notification_service.update_user_notification_settings(
    "user123", updates
)
```

### 3. 설정 옵션

#### 알림 타입 설정
- `trade_execution`: 거래 실행 알림
- `profit_achievement`: 수익률 달성 알림
- `loss_limit`: 손실 한계 알림
- `system_error`: 시스템 오류 알림
- `status_report`: 정기 상태 보고
- `config_change`: 설정 변경 알림
- `risk_warning`: 리스크 경고 알림

#### 우선순위 임계값
- `1`: CRITICAL만 (긴급 알림만)
- `2`: HIGH 이상 (중요 알림 이상)
- `3`: MEDIUM 이상 (일반 알림 이상)
- `4`: 모든 알림 (기본값)

#### 조용한 시간 설정
```python
quiet_hours = {
    "enabled": True,
    "start_time": "22:00",  # HH:MM 형식
    "end_time": "08:00",    # HH:MM 형식
    "timezone": "Asia/Seoul"
}
```

## 🔄 중복 방지 시스템

### 쿨다운 시간 설정

각 알림 타입별로 기본 쿨다운 시간이 설정되어 있습니다:

- 거래 실행: 5분
- 수익률 달성: 1시간
- 손실 한계: 30분
- 시스템 오류: 1시간
- 정기 보고: 24시간
- 설정 변경: 5분
- 리스크 경고: 15분

### 중복 감지 방식

1. **내용 기반 중복**: 메시지 내용의 해시값 비교
2. **시간 기반 중복**: 쿨다운 시간 내 동일 타입 알림 차단
3. **사용자별 설정**: 개별 쿨다운 시간 설정 가능

## 📊 알림 히스토리 관리

### 히스토리 조회

```python
# 사용자별 알림 히스토리 조회
history = notification_service.get_notification_history(
    user_id="user123",
    limit=50
)

for notification in history:
    print(f"{notification.timestamp}: {notification.type.value}")
```

### 히스토리 정보

- 알림 ID, 타입, 우선순위
- 전송 시간, 수신자
- 메시지 내용, 메타데이터
- 전송 상태, 재시도 횟수

## 🛠️ 고급 기능

### 1. 브로드캐스트 알림

```python
# 모든 사용자에게 알림 전송
results = await notification_service.broadcast_notification(
    notification_type=NotificationType.SYSTEM_ERROR,
    title="🔥 긴급 시스템 점검",
    message="시스템 점검으로 인해 30분간 서비스가 중단됩니다.",
    priority=NotificationPriority.CRITICAL
)

print(f"전송 결과: {results}")
```

### 2. 알림 시스템 테스트

```python
# 종합 테스트 실행
test_results = await notification_service.test_notification_system("user123")

print(f"테스트 결과: {test_results}")
```

### 3. 서비스 상태 모니터링

```python
# 서비스 상태 확인
status = notification_service.get_service_status()

print(f"서비스 실행 중: {status['service_running']}")
print(f"큐 상태: {status['queue_status']}")
print(f"설정 요약: {status['settings_summary']}")
```

## 🔧 설정 파일 구조

### 사용자 설정 파일 (`data/user_settings/user_id.json`)

```json
{
  "user_id": "user123",
  "enabled_types": ["trade_execution", "profit_achievement"],
  "priority_threshold": 2,
  "cooldown_settings": {
    "trade_execution": 300,
    "profit_achievement": 3600
  },
  "quiet_hours": {
    "enabled": true,
    "start_time": "22:00",
    "end_time": "08:00"
  },
  "batch_mode": false,
  "summary_mode": false,
  "language": "ko",
  "timezone": "Asia/Seoul"
}
```

## 🧪 테스트 실행

### 종합 테스트

```bash
# 알림 시스템 테스트 실행
python test_notification_system.py
```

### 테스트 시나리오

1. **기본 알림 전송 테스트**
   - 거래 실행 (매수/매도)
   - 수익률 달성
   - 손실 한계 도달
   - 시스템 오류 발생

2. **중복 방지 테스트**
   - 동일 알림 연속 전송
   - 쿨다운 시간 확인

3. **사용자 설정 테스트**
   - 설정 저장/로드
   - 설정 유효성 검증
   - 설정 내보내기/가져오기

4. **서비스 상태 테스트**
   - 큐 상태 모니터링
   - 히스토리 관리
   - 브로드캐스트 기능

## 📈 성능 최적화

### 1. 배치 처리

- 30초마다 최대 10개 알림 배치 처리
- 우선순위 기반 순차 처리
- 재시도 로직 자동 처리

### 2. 메모리 관리

- 알림 히스토리 자동 정리 (최대 1000건)
- 중복 필터 캐시 자동 정리
- 사용자 설정 캐시 (1시간 TTL)

### 3. 오류 처리

- 전송 실패 시 자동 재시도 (최대 3회)
- 오류 로깅 및 모니터링
- 서비스 복구 메커니즘

## 🚨 주의사항

### 1. 텔레그램 API 제한

- 초당 최대 30개 메시지 전송 제한
- 대량 전송 시 배치 처리 필수
- 스팸 방지를 위한 쿨다운 시간 준수

### 2. 보안 고려사항

- 사용자 설정 파일 암호화 권장
- API 토큰 환경 변수로 관리
- 민감한 정보 로깅 금지

### 3. 모니터링

- 알림 전송 실패율 모니터링
- 큐 크기 및 처리 지연 시간 확인
- 사용자 설정 변경 이력 추적

## 📞 문제 해결

### 자주 발생하는 문제

1. **알림이 전송되지 않음**
   - 텔레그램 봇 토큰 확인
   - 사용자 설정에서 알림 타입 활성화 확인
   - 우선순위 임계값 확인

2. **중복 알림 전송**
   - 쿨다운 시간 설정 확인
   - 알림 내용 중복 여부 확인

3. **서비스 시작 실패**
   - 설정 파일 유효성 검증
   - 로그 파일 확인
   - 의존성 패키지 설치 확인

### 로그 확인

```bash
# 로그 파일 위치
tail -f logs/notification_system.log

# 특정 오류 검색
grep "ERROR" logs/notification_system.log
```

## 📚 추가 자료

- [텔레그램 Bot API 문서](https://core.telegram.org/bots/api)
- [Python asyncio 문서](https://docs.python.org/3/library/asyncio.html)
- [프로젝트 README](README.md)
- [API 통합 가이드](UPBIT_API_README.md)

---

## 🎯 다음 단계

1. **실제 거래 시스템과 연동**
2. **웹 대시보드 구축**
3. **알림 분석 및 최적화**
4. **다중 채널 지원 (이메일, SMS)**
5. **AI 기반 알림 개인화**

이 가이드를 통해 효과적인 알림 시스템을 구축하고 운영할 수 있습니다. 추가 질문이나 지원이 필요하시면 언제든 문의해주세요!
