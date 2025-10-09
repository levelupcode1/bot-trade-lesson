"""
시스템 통합 테스트
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.user.profile.profile_manager import ProfileManager
from src.user.profile.user_profile import UserType
from src.user.auth.authorization import Authorization
from src.strategy.strategy_loader import StrategyLoader
from src.config.config_manager import ConfigManager


class TestSystemIntegration:
    """시스템 통합 테스트"""
    
    def setup_method(self):
        """테스트 준비"""
        self.profile_manager = ProfileManager("data/test_profiles")
        self.authorization = Authorization()
        self.strategy_loader = StrategyLoader()
        self.config_manager = ConfigManager("config")
    
    def teardown_method(self):
        """테스트 정리"""
        import shutil
        if os.path.exists("data/test_profiles"):
            shutil.rmtree("data/test_profiles")
    
    def test_full_workflow_beginner(self):
        """초보자 전체 워크플로우 테스트"""
        # 1. 프로필 생성
        profile = self.profile_manager.create_profile(
            user_id="beginner_test",
            user_type=UserType.BEGINNER,
            investment_amount=1000000
        )
        
        assert profile is not None
        
        # 2. 권한 확인
        can_trade = self.authorization.check_permission(profile, "place_basic_order")
        assert can_trade == True
        
        can_api = self.authorization.check_permission(profile, "access_api")
        assert can_api == False
        
        # 3. 전략 로드
        self.strategy_loader.load_all_strategies()
        strategies = self.strategy_loader.get_strategies_for_profile(profile)
        
        assert len(strategies) > 0
        
        # 4. 거래 검증
        is_valid, _ = profile.validate_trade({
            "coin": "KRW-BTC",
            "position_size": 0.10
        })
        assert is_valid == True
        
        # 5. 설정 로드
        config = self.config_manager.load_profile_config(UserType.BEGINNER)
        assert config.get("ui.complexity_level") == "simple"
    
    def test_full_workflow_advanced(self):
        """고급자 전체 워크플로우 테스트"""
        # 1. 프로필 생성
        profile = self.profile_manager.create_profile(
            user_id="advanced_test",
            user_type=UserType.ADVANCED,
            investment_amount=20000000
        )
        
        # 2. 권한 확인
        can_api = self.authorization.check_permission(profile, "access_api")
        assert can_api == True
        
        can_ml = self.authorization.check_permission(profile, "use_ml_models")
        assert can_ml == True
        
        # 3. 모든 전략 접근 가능
        self.strategy_loader.load_all_strategies()
        strategies = self.strategy_loader.get_strategies_for_profile(profile)
        
        # 고급자는 모든 전략 사용 가능 ("*" 허용)
        assert "*" in profile.allowed_strategies
        
        # 4. 높은 포지션 크기 허용
        is_valid, _ = profile.validate_trade({
            "coin": "KRW-BTC",
            "position_size": 0.50  # 50%
        })
        assert is_valid == True
    
    def test_profile_upgrade_workflow(self):
        """프로필 업그레이드 워크플로우 테스트"""
        # 1. 초보자로 시작
        profile = self.profile_manager.create_profile(
            user_id="upgrade_test",
            user_type=UserType.BEGINNER,
            investment_amount=1000000
        )
        
        assert profile.user_type == UserType.BEGINNER
        assert profile.trading_limits.daily_trade_limit == 3
        
        # 2. 중급자로 업그레이드
        upgraded = self.profile_manager.upgrade_profile("upgrade_test")
        assert upgraded.user_type == UserType.INTERMEDIATE
        assert upgraded.trading_limits.daily_trade_limit == 10
        
        # 3. 고급자로 업그레이드
        upgraded2 = self.profile_manager.upgrade_profile("upgrade_test")
        assert upgraded2.user_type == UserType.ADVANCED
        assert upgraded2.feature_access.api_access == True
        
        # 4. 더 이상 업그레이드 불가
        final = self.profile_manager.upgrade_profile("upgrade_test")
        assert final.user_type == UserType.ADVANCED  # 변경 없음
    
    def test_authorization_workflow(self):
        """권한 관리 워크플로우 테스트"""
        profiles = []
        
        # 모든 유형의 프로필 생성
        for user_type in [UserType.BEGINNER, UserType.INTERMEDIATE, UserType.ADVANCED]:
            profile = self.profile_manager.create_profile(
                user_id=f"{user_type.value}_auth_test",
                user_type=user_type,
                investment_amount=1000000
            )
            profiles.append(profile)
        
        # 권한 체계 확인
        for profile in profiles:
            available = self.authorization.get_available_features(profile)
            restricted = self.authorization.get_restricted_features(profile)
            
            # 모든 기능은 available 또는 restricted 중 하나
            total_features = len(available) + len(restricted)
            assert total_features > 0
            
            # 초보자는 제한이 많음
            if profile.user_type == UserType.BEGINNER:
                assert len(restricted) > len(available)
            
            # 고급자는 제한이 거의 없음
            if profile.user_type == UserType.ADVANCED:
                assert len(available) > len(restricted)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

