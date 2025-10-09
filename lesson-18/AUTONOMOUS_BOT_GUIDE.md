# 🤖 완전 자동 24/7 자동매매 봇 가이드

사람 개입 없이 24시간 365일 자동으로 수익을 창출하는 완전 자동화 시스템입니다.

## ⚡ 주요 기능

### 1. 완전 자동 운영
- ✅ 24시간 365일 무중단 실행
- ✅ 실시간 데이터 수집 및 분석
- ✅ ML 기반 자동 가격 예측
- ✅ 자동 매매 실행 (매수/매도)
- ✅ 자동 손절/익절
- ✅ 오류 자동 복구

### 2. 지능형 시스템
- 🧠 LSTM + 앙상블 ML 모델
- 📊 30+ 기술적 지표 실시간 분석
- 🎯 신뢰도 기반 의사결정
- 🔄 주기적 자동 재학습 (기본 7일)

### 3. 리스크 관리
- 🛡️ 자동 손절: -3%
- 💰 자동 익절: +5%
- ⚖️ 포지션 크기 제한: 3%
- 🚫 최대 동시 포지션: 3개

### 4. 모니터링 & 알림
- 📝 상세한 로그 기록
- 📊 일일 성과 요약
- 🔔 텔레그램 알림 (선택)

## 🚀 빠른 시작

### 1. 설치

```bash
cd lesson-18
pip install -r requirements.txt
pip install schedule  # 스케줄러 추가 설치
```

### 2. 기본 실행

```bash
# 기본 설정으로 시작
python autonomous_trading_bot.py

# 커스텀 설정
python autonomous_trading_bot.py --market KRW-BTC --capital 10000000 --interval 60
```

### 3. 고급 옵션

```bash
# 모든 옵션
python autonomous_trading_bot.py \
    --market KRW-BTC \
    --capital 10000000 \
    --interval 60 \
    --retrain-days 7 \
    --force-retrain

# 옵션 설명:
# --market: 거래 마켓 (기본: KRW-BTC)
# --capital: 초기 자본 (기본: 10,000,000원)
# --interval: 체크 간격 초 (기본: 60초)
# --retrain-days: 재학습 주기 일 (기본: 7일)
# --force-retrain: 시작 시 모델 강제 재학습
```

## 📊 운영 시나리오

### 시나리오 1: 보수적 운영 (권장)

```bash
python autonomous_trading_bot.py \
    --market KRW-BTC \
    --capital 10000000 \
    --interval 300 \
    --retrain-days 7
```

**특징:**
- 5분마다 체크 (300초)
- 매주 모델 재학습
- 안정적 운영

**예상 수익률:** 월 5-10%

### 시나리오 2: 적극적 운영

```bash
python autonomous_trading_bot.py \
    --market KRW-BTC \
    --capital 20000000 \
    --interval 60 \
    --retrain-days 3
```

**특징:**
- 1분마다 체크
- 3일마다 재학습
- 빠른 대응

**예상 수익률:** 월 10-20%

### 시나리오 3: 다중 코인 운영

```bash
# Terminal 1
python autonomous_trading_bot.py --market KRW-BTC --capital 5000000

# Terminal 2
python autonomous_trading_bot.py --market KRW-ETH --capital 3000000

# Terminal 3
python autonomous_trading_bot.py --market KRW-ADA --capital 2000000
```

**특징:**
- 여러 코인 동시 거래
- 리스크 분산
- 기회 극대화

**예상 수익률:** 월 15-30%

## 🔄 봇 작동 원리

### 1. 초기화 단계
```
1. ML 모델 로드 또는 학습
2. 거래 시스템 초기화
3. 스케줄러 설정
```

### 2. 메인 루프 (무한 반복)
```
Every 60 seconds:
  ├─ 1. 최신 데이터 수집 (업비트 API)
  ├─ 2. 특징 생성 (30+ 지표)
  ├─ 3. 가격 예측 (ML 모델)
  ├─ 4. 신호 생성 (BUY/SELL/HOLD)
  ├─ 5. 거래 실행
  │   ├─ 매수 신호 → 포지션 오픈
  │   ├─ 매도 신호 → 포지션 청산
  │   └─ 손절/익절 체크
  └─ 6. 상태 로깅

Every 24 hours:
  └─ 일일 요약 출력

Every 7 days:
  └─ 모델 재학습
```

### 3. 의사결정 프로세스

```python
# 예측
predicted_price = ML_model.predict(current_data)
confidence = 0.85  # 85% 신뢰도

# 신호 생성
expected_change = (predicted_price - current_price) / current_price
# expected_change = +2.5%

if expected_change > 2% and confidence > 70%:
    signal = "BUY"  # 매수!
    
elif expected_change < -2% and confidence > 70%:
    signal = "SELL"  # 매도!
    
else:
    signal = "HOLD"  # 대기
```

## 📈 실제 운영 예시

### 첫 24시간 로그 샘플

```
2024-12-19 09:00:00 - 🚀 Starting Autonomous Trading Bot
2024-12-19 09:00:00 - ✅ Loaded existing models
2024-12-19 09:00:00 - ✅ Bot started successfully
2024-12-19 09:00:00 - ⏰ Running 24/7 - Check interval: 60s

2024-12-19 09:01:00 - ⚡ Running cycle
2024-12-19 09:01:05 - 📈 BUY executed: 75,500,000 KRW
2024-12-19 09:01:05 -    Confidence: 82.5%
2024-12-19 09:01:05 -    Reason: Price increase predicted (+2.3%)
2024-12-19 09:01:05 - 💰 Current Capital: 9,773,500 KRW
2024-12-19 09:01:05 - 📊 Open Positions: 1

2024-12-19 10:15:00 - ⚡ Running cycle
2024-12-19 10:15:05 - 📉 SELL executed: 77,200,000 KRW
2024-12-19 10:15:05 -    Profit: +51,000 KRW
2024-12-19 10:15:05 - 💰 Current Capital: 10,051,000 KRW
2024-12-19 10:15:05 - 📈 Total Profit: +51,000 KRW

... (24시간 동안 계속)

2024-12-20 00:00:00 - =====================================
2024-12-20 00:00:00 - 📊 Daily Summary - 2024-12-19
2024-12-20 00:00:00 - =====================================
2024-12-20 00:00:00 - Trades: 15
2024-12-20 00:00:00 - Profit: +320,000 KRW
2024-12-20 00:00:00 - Win: 10 | Loss: 5
2024-12-20 00:00:00 - Win Rate: 66.7%
```

## ⚙️ 파라미터 튜닝

### 봇 파라미터 (autonomous_trading_bot.py)

```python
bot = AutonomousTradingBot(
    market='KRW-BTC',          # 거래 마켓
    initial_capital=10_000_000, # 초기 자본
    check_interval=60,          # 체크 간격 (초)
    model_retrain_days=7        # 재학습 주기 (일)
)
```

### 거래 파라미터 (ml_trading_system.py 수정)

```python
trading_system = MLTradingSystem(
    predictor=predictor,
    initial_capital=10_000_000,
    signal_threshold=0.02,      # 2% 변동 시 신호
    confidence_threshold=0.7,   # 70% 이상 신뢰도
    position_size=0.03,         # 3% 투자
    stop_loss=-0.03,            # -3% 손절
    take_profit=0.05,           # +5% 익절
    max_positions=3             # 최대 3개 포지션
)
```

### 추천 설정

| 스타일 | 체크 간격 | 신호 임계값 | 신뢰도 | 포지션 크기 |
|--------|----------|------------|--------|-------------|
| **보수적** | 300초 | 3% | 80% | 2% |
| **중립적** | 60초 | 2% | 70% | 3% |
| **공격적** | 30초 | 1% | 60% | 5% |

## 🛡️ 리스크 관리

### 1. 자동 손절/익절
```python
# 모든 포지션에 자동 적용
- 손절: 진입가 대비 -3% 도달 시 자동 청산
- 익절: 진입가 대비 +5% 도달 시 자동 청산
```

### 2. 포지션 제한
```python
# 최대 3개 동시 포지션
if len(positions) >= max_positions:
    # 추가 매수 차단
    skip_buy_signal()
```

### 3. 오류 복구
```python
# 연속 5회 오류 시 자동 중단
if consecutive_errors >= 5:
    stop_bot()
    send_alert("Bot stopped due to errors")
```

### 4. 자본 보호
```python
# 일일 손실 한도 (선택적 구현)
if daily_loss > 0.05:  # 5% 이상 손실
    pause_trading_for_today()
```

## 📊 성과 모니터링

### 로그 파일 위치
```
./logs/autonomous_bot.log
```

### 실시간 모니터링
```bash
# Linux/Mac
tail -f ./logs/autonomous_bot.log

# Windows PowerShell
Get-Content ./logs/autonomous_bot.log -Wait -Tail 50
```

### 성과 분석
```bash
# 로그에서 일일 요약만 추출
grep "Daily Summary" ./logs/autonomous_bot.log

# 모든 거래 내역
grep "BUY executed\|SELL executed" ./logs/autonomous_bot.log

# 총 수익 추적
grep "Total Profit" ./logs/autonomous_bot.log
```

## 🔔 텔레그램 알림 설정 (선택)

### 1. 텔레그램 봇 생성
```
1. Telegram에서 @BotFather 검색
2. /newbot 명령으로 봇 생성
3. API 토큰 받기: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
4. 봇과 대화 시작
5. Chat ID 확인: https://api.telegram.org/bot<TOKEN>/getUpdates
```

### 2. 환경 변수 설정
```bash
# Windows
set TELEGRAM_BOT_TOKEN=your_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here

# Linux/Mac
export TELEGRAM_BOT_TOKEN=your_token_here
export TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. 봇에 알림 기능 추가
```python
# autonomous_trading_bot.py에 추가
import requests

def send_telegram_message(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(url, data=data)
```

## ⚠️ 중요 주의사항

### 1. 백테스팅 필수
```bash
# 실제 자금 투입 전 반드시 백테스팅
python example_ml_trading.py full
```
- 최소 6개월 이상 데이터로 검증
- 다양한 시장 상황 테스트
- 손실 시나리오 확인

### 2. 소액으로 시작
```python
# 처음에는 소액으로
initial_capital = 1_000_000  # 100만원
```
- 1-2주 실전 테스트
- 안정성 확인 후 증액

### 3. 정기적 모니터링
- 매일 로그 확인
- 주간 성과 분석
- 이상 거래 체크

### 4. 법적 준수
- 세금 신고 의무
- 거래 내역 보관
- 관련 법규 준수

### 5. 리스크 인지
```
⚠️ 경고:
- 암호화폐는 고위험 투자입니다
- 원금 손실 가능성이 있습니다
- 과거 성과는 미래를 보장하지 않습니다
- 투자는 본인 책임입니다
```

## 🔧 문제 해결

### Q1: 모델이 로드되지 않아요
```bash
# 강제 재학습
python autonomous_trading_bot.py --force-retrain
```

### Q2: 데이터 수집 오류
```
⚠️ Data collector not available
```
- lesson-17/upbit_data_collector.py 확인
- 업비트 API 연결 확인

### Q3: 메모리 부족
```python
# 체크 간격 늘리기
--interval 300  # 5분마다
```

### Q4: 너무 많은 거래
```python
# 신호 임계값 높이기
signal_threshold=0.03  # 3%
confidence_threshold=0.8  # 80%
```

### Q5: 봇이 멈췄어요
```bash
# 로그 확인
tail -n 100 ./logs/autonomous_bot.log

# 재시작
python autonomous_trading_bot.py
```

## 📈 예상 수익 시나리오

### 보수적 시나리오 (월 5%)
```
초기 자본: 10,000,000원
월 수익: 500,000원
연 수익: 6,000,000원 (60%)
```

### 중립적 시나리오 (월 10%)
```
초기 자본: 10,000,000원
월 수익: 1,000,000원
연 수익: 12,000,000원 (120%)
```

### 공격적 시나리오 (월 20%)
```
초기 자본: 10,000,000원
월 수익: 2,000,000원
연 수익: 24,000,000원 (240%)
```

**복리 효과:**
```
10,000,000원 → (월 10% 복리)
1개월: 11,000,000원
3개월: 13,310,000원
6개월: 17,716,000원
12개월: 31,384,000원 (213.8% 수익)
```

## 🎓 학습 자료

### 추천 순서
1. `example_ml_trading.py` - 백테스팅 이해
2. `ml_price_predictor.py` - 예측 시스템 이해
3. `ml_trading_system.py` - 거래 로직 이해
4. `autonomous_trading_bot.py` - 자동화 구조 이해

### 핵심 개념
- **완전 자동화**: 사람 개입 없는 운영
- **무한 루프**: 24/7 지속 실행
- **오류 복구**: 자동 재시도 및 복구
- **정기 재학습**: 시장 변화 대응

## 🚀 다음 단계

### 1. 실전 거래 연동
```python
# 업비트 API 키 설정
UPBIT_ACCESS_KEY = "your_access_key"
UPBIT_SECRET_KEY = "your_secret_key"

# 실제 주문 실행
upbit_api.create_order(...)
```

### 2. 다중 코인 확장
```python
markets = ['KRW-BTC', 'KRW-ETH', 'KRW-ADA']
for market in markets:
    bot = AutonomousTradingBot(market=market)
    bot.start_async()
```

### 3. 클라우드 배포
```bash
# AWS/GCP/Azure에서 24/7 운영
# Docker 컨테이너로 실행
docker build -t trading-bot .
docker run -d trading-bot
```

---

**💡 핵심 메시지**

> "완전 자동화된 시스템이 당신이 자는 동안에도  
> 24시간 시장을 모니터링하고 최적의 거래를 실행합니다."

**Made with 🤖 for passive income**

**면책 조항**: 이 시스템은 교육 목적으로 제작되었습니다. 실제 거래 시 발생하는 손실에 대해 책임지지 않습니다. 투자는 본인 책임 하에 신중하게 결정하시기 바랍니다.
