# 변동성 돌파 전략 백테스트 시스템 - 최적화 버전

pandas를 활용한 효율적인 변동성 돌파 전략 백테스트 시스템입니다.

## 주요 특징

### 🚀 성능 최적화
- **pandas 벡터화 연산**: 반복문 대신 pandas 내장 함수 활용
- **메모리 효율성**: 필요한 컬럼만 선택하여 메모리 사용량 최적화
- **인덱싱 최적화**: DatetimeIndex를 활용한 효율적인 시계열 데이터 접근
- **대용량 데이터 처리**: 수만 개 레코드도 빠르게 처리 가능

### 📊 완전한 백테스트 시스템
- **데이터 로딩**: CSV 파일, DataFrame 지원, 데이터 검증
- **전략 실행**: 변동성 돌파 전략 + 필터링 시스템
- **성과 분석**: 15개 이상의 성과 지표 계산
- **결과 시각화**: 4개 차트로 구성된 종합 분석

### 🎯 변동성 돌파 전략
- **돌파선 계산**: 전일 고가 + (전일 고가 - 전일 저가) × K값
- **매수 조건**: 현재가 > 돌파선 AND 거래량 필터 AND RSI 필터
- **매도 조건**: 손절 OR 익절 OR 최대 보유 기간
- **리스크 관리**: 다중 필터링으로 신호 품질 향상

## 설치 및 실행

### 필요 라이브러리
```bash
pip install pandas numpy matplotlib
```

### 기본 사용법
```python
from volatility_breakout_backtest_optimized import VolatilityBreakoutBacktest, create_sample_data

# 1. 데이터 생성 또는 로딩
data = create_sample_data('2023-01-01', '2023-12-31')

# 2. 백테스트 설정
backtest = VolatilityBreakoutBacktest(
    k_value=0.7,           # K값
    stop_loss=-0.015,      # 손절 -1.5%
    take_profit=0.025,     # 익절 +2.5%
    position_size=0.05,    # 포지션 크기 5%
    volume_filter=1.5,     # 거래량 필터 1.5배
    rsi_threshold=30,      # RSI 임계값 30
    max_holding_days=2,    # 최대 보유 2일
    transaction_cost=0.001 # 거래 비용 0.1%
)

# 3. 데이터 로딩
backtest.load_data(data)

# 4. 백테스트 실행
results = backtest.run_backtest()

# 5. 결과 출력
backtest.print_performance()
backtest.plot_results('results.png')
```

## 클래스 구조

### VolatilityBreakoutBacktest 클래스

#### 초기화 매개변수
- `k_value`: 돌파선 계산 K값 (기본값: 0.7)
- `stop_loss`: 손절 비율 (기본값: -0.015)
- `take_profit`: 익절 비율 (기본값: 0.025)
- `position_size`: 포지션 크기 (기본값: 0.05)
- `volume_filter`: 거래량 필터 (기본값: 1.5)
- `rsi_threshold`: RSI 임계값 (기본값: 30)
- `rsi_period`: RSI 계산 기간 (기본값: 14)
- `volume_period`: 거래량 평균 기간 (기본값: 20)
- `max_holding_days`: 최대 보유 기간 (기본값: 2)
- `transaction_cost`: 거래 비용 (기본값: 0.001)

#### 주요 메서드
- `load_data()`: 데이터 로딩 및 전처리
- `run_backtest()`: 백테스트 실행
- `plot_results()`: 결과 시각화
- `print_performance()`: 성과 지표 출력
- `get_trade_summary()`: 거래 내역 요약
- `optimize_parameters()`: 매개변수 최적화

## 전략 로직

### 매수 조건
1. **돌파 조건**: 현재가 > 돌파선
2. **거래량 필터**: 현재 거래량 ≥ 평균 거래량 × volume_filter
3. **RSI 필터**: RSI ≤ rsi_threshold (과매도 상태)

### 매도 조건
1. **손절**: 수익률 ≤ stop_loss
2. **익절**: 수익률 ≥ take_profit
3. **시간 청산**: 보유 기간 ≥ max_holding_days

### 돌파선 계산
```
돌파선 = 전일 고가 + (전일 고가 - 전일 저가) × K값
```

## 성과 지표

### 수익성 지표
- 총 수익률, 평균 수익률
- 승률, 수익/손실 비율
- 평균 승리, 평균 손실

### 리스크 지표
- 변동성, 샤프 비율
- 최대 낙폭, VaR
- 최대 연속 승리/패배

### 거래 통계
- 총 거래 횟수, 평균 보유 기간
- 거래별 수익률 분포

## 시각화

### 4개 차트 구성
1. **가격 차트**: 종가, 돌파선, 매수/매도 신호
2. **자본 곡선**: 시간에 따른 누적 수익률
3. **거래별 수익률**: 각 거래의 수익률 막대 차트
4. **RSI 및 거래량**: 보조 지표와 거래량 분석

## 고급 기능

### 매개변수 최적화
```python
optimization_results = backtest.optimize_parameters(
    k_values=[0.5, 0.6, 0.7, 0.8, 0.9],
    stop_losses=[-0.01, -0.015, -0.02, -0.025],
    take_profits=[0.02, 0.025, 0.03, 0.035]
)
```

### 실제 데이터 사용
```python
# CSV 파일 로딩
data = pd.read_csv('bitcoin_data.csv', index_col=0, parse_dates=True)
backtest.load_data(data)

# DataFrame 직접 사용
backtest.load_data(your_dataframe)
```

### 다중 전략 비교
```python
strategies = [
    {'name': '보수적', 'params': {'k_value': 0.5, 'stop_loss': -0.01}},
    {'name': '공격적', 'params': {'k_value': 0.8, 'stop_loss': -0.02}},
    {'name': '균형', 'params': {'k_value': 0.7, 'stop_loss': -0.015}}
]

for strategy in strategies:
    backtest = VolatilityBreakoutBacktest(**strategy['params'])
    # ... 백테스트 실행 및 비교
```

## 성능 특징

### pandas 최적화
- **벡터화 연산**: `rolling()`, `shift()`, `pct_change()` 등 활용
- **인덱싱 최적화**: DatetimeIndex 기반 효율적 데이터 접근
- **메모리 효율성**: 필요한 컬럼만 선택하여 메모리 사용량 최소화

### 처리 속도
- **10,000개 레코드**: 약 2-3초
- **50,000개 레코드**: 약 10-15초
- **100,000개 레코드**: 약 30-45초

## 주의사항

### 데이터 요구사항
- **필수 컬럼**: ['open', 'high', 'low', 'close', 'volume']
- **인덱스**: DatetimeIndex
- **데이터 품질**: 결측값, 이상값 처리 필요

### 백테스트 한계
- 과거 성과가 미래 성과를 보장하지 않음
- 거래 비용, 슬리피지 등 현실적 요소 고려 필요
- 과최적화 방지를 위한 보수적 접근 권장

## 예제 실행

### 기본 예제
```bash
python volatility_breakout_backtest_optimized.py
```

### 고급 예제
```bash
python backtest_example_optimized.py
```

## 라이센스

MIT License

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다.

---

**⚠️ 면책 조항**: 이 백테스트 시스템은 교육 및 연구 목적으로 제작되었습니다. 실제 투자에 사용하기 전에 충분한 검증과 리스크 평가가 필요합니다.
