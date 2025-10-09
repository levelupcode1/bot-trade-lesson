"""
메인 트레이딩 시스템 - 전체 거래 시스템의 중앙 제어
"""

from typing import Optional, Dict, Any


class TradingSystem:
    """
    자동매매 시스템의 메인 컨트롤러
    """
    
    def __init__(self):
        """
        트레이딩 시스템 초기화
        """
        self.is_running = False
        self.strategies = {}
        
    def start(self):
        """
        트레이딩 시스템 시작
        """
        # TODO: 구현 필요
        pass
    
    def stop(self):
        """
        트레이딩 시스템 중지
        """
        # TODO: 구현 필요
        pass
    
    def add_strategy(self, strategy_name: str, strategy: Any):
        """
        전략 추가
        
        Args:
            strategy_name: 전략 이름
            strategy: 전략 인스턴스
        """
        # TODO: 구현 필요
        pass

