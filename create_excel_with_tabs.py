# -*- coding: utf-8 -*-
"""
CSV 파일을 읽어서 각 차시별로 엑셀 시트(탭)를 만드는 스크립트
"""
import pandas as pd
import sys
import os
from collections import defaultdict

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def create_excel_with_tabs(csv_file, excel_file=None):
    """
    CSV 파일을 읽어서 각 차시별로 엑셀 시트를 생성
    
    Args:
        csv_file: 입력 CSV 파일 경로
        excel_file: 출력 엑셀 파일 경로 (없으면 자동 생성)
    """
    try:
        # CSV 파일 읽기
        print(f'[진행] CSV 파일 읽는 중: {csv_file}')
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8', on_bad_lines='skip', engine='python')
        print(f'[정보] 총 {len(df)}개 행 읽기 완료')
        
        # 차시별로 그룹화
        grouped = defaultdict(list)
        for idx, row in df.iterrows():
            차시 = row['차시']
            grouped[차시].append(row.to_dict())
        
        # 엑셀 파일명이 없으면 자동 생성
        if excel_file is None:
            excel_file = csv_file.replace('.csv', '_차시별.xlsx')
        
        # 엑셀 파일 생성 (각 차시를 별도 시트로)
        print(f'[진행] 엑셀 파일 생성 중: {excel_file}')
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 차시별로 정렬하여 시트 생성
            sorted_차시 = sorted(grouped.keys(), key=lambda x: int(x.replace('차시', '')) if x.replace('차시', '').isdigit() else 999)
            
            for 차시 in sorted_차시:
                차시_df = pd.DataFrame(grouped[차시])
                # 시트 이름은 최대 31자 (엑셀 제한)
                sheet_name = 차시[:31] if len(차시) > 31 else 차시
                차시_df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f'  - {차시} 시트 생성: {len(차시_df)}개 행')
        
        print(f'\n[성공] 엑셀 파일 생성 완료: {excel_file}')
        print(f'       총 {len(grouped)}개 차시 시트 생성됨')
        
        return excel_file
        
    except ImportError:
        print('[오류] openpyxl이 설치되지 않았습니다.')
        print('       다음 명령을 실행하세요: pip install openpyxl')
        return None
    except Exception as e:
        print(f'[오류] 변환 중 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    create_excel_with_tabs(csv_file)

if __name__ == '__main__':
    main()

