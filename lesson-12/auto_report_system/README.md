# 🤖 자동매매 자동 리포트 생성 시스템

자동매매 시스템의 거래 데이터를 자동으로 분석하고 정기적으로 리포트를 생성/발송하는 시스템입니다.

## ✨ 주요 기능

### 📊 리포트 유형
1. **일간 리포트** - 거래 요약, 수익률, 주요 이벤트
2. **주간 리포트** - 성과 분석, 전략 평가, 개선점
3. **월간 리포트** - 종합 성과, 시장 분석, 전략 조정
4. **특별 리포트** - 이상 상황 감지 시 긴급 알림

### 🎯 리포트 구성
- **실행 요약** - 핵심 지표 한눈에 보기
- **성과 지표** - 수익률, 샤프 비율, 승률 등
- **인사이트** - AI 기반 자동 분석 및 권장사항
- **시각화** - 차트 및 그래프 (선택사항)

### 🔄 자동화 기능
- **정기 스케줄링** - 설정한 시간에 자동 생성
- **템플릿 기반** - 일관된 형식의 리포트
- **다양한 포맷** - HTML, PDF, Excel 지원
- **자동 발송** - 이메일/텔레그램 자동 전송

## 🏗️ 시스템 구조

```
auto_report_system/
├── core/                      # 핵심 모듈
│   ├── config.py             # 설정 관리
│   ├── report_manager.py     # 리포트 관리자
│   └── scheduler.py          # 스케줄러
├── templates/                 # 리포트 템플릿
│   ├── base_template.py
│   ├── daily_template.py
│   ├── weekly_template.py
│   └── monthly_template.py
├── generators/                # 포맷 생성기
│   ├── html_generator.py
│   ├── pdf_generator.py
│   └── excel_generator.py
├── analyzers/                 # 데이터 분석기
│   ├── daily_analyzer.py
│   ├── weekly_analyzer.py
│   ├── monthly_analyzer.py
│   └── alert_analyzer.py
├── notifications/             # 알림 시스템
│   ├── telegram_sender.py
│   └── email_sender.py
├── utils/                     # 유틸리티
│   ├── data_collector.py     # 데이터 수집
│   └── insight_engine.py     # 인사이트 엔진
├── main.py                    # 메인 실행 파일
├── config.yaml.example        # 설정 예시
└── requirements.txt           # 패키지 목록
```

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
cd lesson-12/auto_report_system
pip install -r requirements.txt
```

### 2. 설정 파일 준비

```bash
# 예시 파일을 복사
cp config.yaml.example config.yaml

# 설정 파일 수정
# - 텔레그램 토큰/채팅 ID
# - 이메일 SMTP 설정
# - 스케줄 설정
```

### 3. 시스템 실행

```bash
# 자동 스케줄링 모드 (백그라운드 실행)
python main.py

# 또는 수동 리포트 생성
python -c "from core.report_manager import ReportManager; from core.config import ConfigManager; config = ConfigManager.load_config(); manager = ReportManager(config); manager.generate_report('daily')"
```

## ⚙️ 설정 가이드

### config.yaml 주요 설정

```yaml
# 리포트 설정
report:
  output_dir: "auto_reports"
  output_formats: ["html"]  # html, pdf, excel
  send_telegram: true
  send_email: false

# 스케줄 설정
schedule:
  daily:
    enabled: true
    hour: 23  # 매일 23:00
    minute: 0
  
  weekly:
    enabled: true
    day_of_week: 6  # 일요일
    hour: 23
    minute: 30

# 알림 임계값
alerts:
  max_drawdown: 10.0  # 10% 낙폭 시 알림
  daily_loss: 5.0     # 5% 손실 시 알림
```

### 텔레그램 봇 설정

1. BotFather(@BotFather)에게 `/newbot` 명령으로 봇 생성
2. 발급받은 토큰을 `config.yaml`의 `telegram.token`에 입력
3. 봇에게 메시지를 보낸 후 아래 명령으로 chat_id 확인:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. chat_id를 `config.yaml`의 `telegram.chat_id`에 입력

## 📊 리포트 예시

### 일간 리포트
- 오늘의 거래 요약
- 수익률 및 거래 수
- 활동 시간대 분석
- 코인별 성과

### 주간 리포트
- 일별 수익률 추이
- 전략별 성과 비교
- 리스크 지표
- 개선 권장사항

### 월간 리포트
- 월간 종합 성과
- 주별 수익률 분석
- 전략 및 코인별 상세 분석
- 장기 트렌드 분석

## 🔔 알림 시스템

### 자동 알림 조건
- **높은 낙폭** - 설정한 임계값 초과 시
- **일일 손실** - 당일 손실이 임계값 초과 시
- **낮은 승률** - 최근 승률이 임계값 이하 시
- **거래 중단** - 일정 시간 거래 없을 시
- **시스템 오류** - 거래 실패 등 오류 발생 시

### 알림 채널
- **텔레그램** - 즉시 알림 (권장)
- **이메일** - 상세 리포트 첨부

## 🛠️ 고급 사용법

### 수동 리포트 생성

```python
from core.report_manager import ReportManager
from core.config import ConfigManager

# 설정 로드
config = ConfigManager.load_config()

# 리포트 생성
manager = ReportManager(config)

# 일간 리포트
files = manager.generate_report('daily')

# 주간 리포트
files = manager.generate_report('weekly')

# 월간 리포트
files = manager.generate_report('monthly')
```

### 커스텀 분석기 추가

새로운 분석기를 추가하려면:

1. `analyzers/` 폴더에 새 파일 생성
2. 기본 분석 메서드 구현
3. `report_manager.py`에서 분석기 등록

```python
class CustomAnalyzer:
    def analyze(self, data):
        # 분석 로직 구현
        return {
            'custom_metric': 100,
            # ...
        }
```

### 새로운 포맷 추가

새로운 리포트 포맷을 추가하려면:

1. `generators/` 폴더에 새 생성기 생성
2. `BaseReportGenerator` 상속
3. `generate()` 메서드 구현

## 📋 요구사항

### 필수 패키지
- pandas
- numpy
- PyYAML
- requests (텔레그램용)

### 선택 패키지
- apscheduler (스케줄링용)
- reportlab (PDF 생성용)
- openpyxl (Excel 생성용)

## 🐛 문제 해결

### 스케줄러가 시작되지 않음
- `apscheduler` 패키지가 설치되어 있는지 확인
- 설치: `pip install apscheduler`

### 텔레그램 발송 실패
- 토큰과 chat_id가 올바른지 확인
- 봇이 차단되지 않았는지 확인
- 인터넷 연결 확인

### 데이터가 없음
- 데이터베이스 경로 확인 (`data/trading.db`)
- 거래 데이터가 실제로 존재하는지 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요!

