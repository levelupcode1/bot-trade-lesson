"""
개인화 시스템 사용 예제
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.personalization import (
    PersonalizationSystem,
    RecommendationType,
    FeedbackType
)
from src.personalization.user_preferences import (
    InvestmentProfile,
    InvestmentGoal,
    RiskTolerance,
    TradingStyle
)


def main():
    """개인화 시스템 사용 예제"""
    
    # 개인화 시스템 초기화
    personalization = PersonalizationSystem()
    
    # 사용자 ID
    user_id = "user001"
    
    print("=" * 60)
    print("개인화 시스템 사용 예제")
    print("=" * 60)
    
    # 1. 사용자 초기화
    print("\n[1] 사용자 초기화")
    print("-" * 60)
    
    initial_prefs = {
        "investment_profile": InvestmentProfile(
            goal=InvestmentGoal.GROWTH,
            risk_tolerance=RiskTolerance.MODERATE,
            trading_style=TradingStyle.BALANCED,
            target_return=10.0,
            max_drawdown=-15.0,
            investment_horizon=12
        )
    }
    
    preferences = personalization.initialize_user(user_id, initial_prefs)
    print(f"사용자 {user_id} 초기화 완료")
    print(f"리스크 허용도: {preferences.investment_profile.risk_tolerance.value}")
    print(f"거래 스타일: {preferences.investment_profile.trading_style.value}")
    
    # 2. 사용자 행동 기록
    print("\n[2] 사용자 행동 기록")
    print("-" * 60)
    
    # 여러 행동 기록
    actions = [
        ("view_dashboard", {"page": "dashboard", "feature": "portfolio"}),
        ("view_strategy", {"strategy": "volatility_breakout"}),
        ("add_favorite_coin", {"coin": "KRW-BTC"}),
        ("view_chart", {"coin": "KRW-BTC", "timeframe": "1d"}),
        ("place_order", {"coin": "KRW-BTC", "amount": 100000}),
    ]
    
    for action, context in actions:
        personalization.record_user_action(user_id, action, context)
        print(f"행동 기록: {action}")
    
    # 3. 사용자 분석
    print("\n[3] 사용자 종합 분석")
    print("-" * 60)
    
    # 거래 내역 (예시)
    trade_history = [
        {
            "coin": "KRW-BTC",
            "strategy": "volatility_breakout",
            "profit": 2.5,
            "timestamp": "2024-01-15T10:00:00"
        },
        {
            "coin": "KRW-ETH",
            "strategy": "ma_crossover",
            "profit": -1.2,
            "timestamp": "2024-01-15T14:00:00"
        },
        {
            "coin": "KRW-BTC",
            "strategy": "volatility_breakout",
            "profit": 3.1,
            "timestamp": "2024-01-16T09:00:00"
        }
    ]
    
    analysis = personalization.analyze_user(user_id, trade_history)
    print(f"분석 완료: {analysis['analyzed_at']}")
    print(f"행동 패턴: {len(analysis['behavior_analysis']['behavior_patterns'])}개 패턴 발견")
    print(f"모델 신뢰도: {analysis['learning_model']['confidence_score']:.2%}")
    
    # 인사이트 출력
    print("\n인사이트:")
    for insight in analysis['insights'][:3]:
        print(f"  - {insight}")
    
    # 4. 맞춤 추천
    print("\n[4] 맞춤 추천")
    print("-" * 60)
    
    recommendations = personalization.get_recommendations(
        user_id,
        recommendation_types=[
            RecommendationType.STRATEGY,
            RecommendationType.COIN,
            RecommendationType.ACTION
        ],
        limit=5
    )
    
    print(f"추천 항목 {len(recommendations)}개:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']}")
        print(f"   타입: {rec['type']}")
        print(f"   신뢰도: {rec['confidence']:.2%}")
        print(f"   이유: {rec['reason']}")
    
    # 5. 개인화된 대시보드
    print("\n[5] 개인화된 대시보드 생성")
    print("-" * 60)
    
    dashboard = personalization.get_personalized_dashboard(user_id)
    print(f"대시보드 생성 완료")
    print(f"레이아웃: {dashboard['layout']['type']}")
    print(f"테마: {dashboard['theme']}")
    print(f"위젯 수: {len(dashboard['widgets'])}")
    
    print("\n위젯 목록:")
    for widget in dashboard['widgets'][:5]:
        print(f"  - {widget['title']} ({widget['size']})")
    
    # 6. 피드백 수집
    print("\n[6] 피드백 수집")
    print("-" * 60)
    
    # 평점 피드백
    feedback1 = personalization.collect_feedback(
        user_id,
        FeedbackType.RATING,
        {
            "item_type": "strategy",
            "item_id": "volatility_breakout",
            "rating": 5,
            "comment": "매우 만족합니다!"
        }
    )
    print(f"평점 피드백 수집: {feedback1['feedback_type']}")
    
    # 기능 피드백
    feedback2 = personalization.collect_feedback(
        user_id,
        FeedbackType.FEATURE_FEEDBACK,
        {
            "feature": "portfolio_value",
            "rating": 4,
            "usefulness": 5,
            "ease_of_use": 4,
            "comment": "유용한 기능입니다"
        }
    )
    print(f"기능 피드백 수집: {feedback2['feedback_type']}")
    
    # 추천 피드백
    if recommendations:
        feedback3 = personalization.collect_feedback(
            user_id,
            FeedbackType.RECOMMENDATION_FEEDBACK,
            {
                "recommendation_id": recommendations[0]['item_id'],
                "accepted": True,
                "reason": "추천이 적절했습니다"
            }
        )
        print(f"추천 피드백 수집: {feedback3['feedback_type']}")
    
    # 7. 피드백 요약
    print("\n[7] 피드백 요약")
    print("-" * 60)
    
    feedback_summary = personalization.get_feedback_summary(user_id)
    print(f"총 피드백 수: {feedback_summary['total_feedback']}")
    print(f"평균 평점: {feedback_summary['average_rating']:.2f}")
    print(f"만족도 점수: {feedback_summary['satisfaction_score']:.2f}")
    print(f"피드백 트렌드: {feedback_summary['feedback_trend']}")
    
    # 8. 학습 인사이트
    print("\n[8] 학습 인사이트")
    print("-" * 60)
    
    learning_insights = personalization.get_learning_insights(user_id)
    print("학습 기반 인사이트:")
    for insight in learning_insights:
        print(f"  - {insight}")
    
    # 9. 행동 인사이트
    print("\n[9] 행동 인사이트")
    print("-" * 60)
    
    behavioral_insights = personalization.get_behavioral_insights(user_id)
    print("행동 기반 인사이트:")
    for insight in behavioral_insights:
        print(f"  - {insight}")
    
    # 10. 사용자 니즈 예측
    print("\n[10] 사용자 니즈 예측")
    print("-" * 60)
    
    needs = personalization.predict_user_needs(user_id)
    print("예측된 니즈:")
    for need in needs:
        print(f"  - {need}")
    
    # 11. 개인화 점수
    print("\n[11] 개인화 점수")
    print("-" * 60)
    
    score = personalization.get_personalization_score(user_id)
    print(f"개인화 점수: {score['score']:.2f}/100 ({score['level']})")
    print("\n세부 점수:")
    for key, value in score['breakdown'].items():
        print(f"  - {key}: {value:.2f}")
    
    # 12. 선호도 업데이트
    print("\n[12] 선호도 업데이트")
    print("-" * 60)
    
    updated = personalization.update_preferences(
        user_id,
        "trading",
        favorite_coins=["KRW-BTC", "KRW-ETH", "KRW-XRP"]
    )
    if updated:
        print("선호 코인 업데이트 완료")
        print(f"선호 코인: {', '.join(updated.trading_prefs.favorite_coins)}")
    
    # 13. 대시보드 새로고침
    print("\n[13] 대시보드 새로고침")
    print("-" * 60)
    
    refreshed_dashboard = personalization.refresh_dashboard(user_id)
    print(f"대시보드 새로고침 완료 (위젯 수: {len(refreshed_dashboard['widgets'])})")
    
    # 14. 시스템 상태
    print("\n[14] 시스템 상태")
    print("-" * 60)
    
    status = personalization.get_system_status()
    print(f"로드된 선호도: {status['preferences_loaded']}")
    print(f"캐시된 대시보드: {status['dashboards_cached']}")
    print(f"학습 모델 수: {status['learning_models']}")
    print(f"시스템 상태: {status['status']}")
    
    print("\n" + "=" * 60)
    print("예제 실행 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()

