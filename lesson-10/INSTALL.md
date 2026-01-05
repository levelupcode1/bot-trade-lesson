# 텔레그램 봇 설치 가이드

## 🎯 빠른 시작

### 1단계: 의존성 설치

```bash
# python-telegram-bot 설치
pip install python-telegram-bot[all]==21.10

# 기타 필수 패키지 설치
pip install PyYAML python-dotenv
```

### 2단계: 환경 변수 설정

**Windows PowerShell:**
```powershell
$env:TELEGRAM_BOT_TOKEN="8245175655:AAFTnz7OR_JNzeRd0TyzuXkNPzz-CQV-wKQ"
```

**Windows CMD:**
```cmd
set TELEGRAM_BOT_TOKEN=8245175655:AAFTnz7OR_JNzeRd0TyzuXkNPzz-CQV-wKQ
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="8245175655:AAFTnz7OR_JNzeRd0TyzuXkNPzz-CQV-wKQ"
```

### 3단계: 봇 실행

```bash
python main.py
```

성공 메시지가 표시되면 텔레그램에서 봇을 테스트할 수 있습니다!

## ⚠️ 문제 해결

### 문제 1: httpx 버전 충돌

**증상:**
```
ERROR: Cannot install httpx==0.25.2 and python-telegram-bot because these package versions have conflicting dependencies.
```

**해결 방법:**
```bash
# 기존 httpx 제거
pip uninstall -y httpx

# 호환되는 버전 설치
pip install httpx~=0.27

# python-telegram-bot 재설치
pip install python-telegram-bot[all]==21.10
```

### 문제 2: 'Updater' object has no attribute '_Updater__polling_cleanup_cb'

**증상:**
```
'Updater' object has no attribute '_Updater__polling_cleanup_cb'
```

**원인:** Python 3.13과 python-telegram-bot 20.x 버전 간 호환성 문제

**해결 방법:**
```bash
# 호환되는 버전으로 업그레이드
pip install --upgrade python-telegram-bot[all]==21.10
```

### 문제 3: 환경 변수를 찾을 수 없음

**증상:**
```
❌ TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.
```

**해결 방법:**

1. **임시 설정 (현재 세션만):**
   ```bash
   $env:TELEGRAM_BOT_TOKEN="your_token_here"
   ```

2. **영구 설정 (Windows):**
   - 시스템 속성 → 고급 → 환경 변수
   - 새로 만들기: `TELEGRAM_BOT_TOKEN`

3. **영구 설정 (Linux/Mac):**
   ```bash
   echo 'export TELEGRAM_BOT_TOKEN="your_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

### 문제 4: 가상환경 충돌

**증상:**
여러 Python 환경에서 패키지 버전이 충돌

**해결 방법:**
```bash
# 새 가상환경 생성
python -m venv telegram-bot-env

# 가상환경 활성화 (Windows)
.\telegram-bot-env\Scripts\Activate.ps1

# 가상환경 활성화 (Linux/Mac)
source telegram-bot-env/bin/activate

# 깨끗한 환경에서 설치
pip install python-telegram-bot[all]==21.10
pip install PyYAML python-dotenv
```

## ✅ 설치 확인

봇이 정상적으로 작동하는지 확인:

1. **봇 실행:**
   ```bash
   python main.py
   ```

2. **로그 확인:**
   ```
   ✅ 텔레그램 봇이 성공적으로 시작되었습니다!
   Application started
   ```

3. **텔레그램 테스트:**
   - 봇에게 `/start` 명령 전송
   - 환영 메시지 수신 확인
   - `/help`로 명령어 목록 확인
   - `/status`로 시스템 상태 확인

## 📋 패키지 버전 정보

정상 작동 확인된 버전:

- **Python:** 3.13.5 (권장: 3.8+)
- **python-telegram-bot:** 21.10
- **httpx:** 0.27.x 또는 0.28.x
- **PyYAML:** 6.0+
- **python-dotenv:** 1.0.0+

## 🔗 추가 리소스

- [python-telegram-bot 공식 문서](https://python-telegram-bot.org/)
- [텔레그램 봇 API](https://core.telegram.org/bots/api)
- [BotFather로 봇 생성](https://t.me/botfather)

## 💡 팁

1. **가상환경 사용 권장:**
   - 프로젝트별 독립적인 패키지 관리
   - 버전 충돌 최소화

2. **환경 변수 대신 .env 파일:**
   ```bash
   # .env 파일 생성
   echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
   ```

3. **로그 모니터링:**
   ```bash
   tail -f logs/bot.log
   ```













