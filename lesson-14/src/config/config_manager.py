"""
설정 관리자 - YAML 기반 설정 관리
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import logging

from ..user.profile.user_profile import UserType


logger = logging.getLogger(__name__)


class ProfileConfig:
    """프로필 설정 클래스"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config_dict = config_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기"""
        keys = key.split(".")
        value = self.config_dict
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """설정값 설정하기"""
        keys = key.split(".")
        config = self.config_dict
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return self.config_dict.copy()


class ConfigManager:
    """설정 관리자"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.features_dir = self.config_dir / "features"
        self.features_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache: Dict[str, ProfileConfig] = {}
    
    def load_profile_config(self, user_type: UserType) -> ProfileConfig:
        """
        프로필별 설정 로드
        
        Args:
            user_type: 사용자 유형
            
        Returns:
            프로필 설정 객체
        """
        cache_key = f"profile_{user_type.value}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config_file = self.profiles_dir / f"{user_type.value}.yaml"
        
        if not config_file.exists():
            # 기본 설정 생성
            self._create_default_profile_config(user_type)
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}
        
        config = ProfileConfig(config_dict)
        self._cache[cache_key] = config
        
        return config
    
    def save_profile_config(
        self,
        user_type: UserType,
        config: ProfileConfig
    ) -> None:
        """
        프로필 설정 저장
        
        Args:
            user_type: 사용자 유형
            config: 프로필 설정
        """
        config_file = self.profiles_dir / f"{user_type.value}.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(
                config.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        
        # 캐시 갱신
        cache_key = f"profile_{user_type.value}"
        self._cache[cache_key] = config
        
        logger.info(f"프로필 설정 저장 완료: {user_type.value}")
    
    def load_feature_flags(self) -> Dict[str, bool]:
        """
        기능 플래그 로드
        
        Returns:
            기능 플래그 딕셔너리
        """
        feature_file = self.features_dir / "feature_flags.yaml"
        
        if not feature_file.exists():
            self._create_default_feature_flags()
        
        with open(feature_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def update_feature_flag(self, feature: str, enabled: bool) -> None:
        """
        기능 플래그 업데이트
        
        Args:
            feature: 기능 이름
            enabled: 활성화 여부
        """
        flags = self.load_feature_flags()
        flags[feature] = enabled
        
        feature_file = self.features_dir / "feature_flags.yaml"
        with open(feature_file, 'w', encoding='utf-8') as f:
            yaml.dump(flags, f, default_flow_style=False)
        
        logger.info(f"기능 플래그 업데이트: {feature} = {enabled}")
    
    def _create_default_profile_config(self, user_type: UserType) -> None:
        """기본 프로필 설정 생성"""
        configs = {
            UserType.BEGINNER: {
                "trading": {
                    "max_position_size": 0.15,
                    "min_cash_ratio": 0.50,
                    "daily_trade_limit": 3,
                    "stop_loss": -0.03,
                    "take_profit": 0.05
                },
                "ui": {
                    "complexity_level": "simple",
                    "show_tooltips": True,
                    "tutorial_mode": True
                },
                "notifications": {
                    "all_trades": True,
                    "educational_tips": True
                }
            },
            UserType.INTERMEDIATE: {
                "trading": {
                    "max_position_size": 0.30,
                    "min_cash_ratio": 0.30,
                    "daily_trade_limit": 10,
                    "stop_loss": -0.07,
                    "take_profit": 0.10
                },
                "ui": {
                    "complexity_level": "intermediate",
                    "show_tooltips": True,
                    "tutorial_mode": False
                },
                "notifications": {
                    "significant_trades": True,
                    "strategy_signals": True
                }
            },
            UserType.ADVANCED: {
                "trading": {
                    "max_position_size": 0.80,
                    "min_cash_ratio": 0.10,
                    "daily_trade_limit": 9999,
                    "stop_loss": -0.15,
                    "take_profit": 0.20
                },
                "ui": {
                    "complexity_level": "expert",
                    "show_tooltips": False,
                    "enable_code_editor": True
                },
                "notifications": {
                    "critical_only": True
                }
            }
        }
        
        config = configs.get(user_type, configs[UserType.BEGINNER])
        config_file = self.profiles_dir / f"{user_type.value}.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def _create_default_feature_flags(self) -> None:
        """기본 기능 플래그 생성"""
        default_flags = {
            "basic_trading": True,
            "custom_strategies": True,
            "advanced_analytics": True,
            "api_access": True,
            "ml_models": False,  # 기본적으로 비활성화
            "multi_exchange": False,  # 향후 기능
            "paper_trading": True,
            "backtesting": True,
        }
        
        feature_file = self.features_dir / "feature_flags.yaml"
        with open(feature_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_flags, f, default_flow_style=False)
    
    def merge_configs(
        self,
        base_config: ProfileConfig,
        custom_config: Dict[str, Any]
    ) -> ProfileConfig:
        """
        설정 병합
        
        Args:
            base_config: 기본 설정
            custom_config: 커스텀 설정
            
        Returns:
            병합된 설정
        """
        merged = base_config.to_dict()
        self._deep_merge(merged, custom_config)
        return ProfileConfig(merged)
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """딕셔너리 깊은 병합"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

