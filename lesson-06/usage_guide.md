# 실시간 가격 데이터 수집기 사용 가이드

## 📚 개요

업비트 WebSocket API를 사용하여 실시간으로 암호화폐 가격 데이터를 수집하고 분석하는 도구입니다.

## 🚀 주요 기능

- **실시간 데이터 수집**: WebSocket을 통한 실시간 가격 데이터 수집
- **자동 재연결**: 연결 끊김 시 자동 재연결
- **데이터 저장**: CSV/JSON 형식으로 데이터 저장
- **데이터 분석**: 수집된 데이터의 통계 분석 및 시각화
- **오류 처리**: 강력한 오류 처리 및 로깅

## 📦 설치 방법

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 프로젝트 구조 확인
```
lesson-06/
├── realtime_price_collector.py  # 실시간 데이터 수집기
├── data_analyzer.py             # 데이터 분석기
├── requirements.txt             # 필요한 패키지 목록
├── usage_guide.md              # 사용 가이드
└── realtime_data/              # 데이터 저장 디렉토리 (자동 생성)
```

## 🔧 사용 방법

### 1. 기본 사용법

#### 실시간 데이터 수집 시작
```python
from realtime_price_collector import UpbitWebSocketCollector

# 수집할 마켓 설정
markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT']

# 데이터 수집기 생성
collector = UpbitWebSocketCollector(
    markets=markets,           # 수집할 마켓
    data_dir="realtime_data", # 데이터 저장 디렉토리
    save_format="csv"         # 저장 형식 (csv 또는 json)
)

# 데이터 수집 시작
collector.start()
```

#### 콜백 함수 설정
```python
def on_ticker(data):
    """티커 데이터 수신 시 호출되는 함수"""
    print(f"📊 {data['market']}: {data['trade_price']:,}원 "
          f"({data['signed_change_rate']:.2%})")

def on_error(error):
    """오류 발생 시 호출되는 함수"""
    print(f"❌ 오류 발생: {error}")

def on_connect():
    """연결 성공 시 호출되는 함수"""
    print("✅ WebSocket 연결 성공!")

# 콜백 함수 등록
collector.set_callbacks(
    on_ticker=on_ticker,
    on_error=on_error,
    on_connect=on_connect
)
```

### 2. 고급 사용법

#### 커스텀 설정
```python
collector = UpbitWebSocketCollector(
    markets=['KRW-BTC', 'KRW-ETH'],
    data_dir="custom_data",
    save_format="json"
)

# 버퍼 크기 및 저장 간격 설정
collector.buffer_size = 50      # 버퍼 크기 (기본: 100)
collector.save_interval = 60    # 저장 간격 초 (기본: 30)

# 재연결 설정
collector.max_reconnect_attempts = 20  # 최대 재연결 시도 횟수
collector.reconnect_delay = 10         # 재연결 대기 시간 (초)
```

#### 데이터 수집 중지
```python
# 수집 중지
collector.stop()

# 통계 정보 확인
stats = collector.get_statistics()
print(f"수집 상태: {stats['is_running']}")
print(f"버퍼 크기: {stats['buffer_size']}")
```

### 3. 데이터 분석

#### 기본 분석
```python
from data_analyzer import RealtimeDataAnalyzer

# 분석기 생성
analyzer = RealtimeDataAnalyzer("realtime_data")

# 데이터 로드
data = analyzer.load_data()

# 기본 통계
stats = analyzer.get_basic_statistics()
print(stats)

# 마켓별 요약
summary = analyzer.get_market_summary()
print(summary)
```

#### 차트 생성
```python
# 가격 차트 생성
analyzer.create_price_chart('KRW-BTC', 'btc_price_chart.png')

# 상관관계 히트맵 생성
analyzer.create_correlation_heatmap('correlation.png')

# 변동성 분석
volatility = analyzer.analyze_volatility('KRW-BTC')
print(volatility)
```

#### 분석 보고서 생성
```python
# HTML 보고서 생성
analyzer.export_analysis_report('analysis_report.html')
```

## 📊 수집되는 데이터

### 티커 데이터 구조
```json
{
    "timestamp": "2024-01-01T12:00:00.000000",
    "market": "KRW-BTC",
    "trade_price": 50000000,
    "trade_volume": 0.001,
    "signed_change_rate": 0.025,
    "signed_change_price": 1250000,
    "high_price": 51000000,
    "low_price": 49000000,
    "opening_price": 49500000,
    "prev_closing_price": 48750000,
    "acc_trade_volume_24h": 100.5,
    "acc_trade_price_24h": 5000000000,
    "highest_52_week_price": 60000000,
    "lowest_52_week_price": 30000000,
    "trade_date": "20240101",
    "trade_time": "120000",
    "trade_timestamp": 1704067200000
}
```

## 🛠️ 설정 옵션

### UpbitWebSocketCollector 설정
| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `markets` | List[str] | ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'] | 수집할 마켓 코드 리스트 |
| `data_dir` | str | "data" | 데이터 저장 디렉토리 |
| `save_format` | str | "csv" | 저장 형식 (csv 또는 json) |

### 내부 설정
| 속성 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `buffer_size` | int | 100 | 데이터 버퍼 크기 |
| `save_interval` | int | 30 | 자동 저장 간격 (초) |
| `max_reconnect_attempts` | int | 10 | 최대 재연결 시도 횟수 |
| `reconnect_delay` | int | 5 | 재연결 대기 시간 (초) |

## 📁 파일 구조

### 생성되는 파일들
```
realtime_data/
├── realtime_data_20240101_120000.csv  # CSV 형식 데이터
├── realtime_data_20240101_120030.csv
├── realtime_data_20240101_120100.json # JSON 형식 데이터
└── ...

analysis_output/
├── price_chart_KRW-BTC.png           # 가격 차트
├── correlation_heatmap.png           # 상관관계 히트맵
└── analysis_report.html              # 분석 보고서
```

## ⚠️ 주의사항

### 1. API 제한사항
- 업비트 WebSocket API는 무료로 사용 가능
- 연결 수 제한: IP당 최대 5개 연결
- 데이터 수집량에 따른 네트워크 사용량 고려

### 2. 데이터 저장
- 데이터는 실시간으로 버퍼에 저장됨
- 버퍼가 가득 차거나 설정된 간격마다 파일로 저장
- 충분한 디스크 공간 확보 필요

### 3. 오류 처리
- 네트워크 연결 오류 시 자동 재연결 시도
- 최대 재연결 시도 횟수 초과 시 수집 중지
- 모든 오류는 로그 파일에 기록됨

## 🔍 문제 해결

### 자주 발생하는 문제들

#### 1. 연결 실패
```python
# 재연결 설정 조정
collector.max_reconnect_attempts = 20
collector.reconnect_delay = 10
```

#### 2. 데이터 저장 오류
```python
# 데이터 디렉토리 권한 확인
import os
os.makedirs("realtime_data", exist_ok=True)
```

#### 3. 메모리 사용량 증가
```python
# 버퍼 크기 조정
collector.buffer_size = 50
collector.save_interval = 30
```

## 📈 성능 최적화

### 1. 수집 성능 향상
- 필요한 마켓만 선택하여 수집
- 불필요한 콜백 함수 제거
- 적절한 버퍼 크기 설정

### 2. 저장 성능 향상
- CSV 형식이 JSON보다 빠름
- 적절한 저장 간격 설정
- SSD 사용 권장

### 3. 분석 성능 향상
- 대용량 데이터는 청크 단위로 처리
- 필요한 컬럼만 선택하여 로드
- 인덱스 설정으로 검색 성능 향상

## 📞 지원

문제가 발생하거나 질문이 있으시면:
1. 로그 파일 확인 (`realtime_collector.log`)
2. 오류 메시지 확인
3. 설정값 검토
4. 네트워크 연결 상태 확인

## 🔄 업데이트 내역

- **v1.0.0**: 초기 버전
  - 기본 실시간 데이터 수집 기능
  - CSV/JSON 저장 기능
  - 기본 데이터 분석 기능
