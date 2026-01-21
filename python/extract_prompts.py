# -*- coding: utf-8 -*-
"""
각 레슨별 프롬프트 파일에서 프롬프트 내용만 추출하여 prompts 폴더에 정리하는 스크립트
"""
import os
import re
from pathlib import Path

def extract_prompts_from_file(file_path):
    """프롬프트 파일에서 프롬프트 내용만 추출"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 프롬프트만 추출 (```text ... ``` 부분)
    prompts = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 프롬프트 시작 패턴 찾기
        if re.match(r'^## \d+번 프롬프트', line):
            prompt_num = re.search(r'(\d+)번', line).group(1)
            prompt_content = []
            
            # 다음 줄부터 프롬프트 내용 찾기
            i += 1
            while i < len(lines):
                current_line = lines[i]
                
                # ```text 시작
                if current_line.strip() == '```text':
                    i += 1
                    # ``` 까지 읽기
                    while i < len(lines):
                        if lines[i].strip() == '```':
                            break
                        prompt_content.append(lines[i])
                        i += 1
                    break
                elif current_line.strip().startswith('```'):
                    # 다른 코드 블록 시작 (프롬프트가 아님)
                    break
                elif re.match(r'^### ', current_line) or re.match(r'^---', current_line):
                    # 결과 섹션 시작
                    break
                i += 1
            
            if prompt_content:
                prompts.append({
                    'num': prompt_num,
                    'content': '\n'.join(prompt_content).strip()
                })
        else:
            i += 1
    
    return prompts

def create_prompt_file(lesson_num, prompts, output_dir):
    """프롬프트 내용만으로 새 파일 생성"""
    output_file = output_dir / f"lesson-{lesson_num:02d}-prompts.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {lesson_num}차시 프롬프트 모음\n\n")
        
        for prompt in prompts:
            f.write(f"## {prompt['num']}번 프롬프트\n")
            f.write("```text\n")
            f.write(prompt['content'])
            f.write("\n```\n\n")
            f.write("---\n\n")
    
    print(f"✓ {output_file.name} 생성 완료 ({len(prompts)}개 프롬프트)")

def main():
    base_dir = Path(__file__).parent.parent
    prompts_dir = base_dir / 'prompts'
    prompts_dir.mkdir(exist_ok=True)
    
    # 모든 lesson 폴더 찾기
    lesson_dirs = sorted([d for d in base_dir.glob('lesson-*') if d.is_dir()])
    
    for lesson_dir in lesson_dirs:
        lesson_num_str = lesson_dir.name.replace('lesson-', '')
        try:
            lesson_num = int(lesson_num_str)
        except ValueError:
            continue
        
        prompt_file = lesson_dir / f"lesson-{lesson_num_str}-prompts.md"
        
        if prompt_file.exists():
            print(f"\n[{lesson_num}차시] {prompt_file.name} 처리 중...")
            prompts = extract_prompts_from_file(prompt_file)
            
            if prompts:
                create_prompt_file(lesson_num, prompts, prompts_dir)
            else:
                print(f"  ⚠ 프롬프트를 찾을 수 없습니다.")
        else:
            print(f"\n[{lesson_num}차시] 프롬프트 파일이 없습니다.")
    
    print(f"\n\n완료! 총 {len(list(prompts_dir.glob('*.md')))}개 파일 생성")

if __name__ == '__main__':
    main()
