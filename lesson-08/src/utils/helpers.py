"""
헬퍼 함수
"""

from datetime import datetime
from typing import Any, Dict


def format_currency(amount: float, currency: str = "KRW") -> str:
    """
    통화 포맷팅
    
    Args:
        amount: 금액
        currency: 통화 코드
        
    Returns:
        포맷된 문자열
    """
    if currency == "KRW":
        return f"₩{amount:,.0f}"
    else:
        return f"{amount:,.8f} {currency}"


def format_percentage(value: float) -> str:
    """
    퍼센트 포맷팅
    
    Args:
        value: 값 (예: 0.05 = 5%)
        
    Returns:
        포맷된 문자열
    """
    return f"{value * 100:.2f}%"


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    타임스탬프를 datetime으로 변환
    
    Args:
        timestamp: 유닉스 타임스탬프 (밀리초)
        
    Returns:
        datetime 객체
    """
    return datetime.fromtimestamp(timestamp / 1000)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    안전한 나눗셈 (0으로 나누기 방지)
    
    Args:
        numerator: 분자
        denominator: 분모
        default: 분모가 0일 때 기본값
        
    Returns:
        나눗셈 결과
    """
    return numerator / denominator if denominator != 0 else default

