#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 데이터 수집기
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import asyncio
import aiohttp
from dataclasses import dataclass
import time
from threading import Thread, Event
import queue


@dataclass
class MarketData:
    """시장 데이터"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    bid: float
    ask: float
    high_24h: float
    low_24h: float
    change_24h: float


@dataclass
class StrategyPerformance:
    """전략 성과 데이터"""
    timestamp: datetime
    strategy_id: str
    position_size: float
    unrealized_pnl: float
    realized_pnl: float
    total_trades: int
    win_trades: int
    current_drawdown: float


class RealtimeDataCollector:
    """실시간 데이터 수집기"""
    
    def __init__(self, symbols: List[str], update_interval: int = 1):
        """
        Args:
            symbols: 수집할 심볼 리스트
            update_interval: 업데이트 간격 (초)
        """
        self.symbols = symbols
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        
        # 데이터 저장소
        self.market_data: Dict[str, MarketData] = {}
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # 데이터 히스토리
        self.market_history: List[MarketData] = []
        self.performance_history: List[StrategyPerformance] = []
        
        # 제어 플래그
        self._stop_event = Event()
        self._collection_thread: Optional[Thread] = None
        
        # 데이터 큐
        self.data_queue = queue.Queue(maxsize=1000)
        
        self.logger.info(f"실시간 데이터 수집기 초기화: {len(symbols)}개 심볼")
    
    def start(self):
        """데이터 수집 시작"""
        if self._collection_thread and self._collection_thread.is_alive():
            self.logger.warning("이미 수집 중입니다")
            return
        
        self._stop_event.clear()
        self._collection_thread = Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        
        self.logger.info("실시간 데이터 수집 시작")
    
    def stop(self):
        """데이터 수집 중지"""
        self._stop_event.set()
        
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        
        self.logger.info("실시간 데이터 수집 중지")
    
    def _collection_loop(self):
        """데이터 수집 루프"""
        while not self._stop_event.is_set():
            try:
                # 시장 데이터 수집
                self._collect_market_data()
                
                # 전략 성과 수집
                self._collect_strategy_performance()
                
                # 대기
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"데이터 수집 오류: {e}")
                time.sleep(self.update_interval)
    
    def _collect_market_data(self):
        """시장 데이터 수집 (시뮬레이션)"""
        timestamp = datetime.now()
        
        for symbol in self.symbols:
            # 실제 환경에서는 API 호출
            # 여기서는 시뮬레이션 데이터 생성
            
            if symbol in self.market_data:
                prev_price = self.market_data[symbol].price
            else:
                prev_price = 50000000  # 초기 가격
            
            # 랜덤 워크
            price = prev_price * (1 + np.random.normal(0, 0.001))
            
            market_data = MarketData(
                timestamp=timestamp,
                symbol=symbol,
                price=price,
                volume=np.random.uniform(100, 1000),
                bid=price * 0.999,
                ask=price * 1.001,
                high_24h=price * 1.02,
                low_24h=price * 0.98,
                change_24h=np.random.uniform(-0.05, 0.05)
            )
            
            self.market_data[symbol] = market_data
            self.market_history.append(market_data)
            
            # 큐에 추가
            try:
                self.data_queue.put_nowait(('market', market_data))
            except queue.Full:
                pass
        
        # 히스토리 제한 (최근 10000개만 유지)
        if len(self.market_history) > 10000:
            self.market_history = self.market_history[-10000:]
    
    def _collect_strategy_performance(self):
        """전략 성과 수집"""
        timestamp = datetime.now()
        
        # 전략별 성과 업데이트 (시뮬레이션)
        for strategy_id in ['vb_001', 'ma_001']:
            # 실제 환경에서는 전략 엔진에서 데이터 가져오기
            
            performance = StrategyPerformance(
                timestamp=timestamp,
                strategy_id=strategy_id,
                position_size=np.random.uniform(0, 0.1),
                unrealized_pnl=np.random.uniform(-10000, 20000),
                realized_pnl=np.random.uniform(-5000, 15000),
                total_trades=np.random.randint(10, 100),
                win_trades=np.random.randint(5, 80),
                current_drawdown=np.random.uniform(-0.05, 0)
            )
            
            self.strategy_performance[strategy_id] = performance
            self.performance_history.append(performance)
            
            # 큐에 추가
            try:
                self.data_queue.put_nowait(('performance', performance))
            except queue.Full:
                pass
        
        # 히스토리 제한
        if len(self.performance_history) > 10000:
            self.performance_history = self.performance_history[-10000:]
    
    def get_latest_market_data(self, symbol: str) -> Optional[MarketData]:
        """최신 시장 데이터 조회"""
        return self.market_data.get(symbol)
    
    def get_latest_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """최신 전략 성과 조회"""
        return self.strategy_performance.get(strategy_id)
    
    def get_market_history(self, symbol: str, minutes: int = 60) -> List[MarketData]:
        """시장 데이터 히스토리 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            data for data in self.market_history
            if data.symbol == symbol and data.timestamp >= cutoff_time
        ]
    
    def get_performance_history(self, strategy_id: str, minutes: int = 60) -> List[StrategyPerformance]:
        """전략 성과 히스토리 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            perf for perf in self.performance_history
            if perf.strategy_id == strategy_id and perf.timestamp >= cutoff_time
        ]
    
    def export_to_dataframe(self, data_type: str = 'market') -> pd.DataFrame:
        """데이터프레임으로 내보내기"""
        if data_type == 'market':
            if not self.market_history:
                return pd.DataFrame()
            
            data = []
            for item in self.market_history:
                data.append({
                    'timestamp': item.timestamp,
                    'symbol': item.symbol,
                    'price': item.price,
                    'volume': item.volume,
                    'bid': item.bid,
                    'ask': item.ask,
                    'high_24h': item.high_24h,
                    'low_24h': item.low_24h,
                    'change_24h': item.change_24h
                })
            
            return pd.DataFrame(data)
        
        elif data_type == 'performance':
            if not self.performance_history:
                return pd.DataFrame()
            
            data = []
            for item in self.performance_history:
                data.append({
                    'timestamp': item.timestamp,
                    'strategy_id': item.strategy_id,
                    'position_size': item.position_size,
                    'unrealized_pnl': item.unrealized_pnl,
                    'realized_pnl': item.realized_pnl,
                    'total_trades': item.total_trades,
                    'win_trades': item.win_trades,
                    'current_drawdown': item.current_drawdown
                })
            
            return pd.DataFrame(data)
        
        return pd.DataFrame()

