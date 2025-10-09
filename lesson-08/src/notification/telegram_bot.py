"""
텔레그램 봇
"""

from typing import Optional


class TelegramBot:
    """
    텔레그램 봇 클라이언트
    """
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        """
        텔레그램 봇 초기화
        
        Args:
            bot_token: 봇 토큰
            chat_id: 채팅 ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        
    def send_message(self, message: str) -> bool:
        """
        메시지 전송
        
        Args:
            message: 전송할 메시지
            
        Returns:
            전송 성공 여부
        """
        # TODO: 구현 필요
        pass
    
    def send_image(self, image_path: str, caption: str = "") -> bool:
        """
        이미지 전송
        
        Args:
            image_path: 이미지 파일 경로
            caption: 이미지 설명
            
        Returns:
            전송 성공 여부
        """
        # TODO: 구현 필요
        pass

