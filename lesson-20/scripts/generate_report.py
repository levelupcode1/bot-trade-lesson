"""
멜론 차트 분석 리포트 생성
"""

import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.google_sheets_reader import GoogleSheetsReader
from scripts.gemini_analyzer import GeminiAnalyzer
from datetime import datetime


def generate_report():
    """분석 리포트 생성"""
    # 데이터 읽기
    reader = GoogleSheetsReader(
        spreadsheet_id="1aGXXGPK_PbbTnVKtjQyXwY35KUpyOLX8zhZEinFsm6Q",
        credentials_path="credentials.json"
    )
    
    df = reader.get_latest_data("멜론차트", limit=200)
    
    if len(df) == 0:
        print("⚠️ 분석할 데이터가 없습니다.")
        return None
    
    # 분석기 생성
    analyzer = GeminiAnalyzer()
    
    # 인사이트 생성
    print("📊 데이터 분석 중...")
    insights = analyzer.generate_insights(df)
    
    # 리포트 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/melon_analysis_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 멜론 차트 분석 리포트\n\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(insights)
    
    print(f"✅ 리포트 저장 완료: {report_file}")
    
    return report_file


if __name__ == "__main__":
    generate_report()

