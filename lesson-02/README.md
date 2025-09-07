# CoinGecko API 비트코인 가격 조회 프로그램

## 프로젝트 설명
이 프로젝트는 2차시 1번 프롬프트에 따라 구현된 CoinGecko API 기반 비트코인 가격 조회 프로그램입니다.
requests 라이브러리를 사용하여 API 호출을 수행하고, 종합적인 오류 처리를 포함합니다.

## 주요 기능
- CoinGecko API를 사용한 실시간 비트코인 가격 조회
- matplotlib을 활용한 시간-가격 선 그래프 생성
- **1시간마다 자동 가격 업데이트**
- **새로운 데이터 추가 시 실시간 그래프 자동 갱신**
- 다중 통화 지원 (KRW, USD, EUR 등)
- 종합적인 오류 처리 및 재시도 메커니즘
- Rate limit 관리 및 자동 재시도
- 사용자 친화적인 출력 형식
- 상세한 비트코인 정보 조회
- 차트 자동 저장 및 통계 정보 표시
- 백그라운드 데이터 수집 및 실시간 모니터링

## 기술 스택
- **언어**: Python 3.7+
- **HTTP 요청**: requests
- **API**: CoinGecko Public API v3
- **차트 생성**: matplotlib
- **실시간 애니메이션**: matplotlib.animation
- **수치 계산**: numpy
- **멀티스레딩**: threading
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

#### 자동 업데이트 차트 프로그램
```bash
python bitcoin_auto_update_chart.py
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

### BitcoinAutoUpdateChart 클래스 (3번 프롬프트)
- **`__init__()`**: 자동 업데이트 차트 시스템 초기화
- **`setup_matplotlib()`**: matplotlib 설정 및 폰트 구성
- **`get_current_bitcoin_price()`**: 현재 비트코인 가격 조회
- **`get_bitcoin_price_history()`**: 비트코인 가격 히스토리 조회
- **`update_price_data()`**: 가격 데이터 업데이트
- **`data_collection_worker()`**: 백그라운드 데이터 수집 워커
- **`start_data_collection()`**: 자동 데이터 수집 시작
- **`stop_data_collection()`**: 자동 데이터 수집 중지
- **`create_auto_update_chart()`**: 실시간 자동 업데이트 차트 생성
- **`save_price_data()`**: CSV 파일에 데이터 저장
- **`load_initial_data()`**: 초기 데이터 로드

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
├── bitcoin_price_coingecko.py        # 1번 프롬프트: 기본 가격 조회 프로그램
├── bitcoin_price_chart.py            # 2번 프롬프트: 차트 생성 프로그램
├── bitcoin_auto_update_chart.py      # 3번 프롬프트: 자동 업데이트 차트 프로그램
├── bitcoin_price_live_chart.py       # 기존 실시간 차트 프로그램
├── requirements.txt                   # 파이썬 의존성
└── README.md                         # 프로젝트 설명서
```

## 주의사항
- 인터넷 연결이 필요합니다
- CoinGecko API의 요청 제한을 고려하여 재시도 로직이 구현되어 있습니다
- User-Agent 헤더가 설정되어 있어 API 호환성이 향상됩니다
- 모든 API 호출에 10초 타임아웃이 설정되어 있습니다

## 3번 프롬프트 자동 업데이트 차트 기능

### 주요 특징
- **자동 데이터 수집**: 1시간마다 백그라운드에서 비트코인 가격 자동 수집
- **실시간 차트 갱신**: 5초마다 차트 자동 새로고침으로 최신 데이터 반영
- **데이터 저장**: 모든 가격 데이터를 CSV 파일에 자동 저장
- **24시간 히스토리**: 최근 24시간 데이터만 유지하여 메모리 효율성 확보
- **실시간 통계**: 가격 변화율, 최고/최저가, 다음 업데이트 시간 표시

### 작동 방식
1. **프로그램 시작**: 초기 24시간 가격 데이터 로드
2. **백그라운드 수집**: 별도 스레드에서 1시간마다 새 가격 데이터 수집
3. **실시간 갱신**: matplotlib 애니메이션으로 5초마다 차트 자동 업데이트
4. **데이터 관리**: 중복 데이터 방지 및 자동 정리
5. **통계 표시**: 실시간 가격 변화율과 차트 통계 정보 표시

### 사용법
```bash
python bitcoin_auto_update_chart.py
```

프로그램 실행 후:
- 차트 창이 열리며 실시간으로 업데이트됩니다
- 콘솔에서 데이터 수집 상태를 확인할 수 있습니다
- 차트를 닫으면 프로그램이 종료됩니다

## 개발자 정보
- **프로젝트**: Bot Trade Project
- **차시**: 2차시 (1번, 2번, 3번 프롬프트)
- **구현 언어**: Python
- **API**: CoinGecko Public API
