"""
중급자 사용자 프로필
"""

from typing import Dict, Any, List
from .user_profile import (
    UserProfile, UserType, RiskLevel,
    TradingLimits, FeatureAccess
)


class IntermediateProfile(UserProfile):
    """중급자 프로필 - 균형잡힌 접근"""
    
    def __init__(self, user_id: str, investment_amount: float):
        super().__init__(
            user_id=user_id,
            user_type=UserType.INTERMEDIATE,
            risk_level=RiskLevel.MODERATE,
            investment_amount=investment_amount
        )
    
    def _init_trading_limits(self) -> TradingLimits:
        """균형잡힌 거래 제한"""
        return TradingLimits(
            max_position_size=0.30,      # 30% 최대
            min_cash_ratio=0.30,         # 30% 현금 유지
            daily_trade_limit=10,        # 하루 10회
            stop_loss=-0.07,             # -7% 손절 (조정 가능)
            take_profit=0.10,            # 10% 익절
            daily_loss_limit=-0.10,      # -10% 일일 손실 한도
            max_concurrent_positions=5   # 동시 5개 포지션
        )
    
    def _init_feature_access(self) -> FeatureAccess:
        """고급 기능 일부 접근 가능"""
        return FeatureAccess(
            basic_trading=True,
            custom_strategies=True,      # 커스텀 전략 가능
            advanced_analytics=True,     # 고급 분석 가능
            api_access=False,
            ml_models=False,
            multi_exchange=False,
            portfolio_management=True,   # 포트폴리오 관리 가능
            backtesting=True,
            paper_trading=True
        )
    
    def _init_allowed_strategies(self) -> List[str]:
        """다양한 전략 허용"""
        return [
            "volatility_breakout",
            "volatility_breakout_conservative",
            "ma_crossover",
            "ma_crossover_long",
            "rsi_strategy",
            "multi_strategy",            # 다중 전략
            "portfolio_strategy",        # 포트폴리오 전략
        ]
    
    def _init_allowed_coins(self) -> List[str]:
        """메이저 + 중형 코인 허용"""
        return [
            # 메이저 (TOP 10)
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA",
            "KRW-SOL", "KRW-DOT", "KRW-AVAX", "KRW-MATIC",
            # 중형 (TOP 11-30)
            "KRW-ATOM", "KRW-LINK", "KRW-ALGO", "KRW-NEAR",
            "KRW-APT", "KRW-OP", "KRW-ARB",
        ]
    
    def _init_ui_settings(self) -> Dict[str, Any]:
        """다기능 UI"""
        return {
            "complexity_level": "intermediate",
            "layout": "multi_column",
            "show_tooltips": True,
            "show_explanations": False,
            "tutorial_mode": False,
            "safe_mode": False,
            "color_scheme": "professional",
            "font_size": "medium",
            "show_advanced_features": True,
            "dashboard_widgets": [
                "account_summary",
                "portfolio_overview",
                "performance_chart",
                "active_strategies",
                "recent_trades",
                "market_analysis",
                "advanced_settings"
            ],
            "enable_custom_layout": True,
            "show_technical_indicators": True
        }
    
    def _init_notification_settings(self) -> Dict[str, Any]:
        """선택적 알림"""
        return {
            "all_trades": False,
            "significant_trades": True,   # 중요 거래만
            "daily_summary": True,
            "weekly_report": True,
            "risk_alerts": True,
            "educational_tips": False,
            "market_news": True,
            "strategy_signals": True,
            "notification_frequency": "medium",
            "notification_channels": ["telegram", "email"],
            "alert_sounds": False,
            "custom_alerts": True
        }

