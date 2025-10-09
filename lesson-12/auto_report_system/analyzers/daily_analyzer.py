#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일간 분석기
하루 동안의 거래 데이터 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
import sys
from pathlib import Path

# 상위 모듈 임포트를 위한 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from performance_metrics import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class DailyAnalyzer:
    """일간 분석 클래스"""
    
    def __init__(self):
        self.perf_analyzer = PerformanceAnalyzer()
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        일간 데이터 분석
        
        Args:
            data: 수집된 데이터
            
        Returns:
            분석 결과
        """
        trades = data.get('trades', pd.DataFrame())
        account = data.get('account_history', pd.DataFrame())
        
        if trades.empty and account.empty:
            return self._empty_analysis()
        
        try:
            # 기본 성과 분석
            if not trades.empty and not account.empty:
                metrics = self.perf_analyzer.calculate_comprehensive_metrics(trades, account)
                
                return {
                    'total_return': metrics.total_return,
                    'daily_return': metrics.total_return,  # 일간이므로 동일
                    'total_trades': metrics.total_trades,
                    'winning_trades': metrics.winning_trades,
                    'losing_trades': metrics.losing_trades,
                    'win_rate': metrics.win_rate,
                    'max_drawdown': metrics.max_drawdown,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'profit_factor': metrics.profit_factor,
                    'avg_holding_period': metrics.avg_holding_period,
                    
                    # 일간 특화 지표
                    'today_pnl': self._calculate_daily_pnl(account),
                    'active_hours': self._analyze_active_hours(trades),
                    'symbol_breakdown': self._analyze_symbols(trades),
                }
            else:
                return self._empty_analysis()
                
        except Exception as e:
            logger.error(f"일간 분석 오류: {e}", exc_info=True)
            return self._empty_analysis()
    
    def _calculate_daily_pnl(self, account: pd.DataFrame) -> float:
        """일간 손익 계산"""
        if account.empty or len(account) < 2:
            return 0.0
        
        start_value = account.iloc[0]['total_value']
        end_value = account.iloc[-1]['total_value']
        
        return ((end_value - start_value) / start_value * 100) if start_value > 0 else 0.0
    
    def _analyze_active_hours(self, trades: pd.DataFrame) -> Dict[str, int]:
        """활동 시간대 분석"""
        if trades.empty or 'timestamp' not in trades.columns:
            return {}
        
        trades['hour'] = pd.to_datetime(trades['timestamp']).dt.hour
        hourly_counts = trades['hour'].value_counts().to_dict()
        
        return {f"{hour}시": count for hour, count in sorted(hourly_counts.items())}
    
    def _analyze_symbols(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """코인별 분석"""
        if trades.empty or 'symbol' not in trades.columns:
            return {}
        
        symbol_stats = {}
        
        for symbol in trades['symbol'].unique():
            symbol_trades = trades[trades['symbol'] == symbol]
            
            if 'profit_loss' in symbol_trades.columns:
                total_pnl = symbol_trades['profit_loss'].sum()
                avg_pnl = symbol_trades['profit_loss'].mean()
            else:
                total_pnl = 0
                avg_pnl = 0
            
            symbol_stats[symbol] = {
                'trades': len(symbol_trades),
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl
            }
        
        return symbol_stats
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """빈 분석 결과"""
        return {
            'total_return': 0.0,
            'daily_return': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'profit_factor': 0.0,
            'avg_holding_period': 0.0,
            'today_pnl': 0.0,
            'active_hours': {},
            'symbol_breakdown': {}
        }

