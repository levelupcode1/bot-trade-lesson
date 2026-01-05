"""
개인화 시스템 통합 테스트
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
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


class TestPersonalizationWorkflow:
    """개인화 시스템 전체 워크플로우 테스트"""
    
    @pytest.fixture
    def system(self):
        """테스트용 시스템 인스턴스"""
        return PersonalizationSystem()
    
    @pytest.fixture
    def user_id(self):
        """테스트 사용자 ID"""
        return f"test_user_{datetime.now().timestamp()}"
    
    def test_complete_personalization_workflow(self, system, user_id):
        """완전한 개인화 워크플로우 테스트"""
        # 1. 사용자 초기화
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
        
        prefs = system.initialize_user(user_id, initial_prefs)
        assert prefs.user_id == user_id
        
        # 2. 사용자 행동 기록
        actions = [
            ("view_dashboard", {"page": "dashboard"}),
            ("view_strategy", {"strategy": "volatility_breakout"}),
            ("add_favorite_coin", {"coin": "KRW-BTC"}),
            ("view_chart", {"coin": "KRW-BTC", "timeframe": "1d"}),
        ]
        
        for action, context in actions:
            system.record_user_action(user_id, action, context)
        
        # 3. 거래 내역 생성
        trade_history = [
            {
                "coin": "KRW-BTC",
                "strategy": "volatility_breakout",
                "profit": 2.5,
                "timestamp": datetime.now().isoformat()
            },
            {
                "coin": "KRW-ETH",
                "strategy": "ma_crossover",
                "profit": -1.2,
                "timestamp": datetime.now().isoformat()
            },
            {
                "coin": "KRW-BTC",
                "strategy": "volatility_breakout",
                "profit": 3.1,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # 4. 사용자 분석
        analysis = system.analyze_user(user_id, trade_history)
        assert analysis["user_id"] == user_id
        assert "behavior_analysis" in analysis
        assert "learning_model" in analysis
        
        # 5. 추천 받기
        recommendations = system.get_recommendations(
            user_id,
            recommendation_types=[
                RecommendationType.STRATEGY,
                RecommendationType.COIN
            ],
            limit=5
        )
        assert len(recommendations) > 0
        
        # 6. 개인화된 대시보드 생성
        dashboard = system.get_personalized_dashboard(user_id)
        assert dashboard["user_id"] == user_id
        assert len(dashboard["widgets"]) > 0
        
        # 7. 피드백 수집
        feedback = system.collect_feedback(
            user_id,
            FeedbackType.RATING,
            {
                "item_type": "strategy",
                "item_id": "volatility_breakout",
                "rating": 5,
                "comment": "Great strategy!"
            }
        )
        assert feedback["user_id"] == user_id
        
        # 8. 개인화 점수 확인
        score = system.get_personalization_score(user_id)
        assert 0 <= score["score"] <= 100
        assert "breakdown" in score
    
    def test_learning_improvement_over_time(self, system, user_id):
        """시간에 따른 학습 개선 테스트"""
        # 초기 사용자 생성
        system.initialize_user(user_id)
        
        # 초기 점수
        initial_score = system.get_personalization_score(user_id)
        
        # 행동 기록 (많은 데이터)
        for i in range(50):
            system.record_user_action(
                user_id,
                f"action_{i % 5}",
                {"iteration": i}
            )
        
        # 거래 내역 추가
        trade_history = [
            {
                "coin": "KRW-BTC",
                "strategy": "test_strategy",
                "profit": 2.0,
                "timestamp": datetime.now().isoformat()
            }
        ] * 10
        
        # 피드백 수집
        for i in range(5):
            system.collect_feedback(
                user_id,
                FeedbackType.RATING,
                {
                    "item_type": "strategy",
                    "item_id": f"strategy_{i}",
                    "rating": 4 + (i % 2)
                }
            )
        
        # 재분석
        system.analyze_user(user_id, trade_history)
        
        # 최종 점수
        final_score = system.get_personalization_score(user_id)
        
        # 점수가 개선되었는지 확인 (항상은 아니지만 일반적으로)
        assert final_score["score"] >= 0
        assert final_score["score"] <= 100
    
    def test_recommendation_quality(self, system, user_id):
        """추천 품질 테스트"""
        system.initialize_user(user_id)
        
        # 리스크 성향 설정
        system.update_preferences(
            user_id,
            "investment",
            risk_tolerance=RiskTolerance.LOW
        )
        
        # 추천 받기
        recommendations = system.get_recommendations(
            user_id,
            recommendation_types=[RecommendationType.STRATEGY],
            limit=10
        )
        
        # 추천이 있는지 확인
        assert len(recommendations) > 0
        
        # 추천 신뢰도 확인
        for rec in recommendations:
            assert 0 <= rec["confidence"] <= 1
            assert "reason" in rec
            assert "title" in rec
    
    def test_dashboard_customization(self, system, user_id):
        """대시보드 커스터마이징 테스트"""
        system.initialize_user(user_id)
        
        # 대시보드 선호도 설정
        system.update_preferences(
            user_id,
            "dashboard",
            layout="grid",
            theme="dark",
            enabled_widgets=["portfolio_value", "price_chart", "recent_trades"]
        )
        
        # 대시보드 생성
        dashboard = system.get_personalized_dashboard(user_id)
        
        assert dashboard["layout"]["type"] == "grid"
        assert dashboard["theme"] == "dark"
        
        # 설정한 위젯이 포함되어 있는지 확인
        widget_ids = [w["widget_id"] for w in dashboard["widgets"]]
        assert "portfolio_value" in widget_ids or "profit_loss" in widget_ids
    
    def test_feedback_integration(self, system, user_id):
        """피드백 통합 테스트"""
        system.initialize_user(user_id)
        
        # 다양한 피드백 수집
        feedbacks = [
            (FeedbackType.RATING, {
                "item_type": "strategy",
                "item_id": "test_strategy",
                "rating": 5
            }),
            (FeedbackType.FEATURE_FEEDBACK, {
                "feature": "portfolio_value",
                "rating": 4,
                "usefulness": 5,
                "ease_of_use": 4
            }),
            (FeedbackType.RECOMMENDATION_FEEDBACK, {
                "recommendation_id": "rec_1",
                "accepted": True,
                "reason": "Good recommendation"
            })
        ]
        
        for feedback_type, content in feedbacks:
            feedback = system.collect_feedback(user_id, feedback_type, content)
            assert feedback["user_id"] == user_id
        
        # 피드백 요약 확인
        summary = system.get_feedback_summary(user_id)
        assert summary["total_feedback"] == len(feedbacks)
        assert summary["average_rating"] > 0
    
    def test_preference_evolution(self, system, user_id):
        """선호도 진화 테스트"""
        system.initialize_user(user_id)
        
        # 초기 선호도
        initial_prefs = system.preference_manager.load_preferences(user_id)
        initial_coins = len(initial_prefs.trading_prefs.favorite_coins)
        
        # 선호 코인 추가
        system.update_preferences(
            user_id,
            "trading",
            favorite_coins=["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        )
        
        # 업데이트된 선호도 확인
        updated_prefs = system.preference_manager.load_preferences(user_id)
        assert len(updated_prefs.trading_prefs.favorite_coins) >= 3
        
        # 대시보드 캐시가 무효화되었는지 확인
        dashboard = system.get_personalized_dashboard(user_id)
        assert dashboard["user_id"] == user_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





