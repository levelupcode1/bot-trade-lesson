# 구글 시트 연동 설정 가이드

## 📋 목차

- [필요한 라이브러리 설치](#필요한-라이브러리-설치)
- [구글 클라우드 설정](#구글-클라우드-설정)
- [사용 방법](#사용-방법)
- [문제 해결](#문제-해결)

## 📦 필요한 라이브러리 설치

```bash
pip install gspread google-auth
```

또는 requirements.txt로 설치:

```bash
pip install -r requirements.txt
```

## 🔧 구글 클라우드 설정

### 1단계: Google Cloud Console 접속

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Google 계정으로 로그인

### 2단계: 프로젝트 생성

1. 상단 메뉴에서 프로젝트 선택 또는 새 프로젝트 생성
2. 프로젝트 이름 입력 (예: "melon-crawler")

### 3단계: Google Sheets API 활성화

1. 좌측 메뉴에서 **"API 및 서비스"** > **"라이브러리"** 클릭
2. 검색창에 "Google Sheets API" 입력
3. **"Google Sheets API"** 선택 후 **"사용 설정"** 클릭
4. **"Google Drive API"**도 활성화 (필수)

### 4단계: 서비스 계정 생성

1. **"API 및 서비스"** > **"사용자 인증 정보"** 이동
2. 상단 **"사용자 인증 정보 만들기"** 클릭
3. **"서비스 계정"** 선택
4. 서비스 계정 정보 입력:
   - 서비스 계정 이름: `melon-crawler-service`
   - 서비스 계정 ID: 자동 생성됨
   - 설명: (선택사항)
5. **"만들기"** 클릭

### 5단계: 서비스 계정 키 생성

1. 생성된 서비스 계정 클릭
2. **"키"** 탭 이동
3. **"키 추가"** > **"새 키 만들기"** 클릭
4. 키 유형: **"JSON"** 선택
5. **"만들기"** 클릭
6. JSON 파일이 자동으로 다운로드됨

### 6단계: 구글 시트 공유 설정

1. 구글 시트 열기: https://docs.google.com/spreadsheets/d/1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q
2. 우측 상단 **"공유"** 버튼 클릭
3. 다운로드한 JSON 파일에서 `client_email` 값을 복사
   - 예: `melon-crawler-service@프로젝트명.iam.gserviceaccount.com`
4. 이메일을 공유 대상에 추가
5. 권한: **"편집자"** 선택
6. **"완료"** 클릭

### 7단계: 인증 파일 설정

다운로드한 JSON 파일을 프로젝트 폴더에 복사:

**방법 1: 파일명을 credentials.json으로 저장**
```
lesson-19/
  ├── credentials.json  ← 여기에 저장
  ├── save_to_google_sheets.py
  └── ...
```

**방법 2: 환경변수 설정**
```bash
# Windows (PowerShell)
$env:GOOGLE_CREDENTIALS_PATH="D:\projects\cursor-proj\bot-trade-lesson\lesson-19\credentials.json"

# Windows (CMD)
set GOOGLE_CREDENTIALS_PATH=D:\projects\cursor-proj\bot-trade-lesson\lesson-19\credentials.json

# Linux/Mac
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
```

## 🚀 사용 방법

### 기본 사용

```bash
# 가장 최근 JSON 파일 자동 사용
python save_to_google_sheets.py

# 특정 JSON 파일 지정
python save_to_google_sheets.py melon_new_songs_20251130_011219.json
```

### Python 코드에서 사용

```python
from save_to_google_sheets import GoogleSheetsUploader

# 업로더 생성
uploader = GoogleSheetsUploader(
    spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
    credentials_path="credentials.json"
)

# JSON 파일에서 데이터 로드
data = uploader.load_json_data("melon_new_songs_20251130_011219.json")

# 구글 시트에 업로드
uploader.upload_data(data, worksheet_name="멜론최신곡_20251130")
```

### 크롤링과 함께 사용

```python
from melon_new_songs_crawler import MelonNewSongsCrawler
from save_to_google_sheets import GoogleSheetsUploader

# 크롤링
crawler = MelonNewSongsCrawler()
songs = crawler.crawl()

# 구글 시트에 업로드
uploader = GoogleSheetsUploader(
    spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
    credentials_path="credentials.json"
)
uploader.upload_data(songs, worksheet_name="멜론최신곡")
```

## 📊 업로드되는 데이터 형식

| 순위 | 곡명 | 아티스트 | 앨범 | 곡 ID | 앨범 ID | 앨범 이미지 | 스냅샷 날짜 | 크롤링 시간 |
|------|------|----------|------|-------|---------|-------------|-------------|-------------|
| 1 | 그리워 혼자 하는 말... | 조째즈 | ... | 600585793 | 12411275 | https://... | 2025-11-30 | 2025-11-30T01:12:19 |

## ⚠️ 문제 해결

### 오류 1: 인증 파일을 찾을 수 없음

```
❌ 구글 서비스 계정 인증 파일을 찾을 수 없습니다.
```

**해결:**
- JSON 파일이 프로젝트 폴더에 있는지 확인
- 파일명이 `credentials.json`인지 확인
- 또는 환경변수 `GOOGLE_CREDENTIALS_PATH` 설정

### 오류 2: 권한 오류

```
❌ 업로드 오류: Insufficient Permission
```

**해결:**
1. 구글 시트에 서비스 계정 이메일 공유 확인
2. 권한이 "편집자"인지 확인
3. Google Sheets API 활성화 확인

### 오류 3: API 비활성화

```
❌ 업로드 오류: API not enabled
```

**해결:**
1. Google Cloud Console에서 Google Sheets API 활성화
2. Google Drive API도 활성화 확인

### 오류 4: 시트를 찾을 수 없음

```
❌ 업로드 오류: Spreadsheet not found
```

**해결:**
1. 구글 시트 ID 확인
2. 서비스 계정이 시트에 공유되어 있는지 확인

## 🔒 보안 주의사항

1. **JSON 파일 보안**
   - 절대 Git에 커밋하지 마세요
   - `.gitignore`에 추가:
     ```
     credentials.json
     service_account.json
     *.json
     !requirements.txt
     ```

2. **환경변수 사용 권장**
   - 프로덕션 환경에서는 환경변수 사용
   - JSON 파일을 안전한 위치에 저장

## 📚 참고 자료

- [gspread 문서](https://docs.gspread.org/)
- [Google Sheets API 문서](https://developers.google.com/sheets/api)
- [서비스 계정 생성 가이드](https://cloud.google.com/iam/docs/service-accounts)

---

**문의사항이나 문제 발생 시 이슈를 등록해주세요!**

