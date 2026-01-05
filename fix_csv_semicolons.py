# -*- coding: utf-8 -*-
"""
CSV 파일에서 내용 안의 세미콜론을 쉼표로 변경하는 스크립트
"""
import re
import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fix_semicolons_in_content(csv_file):
    """
    CSV 파일에서 내용 안의 세미콜론을 쉼표로 변경
    패턴: "하고; " -> "하고, ", "하며; " -> "하며, "
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    changes = []
    
    for i, line in enumerate(lines, 1):
        original = line
        
        # 패턴 1: "하고; " -> "하고, "
        if '하고; ' in line:
            line = line.replace('하고; ', '하고, ')
            changes.append(f"줄 {i}: '하고; ' -> '하고, '")
        
        # 패턴 2: "하며; " -> "하며, "
        if '하며; ' in line:
            line = line.replace('하며; ', '하며, ')
            changes.append(f"줄 {i}: '하며; ' -> '하며, '")
        
        fixed_lines.append(line)
    
    # 수정된 내용 저장
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    return changes

def main():
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    print(f'[진행] CSV 파일 수정 중: {csv_file}')
    changes = fix_semicolons_in_content(csv_file)
    
    if changes:
        print(f'[성공] 총 {len(changes)}개 수정 완료:')
        for change in changes:
            print(f'  - {change}')
    else:
        print('[정보] 수정할 내용이 없습니다.')
    
    # 엑셀 파일로 변환
    print('\n[진행] 엑셀 파일 생성 중...')
    try:
        import pandas as pd
        
        # CSV 파일 읽기
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8', on_bad_lines='skip', engine='python')
        
        # UTF-8 BOM으로 저장
        output_csv = csv_file.replace('.csv', '_utf8bom.csv')
        df.to_csv(output_csv, sep=';', index=False, encoding='utf-8-sig')
        print(f'[성공] UTF-8 BOM 파일 생성: {output_csv}')
        
        # 엑셀 파일로 저장
        try:
            output_excel = csv_file.replace('.csv', '.xlsx')
            df.to_excel(output_excel, index=False, engine='openpyxl')
            print(f'[성공] 엑셀 파일 생성: {output_excel}')
        except ImportError:
            print('[경고] openpyxl이 설치되지 않았습니다.')
            print('       pip install openpyxl')
        
    except Exception as e:
        print(f'[오류] 변환 중 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

