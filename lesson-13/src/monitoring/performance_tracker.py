#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 지표 계산 엔진
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    timestamp: datetime
    
    # 수익률 지표
    total_return: float
    daily_return: float
    monthly_return: float
    annual_return: float
    
    # 리스크 지표
    volatility: float
    max_drawdown: float
    current_drawdown: float
    var_95: float
    cvar_95: float
    
    # 효율성 지표
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # 거래 지표
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    
    # 포지션 지표
    current_positions: int
    total_exposure: float
    leverage: float


class PerformanceTracker:
    """실시간 성능 추적기"""
    
    def __init__(self, initial_capital: float = 1_000_000):
        """
        Args:
            initial_capital: 초기 자본
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # 거래 기록
        self.trades: List[Dict] = []
        
        # 자산 히스토리
        self.equity_curve: List[Dict] = []
        
        # 최근 메트릭
        self.latest_metrics: Optional[PerformanceMetrics] = None
        
        # 성과 히스토리
        self.metrics_history: List[PerformanceMetrics] = []
        
        self.logger.info(f"성능 추적기 초기화: 초기자본 {initial_capital:,.0f}원")
    
    def update(self, market_data: Dict, strategy_performance: Dict):
        """성능 지표 업데이트"""
        timestamp = datetime.now()
        
        # 자산 가치 계산
        equity = self._calculate_equity(market_data, strategy_performance)
        
        # 자산 곡선 업데이트
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity,
            'cash': self.current_capital,
            'positions_value': equity - self.current_capital
        })
        
        # 메트릭 계산
        metrics = self._calculate_metrics(timestamp)
        
        self.latest_metrics = metrics
        self.metrics_history.append(metrics)
        
        # 히스토리 제한 (최근 10000개)
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-10000:]
        
        return metrics
    
    def _calculate_equity(self, market_data: Dict, strategy_performance: Dict) -> float:
        """자산 가치 계산"""
        # 현금 + 포지션 가치
        equity = self.current_capital
        
        # 각 전략의 미실현 손익 합산
        for strategy_id, perf in strategy_performance.items():
            if hasattr(perf, 'unrealized_pnl'):
                equity += perf.unrealized_pnl
        
        return equity
    
    def _calculate_metrics(self, timestamp: datetime) -> PerformanceMetrics:
        """성능 메트릭 계산"""
        if len(self.equity_curve) < 2:
            # 초기 상태
            return PerformanceMetrics(
                timestamp=timestamp,
                total_return=0.0,
                daily_return=0.0,
                monthly_return=0.0,
                annual_return=0.0,
                volatility=0.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                var_95=0.0,
                cvar_95=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                total_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                current_positions=0,
                total_exposure=0.0,
                leverage=1.0
            )
        
        # 자산 곡선을 DataFrame으로 변환
        df = pd.DataFrame(self.equity_curve)
        df['return'] = df['equity'].pct_change()
        
        # 수익률 계산
        current_equity = df['equity'].iloc[-1]
        total_return = (current_equity / self.initial_capital) - 1
        
        # 일간 수익률 (최근 24시간)
        if len(df) > 24:
            daily_return = (df['equity'].iloc[-1] / df['equity'].iloc[-24]) - 1
        else:
            daily_return = total_return
        
        # 월간/연간 수익률 추정
        if len(df) > 1:
            avg_hourly_return = df['return'].mean()
            monthly_return = (1 + avg_hourly_return) ** (24 * 30) - 1
            annual_return = (1 + avg_hourly_return) ** (24 * 365) - 1
        else:
            monthly_return = 0.0
            annual_return = 0.0
        
        # 변동성
        if len(df['return'].dropna()) > 1:
            volatility = df['return'].std() * np.sqrt(24 * 365)  # 연간화
        else:
            volatility = 0.0
        
        # 최대 낙폭
        df['cummax'] = df['equity'].expanding().max()
        df['drawdown'] = (df['equity'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        current_drawdown = df['drawdown'].iloc[-1]
        
        # VaR / CVaR
        returns = df['return'].dropna()
        if len(returns) > 0:
            var_95 = returns.quantile(0.05)
            cvar_95 = returns[returns <= var_95].mean()
        else:
            var_95 = 0.0
            cvar_95 = 0.0
        
        # 샤프 비율
        if volatility > 0 and len(returns) > 0:
            excess_return = annual_return - 0.02  # 무위험 수익률 2%
            sharpe_ratio = excess_return / volatility
        else:
            sharpe_ratio = 0.0
        
        # 소르티노 비율
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std() * np.sqrt(24 * 365)
            if downside_std > 0:
                sortino_ratio = (annual_return - 0.02) / downside_std
            else:
                sortino_ratio = 0.0
        else:
            sortino_ratio = 0.0
        
        # 칼마 비율
        if max_drawdown < 0:
            calmar_ratio = annual_return / abs(max_drawdown)
        else:
            calmar_ratio = 0.0
        
        # 거래 지표
        total_trades = len(self.trades)
        
        if total_trades > 0:
            wins = [t for t in self.trades if t.get('pnl', 0) > 0]
            losses = [t for t in self.trades if t.get('pnl', 0) < 0]
            
            win_rate = len(wins) / total_trades
            
            total_wins = sum(t.get('pnl', 0) for t in wins)
            total_losses = abs(sum(t.get('pnl', 0) for t in losses))
            
            if total_losses > 0:
                profit_factor = total_wins / total_losses
            else:
                profit_factor = 0.0
            
            avg_win = total_wins / len(wins) if wins else 0.0
            avg_loss = total_losses / len(losses) if losses else 0.0
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_win = 0.0
            avg_loss = 0.0
        
        # 포지션 지표 (시뮬레이션)
        current_positions = np.random.randint(0, 3)
        total_exposure = np.random.uniform(0, 0.5) * current_equity
        leverage = total_exposure / current_equity if current_equity > 0 else 1.0
        
        return PerformanceMetrics(
            timestamp=timestamp,
            total_return=total_return,
            daily_return=daily_return,
            monthly_return=monthly_return,
            annual_return=annual_return,
            volatility=volatility,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            current_positions=current_positions,
            total_exposure=total_exposure,
            leverage=leverage
        )
    
    def add_trade(self, trade: Dict):
        """거래 추가"""
        self.trades.append(trade)
        
        # PnL 업데이트
        if 'pnl' in trade:
            self.current_capital += trade['pnl']
    
    def get_performance_summary(self) -> Dict:
        """성능 요약 조회"""
        if not self.latest_metrics:
            return {}
        
        m = self.latest_metrics
        
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
            },
            'positions': {
                'current_positions': m.current_positions,
                'total_exposure': f"{m.total_exposure:,.0f}원",
                'leverage': f"{m.leverage:.2f}x"
            }
        }
    
    def get_metrics_dataframe(self, hours: int = 24) -> pd.DataFrame:
        """메트릭 히스토리를 DataFrame으로"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return pd.DataFrame()
        
        data = []
        for m in recent_metrics:
            data.append({
                'timestamp': m.timestamp,
                'total_return': m.total_return,
                'sharpe_ratio': m.sharpe_ratio,
                'max_drawdown': m.max_drawdown,
                'win_rate': m.win_rate
            })
        
        return pd.DataFrame(data)

