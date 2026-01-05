#!/usr/bin/env python
"""
테스트 실행 스크립트
"""

import sys
import subprocess
from pathlib import Path

def main():
    """테스트 실행"""
    project_root = Path(__file__).parent
    
    # 테스트 타입 선택
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    # pytest 명령어 구성
    cmd = ["pytest", "-v"]
    
    if test_type == "unit":
        cmd.append("tests/unit/")
        print("단위 테스트 실행 중...")
    elif test_type == "integration":
        cmd.append("tests/integration/")
        print("통합 테스트 실행 중...")
    elif test_type == "personalization":
        cmd.extend([
            "tests/unit/test_personalization.py",
            "tests/integration/test_personalization_integration.py"
        ])
        print("개인화 시스템 테스트 실행 중...")
    elif test_type == "coverage":
        cmd.extend([
            "--cov=src/personalization",
            "--cov-report=html",
            "--cov-report=term",
            "tests/"
        ])
        print("커버리지 포함 테스트 실행 중...")
    else:
        cmd.append("tests/")
        print("전체 테스트 실행 중...")
    
    # 테스트 실행
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()





