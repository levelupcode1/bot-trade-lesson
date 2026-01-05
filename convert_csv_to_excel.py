#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 파일을 엑셀 파일로 변환하거나 UTF-8 BOM으로 저장하는 스크립트
"""

import pandas as pd
import sys
from pathlib import Path

def convert_csv_to_excel(csv_file: str, excel_file: str = None):
    """
    CSV 파일을 엑셀 파일로 변환
    
    Args:
        csv_file: 입력 CSV 파일 경로
        excel_file: 출력 엑셀 파일 경로 (없으면 자동 생성)
    """
    try:
        # CSV 파일 읽기 (세미콜론 구분자)
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
        
        # 엑셀 파일명이 없으면 자동 생성
        if excel_file is None:
            csv_path = Path(csv_file)
            excel_file = csv_path.with_suffix('.xlsx')
        
        # 엑셀 파일로 저장
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        print(f"[성공] 엑셀 파일로 변환 완료: {excel_file}")
        print(f"       총 {len(df)}개 행 저장됨")
        
        return str(excel_file)
        
    except Exception as e:
        print(f"[오류] 오류 발생: {e}")
        return None

def convert_csv_to_utf8_bom(csv_file: str, output_file: str = None):
    """
    CSV 파일을 UTF-8 BOM으로 변환 (엑셀에서 자동 인식)
    
    Args:
        csv_file: 입력 CSV 파일 경로
        output_file: 출력 CSV 파일 경로 (없으면 원본 덮어쓰기)
    """
    try:
        # CSV 파일 읽기 (세미콜론 구분자)
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
        
        # 출력 파일명이 없으면 원본 파일명 사용
        if output_file is None:
            output_file = csv_file
        
        # UTF-8 BOM으로 저장 (엑셀에서 자동 인식)
        df.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')
        
        print(f"[성공] UTF-8 BOM으로 변환 완료: {output_file}")
        print(f"       엑셀에서 열 때 한글이 깨지지 않습니다.")
        
        return output_file
        
    except Exception as e:
        print(f"[오류] 오류 발생: {e}")
        return None

def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python convert_csv_to_excel.py <CSV파일> [옵션]")
        print("\n옵션:")
        print("  --excel        : 엑셀 파일(.xlsx)로 변환")
        print("  --utf8-bom     : UTF-8 BOM으로 변환 (기본값)")
        print("\n예시:")
        print("  python convert_csv_to_excel.py 각_차시별_학습정리.csv --excel")
        print("  python convert_csv_to_excel.py 각_차시별_학습정리.csv --utf8-bom")
        return
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    # 옵션 확인
    if len(sys.argv) > 2 and sys.argv[2] == '--excel':
        # 엑셀 파일로 변환
        convert_csv_to_excel(csv_file)
    else:
        # UTF-8 BOM으로 변환 (기본값)
        convert_csv_to_utf8_bom(csv_file)

if __name__ == '__main__':
    main()

