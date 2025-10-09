"""
Validator 유틸리티 테스트
"""

import pytest
from src.utils.validators import (
    validate_market_code,
    validate_api_key,
    validate_positive_number,
    validate_ratio
)


def test_validate_market_code():
    """마켓 코드 검증 테스트"""
    # 유효한 마켓 코드
    assert validate_market_code("KRW-BTC") == True
    assert validate_market_code("KRW-ETH") == True
    assert validate_market_code("USDT-BTC") == True
    
    # 무효한 마켓 코드
    assert validate_market_code("BTC") == False
    assert validate_market_code("KRW_BTC") == False
    assert validate_market_code("krw-btc") == False
    assert validate_market_code("") == False


def test_validate_api_key():
    """API 키 검증 테스트"""
    assert validate_api_key("valid_key_123") == True
    assert validate_api_key("") == False


def test_validate_positive_number():
    """양수 검증 테스트"""
    assert validate_positive_number(100) == True
    assert validate_positive_number(0.1) == True
    assert validate_positive_number("100") == True
    
    assert validate_positive_number(0) == False
    assert validate_positive_number(-100) == False
    assert validate_positive_number("invalid") == False


def test_validate_ratio():
    """비율 검증 테스트"""
    assert validate_ratio(0.0) == True
    assert validate_ratio(0.5) == True
    assert validate_ratio(1.0) == True
    assert validate_ratio("0.7") == True
    
    assert validate_ratio(-0.1) == False
    assert validate_ratio(1.1) == False
    assert validate_ratio("invalid") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

