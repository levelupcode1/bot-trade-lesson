"""
구글 시트에서 데이터를 읽어오는 스크립트
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os


class GoogleSheetsReader:
    """구글 시트 리더 클래스"""
    
    def __init__(self, spreadsheet_id: str, credentials_path: str = None):
        """
        Args:
            spreadsheet_id: 구글 시트 ID
            credentials_path: 서비스 계정 JSON 파일 경로
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.client = self._authenticate()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
    
    def _authenticate(self):
        """구글 시트 인증"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"인증 파일을 찾을 수 없습니다: {self.credentials_path}")
        
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
            df['크롤링시간'] = pd.to_datetime(df['크롤링시간'], errors='coerce')
            df = df.sort_values('크롤링시간', ascending=False, na_position='last')
        
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

