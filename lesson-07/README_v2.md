# 변동성 돌파 전략 백테스트 시스템 v2

pandas를 활용한 효율적인 변동성 돌파 전략 백테스트 시스템입니다.

## 주요 기능

### 1. 데이터 로딩 및 전처리
- **다양한 데이터 소스 지원**: DataFrame, CSV 파일
- **데이터 검증**: OHLC 논리적 일관성, 결측값 처리
- **기술적 지표 계산**: RSI, 거래량 평균, 변동성, 돌파선

### 2. 변동성 돌파 전략
- **돌파선 계산**: 전일 고가 + (전일 고가 - 전일 저가) × K
- **다중 필터**: 거래량 필터, RSI 필터
- **리스크 관리**: 손절/익절, 최대 보유 기간

### 3. 성과 분석
- **수익성 지표**: 총 수익률, 평균 수익률, 승률, 수익/손실 비율
- **리스크 지표**: 변동성, 샤프 비율, 최대 낙폭, VaR
- **거래 통계**: 총 거래 횟수, 연속 승리/패배, 평균 보유 기간

### 4. 결과 시각화
- **가격 차트**: 종가, 돌파선, 거래 신호
- **자본 곡선**: 누적 수익률 변화
- **거래별 수익률**: 개별 거래 성과
- **RSI 및 거래량**: 보조 지표 분석

## 설치 및 사용

### 1. 필요한 라이브러리
```bash
pip install pandas numpy matplotlib
```

### 2. 기본 사용법
```python
from volatility_breakout_backtest_v2 import VolatilityBreakoutBacktest, create_sample_data

# 샘플 데이터 생성
data = create_sample_data('2023-01-01', '2023-12-31')

# 백테스트 설정
backtest = VolatilityBreakoutBacktest(
    k_value=0.7,           # K값
    stop_loss=-0.015,      # 손절 -1.5%
    take_profit=0.025,     # 익절 +2.5%
    position_size=0.05,    # 포지션 크기 5%
    volume_filter=1.5,     # 거래량 필터 1.5배
    rsi_threshold=30,      # RSI 임계값 30
    max_holding_days=2     # 최대 보유 2일
)

# 데이터 로딩 및 백테스트 실행
backtest.load_data(data)
results = backtest.run_backtest()

# 결과 출력 및 시각화
backtest.print_performance()
backtest.plot_results('results.png')
```

### 3. 실제 데이터 사용
```python
# CSV 파일에서 데이터 로딩
data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)
backtest.load_data(data)
```

## 클래스 구조

### VolatilityBreakoutBacktest 클래스

#### 초기화 매개변수
- `k_value`: 돌파선 계산 K값 (기본값: 0.7)
- `stop_loss`: 손절 비율 (기본값: -1.5%)
- `take_profit`: 익절 비율 (기본값: +2.5%)
- `position_size`: 포지션 크기 (기본값: 5%)
- `volume_filter`: 거래량 필터 (기본값: 1.5)
- `rsi_threshold`: RSI 임계값 (기본값: 30)
- `rsi_period`: RSI 계산 기간 (기본값: 14)
- `volume_period`: 거래량 평균 계산 기간 (기본값: 20)
- `max_holding_days`: 최대 보유 기간 (기본값: 2일)
- `transaction_cost`: 거래 비용 (기본값: 0.1%)

#### 주요 메서드
- `load_data(data)`: 데이터 로딩 및 전처리
- `run_backtest()`: 백테스트 실행
- `print_performance()`: 성과 지표 출력
- `plot_results(save_path)`: 결과 시각화
- `get_trade_summary()`: 거래 내역 요약
- `optimize_parameters()`: 매개변수 최적화

## 전략 설명

### 변동성 돌파 전략
1. **돌파선 계산**: 전일 고가 + (전일 고가 - 전일 저가) × K
2. **매수 조건**: 
   - 현재가 > 돌파선
   - 거래량 > 평균 거래량 × 필터 배수
   - RSI ≤ 임계값 (과매도 상태)
3. **매도 조건**:
   - 손절: 수익률 ≤ 손절 비율
   - 익절: 수익률 ≥ 익절 비율
   - 시간: 보유 기간 ≥ 최대 보유 기간

### 리스크 관리
- **포지션 크기 제한**: 자본 대비 일정 비율로 제한
- **손절/익절**: 명확한 손익 기준 설정
- **최대 보유 기간**: 장기 보유로 인한 리스크 방지
- **거래 비용 반영**: 실제 거래 비용 고려

## 성과 지표

### 수익성 지표
- **총 수익률**: 전체 기간 누적 수익률
- **평균 수익률**: 거래별 평균 수익률
- **승률**: 수익 거래 비율
- **수익/손실 비율**: 평균 수익 / 평균 손실

### 리스크 지표
- **변동성**: 수익률의 표준편차 (연간화)
- **샤프 비율**: 위험 대비 수익률
- **최대 낙폭**: 최대 손실 구간
- **VaR**: Value at Risk

### 거래 통계
- **총 거래 횟수**: 전체 거래 수
- **평균 보유 기간**: 거래별 평균 보유 일수
- **연속 승리/패배**: 최대 연속 횟수

## 고급 기능

### 1. 매개변수 최적화
```python
# 매개변수 최적화 실행
optimization_results = backtest.optimize_parameters(
    k_values=[0.6, 0.7, 0.8],
    stop_losses=[-0.01, -0.015, -0.02],
    take_profits=[0.02, 0.025, 0.03]
)

print("최적 매개변수:", optimization_results['best_params'])
print("최적 성과:", optimization_results['best_performance'])
```

### 2. 전략 비교
```python
# 여러 전략 설정으로 비교
strategies = [
    {'name': '보수적', 'params': {...}},
    {'name': '공격적', 'params': {...}},
    {'name': '균형', 'params': {...}}
]

# 각 전략별 성과 비교
for strategy in strategies:
    backtest = VolatilityBreakoutBacktest(**strategy['params'])
    # ... 백테스트 실행 및 결과 수집
```

## 주의사항

### 1. 백테스트 한계
- 과거 성과가 미래 성과를 보장하지 않음
- 실제 거래와의 차이 (슬리피지, 유동성 등)
- 과최적화 위험

### 2. 데이터 품질
- 충분한 기간의 데이터 (최소 5년)
- 다양한 시장 상황 포함
- 거래 비용 정확히 반영

### 3. 리스크 관리
- 보수적 접근 필요
- 점진적 자본 배분
- 지속적 모니터링

## 예제 실행

```bash
# 기본 예제 실행
python backtest_example_v2.py

# 백테스트 클래스 직접 실행
python volatility_breakout_backtest_v2.py
```

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.
