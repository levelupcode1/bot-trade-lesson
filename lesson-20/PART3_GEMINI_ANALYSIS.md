# Part 3: Gemini AI 분석

구글 시트에 저장된 멜론 차트 데이터를 Gemini AI로 분석하여 의미있는 인사이트를 도출합니다.

## 📋 목차

- [Gemini API 설정](#gemini-api-설정)
- [구글 시트 데이터 읽기](#구글-시트-데이터-읽기)
- [Gemini AI 분석 구현](#gemini-ai-분석-구현)
- [인사이트 리포트 생성](#인사이트-리포트-생성)
- [자동화 워크플로우 구축](#자동화-워크플로우-구축)
- [고급 분석 기법](#고급-분석-기법)
- [문제 해결](#문제-해결)

## 🎯 학습 목표

이 파트를 완료하면:
- ✅ Google Gemini API를 설정하고 사용할 수 있습니다
- ✅ 구글 시트 데이터를 AI로 분석할 수 있습니다
- ✅ 트렌드 분석 및 인사이트를 도출할 수 있습니다
- ✅ 자동화된 분석 리포트를 생성할 수 있습니다

---

## 1. Gemini API 설정

### 1.1 Google AI Studio 접속

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. Google 계정으로 로그인

### 1.2 API 키 생성

1. **"Create API Key"** 클릭
2. 프로젝트 선택 (기존 프로젝트 또는 새 프로젝트)
3. API 키가 생성됨
4. **⚠️ 중요**: API 키를 안전하게 보관하세요!

### 1.3 API 키 저장

환경변수로 저장 (권장):

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your-api-key-here"

# Windows (CMD)
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY=your-api-key-here
```

또는 `.env` 파일 사용:

```
GEMINI_API_KEY=your-api-key-here
```

### 1.4 필요한 라이브러리 설치

```bash
pip install google-generativeai pandas python-dotenv
```

---

## 2. 구글 시트 데이터 읽기

### 2.1 데이터 읽기 스크립트

Part 2에서 만든 `google_sheets_reader.py`를 사용합니다.

### 2.2 데이터 준비

```python
from scripts.google_sheets_reader import GoogleSheetsReader
import pandas as pd

# 구글 시트에서 데이터 읽기
reader = GoogleSheetsReader(
    spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
    credentials_path="credentials.json"
)

# 최근 데이터 가져오기
df = reader.get_latest_data("멜론차트", limit=200)
```

---

## 3. Gemini AI 분석 구현

### 3.1 Gemini Analyzer 클래스

`scripts/gemini_analyzer.py`:

```python
"""
Gemini AI를 사용한 멜론 차트 분석
"""

import os
import google.generativeai as genai
import pandas as pd
from typing import Dict, List
from datetime import datetime
import json


class GeminiAnalyzer:
    """Gemini AI 분석기 클래스"""
    
    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 읽음)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("Gemini API 키가 필요합니다. 환경변수 GEMINI_API_KEY를 설정하세요.")
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_trends(self, df: pd.DataFrame) -> Dict:
        """
        트렌드 분석
        
        Args:
            df: 멜론 차트 데이터프레임
        
        Returns:
            분석 결과 딕셔너리
        """
        # 데이터 요약
        summary = self._prepare_summary(df)
        
        # 프롬프트 생성
        prompt = f"""
다음은 멜론 차트 데이터입니다. 의미있는 트렌드와 인사이트를 분석해주세요.

{summary}

다음 형식으로 분석 결과를 제공해주세요:
1. 주요 트렌드 (3-5개)
2. 인기 아티스트 분석
3. 장르 트렌드
4. 순위 변동 패턴
5. 예측 및 추천

JSON 형식으로 응답해주세요:
{{
  "trends": ["트렌드1", "트렌드2", ...],
  "popular_artists": ["아티스트1", "아티스트2", ...],
  "genre_trends": "장르 분석",
  "rank_patterns": "순위 변동 패턴",
  "predictions": "예측 및 추천"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            return result
        except Exception as e:
            print(f"❌ 분석 오류: {e}")
            return {"error": str(e)}
    
    def analyze_artists(self, df: pd.DataFrame) -> Dict:
        """
        아티스트 분석
        
        Args:
            df: 멜론 차트 데이터프레임
        
        Returns:
            아티스트 분석 결과
        """
        # 아티스트별 통계
        artist_stats = df.groupby('아티스트').agg({
            '순위': ['count', 'mean', 'min'],
            '순위변동': 'mean'
        }).round(2)
        
        summary = f"""
아티스트별 통계:
{artist_stats.to_string()}

상위 10개 곡:
{df.head(10).to_string()}
"""
        
        prompt = f"""
다음 멜론 차트 데이터를 분석하여 아티스트별 인기와 트렌드를 분석해주세요.

{summary}

다음 항목을 포함하여 분석해주세요:
1. 가장 인기 있는 아티스트 TOP 5
2. 상승세인 아티스트
3. 아티스트별 특징
4. 협업 트렌드

JSON 형식으로 응답해주세요.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            return result
        except Exception as e:
            print(f"❌ 분석 오류: {e}")
            return {"error": str(e)}
    
    def generate_insights(self, df: pd.DataFrame) -> str:
        """
        종합 인사이트 생성
        
        Args:
            df: 멜론 차트 데이터프레임
        
        Returns:
            인사이트 리포트 텍스트
        """
        summary = self._prepare_summary(df)
        
        prompt = f"""
멜론 차트 데이터를 분석하여 종합적인 인사이트 리포트를 작성해주세요.

{summary}

다음 구조로 리포트를 작성해주세요:

# 멜론 차트 분석 리포트

## 1. 개요
- 분석 기간
- 총 곡 수
- 주요 특징

## 2. 주요 트렌드
- 음악 트렌드 분석
- 인기 장르
- 아티스트 트렌드

## 3. 순위 변동 분석
- 상승 곡
- 하락 곡
- 신규 진입 곡

## 4. 인사이트
- 시장 동향
- 예측
- 추천 사항

마크다운 형식으로 작성해주세요.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ 리포트 생성 오류: {e}"
    
    def _prepare_summary(self, df: pd.DataFrame) -> str:
        """데이터 요약 준비"""
        summary = f"""
데이터 개요:
- 총 레코드 수: {len(df)}
- 분석 기간: {df['스냅샷날짜'].min() if '스냅샷날짜' in df.columns else 'N/A'} ~ {df['스냅샷날짜'].max() if '스냅샷날짜' in df.columns else 'N/A'}

상위 20개 곡:
{df.head(20)[['순위', '곡명', '아티스트', '앨범', '순위변동']].to_string()}

아티스트별 곡 수:
{df['아티스트'].value_counts().head(10).to_string() if '아티스트' in df.columns else 'N/A'}

순위 변동 통계:
{df['순위변동'].describe().to_string() if '순위변동' in df.columns else 'N/A'}
"""
        return summary
    
    def _parse_response(self, text: str) -> Dict:
        """응답 파싱"""
        try:
            # JSON 코드 블록 제거
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except:
            # JSON 파싱 실패 시 텍스트 그대로 반환
            return {"raw_response": text}


def main():
    """메인 함수"""
    from scripts.google_sheets_reader import GoogleSheetsReader
    
    # 구글 시트에서 데이터 읽기
    reader = GoogleSheetsReader(
        spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
        credentials_path="credentials.json"
    )
    
    df = reader.get_latest_data("멜론차트", limit=200)
    
    # Gemini 분석기 생성
    analyzer = GeminiAnalyzer()
    
    # 트렌드 분석
    print("📊 트렌드 분석 중...")
    trends = analyzer.analyze_trends(df)
    print(json.dumps(trends, ensure_ascii=False, indent=2))
    
    # 아티스트 분석
    print("\n🎤 아티스트 분석 중...")
    artists = analyzer.analyze_artists(df)
    print(json.dumps(artists, ensure_ascii=False, indent=2))
    
    # 인사이트 리포트
    print("\n📝 인사이트 리포트 생성 중...")
    insights = analyzer.generate_insights(df)
    print(insights)


if __name__ == "__main__":
    main()
```

---

## 4. 인사이트 리포트 생성

### 4.1 리포트 생성 스크립트

`scripts/generate_report.py`:

```python
"""
멜론 차트 분석 리포트 생성
"""

from scripts.google_sheets_reader import GoogleSheetsReader
from scripts.gemini_analyzer import GeminiAnalyzer
from datetime import datetime
import os


def generate_report():
    """분석 리포트 생성"""
    # 데이터 읽기
    reader = GoogleSheetsReader(
        spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
        credentials_path="credentials.json"
    )
    
    df = reader.get_latest_data("멜론차트", limit=200)
    
    # 분석기 생성
    analyzer = GeminiAnalyzer()
    
    # 인사이트 생성
    print("📊 데이터 분석 중...")
    insights = analyzer.generate_insights(df)
    
    # 리포트 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"reports/melon_analysis_{timestamp}.md"
    
    os.makedirs("reports", exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 멜론 차트 분석 리포트\n\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(insights)
    
    print(f"✅ 리포트 저장 완료: {report_file}")
    
    return report_file


if __name__ == "__main__":
    generate_report()
```

---

## 5. 자동화 워크플로우 구축

### 5.1 n8n 워크플로우 확장

기존 워크플로우에 분석 단계 추가:

```
Schedule Trigger → HTTP Request → Code → Google Sheets
                                              ↓
                                         Code (Python)
                                              ↓
                                         Gemini AI
                                              ↓
                                         리포트 저장
```

### 5.2 n8n에서 Python 실행

**Execute Command 노드 사용:**

1. Google Sheets 노드 다음에 **"Execute Command"** 노드 추가
2. Command 설정:
   ```bash
   python scripts/generate_report.py
   ```

### 5.3 완전 자동화

매일 8시에:
1. 멜론 차트 크롤링
2. 구글 시트 저장
3. Gemini AI 분석
4. 리포트 생성

---

## 6. 고급 분석 기법

### 6.1 시계열 분석

```python
def analyze_time_series(self, df: pd.DataFrame) -> Dict:
    """시계열 분석"""
    # 날짜별 데이터 그룹화
    daily_data = df.groupby('스냅샷날짜').agg({
        '순위': 'mean',
        '곡명': 'count'
    })
    
    prompt = f"""
시계열 데이터를 분석하여 트렌드를 파악해주세요.

{daily_data.to_string()}

주요 패턴과 예측을 제공해주세요.
"""
    
    response = self.model.generate_content(prompt)
    return response.text
```

### 6.2 비교 분석

```python
def compare_periods(self, df: pd.DataFrame, period1: str, period2: str) -> Dict:
    """기간별 비교 분석"""
    period1_data = df[df['스냅샷날짜'] == period1]
    period2_data = df[df['스냅샷날짜'] == period2]
    
    prompt = f"""
두 기간의 멜론 차트를 비교 분석해주세요.

기간 1 ({period1}):
{period1_data.head(20).to_string()}

기간 2 ({period2}):
{period2_data.head(20).to_string()}

변화 추이와 인사이트를 제공해주세요.
"""
    
    response = self.model.generate_content(prompt)
    return response.text
```

### 6.3 예측 분석

```python
def predict_trends(self, df: pd.DataFrame) -> Dict:
    """트렌드 예측"""
    # 최근 데이터 분석
    recent_data = df.tail(100)
    
    prompt = f"""
최근 멜론 차트 데이터를 분석하여 향후 트렌드를 예측해주세요.

{recent_data.to_string()}

다음 주 예상 트렌드와 인기 아티스트를 예측해주세요.
"""
    
    response = self.model.generate_content(prompt)
    return response.text
```

---

## 7. 문제 해결

### 문제 1: API 키 오류

**증상**: `API key not valid`

**해결**:
- API 키 확인
- 환경변수 설정 확인
- API 키 권한 확인

### 문제 2: 할당량 초과

**증상**: `Quota exceeded`

**해결**:
- API 사용량 확인
- 요청 간격 조정
- 유료 플랜 고려

### 문제 3: 응답 파싱 오류

**증상**: JSON 파싱 실패

**해결**:
- 응답 형식 확인
- 에러 처리 개선
- 대체 파싱 방법 사용

---

## ✅ Part 3 완료 체크리스트

- [ ] Gemini API 키 발급
- [ ] Gemini Analyzer 클래스 구현
- [ ] 트렌드 분석 테스트
- [ ] 인사이트 리포트 생성
- [ ] 자동화 워크플로우 구축
- [ ] 리포트 자동 저장

---

## 🎉 완료!

이제 완전 자동화된 멜론 차트 분석 시스템이 구축되었습니다!

**시스템 흐름:**
1. 매일 8시 n8n이 멜론 차트 크롤링
2. 구글 시트에 자동 저장
3. Gemini AI가 데이터 분석
4. 인사이트 리포트 자동 생성

**다음 단계:**
- 리포트를 이메일로 전송
- 텔레그램 봇으로 알림
- 웹 대시보드 구축

---

**이전 단계**: [Part 2: 구글 시트 연동](./PART2_GOOGLE_SHEETS.md) ←

