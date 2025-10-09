"""
가격 모니터링
"""

from typing import List, Dict, Any


class PriceMonitor:
    """
    가격 모니터링 시스템
    """
    
    def __init__(self):
        """
        가격 모니터 초기화
        """
        self.monitored_markets: List[str] = []
        
    def add_market(self, market: str):
        """
        모니터링할 마켓 추가
        
        Args:
            market: 마켓 코드
        """
        # TODO: 구현 필요
        pass
    
    def start_monitoring(self):
        """
        모니터링 시작
        """
        # TODO: 구현 필요
        pass
    
    def stop_monitoring(self):
        """
        모니터링 중지
        """
        # TODO: 구현 필요
        pass

