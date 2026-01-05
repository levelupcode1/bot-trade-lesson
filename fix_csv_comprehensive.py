# -*- coding: utf-8 -*-
"""
CSV 파일 종합 수정:
1. 내용 안의 세미콜론을 쉼표로 변경 (구분자는 유지)
2. 퀴즈 문제에 X 문제 추가
"""
import sys
import os
import re

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fix_csv_file(csv_file):
    """
    CSV 파일 수정:
    1. 내용 필드의 세미콜론을 쉼표로 변경
    2. 해설 필드의 세미콜론을 쉼표로 변경
    3. 각 차시의 두 번째 퀴즈를 X 문제로 변경 (이미 X가 있으면 유지)
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    semicolon_changes = []
    x_changes = []
    
    # 차시별 퀴즈 카운터
    차시별_퀴즈_번호 = {}
    차시별_X_존재 = {}
    
    for i, line in enumerate(lines, 1):
        original_line = line.strip()
        
        # 헤더는 그대로
        if i == 1:
            fixed_lines.append(line)
            continue
        
        # 세미콜론으로 분리
        parts = original_line.split(';')
        
        if len(parts) < 4:
            fixed_lines.append(line)
            continue
        
        차시 = parts[0]
        유형 = parts[1]
        번호 = parts[2]
        내용 = parts[3]
        정답 = parts[4] if len(parts) > 4 else ''
        해설 = parts[5] if len(parts) > 5 else ''
        
        # 퀴즈인 경우 카운트
        if 유형 == '퀴즈':
            if 차시 not in 차시별_퀴즈_번호:
                차시별_퀴즈_번호[차시] = []
                차시별_X_존재[차시] = False
            차시별_퀴즈_번호[차시].append((i, 번호))
            if 정답 == 'X':
                차시별_X_존재[차시] = True
        
        # 내용 필드의 세미콜론을 쉼표로 변경
        original_content = 내용
        # 괄호 안의 세미콜론도 쉼표로 변경
        내용 = re.sub(r'\(([^)]*);([^)]*)\)', r'(\1, \2)', 내용)
        내용 = 내용.replace('; ', ', ')
        # 남은 세미콜론도 쉼표로 (단, 구분자 세미콜론은 이미 분리했으므로 내용 안의 것만)
        if ';' in 내용:
            내용 = 내용.replace(';', ',')
        
        if 내용 != original_content:
            semicolon_changes.append(f"줄 {i}: 내용 필드 세미콜론 -> 쉼표")
        
        # 해설 필드의 세미콜론을 쉼표로 변경
        original_explanation = 해설
        해설 = re.sub(r'\(([^)]*);([^)]*)\)', r'(\1, \2)', 해설)
        해설 = 해설.replace('; ', ', ')
        if ';' in 해설:
            해설 = 해설.replace(';', ',')
        
        if 해설 != original_explanation:
            semicolon_changes.append(f"줄 {i}: 해설 필드 세미콜론 -> 쉼표")
        
        # X 문제 추가 (두 번째 퀴즈이고 X가 없는 경우)
        if 유형 == '퀴즈' and 번호 == '2' and not 차시별_X_존재[차시]:
            original_answer = 정답
            original_explanation = 해설
            
            # 문제를 반대로 만들어서 X로 변경
            if '없이' in 내용 or '불필요' in 내용:
                내용 = 내용.replace('없이', '필요로').replace('불필요', '필요')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            elif '필요' in 내용 and '없이' not in 내용:
                내용 = 내용.replace('필요', '불필요').replace('사용', '사용하지 않음')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            elif '수 있다' in 내용:
                내용 = 내용.replace('수 있다', '수 없다')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            elif '가능하다' in 내용:
                내용 = 내용.replace('가능하다', '불가능하다')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            else:
                # 일반적인 반대 문제
                내용 = f"{내용} (반대)"
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            
            if 정답 != original_answer:
                x_changes.append(f"{차시} 2번 퀴즈를 X 문제로 변경")
        
        # 수정된 라인 재구성
        new_line = f"{차시};{유형};{번호};{내용};{정답};{해설}\n"
        fixed_lines.append(new_line)
    
    # 수정된 내용 저장
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        f.writelines(fixed_lines)
    
    return semicolon_changes, x_changes

def main():
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    print(f'[진행] CSV 파일 수정 중: {csv_file}')
    
    semicolon_changes, x_changes = fix_csv_file(csv_file)
    
    print(f'\n[1단계] 세미콜론 -> 쉼표 변경: {len(semicolon_changes)}개')
    if semicolon_changes:
        for change in semicolon_changes[:5]:  # 처음 5개만 표시
            print(f'  - {change}')
        if len(semicolon_changes) > 5:
            print(f'  ... 외 {len(semicolon_changes) - 5}개')
    
    print(f'\n[2단계] X 문제 추가: {len(x_changes)}개')
    for change in x_changes:
        print(f'  - {change}')
    
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

