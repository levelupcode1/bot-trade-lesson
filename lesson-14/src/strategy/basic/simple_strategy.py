"""
단순 매매 전략 (초보자용)
"""

from ..strategy_registry import BaseStrategy, register_strategy


@register_strategy(
    name="simple_buy_hold",
    level="basic",
    description="단순 매수 후 보유 전략"
)
class SimpleBuyHoldStrategy(BaseStrategy):
    """단순 매수 후 보유 전략"""
    
    def __init__(self, target_return: float = 0.05):
        self.target_return = target_return
    
    def execute(self, current_price: float, buy_price: float, **kwargs):
        """
        전략 실행
        
        Args:
            current_price: 현재 가격
            buy_price: 매수 가격
            
        Returns:
            "HOLD" 또는 "SELL"
        """
        if buy_price <= 0:
            return "HOLD"
        
        return_rate = (current_price - buy_price) / buy_price
        
        if return_rate >= self.target_return:
            return "SELL"
        
        return "HOLD"


@register_strategy(
    name="volatility_breakout_conservative",
    level="basic",
    description="보수적 변동성 돌파 전략"
)
class ConservativeVolatilityBreakout(BaseStrategy):
    """보수적 변동성 돌파 전략"""
    
    def __init__(self, k_value: float = 0.3):
        self.k_value = k_value
    
    def execute(self, current_price: float, yesterday_range: float, **kwargs):
        """전략 실행"""
        breakout_price = yesterday_range * self.k_value
        
        # 매우 보수적인 진입
        if current_price > breakout_price:
            return "BUY"
        
        return "HOLD"

