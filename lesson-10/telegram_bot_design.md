# 텔레그램 알림 봇 설계 (10차시)

## 목표
- 실시간 거래 이벤트/상태/오류 알림과 운영 커맨드 제공
- 안정성(재시도/백오프/서킷), 신뢰성(중복 억제/유실 방지), 보안(권한/화이트리스트)

## 아키텍처
- Producer: Trading/Risk/Order/Scheduler/Monitoring
- Notification Service: Router, Deduplicator, RateLimiter, Formatter, Sender, Outbox
- Telegram Bot: Webhook 또는 Long-polling, Command Handler
- Config: 정책/채널 매핑/권한

## 메시지 카테고리/정책
- P0 긴급: 즉시 전송(우회큐), 개별 메세지, 중복 억제 10s
- P1 중요: 집계(30s), 묶음 전송
- P2 일반: 배치(5~10분)
- P3 디버그: 기본 비활성

## 포맷/템플릿
- 공통 헤더: [event_type][severity][source] ts
- 주문/체결/오류/리소스/스케줄 전용 템플릿

## 운영 커맨드 예시
- /start_trading, /stop_trading, /status, /positions, /pnl, /reload_config, /health
- 권한: read_only, operator, admin 로 분리

## 장애/복구 전략
- API/네트워크 실패: 지수 백오프+서킷 브레이커, Outbox 재플레이
- 텔레그램 장애: 로컬 큐 적치, 복구 후 배치 전송(최대량 제한)
- 프로세스 크래시: 상태 스냅샷 복원, 미전송 outbox 재전송

## 보안
- 토큰 보호, 채팅 화이트리스트, 명령어 권한 체크, 감사 로그

## 모니터링
- 전송지연, 드롭율, 재시도율, 큐 길이, 오류율, 커맨드 사용 현황
