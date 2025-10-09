"""
TradingSystem 클래스 테스트
"""

import pytest
from src.core.trading_system import TradingSystem


def test_trading_system_initialization():
    """트레이딩 시스템 초기화 테스트"""
    system = TradingSystem()
    
    assert system.is_running == False
    assert system.strategies == {}


def test_add_strategy():
    """전략 추가 테스트"""
    system = TradingSystem()
    
    # Mock 전략 추가
    class MockStrategy:
        name = "TestStrategy"
    
    system.add_strategy("test", MockStrategy())
    
    # TODO: 구현 완료 후 주석 해제
    # assert "test" in system.strategies


def test_system_start_stop():
    """시스템 시작/중지 테스트"""
    system = TradingSystem()
    
    # TODO: 구현 완료 후 주석 해제
    # system.start()
    # assert system.is_running == True
    
    # system.stop()
    # assert system.is_running == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

