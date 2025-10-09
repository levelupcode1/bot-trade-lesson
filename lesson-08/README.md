# CryptoAutoTrader - 암호화폐 자동매매 시스템

## 📋 프로젝트 개요

**CryptoAutoTrader**는 업비트 거래소와 연동하여 24/7 자동으로 암호화폐 거래를 실행하는 시스템입니다.

### 주요 기능

- ✅ **실시간 가격 모니터링**: WebSocket을 통한 실시간 시세 수집
- ✅ **다양한 트레이딩 전략**: 변동성 돌파, 이동평균 교차, RSI 전략
- ✅ **리스크 관리**: 손절/익절, 포지션 크기 관리, 일일 손실 한도
- ✅ **텔레그램 알림**: 실시간 거래 알림 및 수익률 리포트
- ✅ **웹 인터페이스**: 실시간 모니터링 및 설정 관리
- ✅ **백테스팅**: 과거 데이터를 활용한 전략 검증

## 🚀 시작하기

### 시스템 요구사항

- Python 3.8 이상
- 최소 4GB RAM
- 최소 10GB 여유 디스크 공간
- 안정적인 인터넷 연결

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/crypto-auto-trader.git
cd crypto-auto-trader
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **설정 파일 구성**
```bash
cp config/config.yaml.example config/config.yaml
# config/config.yaml 파일을 편집하여 API 키 설정
```

### 설정

1. **업비트 API 키 발급**
   - [업비트](https://upbit.com) 로그인
   - 마이페이지 > Open API 관리
   - API 키 생성 (조회, 거래 권한 필요)

2. **텔레그램 봇 생성**
   - Telegram에서 [@BotFather](https://t.me/botfather) 검색
   - `/newbot` 명령으로 새 봇 생성
   - 봇 토큰 복사

3. **설정 파일 수정**
```yaml
# config/config.yaml
api:
  upbit:
    access_key: "YOUR_ACCESS_KEY"
    secret_key: "YOUR_SECRET_KEY"
    
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

## 📖 사용법

### 기본 실행

```bash
python main.py
```

### 웹 인터페이스 실행

```bash
python src/web/app.py
```

웹 브라우저에서 `http://localhost:5000` 접속

## 📁 프로젝트 구조

```
crypto-auto-trader/
├── src/                    # 소스 코드
│   ├── core/              # 핵심 모듈
│   ├── exchange/          # 거래소 연동
│   ├── strategy/          # 거래 전략
│   ├── risk/              # 리스크 관리
│   ├── notification/      # 알림 시스템
│   ├── database/          # 데이터베이스
│   ├── monitoring/        # 모니터링
│   ├── utils/             # 유틸리티
│   └── web/               # 웹 인터페이스
├── config/                # 설정 파일
├── tests/                 # 테스트 코드
├── docs/                  # 문서
├── logs/                  # 로그 파일
└── data/                  # 데이터 저장소
```

## 🔧 전략 설정

### 변동성 돌파 전략

```yaml
# config/strategies.yaml
volatility_breakout:
  enabled: true
  k_value: 0.5
  markets:
    - "KRW-BTC"
    - "KRW-ETH"
```

### 이동평균 교차 전략

```yaml
ma_crossover:
  enabled: true
  short_period: 5
  long_period: 20
  markets:
    - "KRW-BTC"
```

## ⚠️ 주의사항

1. **실제 자금 사용 전 충분한 테스트 필수**
2. **리스크 관리 규칙 반드시 설정**
3. **API 키 절대 노출 금지**
4. **정기적인 시스템 모니터링 필요**

## 📊 성과 지표

- **수익률**: 월간 목표 5-15%
- **최대 낙폭(MDD)**: 10% 이하
- **승률**: 60% 이상
- **샤프 비율**: 1.5 이상

## 🤝 기여하기

프로젝트에 기여하고 싶으시다면:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

- GitHub Issues: [이슈 등록](https://github.com/yourusername/crypto-auto-trader/issues)
- 텔레그램: [커뮤니티 채널](https://t.me/cryptoautotrader)

## 📚 참고 문서

- [PRD 문서](./PRD.md)
- [개발 체크리스트](./DEVELOPMENT_CHECKLIST.md)
- [API 문서](./docs/api/)
- [사용자 가이드](./docs/user_guide/)

---

**⚠️ 면책 조항**: 이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 암호화폐 거래는 높은 위험을 수반하며, 투자 손실에 대한 책임은 사용자 본인에게 있습니다.

