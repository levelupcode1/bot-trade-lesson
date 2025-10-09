# 🔧 API 인터페이스 수정 사항

## 수정 날짜
2025-10-08

## 📋 수정 내용

### 1. MarketConditionAnalyzer (시장 분석기)

#### ❌ 이전 (잘못됨)
```python
condition = analyzer.analyze_market_condition(data)  # 단수형
```

#### ✅ 수정 (올바름)
```python
conditions = analyzer.analyze_market_conditions(data)  # 복수형
if conditions:
    condition = conditions[-1]  # 최신 상황 사용
```

**이유:** 실제 메서드명은 `analyze_market_conditions` (복수형)이며, 리스트를 반환합니다.

---

### 2. MultiStrategyManager (멀티 전략 관리자)

#### ❌ 이전 (잘못됨)
```python
manager.add_strategy(
    strategy_type=StrategyType.VOLATILITY_BREAKOUT,
    params={'k': 0.5, 'stop_loss': 0.02}
)
```

#### ✅ 수정 (올바름)
```python
from src.optimization.multi_strategy_manager import StrategyConfig

config = StrategyConfig(
    strategy_type=StrategyType.VOLATILITY_BREAKOUT,
    parameters={'k': 0.5, 'stop_loss': 0.02}  # params → parameters
)
manager.add_strategy(
    strategy_id='vb_001',  # 전략 ID 필수
    config=config  # StrategyConfig 객체 전달
)
```

**변경사항:**
- `params` → `parameters`
- `strategy_id` 매개변수 추가 필수
- `StrategyConfig` 객체로 전달

---

### 3. RiskOptimizer (리스크 최적화)

#### ❌ 이전 (잘못됨)
```python
risk_optimizer = RiskOptimizer(
    initial_capital=1_000_000,
    max_position_size=0.15,
    daily_loss_limit=0.02
)

position = risk_optimizer.calculate_position_size(
    current_price=50_000_000,
    volatility=0.03,
    method=PositionSizingMethod.KELLY_CRITERION
)
```

#### ✅ 수정 (올바름)
```python
from src.optimization.risk_optimizer import RiskLimits

# 1. RiskLimits 생성
limits = RiskLimits(
    max_position_size=0.15,
    daily_loss_limit=0.02,
    weekly_loss_limit=0.05,
    monthly_loss_limit=0.10
)

risk_optimizer = RiskOptimizer(
    initial_capital=1_000_000,
    risk_limits=limits
)

# 2. 포지션 사이징 (메서드명 변경)
expected_returns = {'KRW-BTC': 0.05, 'KRW-ETH': 0.04}
volatilities = {'KRW-BTC': 0.03, 'KRW-ETH': 0.04}
correlations = {('KRW-BTC', 'KRW-ETH'): 0.7}

positions = risk_optimizer.optimize_position_sizing(
    expected_returns=expected_returns,
    volatilities=volatilities,
    correlations=correlations,
    method=PositionSizingMethod.KELLY_CRITERION
)

# 3. 리스크 메트릭 계산 (메서드명 변경)
metrics = risk_optimizer.calculate_portfolio_risk_metrics(
    returns_data={'KRW-BTC': btc_returns, 'KRW-ETH': eth_returns},
    weights={'KRW-BTC': 0.6, 'KRW-ETH': 0.4}
)
```

**변경사항:**
- `RiskLimits` 객체 생성 필요
- `calculate_position_size` → `optimize_position_sizing`
- `calculate_risk_metrics` → `calculate_portfolio_risk_metrics`
- 단일 자산이 아닌 포트폴리오 기반 계산

**RiskLimits 필드:**
- `daily_loss_limit`: 일일 손실 한도
- `weekly_loss_limit`: 주간 손실 한도
- `monthly_loss_limit`: 월간 손실 한도
- `max_position_size`: 최대 포지션 크기
- `max_correlation`: 최대 상관관계
- `max_leverage`: 최대 레버리지

**optimize_position_sizing 파라미터:**
- `expected_returns`: Dict[str, float] - 각 자산의 예상 수익률
- `volatilities`: Dict[str, float] - 각 자산의 변동성
- `correlations`: Dict[Tuple[str, str], float] - 자산 간 상관관계
- `method`: PositionSizingMethod - 포지션 사이징 방법

---

### 4. TradeRecord (거래 기록)

#### ❌ 이전 (잘못됨)
```python
trade = TradeRecord(
    timestamp=datetime.now(),
    side='BUY',
    price=50_000_000,
    quantity=0.01,
    profit=100_000,
    return_pct=0.02
)
```

#### ✅ 수정 (올바름)
```python
from datetime import timedelta

trade = TradeRecord(
    entry_time=datetime.now() - timedelta(hours=2),
    exit_time=datetime.now(),
    symbol='KRW-BTC',
    strategy='test_strategy',
    side='buy',
    quantity=0.01,
    entry_price=50_000_000,
    exit_price=51_000_000,
    pnl=100_000,
    pnl_rate=0.02,
    commission=250,
    slippage=50,
    holding_period=timedelta(hours=2)
)
```

**TradeRecord 필드:**
- `entry_time`: 진입 시간
- `exit_time`: 청산 시간
- `symbol`: 거래 심볼
- `strategy`: 전략 이름
- `side`: 거래 방향 ('buy' or 'sell')
- `quantity`: 거래 수량
- `entry_price`: 진입 가격
- `exit_price`: 청산 가격
- `pnl`: 손익 (Profit and Loss)
- `pnl_rate`: 손익률
- `commission`: 수수료
- `slippage`: 슬리피지
- `holding_period`: 보유 기간

---

## 📁 수정된 파일 목록

1. ✅ `quick_test.py` - 테스트 스크립트 수정
2. ✅ `example_usage.py` - 예제 코드 수정
3. ✅ `README.md` - 문서의 예제 코드 수정

---

## ✅ 테스트 방법

### 1. 빠른 테스트
```bash
cd lesson-13
python quick_test.py
```

### 2. 전체 예제 실행
```bash
python example_usage.py
```

### 3. 개별 모듈 테스트
```bash
# 시장 분석기
python -c "from src.optimization import MarketConditionAnalyzer; print('OK')"

# 멀티 전략 관리자
python -c "from src.optimization import MultiStrategyManager; print('OK')"

# 리스크 최적화
python -c "from src.optimization import RiskOptimizer; print('OK')"

# 성능 평가기
python -c "from src.optimization import PerformanceEvaluator; print('OK')"
```

---

## 📚 참고 사항

### StrategyConfig 예제
```python
from src.optimization.multi_strategy_manager import StrategyConfig, StrategyType

# 변동성 돌파 전략
vb_config = StrategyConfig(
    strategy_type=StrategyType.VOLATILITY_BREAKOUT,
    parameters={'k': 0.5, 'stop_loss': 0.02, 'take_profit': 0.05},
    enabled=True,
    min_weight=0.0,
    max_weight=1.0,
    lookback_period=30
)

# 이동평균 교차 전략
ma_config = StrategyConfig(
    strategy_type=StrategyType.MA_CROSSOVER,
    parameters={'short_period': 5, 'long_period': 20},
    enabled=True
)
```

### RiskLimits 예제
```python
from src.optimization.risk_optimizer import RiskLimits

# 보수적 설정
conservative_limits = RiskLimits(
    daily_loss_limit=0.01,    # 1%
    weekly_loss_limit=0.03,   # 3%
    monthly_loss_limit=0.05,  # 5%
    max_position_size=0.10,   # 10%
    max_correlation=0.60,     # 60%
    max_leverage=1.0          # 100%
)

# 공격적 설정
aggressive_limits = RiskLimits(
    daily_loss_limit=0.03,    # 3%
    weekly_loss_limit=0.07,   # 7%
    monthly_loss_limit=0.15,  # 15%
    max_position_size=0.20,   # 20%
    max_correlation=0.80,     # 80%
    max_leverage=2.0          # 200%
)
```

---

## 🐛 트러블슈팅

### 문제: "No module named 'ta'"
**해결:**
```bash
pip install ta
```

### 문제: "analyze_market_condition not found"
**해결:** `analyze_market_conditions` (복수형) 사용

### 문제: "unexpected keyword argument"
**해결:** 이 문서의 올바른 예제 참고

---

## 📞 추가 지원

문제가 계속되면:
1. `requirements.txt` 재설치: `pip install -r requirements.txt`
2. `quick_test.py` 실행하여 각 모듈 확인
3. 이 문서의 예제 코드 복사하여 사용

**마지막 업데이트:** 2025-10-08

