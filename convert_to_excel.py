# -*- coding: utf-8 -*-
"""
CSV 파일을 엑셀 파일로 변환하거나 UTF-8 BOM으로 저장
"""
import pandas as pd
import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def main():
    # 파일명 직접 지정
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    try:
        # CSV 파일 읽기 (세미콜론 구분자)
        print(f'[진행] CSV 파일 읽는 중: {csv_file}')
        # 오류가 있는 행은 건너뛰기
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8', on_bad_lines='skip', engine='python')
        print(f'[정보] 총 {len(df)}개 행 읽기 완료')
        
        # 방법 1: UTF-8 BOM으로 저장
        output_csv = csv_file.replace('.csv', '_utf8bom.csv')
        df.to_csv(output_csv, sep=';', index=False, encoding='utf-8-sig')
        print(f'[성공] UTF-8 BOM 파일 생성: {output_csv}')
        print('       -> 엑셀에서 이 파일을 열면 한글이 깨지지 않습니다.')
        
        # 방법 2: 엑셀 파일로 저장
        try:
            output_excel = csv_file.replace('.csv', '.xlsx')
            df.to_excel(output_excel, index=False, engine='openpyxl')
            print(f'[성공] 엑셀 파일 생성: {output_excel}')
        except ImportError:
            print('[경고] openpyxl이 설치되지 않았습니다.')
            print('       엑셀 파일 생성을 위해 다음 명령을 실행하세요:')
            print('       pip install openpyxl')
        
    except Exception as e:
        print(f'[오류] 변환 중 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

