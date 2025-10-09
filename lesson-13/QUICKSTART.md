# 🚀 빠른 시작 가이드

## 5분 안에 시작하기

### 1단계: 환경 설정 (1분)

```bash
# 가상환경 활성화
cd lesson-13
..\bot-env\Scripts\activate  # Windows
# source ../bot-env/bin/activate  # macOS/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 예제 실행 (3분)

```bash
# 전체 예제 실행
python example_usage.py
```

### 3단계: 결과 확인 (1분)

실행 결과로 다음을 확인할 수 있습니다:
- ✅ 파라미터 최적화 결과
- ✅ 시장 상황 분석
- ✅ 멀티 전략 성과
- ✅ 리스크 메트릭
- ✅ 성능 평가 지표

---

## 개별 모듈 테스트

### 파라미터 최적화만 실행

```python
from src.optimization import ParameterOptimizer, OptimizationMethod
import pandas as pd

# 데이터 로드
data = pd.read_csv('your_data.csv')

# 최적화 실행
optimizer = ParameterOptimizer()
result = optimizer.optimize_volatility_breakout_strategy(
    data=data,
    method=OptimizationMethod.GRID_SEARCH
)

print(f"최적 파라미터: {result.best_parameters}")
```

### 시장 상황 분석만 실행

```python
from src.optimization import MarketConditionAnalyzer

analyzer = MarketConditionAnalyzer()
condition = analyzer.analyze_market_condition(data)

print(f"시장 체제: {condition.market_regime.value}")
print(f"변동성: {condition.volatility_regime.value}")
```

### 리스크 관리만 실행

```python
from src.optimization import RiskOptimizer, PositionSizingMethod

risk_optimizer = RiskOptimizer(initial_capital=1_000_000)
position = risk_optimizer.calculate_position_size(
    current_price=50_000_000,
    volatility=0.03,
    method=PositionSizingMethod.KELLY_CRITERION
)

print(f"포지션 크기: {position.size:.4f}")
```

---

## 문제 해결

### 모듈을 찾을 수 없음
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows
```

### 패키지 설치 오류

**"No module named 'ta'" 오류:**
```bash
pip install ta
```

**empyrical/pyfolio 오류 발생 시:**
- 이미 quantstats로 대체됨
- requirements.txt 다시 설치: `pip install -r requirements.txt`

**참고:**
- `ta` = Technical Analysis Library (순수 Python, 설치 쉬움) ✅
- `TA-Lib` = C 라이브러리 (설치 어려움, 선택사항) ⚠️

### 최적화 너무 느림
```python
# Bayesian Optimization 사용
result = optimizer.optimize_volatility_breakout_strategy(
    data=data,
    method=OptimizationMethod.BAYESIAN_OPTIMIZATION  # 더 빠름
)
```

---

## 다음 단계

1. 📖 [README.md](./README.md) - 전체 문서 읽기
2. 📝 [lesson-13-prompts.md](./lesson-13-prompts.md) - 개발 가이드
3. 🔧 실제 데이터로 테스트하기
4. 📊 성능 결과 분석하기

---

## 주요 명령어

```bash
# 예제 실행
python example_usage.py

# 특정 모듈 테스트
python -c "from src.optimization import ParameterOptimizer; print('OK')"

# 패키지 버전 확인
pip list | grep pandas
```

---

**문의사항이 있으시면 README.md의 문제 해결 섹션을 참고하세요!**
