# 🚀 실시간 모니터링 시스템 - 빠른 시작

## 📋 개요

자동매매 시스템의 성능을 실시간으로 모니터링하는 통합 시스템입니다.

### 구현된 기능
✅ 1. 실시간 데이터 수집기
✅ 2. 성능 지표 계산 엔진  
✅ 3. 알림 시스템
✅ 4. 웹 대시보드
✅ 5. 데이터 저장 및 분석

---

## ⚡ 빠른 시작 (3단계)

### 1단계: 패키지 설치
```bash
cd lesson-13
pip install flask
```

### 2단계: 테스트 실행
```bash
python test_monitoring_system.py
```

### 3단계: 시스템 실행
```bash
python realtime_monitoring_system.py
```

### 4단계: 웹 대시보드 접속
```
http://localhost:5000
```

---

## 📊 주요 기능

### 실시간 모니터링
- **시장 데이터**: 가격, 거래량, 변동성 추적
- **성과 지표**: 수익률, 샤프 비율, 최대 낙폭
- **알림**: 위험 상황 자동 감지

### 웹 대시보드
- **실시간 차트**: 자산 곡선, 샤프 비율 추이
- **성과 카드**: 수익률, 리스크, 효율성, 거래 통계
- **알림 패널**: 최근 알림 실시간 표시

### 자동 저장
- 1분마다 CSV 파일 자동 저장
- 시장 데이터 및 성과 데이터 기록
- 히스토리 관리 및 백업

---

## 🎯 알림 규칙

### 자동 알림 조건

| 규칙 | 조건 | 레벨 | 조치 |
|------|------|------|------|
| 높은 낙폭 | 낙폭 > 5% | ⚠️ WARNING | 포지션 확인 |
| 위험 낙폭 | 낙폭 > 10% | 🚨 CRITICAL | 즉시 확인 |
| 낮은 샤프 | 샤프 < 0 | ⚠️ WARNING | 전략 재검토 |
| 높은 레버리지 | 레버리지 > 2x | ❌ ERROR | 레버리지 축소 |
| 낮은 승률 | 승률 < 40% | ⚠️ WARNING | 전략 분석 |

---

## 📈 대시보드 화면

### 메인 대시보드
```
┌─────────────────────────────────────────────┐
│  🚀 자동매매 실시간 모니터링                │
│  ● 시스템 가동 중                           │
└─────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ 📊 수익률 │ │ ⚠️ 리스크 │ │ 💹 효율성 │ │ 📈 거래   │
│          │ │          │ │          │ │          │
│ 총: 5.2% │ │ MDD:-3%  │ │샤프:1.8  │ │거래:45   │
│ 일:0.3%  │ │ VaR:-2%  │ │소르:2.1  │ │승률:68%  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

┌─────────────────────────────────────────────┐
│  자산 곡선                                   │
│  [실시간 라인 차트]                         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔔 최근 알림                                │
│  ⚠️ 높은 낙폭 감지: 현재 낙폭 5.2%           │
│  ℹ️ 거래 완료: +15,000원                     │
└─────────────────────────────────────────────┘
```

---

## 🔧 설정 가능 항목

### 데이터 수집
```python
collector = RealtimeDataCollector(
    symbols=['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
    update_interval=1  # 업데이트 간격 (초)
)
```

### 알림 쿨다운
```python
alert_system = AlertSystem(
    cooldown_seconds=300  # 5분 쿨다운
)
```

### 대시보드 포트
```python
dashboard = MonitoringDashboard(
    ...,
    port=5000  # 포트 번호
)
```

---

## 📡 API 엔드포인트

### REST API

```bash
# 시스템 상태
GET http://localhost:5000/api/status

# 성능 지표
GET http://localhost:5000/api/performance

# 시장 데이터
GET http://localhost:5000/api/market/KRW-BTC

# 알림 조회
GET http://localhost:5000/api/alerts?minutes=60

# 차트 데이터
GET http://localhost:5000/api/chart/equity?hours=24
GET http://localhost:5000/api/chart/sharpe?hours=24
GET http://localhost:5000/api/chart/drawdown?hours=24
```

### 응답 예시

```json
{
  "returns": {
    "total": "5.20%",
    "daily": "0.30%",
    "monthly": "8.50%",
    "annual": "62.00%"
  },
  "risk": {
    "volatility": "18.50%",
    "max_drawdown": "-3.20%",
    "var_95": "-2.10%"
  },
  "efficiency": {
    "sharpe_ratio": "1.85",
    "sortino_ratio": "2.15"
  }
}
```

---

## 💾 데이터 저장

### 자동 저장 파일

**시장 데이터:**
```
market_data_20251008_143000.csv
├── timestamp
├── symbol
├── price
├── volume
└── ...
```

**성과 데이터:**
```
performance_data_20251008_143000.csv
├── timestamp
├── strategy_id
├── position_size
├── unrealized_pnl
└── ...
```

---

## 🐛 문제 해결

### Flask 설치 오류
```bash
pip install flask flask-cors
```

### 포트 충돌
```python
# realtime_monitoring_system.py에서
dashboard = MonitoringDashboard(..., port=8080)
```

### 템플릿 오류
```bash
# 템플릿 재생성
python -c "
from src.monitoring import MonitoringDashboard
dashboard = MonitoringDashboard(None, None, None)
dashboard.create_dashboard_template()
"
```

---

## 📚 추가 문서

- **[MONITORING_GUIDE.md](./MONITORING_GUIDE.md)** - 상세 가이드
- **[README.md](./README.md)** - 전체 시스템 문서
- **[QUICKSTART.md](./QUICKSTART.md)** - 빠른 시작

---

## 🎯 다음 단계

1. ✅ 테스트 실행: `python test_monitoring_system.py`
2. ✅ 시스템 실행: `python realtime_monitoring_system.py`
3. ✅ 대시보드 접속: `http://localhost:5000`
4. ✅ 성과 확인 및 알림 모니터링

---

**실시간 모니터링으로 더 안전한 자동매매를 경험하세요!** 🚀

