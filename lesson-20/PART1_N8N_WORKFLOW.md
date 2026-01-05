# Part 1: n8n 워크플로우 구축

매일 아침 8시에 자동으로 멜론 차트를 크롤링하는 n8n 워크플로우를 구축합니다.

## 📋 목차

- [n8n 설치 및 설정](#n8n-설치-및-설정)
- [워크플로우 구조 설계](#워크플로우-구조-설계)
- [스케줄 트리거 설정](#스케줄-트리거-설정)
- [HTTP Request 노드 설정](#http-request-노드-설정)
- [Code 노드로 데이터 파싱](#code-노드로-데이터-파싱)
- [구글 시트 저장](#구글-시트-저장)
- [테스트 및 검증](#테스트-및-검증)
- [문제 해결](#문제-해결)

## 🎯 학습 목표

이 파트를 완료하면:
- ✅ n8n 워크플로우를 생성하고 설정할 수 있습니다
- ✅ 스케줄 트리거를 사용하여 자동 실행을 설정할 수 있습니다
- ✅ HTTP Request로 웹 페이지를 크롤링할 수 있습니다
- ✅ Code 노드로 데이터를 파싱하고 변환할 수 있습니다

---

## 1. n8n 설치 및 설정

### 1.1 n8n 설치 방법

n8n은 여러 방법으로 설치할 수 있습니다:

#### 방법 1: npx로 실행 (가장 간단)

```bash
npx n8n
```

#### 방법 2: Docker로 실행

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

#### 방법 3: npm으로 전역 설치

```bash
npm install n8n -g
n8n start
```

### 1.2 n8n 접속

설치 후 브라우저에서 다음 URL로 접속:

```
http://localhost:5678
```

첫 접속 시 계정을 생성합니다.

### 1.3 n8n 기본 사용법

- **워크플로우 생성**: 좌측 상단 "+" 버튼 클릭
- **노드 추가**: "+" 버튼 클릭하여 노드 선택
- **노드 연결**: 노드의 출력 핀을 드래그하여 다음 노드의 입력 핀에 연결
- **워크플로우 실행**: 우측 상단 "Execute Workflow" 버튼 클릭

---

## 2. 워크플로우 구조 설계

### 2.1 전체 워크플로우 구조

```
┌─────────────────┐
│  Schedule       │ (매일 8시 트리거)
│     Trigger     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │ (멜론 차트 페이지 가져오기)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Code Node     │ (HTML 파싱 및 데이터 추출)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Google Sheets  │ (데이터 저장)
└─────────────────┘
```

### 2.2 각 노드의 역할

| 노드 | 역할 | 설명 |
|------|------|------|
| Schedule Trigger | 트리거 | 매일 8시에 워크플로우 실행 |
| HTTP Request | 데이터 수집 | 멜론 차트 페이지 HTML 가져오기 |
| Code | 데이터 처리 | HTML 파싱하여 구조화된 데이터 생성 |
| Google Sheets | 데이터 저장 | 구글 시트에 데이터 저장 |

---

## 3. 스케줄 트리거 설정

### 3.1 Schedule Trigger 노드 추가

1. n8n에서 새 워크플로우 생성
2. "+" 버튼 클릭
3. "Schedule Trigger" 검색 후 선택

### 3.2 매일 8시 설정

**Cron Expression 방식 (권장):**

```json
{
  "rule": {
    "interval": [
      {
        "field": "cronExpression",
        "expression": "0 8 * * *"
      }
    ]
  }
}
```

**설정 설명:**
- `0 8 * * *` = 매일 8시 0분
- Cron 형식: `분 시 일 월 요일`

**다른 시간 설정 예시:**
- `0 9 * * *` = 매일 9시
- `0 8 * * 1-5` = 평일 8시
- `0 */2 * * *` = 2시간마다

### 3.3 노드 설정

Schedule Trigger 노드 설정:

```json
{
  "triggerTimes": {
    "item": [
      {
        "mode": "everyDay",
        "hour": 8,
        "minute": 0
      }
    ]
  }
}
```

---

## 4. HTTP Request 노드 설정

### 4.1 HTTP Request 노드 추가

1. Schedule Trigger 노드 다음에 "+" 버튼 클릭
2. "HTTP Request" 검색 후 선택
3. Schedule Trigger 노드와 연결

### 4.2 멜론 차트 URL 설정

**Method**: `GET`

**URL**: 
```
https://www.melon.com/chart/index.htm
```

또는 최신곡:
```
https://www.melon.com/new/index.htm
```

### 4.3 Headers 설정

봇 차단을 방지하기 위해 브라우저처럼 보이도록 헤더 설정:

```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
  "Referer": "https://www.melon.com/"
}
```

### 4.4 Options 설정

```json
{
  "timeout": 10000,
  "redirect": {
    "followRedirects": true,
    "maxRedirects": 5
  }
}
```

### 4.5 테스트

"Execute Node" 버튼을 클릭하여 테스트:

- ✅ 성공: HTML 데이터가 반환됨
- ❌ 실패: 에러 메시지 확인

---

## 5. Code 노드로 데이터 파싱

### 5.1 Code 노드 추가

1. HTTP Request 노드 다음에 "+" 버튼 클릭
2. "Code" 검색 후 선택
3. HTTP Request 노드와 연결

### 5.2 JavaScript 코드 작성

**Mode**: JavaScript 선택

**옵션 1: Cheerio 사용 (권장)**

```javascript
const cheerio = require('cheerio');

// 입력 데이터에서 HTML 추출
const inputData = $input.first().json;
const html = inputData.data || inputData.body || inputData.html || '';

if (!html) {
  throw new Error('HTML 데이터가 없습니다.');
}

// HTML 파싱
const $ = cheerio.load(html);

// 결과 배열
const songs = [];
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

// 차트 테이블에서 데이터 추출
$('.lst50 tbody tr').each((index, element) => {
  const $row = $(element);
  
  // 순위
  const rankText = $row.find('td.rank').text().trim();
  const rankMatch = rankText.match(/(\d+)/);
  const rank = rankMatch ? parseInt(rankMatch[1]) : 0;
  
  if (rank === 0) return;
  
  // 곡명
  const songLink = $row.find('.ellipsis.rank01 a').first();
  const songTitle = songLink.text().trim();
  if (!songTitle) return;
  
  // 곡 ID
  const songHref = songLink.attr('href') || '';
  const songIdMatch = songHref.match(/songId=(\d+)/);
  const songId = songIdMatch ? songIdMatch[1] : '';
  
  // 아티스트
  const artistLink = $row.find('.ellipsis.rank02 a').first();
  const artist = artistLink.text().trim();
  
  // 앨범
  const albumLink = $row.find('.ellipsis.rank03 a').first();
  const album = albumLink.text().trim();
  
  // 앨범 ID
  const albumHref = albumLink.attr('href') || '';
  const albumIdMatch = albumHref.match(/albumId=(\d+)/);
  const albumId = albumIdMatch ? albumIdMatch[1] : '';
  
  // 앨범 이미지
  const albumImage = $row.find('td img').attr('src') || '';
  
  // 순위 변동
  const changeText = $row.find('.rank_wrap .rank').text().trim();
  let rankChange = 0;
  if (changeText.includes('상승')) {
    const match = changeText.match(/(\d+)/);
    rankChange = match ? parseInt(match[1]) : 0;
  } else if (changeText.includes('하락')) {
    const match = changeText.match(/(\d+)/);
    rankChange = match ? -parseInt(match[1]) : 0;
  } else if (changeText.includes('진입')) {
    rankChange = 999;
  }
  
  songs.push({
    rank: rank,
    song_title: songTitle,
    artist: artist,
    album: album,
    album_image: albumImage,
    song_id: songId,
    album_id: albumId,
    rank_change: rankChange,
    snapshot_date: today,
    crawled_at: now
  });
});

// 순위별로 정렬
songs.sort((a, b) => a.rank - b.rank);

// n8n 형식으로 반환
return songs.map(song => ({ json: song }));
```

**옵션 2: 순수 JavaScript (Cheerio 없이)**

```javascript
// HTML 추출
const html = $input.first().json.data || $input.first().json.body || '';

if (!html) {
  throw new Error('HTML 데이터가 없습니다.');
}

const songs = [];
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

// HTML에서 텍스트 추출 헬퍼 함수
function extractText(html) {
  return html
    .replace(/<[^>]+>/g, '') // HTML 태그 제거
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}

// 테이블 행 찾기
const rowPattern = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
let rowMatch;
let rankCounter = 1;

while ((rowMatch = rowPattern.exec(html)) !== null) {
  const row = rowMatch[1];
  
  // 헤더 스킵
  if (row.includes('<th')) continue;
  
  // 순위 찾기
  let rank = 0;
  const rankMatch = row.match(/<td[^>]*class="rank"[^>]*>[\s\S]*?(\d+)/i) ||
                    row.match(/(\d+)위/i);
  if (rankMatch) {
    rank = parseInt(rankMatch[1]);
  } else {
    rank = rankCounter; // 순위를 찾지 못하면 카운터 사용
  }
  
  // 곡명 찾기
  const songMatch = row.match(/<a[^>]*href[^>]*goSongDetail[^>]*>([\s\S]*?)<\/a>/i);
  if (!songMatch) continue;
  
  const songTitle = extractText(songMatch[1]);
  if (!songTitle) continue;
  
  // 곡 ID
  const songIdMatch = row.match(/goSongDetail\(['"](\d+)['"]\)/i);
  const songId = songIdMatch ? songIdMatch[1] : '';
  
  // 아티스트 찾기
  const artistPattern = /<a[^>]*href[^>]*goArtistDetail[^>]*>([\s\S]*?)<\/a>/gi;
  const artists = [];
  let artistMatch;
  while ((artistMatch = artistPattern.exec(row)) !== null) {
    const artistText = extractText(artistMatch[1]);
    if (artistText) artists.push(artistText);
  }
  const artist = artists.join(', ');
  
  // 앨범 찾기
  const albumMatch = row.match(/<a[^>]*href[^>]*goAlbumDetail[^>]*>([\s\S]*?)<\/a>/i);
  const album = albumMatch ? extractText(albumMatch[1]) : '';
  
  // 앨범 ID
  const albumIdMatch = row.match(/goAlbumDetail\(['"](\d+)['"]\)/i);
  const albumId = albumIdMatch ? albumIdMatch[1] : '';
  
  // 앨범 이미지
  const imgMatch = row.match(/<img[^>]*src=["']([^"']+)["']/i);
  let albumImage = imgMatch ? imgMatch[1] : '';
  if (albumImage && albumImage.startsWith('//')) {
    albumImage = 'https:' + albumImage;
  }
  
  // 순위 변동
  let rankChange = 0;
  const changeMatch = row.match(/(상승|하락|진입)[\s\S]*?(\d+)/i);
  if (changeMatch) {
    const type = changeMatch[1];
    const value = parseInt(changeMatch[2] || '0');
    if (type.includes('상승')) rankChange = value;
    else if (type.includes('하락')) rankChange = -value;
    else if (type.includes('진입')) rankChange = 999;
  }
  
  songs.push({
    rank: rank,
    song_title: songTitle,
    artist: artist,
    album: album,
    album_image: albumImage,
    song_id: songId,
    album_id: albumId,
    rank_change: rankChange,
    snapshot_date: today,
    crawled_at: now
  });
  
  rankCounter++;
}

// 정렬
songs.sort((a, b) => a.rank - b.rank);

// 결과 반환
return songs.map(song => ({ json: song }));
```

### 5.3 에러 처리 추가

```javascript
try {
  // ... 위의 코드 ...
} catch (error) {
  console.error('크롤링 에러:', error.message);
  return [{
    json: {
      error: true,
      error_message: error.message,
      timestamp: new Date().toISOString()
    }
  }];
}
```

### 5.4 테스트

"Execute Node" 버튼으로 테스트:

- ✅ 성공: 곡 데이터 배열이 반환됨
- ❌ 실패: 에러 메시지 확인 및 HTML 구조 재확인

---

## 6. 구글 시트 저장

### 6.1 Google Sheets 노드 추가

1. Code 노드 다음에 "+" 버튼 클릭
2. "Google Sheets" 검색 후 선택
3. Code 노드와 연결

### 6.2 인증 설정

**Authentication**: OAuth2 또는 Service Account

**Service Account 방식 (권장):**

1. Google Cloud Console에서 서비스 계정 생성
2. JSON 키 파일 다운로드
3. n8n Credentials에 추가:
   - Credentials → Add Credential → Google Service Account
   - JSON 파일 내용 붙여넣기

### 6.3 노드 설정

**Operation**: `Append or Update`

**Spreadsheet ID**: 
```
1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q
```

**Sheet Name**: 
```
멜론차트
```

**Columns**: 
```
순위, 곡명, 아티스트, 앨범, 곡ID, 앨범ID, 순위변동, 스냅샷날짜, 크롤링시간
```

**Data Mapping**:

```json
{
  "순위": "={{ $json.rank }}",
  "곡명": "={{ $json.song_title }}",
  "아티스트": "={{ $json.artist }}",
  "앨범": "={{ $json.album }}",
  "곡ID": "={{ $json.song_id }}",
  "앨범ID": "={{ $json.album_id }}",
  "순위변동": "={{ $json.rank_change }}",
  "스냅샷날짜": "={{ $json.snapshot_date }}",
  "크롤링시간": "={{ $json.crawled_at }}"
}
```

### 6.4 테스트

"Execute Node"로 테스트하여 구글 시트에 데이터가 저장되는지 확인

---

## 7. 테스트 및 검증

### 7.1 전체 워크플로우 테스트

1. "Execute Workflow" 버튼 클릭
2. 각 노드의 출력 확인
3. 구글 시트에서 데이터 확인

### 7.2 스케줄 테스트

스케줄이 제대로 작동하는지 테스트:

1. Schedule Trigger 설정을 1분 후로 변경
2. 워크플로우 활성화
3. 1분 후 자동 실행 확인

### 7.3 워크플로우 활성화

테스트 완료 후:

1. 우측 상단 "Inactive" 토글을 "Active"로 변경
2. 매일 8시에 자동 실행됨

---

## 8. 문제 해결

### 문제 1: HTTP Request 실패

**증상**: 403 Forbidden 또는 타임아웃

**해결**:
- User-Agent 헤더 확인
- 요청 간격 추가 (Delay 노드 사용)
- Referer 헤더 추가

### 문제 2: 데이터 추출 실패

**증상**: Code 노드에서 빈 배열 반환

**해결**:
- HTML 구조 확인 (디버깅용 HTML 저장)
- CSS 선택자 수정
- 대체 선택자 시도

### 문제 3: 구글 시트 저장 실패

**증상**: 인증 오류 또는 권한 오류

**해결**:
- 서비스 계정 인증 확인
- 구글 시트 공유 설정 확인
- API 활성화 확인

### 문제 4: 스케줄이 실행되지 않음

**증상**: 매일 8시에 실행되지 않음

**해결**:
- 워크플로우가 Active 상태인지 확인
- Cron 표현식 확인
- n8n 서버 시간대 확인

---

## ✅ Part 1 완료 체크리스트

- [ ] n8n 설치 및 접속
- [ ] Schedule Trigger 설정 (매일 8시)
- [ ] HTTP Request 노드로 멜론 차트 크롤링
- [ ] Code 노드로 데이터 파싱
- [ ] 구글 시트에 데이터 저장
- [ ] 전체 워크플로우 테스트
- [ ] 워크플로우 활성화

---

**다음 단계**: [Part 2: 구글 시트 연동](./PART2_GOOGLE_SHEETS.md) →

