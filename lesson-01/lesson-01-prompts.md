# 1차시 프롬프트 모음

## 1번 프롬프트
```text
비트코인 가격이 5% 이상 올라가면 알림을 보내는 봇을 파이썬으로 만들어줘. 
Upbit API를 사용해서 실시간 가격을 가져오고, 
기준 가격보다 5% 이상 올라갔을 때 화면에 알림을 보여줘.
```

### 생성된 코드 파일 정보
- **파일명**: `bitcoin_price_alert_bot.py`
- **주요 기능**: 
  - Upbit API를 사용한 실시간 비트코인 가격 모니터링
  - 5% 상승 시 화면 알림 표시
  - tkinter 기반 GUI 인터페이스
  - 모니터링 시작/중지 기능
- **의존성**: `requirements.txt`
- **실행 방법**: `python bitcoin_price_alert_bot.py`

---

## 2번 프롬프트
```text
알림을 텍스트 파일로 저장하도록 바꿔줘. 
price_alerts.txt 파일에 알림 메시지를 저장하는 기능을 만들어줘.
```

### 생성된 코드 파일 정보
- **파일명**: `bitcoin_price_alert_bot_v2.py`
- **주요 기능**: 
  - 1번 프롬프트의 모든 기능 포함
  - 알림 메시지를 `price_alerts.txt` 파일에 자동 저장
  - 파일 기반 알림 로그 관리
  - 기존 GUI 인터페이스 유지
- **의존성**: `requirements.txt` (기존과 동일)
- **실행 방법**: `python bitcoin_price_alert_bot_v2.py`

---
