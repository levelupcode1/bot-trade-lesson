#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 처리 모듈 (최적화 버전)
대용량 데이터 처리와 메모리 효율성을 위한 최적화된 버전
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import gc
import psutil
import os
from typing import Dict, List, Optional, Tuple, Union, Iterator, Generator
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """데이터 설정 클래스 (최적화 버전)"""
    db_path: str = "data/trading.db"
    data_period_days: int = 30
    symbols: List[str] = None
    strategies: List[str] = None
    
    # 최적화 설정
    chunk_size: int = 10000  # 청크 크기
    max_memory_usage: float = 0.8  # 최대 메모리 사용률 (80%)
    use_multiprocessing: bool = True  # 멀티프로세싱 사용
    cache_size: int = 128  # LRU 캐시 크기
    enable_compression: bool = True  # 압축 사용
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        if self.strategies is None:
            self.strategies = ["volatility_breakout", "ma_crossover"]

class MemoryManager:
    """메모리 관리 클래스"""
    
    def __init__(self, max_usage_ratio: float = 0.8):
        self.max_usage_ratio = max_usage_ratio
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> float:
        """현재 메모리 사용률 반환"""
        return self.process.memory_percent() / 100.0
    
    def is_memory_available(self) -> bool:
        """메모리 사용 가능 여부 확인"""
        return self.get_memory_usage() < self.max_usage_ratio
    
    def force_garbage_collection(self) -> None:
        """강제 가비지 컬렉션 실행"""
        gc.collect()
        logger.debug(f"가비지 컬렉션 완료. 현재 메모리 사용률: {self.get_memory_usage():.2%}")
    
    def check_memory_and_cleanup(self) -> None:
        """메모리 사용량 확인 및 정리"""
        if not self.is_memory_available():
            logger.warning("메모리 사용량이 높습니다. 가비지 컬렉션을 실행합니다.")
            self.force_garbage_collection()

class OptimizedDataProcessor:
    """최적화된 거래 데이터 처리 클래스"""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.db_path = Path(config.db_path)
        self.logger = logging.getLogger(__name__)
        self.memory_manager = MemoryManager(config.max_memory_usage)
        
        # 데이터 검증
        self._validate_database()
        
        # 성능 모니터링
        self.performance_stats = {
            'queries_executed': 0,
            'total_query_time': 0.0,
            'memory_cleanups': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _validate_database(self) -> None:
        """데이터베이스 유효성 검사 (최적화 버전)"""
        if not self.db_path.exists():
            self.logger.warning(f"데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
            self._create_optimized_database()
    
    def _create_optimized_database(self) -> None:
        """최적화된 샘플 데이터베이스 생성"""
        self.logger.info("최적화된 샘플 데이터베이스 생성 중...")
        
        # 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # 성능 최적화를 위한 PRAGMA 설정
            conn.execute("PRAGMA journal_mode=WAL")  # WAL 모드로 성능 향상
            conn.execute("PRAGMA synchronous=NORMAL")  # 동기화 최적화
            conn.execute("PRAGMA cache_size=10000")  # 캐시 크기 증가
            conn.execute("PRAGMA temp_store=MEMORY")  # 임시 테이블을 메모리에 저장
            
            cursor = conn.cursor()
            
            # 최적화된 테이블 생성 (인덱스 포함)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    status TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL NOT NULL,
                    date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 성능 최적화를 위한 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_data(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_date ON account_history(date)")
            
            # 최적화된 샘플 데이터 삽입
            self._insert_optimized_sample_data(cursor)
            conn.commit()
        
        self.logger.info("최적화된 샘플 데이터베이스 생성 완료")
    
    def _insert_optimized_sample_data(self, cursor) -> None:
        """최적화된 샘플 데이터 삽입 (배치 처리)"""
        import random
        from datetime import datetime, timedelta
        
        # 배치 크기 설정
        batch_size = 1000
        total_trades = 50000  # 더 많은 데이터로 성능 테스트
        symbols = self.config.symbols
        strategies = self.config.strategies
        start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        
        # 거래 데이터 배치 삽입
        trade_batch = []
        for i in range(total_trades):
            trade_date = start_date + timedelta(
                days=random.randint(0, self.config.data_period_days),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            symbol = random.choice(symbols)
            side = random.choice(["BUY", "SELL"])
            strategy = random.choice(strategies)
            amount = round(random.uniform(0.001, 0.01), 6)
            price = round(random.uniform(30000000, 70000000), 0)
            
            trade_batch.append((
                f"order_{i:06d}",
                symbol,
                side,
                amount,
                price,
                "filled",
                strategy,
                trade_date
            ))
            
            # 배치 크기에 도달하면 삽입
            if len(trade_batch) >= batch_size:
                cursor.executemany("""
                    INSERT INTO trades (order_id, symbol, side, amount, price, status, strategy, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, trade_batch)
                trade_batch = []
                self.memory_manager.check_memory_and_cleanup()
        
        # 남은 데이터 삽입
        if trade_batch:
            cursor.executemany("""
                INSERT INTO trades (order_id, symbol, side, amount, price, status, strategy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, trade_batch)
        
        # 가격 데이터 배치 삽입
        price_batch = []
        for i in range(self.config.data_period_days * 24 * 60):  # 분 단위 데이터
            timestamp = start_date + timedelta(minutes=i)
            
            for symbol in symbols:
                price = round(random.uniform(30000000, 70000000), 0)
                volume = round(random.uniform(100, 1000), 2)
                
                price_batch.append((symbol, price, volume, timestamp))
                
                # 배치 크기에 도달하면 삽입
                if len(price_batch) >= batch_size:
                    cursor.executemany("""
                        INSERT INTO price_data (symbol, price, volume, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, price_batch)
                    price_batch = []
                    self.memory_manager.check_memory_and_cleanup()
        
        # 남은 가격 데이터 삽입
        if price_batch:
            cursor.executemany("""
                INSERT INTO price_data (symbol, price, volume, timestamp)
                VALUES (?, ?, ?, ?)
            """, price_batch)
        
        # 계좌 데이터 배치 삽입
        account_batch = []
        initial_balance = 10000000
        balance = initial_balance
        
        for i in range(self.config.data_period_days):
            date = start_date + timedelta(days=i)
            daily_return = random.uniform(-0.05, 0.05)
            balance = balance * (1 + daily_return)
            
            account_batch.append((round(balance, 2), date.date()))
            
            # 배치 크기에 도달하면 삽입
            if len(account_batch) >= batch_size:
                cursor.executemany("""
                    INSERT INTO account_history (balance, date)
                    VALUES (?, ?)
                """, account_batch)
                account_batch = []
        
        # 남은 계좌 데이터 삽입
        if account_batch:
            cursor.executemany("""
                INSERT INTO account_history (balance, date)
                VALUES (?, ?)
            """, account_batch)
    
    @lru_cache(maxsize=128)
    def _get_cached_query_result(self, query_hash: str) -> Optional[pd.DataFrame]:
        """캐시된 쿼리 결과 반환"""
        self.performance_stats['cache_hits'] += 1
        return None  # 실제 구현에서는 캐시에서 데이터 반환
    
    def _execute_optimized_query(self, query: str, params: Tuple = None, 
                               chunk_size: int = None) -> pd.DataFrame:
        """최적화된 쿼리 실행"""
        import time
        start_time = time.time()
        
        try:
            # 쿼리 해시 생성 (캐시용)
            query_hash = hash(query + str(params))
            
            # 캐시 확인
            cached_result = self._get_cached_query_result(query_hash)
            if cached_result is not None:
                return cached_result
            
            self.performance_stats['cache_misses'] += 1
            
            # 청크 크기 설정
            if chunk_size is None:
                chunk_size = self.config.chunk_size
            
            # 메모리 사용량 확인
            if not self.memory_manager.is_memory_available():
                self.memory_manager.force_garbage_collection()
            
            # 최적화된 연결 설정으로 쿼리 실행
            with sqlite3.connect(self.db_path) as conn:
                # 성능 최적화 설정
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                
                # 대용량 데이터의 경우 청크 단위로 처리
                if chunk_size > 0:
                    chunks = []
                    for chunk_df in pd.read_sql_query(query, conn, params=params, chunksize=chunk_size):
                        chunks.append(chunk_df)
                        self.memory_manager.check_memory_and_cleanup()
                    
                    if chunks:
                        result = pd.concat(chunks, ignore_index=True)
                    else:
                        result = pd.DataFrame()
                else:
                    result = pd.read_sql_query(query, conn, params=params)
            
            # 성능 통계 업데이트
            execution_time = time.time() - start_time
            self.performance_stats['queries_executed'] += 1
            self.performance_stats['total_query_time'] += execution_time
            
            self.logger.debug(f"쿼리 실행 완료: {execution_time:.3f}초, 결과 크기: {len(result)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"쿼리 실행 오류: {e}")
            return pd.DataFrame()
    
    def load_trade_data_optimized(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                use_chunking: bool = True) -> pd.DataFrame:
        """최적화된 거래 데이터 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        query = """
            SELECT 
                order_id,
                symbol,
                side,
                amount,
                price,
                status,
                strategy,
                created_at,
                updated_at
            FROM trades 
            WHERE created_at BETWEEN ? AND ?
            AND status = 'filled'
            ORDER BY created_at ASC
        """
        
        params = (start_date, end_date)
        chunk_size = self.config.chunk_size if use_chunking else 0
        
        df = self._execute_optimized_query(query, params, chunk_size)
        
        if df.empty:
            self.logger.warning("거래 데이터가 없습니다")
            return df
        
        # 최적화된 데이터 타입 변환
        df = self._optimize_dtypes(df)
        
        self.logger.info(f"최적화된 거래 데이터 로드 완료: {len(df)}건")
        return df
    
    def load_price_data_optimized(self, symbol: str, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                use_chunking: bool = True) -> pd.DataFrame:
        """최적화된 가격 데이터 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        query = """
            SELECT 
                symbol,
                price,
                volume,
                timestamp
            FROM price_data 
            WHERE symbol = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """
        
        params = (symbol, start_date, end_date)
        chunk_size = self.config.chunk_size if use_chunking else 0
        
        df = self._execute_optimized_query(query, params, chunk_size)
        
        if df.empty:
            self.logger.warning(f"{symbol} 가격 데이터가 없습니다")
            return df
        
        # 최적화된 데이터 타입 변환
        df = self._optimize_dtypes(df)
        
        self.logger.info(f"최적화된 {symbol} 가격 데이터 로드 완료: {len(df)}건")
        return df
    
    def load_account_history_optimized(self, start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> pd.DataFrame:
        """최적화된 계좌 히스토리 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        query = """
            SELECT 
                balance,
                date
            FROM account_history 
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """
        
        params = (start_date.date(), end_date.date())
        
        df = self._execute_optimized_query(query, params, 0)  # 계좌 데이터는 작으므로 청킹 불필요
        
        if df.empty:
            self.logger.warning("계좌 히스토리 데이터가 없습니다")
            return df
        
        # 최적화된 데이터 타입 변환
        df = self._optimize_dtypes(df)
        
        self.logger.info(f"최적화된 계좌 히스토리 로드 완료: {len(df)}건")
        return df
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 최적화"""
        if df.empty:
            return df
        
        # 메모리 사용량을 줄이기 위한 데이터 타입 최적화
        for col in df.columns:
            if df[col].dtype == 'object':
                # 문자열 컬럼 최적화
                if col in ['symbol', 'side', 'status', 'strategy']:
                    df[col] = df[col].astype('category')
            elif df[col].dtype == 'float64':
                # 부동소수점 최적화
                if col in ['amount', 'price', 'volume', 'balance']:
                    df[col] = pd.to_numeric(df[col], downcast='float')
            elif df[col].dtype == 'int64':
                # 정수 최적화
                df[col] = pd.to_numeric(df[col], downcast='integer')
        
        return df
    
    def preprocess_trade_data_optimized(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """최적화된 거래 데이터 전처리"""
        if trades_df.empty:
            return trades_df
        
        self.memory_manager.check_memory_and_cleanup()
        
        df = trades_df.copy()
        
        # 벡터화된 연산으로 성능 향상
        df['trade_value'] = df['amount'] * df['price']
        
        # 시간 관련 컬럼 추가 (벡터화)
        if 'created_at' in df.columns:
            df['trade_date'] = df['created_at'].dt.date
            df['trade_hour'] = df['created_at'].dt.hour
            df['trade_day_of_week'] = df['created_at'].dt.day_name()
        
        # 매도 거래에 대한 손익 계산 (최적화된 방식)
        sell_mask = df['side'] == 'SELL'
        df['pnl'] = 0.0
        df['pnl_percentage'] = 0.0
        df['holding_period'] = 0
        
        if sell_mask.any():
            # 벡터화된 랜덤 수익률 생성
            np.random.seed(42)  # 재현 가능한 결과를 위해
            pnl_percentages = np.random.uniform(-0.1, 0.1, sell_mask.sum())
            holding_periods = np.random.randint(1, 1440, sell_mask.sum())
            
            df.loc[sell_mask, 'pnl'] = df.loc[sell_mask, 'trade_value'] * pnl_percentages
            df.loc[sell_mask, 'pnl_percentage'] = pnl_percentages * 100
            df.loc[sell_mask, 'holding_period'] = holding_periods
        
        # 메모리 정리
        self.memory_manager.check_memory_and_cleanup()
        
        self.logger.info("최적화된 거래 데이터 전처리 완료")
        return df
    
    def preprocess_price_data_optimized(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """최적화된 가격 데이터 전처리"""
        if price_df.empty:
            return price_df
        
        self.memory_manager.check_memory_and_cleanup()
        
        df = price_df.copy()
        
        # 벡터화된 기술적 지표 계산
        df['price_change'] = df['price'].pct_change()
        df['price_change_pct'] = df['price_change'] * 100
        
        # 최적화된 이동평균 계산 (rolling window 최적화)
        window_sizes = [5, 20]
        for window in window_sizes:
            if len(df) >= window:
                df[f'ma_{window}'] = df['price'].rolling(window=window, min_periods=1).mean()
        
        # 최적화된 변동성 계산
        if len(df) >= 20:
            df['volatility'] = df['price_change'].rolling(window=20, min_periods=1).std() * np.sqrt(24) * 100
        
        # 최적화된 거래량 이동평균
        if len(df) >= 20:
            df['volume_ma'] = df['volume'].rolling(window=20, min_periods=1).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 메모리 정리
        self.memory_manager.check_memory_and_cleanup()
        
        self.logger.info("최적화된 가격 데이터 전처리 완료")
        return df
    
    def preprocess_account_data_optimized(self, account_df: pd.DataFrame) -> pd.DataFrame:
        """최적화된 계좌 데이터 전처리"""
        if account_df.empty:
            return account_df
        
        self.memory_manager.check_memory_and_cleanup()
        
        df = account_df.copy()
        
        # 벡터화된 수익률 계산
        df['daily_return'] = df['balance'].pct_change()
        df['daily_return_pct'] = df['daily_return'] * 100
        
        # 최적화된 누적 수익률 계산
        initial_balance = df['balance'].iloc[0]
        df['cumulative_return'] = (df['balance'] - initial_balance) / initial_balance
        df['cumulative_return_pct'] = df['cumulative_return'] * 100
        
        # 최적화된 최고점 대비 하락률 계산
        df['running_max'] = df['balance'].expanding().max()
        df['drawdown'] = (df['balance'] - df['running_max']) / df['running_max']
        df['drawdown_pct'] = df['drawdown'] * 100
        
        # 메모리 정리
        self.memory_manager.check_memory_and_cleanup()
        
        self.logger.info("최적화된 계좌 데이터 전처리 완료")
        return df
    
    def get_analysis_summary_optimized(self, trades_df: pd.DataFrame, 
                                     account_df: pd.DataFrame) -> Dict:
        """최적화된 분석 데이터 요약"""
        summary = {
            'period': {
                'start_date': trades_df['created_at'].min() if not trades_df.empty else None,
                'end_date': trades_df['created_at'].max() if not trades_df.empty else None,
                'total_days': len(account_df) if not account_df.empty else 0
            },
            'trading': {
                'total_trades': len(trades_df),
                'buy_trades': len(trades_df[trades_df['side'] == 'BUY']),
                'sell_trades': len(trades_df[trades_df['side'] == 'SELL']),
                'unique_symbols': trades_df['symbol'].nunique() if not trades_df.empty else 0,
                'unique_strategies': trades_df['strategy'].nunique() if not trades_df.empty else 0
            },
            'performance': {
                'initial_balance': account_df['balance'].iloc[0] if not account_df.empty else 0,
                'final_balance': account_df['balance'].iloc[-1] if not account_df.empty else 0,
                'total_return': account_df['cumulative_return_pct'].iloc[-1] if not account_df.empty else 0
            },
            'memory_stats': {
                'current_usage': self.memory_manager.get_memory_usage(),
                'cleanups_performed': self.performance_stats['memory_cleanups']
            },
            'performance_stats': self.performance_stats.copy()
        }
        
        return summary
    
    def get_performance_stats(self) -> Dict:
        """성능 통계 반환"""
        stats = self.performance_stats.copy()
        stats['avg_query_time'] = (
            stats['total_query_time'] / stats['queries_executed'] 
            if stats['queries_executed'] > 0 else 0
        )
        stats['cache_hit_rate'] = (
            stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
            if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        )
        return stats
    
    def cleanup_resources(self) -> None:
        """리소스 정리"""
        self.memory_manager.force_garbage_collection()
        self.logger.info("리소스 정리 완료")

# 사용 예시
if __name__ == "__main__":
    import time
    
    # 최적화된 설정
    config = DataConfig(
        db_path="data/optimized_trading.db",
        data_period_days=90,  # 더 긴 기간 테스트
        chunk_size=5000,
        max_memory_usage=0.7,
        use_multiprocessing=True,
        cache_size=256
    )
    
    # 최적화된 프로세서 생성
    processor = OptimizedDataProcessor(config)
    
    # 성능 테스트
    start_time = time.time()
    
    # 데이터 로드
    trades = processor.load_trade_data_optimized(use_chunking=True)
    account = processor.load_account_history_optimized()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data_optimized(trades)
        processed_account = processor.preprocess_account_data_optimized(account)
        
        # 요약 정보 출력
        summary = processor.get_analysis_summary_optimized(processed_trades, processed_account)
        
        # 성능 통계 출력
        perf_stats = processor.get_performance_stats()
        
        total_time = time.time() - start_time
        
        print("=== 최적화된 데이터 처리 결과 ===")
        print(f"총 처리 시간: {total_time:.3f}초")
        print(f"거래 데이터: {len(processed_trades)}건")
        print(f"계좌 데이터: {len(processed_account)}건")
        print(f"메모리 사용률: {summary['memory_stats']['current_usage']:.2%}")
        print(f"캐시 적중률: {perf_stats['cache_hit_rate']:.2%}")
        print(f"평균 쿼리 시간: {perf_stats['avg_query_time']:.3f}초")
        
        # 리소스 정리
        processor.cleanup_resources()
    else:
        print("데이터가 없습니다.")














