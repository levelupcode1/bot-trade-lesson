"""
초보자 사용자 프로필
"""

from typing import Dict, Any, List
from .user_profile import (
    UserProfile, UserType, RiskLevel, 
    TradingLimits, FeatureAccess
)


class BeginnerProfile(UserProfile):
    """초보자 프로필 - 안전성과 단순성 중심"""
    
    def __init__(self, user_id: str, investment_amount: float):
        super().__init__(
            user_id=user_id,
            user_type=UserType.BEGINNER,
            risk_level=RiskLevel.CONSERVATIVE,
            investment_amount=investment_amount
        )
    
    def _init_trading_limits(self) -> TradingLimits:
        """보수적인 거래 제한"""
        return TradingLimits(
            max_position_size=0.15,      # 15% 최대
            min_cash_ratio=0.50,         # 50% 현금 유지
            daily_trade_limit=3,         # 하루 3회
            stop_loss=-0.03,             # -3% 손절 (필수)
            take_profit=0.05,            # 5% 익절
            daily_loss_limit=-0.05,      # -5% 일일 손실 한도
            max_concurrent_positions=1   # 동시 1개 포지션
        )
    
    def _init_feature_access(self) -> FeatureAccess:
        """기본 기능만 접근 가능"""
        return FeatureAccess(
            basic_trading=True,
            custom_strategies=False,
            advanced_analytics=False,
            api_access=False,
            ml_models=False,
            multi_exchange=False,
            portfolio_management=False,
            backtesting=True,           # 백테스트는 가능
            paper_trading=True          # 모의 거래 권장
        )
    
    def _init_allowed_strategies(self) -> List[str]:
        """기본 전략만 허용"""
        return [
            "volatility_breakout_conservative",  # 보수적 변동성 돌파
            "ma_crossover_long",                 # 장기 이동평균 교차
        ]
    
    def _init_allowed_coins(self) -> List[str]:
        """메이저 코인만 허용"""
        return [
            "KRW-BTC",   # 비트코인
            "KRW-ETH",   # 이더리움
        ]
    
    def _init_ui_settings(self) -> Dict[str, Any]:
        """단순하고 직관적인 UI"""
        return {
            "complexity_level": "simple",
            "layout": "single_column",
            "show_tooltips": True,
            "show_explanations": True,
            "tutorial_mode": True,
            "safe_mode": True,
            "color_scheme": "beginner_friendly",
            "font_size": "large",
            "show_advanced_features": False,
            "dashboard_widgets": [
                "account_summary",
                "current_position",
                "recent_trades",
                "simple_settings"
            ]
        }
    
    def _init_notification_settings(self) -> Dict[str, Any]:
        """모든 거래 알림"""
        return {
            "all_trades": True,
            "daily_summary": True,
            "risk_alerts": True,
            "educational_tips": True,
            "market_news": False,
            "strategy_signals": False,
            "notification_frequency": "high",
            "notification_channels": ["telegram"],
            "alert_sounds": True
        }

