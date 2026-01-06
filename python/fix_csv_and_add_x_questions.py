# -*- coding: utf-8 -*-
"""
CSV 파일 수정:
1. 내용 안의 세미콜론을 쉼표로 변경 (구분자는 유지)
2. 퀴즈 문제에 X 문제 추가
"""
import csv
import sys
import os
import re
from collections import defaultdict

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fix_semicolons_in_content(csv_file):
    """
    CSV 파일에서 내용 안의 세미콜론을 쉼표로 변경
    구분자 세미콜론은 유지
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    changes = []
    
    for i, line in enumerate(lines, 1):
        original = line
        
        # CSV 구분자 세미콜론을 임시로 다른 문자로 변경
        # 내용 안의 세미콜론만 처리하기 위해
        parts = line.split(';')
        
        if len(parts) >= 4:  # 최소 4개 필드 (차시, 유형, 번호, 내용)
            # 내용 필드(인덱스 3)와 해설 필드(인덱스 5)에서 세미콜론을 쉼표로 변경
            # 단, 괄호 안의 세미콜론은 유지 (예: (KRW; USD; EUR) -> (KRW, USD, EUR))
            
            # 내용 필드 처리
            if len(parts) > 3:
                content = parts[3]
                # 괄호 안의 세미콜론도 쉼표로 변경
                content = re.sub(r'\(([^)]*);([^)]*)\)', r'(\1, \2)', content)
                content = content.replace('; ', ', ')
                content = content.replace(';', ',')
                parts[3] = content
            
            # 해설 필드 처리 (있는 경우)
            if len(parts) > 5:
                explanation = parts[5]
                explanation = re.sub(r'\(([^)]*);([^)]*)\)', r'(\1, \2)', explanation)
                explanation = explanation.replace('; ', ', ')
                explanation = explanation.replace(';', ',')
                parts[5] = explanation
            
            line = ';'.join(parts)
        
        if line != original:
            changes.append(f"줄 {i}: 세미콜론 -> 쉼표 변경")
        
        fixed_lines.append(line)
    
    # 수정된 내용 저장
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        f.writelines(fixed_lines)
    
    return changes

def add_x_questions(csv_file):
    """
    각 차시의 퀴즈 중 하나를 X 문제로 변경
    이미 X가 있는 차시는 유지
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)
    
    # 차시별 퀴즈 그룹화
    차시별_퀴즈 = defaultdict(list)
    for i, row in enumerate(rows):
        if row['유형'] == '퀴즈':
            차시별_퀴즈[row['차시']].append((i, row))
    
    changes = []
    
    # 각 차시별로 X 문제 확인 및 추가
    for 차시, 퀴즈들 in 차시별_퀴즈.items():
        has_x = any(q[1]['정답'] == 'X' for q in 퀴즈들)
        
        if not has_x and len(퀴즈들) >= 2:
            # 두 번째 퀴즈를 X로 변경
            idx, quiz = 퀴즈들[1]
            
            # 문제를 반대로 만들어서 X로 변경
            original_content = quiz['내용']
            original_answer = quiz['정답']
            original_explanation = quiz['해설']
            
            # 문제를 반대로 만들기 (간단한 패턴)
            if '없이' in original_content or '불필요' in original_content:
                # 긍정문으로 변경
                new_content = original_content.replace('없이', '필요로').replace('불필요', '필요')
                new_answer = 'X'
                new_explanation = f"정답은 O입니다. {original_explanation}"
            elif '필요' in original_content or '사용' in original_content:
                # 부정문으로 변경
                new_content = original_content.replace('필요', '불필요').replace('사용', '사용하지 않음')
                new_answer = 'X'
                new_explanation = f"정답은 O입니다. {original_explanation}"
            else:
                # 일반적인 반대 문제 생성
                new_content = original_content.replace('수 있다', '수 없다').replace('가능하다', '불가능하다')
                new_answer = 'X'
                new_explanation = f"정답은 O입니다. {original_explanation}"
            
            rows[idx]['내용'] = new_content
            rows[idx]['정답'] = new_answer
            rows[idx]['해설'] = new_explanation
            
            changes.append(f"{차시} 2번 퀴즈를 X 문제로 변경")
    
    # 수정된 내용 저장
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['차시', '유형', '번호', '내용', '정답', '해설']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    return changes

def main():
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    print(f'[진행] CSV 파일 수정 중: {csv_file}')
    
    # 1. 세미콜론을 쉼표로 변경
    print('[1단계] 내용 안의 세미콜론을 쉼표로 변경 중...')
    semicolon_changes = fix_semicolons_in_content(csv_file)
    print(f'  - {len(semicolon_changes)}개 수정 완료')
    
    # 2. X 문제 추가
    print('[2단계] X 문제 추가 중...')
    x_changes = add_x_questions(csv_file)
    print(f'  - {len(x_changes)}개 차시에 X 문제 추가')
    for change in x_changes:
        print(f'    {change}')
    
    print(f'\n[성공] CSV 파일 수정 완료: {csv_file}')
    
    # 엑셀 파일 재생성
    print('\n[진행] 엑셀 파일 재생성 중...')
    try:
        import subprocess
        result = subprocess.run(['python', 'create_formatted_excel_v2.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f'[경고] 엑셀 파일 재생성 실패: {e}')
        print('       수동으로 create_formatted_excel_v2.py를 실행하세요.')

if __name__ == '__main__':
    main()

