# 스케줄링 시스템 사용 가이드

이 문서는 `APScheduler`와 우선순위 디스패처를 결합한 실시간 스케줄링 시스템의 사용 방법을 설명합니다.

## 주요 기능
- 정확한 시간 기반 실행(KST, Cron/Interval)
- 우선순위 기반 작업 관리(PriorityQueue + 워커 스레드)
- 실패 시 재시도(지수 백오프 + 지터)
- 작업 간 의존성 관리(간단 DAG, 완료 상태 파일 저장)
- 동적 스케줄 변경(YAML 설정 파일 감시 후 자동 적용)

## 파일 구성
- `scheduler_system.py` : 스케줄러/디스패처/작업 구현(더미)
- `schedule_config.yaml` : 스케줄 정의(YAML). 없으면 자동 생성
- `.scheduler_state.json` : 작업 완료 상태 저장 파일
- `requirements.txt` : 필요한 파이썬 패키지 목록

## 설치
```bash
pip install -r lesson-09/requirements.txt
```

## 실행
```bash
python lesson-09/scheduler_system.py
```

## 기본 스케줄(자동 생성)
- 매일 09:00 거래 시작
- 매일 23:00 거래 종료
- 5분마다 거래 조건 평가(거래 시작 의존)
- 매시 정각+5초 상태 보고
- 매일 00:00:10 데이터 정리/백업(거래 종료 의존)
- 1분마다 시스템 헬스 체크(최우선)

## 스케줄 설정 예시(`schedule_config.yaml`)
```yaml
jobs:
  - id: start_trading_daily
    task: start_trading
    trigger: cron
    cron:
      hour: 9
      minute: 0
      second: 0
    priority: 1

  - id: stop_trading_daily
    task: stop_trading
    trigger: cron
    cron:
      hour: 23
      minute: 0
      second: 0
    priority: 1

  - id: evaluate_conditions_every_5m
    task: evaluate_conditions
    trigger: interval
    interval:
      minutes: 5
    priority: 3
    depends_on: ["start_trading_daily"]
    payload:
      symbols: ["KRW-BTC", "KRW-ETH"]

  - id: hourly_status_report
    task: hourly_status_report
    trigger: cron
    cron:
      minute: 0
      second: 5
    priority: 5
    payload:
      detail: summary

  - id: midnight_maintenance
    task: midnight_maintenance
    trigger: cron
    cron:
      hour: 0
      minute: 0
      second: 10
    priority: 2
    depends_on: ["stop_trading_daily"]

  - id: system_health_check
    task: system_health_check
    trigger: interval
    interval:
      minutes: 1
    priority: 0
```

## 운영 팁
- Windows 서비스로 등록 시 `nssm` 등 사용을 권장합니다.
- `.scheduler_state.json`은 의존성 여부 판단에 사용됩니다. 초기화가 필요하면 파일을 삭제하세요.
- 작업 충돌 방지를 위해 중요한 작업은 낮은 `priority` 값을 사용하고, 워커 수를 조정하세요.
- 장애 분석을 위해 표준 출력 로그를 파일 로테이션과 함께 보관하세요.
