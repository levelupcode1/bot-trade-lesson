"""
알림 관리자
"""

from typing import Dict, Any
from enum import Enum


class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertManager:
    """
    알림 관리 시스템
    """
    
    def __init__(self, telegram_bot=None):
        """
        알림 관리자 초기화
        
        Args:
            telegram_bot: 텔레그램 봇 인스턴스
        """
        self.telegram_bot = telegram_bot
        
    def send_trade_alert(self, trade_info: Dict[str, Any]):
        """
        거래 알림 전송
        
        Args:
            trade_info: 거래 정보
        """
        # TODO: 구현 필요
        pass
    
    def send_profit_alert(self, profit_info: Dict[str, Any]):
        """
        수익률 알림 전송
        
        Args:
            profit_info: 수익 정보
        """
        # TODO: 구현 필요
        pass
    
    def send_error_alert(self, error_message: str, level: AlertLevel = AlertLevel.ERROR):
        """
        오류 알림 전송
        
        Args:
            error_message: 오류 메시지
            level: 알림 레벨
        """
        # TODO: 구현 필요
        pass

