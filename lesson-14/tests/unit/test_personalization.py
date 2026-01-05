"""
개인화 시스템 단위 테스트
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.personalization import (
    PersonalizationSystem,
    BehaviorAnalyzer,
    RecommendationEngine,
    LearningEngine,
    FeedbackCollector,
    DashboardGenerator,
    RecommendationType,
    FeedbackType
)
from src.personalization.user_preferences import (
    UserPreferences,
    PreferenceManager,
    InvestmentProfile,
    InvestmentGoal,
    RiskTolerance,
    TradingStyle
)


class TestBehaviorAnalyzer:
    """행동 분석기 테스트"""
    
    def test_analyze_empty_behavior(self):
        """빈 행동 데이터 분석"""
        analyzer = BehaviorAnalyzer()
        prefs = UserPreferences("test_user")
        
        analysis = analyzer.analyze_user_behavior(prefs)
        
        assert analysis["user_id"] == "test_user"
        assert analysis["behavior_patterns"]["total_actions"] == 0
    
    def test_analyze_behavior_patterns(self):
        """행동 패턴 분석"""
        analyzer = BehaviorAnalyzer()
        prefs = UserPreferences("test_user")
        
        # 행동 기록
        prefs.record_behavior("view_dashboard", {"page": "dashboard"})
        prefs.record_behavior("view_strategy", {"strategy": "test"})
        prefs.record_behavior("view_dashboard", {"page": "dashboard"})
        
        analysis = analyzer.analyze_user_behavior(prefs)
        
        assert analysis["behavior_patterns"]["total_actions"] == 3
        assert "view_dashboard" in analysis["behavior_patterns"]["action_frequency"]
    
    def test_analyze_trading_patterns(self):
        """거래 패턴 분석"""
        analyzer = BehaviorAnalyzer()
        prefs = UserPreferences("test_user")
        
        trade_history = [
            {"coin": "KRW-BTC", "profit": 2.5, "timestamp": datetime.now().isoformat()},
            {"coin": "KRW-BTC", "profit": -1.0, "timestamp": datetime.now().isoformat()},
            {"coin": "KRW-ETH", "profit": 3.0, "timestamp": datetime.now().isoformat()},
        ]
        
        analysis = analyzer.analyze_user_behavior(prefs, trade_history)
        
        assert analysis["trading_patterns"]["total_trades"] == 3
        assert analysis["trading_patterns"]["win_rate"] > 0
        assert "KRW-BTC" in analysis["trading_patterns"]["favorite_coins"]


class TestRecommendationEngine:
    """추천 엔진 테스트"""
    
    def test_recommend_strategies(self):
        """전략 추천 테스트"""
        engine = RecommendationEngine()
        prefs = UserPreferences("test_user")
        prefs.investment_profile.risk_tolerance = RiskTolerance.MODERATE
        
        recommendations = engine.get_recommendations(
            prefs,
            recommendation_types=[RecommendationType.STRATEGY],
            limit=5
        )
        
        assert len(recommendations) > 0
        assert all(r.type == RecommendationType.STRATEGY for r in recommendations)
    
    def test_recommend_coins(self):
        """코인 추천 테스트"""
        engine = RecommendationEngine()
        prefs = UserPreferences("test_user")
        prefs.investment_profile.risk_tolerance = RiskTolerance.LOW
        
        recommendations = engine.get_recommendations(
            prefs,
            recommendation_types=[RecommendationType.COIN],
            limit=5
        )
        
        assert len(recommendations) > 0
        assert all(r.type == RecommendationType.COIN for r in recommendations)
    
    def test_recommend_education(self):
        """교육 콘텐츠 추천 테스트"""
        engine = RecommendationEngine()
        prefs = UserPreferences("test_user")
        prefs.learning_prefs.learning_level = "beginner"
        
        recommendations = engine.get_recommendations(
            prefs,
            recommendation_types=[RecommendationType.EDUCATION],
            limit=5
        )
        
        assert len(recommendations) > 0
        assert all(r.type == RecommendationType.EDUCATION for r in recommendations)


class TestLearningEngine:
    """학습 엔진 테스트"""
    
    def test_train_user_model_empty(self):
        """빈 데이터로 모델 훈련"""
        engine = LearningEngine()
        prefs = UserPreferences("test_user")
        
        model = engine.train_user_model("test_user", prefs)
        
        assert model["user_id"] == "test_user"
        assert model["confidence_score"] >= 0
        assert model["confidence_score"] <= 1
    
    def test_train_user_model_with_data(self):
        """데이터가 있는 모델 훈련"""
        engine = LearningEngine()
        prefs = UserPreferences("test_user")
        
        # 행동 기록
        for i in range(10):
            prefs.record_behavior(f"action_{i}", {"test": True})
        
        # 거래 내역
        trade_history = [
            {"coin": "KRW-BTC", "profit": 2.5, "timestamp": datetime.now().isoformat()},
            {"coin": "KRW-ETH", "profit": 1.5, "timestamp": datetime.now().isoformat()},
        ]
        
        model = engine.train_user_model("test_user", prefs, trade_history)
        
        assert model["confidence_score"] > 0
        assert "behavior_patterns" in model
        assert "preference_patterns" in model
    
    def test_predict_preferences(self):
        """선호도 예측 테스트"""
        engine = LearningEngine()
        prefs = UserPreferences("test_user")
        
        # 모델 훈련
        engine.train_user_model("test_user", prefs)
        
        # 예측
        predictions = engine.predict_preferences("test_user", {"current_hour": 14})
        
        assert isinstance(predictions, dict)


class TestFeedbackCollector:
    """피드백 수집기 테스트"""
    
    def test_collect_rating(self):
        """평점 피드백 수집"""
        collector = FeedbackCollector()
        
        feedback = collector.collect_rating(
            "test_user",
            "strategy",
            "test_strategy",
            5,
            "Great!"
        )
        
        assert feedback.user_id == "test_user"
        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.content["rating"] == 5
    
    def test_collect_feature_feedback(self):
        """기능 피드백 수집"""
        collector = FeedbackCollector()
        
        feedback = collector.collect_feature_feedback(
            "test_user",
            "portfolio_value",
            4,
            5,
            4
        )
        
        assert feedback.feedback_type == FeedbackType.FEATURE_FEEDBACK
        assert feedback.content["feature"] == "portfolio_value"
    
    def test_get_feedback_summary(self):
        """피드백 요약 테스트"""
        collector = FeedbackCollector()
        
        # 피드백 수집
        collector.collect_rating("test_user", "strategy", "test", 5)
        collector.collect_rating("test_user", "coin", "KRW-BTC", 4)
        
        summary = collector.get_feedback_summary("test_user")
        
        assert summary["total_feedback"] >= 2
        assert summary["average_rating"] > 0


class TestDashboardGenerator:
    """대시보드 생성기 테스트"""
    
    def test_generate_dashboard(self):
        """대시보드 생성 테스트"""
        generator = DashboardGenerator()
        prefs = UserPreferences("test_user")
        
        dashboard = generator.generate_dashboard(prefs)
        
        assert dashboard["user_id"] == "test_user"
        assert "layout" in dashboard
        assert "widgets" in dashboard
        assert len(dashboard["widgets"]) > 0
    
    def test_generate_dashboard_with_preferences(self):
        """선호도 기반 대시보드 생성"""
        generator = DashboardGenerator()
        prefs = UserPreferences("test_user")
        
        # 대시보드 선호도 설정
        prefs.dashboard_prefs.layout = "grid"
        prefs.dashboard_prefs.theme = "dark"
        prefs.dashboard_prefs.enabled_widgets = ["portfolio_value", "price_chart"]
        
        dashboard = generator.generate_dashboard(prefs)
        
        assert dashboard["layout"]["type"] == "grid"
        assert dashboard["theme"] == "dark"
        assert len(dashboard["widgets"]) >= 2


class TestPersonalizationSystem:
    """통합 개인화 시스템 테스트"""
    
    def test_initialize_user(self):
        """사용자 초기화 테스트"""
        system = PersonalizationSystem()
        
        prefs = system.initialize_user("test_user")
        
        assert prefs.user_id == "test_user"
        assert prefs.investment_profile is not None
    
    def test_record_user_action(self):
        """사용자 행동 기록 테스트"""
        system = PersonalizationSystem()
        system.initialize_user("test_user")
        
        system.record_user_action(
            "test_user",
            "view_dashboard",
            {"page": "dashboard"}
        )
        
        prefs = system.preference_manager.load_preferences("test_user")
        assert len(prefs.behavior_history) > 0
    
    def test_get_recommendations(self):
        """추천 받기 테스트"""
        system = PersonalizationSystem()
        system.initialize_user("test_user")
        
        recommendations = system.get_recommendations("test_user", limit=5)
        
        assert isinstance(recommendations, list)
    
    def test_get_personalized_dashboard(self):
        """개인화된 대시보드 생성 테스트"""
        system = PersonalizationSystem()
        system.initialize_user("test_user")
        
        dashboard = system.get_personalized_dashboard("test_user")
        
        assert dashboard["user_id"] == "test_user"
        assert "widgets" in dashboard
    
    def test_collect_feedback(self):
        """피드백 수집 테스트"""
        system = PersonalizationSystem()
        system.initialize_user("test_user")
        
        feedback = system.collect_feedback(
            "test_user",
            FeedbackType.RATING,
            {
                "item_type": "strategy",
                "item_id": "test_strategy",
                "rating": 5
            }
        )
        
        assert feedback["user_id"] == "test_user"
        assert feedback["feedback_type"] == "rating"
    
    def test_get_personalization_score(self):
        """개인화 점수 계산 테스트"""
        system = PersonalizationSystem()
        system.initialize_user("test_user")
        
        # 행동 기록
        for i in range(5):
            system.record_user_action("test_user", f"action_{i}", {})
        
        score = system.get_personalization_score("test_user")
        
        assert "score" in score
        assert "level" in score
        assert 0 <= score["score"] <= 100
        assert score["level"] in ["low", "fair", "good", "excellent"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





