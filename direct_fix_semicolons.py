# -*- coding: utf-8 -*-
"""
CSV 파일에서 내용 안의 세미콜론을 직접 찾아서 쉼표로 변경
"""
import sys
import os
import re

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def direct_replace_semicolons(csv_file):
    """내용 필드의 세미콜론을 직접 찾아서 쉼표로 변경"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # 패턴 1: 괄호 안의 세미콜론 (KRW;USD;EUR) -> (KRW, USD, EUR)
    def replace_in_parens(match):
        full_match = match.group(0)
        inner = match.group(1)
        # 세미콜론을 쉼표로 변경
        inner_fixed = inner.replace(';', ',')
        return '(' + inner_fixed + ')'
    
    # 괄호 안의 세미콜론 처리
    content = re.sub(r'\(([^)]*;[^)]*)\)', replace_in_parens, content)
    
    # 패턴 2: 일반적인 세미콜론 (공백이 있는 경우)
    # 내용 필드와 해설 필드에서만 변경 (구분자 세미콜론은 유지)
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines, 1):
        original_line = line
        
        # 헤더는 그대로
        if i == 1:
            fixed_lines.append(line)
            continue
        
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # 세미콜론으로 분리
        parts = line.split(';')
        
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
        original_content_field = 내용
        # 세미콜론을 쉼표로 변경 (공백 정리)
        내용 = re.sub(r'\s*;\s*', ', ', 내용)
        if ';' in 내용:
            내용 = 내용.replace(';', ',')
        
        if 내용 != original_content_field:
            changes.append(f"줄 {i}: 내용")
        
        # 해설 필드의 세미콜론을 쉼표로 변경
        original_explanation_field = 해설
        해설 = re.sub(r'\s*;\s*', ', ', 해설)
        if ';' in 해설:
            해설 = 해설.replace(';', ',')
        
        if 해설 != original_explanation_field:
            changes.append(f"줄 {i}: 해설")
        
        # 수정된 라인 재구성
        if 해설:
            new_line = f"{차시};{유형};{번호};{내용};{정답};{해설}\n"
        else:
            new_line = f"{차시};{유형};{번호};{내용};{정답};\n"
        fixed_lines.append(new_line)
    
    # 저장
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        f.writelines(fixed_lines)
    
    return changes

def main():
    csv_file = '각_차시별_학습정리.csv'
    
    if not os.path.exists(csv_file):
        print(f'[오류] 파일을 찾을 수 없습니다: {csv_file}')
        return
    
    print(f'[진행] 세미콜론 -> 쉼표 변경 중: {csv_file}')
    changes = direct_replace_semicolons(csv_file)
    
    print(f'[성공] {len(changes)}개 수정 완료')
    if changes:
        for change in changes[:30]:
            print(f'  - {change}')
        if len(changes) > 30:
            print(f'  ... 외 {len(changes) - 30}개')
    
    # 엑셀 파일 재생성
    print('\n[진행] 엑셀 파일 재생성 중...')
    try:
        import subprocess
        result = subprocess.run(['python', 'final_fix_csv.py'], 
                              capture_output=True, text=True, encoding='utf-8', timeout=30)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print('[경고] 엑셀 파일 재생성 실패')
            if result.stderr:
                print(result.stderr)
    except Exception as e:
        print(f'[경고] 엑셀 파일 재생성 실패: {e}')

if __name__ == '__main__':
    main()

