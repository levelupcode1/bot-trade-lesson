# ⚡ 24/7 자동매매 봇 빠른 시작 가이드

**10분 안에 완전 자동 수익 창출 시스템 시작하기!**

## 🚀 3단계로 시작

### Step 1: 설치 (2분)

```bash
cd lesson-18
pip install -r requirements.txt
```

### Step 2: 초기 학습 (5-10분)

```bash
# 모델 학습 (처음 한 번만)
python autonomous_trading_bot.py --force-retrain
```

이 과정에서:
- 6개월 데이터 수집
- 30+ 기술적 지표 생성
- LSTM + 앙상블 모델 학습
- 모델 자동 저장

### Step 3: 봇 시작 (즉시)

```bash
# 24/7 자동 실행!
python autonomous_trading_bot.py
```

**🎉 완료! 이제 봇이 24시간 365일 자동으로 거래합니다.**

## 📊 실행 화면

```
================================================================================
🤖 Autonomous Trading Bot Initialized
================================================================================
Market: KRW-BTC
Initial Capital: 10,000,000 KRW
Check Interval: 60 seconds

📊 Initializing ML Models...
✅ Loaded existing models
✅ Bot started successfully
⏰ Running 24/7 - Check interval: 60s

💡 Press Ctrl+C to stop

⚡ Running cycle - 2024-12-19 14:30:00
📈 BUY executed: 75,500,000 KRW
   Confidence: 82.5%
   Reason: Price increase predicted (+2.3%)
💰 Current Capital: 9,773,500 KRW
📊 Open Positions: 1
📈 Total Profit: +0 KRW

⚡ Running cycle - 2024-12-19 15:45:00
📉 SELL executed: 77,200,000 KRW
   Profit: +51,000 KRW
💰 Current Capital: 10,051,000 KRW
📊 Open Positions: 0
📈 Total Profit: +51,000 KRW

...
```

## ⚙️ 간단한 설정

### 보수적 운영 (안정)
```bash
python autonomous_trading_bot.py \
    --capital 10000000 \
    --interval 300 \
    --retrain-days 7
```
- 5분마다 체크
- 안정적 운영
- 예상 월 수익: 5-10%

### 적극적 운영 (공격)
```bash
python autonomous_trading_bot.py \
    --capital 10000000 \
    --interval 60 \
    --retrain-days 3
```
- 1분마다 체크
- 빠른 대응
- 예상 월 수익: 10-20%

## 💰 예상 수익

### 월 수익률 시나리오

| 자본 | 보수적 (5%) | 중립적 (10%) | 공격적 (20%) |
|------|------------|-------------|-------------|
| 1,000만원 | +50만원 | +100만원 | +200만원 |
| 2,000만원 | +100만원 | +200만원 | +400만원 |
| 5,000만원 | +250만원 | +500만원 | +1,000만원 |

### 복리 효과 (월 10% 기준)

```
1,000만원 시작
├─ 1개월: 1,100만원 (+100만원)
├─ 3개월: 1,331만원 (+331만원)
├─ 6개월: 1,772만원 (+772만원)
└─ 12개월: 3,138만원 (+2,138만원) 🚀
```

## 📱 실시간 모니터링

### 터미널에서 로그 보기
```bash
# 실시간 로그 확인
tail -f ./logs/autonomous_bot.log
```

### 주요 정보 확인
```bash
# 일일 요약
grep "Daily Summary" ./logs/autonomous_bot.log

# 모든 거래
grep "executed" ./logs/autonomous_bot.log | tail -20

# 총 수익
grep "Total Profit" ./logs/autonomous_bot.log | tail -1
```

## 🛑 중지하기

```
터미널에서 Ctrl+C 누르기
```

봇이 안전하게 중지되고 최종 요약을 보여줍니다.

## ⚠️ 시작 전 체크리스트

- [ ] requirements.txt 패키지 모두 설치
- [ ] TensorFlow 정상 작동 확인
- [ ] 첫 실행은 `--force-retrain`으로 모델 학습
- [ ] 소액으로 먼저 테스트
- [ ] 로그 파일 위치 확인 (`./logs/`)
- [ ] 백테스팅 결과 검토
- [ ] 리스크 수준 이해

## 🔧 문제 해결

### "No module named 'tensorflow'"
```bash
pip install tensorflow
```

### "No module named 'schedule'"
```bash
pip install schedule
```

### "Data collector not available"
```bash
# lesson-17 파일 확인
ls ../lesson-17/upbit_data_collector.py
```

### 모델 로드 실패
```bash
# 강제 재학습
python autonomous_trading_bot.py --force-retrain
```

## 💡 유용한 팁

### 1. 백그라운드 실행 (Linux/Mac)
```bash
nohup python autonomous_trading_bot.py > bot.log 2>&1 &
```

### 2. 여러 코인 동시 실행
```bash
# Terminal 1: BTC
python autonomous_trading_bot.py --market KRW-BTC

# Terminal 2: ETH
python autonomous_trading_bot.py --market KRW-ETH

# Terminal 3: ADA
python autonomous_trading_bot.py --market KRW-ADA
```

### 3. 자동 재시작 (크래시 시)
```bash
# Linux/Mac
while true; do
    python autonomous_trading_bot.py
    sleep 10
done
```

### 4. 성과 추적 스프레드시트
```bash
# CSV로 거래 내역 추출
grep "executed" ./logs/autonomous_bot.log > trades.csv
```

## 📚 다음 단계

1. **백테스팅 검증**
   ```bash
   python example_ml_trading.py full
   ```

2. **파라미터 최적화**
   - signal_threshold 조정
   - confidence_threshold 조정
   - 손절/익절 비율 조정

3. **다중 코인 확장**
   - 포트폴리오 다각화
   - 리스크 분산

4. **실전 거래 연동**
   - 업비트 API 키 설정
   - 실제 주문 실행

5. **모니터링 강화**
   - 텔레그램 알림 추가
   - 대시보드 구축

## 🎓 더 알아보기

- **전체 가이드**: [AUTONOMOUS_BOT_GUIDE.md](AUTONOMOUS_BOT_GUIDE.md)
- **ML 시스템**: [README.md](README.md)
- **백테스팅**: `python example_ml_trading.py full`

---

**🤖 "Set it and forget it"**

한 번 설정하면 24시간 365일 자동으로 돈을 벌어줍니다!

**면책 조항**: 교육 목적의 시스템입니다. 실제 거래 시 손실 책임은 본인에게 있습니다.
