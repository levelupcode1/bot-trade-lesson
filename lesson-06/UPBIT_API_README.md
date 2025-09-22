# 업비트 API 통합 클래스

업비트 API를 쉽게 사용할 수 있는 포괄적인 Python 클래스입니다.

## 🚀 주요 기능

### 📊 시장 데이터 조회 (인증 불필요)
- 전체 마켓 코드 조회
- 현재가 정보 조회
- 캔들(차트) 데이터 조회
- 호가 정보 조회
- 체결 내역 조회

### 💰 계좌 조회 (인증 필요)
- 전체 계좌 조회
- 주문 리스트 조회
- 개별 주문 조회
- 잔고 조회

### 📋 주문 실행 (인증 필요)
- 주문 생성 (매수/매도)
- 주문 취소
- 다양한 주문 타입 지원

### 🛡️ 안전 기능
- JWT 토큰 기반 인증
- 자동 재시도 및 오류 처리
- 요청 제한 관리
- 상세한 로깅

## 📦 설치

```bash
pip install requests PyJWT python-dotenv
```

## ⚙️ 설정

### 1. 환경 변수 설정

`.env` 파일을 생성하고 API 키를 설정하세요:

```bash
# .env 파일
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here
```

### 2. API 키 생성

1. [업비트 개발자 센터](https://upbit.com/mypage/open_api_management) 접속
2. API 키 생성
3. 필요한 권한 설정:
   - 자산 조회
   - 주문 조회
   - 주문하기 (실제 거래 시)

## 🎯 사용법

### 기본 사용법

```python
from upbit_api_integration import UpbitAPI

# API 클라이언트 생성
api = UpbitAPI()

# 시장 데이터 조회 (인증 불필요)
markets = api.get_markets()
tickers = api.get_ticker(['KRW-BTC', 'KRW-ETH'])
candles = api.get_candles('KRW-BTC', count=100, unit='days')
```

### 인증이 필요한 기능

```python
# API 키와 함께 생성
api = UpbitAPI(
    access_key='your_access_key',
    secret_key='your_secret_key'
)

# 계좌 조회
accounts = api.get_accounts()
orders = api.get_orders()

# 주문 생성 (주의: 실제 거래)
order = api.create_order(
    market='KRW-BTC',
    side='bid',  # 매수
    volume='0.001',
    price='160000000',
    ord_type='limit'
)
```

### 편의 메서드

```python
# 현재가 조회
price = api.get_current_price('KRW-BTC')

# 특정 통화 잔고 조회
balance = api.get_balance('KRW')

# 마켓 요약 정보
summary = api.get_market_summary(['KRW-BTC', 'KRW-ETH'])
```

## 📚 API 메서드 목록

### 시장 데이터 조회

| 메서드 | 설명 | 인증 필요 |
|--------|------|-----------|
| `get_markets()` | 전체 마켓 코드 조회 | ❌ |
| `get_ticker(markets)` | 현재가 정보 조회 | ❌ |
| `get_candles(market, count, unit)` | 캔들 데이터 조회 | ❌ |
| `get_orderbook(markets)` | 호가 정보 조회 | ❌ |
| `get_trades_ticks(market, count)` | 체결 내역 조회 | ❌ |

### 계좌 조회

| 메서드 | 설명 | 인증 필요 |
|--------|------|-----------|
| `get_accounts()` | 전체 계좌 조회 | ✅ |
| `get_orders(market, state)` | 주문 리스트 조회 | ✅ |
| `get_order_detail(uuid)` | 개별 주문 조회 | ✅ |

### 주문 실행

| 메서드 | 설명 | 인증 필요 |
|--------|------|-----------|
| `create_order(market, side, volume, price)` | 주문 생성 | ✅ |
| `cancel_order(uuid)` | 주문 취소 | ✅ |

### 편의 메서드

| 메서드 | 설명 | 인증 필요 |
|--------|------|-----------|
| `get_balance(currency)` | 잔고 조회 | ✅ |
| `get_current_price(market)` | 현재가 조회 | ❌ |
| `get_market_summary(markets)` | 마켓 요약 정보 | ❌ |
| `get_request_stats()` | 요청 통계 | ❌ |

## 🔧 고급 설정

### 커스텀 설정

```python
api = UpbitAPI(
    access_key='your_key',
    secret_key='your_secret',
    base_url='https://api.upbit.com',
    timeout=30,
    max_retries=3
)
```

### 요청 제한 관리

클래스는 자동으로 요청 제한을 관리합니다:
- 요청 간 최소 간격: 0.1초
- 자동 재시도: 최대 3회
- 지수 백오프 적용

## 📝 로깅

모든 API 요청과 응답이 `upbit_api.log` 파일에 기록됩니다:

```
2025-09-20 23:30:15 - upbit_api_integration - INFO - 마켓 코드 조회 완료: 300개
2025-09-20 23:30:16 - upbit_api_integration - INFO - 현재가 정보 조회 완료: 5개
```

## ⚠️ 주의사항

### 보안
- API 키를 코드에 직접 입력하지 마세요
- 환경 변수나 별도 설정 파일을 사용하세요
- API 키 권한을 최소한으로 설정하세요

### 요청 제한
- 업비트 API는 요청 제한이 있습니다
- 클래스가 자동으로 관리하지만, 과도한 요청은 피하세요

### 실제 거래
- 테스트 환경에서 충분히 검증 후 사용하세요
- 실제 거래 시에는 소액으로 시작하세요
- 주문 전에 모든 파라미터를 확인하세요

## 🐛 오류 처리

### 일반적인 오류

```python
try:
    result = api.get_ticker(['KRW-BTC'])
except ValueError as e:
    print(f"파라미터 오류: {e}")
except ConnectionError as e:
    print(f"연결 오류: {e}")
except Exception as e:
    print(f"기타 오류: {e}")
```

### 오류 코드

| 오류 | 설명 | 해결 방법 |
|------|------|-----------|
| 401 | 인증 오류 | API 키 확인 |
| 403 | 권한 오류 | API 키 권한 확인 |
| 429 | 요청 제한 초과 | 잠시 후 재시도 |
| 500 | 서버 오류 | 잠시 후 재시도 |

## 📊 사용 예시

### 실시간 가격 모니터링

```python
import time

api = UpbitAPI()

while True:
    try:
        price = api.get_current_price('KRW-BTC')
        print(f"비트코인 현재가: {price:,.0f}원")
        time.sleep(10)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"오류: {e}")
        time.sleep(5)
```

### 포트폴리오 분석

```python
api = UpbitAPI(access_key='your_key', secret_key='your_secret')

# 계좌 조회
accounts = api.get_accounts()

total_value = 0
for account in accounts:
    if float(account['balance']) > 0:
        currency = account['currency']
        balance = float(account['balance'])
        avg_price = float(account['avg_buy_price'])
        
        if currency == 'KRW':
            value = balance
        else:
            current_price = api.get_current_price(f'KRW-{currency}')
            value = balance * current_price
        
        total_value += value
        print(f"{currency}: {value:,.0f}원")

print(f"총 자산: {total_value:,.0f}원")
```

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

## 📄 라이선스

MIT License

## 🔗 관련 링크

- [업비트 API 문서](https://docs.upbit.com/)
- [업비트 개발자 센터](https://upbit.com/mypage/open_api_management)
- [JWT 토큰 생성기](https://jwt.io/)
