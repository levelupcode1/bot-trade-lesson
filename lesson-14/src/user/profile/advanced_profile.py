"""
고급자 사용자 프로필
"""

from typing import Dict, Any, List
from .user_profile import (
    UserProfile, UserType, RiskLevel,
    TradingLimits, FeatureAccess
)


class AdvancedProfile(UserProfile):
    """고급자 프로필 - 완전한 제어와 커스터마이징"""
    
    def __init__(self, user_id: str, investment_amount: float):
        super().__init__(
            user_id=user_id,
            user_type=UserType.ADVANCED,
            risk_level=RiskLevel.AGGRESSIVE,
            investment_amount=investment_amount
        )
    
    def _init_trading_limits(self) -> TradingLimits:
        """유연한 거래 제한 (사용자 정의 가능)"""
        return TradingLimits(
            max_position_size=0.80,      # 80% 최대 (사용자 정의 가능)
            min_cash_ratio=0.10,         # 10% 현금 유지
            daily_trade_limit=9999,      # 무제한
            stop_loss=-0.15,             # -15% (사용자 정의)
            take_profit=0.20,            # 20% (사용자 정의)
            daily_loss_limit=-0.20,      # -20% 일일 손실 한도
            max_concurrent_positions=999 # 무제한
        )
    
    def _init_feature_access(self) -> FeatureAccess:
        """모든 기능 접근 가능"""
        return FeatureAccess(
            basic_trading=True,
            custom_strategies=True,
            advanced_analytics=True,
            api_access=True,             # API 직접 접근
            ml_models=True,              # ML 모델 사용
            multi_exchange=True,         # 다중 거래소 (향후)
            portfolio_management=True,
            backtesting=True,
            paper_trading=True
        )
    
    def _init_allowed_strategies(self) -> List[str]:
        """모든 전략 + 커스텀 허용"""
        return ["*"]  # 모든 전략
    
    def _init_allowed_coins(self) -> List[str]:
        """모든 코인 허용"""
        return ["*"]  # 모든 KRW 마켓
    
    def _init_ui_settings(self) -> Dict[str, Any]:
        """전문가용 UI"""
        return {
            "complexity_level": "expert",
            "layout": "professional_multi_monitor",
            "show_tooltips": False,
            "show_explanations": False,
            "tutorial_mode": False,
            "safe_mode": False,
            "color_scheme": "dark_professional",
            "font_size": "small",
            "show_advanced_features": True,
            "dashboard_widgets": [
                "account_summary",
                "portfolio_overview",
                "performance_chart",
                "active_strategies",
                "order_book",
                "market_depth",
                "technical_analysis",
                "risk_metrics",
                "code_editor",
                "terminal",
                "api_console",
                "ml_dashboard",
                "custom_widgets"
            ],
            "enable_custom_layout": True,
            "enable_code_editor": True,
            "enable_terminal": True,
            "show_technical_indicators": True,
            "show_advanced_charts": True,
            "multi_monitor_support": True,
            "real_time_analytics": True
        }
    
    def _init_notification_settings(self) -> Dict[str, Any]:
        """최소한의 알림 (중요만)"""
        return {
            "all_trades": False,
            "significant_trades": False,
            "daily_summary": False,
            "weekly_report": True,
            "risk_alerts": True,         # 중요 리스크만
            "educational_tips": False,
            "market_news": False,
            "strategy_signals": False,
            "notification_frequency": "low",
            "notification_channels": ["api_webhook", "email"],
            "alert_sounds": False,
            "custom_alerts": True,
            "api_webhooks": True,
            "critical_only": True
        }
    
    def can_modify_limits(self) -> bool:
        """거래 제한 수정 가능 여부"""
        return True
    
    def can_access_raw_api(self) -> bool:
        """Raw API 접근 가능 여부"""
        return True

