"""
기본 전략 클래스 - 모든 트레이딩 전략의 추상 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseStrategy(ABC):
    """
    모든 트레이딩 전략이 상속해야 하는 추상 베이스 클래스
    """
    
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        전략 초기화
        
        Args:
            name: 전략 이름
            params: 전략 매개변수
        """
        self.name = name
        self.params = params or {}
        
    @abstractmethod
    def generate_signal(self, data: Dict[str, Any]) -> str:
        """
        매수/매도/홀드 신호 생성
        
        Args:
            data: 시장 데이터
            
        Returns:
            "BUY", "SELL", "HOLD" 중 하나
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, account_balance: float, current_price: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            account_balance: 계좌 잔고
            current_price: 현재 가격
            
        Returns:
            투자 금액
        """
        pass

