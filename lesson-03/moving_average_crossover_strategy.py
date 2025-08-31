#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이동평균 크로스오버 전략 (Moving Average Crossover Strategy)
단기 이동평균(5일)과 장기 이동평균(20일)을 사용하여 매수/매도 신호를 생성하는 자동매매 시스템
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ma_crossover.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class PriceData:
    """가격 데이터 구조"""
    date: datetime
    price: float
    volume: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'date': self.date.isoformat(),
            'price': self.price,
            'volume': self.volume
        }

@dataclass
class TradeSignal:
    """거래 신호 구조"""
    timestamp: datetime
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    short_ma: float
    long_ma: float
    volume: float
    avg_volume: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'price': self.price,
            'short_ma': self.short_ma,
            'long_ma': self.long_ma,
            'volume': self.volume,
            'avg_volume': self.avg_volume,
            'reason': self.reason
        }

@dataclass
class Position:
    """포지션 정보 구조"""
    entry_time: datetime
    entry_price: float
    quantity: float
    position_size: float
    short_ma_at_entry: float
    long_ma_at_entry: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'position_size': self.position_size,
            'short_ma_at_entry': self.short_ma_at_entry,
            'long_ma_at_entry': self.long_ma_at_entry
        }

class DataCollector:
    """데이터 수집 클래스"""
    
    def __init__(self):
        """초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_bitcoin_price_data(self, days: int = 30) -> List[PriceData]:
        """비트코인 가격 및 거래량 데이터 수집 (CoinGecko API 사용)"""
        try:
            # 일별 가격 데이터 수집
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "krw",
                "days": days
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                price_list = []
                
                # 가격 데이터 처리
                if "prices" in data and data["prices"]:
                    for timestamp_ms, price in data["prices"]:
                        date = datetime.fromtimestamp(timestamp_ms / 1000)
                        
                        price_data = PriceData(
                            date=date,
                            price=float(price),
                            volume=0.0  # 기본값 설정
                        )
                        price_list.append(price_data)
                
                # 거래량 데이터 처리 (가능한 경우)
                if "total_volumes" in data and data["total_volumes"]:
                    for i, (timestamp_ms, volume) in enumerate(data["total_volumes"]):
                        if i < len(price_list):
                            price_list[i].volume = float(volume)
                
                # 날짜순으로 정렬
                price_list.sort(key=lambda x: x.date)
                
                # 거래량이 0인 경우 평균값으로 대체
                if price_list:
                    avg_volume = np.mean([p.volume for p in price_list if p.volume > 0])
                    if avg_volume > 0:
                        for price_data in price_list:
                            if price_data.volume == 0:
                                price_data.volume = avg_volume
                
                logging.info(f"비트코인 가격 데이터 {len(price_list)}개 수집 완료")
                return price_list
            else:
                logging.error(f"API 호출 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"데이터 수집 오류: {e}")
            return []
    
    def get_current_bitcoin_price(self) -> Optional[float]:
        """현재 비트코인 가격 조회"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "krw"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "bitcoin" in data and "krw" in data["bitcoin"]:
                    return float(data["bitcoin"]["krw"])
            return None
            
        except Exception as e:
            logging.error(f"현재 가격 조회 오류: {e}")
            return None

class MovingAverageCalculator:
    """이동평균 계산 클래스"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """단순이동평균 (Simple Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i-period+1:i+1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """지수가동평균 (Exponential Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        ema_values = []
        multiplier = 2 / (period + 1)
        
        # 첫 번째 EMA는 SMA로 계산
        first_ema = sum(prices[:period]) / period
        ema_values.append(first_ema)
        
        # 나머지 EMA 계산
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def calculate_volume_ma(volumes: List[float], period: int) -> List[float]:
        """거래량 이동평균 계산"""
        if len(volumes) < period:
            return []
        
        volume_ma_values = []
        for i in range(period - 1, len(volumes)):
            volume_ma = sum(volumes[i-period+1:i+1]) / period
            volume_ma_values.append(volume_ma)
        
        return volume_ma_values

# 메인 전략 클래스는 별도 파일로 분할
