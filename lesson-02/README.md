# CoinGecko API 비트코인 가격 조회 프로그램

## 프로젝트 설명
이 프로젝트는 2차시 1번 프롬프트에 따라 구현된 CoinGecko API 기반 비트코인 가격 조회 프로그램입니다.
requests 라이브러리를 사용하여 API 호출을 수행하고, 종합적인 오류 처리를 포함합니다.

## 주요 기능
- CoinGecko API를 사용한 실시간 비트코인 가격 조회
- matplotlib을 활용한 시간-가격 선 그래프 생성
- 다중 통화 지원 (KRW, USD, EUR 등)
- 종합적인 오류 처리 및 재시도 메커니즘
- Rate limit 관리 및 자동 재시도
- 사용자 친화적인 출력 형식
- 상세한 비트코인 정보 조회
- 차트 자동 저장 및 통계 정보 표시

## 기술 스택
- **언어**: Python 3.7+
- **HTTP 요청**: requests
- **API**: CoinGecko Public API v3
- **차트 생성**: matplotlib
- **수치 계산**: numpy
- **타입 힌트**: typing 모듈 활용

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 프로그램 실행

#### 가격 조회 프로그램
```bash
python bitcoin_price_coingecko.py
```

#### 차트 생성 프로그램
```bash
python bitcoin_price_chart.py
```

## 주요 클래스 및 메서드

### CoinGeckoBitcoinPrice 클래스
- **`__init__()`**: API 클라이언트 초기화
- **`_make_request()`**: 내부 API 요청 처리 (오류 처리 포함)
- **`get_bitcoin_price()`**: 비트코인 현재가 조회
- **`get_bitcoin_detailed_info()`**: 비트코인 상세 정보 조회
- **`format_price()`**: 가격 포맷팅
- **`display_price_info()`**: 가격 정보 표시
- **`display_detailed_info()`**: 상세 정보 표시

## 오류 처리 기능

### 1. HTTP 상태 코드별 처리
- **200**: 성공적인 응답
- **429**: Rate limit 초과 시 자동 재시도
- **404**: 리소스 없음
- **5xx**: 서버 오류 시 재시도

### 2. 네트워크 오류 처리
- **Timeout**: 요청 시간 초과 시 재시도
- **ConnectionError**: 연결 오류 시 재시도
- **RequestException**: 일반적인 요청 오류

### 3. 데이터 처리 오류
- **JSONDecodeError**: JSON 파싱 오류
- **예상치 못한 오류**: 일반적인 예외 상황

## 출력 예시

```
CoinGecko API를 사용한 비트코인 가격 조회 프로그램
------------------------------------------------------------

1. 한국 원화 기준 비트코인 가격 조회
비트코인 가격 조회 중... (통화: KRW)
API 요청 시도 1/3: https://api.coingecko.com/api/v3/simple/price

============================================================
비트코인 현재가 정보
============================================================
현재 가격: 45,000,000원
시가총액: 45,000,000,000,000원
24시간 거래량: 2,500,000,000,000원
24시간 변화: 📈 +2.50%
마지막 업데이트: 2024-01-15 14:30:25
============================================================
```

## 파일 구조
```
lesson-02/
├── lesson-02-prompts.md              # 2차시 모든 프롬프트와 코드 정보
├── bitcoin_price_coingecko.py        # 메인 프로그램 코드
├── requirements.txt                   # 파이썬 의존성
└── README.md                         # 프로젝트 설명서
```

## 주의사항
- 인터넷 연결이 필요합니다
- CoinGecko API의 요청 제한을 고려하여 재시도 로직이 구현되어 있습니다
- User-Agent 헤더가 설정되어 있어 API 호환성이 향상됩니다
- 모든 API 호출에 10초 타임아웃이 설정되어 있습니다

## 개발자 정보
- **프로젝트**: Bot Trade Project
- **차시**: 2차시 1번
- **구현 언어**: Python
- **API**: CoinGecko Public API
