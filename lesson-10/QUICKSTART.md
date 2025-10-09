# ⚡ 빠른 시작 가이드

## 1️⃣ 설치 (1분)

```powershell
# 1. python-telegram-bot 설치
pip install python-telegram-bot[all]==21.10

# 2. 기타 패키지 설치
pip install PyYAML python-dotenv
```

---

## 2️⃣ 환경 설정 (30초)

```powershell
# 환경 변수 설정
$env:TELEGRAM_BOT_TOKEN='8245175655:AAFTnz7OR_JNzeRd0TyzuXkNPzz-CQV-wKQ'
```

---

## 3️⃣ 봇 실행 (10초)

```powershell
python main.py
```

**성공 메시지:**
```
✅ 텔레그램 봇이 성공적으로 시작되었습니다!
Application started
```

---

## 4️⃣ 텔레그램에서 테스트 (1분)

### 📱 봇 찾기
1. 텔레그램 앱 열기
2. 검색: `@gilbert_ai_bot`
3. 봇 클릭하여 채팅 시작

### 🎮 명령어 테스트

#### 기본 테스트
```
/start
```
→ 메인 메뉴와 인라인 버튼 표시

#### 거래 내역
```
/trades
```
→ 최근 5개 거래 내역 표시

#### 수익률
```
/profit
```
→ 수익률 분석 및 통계 표시

#### 시스템 상태
```
/status
```
→ 현재 시스템 상태 및 제어 버튼

#### 거래 제어
```
/stop
```
→ 거래 중지 확인

```
/start_trading
```
→ 거래 시작 확인

---

## 🎯 핵심 명령어 요약

| 명령어 | 기능 |
|--------|------|
| `/start` | 메인 메뉴 |
| `/trades` | 거래 내역 |
| `/profit` | 수익률 |
| `/status` | 시스템 상태 |
| `/settings` | 설정 |
| `/stop` | 거래 중지 |
| `/start_trading` | 거래 시작 |

---

## 💡 인라인 버튼 사용

`/start` 명령 후 버튼 클릭만으로 모든 기능 사용 가능:

```
📊 거래내역 | 💰 수익률
🖥️ 상태    | ⚙️ 설정
      ❓ 도움말
```

---

## 🔍 테스트 체크리스트

- [ ] 봇이 정상 실행됨
- [ ] `/start` 명령어 작동
- [ ] 인라인 버튼 클릭 가능
- [ ] `/trades` 거래 내역 표시
- [ ] `/profit` 수익률 표시
- [ ] `/status` 상태 표시
- [ ] 거래 중지/시작 기능 작동

---

## 🚨 문제 해결

### 봇이 응답 안 함
```powershell
# 1. 토큰 재확인
$env:TELEGRAM_BOT_TOKEN='your_actual_token'

# 2. 봇 재시작
Ctrl+C
python main.py
```

### 패키지 오류
```powershell
# httpx 충돌 해결
pip uninstall -y httpx
pip install httpx~=0.27
pip install python-telegram-bot[all]==21.10
```

---

## 📚 더 알아보기

- **상세 가이드**: [TRADING_FEATURES_GUIDE.md](TRADING_FEATURES_GUIDE.md)
- **테스트 가이드**: [BOT_TEST_GUIDE.md](BOT_TEST_GUIDE.md)
- **전체 문서**: [README.md](README.md)

---

## 🎉 완료!

이제 텔레그램에서 `@gilbert_ai_bot`으로 이동하여 봇을 사용해보세요!

**첫 명령어:**
```
/start
```








