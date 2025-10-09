"""
포트폴리오 전략 (중급자용)
"""

from typing import Dict, List
from ..strategy_registry import BaseStrategy, register_strategy


@register_strategy(
    name="portfolio_strategy",
    level="advanced",
    description="다중 코인 포트폴리오 전략",
    required_permissions=["portfolio_management"]
)
class PortfolioStrategy(BaseStrategy):
    """다중 코인 포트폴리오 전략"""
    
    def __init__(self, coins: List[str], weights: List[float]):
        """
        Args:
            coins: 코인 목록
            weights: 각 코인의 비중 (합계 1.0)
        """
        if len(coins) != len(weights):
            raise ValueError("코인 수와 비중 수가 일치해야 합니다")
        
        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError("비중 합계는 1.0이어야 합니다")
        
        self.coins = coins
        self.weights = dict(zip(coins, weights))
    
    def execute(
        self,
        current_portfolio: Dict[str, float],
        total_value: float,
        **kwargs
    ) -> Dict[str, str]:
        """
        포트폴리오 리밸런싱 결정
        
        Args:
            current_portfolio: 현재 포트폴리오 {코인: 비중}
            total_value: 총 자산 가치
            
        Returns:
            각 코인별 액션 {"BTC": "BUY", "ETH": "SELL", ...}
        """
        actions = {}
        
        for coin in self.coins:
            target_weight = self.weights[coin]
            current_weight = current_portfolio.get(coin, 0.0)
            
            # 5% 이상 차이나면 리밸런싱
            if abs(target_weight - current_weight) > 0.05:
                if current_weight < target_weight:
                    actions[coin] = "BUY"
                else:
                    actions[coin] = "SELL"
            else:
                actions[coin] = "HOLD"
        
        return actions

