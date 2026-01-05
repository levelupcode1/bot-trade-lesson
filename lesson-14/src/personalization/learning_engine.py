"""
학습 알고리즘 - 사용자 행동을 학습하여 개인화 개선
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import json
from pathlib import Path

from .user_preferences import UserPreferences, RiskTolerance, TradingStyle

# 순환 참조 방지를 위한 타입 체크
try:
    from .feedback_collector import Feedback
except ImportError:
    Feedback = Any


class LearningEngine:
    """사용자 행동 학습 엔진"""
    
    def __init__(self, model_dir: str = "data/learning_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 학습 모델 캐시
        self.user_models: Dict[str, Dict[str, Any]] = {}
        
        # 가중치 초기값
        self.default_weights = {
            "behavior_weight": 0.4,      # 행동 데이터 가중치
            "preference_weight": 0.3,     # 명시적 선호도 가중치
            "performance_weight": 0.2,    # 성과 데이터 가중치
            "feedback_weight": 0.1        # 피드백 가중치
        }
    
    def train_user_model(
        self,
        user_id: str,
        user_preferences: UserPreferences,
        trade_history: Optional[List[Dict]] = None,
        feedback_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """사용자별 학습 모델 훈련"""
        
        # 행동 패턴 학습
        behavior_patterns = self._learn_behavior_patterns(
            user_preferences.behavior_history
        )
        
        # 선호도 패턴 학습
        preference_patterns = self._learn_preference_patterns(
            user_preferences
        )
        
        # 성과 기반 학습
        performance_patterns = self._learn_performance_patterns(
            trade_history or []
        )
        
        # 피드백 기반 학습
        feedback_patterns = self._learn_feedback_patterns(
            feedback_history or []
        )
        
        # 통합 모델 생성
        model = {
            "user_id": user_id,
            "trained_at": datetime.now().isoformat(),
            "behavior_patterns": behavior_patterns,
            "preference_patterns": preference_patterns,
            "performance_patterns": performance_patterns,
            "feedback_patterns": feedback_patterns,
            "weights": self.default_weights.copy(),
            "confidence_score": self._calculate_model_confidence(
                behavior_patterns,
                preference_patterns,
                performance_patterns,
                feedback_patterns
            )
        }
        
        # 모델 저장
        self.user_models[user_id] = model
        self._save_model(user_id, model)
        
        return model
    
    def _learn_behavior_patterns(
        self,
        behavior_history: List[Dict]
    ) -> Dict[str, Any]:
        """행동 패턴 학습"""
        if not behavior_history:
            return {
                "action_preferences": {},
                "time_preferences": {},
                "feature_usage": {},
                "navigation_patterns": {}
            }
        
        # 액션 선호도
        action_counts = defaultdict(int)
        for behavior in behavior_history:
            action = behavior.get("action", "")
            action_counts[action] += 1
        
        total_actions = sum(action_counts.values())
        action_preferences = {
            action: count / total_actions
            for action, count in action_counts.items()
        }
        
        # 시간대 선호도
        hour_counts = defaultdict(int)
        for behavior in behavior_history:
            try:
                timestamp = datetime.fromisoformat(behavior["timestamp"])
                hour_counts[timestamp.hour] += 1
            except:
                continue
        
        total_hours = sum(hour_counts.values())
        time_preferences = {
            hour: count / total_hours
            for hour, count in hour_counts.items()
        }
        
        # 기능 사용 패턴
        feature_usage = defaultdict(int)
        for behavior in behavior_history:
            context = behavior.get("context", {})
            feature = context.get("feature", "")
            if feature:
                feature_usage[feature] += 1
        
        # 네비게이션 패턴
        navigation_patterns = self._extract_navigation_patterns(behavior_history)
        
        return {
            "action_preferences": dict(sorted(
                action_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # 상위 10개
            "time_preferences": dict(sorted(
                time_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),  # 상위 5개
            "feature_usage": dict(feature_usage),
            "navigation_patterns": navigation_patterns
        }
    
    def _extract_navigation_patterns(
        self,
        behavior_history: List[Dict]
    ) -> Dict[str, Any]:
        """네비게이션 패턴 추출"""
        patterns = {
            "common_paths": [],
            "entry_points": [],
            "exit_points": []
        }
        
        # 페이지 전환 패턴 분석
        page_sequence = []
        for behavior in behavior_history:
            context = behavior.get("context", {})
            page = context.get("page", "")
            if page:
                page_sequence.append(page)
        
        # 일반적인 경로 찾기
        if len(page_sequence) > 1:
            path_counts = defaultdict(int)
            for i in range(len(page_sequence) - 1):
                path = f"{page_sequence[i]} -> {page_sequence[i+1]}"
                path_counts[path] += 1
            
            patterns["common_paths"] = [
                {"path": path, "count": count}
                for path, count in sorted(
                    path_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            ]
        
        # 진입점 (첫 페이지)
        if page_sequence:
            entry_counts = defaultdict(int)
            for i, page in enumerate(page_sequence):
                if i == 0 or (i > 0 and page_sequence[i-1] != page):
                    entry_counts[page] += 1
            patterns["entry_points"] = [
                {"page": page, "count": count}
                for page, count in sorted(
                    entry_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
            ]
        
        return patterns
    
    def _learn_preference_patterns(
        self,
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """선호도 패턴 학습"""
        return {
            "risk_tolerance": user_preferences.investment_profile.risk_tolerance.value,
            "trading_style": user_preferences.investment_profile.trading_style.value,
            "favorite_coins": user_preferences.trading_prefs.favorite_coins,
            "favorite_strategies": user_preferences.trading_prefs.favorite_strategies,
            "dashboard_customization": {
                "layout": user_preferences.dashboard_prefs.layout,
                "theme": user_preferences.dashboard_prefs.theme,
                "enabled_widgets": user_preferences.dashboard_prefs.enabled_widgets
            },
            "notification_preferences": {
                "telegram": user_preferences.notification_prefs.telegram_enabled,
                "immediate_alerts": user_preferences.notification_prefs.immediate_alerts,
                "daily_summary": user_preferences.notification_prefs.daily_summary
            }
        }
    
    def _learn_performance_patterns(
        self,
        trade_history: List[Dict]
    ) -> Dict[str, Any]:
        """성과 기반 패턴 학습"""
        if not trade_history:
            return {
                "profitable_strategies": [],
                "profitable_coins": [],
                "optimal_timeframes": [],
                "risk_adjusted_returns": {}
            }
        
        # 수익성 높은 전략
        strategy_profits = defaultdict(list)
        for trade in trade_history:
            strategy = trade.get("strategy", "")
            profit = trade.get("profit", 0)
            if strategy and profit is not None:
                strategy_profits[strategy].append(profit)
        
        profitable_strategies = []
        for strategy, profits in strategy_profits.items():
            avg_profit = statistics.mean(profits)
            if avg_profit > 0:
                profitable_strategies.append({
                    "strategy": strategy,
                    "avg_profit": round(avg_profit, 2),
                    "win_rate": len([p for p in profits if p > 0]) / len(profits)
                })
        
        profitable_strategies.sort(key=lambda x: x["avg_profit"], reverse=True)
        
        # 수익성 높은 코인
        coin_profits = defaultdict(list)
        for trade in trade_history:
            coin = trade.get("coin", "")
            profit = trade.get("profit", 0)
            if coin and profit is not None:
                coin_profits[coin].append(profit)
        
        profitable_coins = []
        for coin, profits in coin_profits.items():
            avg_profit = statistics.mean(profits)
            if avg_profit > 0:
                profitable_coins.append({
                    "coin": coin,
                    "avg_profit": round(avg_profit, 2),
                    "trade_count": len(profits)
                })
        
        profitable_coins.sort(key=lambda x: x["avg_profit"], reverse=True)
        
        # 최적 시간대
        timeframe_profits = defaultdict(list)
        for trade in trade_history:
            if "timestamp" in trade:
                try:
                    timestamp = datetime.fromisoformat(trade["timestamp"])
                    hour = timestamp.hour
                    profit = trade.get("profit", 0)
                    if profit is not None:
                        timeframe_profits[hour].append(profit)
                except:
                    continue
        
        optimal_timeframes = []
        for hour, profits in timeframe_profits.items():
            avg_profit = statistics.mean(profits)
            optimal_timeframes.append({
                "hour": hour,
                "avg_profit": round(avg_profit, 2),
                "trade_count": len(profits)
            })
        
        optimal_timeframes.sort(key=lambda x: x["avg_profit"], reverse=True)
        
        return {
            "profitable_strategies": profitable_strategies[:5],
            "profitable_coins": profitable_coins[:5],
            "optimal_timeframes": optimal_timeframes[:3],
            "risk_adjusted_returns": self._calculate_risk_adjusted_returns(
                trade_history
            )
        }
    
    def _calculate_risk_adjusted_returns(
        self,
        trade_history: List[Dict]
    ) -> Dict[str, float]:
        """리스크 조정 수익률 계산"""
        if not trade_history:
            return {}
        
        profits = [t.get("profit", 0) for t in trade_history]
        if not profits:
            return {}
        
        avg_return = statistics.mean(profits)
        std_return = statistics.stdev(profits) if len(profits) > 1 else 0
        
        # 샤프 비율 (간단 버전)
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        # 최대 낙폭
        cumulative = 0
        max_drawdown = 0
        peak = 0
        
        for profit in profits:
            cumulative += profit
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "avg_return": round(avg_return, 4),
            "volatility": round(std_return, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 4)
        }
    
    def _learn_feedback_patterns(
        self,
        feedback_history: List[Union[Dict[str, Any], Any]]  # List[Dict] 또는 List[Feedback]
    ) -> Dict[str, Any]:
        """피드백 패턴 학습"""
        if not feedback_history:
            return {
                "satisfaction_score": 0.5,
                "preferred_features": [],
                "disliked_features": [],
                "improvement_suggestions": []
            }
        
        # Feedback 객체를 딕셔너리로 변환
        feedback_dicts = []
        for f in feedback_history:
            if hasattr(f, 'to_dict'):
                # Feedback 객체인 경우
                feedback_dicts.append(f.to_dict())
            elif isinstance(f, dict):
                # 이미 딕셔너리인 경우
                feedback_dicts.append(f)
            else:
                continue
        
        # 만족도 점수
        satisfaction_scores = []
        for f in feedback_dicts:
            content = f.get("content", {})
            # SATISFACTION 타입의 피드백에서 overall_satisfaction 추출
            if f.get("feedback_type") == "satisfaction":
                satisfaction = content.get("overall_satisfaction", 0)
                if satisfaction > 0:
                    satisfaction_scores.append(satisfaction / 5.0)  # 1-5를 0-1로 정규화
        
        avg_satisfaction = (
            statistics.mean(satisfaction_scores)
            if satisfaction_scores
            else 0.5
        )
        
        # 선호 기능
        preferred_features = defaultdict(int)
        disliked_features = defaultdict(int)
        
        for f in feedback_dicts:
            content = f.get("content", {})
            if f.get("feedback_type") == "feature_feedback":
                feature = content.get("feature", "")
                rating = content.get("rating", 0)
                if rating >= 4:
                    preferred_features[feature] += 1
                elif rating <= 2:
                    disliked_features[feature] += 1
        
        # 개선 제안
        improvement_suggestions = [
            f.get("content", {}).get("suggestion", "")
            for f in feedback_dicts
            if f.get("feedback_type") == "improvement" and f.get("content", {}).get("suggestion")
        ]
        
        return {
            "satisfaction_score": round(avg_satisfaction, 2),
            "preferred_features": list(preferred_features.keys())[:5],
            "disliked_features": list(disliked_features.keys())[:5],
            "improvement_suggestions": improvement_suggestions[:5]
        }
    
    def _calculate_model_confidence(
        self,
        behavior_patterns: Dict[str, Any],
        preference_patterns: Dict[str, Any],
        performance_patterns: Dict[str, Any],
        feedback_patterns: Dict[str, Any]
    ) -> float:
        """모델 신뢰도 계산 (0.0 ~ 1.0)"""
        confidence = 0.0
        
        # 행동 데이터 충분성 (최대 0.3)
        behavior_actions = len(behavior_patterns.get("action_preferences", {}))
        confidence += min(behavior_actions / 10, 0.3)
        
        # 선호도 명확성 (최대 0.2)
        if preference_patterns.get("favorite_coins"):
            confidence += min(len(preference_patterns["favorite_coins"]) / 5, 0.1)
        if preference_patterns.get("favorite_strategies"):
            confidence += min(len(preference_patterns["favorite_strategies"]) / 3, 0.1)
        
        # 성과 데이터 (최대 0.3)
        if performance_patterns.get("profitable_strategies"):
            confidence += min(len(performance_patterns["profitable_strategies"]) / 3, 0.15)
        if performance_patterns.get("profitable_coins"):
            confidence += min(len(performance_patterns["profitable_coins"]) / 3, 0.15)
        
        # 피드백 데이터 (최대 0.2)
        if feedback_patterns.get("satisfaction_score", 0) > 0:
            confidence += 0.1
        if feedback_patterns.get("preferred_features"):
            confidence += min(len(feedback_patterns["preferred_features"]) / 3, 0.1)
        
        return min(confidence, 1.0)
    
    def predict_preferences(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상황에 따른 선호도 예측"""
        model = self.user_models.get(user_id)
        if not model:
            return {}
        
        predictions = {}
        
        # 시간대 기반 예측
        current_hour = datetime.now().hour
        time_prefs = model["behavior_patterns"].get("time_preferences", {})
        if current_hour in time_prefs:
            predictions["likely_active"] = True
            predictions["activity_probability"] = time_prefs[current_hour]
        else:
            predictions["likely_active"] = False
            predictions["activity_probability"] = 0.3
        
        # 기능 사용 예측
        feature_usage = model["behavior_patterns"].get("feature_usage", {})
        if feature_usage:
            most_used = max(feature_usage.items(), key=lambda x: x[1])
            predictions["likely_feature"] = most_used[0]
            predictions["feature_confidence"] = most_used[1]
        
        # 전략 선호도 예측
        performance = model["performance_patterns"]
        if performance.get("profitable_strategies"):
            top_strategy = performance["profitable_strategies"][0]
            predictions["recommended_strategy"] = top_strategy["strategy"]
            predictions["strategy_confidence"] = top_strategy["win_rate"]
        
        return predictions
    
    def update_model_weights(
        self,
        user_id: str,
        weights: Dict[str, float]
    ) -> None:
        """모델 가중치 업데이트"""
        if user_id not in self.user_models:
            return
        
        # 가중치 합이 1.0이 되도록 정규화
        total = sum(weights.values())
        if total > 0:
            normalized_weights = {
                k: v / total
                for k, v in weights.items()
            }
            self.user_models[user_id]["weights"] = normalized_weights
            self._save_model(user_id, self.user_models[user_id])
    
    def get_learning_insights(
        self,
        user_id: str
    ) -> List[str]:
        """학습 기반 인사이트 제공"""
        model = self.user_models.get(user_id)
        if not model:
            return ["아직 충분한 데이터가 없습니다. 더 사용해보세요!"]
        
        insights = []
        
        # 행동 패턴 인사이트
        behavior = model["behavior_patterns"]
        top_action = max(
            behavior.get("action_preferences", {}).items(),
            key=lambda x: x[1]
        ) if behavior.get("action_preferences") else None
        
        if top_action:
            insights.append(
                f"주로 '{top_action[0]}' 작업을 자주 수행하십니다"
            )
        
        # 성과 인사이트
        performance = model["performance_patterns"]
        if performance.get("profitable_strategies"):
            top_strategy = performance["profitable_strategies"][0]
            insights.append(
                f"'{top_strategy['strategy']}' 전략에서 "
                f"평균 {top_strategy['avg_profit']:.2f}% 수익을 내고 있습니다"
            )
        
        # 피드백 인사이트
        feedback = model["feedback_patterns"]
        if feedback.get("satisfaction_score", 0) > 0.7:
            insights.append("시스템 만족도가 높습니다!")
        elif feedback.get("satisfaction_score", 0) < 0.4:
            insights.append("개선이 필요한 부분이 있습니다")
        
        # 모델 신뢰도
        confidence = model.get("confidence_score", 0)
        if confidence < 0.3:
            insights.append("더 많은 데이터를 수집하면 더 정확한 개인화가 가능합니다")
        elif confidence > 0.7:
            insights.append("충분한 데이터로 개인화가 잘 이루어지고 있습니다")
        
        return insights
    
    def _save_model(self, user_id: str, model: Dict[str, Any]) -> None:
        """모델 저장"""
        model_file = self.model_dir / f"{user_id}_model.json"
        with open(model_file, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)
    
    def load_model(self, user_id: str) -> Optional[Dict[str, Any]]:
        """모델 로드"""
        if user_id in self.user_models:
            return self.user_models[user_id]
        
        model_file = self.model_dir / f"{user_id}_model.json"
        if not model_file.exists():
            return None
        
        with open(model_file, 'r', encoding='utf-8') as f:
            model = json.load(f)
        
        self.user_models[user_id] = model
        return model

