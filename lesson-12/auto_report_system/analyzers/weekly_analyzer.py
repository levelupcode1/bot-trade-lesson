#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주간 분석기
"""

import pandas as pd
from typing import Dict, Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from performance_metrics import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class WeeklyAnalyzer:
    """주간 분석 클래스"""
    
    def __init__(self):
        self.perf_analyzer = PerformanceAnalyzer()
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """주간 데이터 분석"""
        trades = data.get('trades', pd.DataFrame())
        account = data.get('account_history', pd.DataFrame())
        
        if trades.empty and account.empty:
            return self._empty_analysis()
        
        try:
            if not trades.empty and not account.empty:
                metrics = self.perf_analyzer.calculate_comprehensive_metrics(trades, account)
                
                # 전략별 분석
                strategy_analysis = {}
                if 'strategy' in trades.columns:
                    strategy_analysis = self.perf_analyzer.analyze_by_strategy(trades, account)
                
                # 일별 분석
                daily_returns = self._calculate_daily_returns(account)
                
                return {
                    'total_return': metrics.total_return,
                    'total_trades': metrics.total_trades,
                    'win_rate': metrics.win_rate,
                    'max_drawdown': metrics.max_drawdown,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'profit_factor': metrics.profit_factor,
                    
                    # 주간 특화
                    'daily_returns': daily_returns,
                    'best_day': max(daily_returns.items(), key=lambda x: x[1])[0] if daily_returns else None,
                    'worst_day': min(daily_returns.items(), key=lambda x: x[1])[0] if daily_returns else None,
                    'strategy_analysis': strategy_analysis,
                    'weekly_volatility': self._calculate_volatility(account)
                }
            else:
                return self._empty_analysis()
                
        except Exception as e:
            logger.error(f"주간 분석 오류: {e}", exc_info=True)
            return self._empty_analysis()
    
    def _calculate_daily_returns(self, account: pd.DataFrame) -> Dict[str, float]:
        """일별 수익률 계산"""
        if account.empty or 'timestamp' not in account.columns:
            return {}
        
        account['date'] = pd.to_datetime(account['timestamp']).dt.date
        daily = account.groupby('date')['total_value'].last()
        daily_returns = daily.pct_change() * 100
        
        return {str(date): ret for date, ret in daily_returns.items() if not pd.isna(ret)}
    
    def _calculate_volatility(self, account: pd.DataFrame) -> float:
        """변동성 계산"""
        if account.empty or len(account) < 2:
            return 0.0
        
        returns = account['total_value'].pct_change().dropna()
        return float(returns.std() * 100) if len(returns) > 0 else 0.0
    
    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            'total_return': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'profit_factor': 0.0,
            'daily_returns': {},
            'best_day': None,
            'worst_day': None,
            'strategy_analysis': {},
            'weekly_volatility': 0.0
        }

