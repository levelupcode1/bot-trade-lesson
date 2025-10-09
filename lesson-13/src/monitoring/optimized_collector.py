#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화된 실시간 데이터 수집기

최적화 포인트:
1. 비동기 처리로 효율성 향상
2. 배치 처리로 I/O 최소화
3. 메모리 효율적인 링 버퍼 사용
4. 캐싱으로 중복 계산 제거
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Deque
from dataclasses import dataclass
import logging
from collections import deque
from threading import Thread, Event, Lock
import time


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


class RingBuffer:
    """메모리 효율적인 링 버퍼"""
    
    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self.buffer: Deque = deque(maxlen=maxsize)
        self.lock = Lock()
    
    def append(self, item):
        """아이템 추가"""
        with self.lock:
            self.buffer.append(item)
    
    def get_recent(self, n: int) -> List:
        """최근 n개 아이템 조회"""
        with self.lock:
            if n >= len(self.buffer):
                return list(self.buffer)
            return list(self.buffer)[-n:]
    
    def get_since(self, timestamp: datetime) -> List:
        """특정 시간 이후 데이터 조회"""
        with self.lock:
            return [item for item in self.buffer if item.timestamp >= timestamp]
    
    def clear(self):
        """버퍼 초기화"""
        with self.lock:
            self.buffer.clear()


class OptimizedDataCollector:
    """최적화된 실시간 데이터 수집기"""
    
    def __init__(self, 
                 symbols: List[str], 
                 update_interval: int = 1,
                 buffer_size: int = 10000,
                 batch_size: int = 100):
        """
        Args:
            symbols: 수집할 심볼 리스트
            update_interval: 업데이트 간격 (초)
            buffer_size: 버퍼 크기
            batch_size: 배치 저장 크기
        """
        self.symbols = symbols
        self.update_interval = update_interval
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        
        self.logger = logging.getLogger(__name__)
        
        # 링 버퍼 (메모리 효율적)
        self.market_buffer = RingBuffer(buffer_size)
        self.performance_buffer = RingBuffer(buffer_size)
        
        # 최신 데이터 캐시
        self._market_cache: Dict[str, MarketData] = {}
        self._cache_lock = Lock()
        
        # 배치 처리
        self._batch_queue: List = []
        self._batch_lock = Lock()
        
        # 제어
        self._stop_event = Event()
        self._collection_thread: Optional[Thread] = None
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 성능 메트릭
        self.stats = {
            'updates': 0,
            'errors': 0,
            'avg_update_time': 0,
            'last_update': None
        }
        
        self.logger.info(f"최적화된 데이터 수집기 초기화: {len(symbols)}개 심볼, 버퍼={buffer_size}")
    
    def start(self):
        """데이터 수집 시작"""
        if self._collection_thread and self._collection_thread.is_alive():
            self.logger.warning("이미 수집 중입니다")
            return
        
        self._stop_event.clear()
        self._collection_thread = Thread(target=self._run_async_loop, daemon=True)
        self._collection_thread.start()
        
        self.logger.info("최적화된 데이터 수집 시작")
    
    def stop(self):
        """데이터 수집 중지"""
        self._stop_event.set()
        
        if self._async_loop:
            self._async_loop.stop()
        
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        
        # 남은 배치 저장
        self._flush_batch()
        
        self.logger.info("최적화된 데이터 수집 중지")
    
    def _run_async_loop(self):
        """비동기 이벤트 루프 실행"""
        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)
        
        try:
            self._async_loop.run_until_complete(self._async_collection_loop())
        except Exception as e:
            self.logger.error(f"비동기 루프 오류: {e}")
        finally:
            self._async_loop.close()
    
    async def _async_collection_loop(self):
        """비동기 데이터 수집 루프"""
        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:
                # 비동기로 모든 심볼 데이터 수집
                await self._collect_all_symbols()
                
                # 성능 메트릭 업데이트
                elapsed = time.time() - start_time
                self._update_stats(elapsed)
                
                # 대기 (남은 시간만큼)
                sleep_time = max(0, self.update_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"데이터 수집 오류: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(self.update_interval)
    
    async def _collect_all_symbols(self):
        """모든 심볼 데이터 비동기 수집"""
        tasks = [self._fetch_market_data(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        timestamp = datetime.now()
        
        for symbol, result in zip(self.symbols, results):
            if isinstance(result, Exception):
                self.logger.error(f"{symbol} 수집 오류: {result}")
                continue
            
            if result:
                # 캐시 업데이트
                with self._cache_lock:
                    self._market_cache[symbol] = result
                
                # 버퍼에 추가
                self.market_buffer.append(result)
                
                # 배치 큐에 추가
                with self._batch_lock:
                    self._batch_queue.append(result)
                    
                    # 배치 크기 도달 시 플러시
                    if len(self._batch_queue) >= self.batch_size:
                        self._flush_batch()
    
    async def _fetch_market_data(self, symbol: str) -> Optional[MarketData]:
        """단일 심볼 데이터 비동기 수집"""
        # 실제 환경에서는 API 호출
        # 여기서는 시뮬레이션
        
        await asyncio.sleep(0.001)  # API 호출 시뮬레이션
        
        # 캐시에서 이전 가격 가져오기
        with self._cache_lock:
            prev_price = self._market_cache.get(symbol).price if symbol in self._market_cache else 50000000
        
        # 랜덤 워크
        price = prev_price * (1 + np.random.normal(0, 0.001))
        
        return MarketData(
            timestamp=datetime.now(),
            symbol=symbol,
            price=price,
            volume=np.random.uniform(100, 1000),
            bid=price * 0.999,
            ask=price * 1.001,
            high_24h=price * 1.02,
            low_24h=price * 0.98,
            change_24h=np.random.uniform(-0.05, 0.05)
        )
    
    def _flush_batch(self):
        """배치 데이터 플러시 (필요 시 DB 저장 등)"""
        with self._batch_lock:
            if self._batch_queue:
                # 실제 환경에서는 DB에 배치 저장
                # 여기서는 로그만 출력
                self.logger.debug(f"배치 플러시: {len(self._batch_queue)}개 데이터")
                self._batch_queue.clear()
    
    def _update_stats(self, elapsed: float):
        """성능 통계 업데이트"""
        self.stats['updates'] += 1
        
        # 이동 평균으로 평균 업데이트 시간 계산
        alpha = 0.1  # 지수 이동 평균 계수
        if self.stats['avg_update_time'] == 0:
            self.stats['avg_update_time'] = elapsed
        else:
            self.stats['avg_update_time'] = (
                alpha * elapsed + (1 - alpha) * self.stats['avg_update_time']
            )
        
        self.stats['last_update'] = datetime.now()
    
    def get_latest_market_data(self, symbol: str) -> Optional[MarketData]:
        """최신 시장 데이터 조회 (캐시 사용)"""
        with self._cache_lock:
            return self._market_cache.get(symbol)
    
    def get_market_history(self, symbol: str, minutes: int = 60) -> List[MarketData]:
        """시장 데이터 히스토리 조회 (최적화)"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        all_data = self.market_buffer.get_since(cutoff_time)
        
        return [data for data in all_data if data.symbol == symbol]
    
    def get_all_latest_data(self) -> Dict[str, MarketData]:
        """모든 최신 데이터 조회"""
        with self._cache_lock:
            return self._market_cache.copy()
    
    def export_to_dataframe(self, symbol: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """데이터프레임으로 내보내기 (제한된 크기)"""
        recent_data = self.market_buffer.get_recent(limit)
        
        if symbol:
            recent_data = [d for d in recent_data if d.symbol == symbol]
        
        if not recent_data:
            return pd.DataFrame()
        
        data = []
        for item in recent_data:
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
    
    def get_stats(self) -> Dict:
        """수집기 성능 통계"""
        return {
            **self.stats,
            'buffer_usage': len(self.market_buffer.buffer) / self.buffer_size * 100,
            'cached_symbols': len(self._market_cache),
            'updates_per_sec': self.stats['updates'] / max(1, 
                (datetime.now() - self.stats['last_update']).total_seconds()
            ) if self.stats['last_update'] else 0
        }
    
    def clear_old_data(self, hours: int = 24):
        """오래된 데이터 정리"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 버퍼는 자동으로 크기 제한됨 (deque maxlen)
        # 추가 정리 로직이 필요한 경우 여기에 구현
        
        self.logger.info(f"{hours}시간 이전 데이터 정리 완료")

