# 18차시: ML/DL 기반 가격 예측 자동매매 시스템

업비트 API 실시간 데이터를 활용한 머신러닝/딥러닝 기반 암호화폐 가격 예측 및 자동매매 시스템입니다.

## 🎯 시스템 개요

### 핵심 기능
1. **데이터 파이프라인**: 업비트 API 실시간 데이터 수집 및 전처리
2. **특징 엔지니어링**: 30-40개 기술적 지표 생성
3. **LSTM 모델**: 시계열 딥러닝 가격 예측
4. **앙상블 모델**: Random Forest + XGBoost
5. **통합 예측**: 다중 모델 앙상블 예측
6. **자동매매**: 예측 기반 매매 신호 생성 및 백테스팅

### 시스템 구조
```
[업비트 API] → [데이터 수집] → [특징 생성] → [모델 학습]
                                              ↓
[백테스팅] ← [거래 시스템] ← [매매 신호] ← [가격 예측]
```

## 📁 프로젝트 구조

```
lesson-18/
├── data_pipeline.py              # 데이터 수집 및 전처리
├── feature_engineering.py        # 기술적 지표 생성
├── ml_price_predictor.py         # 통합 ML 예측 시스템
├── ml_trading_system.py          # 자동매매 시스템
├── example_ml_trading.py         # 실행 예제
├── autonomous_trading_bot.py     # 🤖 24/7 자동매매 봇 (NEW!)
├── models/
│   ├── __init__.py
│   ├── lstm_model.py             # LSTM 딥러닝 모델
│   └── ensemble_model.py         # 앙상블 ML 모델
├── requirements.txt              # 필요 패키지
├── README.md                     # 문서 (이 파일)
└── AUTONOMOUS_BOT_GUIDE.md       # 🤖 자동매매 봇 가이드 (NEW!)
```

## 🚀 설치 및 설정

### 1. 필요 패키지 설치

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 필요 패키지
- **데이터 처리**: pandas, numpy
- **머신러닝**: scikit-learn, xgboost
- **딥러닝**: tensorflow (CPU 버전)
- **기술적 지표**: pandas-ta
- **시각화**: matplotlib, seaborn
- **API 통신**: requests

## 📊 사용 방법

### 1. 전체 플로우 실행

```bash
python example_ml_trading.py full
```

**실행 단계:**
1. 시스템 초기화
2. 데이터 수집 (업비트 API)
3. 특징 생성 (30-40개 기술적 지표)
4. 모델 학습 (LSTM + 앙상블)
5. 모델 평가
6. 가격 예측
7. 백테스팅
8. 결과 시각화
9. 모델 저장

### 2. 실시간 예측

```bash
python example_ml_trading.py realtime
```

저장된 모델을 로드하여 최신 데이터로 예측을 수행합니다.

### 3. 🤖 24/7 완전 자동 매매 봇 (NEW!)

```bash
# 기본 실행 - 사람 개입 없이 24시간 자동 운영
python autonomous_trading_bot.py

# 커스텀 설정
python autonomous_trading_bot.py \
    --market KRW-BTC \
    --capital 10000000 \
    --interval 60 \
    --retrain-days 7
```

**자세한 사용법은 [AUTONOMOUS_BOT_GUIDE.md](AUTONOMOUS_BOT_GUIDE.md) 참조**

### 4. 코드로 사용

```python
from ml_price_predictor import MLPricePredictor
from ml_trading_system import MLTradingSystem

# 1. 예측 시스템 초기화
predictor = MLPricePredictor(
    market='KRW-BTC',
    sequence_length=60,
    forecast_horizon=1
)

# 2. 데이터 준비
(X_train_lstm, X_train_ml, X_val_lstm, X_val_ml,
 X_test_lstm, X_test_ml, y_train, y_val, y_test) = predictor.prepare_data(
    interval='60',  # 1시간봉
    days=180        # 6개월
)

# 3. 모델 학습
predictor.train_models(
    X_train_lstm, X_train_ml,
    X_val_lstm, X_val_ml,
    y_train, y_val,
    lstm_epochs=50,
    lstm_batch_size=32
)

# 4. 예측
result = predictor.predict(X_test_lstm, X_test_ml)
predictions = result['predictions']
confidence = result['confidence']

# 5. 자동매매 백테스팅
trading_system = MLTradingSystem(
    predictor=predictor,
    initial_capital=10_000_000
)

backtest_results = trading_system.backtest(
    X_test_lstm, X_test_ml, prices, timestamps
)
```

## 🧠 모델 아키텍처

### 1. LSTM 딥러닝 모델
```python
입력: (batch_size, 60, n_features)
  ↓
LSTM Layer 1 (128 units) + BatchNorm + Dropout
  ↓
LSTM Layer 2 (64 units) + BatchNorm + Dropout
  ↓
LSTM Layer 3 (32 units) + BatchNorm + Dropout
  ↓
Dense Layer 1 (32 units, ReLU) + Dropout
  ↓
Dense Layer 2 (16 units, ReLU)
  ↓
Output Layer (1 unit) → 가격 예측
```

**특징:**
- 시계열 패턴 학습
- 과거 60 타임스텝 기반 예측
- Dropout으로 과적합 방지
- 조기 종료 및 학습률 스케줄링

### 2. 앙상블 ML 모델

**Random Forest:**
- n_estimators: 100
- max_depth: 10
- 빠른 학습 및 안정적 예측

**XGBoost:**
- n_estimators: 100
- max_depth: 6
- learning_rate: 0.1
- 높은 정확도 및 특징 중요도 분석

**앙상블:**
- LSTM: 60% 가중치
- Random Forest: 20% 가중치
- XGBoost: 20% 가중치

### 3. 특징 엔지니어링

**생성 특징 (30-40개):**

| 카테고리 | 특징 | 개수 |
|---------|------|------|
| 가격 | 수익률, 변화율, 고저비율, 이동평균 | 12 |
| 기술지표 | RSI, MACD, Bollinger Bands, ATR, Stochastic | 15 |
| 거래량 | 거래량 비율, OBV, VWAP | 8 |
| 시간 | 요일, 시간, 주기성 인코딩 | 6 |
| 상호작용 | RSI-BB, MACD-RSI, Volume-Return | 3 |

## 📈 성능 지표

### 예측 정확도
- **RMSE**: Root Mean Squared Error
- **MAE**: Mean Absolute Error
- **MAPE**: Mean Absolute Percentage Error
- **방향 정확도**: 상승/하락 방향 맞춤률

### 백테스팅 지표
- **총 수익률**: 초기 자본 대비 수익
- **승률**: 수익 거래 비율
- **손익비**: 평균 수익 / 평균 손실
- **최대 낙폭 (MDD)**: 최고점 대비 최대 하락
- **샤프 비율**: 위험 대비 수익률

## ⚙️ 주요 파라미터

### 데이터 파라미터
```python
market = 'KRW-BTC'          # 거래 마켓
interval = '60'             # 캔들 간격 (분)
days = 180                  # 수집 기간 (일)
sequence_length = 60        # LSTM 시퀀스 길이
forecast_horizon = 1        # 예측 시점 (시간 후)
```

### 모델 파라미터
```python
# LSTM
lstm_units = [128, 64, 32]  # 레이어별 유닛 수
dropout_rate = 0.2          # 드롭아웃 비율
learning_rate = 0.001       # 학습률
epochs = 50                 # 에폭 수
batch_size = 32             # 배치 크기

# 앙상블
rf_n_estimators = 100       # Random Forest 트리 수
xgb_n_estimators = 100      # XGBoost 트리 수
```

### 거래 파라미터
```python
initial_capital = 10_000_000    # 초기 자본 (원)
signal_threshold = 0.02         # 신호 임계값 (2%)
confidence_threshold = 0.7      # 신뢰도 임계값 (70%)
position_size = 0.03            # 포지션 크기 (3%)
stop_loss = -0.03               # 손절 (-3%)
take_profit = 0.05              # 익절 (+5%)
max_positions = 3               # 최대 포지션 수
```

## 📊 백테스팅 예시

### 시나리오: BTC 6개월 데이터

**설정:**
- 초기 자본: 1,000만원
- 기간: 2024년 1월 ~ 6월
- 전략: ML 예측 기반 매매

**결과 예시:**
```
💰 수익 지표:
  초기 자본: 10,000,000원
  최종 자본: 11,250,000원
  총 수익: +1,250,000원 (+12.5%)

📊 거래 통계:
  총 거래 수: 45회
  승리: 28회
  손실: 17회
  승률: 62.2%

📈 성과 지표:
  평균 수익: +85,000원
  평균 손실: -45,000원
  손익비: 1.89
  최대 낙폭: -8.5%
  샤프 비율: 1.65
```

## 🎨 결과 시각화

실행 시 자동으로 다음 그래프가 생성됩니다:

1. **가격 예측 vs 실제**: 예측 정확도 시각화
2. **예측 오차 분포**: 오차 패턴 분석
3. **누적 수익률**: 시간에 따른 수익 변화
4. **거래 통계**: 승률 및 거래 분포

저장 위치: `./results/backtest_results.png`

## ⚠️ 주의사항

### 1. 프로토타입 수준
- 실제 자금 투입 전 충분한 검증 필요
- 다양한 시장 상황에서 테스트
- 최소 1년 이상 데이터로 백테스팅

### 2. 과적합 방지
- 검증 데이터로 모델 평가
- 조기 종료 사용
- 드롭아웃 및 정규화 적용

### 3. 리스크 관리
- 손절/익절 철저히 준수
- 최대 포지션 크기 제한
- 일일 손실 한도 설정

### 4. API 제한
- 업비트 API: 초당 10회 요청 제한
- 과도한 요청 시 IP 차단 가능
- 적절한 요청 간격 유지

### 5. 모델 재학습
- 매주 또는 매월 재학습 권장
- 시장 변화에 따라 모델 성능 저하 가능
- 최신 데이터로 지속적 업데이트

## 🔧 커스터마이징

### 1. 새로운 특징 추가

```python
# feature_engineering.py 수정
def create_custom_features(self, df):
    # 사용자 정의 특징 추가
    df['custom_indicator'] = ...
    return df
```

### 2. 모델 구조 변경

```python
# models/lstm_model.py 수정
lstm_units = [256, 128, 64, 32]  # 더 깊은 네트워크
dropout_rate = 0.3               # 드롭아웃 증가
```

### 3. 거래 전략 조정

```python
# ml_trading_system.py 수정
signal_threshold = 0.01      # 더 민감한 신호
confidence_threshold = 0.8   # 더 높은 신뢰도 요구
```

## 📚 참고 자료

### 머신러닝/딥러닝
- [TensorFlow 공식 문서](https://www.tensorflow.org/)
- [Scikit-learn 문서](https://scikit-learn.org/)
- [XGBoost 문서](https://xgboost.readthedocs.io/)

### 기술적 분석
- [TA-Lib 문서](https://ta-lib.org/)
- [pandas-ta 문서](https://github.com/twopirllc/pandas-ta)

### 암호화폐 거래
- [업비트 API 문서](https://docs.upbit.com/)
- [암호화폐 투자 가이드](https://www.investopedia.com/cryptocurrency-4427699)

## 🐛 문제 해결

### TensorFlow 설치 오류
```bash
# CPU 버전 설치
pip install tensorflow

# GPU 버전 (CUDA 필요)
pip install tensorflow-gpu
```

### pandas-ta 오류
```bash
# 대체: 직접 기술적 지표 계산
# feature_engineering.py의 calculate_* 메서드 사용
```

### 메모리 부족
```python
# 배치 크기 줄이기
batch_size = 16

# 시퀀스 길이 줄이기
sequence_length = 30
```

## 🚀 다음 단계

1. **실시간 거래 연동**: 실제 주문 API 통합
2. **멀티 코인**: 여러 코인 동시 예측
3. **강화학습**: DQN/PPO 기반 학습
4. **감정 분석**: 뉴스/소셜미디어 데이터 통합
5. **클라우드 배포**: AWS/GCP에서 24/7 운영

## 📞 문의 및 기여

- **버그 리포트**: GitHub Issues
- **기능 제안**: Pull Request
- **질문**: Discussions

---

**⚡ 핵심 메시지**

> "머신러닝과 딥러닝을 활용한 데이터 기반 의사결정으로  
> 감정을 배제하고 객관적인 자동매매를 실현합니다."

---

**Made with 💡 for algorithmic traders**

**면책 조항**: 이 시스템은 교육 목적으로 제작되었습니다. 실제 거래에 사용 시 발생하는 손실에 대해 책임지지 않습니다. 투자는 본인 책임 하에 신중하게 결정하시기 바랍니다.

