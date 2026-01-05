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
        if '아티스트' in df.columns and '순위' in df.columns:
            artist_stats = df.groupby('아티스트').agg({
                '순위': ['count', 'mean', 'min'],
            }).round(2)
            stats_text = artist_stats.to_string()
        else:
            stats_text = "통계 데이터 없음"
        
        summary = f"""
아티스트별 통계:
{stats_text}

상위 10개 곡:
{df.head(10).to_string() if len(df) > 0 else '데이터 없음'}
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
        if len(df) == 0:
            return "데이터가 없습니다."
        
        date_info = ""
        if '스냅샷날짜' in df.columns:
            date_info = f"- 분석 기간: {df['스냅샷날짜'].min()} ~ {df['스냅샷날짜'].max()}"
        
        top_songs = ""
        if len(df) > 0:
            columns = ['순위', '곡명', '아티스트', '앨범', '순위변동']
            available_columns = [col for col in columns if col in df.columns]
            top_songs = df.head(20)[available_columns].to_string()
        
        artist_info = ""
        if '아티스트' in df.columns:
            artist_info = df['아티스트'].value_counts().head(10).to_string()
        
        rank_change_info = ""
        if '순위변동' in df.columns:
            rank_change_info = df['순위변동'].describe().to_string()
        
        summary = f"""
데이터 개요:
- 총 레코드 수: {len(df)}
{date_info}

상위 20개 곡:
{top_songs}

아티스트별 곡 수:
{artist_info}

순위 변동 통계:
{rank_change_info}
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
    from google_sheets_reader import GoogleSheetsReader
    
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

