# 0차시 맛보기 강의 - 비트코인 가격 실시간 표시 프로그램

## 개요

이 강의는 암호화폐 트레이딩 봇 개발의 첫 번째 단계로, 비트코인 가격을 실시간으로 가져와서 표시하는 간단한 프로그램을 만드는 방법을 학습합니다.

## 학습 목표

- **API 활용**: 무료 암호화폐 API를 사용하여 비트코인 가격 데이터를 가져오는 방법
- **실시간 업데이트**: 주기적으로 데이터를 갱신하여 최신 가격 정보를 표시
- **데이터 처리**: JSON 형태의 API 응답을 파싱하고 필요한 정보만 추출
- **에러 처리**: 네트워크 오류나 API 제한 등 예외 상황에 대한 대응

## 주요 기능

- 현재 비트코인 가격 표시 (USD 기준)
- 24시간 가격 변동률 표시
- 실시간 자동 업데이트 (기본 30초 간격)
- **가격 상승 알림 시스템** (0.5% 이상 상승 시 데스크톱 알림)
- **실시간 차트 시각화** (matplotlib 기반)
- 간단한 콘솔 출력 및 GUI 인터페이스

## 사용된 기술

- **Python 3.x**: 프로그래밍 언어
- **requests**: HTTP 요청을 위한 라이브러리
- **json**: API 응답 데이터 파싱
- **time**: 업데이트 간격 제어
- **matplotlib**: 실시간 차트 생성 및 시각화
- **plyer**: 크로스 플랫폼 데스크톱 알림
- **deque**: 효율적인 데이터 히스토리 관리

## API 정보

이 강의에서는 다음 무료 API를 사용합니다:
- **CoinGecko API**: 무료, API 키 불필요
- **CoinCap API**: 무료, API 키 불필요

## 파일 구조

```
lesson-00/
├── README.md                              # 이 파일
├── lesson-00-prompts.md                   # 강의 프롬프트
├── requirements.txt                       # 필요한 패키지 목록
├── bitcoin_price_realtime.py              # 기본 프로그램 (첫 번째 프롬프트)
└── bitcoin_price_with_alerts_and_chart.py # 개선된 프로그램 (두 번째 프롬프트)
```

## 실행 방법

### 1. 파이썬 가상 환경 설정 (권장)

가상 환경을 사용하면 프로젝트별로 독립적인 패키지 환경을 관리할 수 있습니다.

**Windows:**
```bash
# 가상 환경 생성
python -m venv bot-env

# 가상 환경 활성화
bot-env\Scripts\activate

# 가상 환경 비활성화 (작업 완료 후)
deactivate
```

**macOS/Linux:**
```bash
# 가상 환경 생성
python3 -m venv bot-env

# 가상 환경 활성화
source bot-env/bin/activate

# 가상 환경 비활성화 (작업 완료 후)
deactivate
```

### 2. 필요한 패키지 설치

가상 환경이 활성화된 상태에서:
```bash
pip install -r requirements.txt
```

**또는 개별 설치:**
```bash
pip install requests matplotlib plyer
```

### 3. matplotlib 설치 문제 해결

Windows에서 matplotlib 설치 시 다음과 같은 오류가 발생할 수 있습니다:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**해결 방법 (순서대로 시도):**

**방법 1: 미리 컴파일된 wheel 사용 (가장 쉬움)**
```bash
pip install --only-binary=all matplotlib
```

**방법 2: conda 사용 (권장)**
```bash
# Anaconda나 Miniconda가 설치되어 있다면
conda install matplotlib
```

**방법 3: Visual C++ Build Tools 설치**
1. [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 다운로드
2. 설치 후 재부팅
3. 다시 설치 시도

**방법 4: 대체 패키지 사용**
```bash
# matplotlib 대신 plotly 사용 (웹 기반 차트)
pip install plotly
```

### 4. 프로그램 실행

**첫 번째 프롬프트 (기본 기능):**
```bash
python bitcoin_price_realtime.py
```

**두 번째 프롬프트 (알림 & 차트 기능):**
```bash
python bitcoin_price_with_alerts_and_chart.py
```

## 가상 환경 사용의 장점

- **패키지 충돌 방지**: 다른 프로젝트와 독립적인 패키지 환경
- **깔끔한 관리**: 프로젝트별로 필요한 패키지만 설치
- **버전 호환성**: 각 프로젝트에 맞는 패키지 버전 사용
- **배포 용이성**: requirements.txt로 정확한 환경 재현 가능

## 다음 단계

이 강의를 완료한 후에는 다음 내용을 학습할 수 있습니다:
- 가격 알림 시스템 (Lesson 1)
- 차트 생성 및 시각화 (Lesson 2)
- 자동화된 트레이딩 전략 (Lesson 3)

## 주의사항

- API 사용량 제한을 고려하여 적절한 업데이트 간격을 설정하세요
- 네트워크 연결이 필요합니다
- 일부 API는 요청 빈도에 제한이 있을 수 있습니다
