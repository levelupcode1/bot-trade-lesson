"""
RSI 전략
"""

from src.core.base_strategy import BaseStrategy
from typing import Dict, Any


class RSIStrategy(BaseStrategy):
    """
    RSI(Relative Strength Index) 전략
    
    RSI가 과매도 구간(30 이하)에서 매수
    RSI가 과매수 구간(70 이상)에서 매도
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        전략 초기화
        
        Args:
            period: RSI 계산 기간
            oversold: 과매도 기준
            overbought: 과매수 기준
        """
        super().__init__("RSI", {
            "period": period,
            "oversold": oversold,
            "overbought": overbought
        })
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def generate_signal(self, data: Dict[str, Any]) -> str:
        """
        매수/매도 신호 생성
        
        Args:
            data: 시장 데이터
            
        Returns:
            "BUY", "SELL", "HOLD"
        """
        # TODO: 구현 필요
        pass
    
    def calculate_position_size(self, account_balance: float, current_price: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            account_balance: 계좌 잔고
            current_price: 현재 가격
            
        Returns:
            투자 금액
        """
        # TODO: 구현 필요
        pass

