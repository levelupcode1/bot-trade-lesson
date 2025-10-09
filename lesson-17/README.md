# 17차시: 적응형 전략 자동 전환 시스템

시장 상황을 자동으로 감지하고, **상승장, 하락장, 횡보장**에 따라 최적의 전략으로 자동 전환하는 지능형 자동매매 시스템입니다.

## 🎯 시스템 개요

### 핵심 기능
1. **시장 상황 자동 감지**: 추세, 변동성, 모멘텀, 거래량을 종합 분석
2. **전략 자동 전환**: 시장 상황에 맞는 최적 전략으로 실시간 전환
3. **리스크 관리**: 시장별 차별화된 포지션 사이징
4. **성과 추적**: 전략별 성과 분석 및 최적화

### 지원 전략

| 전략 | 적용 시장 | 특징 | 리스크 |
|------|----------|------|--------|
| 추세 추종 | 상승장 | 이동평균 크로스, 적극적 진입 | 중간 |
| 레인지 트레이딩 | 횡보장 | RSI + 볼린저 밴드, 지지/저항 매매 | 낮음 |
| 변동성 돌파 | 횡보→추세 전환 | 래리 윌리엄스 전략 | 중간 |
| 모멘텀 스캘핑 | 고변동성 상승 | 단기 모멘텀, 빠른 회전 | 높음 |
| 방어 전략 | 하락장 | 현금 보유, 극히 제한적 진입 | 매우 낮음 |

## 📁 파일 구조

```
lesson-17/
├── market_condition_detector.py    # 시장 상황 감지 모듈
├── market_strategies.py            # 전략 구현
├── adaptive_strategy_system.py     # 적응형 시스템 (통합)
├── example_adaptive_trading.py     # 실행 예제
├── requirements.txt                # 필요 패키지
└── README.md                       # 문서
```

## 🚀 사용 방법

### 1. 설치

```bash
# 필요 패키지 설치
pip install -r requirements.txt
```

### 2. 실행

```bash
# 시뮬레이션 실행
python example_adaptive_trading.py
```

### 3. 코드 사용 예제

```python
from adaptive_strategy_system import AdaptiveStrategySystem
import pandas as pd

# 시스템 초기화
system = AdaptiveStrategySystem(account_balance=10_000_000)

# 가격 데이터 준비 (OHLCV)
price_data = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 전략 실행
signal = system.execute_strategy(price_data)

# 신호에 따라 매매
if signal['action'] == 'BUY':
    system.open_position(signal)
elif signal['action'] == 'SELL' and system.current_position:
    current_price = price_data['close'].iloc[-1]
    system.close_position(current_price, signal['reason'])

# 성과 확인
system.print_performance_report()
```

## 🧪 시뮬레이션 시나리오

시스템은 다음 4가지 시나리오에서 자동으로 전략을 전환합니다:

### 1. 상승장 (Bull Market)
- **감지**: 가격 상승 + 이동평균 정배열 + 긍정적 모멘텀
- **전략**: 추세 추종 또는 모멘텀 스캘핑
- **포지션**: 적극적 (계좌의 3-5%)

### 2. 하락장 (Bear Market)
- **감지**: 가격 하락 + 이동평균 역배열 + 부정적 모멘텀
- **전략**: 방어 전략 (현금 보유 우선)
- **포지션**: 극히 보수적 (계좌의 1% 이하)

### 3. 횡보장 (Sideways Market)
- **감지**: 방향성 없음 + 일정한 변동 범위
- **전략**: 레인지 트레이딩 또는 변동성 돌파
- **포지션**: 보수적 (계좌의 2-3%)

### 4. 혼합장 (Mixed Market)
- **감지**: 추세 자주 변경
- **전략**: 신호 신뢰도에 따라 유연하게 전환
- **포지션**: 적응적

## 📊 시장 상황 감지 방법

### 추세 분석
```python
# 이동평균선 배열
단기(10일) > 중기(20일) > 장기(50일) → 상승 추세
단기(10일) < 중기(20일) < 장기(50일) → 하락 추세

# 가격 변화율
20일 기준 +5% 이상 → 상승
20일 기준 -5% 이하 → 하락
20일 기준 ±5% 이내 → 횡보
```

### 변동성 분석
```python
# ATR (Average True Range)
일일 변동률 < 2% → 저변동성
일일 변동률 2-4% → 보통
일일 변동률 > 6% → 고변동성
```

### 모멘텀 분석
```python
# RSI + MACD + ROC 종합
모멘텀 > 0.5 → 강한 상승
모멘텀 < -0.5 → 강한 하락
```

## 💡 전략 전환 예시

```
시간: 2024-01-01 09:00
상태: 횡보장 감지 (변동성 낮음)
전략: 레인지 트레이딩 → RSI 30 미만에서 매수

시간: 2024-01-15 14:30
상태: 상승 추세 전환 감지 (골든 크로스)
전략: 추세 추종으로 전환 → 추세 추종 매수

시간: 2024-02-01 11:00
상태: 하락 추세 감지 (데드 크로스)
전략: 방어 전략으로 전환 → 현금 보유

시간: 2024-02-20 10:00
상태: 극심한 과매도 감지 (RSI 20)
전략: 단기 반등 시도 → 작은 포지션 진입
```

## ⚙️ 시스템 파라미터

### 시장 감지 기준
```python
# 추세 판단 기준
STRONG_BULL = +15% 이상
BULL = +5% 이상
SIDEWAYS = ±5% 이내
BEAR = -5% 이하
STRONG_BEAR = -15% 이하

# 신뢰도 기준
MIN_CONFIDENCE = 0.6  # 60% 이상 신뢰도에서만 전략 전환
```

### 리스크 관리
```python
# 전략별 리스크
추세 추종: 2-5% (적극적)
레인지: 2-3% (보수적)
변동성 돌파: 2-4% (중간)
스캘핑: 2-3% (빠른 회전)
방어: 0.5-1% (극히 보수적)
```

## 📈 성과 측정

시스템은 다음 지표를 추적합니다:

- **전체 수익률**: 초기 자본 대비 수익
- **승률**: 수익 거래 / 전체 거래
- **전략별 성과**: 각 전략의 개별 성과
- **전략 전환 횟수**: 시장 적응력 지표
- **최대 낙폭 (MDD)**: 리스크 관리 효과

## ⚠️ 주의사항

### 백테스팅 필수
- 실제 자금 투입 전 충분한 백테스팅
- 다양한 시장 상황에서 테스트
- 최소 1년 이상 데이터로 검증

### 시장 급변 대응
- 급격한 시장 변동 시 신뢰도 하락
- 신뢰도 낮을 때는 현재 전략 유지
- 연속 손실 시 거래 중단 메커니즘

### 수수료 고려
- 전략 전환 시 거래 비용 발생
- 과도한 전환은 수익률 저하
- 최소 신뢰도 기준으로 불필요한 전환 방지

## 🔧 커스터마이징

### 1. 새로운 전략 추가

```python
from market_strategies import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("나만의 전략")
    
    def generate_signal(self, market_data):
        # 신호 생성 로직
        return {'action': 'BUY', 'confidence': 0.8, ...}
    
    def calculate_position_size(self, account_balance, risk_percent):
        return account_balance * risk_percent
```

### 2. 감지 기준 조정

```python
# market_condition_detector.py에서
detector = MarketConditionDetector()

# 추세 기준 변경
detector.trend_thresholds['bull'] = 0.03  # 3%로 하향

# 변동성 기준 변경
detector.volatility_thresholds['high'] = 0.05  # 5%로 하향
```

### 3. 리스크 파라미터 조정

```python
# adaptive_strategy_system.py에서
system = AdaptiveStrategySystem(
    account_balance=10_000_000,
    min_confidence=0.7  # 신뢰도 기준 상향
)
```

## 📚 학습 자료

### 추천 학습 순서
1. `market_condition_detector.py` - 시장 분석 이해
2. `market_strategies.py` - 개별 전략 이해
3. `adaptive_strategy_system.py` - 통합 시스템 이해
4. `example_adaptive_trading.py` - 실전 적용

### 핵심 개념
- **적응형 매매**: 시장 변화에 따라 전략 변경
- **다중 전략**: 한 가지 전략의 한계 극복
- **리스크 분산**: 시장별 차별화된 리스크 관리
- **신뢰도 기반**: 확실할 때만 전환

## 🌐 실시간 업비트 연동 (✅ 완료!)

업비트 API와 실시간 연동이 구현되었습니다!

### 사용 방법

1. **테스트 실행**
   ```bash
   python test_realtime_system.py
   ```

2. **실시간 봇 실행**
   ```bash
   python realtime_adaptive_bot.py
   ```

3. **상세 가이드**
   - [REALTIME_GUIDE.md](REALTIME_GUIDE.md) 참조

### 주요 파일

- `upbit_data_collector.py`: 업비트 실시간 데이터 수집
- `realtime_adaptive_bot.py`: 실시간 자동매매 봇
- `test_realtime_system.py`: 시스템 테스트

## 🎓 다음 단계

1. ~~**실시간 데이터 연동**: 업비트 API 연동~~ ✅ 완료!
2. **실제 주문 API**: 주문 실행 기능 추가
3. **머신러닝 통합**: 시장 예측 모델 추가
4. **포트폴리오 확장**: 여러 코인 동시 관리
5. **백테스트 엔진**: 과거 데이터 검증 시스템
6. **텔레그램 알림**: 전략 전환 시 실시간 알림

## 📞 문의 및 개선

- 버그 리포트: GitHub Issues
- 기능 제안: Pull Request 환영
- 질문: Discussions 활용

---

**⚡ 핵심 메시지**

> "시장은 변합니다. 전략도 변해야 합니다."
> 
> 적응형 전략 시스템은 시장의 변화를 감지하고,
> 최적의 전략으로 자동 전환하여 안정적인 수익을 추구합니다.

---

**Made with ❤️ for algorithmic traders**

