# -*- coding: utf-8 -*-
"""
CSV 파일 최종 수정:
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
    CSV 파일 수정
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    semicolon_changes = []
    x_changes = []
    
    # 차시별 X 문제 존재 여부 추적
    차시별_X_존재 = {}
    차시별_퀴즈_정보 = {}  # {차시: [(라인번호, 번호, 정답)]}
    
    # 첫 번째 패스: X 문제 확인
    for i, line in enumerate(lines, 1):
        if i == 1:  # 헤더
            continue
        
        parts = line.strip().split(';')
        if len(parts) < 5:
            continue
        
        차시 = parts[0]
        유형 = parts[1]
        번호 = parts[2]
        정답 = parts[4]
        
        if 유형 == '퀴즈':
            if 차시 not in 차시별_퀴즈_정보:
                차시별_퀴즈_정보[차시] = []
                차시별_X_존재[차시] = False
            차시별_퀴즈_정보[차시].append((i, 번호, 정답))
            if 정답 == 'X':
                차시별_X_존재[차시] = True
    
    # 두 번째 패스: 수정
    for i, line in enumerate(lines, 1):
        original_line = line
        
        # 헤더는 그대로
        if i == 1:
            fixed_lines.append(line)
            continue
        
        # 세미콜론으로 분리
        parts = line.strip().split(';')
        
        if len(parts) < 4:
            fixed_lines.append(line)
            continue
        
        차시 = parts[0]
        유형 = parts[1]
        번호 = parts[2]
        내용 = parts[3]
        정답 = parts[4] if len(parts) > 4 else ''
        해설 = parts[5] if len(parts) > 5 else ''
        
        # 내용 필드의 세미콜론을 쉼표로 변경
        original_content = 내용
        # 괄호 안의 세미콜론 처리: (KRW; USD; EUR) -> (KRW, USD, EUR)
        def replace_in_parens(match):
            text = match.group(1)
            return '(' + text.replace(';', ',') + ')'
        내용 = re.sub(r'\(([^)]*)\)', replace_in_parens, 내용)
        # 일반적인 세미콜론을 쉼표로 (공백이 있는 경우)
        내용 = 내용.replace('; ', ', ')
        # 나머지 세미콜론도 쉼표로
        if ';' in 내용:
            내용 = 내용.replace(';', ',')
        
        if 내용 != original_content:
            semicolon_changes.append(f"줄 {i}: 내용 필드")
        
        # 해설 필드의 세미콜론을 쉼표로 변경
        original_explanation = 해설
        해설 = re.sub(r'\(([^)]*)\)', replace_in_parens, 해설)
        해설 = 해설.replace('; ', ', ')
        if ';' in 해설:
            해설 = 해설.replace(';', ',')
        
        if 해설 != original_explanation:
            semicolon_changes.append(f"줄 {i}: 해설 필드")
        
        # X 문제 추가 (두 번째 퀴즈이고 X가 없는 경우)
        if 유형 == '퀴즈' and 번호 == '2' and not 차시별_X_존재[차시]:
            original_answer = 정답
            original_explanation = 해설
            original_content_before = 내용
            
            # 문제를 반대로 만들어서 X로 변경
            if '없이' in 내용:
                내용 = 내용.replace('없이', '필요로')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            elif '필요하다' in 내용:
                내용 = 내용.replace('필요하다', '불필요하다')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            elif '불필요하다' in 내용:
                내용 = 내용.replace('불필요하다', '필요하다')
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
                if '한다' in 내용:
                    내용 = 내용.replace('한다', '하지 않는다')
                elif '된다' in 내용:
                    내용 = 내용.replace('된다', '되지 않는다')
                정답 = 'X'
                해설 = f"정답은 O입니다. {original_explanation}"
            
            if 정답 != original_answer:
                x_changes.append(f"{차시} 2번 퀴즈")
        
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
        for change in semicolon_changes[:10]:  # 처음 10개만 표시
            print(f'  - {change}')
        if len(semicolon_changes) > 10:
            print(f'  ... 외 {len(semicolon_changes) - 10}개')
    
    print(f'\n[2단계] X 문제 추가: {len(x_changes)}개')
    for change in x_changes:
        print(f'  - {change}')
    
    print(f'\n[성공] CSV 파일 수정 완료: {csv_file}')
    
    # 엑셀 파일 재생성 (다른 이름으로)
    print('\n[진행] 엑셀 파일 재생성 중...')
    try:
        import subprocess
        # 다른 파일명으로 생성
        result = subprocess.run(['python', '-c', 
            'import sys; sys.path.insert(0, "."); from create_formatted_excel_v2 import create_formatted_excel; create_formatted_excel("각_차시별_학습정리.csv", "각_차시별_학습정리_최종.xlsx")'], 
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print('[경고] 엑셀 파일 재생성 실패')
            print('       수동으로 다음 명령을 실행하세요:')
            print('       python create_formatted_excel_v2.py')
    except Exception as e:
        print(f'[경고] 엑셀 파일 재생성 실패: {e}')
        print('       수동으로 다음 명령을 실행하세요:')
        print('       python create_formatted_excel_v2.py')

if __name__ == '__main__':
    main()

