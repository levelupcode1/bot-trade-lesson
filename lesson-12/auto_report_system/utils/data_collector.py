#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 수집 모듈
거래 데이터베이스에서 필요한 데이터를 수집
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataCollector:
    """데이터 수집 클래스"""
    
    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: 데이터베이스 경로 (기본: lesson-12/data/trading.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "trading.db"
        
        self.db_path = str(db_path)
        logger.info(f"데이터 수집기 초기화: {self.db_path}")
    
    def collect(self, start_date: datetime, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        지정된 기간의 데이터 수집
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜 (기본: 현재)
            
        Returns:
            수집된 데이터 딕셔너리
        """
        if end_date is None:
            end_date = datetime.now()
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 거래 데이터 수집
            trades_df = self._collect_trades(conn, start_date, end_date)
            
            # 계좌 내역 수집
            account_df = self._collect_account_history(conn, start_date, end_date)
            
            # 주문 내역 수집
            orders_df = self._collect_orders(conn, start_date, end_date)
            
            conn.close()
            
            logger.info(f"데이터 수집 완료: 거래 {len(trades_df)}건, 계좌 {len(account_df)}건")
            
            return {
                'trades': trades_df,
                'account_history': account_df,
                'orders': orders_df,
                'period': {
                    'start': start_date,
                    'end': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"데이터 수집 오류: {e}", exc_info=True)
            return {
                'trades': pd.DataFrame(),
                'account_history': pd.DataFrame(),
                'orders': pd.DataFrame(),
                'period': {'start': start_date, 'end': end_date}
            }
    
    def _collect_trades(self, conn: sqlite3.Connection, 
                       start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """거래 내역 수집"""
        query = """
        SELECT * FROM trades 
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(start_date.isoformat(), end_date.isoformat())
            )
            
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        except Exception as e:
            logger.error(f"거래 데이터 수집 오류: {e}")
            return pd.DataFrame()
    
    def _collect_account_history(self, conn: sqlite3.Connection,
                                 start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """계좌 내역 수집"""
        query = """
        SELECT * FROM account_history 
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(start_date.isoformat(), end_date.isoformat())
            )
            
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        except Exception as e:
            logger.error(f"계좌 데이터 수집 오류: {e}")
            return pd.DataFrame()
    
    def _collect_orders(self, conn: sqlite3.Connection,
                       start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """주문 내역 수집"""
        query = """
        SELECT * FROM orders 
        WHERE created_at >= ? AND created_at <= ?
        ORDER BY created_at
        """
        
        try:
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(start_date.isoformat(), end_date.isoformat())
            )
            
            if not df.empty and 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            
            return df
        except Exception as e:
            logger.warning(f"주문 데이터 수집 오류 (테이블이 없을 수 있음): {e}")
            return pd.DataFrame()
    
    def collect_daily(self) -> Dict[str, Any]:
        """일간 데이터 수집"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        return self.collect(start_date, end_date)
    
    def collect_weekly(self) -> Dict[str, Any]:
        """주간 데이터 수집"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=1)
        return self.collect(start_date, end_date)
    
    def collect_monthly(self) -> Dict[str, Any]:
        """월간 데이터 수집"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return self.collect(start_date, end_date)
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """최신 메트릭 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 최신 계좌 정보
            query = "SELECT * FROM account_history ORDER BY timestamp DESC LIMIT 1"
            latest_account = pd.read_sql_query(query, conn)
            
            # 오늘의 거래 수
            today = datetime.now().date()
            query = f"""
            SELECT COUNT(*) as count FROM trades 
            WHERE date(timestamp) = '{today}'
            """
            today_trades = pd.read_sql_query(query, conn)
            
            conn.close()
            
            return {
                'balance': latest_account['balance'].iloc[0] if not latest_account.empty else 0,
                'total_value': latest_account['total_value'].iloc[0] if not latest_account.empty else 0,
                'today_trades': today_trades['count'].iloc[0] if not today_trades.empty else 0
            }
            
        except Exception as e:
            logger.error(f"최신 메트릭 조회 오류: {e}")
            return {'balance': 0, 'total_value': 0, 'today_trades': 0}

