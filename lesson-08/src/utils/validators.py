"""
검증 유틸리티
"""

import re
from typing import Any


def validate_market_code(market: str) -> bool:
    """
    마켓 코드 검증
    
    Args:
        market: 마켓 코드 (예: KRW-BTC)
        
    Returns:
        유효성 여부
    """
    pattern = r'^[A-Z]{3,}-[A-Z]{3,}$'
    return bool(re.match(pattern, market))


def validate_api_key(api_key: str) -> bool:
    """
    API 키 형식 검증
    
    Args:
        api_key: API 키
        
    Returns:
        유효성 여부
    """
    # TODO: 구현 필요
    return len(api_key) > 0


def validate_positive_number(value: Any) -> bool:
    """
    양수 검증
    
    Args:
        value: 검증할 값
        
    Returns:
        유효성 여부
    """
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False


def validate_ratio(value: Any) -> bool:
    """
    비율 검증 (0.0 ~ 1.0)
    
    Args:
        value: 검증할 값
        
    Returns:
        유효성 여부
    """
    try:
        val = float(value)
        return 0.0 <= val <= 1.0
    except (ValueError, TypeError):
        return False

