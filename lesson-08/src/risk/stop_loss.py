"""
손절/익절 관리
"""

from typing import Optional


class StopLossManager:
    """
    손절/익절 관리자
    """
    
    def __init__(self, stop_loss_ratio: float = -0.02, take_profit_ratio: float = 0.05):
        """
        손절/익절 관리자 초기화
        
        Args:
            stop_loss_ratio: 손절 비율 (예: -0.02 = -2%)
            take_profit_ratio: 익절 비율 (예: 0.05 = 5%)
        """
        self.stop_loss_ratio = stop_loss_ratio
        self.take_profit_ratio = take_profit_ratio
        
    def check_stop_loss(self, entry_price: float, current_price: float) -> bool:
        """
        손절 확인
        
        Args:
            entry_price: 진입 가격
            current_price: 현재 가격
            
        Returns:
            손절 여부
        """
        # TODO: 구현 필요
        pass
    
    def check_take_profit(self, entry_price: float, current_price: float) -> bool:
        """
        익절 확인
        
        Args:
            entry_price: 진입 가격
            current_price: 현재 가격
            
        Returns:
            익절 여부
        """
        # TODO: 구현 필요
        pass

