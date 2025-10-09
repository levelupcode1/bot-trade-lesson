"""
사용자 프로필 단위 테스트
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.user.profile.user_profile import UserType, RiskLevel
from src.user.profile.beginner_profile import BeginnerProfile
from src.user.profile.intermediate_profile import IntermediateProfile
from src.user.profile.advanced_profile import AdvancedProfile
from src.user.profile.profile_manager import ProfileManager


class TestBeginnerProfile:
    """초보자 프로필 테스트"""
    
    def test_create_beginner_profile(self):
        """초보자 프로필 생성 테스트"""
        profile = BeginnerProfile("test_user", 1000000)
        
        assert profile.user_id == "test_user"
        assert profile.user_type == UserType.BEGINNER
        assert profile.risk_level == RiskLevel.CONSERVATIVE
        assert profile.investment_amount == 1000000
    
    def test_beginner_trading_limits(self):
        """초보자 거래 제한 테스트"""
        profile = BeginnerProfile("test_user", 1000000)
        
        assert profile.trading_limits.max_position_size == 0.15
        assert profile.trading_limits.min_cash_ratio == 0.50
        assert profile.trading_limits.daily_trade_limit == 3
        assert profile.trading_limits.stop_loss == -0.03
    
    def test_beginner_feature_access(self):
        """초보자 기능 접근 테스트"""
        profile = BeginnerProfile("test_user", 1000000)
        
        assert profile.feature_access.basic_trading == True
        assert profile.feature_access.custom_strategies == False
        assert profile.feature_access.api_access == False
    
    def test_beginner_allowed_coins(self):
        """초보자 허용 코인 테스트"""
        profile = BeginnerProfile("test_user", 1000000)
        
        assert "KRW-BTC" in profile.allowed_coins
        assert "KRW-ETH" in profile.allowed_coins
        assert len(profile.allowed_coins) == 2


class TestIntermediateProfile:
    """중급자 프로필 테스트"""
    
    def test_create_intermediate_profile(self):
        """중급자 프로필 생성 테스트"""
        profile = IntermediateProfile("test_user", 5000000)
        
        assert profile.user_type == UserType.INTERMEDIATE
        assert profile.risk_level == RiskLevel.MODERATE
    
    def test_intermediate_trading_limits(self):
        """중급자 거래 제한 테스트"""
        profile = IntermediateProfile("test_user", 5000000)
        
        assert profile.trading_limits.max_position_size == 0.30
        assert profile.trading_limits.daily_trade_limit == 10
    
    def test_intermediate_feature_access(self):
        """중급자 기능 접근 테스트"""
        profile = IntermediateProfile("test_user", 5000000)
        
        assert profile.feature_access.custom_strategies == True
        assert profile.feature_access.advanced_analytics == True
        assert profile.feature_access.portfolio_management == True
        assert profile.feature_access.api_access == False


class TestAdvancedProfile:
    """고급자 프로필 테스트"""
    
    def test_create_advanced_profile(self):
        """고급자 프로필 생성 테스트"""
        profile = AdvancedProfile("test_user", 20000000)
        
        assert profile.user_type == UserType.ADVANCED
        assert profile.risk_level == RiskLevel.AGGRESSIVE
    
    def test_advanced_trading_limits(self):
        """고급자 거래 제한 테스트"""
        profile = AdvancedProfile("test_user", 20000000)
        
        assert profile.trading_limits.max_position_size == 0.80
        assert profile.trading_limits.daily_trade_limit == 9999
    
    def test_advanced_feature_access(self):
        """고급자 기능 접근 테스트"""
        profile = AdvancedProfile("test_user", 20000000)
        
        assert profile.feature_access.api_access == True
        assert profile.feature_access.ml_models == True
        assert profile.can_access_raw_api() == True
    
    def test_advanced_allowed_all(self):
        """고급자 전체 허용 테스트"""
        profile = AdvancedProfile("test_user", 20000000)
        
        assert "*" in profile.allowed_strategies
        assert "*" in profile.allowed_coins


class TestProfileManager:
    """프로필 관리자 테스트"""
    
    def setup_method(self):
        """테스트 준비"""
        self.profile_manager = ProfileManager("data/test_profiles")
    
    def teardown_method(self):
        """테스트 정리"""
        # 테스트 프로필 삭제
        import shutil
        import os
        if os.path.exists("data/test_profiles"):
            shutil.rmtree("data/test_profiles")
    
    def test_create_and_load_profile(self):
        """프로필 생성 및 로드 테스트"""
        # 프로필 생성
        profile = self.profile_manager.create_profile(
            user_id="test_user",
            user_type=UserType.BEGINNER,
            investment_amount=1000000
        )
        
        assert profile is not None
        assert profile.user_id == "test_user"
        
        # 프로필 로드
        loaded_profile = self.profile_manager.load_profile("test_user")
        
        assert loaded_profile is not None
        assert loaded_profile.user_id == "test_user"
        assert loaded_profile.user_type == UserType.BEGINNER
    
    def test_upgrade_profile(self):
        """프로필 업그레이드 테스트"""
        # 초보자 프로필 생성
        profile = self.profile_manager.create_profile(
            user_id="test_user",
            user_type=UserType.BEGINNER,
            investment_amount=1000000
        )
        
        assert profile.user_type == UserType.BEGINNER
        
        # 중급자로 업그레이드
        upgraded = self.profile_manager.upgrade_profile("test_user")
        
        assert upgraded is not None
        assert upgraded.user_type == UserType.INTERMEDIATE
    
    def test_validate_trade(self):
        """거래 유효성 검증 테스트"""
        profile = self.profile_manager.create_profile(
            user_id="test_user",
            user_type=UserType.BEGINNER,
            investment_amount=1000000
        )
        
        # 유효한 거래
        is_valid, error = profile.validate_trade({
            "coin": "KRW-BTC",
            "position_size": 0.10
        })
        assert is_valid == True
        assert error is None
        
        # 포지션 크기 초과
        is_valid, error = profile.validate_trade({
            "coin": "KRW-BTC",
            "position_size": 0.30
        })
        assert is_valid == False
        assert "포지션 크기" in error
        
        # 허용되지 않은 코인
        is_valid, error = profile.validate_trade({
            "coin": "KRW-DOGE",
            "position_size": 0.10
        })
        assert is_valid == False
        assert "허용 목록" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

