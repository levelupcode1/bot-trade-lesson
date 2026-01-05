"""
간단한 구글 시트 업로드 스크립트
JSON 파일을 구글 시트에 업로드합니다.
"""

import json
import sys
import os
from datetime import datetime

# 구글 시트 ID
SPREADSHEET_ID = "1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q"

def main():
    """메인 함수"""
    try:
        from save_to_google_sheets import GoogleSheetsUploader
    except ImportError:
        print("❌ save_to_google_sheets 모듈을 찾을 수 없습니다.")
        return
    
    # JSON 파일 경로
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
            print("사용법: python upload_to_sheets.py <json_file>")
            return
    
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return
    
    # 인증 파일 찾기
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
    if not credentials_path:
        possible_paths = ['credentials.json', 'service_account.json', 'google-credentials.json']
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                break
    
    if not credentials_path:
        print("❌ 구글 인증 파일을 찾을 수 없습니다.")
        print("자세한 설정 방법은 GOOGLE_SHEETS_SETUP.md를 참고하세요.")
        return
    
    try:
        # 업로더 생성 및 업로드
        uploader = GoogleSheetsUploader(SPREADSHEET_ID, credentials_path)
        data = uploader.load_json_data(json_file)
        
        worksheet_name = f"멜론최신곡_{datetime.now().strftime('%Y%m%d')}"
        uploader.upload_data(data, worksheet_name=worksheet_name, clear_first=True)
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

