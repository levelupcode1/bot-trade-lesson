# -*- coding: utf-8 -*-
"""
CSV 파일 완전 수정:
1. 헤더 수정
2. 내용 안의 모든 세미콜론을 쉼표로 변경
3. 13차시 2번 퀴즈 수정
"""
import sys
import os
import re

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fix_csv_completely(csv_file):
    """CSV 파일 완전 수정"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 헤더 수정 (첫 줄이 잘못된 경우)
    lines = content.split('\n')
    if lines[0].startswith('차시;유형;번호;내용;정답;해설1차시'):
        # 헤더와 첫 데이터가 합쳐진 경우
        lines[0] = '차시;유형;번호;내용;정답;해설'
        if '1차시;퀴즈;1;' not in lines[1]:
            # 첫 데이터 추가
            first_data = content.split('해설')[1].split('1차시')[1] if '해설' in content and '1차시' in content.split('해설')[1] else ''
            if first_data:
                lines.insert(1, '1차시' + first_data.split('\n')[0])
    
    fixed_lines = []
    changes = []
    
    for i, line in enumerate(lines, 1):
        original = line.rstrip('\n')
        
        # 헤더는 그대로
        if i == 1:
            if not original.startswith('차시;유형;번호;내용;정답;해설'):
                original = '차시;유형;번호;내용;정답;해설'
            fixed_lines.append(original + '\n')
            continue
        
        if not original.strip():
            fixed_lines.append('\n')
            continue
        
        # 세미콜론으로 분리
        parts = original.split(';')
        
        if len(parts) < 4:
            fixed_lines.append(original + '\n')
            continue
        
        차시 = parts[0]
        유형 = parts[1]
        번호 = parts[2]
        내용 = parts[3]
        정답 = parts[4] if len(parts) > 4 else ''
        해설 = parts[5] if len(parts) > 5 else ''
        
        # 13차시 2번 퀴즈 수정 (손상된 경우)
        if 차시 == '13차시' and 유형 == '퀴즈' and 번호 == '2':
            if '시장 상황별 최적화는 변동성 구간;X;' in original:
                내용 = '시장 상황별 최적화는 변동성 구간, 트렌드/사이드웨이스, 시간대별로 다른 파라미터를 사용하는 방법이다.'
                정답 = 'X'
                해설 = '정답은 O입니다. 시장 상황에 따라 적응적으로 전략 파라미터를 조정하면 더 나은 성과를 얻을 수 있습니다.'
                changes.append(f"줄 {i}: 13차시 2번 퀴즈 수정")
        
        # 내용 필드의 세미콜론을 쉼표로 변경
        original_content = 내용
        # 괄호 안의 세미콜론 처리
        def replace_in_parens(match):
            text = match.group(1)
            return '(' + text.replace(';', ',') + ')'
        내용 = re.sub(r'\(([^)]+)\)', replace_in_parens, 내용)
        # 일반적인 세미콜론을 쉼표로
        내용 = 내용.replace('; ', ', ')
        if ';' in 내용:
            내용 = 내용.replace(';', ',')
        
        if 내용 != original_content:
            changes.append(f"줄 {i}: 내용")
        
        # 해설 필드의 세미콜론을 쉼표로 변경
        original_explanation = 해설
        해설 = re.sub(r'\(([^)]+)\)', replace_in_parens, 해설)
        해설 = 해설.replace('; ', ', ')
        if ';' in 해설:
            해설 = 해설.replace(';', ',')
        
        if 해설 != original_explanation:
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
    
    print(f'[진행] CSV 파일 완전 수정 중: {csv_file}')
    changes = fix_csv_completely(csv_file)
    
    print(f'[성공] {len(changes)}개 수정 완료')
    if changes:
        for change in changes[:20]:
            print(f'  - {change}')
        if len(changes) > 20:
            print(f'  ... 외 {len(changes) - 20}개')
    
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

