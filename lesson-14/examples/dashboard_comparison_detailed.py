"""
프로필별 대시보드 상세 비교 - 행동 데이터 포함
"""

import sys
from pathlib import Path
from datetime import datetime

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


def create_detailed_comparison():
    """상세한 프로필별 대시보드 비교"""
    
    personalization = PersonalizationSystem()
    profile_manager = ProfileManager()
    
    print("=" * 80)
    print("프로필별 대시보드 상세 비교 (행동 데이터 포함)")
    print("=" * 80)
    
    # 프로필 설정
    profiles_config = [
        {
            "id": "beginner",
            "type": UserType.BEGINNER,
            "name": "초보자",
            "learning_level": "beginner",
            "risk": RiskTolerance.LOW,
            "style": TradingStyle.CONSERVATIVE,
            "target_return": 5.0,
            "actions": [
                ("view_dashboard", {"page": "dashboard"}),
                ("view_tutorial", {"topic": "basics"}),
            ]
        },
        {
            "id": "intermediate",
            "type": UserType.INTERMEDIATE,
            "name": "중급자",
            "learning_level": "intermediate",
            "risk": RiskTolerance.MODERATE,
            "style": TradingStyle.BALANCED,
            "target_return": 10.0,
            "actions": [
                ("view_dashboard", {"page": "dashboard"}),
                ("view_strategy", {"strategy": "volatility_breakout"}),
                ("view_chart", {"coin": "KRW-BTC"}),
                ("view_analytics", {"type": "performance"}),
            ]
        },
        {
            "id": "advanced",
            "type": UserType.ADVANCED,
            "name": "고급자",
            "learning_level": "advanced",
            "risk": RiskTolerance.HIGH,
            "style": TradingStyle.AGGRESSIVE,
            "target_return": 15.0,
            "actions": [
                ("view_dashboard", {"page": "dashboard"}),
                ("view_strategy", {"strategy": "custom"}),
                ("view_chart", {"coin": "KRW-BTC", "indicators": ["RSI", "MACD", "Bollinger"]}),
                ("view_analytics", {"type": "advanced"}),
                ("view_statistics", {"metrics": ["sharpe", "max_drawdown"]}),
                ("view_risk_metrics", {"type": "detailed"}),
            ]
        }
    ]
    
    dashboards = {}
    
    for config in profiles_config:
        user_id = f"test_{config['id']}"
        
        print(f"\n{'='*80}")
        print(f"[{config['name']} 프로필]")
        print(f"{'='*80}")
        
        # 프로필 생성
        profile = profile_manager.create_profile(
            user_id=user_id,
            user_type=config['type'],
            investment_amount=1000000
        )
        
        # 선호도 초기화
        initial_prefs = {
            "investment_profile": InvestmentProfile(
                goal=InvestmentGoal.GROWTH if config['type'] != UserType.BEGINNER else InvestmentGoal.CAPITAL_PRESERVATION,
                risk_tolerance=config['risk'],
                trading_style=config['style'],
                target_return=config['target_return'],
                max_drawdown=-10.0 if config['type'] == UserType.BEGINNER else (-15.0 if config['type'] == UserType.INTERMEDIATE else -20.0),
                investment_horizon=12
            ),
            "learning_prefs": LearningPreferences(
                learning_level=config['learning_level']
            )
        }
        
        # 선호도 생성
        preferences = personalization.initialize_user(user_id, initial_prefs)
        
        # 행동 기록
        print(f"\n행동 기록 중...")
        for action, context in config['actions']:
            personalization.record_user_action(user_id, action, context)
            print(f"  ✓ {action}")
        
        # 거래 내역 추가 (중급자, 고급자만)
        if config['type'] != UserType.BEGINNER:
            trade_history = [
                {
                    "coin": "KRW-BTC",
                    "strategy": "volatility_breakout",
                    "profit": 2.5,
                    "timestamp": datetime.now().isoformat()
                }
            ] * 5
            
            # 분석 수행
            analysis = personalization.analyze_user(user_id, trade_history)
            print(f"  ✓ 분석 완료 (모델 신뢰도: {analysis['learning_model']['confidence_score']:.1%})")
        
        # 대시보드 생성
        dashboard = personalization.get_personalized_dashboard(user_id)
        dashboards[config['name']] = dashboard
        
        # 대시보드 정보 출력
        print(f"\n📊 대시보드 구성:")
        print(f"  레이아웃: {dashboard.get('layout', {}).get('type', 'N/A')}")
        print(f"  테마: {dashboard.get('theme', 'N/A')}")
        print(f"  총 위젯 수: {len(dashboard.get('widgets', []))}")
        
        print(f"\n위젯 상세:")
        for i, widget in enumerate(dashboard.get('widgets', []), 1):
            widget_type = widget.get('widget_type', 'N/A')
            title = widget.get('title', 'N/A')
            size = widget.get('size', 'N/A')
            
            # 위젯 레벨 확인
            level_info = ""
            if widget_type in ['market_overview', 'performance_chart', 'risk_metrics']:
                level_info = " (중급 이상)"
            elif widget_type == 'statistics':
                level_info = " (고급 전용)"
            elif widget_type == 'learning_progress':
                level_info = " (초보/중급)"
            
            print(f"  {i}. {title} [{size}]{level_info}")
            print(f"     타입: {widget_type}")
    
    # 비교 분석
    print(f"\n{'='*80}")
    print("프로필별 위젯 비교 분석")
    print(f"{'='*80}")
    
    beginner_widgets = {w.get('widget_type') for w in dashboards['초보자'].get('widgets', [])}
    intermediate_widgets = {w.get('widget_type') for w in dashboards['중급자'].get('widgets', [])}
    advanced_widgets = {w.get('widget_type') for w in dashboards['고급자'].get('widgets', [])}
    
    print(f"\n✅ 초보자 대시보드:")
    print(f"   위젯: {', '.join(sorted(beginner_widgets))}")
    print(f"   특징: 기본 필수 위젯만 표시, 단순한 구성")
    print(f"   목적: 혼란 최소화, 핵심 정보만 제공")
    
    print(f"\n✅ 중급자 대시보드:")
    print(f"   위젯: {', '.join(sorted(intermediate_widgets))}")
    print(f"   특징: 리스크 지표 추가, 분석 기능 확대")
    print(f"   목적: 더 많은 정보 제공, 분석 도구 활용")
    
    print(f"\n✅ 고급자 대시보드:")
    print(f"   위젯: {', '.join(sorted(advanced_widgets))}")
    print(f"   특징: 모든 고급 위젯 사용 가능, 통계 포함")
    print(f"   목적: 전문가 수준의 분석 도구 제공")
    
    # 차이점 요약
    print(f"\n{'='*80}")
    print("주요 차이점 요약")
    print(f"{'='*80}")
    
    only_intermediate = intermediate_widgets - beginner_widgets
    only_advanced = advanced_widgets - intermediate_widgets
    common = beginner_widgets & intermediate_widgets & advanced_widgets
    
    print(f"\n🔹 초보자만: {sorted(beginner_widgets - intermediate_widgets - advanced_widgets) or '없음'}")
    print(f"🔹 중급자 이상: {sorted(only_intermediate) or '없음'}")
    print(f"🔹 고급자 전용: {sorted(only_advanced) or '없음'}")
    print(f"🔹 공통 위젯: {sorted(common)}")
    
    # 위젯 레벨별 분류
    print(f"\n{'='*80}")
    print("위젯 레벨별 분류")
    print(f"{'='*80}")
    
    widget_levels = {
        "기본 (모든 레벨)": ["portfolio_value", "profit_loss", "recent_trades"],
        "중급 이상": ["market_overview", "performance_chart", "risk_metrics"],
        "고급 전용": ["statistics"],
        "초보/중급": ["learning_progress"]
    }
    
    for level, widgets in widget_levels.items():
        print(f"\n{level}:")
        for widget in widgets:
            in_beginner = widget in beginner_widgets
            in_intermediate = widget in intermediate_widgets
            in_advanced = widget in advanced_widgets
            
            status = []
            if in_beginner:
                status.append("초보자✓")
            if in_intermediate:
                status.append("중급자✓")
            if in_advanced:
                status.append("고급자✓")
            
            print(f"  - {widget}: {', '.join(status) if status else '없음'}")


if __name__ == "__main__":
    create_detailed_comparison()





