#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화된 성능 추적기

최적화 포인트:
1. 증분 계산으로 중복 계산 제거
2. NumPy 벡터화로 계산 속도 향상
3. 캐싱으로 메트릭 재계산 최소화
4. 지연 평가로 필요한 경우에만 계산
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from functools import lru_cache
from collections import OrderedDict


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    timestamp: datetime
    total_return: float
    daily_return: float
    monthly_return: float
    annual_return: float
    volatility: float
    max_drawdown: float
    current_drawdown: float
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    current_positions: int
    total_exposure: float
    leverage: float


class IncrementalStats:
    """증분 통계 계산기"""
    
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0  # 분산 계산용
        self.min_val = float('inf')
        self.max_val = float('-inf')
    
    def update(self, value: float):
        """새 값으로 통계 업데이트 (Welford's algorithm)"""
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.m2 += delta * delta2
        
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)
    
    @property
    def variance(self) -> float:
        """분산"""
        return self.m2 / self.n if self.n > 1 else 0.0
    
    @property
    def std(self) -> float:
        """표준편차"""
        return np.sqrt(self.variance)


class OptimizedPerformanceTracker:
    """최적화된 성능 추적기"""
    
    def __init__(self, initial_capital: float = 1_000_000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # 증분 통계
        self.returns_stats = IncrementalStats()
        self.negative_returns_stats = IncrementalStats()
        
        # 거래 기록 (제한된 크기의 OrderedDict)
        self._max_trades = 10000
        self.trades: OrderedDict = OrderedDict()
        
        # 자산 곡선 (NumPy 배열로 효율적 관리)
        self._max_equity_points = 10000
        self._equity_array = np.zeros(self._max_equity_points)
        self._equity_timestamps = np.zeros(self._max_equity_points, dtype='datetime64[ns]')
        self._equity_index = 0
        
        # 캐시된 메트릭
        self._cached_metrics: Optional[PerformanceMetrics] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 1  # 1초 TTL
        
        # 최대 낙폭 추적 (증분)
        self._running_max = initial_capital
        self._current_drawdown = 0.0
        self._max_drawdown = 0.0
        
        self.logger.info(f"최적화된 성능 추적기 초기화: 초기자본 {initial_capital:,.0f}원")
    
    def update(self, equity: float) -> PerformanceMetrics:
        """성능 지표 업데이트 (증분 계산)"""
        timestamp = datetime.now()
        
        # 자산 곡선 업데이트 (링 버퍼)
        idx = self._equity_index % self._max_equity_points
        self._equity_array[idx] = equity
        self._equity_timestamps[idx] = np.datetime64(timestamp)
        self._equity_index += 1
        
        # 수익률 계산
        if self._equity_index > 1:
            prev_idx = (self._equity_index - 2) % self._max_equity_points
            prev_equity = self._equity_array[prev_idx]
            
            if prev_equity > 0:
                return_pct = (equity - prev_equity) / prev_equity
                
                # 증분 통계 업데이트
                self.returns_stats.update(return_pct)
                
                if return_pct < 0:
                    self.negative_returns_stats.update(return_pct)
        
        # 낙폭 증분 계산
        if equity > self._running_max:
            self._running_max = equity
            self._current_drawdown = 0.0
        else:
            self._current_drawdown = (equity - self._running_max) / self._running_max
            self._max_drawdown = min(self._max_drawdown, self._current_drawdown)
        
        # 캐시 확인
        if self._is_cache_valid():
            return self._cached_metrics
        
        # 메트릭 계산
        metrics = self._calculate_metrics_fast(timestamp, equity)
        
        # 캐시 업데이트
        self._cached_metrics = metrics
        self._cache_timestamp = timestamp
        
        return metrics
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cached_metrics or not self._cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl
    
    def _calculate_metrics_fast(self, timestamp: datetime, equity: float) -> PerformanceMetrics:
        """빠른 메트릭 계산 (벡터화)"""
        # 수익률 계산 (증분 통계 사용)
        total_return = (equity / self.initial_capital) - 1
        
        # 시간별 수익률 추정
        if self.returns_stats.n > 0:
            avg_return = self.returns_stats.mean
            
            # 복리 수익률로 변환
            daily_return = (1 + avg_return) ** 24 - 1  # 24시간
            monthly_return = (1 + avg_return) ** (24 * 30) - 1
            annual_return = (1 + avg_return) ** (24 * 365) - 1
        else:
            daily_return = monthly_return = annual_return = 0.0
        
        # 변동성 (증분 통계 사용)
        volatility = self.returns_stats.std * np.sqrt(24 * 365) if self.returns_stats.n > 1 else 0.0
        
        # VaR / CVaR (NumPy 벡터화)
        if self._equity_index > 20:
            # 최근 데이터만 사용
            n_points = min(self._equity_index, self._max_equity_points)
            returns = np.diff(self._equity_array[:n_points]) / self._equity_array[:n_points-1]
            returns = returns[~np.isnan(returns)]  # NaN 제거
            
            if len(returns) > 0:
                var_95 = np.percentile(returns, 5)
                cvar_95 = returns[returns <= var_95].mean() if np.any(returns <= var_95) else 0.0
            else:
                var_95 = cvar_95 = 0.0
        else:
            var_95 = cvar_95 = 0.0
        
        # 효율성 비율
        if volatility > 0:
            sharpe_ratio = (annual_return - 0.02) / volatility
        else:
            sharpe_ratio = 0.0
        
        # 소르티노 비율 (음수 수익률 표준편차 사용)
        if self.negative_returns_stats.n > 0:
            downside_std = self.negative_returns_stats.std * np.sqrt(24 * 365)
            sortino_ratio = (annual_return - 0.02) / downside_std if downside_std > 0 else 0.0
        else:
            sortino_ratio = 0.0
        
        # 칼마 비율
        if self._max_drawdown < 0:
            calmar_ratio = annual_return / abs(self._max_drawdown)
        else:
            calmar_ratio = 0.0
        
        # 거래 통계 (캐시된 값 사용)
        trade_stats = self._calculate_trade_stats_fast()
        
        return PerformanceMetrics(
            timestamp=timestamp,
            total_return=total_return,
            daily_return=daily_return,
            monthly_return=monthly_return,
            annual_return=annual_return,
            volatility=volatility,
            max_drawdown=self._max_drawdown,
            current_drawdown=self._current_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            **trade_stats
        )
    
    @lru_cache(maxsize=1)
    def _calculate_trade_stats_fast(self) -> Dict:
        """빠른 거래 통계 계산 (캐시 사용)"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'current_positions': 0,
                'total_exposure': 0.0,
                'leverage': 1.0
            }
        
        # NumPy 배열로 변환하여 벡터화 계산
        pnls = np.array([t.get('pnl', 0) for t in self.trades.values()])
        
        total_trades = len(pnls)
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]
        
        win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
        
        total_wins = wins.sum() if len(wins) > 0 else 0.0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0.0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'current_positions': np.random.randint(0, 3),  # 시뮬레이션
            'total_exposure': np.random.uniform(0, 0.5) * self.current_capital,
            'leverage': 1.0
        }
    
    def add_trade(self, trade_id: str, trade: Dict):
        """거래 추가 (제한된 크기)"""
        self.trades[trade_id] = trade
        
        # 크기 제한
        if len(self.trades) > self._max_trades:
            self.trades.popitem(last=False)  # FIFO
        
        # PnL 업데이트
        if 'pnl' in trade:
            self.current_capital += trade['pnl']
        
        # 캐시 무효화
        self._calculate_trade_stats_fast.cache_clear()
    
    def get_equity_curve(self, hours: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """자산 곡선 조회 (NumPy 배열 반환)"""
        cutoff_time = np.datetime64(datetime.now() - timedelta(hours=hours))
        
        n_points = min(self._equity_index, self._max_equity_points)
        
        # 시간 필터링
        mask = self._equity_timestamps[:n_points] >= cutoff_time
        
        return (
            self._equity_timestamps[:n_points][mask],
            self._equity_array[:n_points][mask]
        )
    
    def get_performance_summary(self) -> Dict:
        """성능 요약 (지연 평가)"""
        if not self._cached_metrics:
            return {}
        
        m = self._cached_metrics
        
        return {
            'timestamp': m.timestamp.isoformat(),
            'returns': {
                'total': f"{m.total_return:.2%}",
                'daily': f"{m.daily_return:.2%}",
                'monthly': f"{m.monthly_return:.2%}",
                'annual': f"{m.annual_return:.2%}"
            },
            'risk': {
                'volatility': f"{m.volatility:.2%}",
                'max_drawdown': f"{m.max_drawdown:.2%}",
                'current_drawdown': f"{m.current_drawdown:.2%}",
                'var_95': f"{m.var_95:.2%}",
                'cvar_95': f"{m.cvar_95:.2%}"
            },
            'efficiency': {
                'sharpe_ratio': f"{m.sharpe_ratio:.2f}",
                'sortino_ratio': f"{m.sortino_ratio:.2f}",
                'calmar_ratio': f"{m.calmar_ratio:.2f}"
            },
            'trading': {
                'total_trades': m.total_trades,
                'win_rate': f"{m.win_rate:.2%}",
                'profit_factor': f"{m.profit_factor:.2f}",
                'avg_win': f"{m.avg_win:,.0f}원",
                'avg_loss': f"{m.avg_loss:,.0f}원"
            }
        }
    
    def get_stats(self) -> Dict:
        """추적기 성능 통계"""
        return {
            'equity_points': min(self._equity_index, self._max_equity_points),
            'total_trades': len(self.trades),
            'cache_hits': self._calculate_trade_stats_fast.cache_info().hits,
            'cache_misses': self._calculate_trade_stats_fast.cache_info().misses,
            'memory_usage_mb': (
                self._equity_array.nbytes + 
                self._equity_timestamps.nbytes
            ) / 1024 / 1024
        }

