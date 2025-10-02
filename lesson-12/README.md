# 자동매매 데이터 분석 시스템

자동매매 시스템의 거래 데이터를 종합적으로 분석하는 Python 기반 분석 도구입니다.

## 🎯 주요 기능

### 📊 데이터 처리
- **pandas, numpy**를 활용한 효율적인 데이터 처리
- SQLite 데이터베이스에서 거래 데이터 자동 로드
- 데이터 전처리 및 정제 기능
- 샘플 데이터 자동 생성 기능

### 📈 성과 분석
- **수익률 지표**: 총 수익률, 연환산 수익률, 일간/월간 수익률
- **리스크 지표**: 최대 낙폭(MDD), 샤프 비율, 소르티노 비율, VaR/CVaR
- **거래 지표**: 승률, 프로핏 팩터, 평균 보유 기간, 수수료 분석
- **코인별/전략별/시간대별** 세분화된 성과 분석

### 📊 시각화
- **matplotlib, seaborn**을 활용한 고품질 차트 생성
- 자산 곡선, 낙폭 차트, 거래 분포 히스토그램
- 월별 성과 히트맵, 리스크-수익 스캐터 플롯
- 종합 대시보드 및 전략 비교 차트

### 🔬 통계 분석
- **scipy**를 활용한 고급 통계 분석
- 정규성 검정 (Shapiro-Wilk, Jarque-Bera, Kolmogorov-Smirnov)
- 상관관계 분석 (피어슨, 스피어만, 켄달)
- 가설 검정 (t-검정, Mann-Whitney U 검정)
- VaR/CVaR 계산 (히스토리컬, 파라메트릭, Cornish-Fisher)

### 📄 리포트 생성
- **HTML, JSON, CSV** 형태의 종합 리포트
- 시각적 대시보드 및 인사이트 자동 도출
- 설정 가능한 리포트 템플릿
- 자동화된 리포트 생성 및 저장

## 🏗️ 시스템 구조

```
lesson-12/
├── data_processor.py          # 데이터 처리 모듈
├── performance_metrics.py     # 성과 지표 계산 모듈
├── visualization.py           # 시각화 모듈
├── statistical_analysis.py    # 통계 분석 모듈
├── report_generator.py        # 리포트 생성 모듈
├── trading_analyzer.py        # 메인 분석 클래스
├── example_usage.py          # 사용 예제
├── requirements.txt          # 의존성 패키지
└── README.md                # 이 파일
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 기본 분석 실행

```python
from trading_analyzer import TradingAnalyzer

# 분석 시스템 초기화
analyzer = TradingAnalyzer()

# 종합 분석 실행
results = analyzer.run_comprehensive_analysis()

# 분석 요약 출력
summary = analyzer.get_analysis_summary()
print(summary)
```

### 3. 예제 실행

```bash
python example_usage.py
```

## 📋 사용법

### 기본 분석

```python
from trading_analyzer import TradingAnalyzer

analyzer = TradingAnalyzer()
results = analyzer.run_comprehensive_analysis()
```

### 커스텀 설정 분석

```python
from trading_analyzer import TradingAnalyzer, AnalysisConfig
from data_processor import DataConfig
from visualization import ChartConfig
from report_generator import ReportConfig

# 커스텀 설정
data_config = DataConfig(
    db_path="data/custom.db",
    data_period_days=60,
    symbols=["KRW-BTC", "KRW-ETH"],
    strategies=["volatility_breakout", "ma_crossover"]
)

chart_config = ChartConfig(
    figure_size=(15, 10),
    save_path="custom_charts/"
)

report_config = ReportConfig(
    output_dir="custom_reports/",
    format_types=["html", "json"]
)

analysis_config = AnalysisConfig(
    data_config=data_config,
    chart_config=chart_config,
    report_config=report_config
)

analyzer = TradingAnalyzer(analysis_config)
results = analyzer.run_comprehensive_analysis()
```

### 특정 기간 분석

```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

results = analyzer.run_comprehensive_analysis(start_date, end_date)
```

### 선택적 분석 (성과 분석만)

```python
from trading_analyzer import TradingAnalyzer, AnalysisConfig

config = AnalysisConfig(
    enable_visualization=False,
    enable_statistical_analysis=False,
    enable_performance_analysis=True,
    enable_report_generation=False
)

analyzer = TradingAnalyzer(config)
results = analyzer.run_comprehensive_analysis()
```

## 📊 분석 지표

### 수익률 지표
- **총 수익률**: 전체 기간 동안의 누적 수익률
- **연환산 수익률**: 연간 기준으로 환산한 수익률
- **일간/월간 수익률**: 단기 수익률 분석

### 리스크 지표
- **최대 낙폭(MDD)**: 최고점 대비 최대 하락폭
- **샤프 비율**: 위험 대비 수익률
- **소르티노 비율**: 하방 위험 대비 수익률
- **VaR/CVaR**: Value at Risk 및 Conditional VaR
- **칼마 비율**: MDD 대비 수익률

### 거래 지표
- **승률**: 수익 거래 비율
- **프로핏 팩터**: 총 수익 / 총 손실 비율
- **평균 수익/손실**: 거래당 평균 손익
- **평균 보유 기간**: 거래당 평균 보유 시간
- **수수료 분석**: 총 거래 수수료 및 비용

## 📈 시각화 차트

### 기본 차트
- **자산 곡선**: 포트폴리오 가치 변화
- **낙폭 차트**: 최대 낙폭 시각화
- **거래 분포**: P&L, 보유기간, 거래크기 분포
- **일일 수익률 히스토그램**: 수익률 분포 분석

### 고급 차트
- **월별 성과 히트맵**: 월별 수익률 히트맵
- **리스크-수익 스캐터**: 코인별 리스크-수익 분석
- **전략 비교 차트**: 전략별 성과 비교
- **종합 대시보드**: 모든 지표를 한눈에

## 🔬 통계 분석

### 정규성 검정
- **Shapiro-Wilk**: 소표본 정규성 검정
- **Jarque-Bera**: 왜도와 첨도 기반 검정
- **Kolmogorov-Smirnov**: 분포 비교 검정

### 상관관계 분석
- **피어슨 상관계수**: 선형 상관관계
- **스피어만 상관계수**: 순위 기반 상관관계
- **켄달 타우**: 순서 기반 상관관계

### 가설 검정
- **t-검정**: 평균 차이 검정
- **Mann-Whitney U 검정**: 비모수 평균 차이 검정
- **단일 평균 검정**: 기댓값과의 차이 검정

## 📄 리포트 형태

### HTML 리포트
- 시각적 대시보드
- 인터랙티브 차트
- 반응형 디자인
- 모바일 친화적

### JSON 리포트
- 구조화된 데이터
- API 연동 가능
- 프로그래밍 방식 접근

### CSV 리포트
- 원시 데이터 내보내기
- Excel 호환
- 추가 분석용 데이터

## ⚙️ 설정 옵션

### 데이터 설정 (DataConfig)
```python
DataConfig(
    db_path="data/trading.db",      # 데이터베이스 경로
    data_period_days=30,           # 분석 기간 (일)
    symbols=["KRW-BTC", "KRW-ETH"], # 분석 대상 코인
    strategies=["volatility_breakout"] # 분석 대상 전략
)
```

### 차트 설정 (ChartConfig)
```python
ChartConfig(
    figure_size=(12, 8),           # 차트 크기
    dpi=100,                       # 해상도
    style="seaborn-v0_8",          # 차트 스타일
    save_path="charts/",           # 저장 경로
    show_grid=True,                # 격자 표시
    tight_layout=True              # 레이아웃 최적화
)
```

### 리포트 설정 (ReportConfig)
```python
ReportConfig(
    output_dir="reports/",         # 출력 디렉토리
    format_types=["html", "json"], # 생성할 포맷
    include_charts=True,           # 차트 포함 여부
    include_raw_data=False         # 원시 데이터 포함 여부
)
```

## 🛠️ 확장성

### 새로운 지표 추가
```python
# performance_metrics.py에 새로운 지표 계산 함수 추가
def calculate_custom_metric(data):
    # 사용자 정의 지표 계산 로직
    return metric_value
```

### 새로운 차트 추가
```python
# visualization.py에 새로운 차트 생성 함수 추가
def create_custom_chart(data, title="Custom Chart"):
    # 사용자 정의 차트 생성 로직
    return fig
```

### 새로운 리포트 포맷 추가
```python
# report_generator.py에 새로운 리포트 생성기 추가
def generate_custom_report(data):
    # 사용자 정의 리포트 생성 로직
    return report_content
```

## 📝 주의사항

1. **데이터베이스**: SQLite 데이터베이스 파일이 존재해야 합니다
2. **메모리 사용량**: 대용량 데이터 처리 시 메모리 사용량에 주의하세요
3. **차트 저장**: 차트 저장 경로에 쓰기 권한이 있어야 합니다
4. **한글 폰트**: 차트에서 한글 폰트 문제를 방지하기 위해 영어 레이블을 사용합니다

## 🔧 문제 해결

### 일반적인 문제
1. **데이터베이스 연결 오류**: 데이터베이스 파일 경로 확인
2. **차트 생성 실패**: matplotlib 백엔드 설정 확인
3. **메모리 부족**: 분석 기간을 줄이거나 배치 처리 사용

### 로그 확인
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📞 지원

문제가 발생하거나 개선 사항이 있으시면 이슈를 등록해 주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
