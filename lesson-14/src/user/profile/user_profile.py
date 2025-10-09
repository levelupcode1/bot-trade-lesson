"""
사용자 프로필 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class UserType(Enum):
    """사용자 유형"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class RiskLevel(Enum):
    """리스크 레벨"""
    CONSERVATIVE = "conservative"  # 보수적
    MODERATE = "moderate"          # 중간
    AGGRESSIVE = "aggressive"      # 공격적


@dataclass
class TradingLimits:
    """거래 제한 설정"""
    max_position_size: float        # 최대 포지션 크기 (%)
    min_cash_ratio: float           # 최소 현금 비율 (%)
    daily_trade_limit: int          # 일일 최대 거래 횟수
    stop_loss: float                # 손절 비율
    take_profit: float              # 익절 비율
    daily_loss_limit: float         # 일일 최대 손실 (%)
    max_concurrent_positions: int   # 최대 동시 포지션 수


@dataclass
class FeatureAccess:
    """기능 접근 권한"""
    basic_trading: bool = True
    custom_strategies: bool = False
    advanced_analytics: bool = False
    api_access: bool = False
    ml_models: bool = False
    multi_exchange: bool = False
    portfolio_management: bool = False
    backtesting: bool = True
    paper_trading: bool = True


class UserProfile(ABC):
    """사용자 프로필 추상 베이스 클래스"""
    
    def __init__(
        self,
        user_id: str,
        user_type: UserType,
        risk_level: RiskLevel,
        investment_amount: float
    ):
        self.user_id = user_id
        self.user_type = user_type
        self.risk_level = risk_level
        self.investment_amount = investment_amount
        
        # 프로필별 설정 초기화
        self.trading_limits = self._init_trading_limits()
        self.feature_access = self._init_feature_access()
        self.allowed_strategies = self._init_allowed_strategies()
        self.allowed_coins = self._init_allowed_coins()
        self.ui_settings = self._init_ui_settings()
        self.notification_settings = self._init_notification_settings()
    
    @abstractmethod
    def _init_trading_limits(self) -> TradingLimits:
        """거래 제한 초기화"""
        pass
    
    @abstractmethod
    def _init_feature_access(self) -> FeatureAccess:
        """기능 접근 권한 초기화"""
        pass
    
    @abstractmethod
    def _init_allowed_strategies(self) -> List[str]:
        """허용된 전략 목록 초기화"""
        pass
    
    @abstractmethod
    def _init_allowed_coins(self) -> List[str]:
        """허용된 코인 목록 초기화"""
        pass
    
    @abstractmethod
    def _init_ui_settings(self) -> Dict[str, Any]:
        """UI 설정 초기화"""
        pass
    
    @abstractmethod
    def _init_notification_settings(self) -> Dict[str, Any]:
        """알림 설정 초기화"""
        pass
    
    def can_perform_action(self, action: str) -> bool:
        """특정 동작 수행 가능 여부 확인"""
        action_map = {
            "place_order": True,
            "create_strategy": self.feature_access.custom_strategies,
            "access_api": self.feature_access.api_access,
            "use_ml": self.feature_access.ml_models,
            "advanced_analytics": self.feature_access.advanced_analytics,
        }
        return action_map.get(action, False)
    
    def validate_trade(self, trade_info: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """거래 유효성 검증"""
        # 포지션 크기 검증
        position_size = trade_info.get("position_size", 0)
        if position_size > self.trading_limits.max_position_size:
            return False, f"포지션 크기가 제한({self.trading_limits.max_position_size}%)을 초과합니다"
        
        # 코인 검증
        coin = trade_info.get("coin", "")
        if "*" not in self.allowed_coins and coin not in self.allowed_coins:
            return False, f"{coin}은(는) 거래 허용 목록에 없습니다"
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """프로필을 딕셔너리로 변환"""
        return {
            "user_id": self.user_id,
            "user_type": self.user_type.value,
            "risk_level": self.risk_level.value,
            "investment_amount": self.investment_amount,
            "trading_limits": self.trading_limits.__dict__,
            "feature_access": self.feature_access.__dict__,
            "allowed_strategies": self.allowed_strategies,
            "allowed_coins": self.allowed_coins,
            "ui_settings": self.ui_settings,
            "notification_settings": self.notification_settings,
        }

