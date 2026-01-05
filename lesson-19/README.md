# Lesson 19: 멜론 최신곡 크롤링

멜론 최신곡 페이지(https://www.melon.com/new/index.htm)에서 최신곡 순위 리스트를 크롤링하는 프로젝트입니다.

## 📋 목차

- [기능](#기능)
- [설치](#설치)
- [사용 방법](#사용-방법)
- [n8n 사용 방법](#n8n-사용-방법)
- [출력 데이터](#출력-데이터)
- [주의사항](#주의사항)

## 🎯 기능

- ✅ 멜론 최신곡 페이지 크롤링
- ✅ 순위, 곡명, 아티스트, 앨범 정보 추출
- ✅ 곡 ID, 앨범 ID 추출
- ✅ 앨범 이미지 URL 추출
- ✅ JSON 파일로 저장
- ✅ n8n Code 노드용 JavaScript 코드 제공

## 📦 설치

```bash
# 프로젝트 디렉토리로 이동
cd lesson-19

# 의존성 설치
pip install -r requirements.txt
```

## 🚀 사용 방법

### Python 스크립트 실행

```bash
python melon_new_songs_crawler.py
```

### 실행 결과

```
멜론 최신곡 페이지 크롤링 시작: https://www.melon.com/new/index.htm
총 50개의 행을 찾았습니다.
총 50개의 곡을 추출했습니다.

================================================================================
멜론 최신곡 TOP 20
================================================================================
순위   곡명                            아티스트              앨범                      
--------------------------------------------------------------------------------
1      그리워 혼자 하는 말 (from 마지막 썸머 OST) 조째즈              그리워 혼자 하는 말 (from 마지막 썸머 OST)
2      돌아오는 길 (The Way Back)    SKINZ (스킨즈)       돌아오는 길 (The Way Back)
3      잠시만 안녕                    리차드파커스          모범택시3 OST Part.2
...

결과를 melon_new_songs_20251129_230000.json에 저장했습니다.

✅ 크롤링 완료: 총 50개 곡
```

## 🔧 n8n 사용 방법

### 워크플로우 구성

```
HTTP Request → Code → Set → Database
```

### 1단계: HTTP Request 노드 설정

**URL:**
```
https://www.melon.com/new/index.htm
```

**Headers:**
```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "ko-KR,ko;q=0.9"
}
```

### 2단계: Code 노드 설정

1. **Mode**: JavaScript 선택
2. **Code**: `n8n_melon_new_songs.js` 파일의 내용을 복사하여 붙여넣기

### 3단계: 결과 확인

Code 노드 실행 후 출력 예시:

```json
[
  {
    "json": {
      "rank": 1,
      "song_title": "그리워 혼자 하는 말 (from 마지막 썸머 OST)",
      "artist": "조째즈",
      "album": "그리워 혼자 하는 말 (from 마지막 썸머 OST)",
      "album_image": "https://cdnimg.melon.co.kr/...",
      "song_id": "600585793",
      "album_id": "12411275",
      "snapshot_date": "2025-11-29",
      "crawled_at": "2025-11-29T23:00:00.000Z"
    }
  },
  ...
]
```

## 📊 출력 데이터

### JSON 형식

```json
{
  "rank": 1,
  "song_title": "그리워 혼자 하는 말 (from 마지막 썸머 OST)",
  "artist": "조째즈",
  "album": "그리워 혼자 하는 말 (from 마지막 썸머 OST)",
  "album_image": "https://cdnimg.melon.co.kr/...",
  "song_id": "600585793",
  "album_id": "12411275",
  "snapshot_date": "2025-11-29",
  "crawled_at": "2025-11-29T23:00:00.000Z"
}
```

### 필드 설명

| 필드 | 설명 | 예시 |
|------|------|------|
| `rank` | 순위 | 1 |
| `song_title` | 곡명 | "그리워 혼자 하는 말 (from 마지막 썸머 OST)" |
| `artist` | 아티스트 | "조째즈" |
| `album` | 앨범명 | "그리워 혼자 하는 말 (from 마지막 썸머 OST)" |
| `album_image` | 앨범 이미지 URL | "https://cdnimg.melon.co.kr/..." |
| `song_id` | 곡 ID | "600585793" |
| `album_id` | 앨범 ID | "12411275" |
| `snapshot_date` | 스냅샷 날짜 | "2025-11-29" |
| `crawled_at` | 크롤링 시간 | "2025-11-29T23:00:00.000Z" |

## 💾 데이터베이스 저장 예시

### PostgreSQL

```sql
CREATE TABLE melon_new_songs (
    id SERIAL PRIMARY KEY,
    rank INTEGER NOT NULL,
    song_title VARCHAR(255) NOT NULL,
    artist VARCHAR(255),
    album VARCHAR(255),
    album_image TEXT,
    song_id VARCHAR(50),
    album_id VARCHAR(50),
    snapshot_date DATE NOT NULL,
    crawled_at TIMESTAMP NOT NULL,
    UNIQUE(snapshot_date, rank)
);

-- 데이터 삽입
INSERT INTO melon_new_songs (
    rank, song_title, artist, album, 
    album_image, song_id, album_id, 
    snapshot_date, crawled_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9
)
ON CONFLICT (snapshot_date, rank) 
DO UPDATE SET
    song_title = EXCLUDED.song_title,
    artist = EXCLUDED.artist,
    album = EXCLUDED.album,
    album_image = EXCLUDED.album_image,
    song_id = EXCLUDED.song_id,
    album_id = EXCLUDED.album_id,
    crawled_at = EXCLUDED.crawled_at;
```

## ⚠️ 주의사항

### 1. 법적 준수

- ✅ **robots.txt 확인**: https://www.melon.com/robots.txt
- ✅ **이용약관 확인**: 크롤링 허용 여부 확인
- ✅ **저작권 존중**: 데이터 사용 시 출처 명시

### 2. 기술적 주의

- ⚠️ **요청 간격**: 최소 1초 간격으로 요청
- ⚠️ **User-Agent 설정**: 브라우저처럼 보이도록 설정
- ⚠️ **에러 처리**: 네트워크 오류 대비
- ⚠️ **HTML 구조 변경**: 멜론 페이지 구조 변경 시 코드 수정 필요

### 3. 윤리적 크롤링

- ✅ **서버 부하 고려**: 과도한 요청 방지
- ✅ **공개 데이터만 수집**: 로그인 필요 데이터 제외
- ✅ **데이터 출처 명시**: 사용 시 출처 표기

## 🔄 자동화 설정

### Schedule Trigger (n8n)

매일 자정에 크롤링:

```json
{
  "rule": {
    "interval": [
      {
        "field": "days",
        "daysInterval": 1
      }
    ],
    "hour": 0,
    "minute": 0
  }
}
```

또는 Cron Expression:

```
0 0 * * *  // 매일 자정
```

## 🐛 문제 해결

### 문제 1: 데이터가 추출되지 않음

**원인**: HTML 구조 변경 또는 선택자 오류

**해결**:
1. 브라우저 개발자 도구로 실제 HTML 구조 확인
2. CSS Selector 수정
3. 대체 선택자 사용

### 문제 2: 일부 데이터만 추출됨

**원인**: 동적 로딩 또는 JavaScript 렌더링

**해결**:
1. Playwright 노드 사용 (n8n)
2. Selenium 사용 (Python)
3. 페이지 로딩 대기 시간 추가

### 문제 3: 403 Forbidden 오류

**원인**: 봇 차단

**해결**:
1. User-Agent 설정 확인
2. 요청 간격 늘리기
3. 헤더 추가 (Referer 등)

## 📊 구글 시트 연동

크롤링 결과를 구글 시트에 자동으로 저장할 수 있습니다.

### 빠른 시작

1. **필요한 라이브러리 설치**
   ```bash
   pip install gspread google-auth
   ```

2. **구글 클라우드 설정**
   - 자세한 설정 방법은 [GOOGLE_SHEETS_SETUP.md](./GOOGLE_SHEETS_SETUP.md) 참고
   - 서비스 계정 생성 및 인증 파일 다운로드
   - 구글 시트에 서비스 계정 이메일 공유

3. **업로드 실행**
   ```bash
   # 가장 최근 JSON 파일 자동 사용
   python save_to_google_sheets.py
   
   # 또는 간단한 스크립트 사용
   python upload_to_sheets.py melon_new_songs_20251130_011219.json
   ```

### Python 코드에서 사용

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

### 구글 시트 URL

업로드된 데이터는 다음 시트에서 확인할 수 있습니다:
https://docs.google.com/spreadsheets/d/1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q

## 📚 참고 자료

- [멜론 최신곡 페이지](https://www.melon.com/new/index.htm)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [n8n Code 노드 문서](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)
- [Cheerio 문서](https://cheerio.js.org/)
- [구글 시트 설정 가이드](./GOOGLE_SHEETS_SETUP.md)
- [gspread 문서](https://docs.gspread.org/)

## 📝 라이선스

이 프로젝트는 교육 목적으로 만들어졌습니다.
실제 사용 시 멜론의 이용약관을 준수하세요.

---

**Made with ❤️ for web scraping learners**

