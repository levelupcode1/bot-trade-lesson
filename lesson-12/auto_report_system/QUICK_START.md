# 🚀 빠른 시작 가이드

## 5분 만에 시작하기

### 1단계: 패키지 설치 (1분)

```bash
cd lesson-12/auto_report_system
pip install -r requirements.txt
```

### 2단계: 설정 파일 생성 (2분)

```bash
# 예시 파일 복사
cp config.yaml.example config.yaml

# 설정 파일 수정 (선택사항)
# 기본 설정으로도 HTML 리포트 생성 가능
```

### 3단계: 테스트 실행 (2분)

```bash
# 데모 모드로 실행
python demo.py

# 1번 선택 -> 일간 리포트 생성 테스트
```

## 📝 기본 설정으로 시작하기

최소 설정으로 바로 시작할 수 있습니다:

```yaml
# config.yaml
report:
  output_dir: "auto_reports"
  output_formats: ["html"]  # HTML만 생성
  send_telegram: false  # 텔레그램 비활성화
  send_email: false  # 이메일 비활성화

schedule:
  daily:
    enabled: true
    hour: 23
    minute: 0
```

## 🎯 주요 사용 시나리오

### 시나리오 1: 매일 자동 리포트

```bash
# main.py 실행 (백그라운드)
python main.py &

# 매일 23:00에 자동으로 일간 리포트 생성
# 리포트는 auto_reports/ 폴더에 저장됨
```

### 시나리오 2: 수동 리포트 생성

```python
from core.report_manager import ReportManager
from core.config import ConfigManager

config = ConfigManager.load_config()
manager = ReportManager(config)

# 지금 즉시 일간 리포트 생성
files = manager.generate_report('daily')
print(f"생성된 리포트: {files}")
```

### 시나리오 3: 텔레그램 알림 설정

```yaml
# config.yaml
telegram:
  token: "YOUR_BOT_TOKEN"  # BotFather에서 발급
  chat_id: "YOUR_CHAT_ID"

report:
  send_telegram: true
```

```bash
# 텔레그램 봇 생성
1. 텔레그램에서 @BotFather 검색
2. /newbot 명령으로 봇 생성
3. 토큰 복사
4. 봇에게 메시지 전송
5. https://api.telegram.org/bot<TOKEN>/getUpdates 에서 chat_id 확인
```

## 📊 생성되는 리포트

### HTML 리포트 (기본)
- `auto_reports/daily_report_YYYYMMDD_HHMMSS.html`
- 웹 브라우저에서 바로 확인 가능
- 차트와 인사이트 포함

### PDF 리포트 (선택)
```bash
pip install reportlab
```

```yaml
report:
  output_formats: ["html", "pdf"]
```

### Excel 리포트 (선택)
```bash
pip install openpyxl
```

```yaml
report:
  output_formats: ["html", "excel"]
```

## 🔍 리포트 내용

생성되는 리포트에는 다음 정보가 포함됩니다:

### 일간 리포트
✅ 오늘의 수익률  
✅ 총 거래 수  
✅ 승률  
✅ 활동 시간대  
✅ 코인별 성과  
✅ AI 인사이트 및 권장사항

### 주간/월간 리포트
위 내용에 추가로:  
✅ 일별/주별 추이  
✅ 전략별 비교  
✅ 리스크 지표  
✅ 장기 트렌드

## 🚨 이상 상황 알림

설정한 임계값을 초과하면 자동 알림:

- 낙폭 10% 이상
- 일일 손실 5% 이상
- 승률 40% 이하
- 거래 중단 감지

## 💡 팁

### 처음 사용하는 경우
1. `python demo.py`로 테스트
2. HTML 리포트 확인
3. 만족스러우면 스케줄러 실행

### 텔레그램 설정이 어려운 경우
- 일단 `send_telegram: false`로 시작
- HTML 파일만 확인하다가
- 나중에 텔레그램 설정

### 데이터가 없는 경우
- 실제 거래 데이터가 쌓일 때까지 대기
- 또는 샘플 데이터로 테스트

## ❓ 문제 해결

### "설정 파일이 없습니다"
```bash
cp config.yaml.example config.yaml
```

### "apscheduler를 찾을 수 없습니다"
```bash
pip install apscheduler
```

### "데이터가 없습니다"
- 거래 데이터가 `lesson-12/data/trading.db`에 있는지 확인
- 샘플 데이터 생성 스크립트 실행 (상위 폴더)

## 📞 지원

문제가 발생하면 README.md의 "문제 해결" 섹션을 확인하세요!

