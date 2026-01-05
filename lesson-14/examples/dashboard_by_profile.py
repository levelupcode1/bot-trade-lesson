"""
프로필별 대시보드 차이 확인 예제
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.personalization import PersonalizationSystem
from src.user.profile.profile_manager import ProfileManager, UserType
from src.personalization.user_preferences import (
    InvestmentProfile,
    InvestmentGoal,
    RiskTolerance,
    TradingStyle,
    LearningPreferences
)


def compare_dashboards():
    """프로필별 대시보드 비교"""
    
    personalization = PersonalizationSystem()
    profile_manager = ProfileManager()
    
    print("=" * 80)
    print("프로필별 대시보드 비교")
    print("=" * 80)
    
    profiles = [
        ("beginner", UserType.BEGINNER, "초보자"),
        ("intermediate", UserType.INTERMEDIATE, "중급자"),
        ("advanced", UserType.ADVANCED, "고급자")
    ]
    
    dashboards = {}
    
    for profile_id, user_type, profile_name in profiles:
        user_id = f"test_{profile_id}"
        
        print(f"\n{'='*80}")
        print(f"[{profile_name} 프로필]")
        print(f"{'='*80}")
        
        # 프로필 생성
        profile = profile_manager.create_profile(
            user_id=user_id,
            user_type=user_type,
            investment_amount=1000000
        )
        
        # 선호도 초기화 (프로필에 맞게)
        learning_level = profile_id  # beginner, intermediate, advanced
        
        initial_prefs = {
            "investment_profile": InvestmentProfile(
                goal=InvestmentGoal.GROWTH if user_type != UserType.BEGINNER else InvestmentGoal.CAPITAL_PRESERVATION,
                risk_tolerance=RiskTolerance.MODERATE if user_type == UserType.INTERMEDIATE 
                            else (RiskTolerance.LOW if user_type == UserType.BEGINNER else RiskTolerance.HIGH),
                trading_style=TradingStyle.BALANCED if user_type == UserType.INTERMEDIATE
                            else (TradingStyle.CONSERVATIVE if user_type == UserType.BEGINNER else TradingStyle.AGGRESSIVE),
                target_return=5.0 if user_type == UserType.BEGINNER else (10.0 if user_type == UserType.INTERMEDIATE else 15.0),
                max_drawdown=-10.0 if user_type == UserType.BEGINNER else (-15.0 if user_type == UserType.INTERMEDIATE else -20.0),
                investment_horizon=12
            ),
            "learning_prefs": LearningPreferences(
                learning_level=learning_level
            )
        }
        
        # 선호도 생성
        preferences = personalization.initialize_user(user_id, initial_prefs)
        
        # 대시보드 생성
        dashboard = personalization.get_personalized_dashboard(user_id)
        dashboards[profile_name] = dashboard
        
        # 대시보드 정보 출력
        print(f"\n사용자 ID: {user_id}")
        print(f"프로필 타입: {user_type.value}")
        print(f"학습 레벨: {learning_level}")
        print(f"리스크 허용도: {preferences.investment_profile.risk_tolerance.value}")
        print(f"\n대시보드 정보:")
        print(f"  - 레이아웃: {dashboard.get('layout', {}).get('type', 'N/A')}")
        print(f"  - 테마: {dashboard.get('theme', 'N/A')}")
        print(f"  - 위젯 수: {len(dashboard.get('widgets', []))}")
        
        print(f"\n위젯 목록:")
        for i, widget in enumerate(dashboard.get('widgets', []), 1):
            print(f"  {i}. {widget.get('title', 'N/A')} ({widget.get('size', 'N/A')})")
            print(f"     - 타입: {widget.get('widget_type', 'N/A')}")
            print(f"     - 활성화: {widget.get('enabled', False)}")
    
    # 비교 요약
    print(f"\n{'='*80}")
    print("프로필별 대시보드 비교 요약")
    print(f"{'='*80}")
    
    for profile_name, dashboard in dashboards.items():
        widgets = dashboard.get('widgets', [])
        widget_types = [w.get('widget_type') for w in widgets]
        
        print(f"\n[{profile_name}]")
        print(f"  총 위젯 수: {len(widgets)}")
        print(f"  위젯 타입: {', '.join(widget_types)}")
        
        # 레벨별 고유 위젯 확인
        if profile_name == "초보자":
            print(f"  특징: 기본 위젯 중심, 학습 진행도 위젯 포함")
        elif profile_name == "중급자":
            print(f"  특징: 시장 개요, 성과 차트, 리스크 지표 포함")
        elif profile_name == "고급자":
            print(f"  특징: 통계 위젯 포함, 모든 고급 위젯 사용 가능")
    
    # 차이점 분석
    print(f"\n{'='*80}")
    print("주요 차이점")
    print(f"{'='*80}")
    
    beginner_widgets = set(w.get('widget_type') for w in dashboards['초보자'].get('widgets', []))
    intermediate_widgets = set(w.get('widget_type') for w in dashboards['중급자'].get('widgets', []))
    advanced_widgets = set(w.get('widget_type') for w in dashboards['고급자'].get('widgets', []))
    
    print(f"\n초보자 전용 위젯:")
    print(f"  - {beginner_widgets - intermediate_widgets - advanced_widgets}")
    
    print(f"\n중급자 이상 위젯:")
    print(f"  - {intermediate_widgets - beginner_widgets}")
    
    print(f"\n고급자 전용 위젯:")
    print(f"  - {advanced_widgets - intermediate_widgets}")
    
    print(f"\n공통 위젯:")
    print(f"  - {beginner_widgets & intermediate_widgets & advanced_widgets}")


if __name__ == "__main__":
    compare_dashboards()





