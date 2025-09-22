# 2차시 프롬프트 모음

## 1번 프롬프트
```text
CoinGecko API를 사용해서 비트코인의 현재 가격을 가져오는 Python 코드를 만들어줘.
requests 라이브러리를 사용하고, 오류 처리를 포함해서 작성해줘.
```

### 생성된 코드 파일 정보
- **파일명**: `bitcoin_price_coingecko.py`
- **주요 기능**: 
  - CoinGecko API를 사용한 비트코인 현재가 조회
  - requests 라이브러리 활용
  - 종합적인 오류 처리 및 예외 상황 대응
  - 사용자 친화적인 출력 형식
- **의존성**: `requirements.txt`
- **실행 방법**: `python bitcoin_price_coingecko.py`

---

## 2번 프롬프트
```text
비트코인 가격 데이터를 matplotlib을 사용해서 선 그래프로 그려줘. 
x축은 시간, y축은 가격으로 설정하고, 제목과 설명을 추가해줘.
```

### 생성된 코드 파일 정보
- **파일명**: `bitcoin_price_chart.py`
- **주요 기능**: 
  - CoinGecko API를 사용한 비트코인 가격 데이터 수집
  - matplotlib을 활용한 선 그래프 생성
  - 시간-가격 축 설정 및 그래프 스타일링
  - 제목, 설명, 레이블 등 그래프 요소 추가
  - 한국어 지원 및 사용자 친화적 인터페이스
- **의존성**: `requirements.txt` (matplotlib 추가)
- **실행 방법**: `python bitcoin_price_chart.py`

---

## 3번 프롬프트
```text
5분 마다 자동으로 가격을 업데이트하는 기능을 추가해줘. 
새로운 데이터가 추가될 때마다 그래프가 자동으로 바뀌도록 해줘.
```

### 생성된 코드 파일 정보
- **파일명**: `bitcoin_price_live_chart.py`
- **주요 기능**: 
  - 5분 마다 자동 가격 업데이트
  - 실시간 그래프 자동 갱신
  - matplotlib 애니메이션 기능 활용
  - 백그라운드 데이터 수집 및 차트 업데이트
  - 사용자 인터페이스 개선 (실시간 모니터링)
  - 데이터 저장 및 로깅 기능
- **의존성**: `requirements.txt` (matplotlib.animation 추가)
- **실행 방법**: `python bitcoin_price_live_chart.py`


