"""
사용자 행동 분석 시스템
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

from .user_preferences import UserPreferences


class BehaviorAnalyzer:
    """사용자 행동 분석기"""
    
    def __init__(self):
        self.analysis_cache: Dict[str, Dict] = {}
    
    def analyze_user_behavior(
        self,
        user_preferences: UserPreferences,
        trade_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """종합 행동 분석"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_preferences.user_id,
            "behavior_patterns": self._analyze_behavior_patterns(
                user_preferences.behavior_history
            ),
            "trading_patterns": self._analyze_trading_patterns(trade_history or []),
            "engagement_metrics": self._calculate_engagement_metrics(
                user_preferences
            ),
            "preferences_evolution": self._track_preferences_evolution(
                user_preferences
            )
        }
        
        # 캐시 저장
        self.analysis_cache[user_preferences.user_id] = analysis
        
        return analysis
    
    def _analyze_behavior_patterns(
        self,
        behavior_history: List[Dict]
    ) -> Dict[str, Any]:
        """행동 패턴 분석"""
        if not behavior_history:
            return {
                "total_actions": 0,
                "action_frequency": {},
                "active_hours": [],
                "session_patterns": {}
            }
        
        # 액션 빈도 분석
        actions = [b["action"] for b in behavior_history]
        action_frequency = dict(Counter(actions))
        
        # 활동 시간대 분석
        active_hours = self._analyze_active_hours(behavior_history)
        
        # 세션 패턴 분석
        session_patterns = self._analyze_sessions(behavior_history)
        
        return {
            "total_actions": len(behavior_history),
            "action_frequency": action_frequency,
            "active_hours": active_hours,
            "session_patterns": session_patterns,
            "most_common_action": max(action_frequency.items(), key=lambda x: x[1])[0] if action_frequency else None
        }
    
    def _analyze_active_hours(
        self,
        behavior_history: List[Dict]
    ) -> List[int]:
        """활동 시간대 분석"""
        hours = []
        
        for behavior in behavior_history:
            try:
                timestamp = datetime.fromisoformat(behavior["timestamp"])
                hours.append(timestamp.hour)
            except:
                continue
        
        if not hours:
            return []
        
        # 가장 활동적인 시간대 TOP 3
        hour_counts = Counter(hours)
        top_hours = [h for h, _ in hour_counts.most_common(3)]
        
        return sorted(top_hours)
    
    def _analyze_sessions(
        self,
        behavior_history: List[Dict]
    ) -> Dict[str, Any]:
        """세션 패턴 분석"""
        if not behavior_history:
            return {
                "avg_session_length": 0,
                "sessions_per_day": 0,
                "actions_per_session": 0
            }
        
        # 세션 구분 (30분 이상 간격이면 새 세션)
        sessions = []
        current_session = []
        session_threshold = timedelta(minutes=30)
        
        sorted_history = sorted(
            behavior_history,
            key=lambda x: x["timestamp"]
        )
        
        last_timestamp = None
        
        for behavior in sorted_history:
            try:
                timestamp = datetime.fromisoformat(behavior["timestamp"])
                
                if last_timestamp and (timestamp - last_timestamp) > session_threshold:
                    if current_session:
                        sessions.append(current_session)
                    current_session = []
                
                current_session.append(behavior)
                last_timestamp = timestamp
            except:
                continue
        
        if current_session:
            sessions.append(current_session)
        
        # 세션 통계
        if sessions:
            session_lengths = []
            for session in sessions:
                if len(session) > 1:
                    start = datetime.fromisoformat(session[0]["timestamp"])
                    end = datetime.fromisoformat(session[-1]["timestamp"])
                    session_lengths.append((end - start).total_seconds() / 60)
            
            avg_session_length = statistics.mean(session_lengths) if session_lengths else 0
            actions_per_session = statistics.mean([len(s) for s in sessions])
            
            # 일별 세션 수
            dates = [
                datetime.fromisoformat(b["timestamp"]).date()
                for session in sessions
                for b in session
            ]
            unique_dates = len(set(dates))
            sessions_per_day = len(sessions) / unique_dates if unique_dates > 0 else 0
        else:
            avg_session_length = 0
            sessions_per_day = 0
            actions_per_session = 0
        
        return {
            "total_sessions": len(sessions),
            "avg_session_length": round(avg_session_length, 2),
            "sessions_per_day": round(sessions_per_day, 2),
            "actions_per_session": round(actions_per_session, 2)
        }
    
    def _analyze_trading_patterns(
        self,
        trade_history: List[Dict]
    ) -> Dict[str, Any]:
        """거래 패턴 분석"""
        if not trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "favorite_coins": [],
                "preferred_timeframes": []
            }
        
        # 승률 계산
        winning_trades = [t for t in trade_history if t.get("profit", 0) > 0]
        win_rate = len(winning_trades) / len(trade_history) if trade_history else 0
        
        # 평균 수익
        profits = [t.get("profit", 0) for t in trade_history]
        avg_profit = statistics.mean(profits) if profits else 0
        
        # 선호 코인 분석
        coins = [t.get("coin") for t in trade_history if t.get("coin")]
        favorite_coins = [coin for coin, _ in Counter(coins).most_common(3)]
        
        # 거래 시간대 분석
        hours = []
        for trade in trade_history:
            if "timestamp" in trade:
                try:
                    timestamp = datetime.fromisoformat(trade["timestamp"])
                    hours.append(timestamp.hour)
                except:
                    continue
        
        preferred_timeframes = list(set(hours))[:5]
        
        return {
            "total_trades": len(trade_history),
            "win_rate": round(win_rate * 100, 2),
            "avg_profit": round(avg_profit, 2),
            "favorite_coins": favorite_coins,
            "preferred_timeframes": sorted(preferred_timeframes),
            "most_profitable_coin": self._find_most_profitable_coin(trade_history)
        }
    
    def _find_most_profitable_coin(
        self,
        trade_history: List[Dict]
    ) -> Optional[str]:
        """가장 수익성 높은 코인 찾기"""
        coin_profits = defaultdict(list)
        
        for trade in trade_history:
            coin = trade.get("coin")
            profit = trade.get("profit", 0)
            if coin and profit is not None:
                coin_profits[coin].append(profit)
        
        if not coin_profits:
            return None
        
        # 평균 수익이 가장 높은 코인
        avg_profits = {
            coin: statistics.mean(profits)
            for coin, profits in coin_profits.items()
        }
        
        return max(avg_profits.items(), key=lambda x: x[1])[0]
    
    def _calculate_engagement_metrics(
        self,
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """참여도 메트릭 계산"""
        # 기간 계산
        days_since_creation = (
            datetime.now() - user_preferences.created_at
        ).days
        
        # 활동 빈도
        activity_frequency = len(user_preferences.behavior_history) / max(days_since_creation, 1)
        
        # 설정 완성도
        config_completeness = self._calculate_config_completeness(user_preferences)
        
        # 학습 진행도
        learning_progress = len(user_preferences.learning_prefs.completed_courses)
        
        # 선호도 설정 점수
        preference_score = self._calculate_preference_score(user_preferences)
        
        return {
            "days_active": days_since_creation,
            "activity_frequency": round(activity_frequency, 2),
            "config_completeness": round(config_completeness, 2),
            "learning_progress": learning_progress,
            "preference_score": round(preference_score, 2),
            "engagement_level": self._determine_engagement_level(
                activity_frequency,
                config_completeness,
                learning_progress
            )
        }
    
    def _calculate_config_completeness(
        self,
        user_preferences: UserPreferences
    ) -> float:
        """설정 완성도 계산 (0-100)"""
        score = 0
        max_score = 100
        
        # 투자 프로필 설정 (30점)
        if user_preferences.investment_profile.target_return > 0:
            score += 30
        
        # 대시보드 커스터마이징 (20점)
        if user_preferences.dashboard_prefs.enabled_widgets:
            score += 20
        
        # 알림 설정 (15점)
        if user_preferences.notification_prefs.telegram_enabled:
            score += 15
        
        # 거래 선호도 (20점)
        if user_preferences.trading_prefs.favorite_coins:
            score += 10
        if user_preferences.trading_prefs.favorite_strategies:
            score += 10
        
        # 학습 선호도 (15점)
        if user_preferences.learning_prefs.interested_topics:
            score += 15
        
        return min(score, max_score)
    
    def _calculate_preference_score(
        self,
        user_preferences: UserPreferences
    ) -> float:
        """선호도 점수 계산 (0-100)"""
        score = 0
        
        # 행동 데이터 충분성 (최대 40점)
        behavior_count = len(user_preferences.behavior_history)
        score += min(behavior_count / 10, 40)
        
        # 선호도 명확성 (최대 30점)
        if user_preferences.trading_prefs.favorite_coins:
            score += min(len(user_preferences.trading_prefs.favorite_coins) * 5, 15)
        if user_preferences.trading_prefs.favorite_strategies:
            score += min(len(user_preferences.trading_prefs.favorite_strategies) * 5, 15)
        
        # 활동 일관성 (최대 30점)
        days_active = (datetime.now() - user_preferences.created_at).days
        if days_active > 0:
            consistency = min(behavior_count / days_active, 5) * 6
            score += consistency
        
        return min(score, 100)
    
    def _determine_engagement_level(
        self,
        activity_frequency: float,
        config_completeness: float,
        learning_progress: int
    ) -> str:
        """참여도 레벨 결정"""
        total_score = (
            activity_frequency * 10 +
            config_completeness +
            learning_progress * 10
        )
        
        if total_score >= 80:
            return "매우 높음"
        elif total_score >= 60:
            return "높음"
        elif total_score >= 40:
            return "보통"
        elif total_score >= 20:
            return "낮음"
        else:
            return "매우 낮음"
    
    def _track_preferences_evolution(
        self,
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """선호도 변화 추적"""
        # 실제로는 과거 데이터와 비교
        return {
            "risk_tolerance_trend": "안정",  # 증가, 감소, 안정
            "activity_trend": "증가",
            "learning_trend": "증가",
            "customization_trend": "안정"
        }
    
    def get_behavioral_insights(
        self,
        user_id: str
    ) -> List[str]:
        """행동 기반 인사이트 제공"""
        if user_id not in self.analysis_cache:
            return []
        
        analysis = self.analysis_cache[user_id]
        insights = []
        
        # 활동 시간대 인사이트
        active_hours = analysis["behavior_patterns"]["active_hours"]
        if active_hours:
            insights.append(
                f"주로 {', '.join(map(str, active_hours))}시에 활동하십니다"
            )
        
        # 거래 패턴 인사이트
        trading = analysis["trading_patterns"]
        if trading["win_rate"] > 60:
            insights.append(f"우수한 승률 {trading['win_rate']}%를 유지하고 있습니다")
        
        if trading["favorite_coins"]:
            insights.append(
                f"{', '.join(trading['favorite_coins'])} 코인을 주로 거래합니다"
            )
        
        # 참여도 인사이트
        engagement = analysis["engagement_metrics"]
        if engagement["engagement_level"] == "매우 높음":
            insights.append("매우 활발하게 시스템을 사용하고 계십니다")
        elif engagement["engagement_level"] == "낮음":
            insights.append("더 자주 시스템을 활용해보세요")
        
        return insights
    
    def predict_user_needs(
        self,
        user_preferences: UserPreferences,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """사용자 니즈 예측"""
        needs = []
        
        # 학습 니즈
        if analysis["engagement_metrics"]["learning_progress"] == 0:
            needs.append("교육 콘텐츠")
        
        # 다각화 니즈
        favorite_coins = len(user_preferences.trading_prefs.favorite_coins)
        if favorite_coins < 3:
            needs.append("포트폴리오 다각화")
        
        # 자동화 니즈
        if not user_preferences.trading_prefs.auto_trading:
            if analysis["trading_patterns"]["total_trades"] > 50:
                needs.append("거래 자동화")
        
        # 고급 기능 니즈
        if (analysis["engagement_metrics"]["engagement_level"] == "매우 높음" and
            user_preferences.learning_prefs.learning_level == "beginner"):
            needs.append("레벨 업그레이드")
        
        return needs


