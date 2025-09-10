# 6차시: 업비트 API 연동

## 📚 학습 목표
- 업비트 API의 기본 구조와 주요 기능 이해
- 시장 데이터 조회, 계좌 조회, 주문 실행 API 사용법 학습
- 실제 거래 봇 개발을 위한 API 연동 기초 마련

## 🎯 주요 내용

### 1. 업비트 API 개요
- **REST API**와 **WebSocket** 연동 방식
- **시세 조회(Quotation) API**: 인증 불필요한 공개 API
- **거래 및 자산 관리(Exchange) API**: 인증이 필요한 개인 API

### 2. 시장 데이터 조회 API
- **페어 목록 조회**: `GET /v1/market/all`
- **현재가 조회**: `GET /v1/ticker`
- **캔들 데이터 조회**: `GET /v1/candles/{unit}`
- **체결 이력 조회**: `GET /v1/trades/ticks`
- **호가 정보 조회**: `GET /v1/orderbook`

### 3. 계좌 및 주문 관리 API
- **계정 잔고 조회**: `GET /v1/accounts`
- **주문 생성**: `POST /v1/orders`
- **주문 조회**: `GET /v1/orders`
- **주문 취소**: `DELETE /v1/orders/{uuid}`

### 4. 인증 및 보안
- **JWT 토큰** 기반 인증
- **API 키** 발급 및 권한 설정
- **보안 레벨 4등급** 이상 요구

## 📁 파일 구조
```
lesson-06/
├── lesson-06-prompts.md    # 프롬프트 모음
├── README.md              # 학습 가이드
└── requirements.txt       # 필요한 패키지 목록
```

## 🚀 시작하기

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 업비트 API 키 발급
1. [업비트 개발자 센터](https://docs.upbit.com) 접속
2. API 키 발급 (Access Key, Secret Key)
3. 보안 레벨 4등급 이상 설정
4. Open API 이용약관 동의

### 3. API 사용 예시
```python
import requests
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

# API 키 설정
access_key = "your_access_key"
secret_key = "your_secret_key"

# 시장 데이터 조회 (인증 불필요)
response = requests.get("https://api.upbit.com/v1/market/all")
markets = response.json()

# 계좌 조회 (인증 필요)
payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
}
jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
authorization_token = f'Bearer {jwt_token}'

headers = {"Authorization": authorization_token}
response = requests.get("https://api.upbit.com/v1/accounts", headers=headers)
accounts = response.json()
```

## ⚠️ 주의사항
- API 키는 절대 공개하지 마세요
- 테스트 환경에서 충분한 검증 후 실제 거래에 사용하세요
- Rate Limits를 준수하여 API를 호출하세요
- 네트워크 오류에 대한 재시도 로직을 구현하세요

## 📖 참고 자료
- [업비트 API 공식 문서](https://docs.upbit.com)
- [JWT 토큰 생성 가이드](https://docs.upbit.com/reference/authentication)
- [API 사용 제한사항](https://docs.upbit.com/reference/rate-limit)
