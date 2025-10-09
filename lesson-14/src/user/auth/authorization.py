"""
권한 관리 시스템
"""

from typing import Dict, List, Optional, Callable
from functools import wraps
from enum import Enum

from ..profile.user_profile import UserProfile, UserType


class Permission(Enum):
    """권한 정의"""
    # 기본 권한
    VIEW_DASHBOARD = "view_dashboard"
    PLACE_ORDER = "place_order"
    VIEW_HISTORY = "view_history"
    
    # 중급 권한
    CUSTOM_STRATEGY = "custom_strategy"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    MODIFY_RISK_SETTINGS = "modify_risk_settings"
    
    # 고급 권한
    API_ACCESS = "api_access"
    ML_MODELS = "ml_models"
    CODE_EXECUTION = "code_execution"
    RAW_DATA_ACCESS = "raw_data_access"
    SYSTEM_SETTINGS = "system_settings"


class FeatureGate:
    """기능 게이트 - 기능별 접근 제어"""
    
    # 기능별 필요 권한 매핑
    FEATURE_PERMISSIONS: Dict[str, List[Permission]] = {
        # 기본 기능
        "view_dashboard": [Permission.VIEW_DASHBOARD],
        "place_basic_order": [Permission.PLACE_ORDER],
        "view_trade_history": [Permission.VIEW_HISTORY],
        
        # 중급 기능
        "create_custom_strategy": [Permission.CUSTOM_STRATEGY],
        "access_advanced_analytics": [Permission.ADVANCED_ANALYTICS],
        "manage_portfolio": [Permission.PORTFOLIO_MANAGEMENT],
        "modify_risk_limits": [Permission.MODIFY_RISK_SETTINGS],
        
        # 고급 기능
        "access_api": [Permission.API_ACCESS],
        "use_ml_models": [Permission.ML_MODELS],
        "execute_code": [Permission.CODE_EXECUTION],
        "access_raw_data": [Permission.RAW_DATA_ACCESS],
        "modify_system_settings": [Permission.SYSTEM_SETTINGS],
    }
    
    # 사용자 유형별 기본 권한
    USER_TYPE_PERMISSIONS: Dict[UserType, List[Permission]] = {
        UserType.BEGINNER: [
            Permission.VIEW_DASHBOARD,
            Permission.PLACE_ORDER,
            Permission.VIEW_HISTORY,
        ],
        UserType.INTERMEDIATE: [
            Permission.VIEW_DASHBOARD,
            Permission.PLACE_ORDER,
            Permission.VIEW_HISTORY,
            Permission.CUSTOM_STRATEGY,
            Permission.ADVANCED_ANALYTICS,
            Permission.PORTFOLIO_MANAGEMENT,
            Permission.MODIFY_RISK_SETTINGS,
        ],
        UserType.ADVANCED: [
            # 모든 권한
            *list(Permission)
        ],
    }
    
    @classmethod
    def can_access_feature(
        cls,
        profile: UserProfile,
        feature: str
    ) -> tuple[bool, Optional[str]]:
        """
        기능 접근 가능 여부 확인
        
        Args:
            profile: 사용자 프로필
            feature: 기능 이름
            
        Returns:
            (접근 가능 여부, 오류 메시지)
        """
        required_permissions = cls.FEATURE_PERMISSIONS.get(feature)
        if not required_permissions:
            return False, f"알 수 없는 기능: {feature}"
        
        user_permissions = cls.USER_TYPE_PERMISSIONS.get(profile.user_type, [])
        
        # 필요한 모든 권한이 있는지 확인
        for perm in required_permissions:
            if perm not in user_permissions:
                return False, f"{feature} 기능을 사용하려면 {perm.value} 권한이 필요합니다"
        
        return True, None
    
    @classmethod
    def require_permission(cls, feature: str):
        """
        권한 확인 데코레이터
        
        Usage:
            @FeatureGate.require_permission("create_custom_strategy")
            def create_strategy(profile: UserProfile, ...):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(profile: UserProfile, *args, **kwargs):
                can_access, error_msg = cls.can_access_feature(profile, feature)
                if not can_access:
                    raise PermissionError(error_msg)
                return func(profile, *args, **kwargs)
            return wrapper
        return decorator


class Authorization:
    """권한 관리자"""
    
    def __init__(self):
        self.feature_gate = FeatureGate()
    
    def check_permission(
        self,
        profile: UserProfile,
        feature: str
    ) -> bool:
        """권한 확인"""
        can_access, _ = self.feature_gate.can_access_feature(profile, feature)
        return can_access
    
    def get_available_features(self, profile: UserProfile) -> List[str]:
        """사용 가능한 기능 목록 반환"""
        available = []
        for feature in self.feature_gate.FEATURE_PERMISSIONS.keys():
            if self.check_permission(profile, feature):
                available.append(feature)
        return available
    
    def get_restricted_features(self, profile: UserProfile) -> List[str]:
        """제한된 기능 목록 반환"""
        restricted = []
        for feature in self.feature_gate.FEATURE_PERMISSIONS.keys():
            if not self.check_permission(profile, feature):
                restricted.append(feature)
        return restricted
    
    def get_permissions_for_user(self, profile: UserProfile) -> List[Permission]:
        """사용자의 권한 목록 반환"""
        return self.feature_gate.USER_TYPE_PERMISSIONS.get(profile.user_type, [])
    
    def validate_action(
        self,
        profile: UserProfile,
        action: str,
        context: Optional[Dict] = None
    ) -> tuple[bool, Optional[str]]:
        """
        액션 수행 가능 여부 검증
        
        Args:
            profile: 사용자 프로필
            action: 수행할 액션
            context: 추가 컨텍스트 정보
            
        Returns:
            (수행 가능 여부, 오류 메시지)
        """
        # 기능 접근 권한 확인
        can_access, error_msg = self.feature_gate.can_access_feature(profile, action)
        if not can_access:
            return False, error_msg
        
        # 추가 검증 (거래 제한 등)
        if context:
            is_valid, validation_error = profile.validate_trade(context)
            if not is_valid:
                return False, validation_error
        
        return True, None

