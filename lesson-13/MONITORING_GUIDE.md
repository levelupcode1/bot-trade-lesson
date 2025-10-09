# 📊 실시간 모니터링 시스템 가이드

## 개요

자동매매 시스템의 성능을 실시간으로 모니터링하고, 문제 상황을 즉시 감지할 수 있는 통합 모니터링 시스템입니다.

## 🎯 핵심 기능

### 1. **실시간 데이터 수집기**
- 시장 데이터 실시간 수집
- 전략 성과 추적
- 데이터 히스토리 관리
- CSV 내보내기 기능

### 2. **성능 지표 계산 엔진**
- 수익률 지표 (총/일간/월간/연간)
- 리스크 지표 (변동성, MDD, VaR, CVaR)
- 효율성 지표 (샤프, 소르티노, 칼마 비율)
- 거래 지표 (승률, 수익 팩터)

### 3. **알림 시스템**
- 규칙 기반 알림
- 다단계 알림 레벨 (INFO, WARNING, ERROR, CRITICAL)
- 쿨다운 메커니즘
- 텔레그램 연동 (선택사항)

### 4. **웹 대시보드**
- 실시간 성과 시각화
- 인터랙티브 차트
- 알림 모니터링
- REST API 제공

### 5. **데이터 저장 및 분석**
- CSV 자동 저장
- 히스토리 관리
- 성과 분석 리포트

---

## 📦 설치

### 필수 패키지

```bash
pip install flask pandas numpy scipy
```

또는 requirements.txt 업데이트:

```bash
pip install -r requirements.txt
```

---

## 🚀 실행 방법

### 1. 기본 실행

```bash
cd lesson-13
python realtime_monitoring_system.py
```

### 2. 웹 대시보드 접속

브라우저에서:
```
http://localhost:5000
```

### 3. 종료

```
Ctrl + C
```

---

## 📊 대시보드 기능

### 메인 화면

#### 성과 카드
- **수익률**: 총/일간/월간/연간 수익률
- **리스크**: 변동성, 최대 낙폭, VaR, CVaR
- **효율성**: 샤프, 소르티노, 칼마 비율
- **거래 통계**: 총 거래, 승률, 수익 팩터

#### 실시간 차트
- **자산 곡선**: 시간별 총 수익률
- **샤프 비율**: 시간별 샤프 비율 추이
- **낙폭 차트**: 최대 낙폭 변화

#### 알림 패널
- 최근 1시간 알림 표시
- 레벨별 색상 구분
- 타임스탬프 포함

### API 엔드포인트

```bash
# 시스템 상태
GET /api/status

# 성능 지표
GET /api/performance

# 시장 데이터
GET /api/market/<symbol>

# 알림 조회
GET /api/alerts?minutes=60

# 차트 데이터
GET /api/chart/<chart_type>?hours=24
```

---

## 🔔 알림 규칙

### 기본 알림 규칙

#### 1. **High Drawdown (경고)**
- **조건**: 현재 낙폭 > 5%
- **레벨**: WARNING
- **조치**: 포지션 확인 필요

#### 2. **Critical Drawdown (위험)**
- **조건**: 현재 낙폭 > 10%
- **레벨**: CRITICAL
- **조치**: 즉시 포지션 청산 검토

#### 3. **Low Sharpe Ratio (경고)**
- **조건**: 샤프 비율 < 0
- **레벨**: WARNING
- **조치**: 전략 재검토 필요

#### 4. **High Leverage (오류)**
- **조건**: 레버리지 > 2.0x
- **레벨**: ERROR
- **조치**: 레버리지 축소 필요

#### 5. **Low Win Rate (경고)**
- **조건**: 승률 < 40% (20회 이상 거래 시)
- **레벨**: WARNING
- **조치**: 전략 성과 분석 필요

### 커스텀 알림 추가

```python
from src.monitoring import AlertRule, AlertType, AlertLevel

# 커스텀 규칙 생성
custom_rule = AlertRule(
    name="high_profit",
    condition=lambda m: m.total_return > 0.20,  # 수익률 20% 초과
    alert_type=AlertType.PERFORMANCE,
    level=AlertLevel.INFO
)

# 알림 시스템에 추가
alert_system.add_rule(custom_rule)
```

---

## 💾 데이터 저장

### 자동 저장

**시장 데이터** (1분마다):
```
market_data_20251008_143000.csv
```

**성과 데이터** (1분마다):
```
performance_data_20251008_143000.csv
```

### 수동 내보내기

```python
# 시장 데이터
market_df = data_collector.export_to_dataframe('market')
market_df.to_csv('custom_market_data.csv', index=False)

# 성과 데이터
performance_df = data_collector.export_to_dataframe('performance')
performance_df.to_csv('custom_performance_data.csv', index=False)
```

---

## 🔧 고급 설정

### 데이터 수집 간격 변경

```python
data_collector = RealtimeDataCollector(
    symbols=['KRW-BTC', 'KRW-ETH'],
    update_interval=5  # 5초마다 업데이트
)
```

### 알림 쿨다운 시간 변경

```python
alert_system = AlertSystem(
    cooldown_seconds=600  # 10분 쿨다운
)
```

### 대시보드 포트 변경

```python
dashboard = MonitoringDashboard(
    data_collector=data_collector,
    performance_tracker=performance_tracker,
    alert_system=alert_system,
    port=8080  # 포트 변경
)
```

---

## 📱 텔레그램 알림 설정 (선택사항)

### 1. 텔레그램 봇 생성

1. @BotFather에게 `/newbot` 명령
2. 봇 이름 및 username 설정
3. API 토큰 받기

### 2. Chat ID 확인

1. 봇과 대화 시작
2. https://api.telegram.org/bot<TOKEN>/getUpdates 접속
3. chat.id 확인

### 3. 핸들러 추가

```python
from src.monitoring.alert_system import TelegramHandler

# 텔레그램 핸들러 생성
telegram = TelegramHandler(
    bot_token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID"
)

# 알림 시스템에 추가
alert_system.add_handler(telegram)
```

---

## 📈 성과 분석

### 성과 요약 조회

```python
summary = performance_tracker.get_performance_summary()

print(summary['returns'])    # 수익률
print(summary['risk'])        # 리스크
print(summary['efficiency'])  # 효율성
print(summary['trading'])     # 거래 통계
```

### 메트릭 히스토리

```python
# 최근 24시간 메트릭
metrics_df = performance_tracker.get_metrics_dataframe(hours=24)

# 데이터 분석
print(metrics_df.describe())
```

### 알림 히스토리

```python
# 최근 1시간 알림
recent_alerts = alert_system.get_recent_alerts(minutes=60)

for alert in recent_alerts:
    print(f"{alert.timestamp}: {alert.title} - {alert.message}")
```

---

## 🎨 대시보드 커스터마이징

### 템플릿 수정

대시보드 템플릿 위치:
```
src/monitoring/templates/dashboard.html
```

### 차트 추가

```javascript
// 새로운 차트 생성
const customCtx = document.getElementById('customChart').getContext('2d');
const customChart = new Chart(customCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Custom Metric',
            data: [],
            borderColor: '#f59e0b',
            tension: 0.4
        }]
    },
    options: chartOptions
});

// 데이터 업데이트
const customResponse = await fetch('/api/chart/custom');
const customData = await customResponse.json();
customChart.data.labels = customData.timestamps;
customChart.data.datasets[0].data = customData.values;
customChart.update();
```

---

## 🐛 문제 해결

### 대시보드 접속 안 됨

**원인**: 포트 충돌
**해결**:
```python
dashboard = MonitoringDashboard(..., port=8080)
```

### 데이터 수집 중단

**원인**: 스레드 충돌
**해결**: 시스템 재시작

### 메모리 사용량 증가

**원인**: 히스토리 누적
**해결**: 히스토리 제한 설정
```python
# realtime_collector.py에서
if len(self.market_history) > 5000:  # 제한 줄이기
    self.market_history = self.market_history[-5000:]
```

---

## 📊 모니터링 모범 사례

### 1. 정기적 확인
- 매 시간 대시보드 확인
- 일일 성과 리포트 검토
- 주간 알림 패턴 분석

### 2. 알림 관리
- 중요 알림만 활성화
- 쿨다운 시간 적절히 설정
- 알림 히스토리 정기 검토

### 3. 데이터 관리
- 주기적 데이터 백업
- 오래된 파일 정리
- 성과 데이터 아카이빙

### 4. 성능 최적화
- 불필요한 심볼 제거
- 업데이트 간격 조정
- 메모리 사용량 모니터링

---

## 🔗 관련 문서

- [README.md](./README.md) - 전체 시스템 가이드
- [QUICKSTART.md](./QUICKSTART.md) - 빠른 시작
- [FIXES.md](./FIXES.md) - API 수정 사항

---

## 📞 지원

문제가 발생하면:
1. 로그 파일 확인 (`monitoring_system.log`)
2. 대시보드 API 상태 확인 (`/api/status`)
3. 시스템 재시작

---

**마지막 업데이트:** 2025-10-08

