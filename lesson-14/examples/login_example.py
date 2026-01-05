"""
프로필별 로그인 예제
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user.profile.profile_manager import ProfileManager, UserType
from src.personalization import PersonalizationSystem


def login_example():
    """프로필별 로그인 예제"""
    
    print("=" * 80)
    print("프로필별 로그인 예제")
    print("=" * 80)
    
    profile_manager = ProfileManager()
    personalization = PersonalizationSystem()
    
    # 로그인할 사용자들
    users = [
        {
            "user_id": "beginner_user",
            "user_type": UserType.BEGINNER,
            "investment_amount": 1000000,
            "name": "초보자"
        },
        {
            "user_id": "intermediate_user",
            "user_type": UserType.INTERMEDIATE,
            "investment_amount": 5000000,
            "name": "중급자"
        },
        {
            "user_id": "advanced_user",
            "user_type": UserType.ADVANCED,
            "investment_amount": 10000000,
            "name": "고급자"
        }
    ]
    
    for user_config in users:
        print(f"\n{'='*80}")
        print(f"[{user_config['name']} 로그인]")
        print(f"{'='*80}")
        
        user_id = user_config['user_id']
        
        # 1. 프로필 로드 또는 생성
        print(f"\n1. 프로필 확인/생성...")
        profile = profile_manager.load_profile(user_id)
        
        if not profile:
            print(f"   새 프로필 생성 중...")
            profile = profile_manager.create_profile(
                user_id=user_id,
                user_type=user_config['user_type'],
                investment_amount=user_config['investment_amount']
            )
            print(f"   ✓ 프로필 생성 완료: {profile.user_type.value}")
        else:
            print(f"   ✓ 기존 프로필 로드: {profile.user_type.value}")
        
        # 2. 개인화 시스템 초기화
        print(f"\n2. 개인화 시스템 초기화...")
        preferences = personalization.initialize_user(user_id)
        print(f"   ✓ 개인화 시스템 초기화 완료")
        
        # 3. 개인화된 대시보드 확인
        print(f"\n3. 개인화된 대시보드 확인...")
        dashboard = personalization.get_personalized_dashboard(user_id)
        print(f"   ✓ 대시보드 생성 완료")
        print(f"   - 레이아웃: {dashboard.get('layout', {}).get('type', 'N/A')}")
        print(f"   - 위젯 수: {len(dashboard.get('widgets', []))}")
        print(f"   - 위젯 목록:")
        for widget in dashboard.get('widgets', [])[:5]:
            print(f"     • {widget.get('title', 'N/A')}")
        
        # 4. 맞춤 추천 확인
        print(f"\n4. 맞춤 추천 확인...")
        recommendations = personalization.get_recommendations(user_id, limit=3)
        print(f"   ✓ 추천 {len(recommendations)}개 생성")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"     {i}. {rec.get('title', 'N/A')} ({rec.get('type', 'N/A')})")
        
        # 5. 개인화 점수 확인
        print(f"\n5. 개인화 점수 확인...")
        score = personalization.get_personalization_score(user_id)
        print(f"   ✓ 개인화 점수: {score.get('score', 0):.2f}/100 ({score.get('level', 'N/A')})")
        
        print(f"\n✅ {user_config['name']} 로그인 완료!")
    
    print(f"\n{'='*80}")
    print("모든 사용자 로그인 완료!")
    print(f"{'='*80}")
    
    print(f"\n웹 인터페이스에서 로그인하려면:")
    print(f"1. python -m src.ui.web.app 실행")
    print(f"2. http://localhost:5000/login 접속")
    print(f"3. 위의 사용자 ID 중 하나를 입력하고 해당 프로필 타입 선택")


if __name__ == "__main__":
    login_example()





