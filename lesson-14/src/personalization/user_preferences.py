"""
사용자 선호도 관리 시스템
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pathlib import Path
from enum import Enum


class InvestmentGoal(Enum):
    """투자 목표"""
    CAPITAL_PRESERVATION = "capital_preservation"  # 자본 보존
    INCOME_GENERATION = "income_generation"        # 수익 창출
    GROWTH = "growth"                              # 성장
    AGGRESSIVE_GROWTH = "aggressive_growth"        # 공격적 성장


class RiskTolerance(Enum):
    """리스크 허용도"""
    VERY_LOW = "very_low"      # 매우 낮음
    LOW = "low"                # 낮음
    MODERATE = "moderate"      # 보통
    HIGH = "high"              # 높음
    VERY_HIGH = "very_high"    # 매우 높음


class TradingStyle(Enum):
    """거래 스타일"""
    CONSERVATIVE = "conservative"    # 보수적
    BALANCED = "balanced"            # 균형
    AGGRESSIVE = "aggressive"        # 공격적
    DAY_TRADER = "day_trader"       # 데이 트레이더
    SWING_TRADER = "swing_trader"   # 스윙 트레이더
    LONG_TERM = "long_term"         # 장기 투자


@dataclass
class InvestmentProfile:
    """투자 성향 프로필"""
    goal: InvestmentGoal
    risk_tolerance: RiskTolerance
    trading_style: TradingStyle
    target_return: float          # 목표 수익률 (월간 %)
    max_drawdown: float          # 최대 허용 낙폭 (%)
    investment_horizon: int      # 투자 기간 (개월)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal.value,
            "risk_tolerance": self.risk_tolerance.value,
            "trading_style": self.trading_style.value,
            "target_return": self.target_return,
            "max_drawdown": self.max_drawdown,
            "investment_horizon": self.investment_horizon
        }


@dataclass
class DashboardPreferences:
    """대시보드 선호도"""
    layout: str = "grid"                           # grid, list, custom
    theme: str = "dark"                            # dark, light, auto
    language: str = "ko"                           # ko, en
    
    # 위젯 설정
    enabled_widgets: List[str] = field(default_factory=list)
    widget_order: List[str] = field(default_factory=list)
    widget_sizes: Dict[str, str] = field(default_factory=dict)  # small, medium, large
    
    # 차트 설정
    default_chart_type: str = "candlestick"       # candlestick, line, area
    chart_timeframe: str = "1d"                   # 1m, 5m, 15m, 1h, 4h, 1d
    chart_indicators: List[str] = field(default_factory=list)
    
    # 표시 설정
    show_portfolio_value: bool = True
    show_profit_loss: bool = True
    show_recent_trades: bool = True
    show_market_news: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationPreferences:
    """알림 선호도"""
    # 알림 채널
    telegram_enabled: bool = True
    email_enabled: bool = False
    push_enabled: bool = False
    
    # 알림 유형
    trade_notifications: bool = True
    price_alerts: bool = True
    news_alerts: bool = False
    performance_reports: bool = True
    
    # 알림 빈도
    immediate_alerts: bool = True      # 즉시 알림
    daily_summary: bool = True         # 일일 요약
    weekly_report: bool = True         # 주간 리포트
    monthly_report: bool = False       # 월간 리포트
    
    # 알림 조건
    min_price_change: float = 0.05     # 최소 가격 변동 (5%)
    min_profit_loss: float = 0.02      # 최소 손익 (2%)
    
    # 알림 시간대
    quiet_hours_start: Optional[int] = 22  # 22시
    quiet_hours_end: Optional[int] = 8     # 8시
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradingPreferences:
    """거래 선호도"""
    # 선호 코인
    favorite_coins: List[str] = field(default_factory=list)
    blacklist_coins: List[str] = field(default_factory=list)
    
    # 선호 전략
    favorite_strategies: List[str] = field(default_factory=list)
    
    # 거래 시간대
    preferred_trading_hours: List[int] = field(default_factory=list)  # 0-23
    avoid_trading_hours: List[int] = field(default_factory=list)
    
    # 자동화 설정
    auto_trading: bool = False
    auto_rebalance: bool = False
    auto_stop_loss: bool = True
    auto_take_profit: bool = True
    
    # 거래 스타일 설정
    prefer_quick_trades: bool = False   # 빠른 거래 선호
    prefer_stable_coins: bool = True    # 안정적인 코인 선호
    diversification_level: int = 3      # 분산 투자 수준 (1-5)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningPreferences:
    """학습 및 교육 선호도"""
    # 학습 레벨
    learning_level: str = "beginner"    # beginner, intermediate, advanced
    
    # 관심 주제
    interested_topics: List[str] = field(default_factory=list)
    # 예: technical_analysis, fundamental_analysis, risk_management, trading_psychology
    
    # 콘텐츠 선호도
    prefer_video: bool = True
    prefer_article: bool = True
    prefer_interactive: bool = False
    
    # 학습 목표
    learning_goals: List[str] = field(default_factory=list)
    completed_courses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UserPreferences:
    """사용자 선호도 종합 관리"""
    
    def __init__(
        self,
        user_id: str,
        investment_profile: Optional[InvestmentProfile] = None,
        dashboard_prefs: Optional[DashboardPreferences] = None,
        notification_prefs: Optional[NotificationPreferences] = None,
        trading_prefs: Optional[TradingPreferences] = None,
        learning_prefs: Optional[LearningPreferences] = None
    ):
        self.user_id = user_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 각 선호도 초기화
        self.investment_profile = investment_profile or self._default_investment_profile()
        self.dashboard_prefs = dashboard_prefs or DashboardPreferences()
        self.notification_prefs = notification_prefs or NotificationPreferences()
        self.trading_prefs = trading_prefs or TradingPreferences()
        self.learning_prefs = learning_prefs or LearningPreferences()
        
        # 행동 데이터
        self.behavior_history: List[Dict] = []
        self.preference_score: float = 0.0  # 선호도 신뢰도 점수
    
    def _default_investment_profile(self) -> InvestmentProfile:
        """기본 투자 프로필"""
        return InvestmentProfile(
            goal=InvestmentGoal.CAPITAL_PRESERVATION,
            risk_tolerance=RiskTolerance.LOW,
            trading_style=TradingStyle.CONSERVATIVE,
            target_return=5.0,
            max_drawdown=-10.0,
            investment_horizon=12
        )
    
    def update_investment_profile(self, **kwargs) -> None:
        """투자 프로필 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.investment_profile, key):
                setattr(self.investment_profile, key, value)
        self.updated_at = datetime.now()
    
    def update_dashboard_prefs(self, **kwargs) -> None:
        """대시보드 선호도 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.dashboard_prefs, key):
                setattr(self.dashboard_prefs, key, value)
        self.updated_at = datetime.now()
    
    def add_favorite_coin(self, coin: str) -> None:
        """선호 코인 추가"""
        if coin not in self.trading_prefs.favorite_coins:
            self.trading_prefs.favorite_coins.append(coin)
            self.updated_at = datetime.now()
    
    def remove_favorite_coin(self, coin: str) -> None:
        """선호 코인 제거"""
        if coin in self.trading_prefs.favorite_coins:
            self.trading_prefs.favorite_coins.remove(coin)
            self.updated_at = datetime.now()
    
    def add_favorite_strategy(self, strategy: str) -> None:
        """선호 전략 추가"""
        if strategy not in self.trading_prefs.favorite_strategies:
            self.trading_prefs.favorite_strategies.append(strategy)
            self.updated_at = datetime.now()
    
    def record_behavior(self, action: str, context: Dict[str, Any]) -> None:
        """사용자 행동 기록"""
        behavior = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context": context
        }
        self.behavior_history.append(behavior)
        
        # 최근 1000개만 유지
        if len(self.behavior_history) > 1000:
            self.behavior_history = self.behavior_history[-1000:]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "investment_profile": self.investment_profile.to_dict(),
            "dashboard_prefs": self.dashboard_prefs.to_dict(),
            "notification_prefs": self.notification_prefs.to_dict(),
            "trading_prefs": self.trading_prefs.to_dict(),
            "learning_prefs": self.learning_prefs.to_dict(),
            "behavior_history": self.behavior_history[-100:],  # 최근 100개만
            "preference_score": self.preference_score
        }


class PreferenceManager:
    """선호도 관리자"""
    
    def __init__(self, preferences_dir: str = "data/user_preferences"):
        self.preferences_dir = Path(preferences_dir)
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, UserPreferences] = {}
    
    def create_preferences(
        self,
        user_id: str,
        **kwargs
    ) -> UserPreferences:
        """새 선호도 생성"""
        preferences = UserPreferences(user_id, **kwargs)
        self.save_preferences(preferences)
        self._cache[user_id] = preferences
        return preferences
    
    def load_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """선호도 로드"""
        # 캐시 확인
        if user_id in self._cache:
            return self._cache[user_id]
        
        # 파일에서 로드
        prefs_file = self.preferences_dir / f"{user_id}_preferences.json"
        if not prefs_file.exists():
            return None
        
        with open(prefs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 객체 재구성
        preferences = self._from_dict(data)
        self._cache[user_id] = preferences
        return preferences
    
    def save_preferences(self, preferences: UserPreferences) -> None:
        """선호도 저장"""
        prefs_file = self.preferences_dir / f"{preferences.user_id}_preferences.json"
        
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(preferences.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 캐시 업데이트
        self._cache[preferences.user_id] = preferences
    
    def update_preferences(
        self,
        user_id: str,
        section: str,
        **updates
    ) -> Optional[UserPreferences]:
        """선호도 업데이트"""
        preferences = self.load_preferences(user_id)
        if not preferences:
            return None
        
        # 섹션별 업데이트
        if section == "investment":
            preferences.update_investment_profile(**updates)
        elif section == "dashboard":
            preferences.update_dashboard_prefs(**updates)
        elif section == "notification":
            for key, value in updates.items():
                if hasattr(preferences.notification_prefs, key):
                    setattr(preferences.notification_prefs, key, value)
        elif section == "trading":
            for key, value in updates.items():
                if hasattr(preferences.trading_prefs, key):
                    setattr(preferences.trading_prefs, key, value)
        elif section == "learning":
            for key, value in updates.items():
                if hasattr(preferences.learning_prefs, key):
                    setattr(preferences.learning_prefs, key, value)
        
        preferences.updated_at = datetime.now()
        self.save_preferences(preferences)
        return preferences
    
    def _from_dict(self, data: Dict[str, Any]) -> UserPreferences:
        """딕셔너리에서 객체 재구성"""
        # 투자 프로필
        inv_data = data["investment_profile"]
        investment_profile = InvestmentProfile(
            goal=InvestmentGoal(inv_data["goal"]),
            risk_tolerance=RiskTolerance(inv_data["risk_tolerance"]),
            trading_style=TradingStyle(inv_data["trading_style"]),
            target_return=inv_data["target_return"],
            max_drawdown=inv_data["max_drawdown"],
            investment_horizon=inv_data["investment_horizon"]
        )
        
        # 대시보드 선호도
        dashboard_prefs = DashboardPreferences(**data["dashboard_prefs"])
        
        # 알림 선호도
        notification_prefs = NotificationPreferences(**data["notification_prefs"])
        
        # 거래 선호도
        trading_prefs = TradingPreferences(**data["trading_prefs"])
        
        # 학습 선호도
        learning_prefs = LearningPreferences(**data["learning_prefs"])
        
        # UserPreferences 객체 생성
        preferences = UserPreferences(
            user_id=data["user_id"],
            investment_profile=investment_profile,
            dashboard_prefs=dashboard_prefs,
            notification_prefs=notification_prefs,
            trading_prefs=trading_prefs,
            learning_prefs=learning_prefs
        )
        
        preferences.behavior_history = data.get("behavior_history", [])
        preferences.preference_score = data.get("preference_score", 0.0)
        preferences.created_at = datetime.fromisoformat(data["created_at"])
        preferences.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return preferences
    
    def analyze_preferences(self, user_id: str) -> Dict[str, Any]:
        """선호도 분석"""
        preferences = self.load_preferences(user_id)
        if not preferences:
            return {}
        
        analysis = {
            "risk_level": preferences.investment_profile.risk_tolerance.value,
            "trading_activity": len(preferences.behavior_history),
            "favorite_coins_count": len(preferences.trading_prefs.favorite_coins),
            "favorite_strategies_count": len(preferences.trading_prefs.favorite_strategies),
            "dashboard_customization": len(preferences.dashboard_prefs.enabled_widgets),
            "notification_engagement": preferences.notification_prefs.trade_notifications,
            "learning_engagement": len(preferences.learning_prefs.completed_courses),
            "preference_maturity": preferences.preference_score
        }
        
        return analysis


