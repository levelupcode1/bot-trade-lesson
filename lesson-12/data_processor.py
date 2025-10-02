#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 처리 모듈
pandas와 numpy를 활용한 거래 데이터 로드 및 전처리
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """데이터 설정 클래스"""
    db_path: str = "data/trading.db"
    data_period_days: int = 30
    symbols: List[str] = None
    strategies: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        if self.strategies is None:
            self.strategies = ["volatility_breakout", "ma_crossover"]

class TradingDataProcessor:
    """거래 데이터 처리 클래스"""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.db_path = Path(config.db_path)
        self.logger = logging.getLogger(__name__)
        
        # 데이터 검증
        self._validate_database()
    
    def _validate_database(self) -> None:
        """데이터베이스 유효성 검사"""
        if not self.db_path.exists():
            self.logger.warning(f"데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
            self._create_sample_database()
    
    def _create_sample_database(self) -> None:
        """샘플 데이터베이스 생성"""
        self.logger.info("샘플 데이터베이스 생성 중...")
        
        # 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 거래 테이블 생성
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 가격 데이터 테이블 생성
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
            
            # 계좌 히스토리 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL NOT NULL,
                    date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 샘플 데이터 삽입
            self._insert_sample_data(cursor)
            conn.commit()
        
        self.logger.info("샘플 데이터베이스 생성 완료")
    
    def _insert_sample_data(self, cursor) -> None:
        """샘플 데이터 삽입"""
        import random
        from datetime import datetime, timedelta
        
        # 샘플 거래 데이터
        symbols = self.config.symbols
        strategies = self.config.strategies
        start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        
        # 거래 데이터 생성
        for i in range(100):
            trade_date = start_date + timedelta(
                days=random.randint(0, self.config.data_period_days),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            symbol = random.choice(symbols)
            side = random.choice(["BUY", "SELL"])
            strategy = random.choice(strategies)
            amount = round(random.uniform(0.001, 0.01), 6)
            price = round(random.uniform(30000000, 70000000), 0)
            
            cursor.execute("""
                INSERT INTO trades (order_id, symbol, side, amount, price, status, strategy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"order_{i:04d}",
                symbol,
                side,
                amount,
                price,
                "filled",
                strategy,
                trade_date
            ))
        
        # 샘플 가격 데이터
        for i in range(self.config.data_period_days * 24):
            timestamp = start_date + timedelta(hours=i)
            
            for symbol in symbols:
                price = round(random.uniform(30000000, 70000000), 0)
                volume = round(random.uniform(100, 1000), 2)
                
                cursor.execute("""
                    INSERT INTO price_data (symbol, price, volume, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (symbol, price, volume, timestamp))
        
        # 샘플 계좌 데이터
        initial_balance = 10000000  # 1000만원
        balance = initial_balance
        
        for i in range(self.config.data_period_days):
            date = start_date + timedelta(days=i)
            
            # 일일 수익률 시뮬레이션 (-5% ~ +5%)
            daily_return = random.uniform(-0.05, 0.05)
            balance = balance * (1 + daily_return)
            
            cursor.execute("""
                INSERT INTO account_history (balance, date)
                VALUES (?, ?)
            """, (round(balance, 2), date.date()))
    
    def load_trade_data(self, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """거래 데이터 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                
                if df.empty:
                    self.logger.warning("거래 데이터가 없습니다")
                    return df
                
                # 데이터 타입 변환
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['updated_at'] = pd.to_datetime(df['updated_at'])
                df['amount'] = pd.to_numeric(df['amount'])
                df['price'] = pd.to_numeric(df['price'])
                
                self.logger.info(f"거래 데이터 로드 완료: {len(df)}건")
                return df
                
        except Exception as e:
            self.logger.error(f"거래 데이터 로드 오류: {e}")
            return pd.DataFrame()
    
    def load_price_data(self, symbol: str, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """가격 데이터 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                
                df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
                
                if df.empty:
                    self.logger.warning(f"{symbol} 가격 데이터가 없습니다")
                    return df
                
                # 데이터 타입 변환
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['price'] = pd.to_numeric(df['price'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                self.logger.info(f"{symbol} 가격 데이터 로드 완료: {len(df)}건")
                return df
                
        except Exception as e:
            self.logger.error(f"{symbol} 가격 데이터 로드 오류: {e}")
            return pd.DataFrame()
    
    def load_account_history(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> pd.DataFrame:
        """계좌 히스토리 로드"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.config.data_period_days)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        balance,
                        date
                    FROM account_history 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date ASC
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date.date(), end_date.date()))
                
                if df.empty:
                    self.logger.warning("계좌 히스토리 데이터가 없습니다")
                    return df
                
                # 데이터 타입 변환
                df['date'] = pd.to_datetime(df['date'])
                df['balance'] = pd.to_numeric(df['balance'])
                
                self.logger.info(f"계좌 히스토리 로드 완료: {len(df)}건")
                return df
                
        except Exception as e:
            self.logger.error(f"계좌 히스토리 로드 오류: {e}")
            return pd.DataFrame()
    
    def preprocess_trade_data(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """거래 데이터 전처리"""
        if trades_df.empty:
            return trades_df
        
        df = trades_df.copy()
        
        # 거래 금액 계산
        df['trade_value'] = df['amount'] * df['price']
        
        # 시간 관련 컬럼 추가
        df['trade_date'] = df['created_at'].dt.date
        df['trade_hour'] = df['created_at'].dt.hour
        df['trade_day_of_week'] = df['created_at'].dt.day_name()
        
        # 매수/매도별 그룹화를 위한 처리
        buy_trades = df[df['side'] == 'BUY'].copy()
        sell_trades = df[df['side'] == 'SELL'].copy()
        
        # 매도 거래에 대한 손익 계산 (간단한 시뮬레이션)
        df['pnl'] = 0.0
        df['pnl_percentage'] = 0.0
        
        # 매도 거래의 경우 랜덤 손익 시뮬레이션
        sell_indices = df[df['side'] == 'SELL'].index
        for idx in sell_indices:
            # -10% ~ +10% 범위의 랜덤 수익률
            pnl_pct = np.random.uniform(-0.1, 0.1)
            trade_value = df.loc[idx, 'trade_value']
            df.loc[idx, 'pnl'] = trade_value * pnl_pct
            df.loc[idx, 'pnl_percentage'] = pnl_pct * 100
        
        # 보유 기간 계산 (매도 거래의 경우)
        df['holding_period'] = 0
        for idx in sell_indices:
            # 랜덤 보유 기간 (1분 ~ 1440분 = 24시간)
            holding_minutes = np.random.randint(1, 1440)
            df.loc[idx, 'holding_period'] = holding_minutes
        
        self.logger.info("거래 데이터 전처리 완료")
        return df
    
    def preprocess_price_data(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """가격 데이터 전처리"""
        if price_df.empty:
            return price_df
        
        df = price_df.copy()
        
        # 기술적 지표 계산
        df['price_change'] = df['price'].pct_change()
        df['price_change_pct'] = df['price_change'] * 100
        
        # 이동평균 계산
        df['ma_5'] = df['price'].rolling(window=5).mean()
        df['ma_20'] = df['price'].rolling(window=20).mean()
        
        # 변동성 계산
        df['volatility'] = df['price_change'].rolling(window=20).std() * np.sqrt(24) * 100
        
        # 거래량 이동평균
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        self.logger.info("가격 데이터 전처리 완료")
        return df
    
    def preprocess_account_data(self, account_df: pd.DataFrame) -> pd.DataFrame:
        """계좌 데이터 전처리"""
        if account_df.empty:
            return account_df
        
        df = account_df.copy()
        
        # 일일 수익률 계산
        df['daily_return'] = df['balance'].pct_change()
        df['daily_return_pct'] = df['daily_return'] * 100
        
        # 누적 수익률 계산
        initial_balance = df['balance'].iloc[0]
        df['cumulative_return'] = (df['balance'] - initial_balance) / initial_balance
        df['cumulative_return_pct'] = df['cumulative_return'] * 100
        
        # 최고점 대비 하락률 계산
        df['running_max'] = df['balance'].expanding().max()
        df['drawdown'] = (df['balance'] - df['running_max']) / df['running_max']
        df['drawdown_pct'] = df['drawdown'] * 100
        
        self.logger.info("계좌 데이터 전처리 완료")
        return df
    
    def get_analysis_summary(self, trades_df: pd.DataFrame, 
                           account_df: pd.DataFrame) -> Dict:
        """분석 데이터 요약"""
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
            }
        }
        
        return summary

# 사용 예시
if __name__ == "__main__":
    # 설정 생성
    config = DataConfig(
        db_path="data/trading.db",
        data_period_days=30,
        symbols=["KRW-BTC", "KRW-ETH"],
        strategies=["volatility_breakout", "ma_crossover"]
    )
    
    # 데이터 프로세서 생성
    processor = TradingDataProcessor(config)
    
    # 데이터 로드
    trades = processor.load_trade_data()
    account = processor.load_account_history()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data(trades)
        processed_account = processor.preprocess_account_data(account)
        
        # 요약 정보 출력
        summary = processor.get_analysis_summary(processed_trades, processed_account)
        print("=== 데이터 분석 요약 ===")
        print(f"분석 기간: {summary['period']['start_date']} ~ {summary['period']['end_date']}")
        print(f"총 거래 건수: {summary['trading']['total_trades']}건")
        print(f"거래 심볼: {summary['trading']['unique_symbols']}개")
        print(f"총 수익률: {summary['performance']['total_return']:.2f}%")
    else:
        print("데이터가 없습니다.")

