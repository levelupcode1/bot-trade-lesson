"""
BaseStrategy 클래스 테스트
"""

import pytest
from src.core.base_strategy import BaseStrategy


class MockStrategy(BaseStrategy):
    """테스트용 전략 클래스"""
    
    def generate_signal(self, data):
        return "BUY"
    
    def calculate_position_size(self, account_balance, current_price):
        return account_balance * 0.1


def test_base_strategy_initialization():
    """전략 초기화 테스트"""
    strategy = MockStrategy("TestStrategy", {"param1": 1, "param2": 2})
    
    assert strategy.name == "TestStrategy"
    assert strategy.params == {"param1": 1, "param2": 2}


def test_generate_signal():
    """신호 생성 테스트"""
    strategy = MockStrategy("TestStrategy")
    signal = strategy.generate_signal({"price": 50000000})
    
    assert signal in ["BUY", "SELL", "HOLD"]


def test_calculate_position_size():
    """포지션 크기 계산 테스트"""
    strategy = MockStrategy("TestStrategy")
    position_size = strategy.calculate_position_size(1000000, 50000000)
    
    assert position_size == 100000  # 10%


def test_strategy_without_params():
    """매개변수 없이 전략 생성 테스트"""
    strategy = MockStrategy("TestStrategy")
    
    assert strategy.name == "TestStrategy"
    assert strategy.params == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

