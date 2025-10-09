# 📋 자동 리포트 시스템 개요

## 🎯 시스템 목적

자동매매 시스템의 거래 성과를 **자동으로 분석**하고 **정기적으로 리포트를 생성/발송**하여, 트레이더가 시스템 상태를 손쉽게 모니터링할 수 있도록 지원합니다.

## 🏗️ 아키텍처 설계

### 계층 구조

```
┌─────────────────────────────────────────┐
│         사용자 인터페이스               │
│   (텔레그램, 이메일, 파일 시스템)       │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         알림 레이어 (Notifications)     │
│   - TelegramSender                       │
│   - EmailSender                          │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         리포트 생성 레이어              │
│   - HTMLGenerator                        │
│   - PDFGenerator                         │
│   - ExcelGenerator                       │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         비즈니스 로직 레이어            │
│   - ReportManager (리포트 관리)         │
│   - Scheduler (스케줄링)                │
│   - InsightEngine (인사이트 생성)       │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         분석 레이어 (Analyzers)         │
│   - DailyAnalyzer                        │
│   - WeeklyAnalyzer                       │
│   - MonthlyAnalyzer                      │
│   - AlertAnalyzer                        │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         데이터 레이어                   │
│   - DataCollector (데이터 수집)         │
│   - SQLite Database                      │
└─────────────────────────────────────────┘
```

## 🔄 처리 흐름

### 1. 정기 리포트 생성 흐름

```
1. Scheduler (cron)
   ↓
2. ReportManager.generate_report()
   ↓
3. DataCollector.collect_data()
   ├─ 거래 데이터 조회 (SQLite)
   ├─ 계좌 내역 조회
   └─ 주문 내역 조회
   ↓
4. Analyzer.analyze()
   ├─ 성과 지표 계산
   ├─ 리스크 분석
   └─ 패턴 분석
   ↓
5. InsightEngine.generate_insights()
   ├─ 수익률 인사이트
   ├─ 리스크 인사이트
   └─ 거래 패턴 인사이트
   ↓
6. Generator.generate()
   ├─ HTML 생성
   ├─ PDF 생성 (선택)
   └─ Excel 생성 (선택)
   ↓
7. Notification.send()
   ├─ 텔레그램 발송
   └─ 이메일 발송
```

### 2. 긴급 알림 흐름

```
1. Scheduler (interval)
   ↓
2. AlertAnalyzer.check_anomalies()
   ├─ 낙폭 체크
   ├─ 손실 체크
   ├─ 승률 체크
   └─ 시스템 오류 체크
   ↓
3. 임계값 초과 시
   ↓
4. ReportManager.generate_alert_report()
   ↓
5. 즉시 알림 발송
   ├─ 텔레그램 (즉시)
   └─ 이메일 (선택)
```

## 🧩 핵심 컴포넌트

### 1. ReportManager (리포트 관리자)
**역할**: 리포트 생성의 중앙 제어
- 데이터 수집 조율
- 분석 실행
- 인사이트 생성
- 포맷별 리포트 생성
- 발송 관리

### 2. Scheduler (스케줄러)
**역할**: 자동화 및 스케줄링
- Cron 기반 정기 실행
- Interval 기반 모니터링
- 멀티 스케줄 관리

### 3. DataCollector (데이터 수집기)
**역할**: 데이터베이스에서 필요한 데이터 수집
- 거래 내역 조회
- 계좌 정보 조회
- 기간별 필터링

### 4. Analyzers (분석기)
**역할**: 리포트 유형별 데이터 분석
- **DailyAnalyzer**: 일간 성과 분석
- **WeeklyAnalyzer**: 주간 트렌드 분석
- **MonthlyAnalyzer**: 월간 종합 분석
- **AlertAnalyzer**: 이상 상황 탐지

### 5. InsightEngine (인사이트 엔진)
**역할**: AI 기반 자동 인사이트 생성
- 수익률 평가
- 리스크 경고
- 거래 패턴 분석
- 전략 권장사항

### 6. Generators (생성기)
**역할**: 다양한 포맷의 리포트 생성
- **HTMLGenerator**: 웹 기반 리포트
- **PDFGenerator**: 인쇄 가능한 문서
- **ExcelGenerator**: 데이터 분석용

### 7. Notifications (알림)
**역할**: 리포트 발송
- **TelegramSender**: 즉시 알림
- **EmailSender**: 상세 리포트

## 📊 데이터 모델

### 수집 데이터
```python
{
    'trades': DataFrame,  # 거래 내역
    'account_history': DataFrame,  # 계좌 내역
    'orders': DataFrame,  # 주문 내역
    'period': {
        'start': datetime,
        'end': datetime
    }
}
```

### 분석 결과
```python
{
    'total_return': float,  # 총 수익률
    'total_trades': int,  # 거래 수
    'win_rate': float,  # 승률
    'max_drawdown': float,  # 최대 낙폭
    'sharpe_ratio': float,  # 샤프 비율
    'sortino_ratio': float,  # 소르티노 비율
    # ... 기타 지표
}
```

### 인사이트 구조
```python
{
    'title': str,  # 제목
    'description': str,  # 설명
    'recommendation': str,  # 권장사항
    'impact': str,  # 영향도 (high/medium/low)
    'category': str  # 카테고리
}
```

## ⚙️ 설정 구조

### config.yaml
```yaml
report:
  output_dir: str
  output_formats: List[str]
  send_email: bool
  send_telegram: bool
  recipients: List[str]

schedule:
  daily/weekly/monthly:
    enabled: bool
    hour/day: int
    minute: int
  alert:
    enabled: bool
    interval_minutes: int

alerts:
  max_drawdown: float
  daily_loss: float
  win_rate_drop: float

telegram:
  token: str
  chat_id: str

email:
  smtp_server: str
  smtp_port: int
  username: str
  password: str
```

## 🔌 확장 포인트

### 새로운 분석기 추가
```python
class CustomAnalyzer:
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # 커스텀 분석 로직
        return analysis_result
```

### 새로운 포맷 추가
```python
class CustomGenerator(BaseReportGenerator):
    def generate(self, report_type: str, data: Dict[str, Any]) -> str:
        # 커스텀 포맷 생성
        return file_path
```

### 새로운 알림 채널 추가
```python
class SlackSender:
    def send_report_notification(self, ...):
        # Slack 발송 로직
        pass
```

## 🔒 보안 고려사항

1. **API 키 관리**
   - 설정 파일은 `.gitignore`에 추가
   - 환경 변수 사용 권장

2. **데이터 접근**
   - 데이터베이스 읽기 전용 권한
   - SQL 인젝션 방지

3. **알림 보안**
   - HTTPS/TLS 사용
   - 민감 정보 마스킹

## 📈 성능 최적화

1. **데이터 수집**
   - 필요한 컬럼만 조회
   - 인덱스 활용
   - 기간별 파티셔닝

2. **분석 처리**
   - 캐싱 활용
   - 병렬 처리 (멀티 프로세싱)
   - 점진적 계산

3. **리포트 생성**
   - 템플릿 재사용
   - 이미지 최적화
   - 비동기 발송

## 🐛 오류 처리

### 계층별 오류 처리
1. **데이터 수집** - 빈 데이터 처리
2. **분석** - 기본값 반환
3. **생성** - 부분 생성 허용
4. **발송** - 재시도 메커니즘

### 로깅 전략
- 모든 작업 로깅
- 오류 스택 트레이스
- 성공/실패 통계

## 🚀 배포 전략

### 개발 환경
```bash
python demo.py  # 테스트
```

### 프로덕션 환경
```bash
# systemd 서비스 등록
sudo systemctl start auto-report
sudo systemctl enable auto-report
```

### Docker 배포
```dockerfile
FROM python:3.8
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## 📊 모니터링

### 시스템 헬스 체크
- 스케줄러 상태
- 리포트 생성 성공률
- 발송 성공률
- 처리 시간

### 메트릭 수집
- 리포트 생성 횟수
- 알림 발생 횟수
- 평균 처리 시간
- 오류 발생률

## 🔄 업데이트 로드맵

### v1.1
- [ ] 웹 대시보드
- [ ] 실시간 알림
- [ ] 커스텀 템플릿

### v1.2
- [ ] 머신러닝 인사이트
- [ ] 예측 분석
- [ ] 자동 전략 최적화

### v2.0
- [ ] 클라우드 배포
- [ ] 멀티 거래소 지원
- [ ] 모바일 앱

