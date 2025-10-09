"""
데이터베이스 모델
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceData:
    """가격 데이터 모델"""
    market: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float


@dataclass
class OrderHistory:
    """주문 내역 모델"""
    order_id: str
    market: str
    side: str  # "bid" or "ask"
    order_type: str  # "market" or "limit"
    price: Optional[float]
    amount: float
    status: str
    created_at: datetime


@dataclass
class TradeHistory:
    """거래 내역 모델"""
    trade_id: str
    market: str
    side: str
    price: float
    amount: float
    fee: float
    profit_loss: Optional[float]
    created_at: datetime


@dataclass
class StrategyConfig:
    """전략 설정 모델"""
    strategy_name: str
    parameters: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

