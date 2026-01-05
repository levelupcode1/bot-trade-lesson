"""
개인화 시스템 통합 클래스
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .user_preferences import UserPreferences, PreferenceManager
from .behavior_analyzer import BehaviorAnalyzer
from .recommendation_engine import RecommendationEngine, RecommendationType
from .learning_engine import LearningEngine
from .feedback_collector import FeedbackCollector, FeedbackType
from .dashboard_generator import DashboardGenerator


class PersonalizationSystem:
    """통합 개인화 시스템"""
    
    def __init__(
        self,
        preferences_dir: str = "data/user_preferences",
        feedback_dir: str = "data/user_feedback",
        model_dir: str = "data/learning_models"
    ):
        # 하위 시스템 초기화
        self.preference_manager = PreferenceManager(preferences_dir)
        self.behavior_analyzer = BehaviorAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.learning_engine = LearningEngine(model_dir)
        self.feedback_collector = FeedbackCollector(feedback_dir)
        self.dashboard_generator = DashboardGenerator()
        
        # 캐시
        self.user_dashboards: Dict[str, Dict[str, Any]] = {}
    
    def initialize_user(
        self,
        user_id: str,
        initial_preferences: Optional[Dict[str, Any]] = None
    ) -> UserPreferences:
        """사용자 초기화"""
        # 선호도 생성 또는 로드
        preferences = self.preference_manager.load_preferences(user_id)
        
        if not preferences:
            preferences = self.preference_manager.create_preferences(
                user_id,
                **(initial_preferences or {})
            )
        
        return preferences
    
    def record_user_action(
        self,
        user_id: str,
        action: str,
        context: Dict[str, Any]
    ) -> None:
        """사용자 행동 기록"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return
        
        # 행동 기록
        preferences.record_behavior(action, context)
        self.preference_manager.save_preferences(preferences)
        
        # 암묵적 피드백 수집
        self.feedback_collector.collect_implicit_feedback(
            user_id,
            action,
            context
        )
    
    def analyze_user(
        self,
        user_id: str,
        trade_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """사용자 종합 분석"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return {}
        
        # 행동 분석
        behavior_analysis = self.behavior_analyzer.analyze_user_behavior(
            preferences,
            trade_history
        )
        
        # 학습 모델 훈련
        feedback_history = self.feedback_collector.get_user_feedback(user_id)
        learning_model = self.learning_engine.train_user_model(
            user_id,
            preferences,
            trade_history,
            feedback_history
        )
        
        # 통합 분석 결과
        analysis = {
            "user_id": user_id,
            "analyzed_at": datetime.now().isoformat(),
            "behavior_analysis": behavior_analysis,
            "learning_model": learning_model,
            "insights": self._generate_insights(
                user_id,
                behavior_analysis,
                learning_model
            )
        }
        
        return analysis
    
    def get_recommendations(
        self,
        user_id: str,
        recommendation_types: Optional[List[RecommendationType]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """맞춤 추천 제공"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return []
        
        # 추천 생성
        recommendations = self.recommendation_engine.get_recommendations(
            preferences,
            recommendation_types,
            limit
        )
        
        # 딕셔너리로 변환
        return [r.to_dict() for r in recommendations]
    
    def get_personalized_dashboard(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """개인화된 대시보드 생성"""
        # 캐시 확인
        if user_id in self.user_dashboards:
            return self.user_dashboards[user_id]
        
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return {}
        
        # 행동 분석 (간단 버전)
        behavior_analysis = self.behavior_analyzer.analyze_user_behavior(preferences)
        
        # 대시보드 생성
        dashboard = self.dashboard_generator.generate_dashboard(
            preferences,
            behavior_analysis
        )
        
        # 캐시 저장
        self.user_dashboards[user_id] = dashboard
        
        return dashboard
    
    def collect_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """피드백 수집"""
        feedback = self.feedback_collector.collect_feedback(
            user_id,
            feedback_type,
            content,
            metadata
        )
        
        # 피드백 기반 선호도 업데이트
        self._update_preferences_from_feedback(user_id, feedback)
        
        # 학습 모델 재훈련 (비동기로 처리 가능)
        # self._retrain_model_async(user_id)
        
        return feedback.to_dict()
    
    def update_preferences(
        self,
        user_id: str,
        section: str,
        **updates
    ) -> Optional[UserPreferences]:
        """선호도 업데이트"""
        preferences = self.preference_manager.update_preferences(
            user_id,
            section,
            **updates
        )
        
        # 대시보드 캐시 무효화
        if user_id in self.user_dashboards:
            del self.user_dashboards[user_id]
        
        return preferences
    
    def get_learning_insights(
        self,
        user_id: str
    ) -> List[str]:
        """학습 기반 인사이트"""
        return self.learning_engine.get_learning_insights(user_id)
    
    def get_behavioral_insights(
        self,
        user_id: str
    ) -> List[str]:
        """행동 기반 인사이트"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return []
        
        return self.behavior_analyzer.get_behavioral_insights(user_id)
    
    def get_feedback_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """피드백 요약"""
        return self.feedback_collector.get_feedback_summary(user_id)
    
    def predict_user_needs(
        self,
        user_id: str
    ) -> List[str]:
        """사용자 니즈 예측"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return []
        
        behavior_analysis = self.behavior_analyzer.analyze_user_behavior(preferences)
        
        return self.behavior_analyzer.predict_user_needs(
            preferences,
            behavior_analysis
        )
    
    def get_personalization_score(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """개인화 점수 계산"""
        preferences = self.preference_manager.load_preferences(user_id)
        if not preferences:
            return {"score": 0.0, "level": "low"}
        
        # 행동 분석
        behavior_analysis = self.behavior_analyzer.analyze_user_behavior(preferences)
        
        # 학습 모델
        learning_model = self.learning_engine.load_model(user_id)
        
        # 피드백 요약
        feedback_summary = self.feedback_collector.get_feedback_summary(user_id)
        
        # 점수 계산
        score = 0.0
        
        # 행동 데이터 (30점)
        behavior_score = min(
            len(preferences.behavior_history) / 100 * 30,
            30
        )
        score += behavior_score
        
        # 선호도 명확성 (25점)
        preference_score = 0
        if preferences.trading_prefs.favorite_coins:
            preference_score += min(len(preferences.trading_prefs.favorite_coins) * 5, 12.5)
        if preferences.trading_prefs.favorite_strategies:
            preference_score += min(len(preferences.trading_prefs.favorite_strategies) * 5, 12.5)
        score += preference_score
        
        # 학습 모델 신뢰도 (25점)
        if learning_model:
            confidence = learning_model.get("confidence_score", 0)
            score += confidence * 25
        
        # 피드백 참여도 (20점)
        feedback_count = feedback_summary.get("total_feedback", 0)
        score += min(feedback_count / 10 * 20, 20)
        
        # 레벨 결정
        if score >= 80:
            level = "excellent"
        elif score >= 60:
            level = "good"
        elif score >= 40:
            level = "fair"
        else:
            level = "low"
        
        return {
            "score": round(score, 2),
            "level": level,
            "breakdown": {
                "behavior": round(behavior_score, 2),
                "preference": round(preference_score, 2),
                "learning": round(confidence * 25, 2) if learning_model else 0,
                "feedback": round(min(feedback_count / 10 * 20, 20), 2)
            }
        }
    
    def _generate_insights(
        self,
        user_id: str,
        behavior_analysis: Dict[str, Any],
        learning_model: Dict[str, Any]
    ) -> List[str]:
        """통합 인사이트 생성"""
        insights = []
        
        # 행동 인사이트
        behavior_insights = self.behavior_analyzer.get_behavioral_insights(user_id)
        insights.extend(behavior_insights)
        
        # 학습 인사이트
        learning_insights = self.learning_engine.get_learning_insights(user_id)
        insights.extend(learning_insights)
        
        # 모델 신뢰도 인사이트
        confidence = learning_model.get("confidence_score", 0)
        if confidence < 0.3:
            insights.append("더 많은 데이터를 수집하면 더 정확한 개인화가 가능합니다")
        elif confidence > 0.7:
            insights.append("충분한 데이터로 개인화가 잘 이루어지고 있습니다")
        
        return insights
    
    def _update_preferences_from_feedback(
        self,
        user_id: str,
        feedback
    ) -> None:
        """피드백 기반 선호도 업데이트"""
        # 피드백 타입에 따라 선호도 업데이트
        if feedback.feedback_type == FeedbackType.RATING:
            content = feedback.content
            item_type = content.get("item_type")
            item_id = content.get("item_id")
            rating = content.get("rating", 0)
            
            # 높은 평점이면 선호도에 추가
            if rating >= 4:
                if item_type == "coin":
                    self.update_preferences(
                        user_id,
                        "trading",
                        favorite_coins=[item_id]  # 리스트로 추가
                    )
                elif item_type == "strategy":
                    self.update_preferences(
                        user_id,
                        "trading",
                        favorite_strategies=[item_id]
                    )
        
        elif feedback.feedback_type == FeedbackType.FEATURE_FEEDBACK:
            content = feedback.content
            feature = content.get("feature")
            rating = content.get("rating", 0)
            
            # 대시보드 위젯 활성화/비활성화
            if rating >= 4 and feature:
                preferences = self.preference_manager.load_preferences(user_id)
                if preferences and feature not in preferences.dashboard_prefs.enabled_widgets:
                    preferences.dashboard_prefs.enabled_widgets.append(feature)
                    self.preference_manager.save_preferences(preferences)
    
    def refresh_dashboard(self, user_id: str) -> Dict[str, Any]:
        """대시보드 새로고침 (캐시 무효화)"""
        if user_id in self.user_dashboards:
            del self.user_dashboards[user_id]
        
        return self.get_personalized_dashboard(user_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            "preferences_loaded": len(self.preference_manager._cache),
            "dashboards_cached": len(self.user_dashboards),
            "learning_models": len(self.learning_engine.user_models),
            "status": "operational"
        }





