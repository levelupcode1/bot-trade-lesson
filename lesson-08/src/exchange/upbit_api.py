"""
업비트 API 클라이언트
"""

from typing import Optional, Dict, Any, List


class UpbitAPI:
    """
    업비트 API 클라이언트
    """
    
    def __init__(self, access_key: str = "", secret_key: str = ""):
        """
        업비트 API 초기화
        
        Args:
            access_key: 액세스 키
            secret_key: 시크릿 키
        """
        self.access_key = access_key
        self.secret_key = secret_key
        
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        # TODO: 구현 필요
        pass
    
    def get_price_data(self, market: str) -> Optional[Dict[str, Any]]:
        """
        가격 데이터 조회
        
        Args:
            market: 마켓 코드 (예: KRW-BTC)
            
        Returns:
            가격 데이터
        """
        # TODO: 구현 필요
        pass
    
    def get_account_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        계좌 정보 조회
        
        Returns:
            계좌 정보 리스트
        """
        # TODO: 구현 필요
        pass

