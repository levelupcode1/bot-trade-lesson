#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
월간 분석기
"""

import pandas as pd
from typing import Dict, Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from performance_metrics import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class MonthlyAnalyzer:
    """월간 분석 클래스"""
    
    def __init__(self):
        self.perf_analyzer = PerformanceAnalyzer()
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """월간 데이터 분석"""
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
                
                # 심볼별 분석
                symbol_analysis = self.perf_analyzer.analyze_by_symbol(trades, account)
                
                # 주별 분석
                weekly_returns = self._calculate_weekly_returns(account)
                
                return {
                    'total_return': metrics.total_return,
                    'annualized_return': metrics.annualized_return,
                    'total_trades': metrics.total_trades,
                    'win_rate': metrics.win_rate,
                    'max_drawdown': metrics.max_drawdown,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'calmar_ratio': metrics.calmar_ratio,
                    'profit_factor': metrics.profit_factor,
                    
                    # 월간 특화
                    'weekly_returns': weekly_returns,
                    'strategy_analysis': strategy_analysis,
                    'symbol_analysis': symbol_analysis,
                    'monthly_volatility': self._calculate_volatility(account),
                    'consistency_score': self._calculate_consistency(weekly_returns)
                }
            else:
                return self._empty_analysis()
                
        except Exception as e:
            logger.error(f"월간 분석 오류: {e}", exc_info=True)
            return self._empty_analysis()
    
    def _calculate_weekly_returns(self, account: pd.DataFrame) -> Dict[str, float]:
        """주별 수익률 계산"""
        if account.empty or 'timestamp' not in account.columns:
            return {}
        
        account['week'] = pd.to_datetime(account['timestamp']).dt.to_period('W')
        weekly = account.groupby('week')['total_value'].last()
        weekly_returns = weekly.pct_change() * 100
        
        return {str(week): ret for week, ret in weekly_returns.items() if not pd.isna(ret)}
    
    def _calculate_volatility(self, account: pd.DataFrame) -> float:
        """변동성 계산"""
        if account.empty or len(account) < 2:
            return 0.0
        
        returns = account['total_value'].pct_change().dropna()
        return float(returns.std() * 100) if len(returns) > 0 else 0.0
    
    def _calculate_consistency(self, weekly_returns: Dict[str, float]) -> float:
        """일관성 점수 계산 (0-100)"""
        if not weekly_returns:
            return 0.0
        
        returns = list(weekly_returns.values())
        positive_weeks = sum(1 for r in returns if r > 0)
        
        return (positive_weeks / len(returns) * 100) if returns else 0.0
    
    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'profit_factor': 0.0,
            'weekly_returns': {},
            'strategy_analysis': {},
            'symbol_analysis': {},
            'monthly_volatility': 0.0,
            'consistency_score': 0.0
        }

