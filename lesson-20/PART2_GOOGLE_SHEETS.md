# Part 2: 구글 시트 연동

n8n에서 구글 시트에 데이터를 저장하고, Python으로 구글 시트 데이터를 읽어오는 방법을 학습합니다.

## 📋 목차

- [구글 클라우드 프로젝트 설정](#구글-클라우드-프로젝트-설정)
- [서비스 계정 생성](#서비스-계정-생성)
- [API 활성화](#api-활성화)
- [n8n에서 구글 시트 연동](#n8n에서-구글-시트-연동)
- [Python으로 구글 시트 읽기](#python으로-구글-시트-읽기)
- [데이터 검증 및 모니터링](#데이터-검증-및-모니터링)
- [문제 해결](#문제-해결)

## 🎯 학습 목표

이 파트를 완료하면:
- ✅ Google Cloud Platform 프로젝트를 생성하고 설정할 수 있습니다
- ✅ 서비스 계정을 생성하고 인증할 수 있습니다
- ✅ n8n에서 구글 시트에 데이터를 저장할 수 있습니다
- ✅ Python으로 구글 시트 데이터를 읽을 수 있습니다

---

## 1. 구글 클라우드 프로젝트 설정

### 1.1 Google Cloud Console 접속

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Google 계정으로 로그인

### 1.2 프로젝트 생성

1. 상단 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 정보 입력:
   - **프로젝트 이름**: `melon-chart-analyzer`
   - **조직**: (선택사항)
   - **위치**: (선택사항)
4. "만들기" 클릭

### 1.3 프로젝트 선택

생성된 프로젝트를 선택하여 활성화합니다.

---

## 2. 서비스 계정 생성

### 2.1 서비스 계정 생성

1. 좌측 메뉴에서 **"IAM 및 관리자"** > **"서비스 계정"** 클릭
2. 상단 **"서비스 계정 만들기"** 클릭
3. 서비스 계정 정보 입력:
   - **서비스 계정 이름**: `n8n-melon-crawler`
   - **서비스 계정 ID**: 자동 생성 (예: `n8n-melon-crawler@melon-chart-analyzer.iam.gserviceaccount.com`)
   - **설명**: `n8n 워크플로우용 서비스 계정`
4. **"만들기"** 클릭

### 2.2 역할 부여 (선택사항)

서비스 계정에 역할 부여:
- **역할**: `Editor` (또는 필요한 최소 권한만 부여)

### 2.3 키 생성

1. 생성된 서비스 계정 클릭
2. **"키"** 탭 이동
3. **"키 추가"** > **"새 키 만들기"** 클릭
4. **키 유형**: `JSON` 선택
5. **"만들기"** 클릭
6. JSON 파일이 자동으로 다운로드됨

**⚠️ 중요**: 이 JSON 파일은 안전하게 보관하세요. 공유하지 마세요!

---

## 3. API 활성화

### 3.1 Google Sheets API 활성화

1. 좌측 메뉴에서 **"API 및 서비스"** > **"라이브러리"** 클릭
2. 검색창에 **"Google Sheets API"** 입력
3. **"Google Sheets API"** 선택
4. **"사용 설정"** 클릭

### 3.2 Google Drive API 활성화

1. 같은 페이지에서 **"Google Drive API"** 검색
2. **"Google Drive API"** 선택
3. **"사용 설정"** 클릭

**왜 필요한가?**: 구글 시트는 Google Drive에 저장되므로 Drive API도 필요합니다.

---

## 4. 구글 시트 공유 설정

### 4.1 구글 시트 열기

구글 시트 URL:
```
https://docs.google.com/spreadsheets/d/1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q
```

### 4.2 서비스 계정 이메일 확인

다운로드한 JSON 파일에서 `client_email` 값을 확인:

```json
{
  "client_email": "n8n-melon-crawler@melon-chart-analyzer.iam.gserviceaccount.com",
  ...
}
```

### 4.3 시트 공유

1. 구글 시트에서 우측 상단 **"공유"** 버튼 클릭
2. 서비스 계정 이메일 주소 입력
3. 권한: **"편집자"** 선택
4. **"완료"** 클릭

**⚠️ 중요**: 서비스 계정 이메일을 공유하지 않으면 데이터 저장이 실패합니다!

---

## 5. n8n에서 구글 시트 연동

### 5.1 Credentials 추가

1. n8n에서 좌측 메뉴 **"Credentials"** 클릭
2. **"Add Credential"** 클릭
3. **"Google Service Account"** 선택
4. 다운로드한 JSON 파일 내용을 복사하여 붙여넣기
5. **"Save"** 클릭

### 5.2 Google Sheets 노드 설정

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

### 5.3 테스트

"Execute Node" 버튼으로 테스트하여 데이터가 저장되는지 확인합니다.

---

## 6. Python으로 구글 시트 읽기

### 6.1 필요한 라이브러리 설치

```bash
pip install gspread google-auth pandas
```

### 6.2 인증 파일 설정

다운로드한 JSON 파일을 프로젝트 폴더에 복사:

```
lesson-20/
  ├── credentials.json  ← 여기에 저장
  └── ...
```

### 6.3 구글 시트 읽기 스크립트

`scripts/google_sheets_reader.py`:

```python
"""
구글 시트에서 데이터를 읽어오는 스크립트
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from typing import List, Dict


class GoogleSheetsReader:
    """구글 시트 리더 클래스"""
    
    def __init__(self, spreadsheet_id: str, credentials_path: str = "credentials.json"):
        """
        Args:
            spreadsheet_id: 구글 시트 ID
            credentials_path: 서비스 계정 JSON 파일 경로
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path
        self.client = self._authenticate()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
    
    def _authenticate(self):
        """구글 시트 인증"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scope
        )
        
        return gspread.authorize(creds)
    
    def read_sheet(self, worksheet_name: str = None) -> pd.DataFrame:
        """
        시트에서 데이터 읽기
        
        Args:
            worksheet_name: 워크시트 이름 (없으면 첫 번째 시트)
        
        Returns:
            pandas DataFrame
        """
        if worksheet_name:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        else:
            worksheet = self.spreadsheet.sheet1
        
        # 모든 데이터 가져오기
        data = worksheet.get_all_records()
        
        # DataFrame으로 변환
        df = pd.DataFrame(data)
        
        return df
    
    def get_latest_data(self, worksheet_name: str = None, limit: int = 100) -> pd.DataFrame:
        """
        최신 데이터만 가져오기
        
        Args:
            worksheet_name: 워크시트 이름
            limit: 가져올 행 수
        
        Returns:
            pandas DataFrame
        """
        df = self.read_sheet(worksheet_name)
        
        # 날짜 기준 정렬 (최신순)
        if '크롤링시간' in df.columns:
            df['크롤링시간'] = pd.to_datetime(df['크롤링시간'])
            df = df.sort_values('크롤링시간', ascending=False)
        
        return df.head(limit)
    
    def get_today_data(self, worksheet_name: str = None) -> pd.DataFrame:
        """
        오늘 날짜의 데이터만 가져오기
        
        Args:
            worksheet_name: 워크시트 이름
        
        Returns:
            pandas DataFrame
        """
        df = self.read_sheet(worksheet_name)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if '스냅샷날짜' in df.columns:
            df = df[df['스냅샷날짜'] == today]
        
        return df
    
    def get_statistics(self, worksheet_name: str = None) -> Dict:
        """
        데이터 통계 정보
        
        Args:
            worksheet_name: 워크시트 이름
        
        Returns:
            통계 정보 딕셔너리
        """
        df = self.read_sheet(worksheet_name)
        
        stats = {
            'total_records': len(df),
            'unique_songs': df['곡명'].nunique() if '곡명' in df.columns else 0,
            'unique_artists': df['아티스트'].nunique() if '아티스트' in df.columns else 0,
            'date_range': {
                'earliest': df['스냅샷날짜'].min() if '스냅샷날짜' in df.columns else None,
                'latest': df['스냅샷날짜'].max() if '스냅샷날짜' in df.columns else None
            }
        }
        
        return stats


def main():
    """메인 함수"""
    SPREADSHEET_ID = "1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q"
    
    try:
        reader = GoogleSheetsReader(SPREADSHEET_ID, "credentials.json")
        
        # 전체 데이터 읽기
        print("📊 전체 데이터 읽기...")
        df = reader.read_sheet("멜론차트")
        print(f"✅ 총 {len(df)}개 레코드")
        print(df.head())
        
        # 오늘 데이터 읽기
        print("\n📅 오늘 데이터 읽기...")
        today_df = reader.get_today_data("멜론차트")
        print(f"✅ 오늘 {len(today_df)}개 레코드")
        
        # 통계 정보
        print("\n📈 통계 정보...")
        stats = reader.get_statistics("멜론차트")
        print(stats)
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
```

### 6.4 실행

```bash
python scripts/google_sheets_reader.py
```

---

## 7. 데이터 검증 및 모니터링

### 7.1 데이터 검증 스크립트

`scripts/validate_data.py`:

```python
"""
구글 시트 데이터 검증 스크립트
"""

from google_sheets_reader import GoogleSheetsReader
from datetime import datetime


def validate_data():
    """데이터 검증"""
    SPREADSHEET_ID = "1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q"
    reader = GoogleSheetsReader(SPREADSHEET_ID, "credentials.json")
    
    # 오늘 데이터 확인
    today_df = reader.get_today_data("멜론차트")
    
    if len(today_df) == 0:
        print("⚠️ 오늘 데이터가 없습니다!")
        return False
    
    # 필수 컬럼 확인
    required_columns = ['순위', '곡명', '아티스트', '스냅샷날짜']
    missing_columns = [col for col in required_columns if col not in today_df.columns]
    
    if missing_columns:
        print(f"⚠️ 필수 컬럼이 없습니다: {missing_columns}")
        return False
    
    # 데이터 개수 확인 (일반적으로 50-100개)
    if len(today_df) < 10:
        print(f"⚠️ 데이터가 너무 적습니다: {len(today_df)}개")
        return False
    
    print(f"✅ 데이터 검증 통과: {len(today_df)}개 레코드")
    return True


if __name__ == "__main__":
    validate_data()
```

### 7.2 모니터링 설정

n8n에서 워크플로우 실행 후 검증 스크립트를 실행하도록 설정할 수 있습니다.

---

## 8. 문제 해결

### 문제 1: 인증 실패

**증상**: `403 Forbidden` 또는 `401 Unauthorized`

**해결**:
- JSON 파일 경로 확인
- 서비스 계정 이메일이 시트에 공유되어 있는지 확인
- API 활성화 확인

### 문제 2: 시트를 찾을 수 없음

**증상**: `Spreadsheet not found`

**해결**:
- 시트 ID 확인
- 서비스 계정 권한 확인
- 시트가 삭제되지 않았는지 확인

### 문제 3: 데이터가 저장되지 않음

**증상**: n8n에서 성공했지만 시트에 데이터가 없음

**해결**:
- 시트 이름 확인
- 컬럼 이름 확인
- 데이터 매핑 확인

---

## ✅ Part 2 완료 체크리스트

- [ ] Google Cloud Platform 프로젝트 생성
- [ ] 서비스 계정 생성 및 키 다운로드
- [ ] Google Sheets API 활성화
- [ ] Google Drive API 활성화
- [ ] 구글 시트에 서비스 계정 공유
- [ ] n8n에서 구글 시트 연동
- [ ] Python으로 구글 시트 읽기 테스트
- [ ] 데이터 검증 스크립트 실행

---

**다음 단계**: [Part 3: Gemini AI 분석](./PART3_GEMINI_ANALYSIS.md) →

