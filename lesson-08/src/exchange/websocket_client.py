"""
WebSocket 클라이언트 - 실시간 데이터 수신
"""

from typing import Callable, List, Optional


class WebSocketClient:
    """
    업비트 WebSocket 클라이언트
    """
    
    def __init__(self):
        """
        WebSocket 클라이언트 초기화
        """
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        WebSocket 연결
        
        Returns:
            연결 성공 여부
        """
        # TODO: 구현 필요
        pass
    
    def disconnect(self):
        """
        WebSocket 연결 종료
        """
        # TODO: 구현 필요
        pass
    
    def subscribe(self, markets: List[str], callback: Callable):
        """
        마켓 구독
        
        Args:
            markets: 구독할 마켓 리스트
            callback: 데이터 수신 콜백 함수
        """
        # TODO: 구현 필요
        pass

