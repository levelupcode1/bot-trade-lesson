# 🧪 텔레그램 봇 테스트 가이드

## 1. 봇 실행하기

### Windows PowerShell
```powershell
# 환경 변수 설정
$env:TELEGRAM_BOT_TOKEN='8245175655:AAFTnz7OR_JNzeRd0TyzuXkNPzz-CQV-wKQ'

# 봇 실행
python main.py
```

### 실행 성공 확인
다음과 같은 로그가 표시되면 성공:
```
✅ 텔레그램 봇이 성공적으로 시작되었습니다!
봇을 종료하려면 Ctrl+C를 누르세요.
...
Application started
```

---

## 2. 텔레그램에서 봇 찾기

### 방법 1: 직접 검색
1. 텔레그램 앱 열기
2. 검색창에 `@gilbert_ai_bot` 입력
3. 봇 선택 후 채팅 시작

### 방법 2: 링크 사용
- 브라우저에서: https://t.me/gilbert_ai_bot
- 텔레그램 자동 실행됨

---

## 3. 테스트 시나리오

### ✅ 시나리오 1: 기본 명령어 테스트

#### 1. `/start` 명령어
**입력:**
```
/start
```

**예상 출력:**
```
🚀 CryptoAutoTrader 봇에 오신 것을 환영합니다!

안녕하세요, [사용자명]님!

이 봇은 암호화폐 자동매매 시스템의 알림 및 제어 기능을 제공합니다.

📋 사용 가능한 명령어:
• /start - 봇 시작 및 환영 메시지
• /help - 도움말 표시
• /status - 시스템 상태 확인
...
```

#### 2. `/help` 명령어
**입력:**
```
/help
```

**예상 출력:**
```
📚 CryptoAutoTrader 봇 도움말

🔹 기본 명령어:
• /start - 봇 시작 및 환영 메시지
• /help - 이 도움말 표시
• /status - 시스템 상태 확인
...
```

#### 3. `/status` 명령어
**입력:**
```
/status
```

**예상 출력:**
```
📊 시스템 상태

🟢 봇 상태: 정상 작동 중
🟢 연결 상태: 텔레그램 API 연결됨
🟡 거래 시스템: 대기 중
...
```

---

### ✅ 시나리오 2: 일반 텍스트 메시지

**입력:**
```
안녕하세요
```

**예상 출력:**
```
안녕하세요! 👋

도움이 필요하시면 다음 명령어를 사용하세요:

• /start - 봇 시작하기
• /help - 도움말 보기
• /status - 시스템 상태 확인
...
```

---

### ✅ 시나리오 3: 잘못된 명령어

**입력:**
```
/unknown_command
```

**예상 동작:**
- 봇이 응답하지 않음 (핸들러가 등록되지 않은 명령어)
- 또는 기본 메시지 표시

---

## 4. 로그 확인

### 터미널 로그 확인
봇 실행 중인 터미널에서 다음과 같은 로그 확인:

```
# 메시지 수신 로그
2025-10-01 07:12:13,108 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot.../getUpdates "HTTP/1.1 200 OK"

# 명령어 처리 로그 (추가 구현 필요)
2025-10-01 07:12:15,234 - telegram.ext.Application - INFO - Received command: /start from user_id: 123456
```

### 파일 로그 확인
```powershell
# 최근 로그 20줄 확인
Get-Content logs\bot.log -Tail 20

# 실시간 로그 모니터링
Get-Content logs\bot.log -Wait
```

---

## 5. 디버깅 팁

### 문제 1: 봇이 응답하지 않음
**확인 사항:**
1. 봇이 실행 중인지 확인 (터미널 로그)
2. 올바른 봇을 선택했는지 확인 (@gilbert_ai_bot)
3. 환경 변수가 올바르게 설정되었는지 확인

**해결 방법:**
```powershell
# 봇 재시작
Ctrl+C  # 현재 봇 중지
$env:TELEGRAM_BOT_TOKEN='your_token'
python main.py
```

### 문제 2: 명령어가 작동하지 않음
**확인 사항:**
1. 명령어 앞에 `/` 붙였는지 확인
2. 오타 확인 (대소문자 구분 없음)
3. 로그에서 오류 메시지 확인

### 문제 3: 한글이 깨짐
**해결 방법:**
```powershell
# PowerShell 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## 6. 고급 테스트

### 동시 다중 사용자 테스트
1. 여러 텔레그램 계정에서 동시 접속
2. 동일 시간에 명령어 전송
3. 봇이 모든 요청을 처리하는지 확인

### 부하 테스트
```python
# 빠른 연속 명령어 전송
/start
/help
/status
/start
/help
```

### 긴 메시지 테스트
```
이것은 매우 긴 메시지입니다. 봇이 긴 메시지를 올바르게 처리하는지 테스트합니다...
(여러 줄 입력)
```

---

## 7. 성공 기준 체크리스트

- [ ] `/start` 명령어 응답 확인
- [ ] `/help` 명령어 응답 확인
- [ ] `/status` 명령어 응답 확인
- [ ] 일반 텍스트 메시지 응답 확인
- [ ] 한글 메시지 정상 표시
- [ ] 로그에 오류 없음
- [ ] 여러 명령어 연속 실행 가능
- [ ] 봇 종료 후 재시작 정상 작동

---

## 8. 다음 단계

테스트가 성공적으로 완료되면:

1. **추가 핸들러 구현**
   - /trades - 거래 내역
   - /positions - 포지션 현황
   - /pnl - 수익률

2. **인라인 키보드 추가**
   - 메뉴 버튼 구현
   - 콜백 쿼리 처리

3. **실제 거래 시스템 연동**
   - API 연결
   - 실시간 데이터 수신

4. **보안 강화**
   - 사용자 인증
   - 권한 관리

---

## 📞 문제 발생 시

1. **로그 확인**: `logs/bot.log` 파일 검토
2. **환경 변수 재확인**: 토큰이 올바른지 확인
3. **봇 재시작**: Ctrl+C 후 재실행
4. **패키지 재설치**: `pip install python-telegram-bot[all]==21.10`

## 📚 참고 자료

- [python-telegram-bot 공식 문서](https://docs.python-telegram-bot.org/)
- [텔레그램 Bot API](https://core.telegram.org/bots/api)
- [BotFather 가이드](https://core.telegram.org/bots#6-botfather)













