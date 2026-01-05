"""
멜론 최신곡 데이터를 구글 시트에 저장하는 스크립트
"""

import json
import os
from typing import List, Dict
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ 필요한 라이브러리가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install gspread google-auth")
    exit(1)


class GoogleSheetsUploader:
    """구글 시트 업로더 클래스"""
    
    def __init__(self, spreadsheet_id: str, credentials_path: str = None):
        """
        Args:
            spreadsheet_id: 구글 시트 ID
            credentials_path: 서비스 계정 JSON 파일 경로 (없으면 환경변수에서 읽음)
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH')
        
        if not self.credentials_path:
            raise ValueError(
                "서비스 계정 인증 파일이 필요합니다.\n"
                "1. Google Cloud Console에서 서비스 계정 생성\n"
                "2. 서비스 계정 키 JSON 파일 다운로드\n"
                "3. 환경변수 GOOGLE_CREDENTIALS_PATH 설정 또는 credentials_path 파라미터로 전달"
            )
        
        # 인증
        self.client = self._authenticate()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
    
    def _authenticate(self):
        """구글 시트 인증"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scope
            )
            
            return gspread.authorize(creds)
        except Exception as e:
            raise Exception(f"인증 실패: {e}")
    
    def load_json_data(self, json_file: str) -> List[Dict]:
        """JSON 파일에서 데이터 로드"""
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def upload_data(self, data: List[Dict], worksheet_name: str = None, clear_first: bool = True):
        """
        데이터를 구글 시트에 업로드
        
        Args:
            data: 업로드할 데이터 리스트
            worksheet_name: 워크시트 이름 (없으면 첫 번째 시트 사용)
            clear_first: 기존 데이터 삭제 여부
        """
        try:
            # 워크시트 선택
            if worksheet_name:
                try:
                    worksheet = self.spreadsheet.worksheet(worksheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            else:
                worksheet = self.spreadsheet.sheet1
            
            if not data:
                print("❌ 업로드할 데이터가 없습니다.")
                return
            
            # 헤더 정의
            headers = [
                '순위', '곡명', '아티스트', '앨범', 
                '곡 ID', '앨범 ID', '앨범 이미지', 
                '스냅샷 날짜', '크롤링 시간'
            ]
            
            # 데이터 변환
            rows = [headers]
            for item in data:
                row = [
                    item.get('rank', ''),
                    item.get('song_title', ''),
                    item.get('artist', ''),
                    item.get('album', ''),
                    item.get('song_id', ''),
                    item.get('album_id', ''),
                    item.get('album_image', ''),
                    item.get('snapshot_date', ''),
                    item.get('crawled_at', '')
                ]
                rows.append(row)
            
            # 기존 데이터 삭제
            if clear_first:
                worksheet.clear()
            
            # 데이터 업로드
            worksheet.update('A1', rows, value_input_option='USER_ENTERED')
            
            # 열 너비 자동 조정 (선택사항)
            try:
                worksheet.columns_auto_resize(0, len(headers))
            except:
                pass  # 자동 조정 실패해도 계속 진행
            
            print(f"✅ 구글 시트에 {len(data)}개 데이터 업로드 완료!")
            print(f"   시트 URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            
        except Exception as e:
            print(f"❌ 업로드 오류: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def append_data(self, data: List[Dict], worksheet_name: str = None):
        """
        기존 데이터에 추가 (헤더는 추가하지 않음)
        
        Args:
            data: 추가할 데이터 리스트
            worksheet_name: 워크시트 이름
        """
        try:
            # 워크시트 선택
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.sheet1
            
            if not data:
                print("❌ 추가할 데이터가 없습니다.")
                return
            
            # 데이터 변환
            rows = []
            for item in data:
                row = [
                    item.get('rank', ''),
                    item.get('song_title', ''),
                    item.get('artist', ''),
                    item.get('album', ''),
                    item.get('song_id', ''),
                    item.get('album_id', ''),
                    item.get('album_image', ''),
                    item.get('snapshot_date', ''),
                    item.get('crawled_at', '')
                ]
                rows.append(row)
            
            # 기존 데이터 다음 행에 추가
            existing_data = worksheet.get_all_values()
            next_row = len(existing_data) + 1
            
            worksheet.update(f'A{next_row}', rows, value_input_option='USER_ENTERED')
            
            print(f"✅ 구글 시트에 {len(data)}개 데이터 추가 완료!")
            
        except Exception as e:
            print(f"❌ 추가 오류: {e}")
            raise


def main():
    """메인 함수"""
    import sys
    
    # 구글 시트 ID
    SPREADSHEET_ID = "1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q"
    
    # JSON 파일 경로 (명령줄 인자 또는 기본값)
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 가장 최근 JSON 파일 찾기
        import glob
        json_files = glob.glob('melon_new_songs_*.json')
        if json_files:
            json_file = max(json_files, key=os.path.getctime)
            print(f"📁 가장 최근 파일 사용: {json_file}")
        else:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            print("사용법: python save_to_google_sheets.py <json_file>")
            return
    
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return
    
    # 인증 파일 경로 확인
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
    if not credentials_path:
        # 현재 디렉토리에서 찾기
        possible_paths = [
            'credentials.json',
            'service_account.json',
            'google-credentials.json'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                break
    
    if not credentials_path or not os.path.exists(credentials_path):
        print("❌ 구글 서비스 계정 인증 파일을 찾을 수 없습니다.")
        print("\n설정 방법:")
        print("1. Google Cloud Console (https://console.cloud.google.com/) 접속")
        print("2. 프로젝트 생성 또는 선택")
        print("3. 'API 및 서비스' > '사용자 인증 정보' 이동")
        print("4. '사용자 인증 정보 만들기' > '서비스 계정' 선택")
        print("5. 서비스 계정 생성 후 키 생성 (JSON 형식)")
        print("6. 다운로드한 JSON 파일을 프로젝트 폴더에 저장")
        print("7. 환경변수 설정: set GOOGLE_CREDENTIALS_PATH=경로/파일명.json")
        print("   또는 파일명을 credentials.json으로 저장")
        return
    
    try:
        # 업로더 생성
        uploader = GoogleSheetsUploader(
            spreadsheet_id=SPREADSHEET_ID,
            credentials_path=credentials_path
        )
        
        # 데이터 로드
        print(f"📂 JSON 파일 로드 중: {json_file}")
        data = uploader.load_json_data(json_file)
        print(f"✅ {len(data)}개 데이터 로드 완료")
        
        # 구글 시트에 업로드
        worksheet_name = f"멜론최신곡_{datetime.now().strftime('%Y%m%d')}"
        print(f"\n📤 구글 시트에 업로드 중...")
        uploader.upload_data(data, worksheet_name=worksheet_name, clear_first=True)
        
        print(f"\n✅ 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

