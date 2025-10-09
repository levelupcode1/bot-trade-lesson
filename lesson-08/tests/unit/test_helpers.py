"""
Helper 유틸리티 테스트
"""

import pytest
from datetime import datetime
from src.utils.helpers import (
    format_currency,
    format_percentage,
    timestamp_to_datetime,
    safe_divide
)


def test_format_currency():
    """통화 포맷팅 테스트"""
    assert format_currency(1000000, "KRW") == "₩1,000,000"
    assert format_currency(1234567, "KRW") == "₩1,234,567"
    
    # BTC 포맷
    btc_formatted = format_currency(0.12345678, "BTC")
    assert "BTC" in btc_formatted
    assert "0.12345678" in btc_formatted


def test_format_percentage():
    """퍼센트 포맷팅 테스트"""
    assert format_percentage(0.05) == "5.00%"
    assert format_percentage(0.1234) == "12.34%"
    assert format_percentage(-0.02) == "-2.00%"


def test_timestamp_to_datetime():
    """타임스탬프 변환 테스트"""
    # 2024-01-01 00:00:00 UTC (밀리초)
    timestamp = 1704067200000
    dt = timestamp_to_datetime(timestamp)
    
    assert isinstance(dt, datetime)
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 1


def test_safe_divide():
    """안전한 나눗셈 테스트"""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0  # 기본값
    assert safe_divide(10, 0, default=100) == 100  # 커스텀 기본값
    assert safe_divide(7, 3) == pytest.approx(2.333, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

