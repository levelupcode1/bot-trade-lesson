#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 평가 시스템
백테스팅, 성과 분석, 실시간 모니터링을 통한 종합적인 성능 평가
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import json
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

class EvaluationMetric(Enum):
    """평가 지표"""
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    RECOVERY_FACTOR = "recovery_factor"
    VAR = "value_at_risk"
    CVAR = "conditional_var"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"

class BacktestMethod(Enum):
    """백테스트 방법"""
    SIMPLE = "simple"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    STRESS_TEST = "stress_test"

class PerformancePeriod(Enum):
    """성과 기간"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class TradeRecord:
    """거래 기록"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    strategy: str
    side: str  # 'buy' or 'sell'
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_rate: float
    commission: float
    slippage: float
    holding_period: timedelta

@dataclass
class PerformanceMetrics:
    """성과 지표"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    recovery_factor: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    skewness: float
    kurtosis: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_period: timedelta
    max_consecutive_wins: int
    max_consecutive_losses: int

@dataclass
class BacktestResult:
    """백테스트 결과"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_trades: int
    trades: List[TradeRecord]
    daily_returns: pd.Series
    equity_curve: pd.Series
    performance_metrics: PerformanceMetrics
    benchmark_comparison: Dict[str, float] = field(default_factory=dict)
    period_performance: Dict[PerformancePeriod, PerformanceMetrics] = field(default_factory=dict)

class PerformanceEvaluator:
    """성능 평가 시스템"""
    
    def __init__(self, 
                 initial_capital: float = 1_000_000,
                 benchmark_data: Optional[pd.Series] = None,
                 commission_rate: float = 0.001,
                 slippage_rate: float = 0.0005):
        self.initial_capital = initial_capital
        self.benchmark_data = benchmark_data
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)
        
        # 백테스트 결과 저장
        self.backtest_results: List[BacktestResult] = []
        self.trade_records: List[TradeRecord] = []
        
        # 실시간 모니터링
        self.real_time_metrics: Dict[str, Any] = {}
        self.performance_alerts: List[Dict[str, Any]] = []
        
        self.logger.info("성능 평가 시스템 초기화 완료")
    
    def run_backtest(self, 
                    strategy_func,
                    data: pd.DataFrame,
                    method: BacktestMethod = BacktestMethod.SIMPLE,
                    **kwargs) -> BacktestResult:
        """백테스트 실행"""
        self.logger.info(f"백테스트 시작 (방법: {method.value})")
        
        if method == BacktestMethod.SIMPLE:
            result = self._simple_backtest(strategy_func, data, **kwargs)
        elif method == BacktestMethod.WALK_FORWARD:
            result = self._walk_forward_backtest(strategy_func, data, **kwargs)
        elif method == BacktestMethod.MONTE_CARLO:
            result = self._monte_carlo_backtest(strategy_func, data, **kwargs)
        elif method == BacktestMethod.STRESS_TEST:
            result = self._stress_test_backtest(strategy_func, data, **kwargs)
        else:
            raise ValueError(f"지원하지 않는 백테스트 방법: {method}")
        
        self.backtest_results.append(result)
        
        self.logger.info(f"백테스트 완료: 총 수익률 {result.performance_metrics.total_return:.2%}")
        
        return result
    
    def _simple_backtest(self, strategy_func, data: pd.DataFrame, **kwargs) -> BacktestResult:
        """단순 백테스트"""
        trades = []
        equity_curve = []
        daily_returns = []
        
        capital = self.initial_capital
        position = None
        
        for i, row in data.iterrows():
            current_time = row.get('timestamp', i)
            current_price = row['close']
            
            # 전략 신호 생성
            signal = strategy_func(row, position, capital, **kwargs)
            
            # 거래 실행
            if signal['action'] == 'buy' and position is None:
                # 매수
                quantity = capital * signal.get('position_size', 0.1) / current_price
                commission = quantity * current_price * self.commission_rate
                slippage = quantity * current_price * self.slippage_rate
                
                position = {
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'quantity': quantity,
                    'commission': commission,
                    'slippage': slippage
                }
                
                capital -= commission + slippage
                
            elif signal['action'] == 'sell' and position is not None:
                # 매도
                exit_price = current_price
                pnl = (exit_price - position['entry_price']) * position['quantity']
                commission = position['quantity'] * exit_price * self.commission_rate
                slippage = position['quantity'] * exit_price * self.slippage_rate
                
                net_pnl = pnl - commission - slippage
                pnl_rate = net_pnl / (position['entry_price'] * position['quantity'])
                
                trade = TradeRecord(
                    entry_time=position['entry_time'],
                    exit_time=current_time,
                    symbol=signal.get('symbol', 'UNKNOWN'),
                    strategy=signal.get('strategy', 'UNKNOWN'),
                    side='long',
                    quantity=position['quantity'],
                    entry_price=position['entry_price'],
                    exit_price=exit_price,
                    pnl=net_pnl,
                    pnl_rate=pnl_rate,
                    commission=commission,
                    slippage=slippage,
                    holding_period=current_time - position['entry_time']
                )
                
                trades.append(trade)
                capital += net_pnl
                position = None
            
            # 자본 곡선 업데이트
            equity_curve.append(capital)
            
            # 일일 수익률 계산
            if len(equity_curve) > 1:
                daily_return = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_return)
        
        # 마지막 포지션 정리
        if position is not None:
            last_price = data.iloc[-1]['close']
            last_time = data.iloc[-1].get('timestamp', len(data) - 1)
            
            pnl = (last_price - position['entry_price']) * position['quantity']
            commission = position['quantity'] * last_price * self.commission_rate
            slippage = position['quantity'] * last_price * self.slippage_rate
            
            net_pnl = pnl - commission - slippage
            pnl_rate = net_pnl / (position['entry_price'] * position['quantity'])
            
            trade = TradeRecord(
                entry_time=position['entry_time'],
                exit_time=last_time,
                symbol=kwargs.get('symbol', 'UNKNOWN'),
                strategy=kwargs.get('strategy', 'UNKNOWN'),
                side='long',
                quantity=position['quantity'],
                entry_price=position['entry_price'],
                exit_price=last_price,
                pnl=net_pnl,
                pnl_rate=pnl_rate,
                commission=commission,
                slippage=slippage,
                holding_period=last_time - position['entry_time']
            )
            
            trades.append(trade)
            capital += net_pnl
        
        # 성과 지표 계산
        equity_series = pd.Series(equity_curve, index=data.index)
        daily_returns_series = pd.Series(daily_returns, index=data.index[1:])
        
        performance_metrics = self._calculate_performance_metrics(
            equity_series, daily_returns_series, trades
        )
        
        # 벤치마크 비교
        benchmark_comparison = self._calculate_benchmark_comparison(daily_returns_series)
        
        # 기간별 성과
        period_performance = self._calculate_period_performance(daily_returns_series)
        
        return BacktestResult(
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=capital,
            total_trades=len(trades),
            trades=trades,
            daily_returns=daily_returns_series,
            equity_curve=equity_series,
            performance_metrics=performance_metrics,
            benchmark_comparison=benchmark_comparison,
            period_performance=period_performance
        )
    
    def _walk_forward_backtest(self, strategy_func, data: pd.DataFrame, 
                             window_size: int = 252, step_size: int = 30, **kwargs) -> BacktestResult:
        """워크 포워드 백테스트"""
        all_trades = []
        all_equity_curves = []
        all_daily_returns = []
        
        for start_idx in range(0, len(data) - window_size, step_size):
            end_idx = start_idx + window_size
            
            # 훈련 데이터와 테스트 데이터 분할
            train_data = data.iloc[start_idx:start_idx + window_size // 2]
            test_data = data.iloc[start_idx + window_size // 2:end_idx]
            
            # 훈련 데이터로 전략 최적화 (여기서는 단순히 전략 실행)
            window_result = self._simple_backtest(strategy_func, test_data, **kwargs)
            
            all_trades.extend(window_result.trades)
            all_equity_curves.extend(window_result.equity_curve.tolist())
            all_daily_returns.extend(window_result.daily_returns.tolist())
        
        # 전체 결과 통합
        final_capital = all_equity_curves[-1] if all_equity_curves else self.initial_capital
        equity_series = pd.Series(all_equity_curves)
        daily_returns_series = pd.Series(all_daily_returns)
        
        performance_metrics = self._calculate_performance_metrics(
            equity_series, daily_returns_series, all_trades
        )
        
        benchmark_comparison = self._calculate_benchmark_comparison(daily_returns_series)
        period_performance = self._calculate_period_performance(daily_returns_series)
        
        return BacktestResult(
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_trades=len(all_trades),
            trades=all_trades,
            daily_returns=daily_returns_series,
            equity_curve=equity_series,
            performance_metrics=performance_metrics,
            benchmark_comparison=benchmark_comparison,
            period_performance=period_performance
        )
    
    def _monte_carlo_backtest(self, strategy_func, data: pd.DataFrame, 
                            n_simulations: int = 1000, **kwargs) -> BacktestResult:
        """몬테카를로 백테스트"""
        simulation_results = []
        
        for _ in range(n_simulations):
            # 데이터 순서 섞기
            shuffled_data = data.sample(frac=1).reset_index(drop=True)
            
            # 백테스트 실행
            result = self._simple_backtest(strategy_func, shuffled_data, **kwargs)
            simulation_results.append(result)
        
        # 결과 통계
        total_returns = [r.performance_metrics.total_return for r in simulation_results]
        sharpe_ratios = [r.performance_metrics.sharpe_ratio for r in simulation_results]
        max_drawdowns = [r.performance_metrics.max_drawdown for r in simulation_results]
        
        # 평균 결과 생성
        avg_result = simulation_results[0]  # 첫 번째 결과를 기본으로 사용
        
        avg_result.performance_metrics.total_return = np.mean(total_returns)
        avg_result.performance_metrics.sharpe_ratio = np.mean(sharpe_ratios)
        avg_result.performance_metrics.max_drawdown = np.mean(max_drawdowns)
        
        # 신뢰구간 추가
        avg_result.performance_metrics.var_95 = np.percentile(total_returns, 5)
        avg_result.performance_metrics.var_99 = np.percentile(total_returns, 1)
        
        return avg_result
    
    def _stress_test_backtest(self, strategy_func, data: pd.DataFrame, 
                            stress_scenarios: List[Dict[str, float]], **kwargs) -> BacktestResult:
        """스트레스 테스트 백테스트"""
        stress_results = []
        
        for scenario in stress_scenarios:
            # 데이터에 스트레스 적용
            stressed_data = data.copy()
            
            if 'price_shock' in scenario:
                shock = scenario['price_shock']
                stressed_data['close'] *= (1 + shock)
                stressed_data['high'] *= (1 + shock)
                stressed_data['low'] *= (1 + shock)
                stressed_data['open'] *= (1 + shock)
            
            if 'volatility_multiplier' in scenario:
                vol_mult = scenario['volatility_multiplier']
                returns = stressed_data['close'].pct_change()
                stressed_returns = returns * vol_mult
                stressed_data['close'] = stressed_data['close'].iloc[0] * (1 + stressed_returns).cumprod()
            
            # 백테스트 실행
            result = self._simple_backtest(strategy_func, stressed_data, **kwargs)
            stress_results.append(result)
        
        # 최악 시나리오 반환
        worst_result = min(stress_results, key=lambda x: x.performance_metrics.total_return)
        
        return worst_result
    
    def _calculate_performance_metrics(self, 
                                     equity_curve: pd.Series,
                                     daily_returns: pd.Series,
                                     trades: List[TradeRecord]) -> PerformanceMetrics:
        """성과 지표 계산"""
        if len(trades) == 0:
            return self._get_empty_metrics()
        
        # 기본 수익률 지표
        total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
        
        # 연간화 수익률
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # 변동성
        volatility = daily_returns.std() * np.sqrt(252)
        
        # 샤프 비율
        risk_free_rate = 0.02  # 2% 가정
        excess_returns = daily_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Sortino 비율
        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        sortino_ratio = excess_returns / downside_volatility if downside_volatility > 0 else 0
        
        # 최대 낙폭
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar 비율
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 거래 통계
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0
        
        # 수익 팩터
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # 회복 팩터
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        # VaR 및 CVaR
        var_95 = np.percentile(daily_returns, 5)
        var_99 = np.percentile(daily_returns, 1)
        cvar_95 = daily_returns[daily_returns <= var_95].mean()
        cvar_99 = daily_returns[daily_returns <= var_99].mean()
        
        # 통계적 특성
        skewness = daily_returns.skew()
        kurtosis = daily_returns.kurtosis()
        
        # 거래별 통계
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # 평균 보유 기간
        holding_periods = [t.holding_period for t in trades]
        avg_holding_period = np.mean(holding_periods) if holding_periods else timedelta(0)
        
        # 연속 승/패
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(trades)
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            recovery_factor=recovery_factor,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            skewness=skewness,
            kurtosis=kurtosis,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_holding_period=avg_holding_period,
            max_consecutive_wins=consecutive_wins,
            max_consecutive_losses=consecutive_losses
        )
    
    def _calculate_consecutive_trades(self, trades: List[TradeRecord]) -> Tuple[int, int]:
        """연속 승/패 계산"""
        if not trades:
            return 0, 0
        
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return max_consecutive_wins, max_consecutive_losses
    
    def _calculate_benchmark_comparison(self, daily_returns: pd.Series) -> Dict[str, float]:
        """벤치마크 비교"""
        if self.benchmark_data is None:
            return {}
        
        # 벤치마크와 일치하는 기간의 수익률만 추출
        common_index = daily_returns.index.intersection(self.benchmark_data.index)
        if len(common_index) == 0:
            return {}
        
        strategy_returns = daily_returns.loc[common_index]
        benchmark_returns = self.benchmark_data.loc[common_index]
        
        # 베타 계산
        if len(strategy_returns) > 1 and benchmark_returns.std() > 0:
            beta = np.cov(strategy_returns, benchmark_returns)[0, 1] / benchmark_returns.var()
            alpha = strategy_returns.mean() * 252 - beta * benchmark_returns.mean() * 252
            
            # 정보 비율
            excess_returns = strategy_returns - benchmark_returns
            information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            
            # 상관관계
            correlation = strategy_returns.corr(benchmark_returns)
            
            return {
                'beta': beta,
                'alpha': alpha,
                'information_ratio': information_ratio,
                'correlation': correlation
            }
        
        return {}
    
    def _calculate_period_performance(self, daily_returns: pd.Series) -> Dict[PerformancePeriod, PerformanceMetrics]:
        """기간별 성과 계산"""
        period_performance = {}
        
        for period in PerformancePeriod:
            if period == PerformancePeriod.WEEKLY:
                period_returns = daily_returns.resample('W').apply(lambda x: (1 + x).prod() - 1)
            elif period == PerformancePeriod.MONTHLY:
                period_returns = daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            elif period == PerformancePeriod.QUARTERLY:
                period_returns = daily_returns.resample('Q').apply(lambda x: (1 + x).prod() - 1)
            elif period == PerformancePeriod.YEARLY:
                period_returns = daily_returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)
            else:  # DAILY
                period_returns = daily_returns
            
            if len(period_returns) > 0:
                # 간단한 성과 지표 계산
                total_return = (1 + period_returns).prod() - 1
                volatility = period_returns.std() * np.sqrt(252 / len(period_returns))
                
                period_performance[period] = PerformanceMetrics(
                    total_return=total_return,
                    annualized_return=total_return,
                    volatility=volatility,
                    sharpe_ratio=0,  # 간소화
                    sortino_ratio=0,
                    calmar_ratio=0,
                    max_drawdown=0,
                    win_rate=len(period_returns[period_returns > 0]) / len(period_returns),
                    profit_factor=0,
                    recovery_factor=0,
                    var_95=0,
                    var_99=0,
                    cvar_95=0,
                    cvar_99=0,
                    skewness=period_returns.skew(),
                    kurtosis=period_returns.kurtosis(),
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    avg_win=0,
                    avg_loss=0,
                    largest_win=0,
                    largest_loss=0,
                    avg_holding_period=timedelta(0),
                    max_consecutive_wins=0,
                    max_consecutive_losses=0
                )
        
        return period_performance
    
    def _get_empty_metrics(self) -> PerformanceMetrics:
        """빈 성과 지표 반환"""
        return PerformanceMetrics(
            total_return=0, annualized_return=0, volatility=0,
            sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
            max_drawdown=0, win_rate=0, profit_factor=0, recovery_factor=0,
            var_95=0, var_99=0, cvar_95=0, cvar_99=0,
            skewness=0, kurtosis=0, total_trades=0,
            winning_trades=0, losing_trades=0, avg_win=0, avg_loss=0,
            largest_win=0, largest_loss=0, avg_holding_period=timedelta(0),
            max_consecutive_wins=0, max_consecutive_losses=0
        )
    
    def generate_performance_report(self, result: BacktestResult) -> str:
        """성능 리포트 생성"""
        report = f"""
=== 성능 평가 리포트 ===
기간: {result.start_date.strftime('%Y-%m-%d')} ~ {result.end_date.strftime('%Y-%m-%d')}
초기 자본: {result.initial_capital:,.0f}원
최종 자본: {result.final_capital:,.0f}원

=== 수익률 지표 ===
총 수익률: {result.performance_metrics.total_return:.2%}
연간화 수익률: {result.performance_metrics.annualized_return:.2%}
변동성: {result.performance_metrics.volatility:.2%}

=== 위험 조정 수익률 ===
샤프 비율: {result.performance_metrics.sharpe_ratio:.2f}
Sortino 비율: {result.performance_metrics.sortino_ratio:.2f}
Calmar 비율: {result.performance_metrics.calmar_ratio:.2f}

=== 위험 지표 ===
최대 낙폭: {result.performance_metrics.max_drawdown:.2%}
VaR (95%): {result.performance_metrics.var_95:.2%}
VaR (99%): {result.performance_metrics.var_99:.2%}
CVaR (95%): {result.performance_metrics.cvar_95:.2%}
CVaR (99%): {result.performance_metrics.cvar_99:.2%}

=== 거래 통계 ===
총 거래 수: {result.performance_metrics.total_trades}
승률: {result.performance_metrics.win_rate:.1%}
수익 팩터: {result.performance_metrics.profit_factor:.2f}
회복 팩터: {result.performance_metrics.recovery_factor:.2f}
평균 승리: {result.performance_metrics.avg_win:,.0f}원
평균 손실: {result.performance_metrics.avg_loss:,.0f}원
최대 승리: {result.performance_metrics.largest_win:,.0f}원
최대 손실: {result.performance_metrics.largest_loss:,.0f}원

=== 통계적 특성 ===
왜도: {result.performance_metrics.skewness:.3f}
첨도: {result.performance_metrics.kurtosis:.3f}
평균 보유 기간: {result.performance_metrics.avg_holding_period}
최대 연속 승: {result.performance_metrics.max_consecutive_wins}
최대 연속 패: {result.performance_metrics.max_consecutive_losses}

=== 벤치마크 비교 ===
"""
        
        if result.benchmark_comparison:
            for metric, value in result.benchmark_comparison.items():
                report += f"{metric}: {value:.3f}\n"
        else:
            report += "벤치마크 데이터 없음\n"
        
        return report
    
    def create_visualizations(self, result: BacktestResult, save_path: str = None):
        """시각화 생성"""
        if save_path is None:
            save_path = f"performance_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 자본 곡선
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve.values,
            mode='lines',
            name='자본 곡선',
            line=dict(color='blue')
        ))
        
        if self.benchmark_data is not None:
            benchmark_normalized = self.benchmark_data / self.benchmark_data.iloc[0] * result.initial_capital
            fig1.add_trace(go.Scatter(
                x=benchmark_normalized.index,
                y=benchmark_normalized.values,
                mode='lines',
                name='벤치마크',
                line=dict(color='red', dash='dash')
            ))
        
        fig1.update_layout(
            title='자본 곡선',
            xaxis_title='날짜',
            yaxis_title='자본 (원)',
            hovermode='x unified'
        )
        
        fig1.write_html(f"{save_path}_equity_curve.html")
        
        # 낙폭 차트
        cumulative_returns = (1 + result.daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max * 100
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode='lines',
            name='낙폭',
            fill='tonexty',
            line=dict(color='red')
        ))
        
        fig2.update_layout(
            title='낙폭 차트',
            xaxis_title='날짜',
            yaxis_title='낙폭 (%)',
            hovermode='x unified'
        )
        
        fig2.write_html(f"{save_path}_drawdown.html")
        
        # 수익률 분포
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=result.daily_returns * 100,
            nbinsx=50,
            name='일일 수익률 분포',
            opacity=0.7
        ))
        
        fig3.update_layout(
            title='일일 수익률 분포',
            xaxis_title='수익률 (%)',
            yaxis_title='빈도',
            hovermode='x unified'
        )
        
        fig3.write_html(f"{save_path}_returns_distribution.html")
        
        # 거래별 수익률
        if result.trades:
            trade_returns = [t.pnl_rate * 100 for t in result.trades]
            
            fig4 = go.Figure()
            colors = ['green' if r > 0 else 'red' for r in trade_returns]
            
            fig4.add_trace(go.Bar(
                x=list(range(len(trade_returns))),
                y=trade_returns,
                name='거래별 수익률',
                marker_color=colors
            ))
            
            fig4.update_layout(
                title='거래별 수익률',
                xaxis_title='거래 번호',
                yaxis_title='수익률 (%)',
                hovermode='x unified'
            )
            
            fig4.write_html(f"{save_path}_trade_returns.html")
        
        self.logger.info(f"시각화 파일 저장 완료: {save_path}_*.html")
    
    def compare_strategies(self, results: List[BacktestResult]) -> pd.DataFrame:
        """전략 비교"""
        comparison_data = []
        
        for i, result in enumerate(results):
            metrics = result.performance_metrics
            
            comparison_data.append({
                '전략': f'전략_{i+1}',
                '총 수익률': f"{metrics.total_return:.2%}",
                '연간화 수익률': f"{metrics.annualized_return:.2%}",
                '변동성': f"{metrics.volatility:.2%}",
                '샤프 비율': f"{metrics.sharpe_ratio:.2f}",
                '최대 낙폭': f"{metrics.max_drawdown:.2%}",
                '승률': f"{metrics.win_rate:.1%}",
                '수익 팩터': f"{metrics.profit_factor:.2f}",
                '총 거래 수': metrics.total_trades
            })
        
        return pd.DataFrame(comparison_data)
    
    def update_real_time_metrics(self, current_value: float, daily_return: float):
        """실시간 성과 지표 업데이트"""
        self.real_time_metrics.update({
            'timestamp': datetime.now(),
            'portfolio_value': current_value,
            'daily_return': daily_return,
            'total_return': (current_value - self.initial_capital) / self.initial_capital
        })
        
        # 성과 알림 확인
        self._check_performance_alerts()
    
    def _check_performance_alerts(self):
        """성과 알림 확인"""
        if not self.real_time_metrics:
            return
        
        current_return = self.real_time_metrics['total_return']
        daily_return = self.real_time_metrics['daily_return']
        
        # 일일 손실 알림
        if daily_return < -0.05:  # 5% 일일 손실
            alert = {
                'timestamp': datetime.now(),
                'type': 'daily_loss',
                'message': f'일일 손실 {daily_return:.2%} 발생',
                'severity': 'high'
            }
            self.performance_alerts.append(alert)
        
        # 누적 손실 알림
        if current_return < -0.10:  # 10% 누적 손실
            alert = {
                'timestamp': datetime.now(),
                'type': 'cumulative_loss',
                'message': f'누적 손실 {current_return:.2%} 발생',
                'severity': 'critical'
            }
            self.performance_alerts.append(alert)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성과 요약 반환"""
        summary = {
            'total_backtests': len(self.backtest_results),
            'real_time_metrics': self.real_time_metrics,
            'performance_alerts': len(self.performance_alerts),
            'recent_alerts': self.performance_alerts[-5:] if self.performance_alerts else []
        }
        
        if self.backtest_results:
            latest_result = self.backtest_results[-1]
            summary['latest_performance'] = {
                'total_return': latest_result.performance_metrics.total_return,
                'sharpe_ratio': latest_result.performance_metrics.sharpe_ratio,
                'max_drawdown': latest_result.performance_metrics.max_drawdown,
                'win_rate': latest_result.performance_metrics.win_rate
            }
        
        return summary

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    prices = 100 * np.cumprod(1 + np.random.randn(252) * 0.02)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(252) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(252)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(252)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    })
    
    # 간단한 전략 함수
    def simple_strategy(row, position, capital, **kwargs):
        # 단순한 이동평균 전략
        if len(kwargs.get('price_history', [])) < 20:
            return {'action': 'hold'}
        
        price_history = kwargs['price_history']
        ma_short = np.mean(price_history[-5:])
        ma_long = np.mean(price_history[-20:])
        current_price = row['close']
        
        if position is None and ma_short > ma_long:
            return {
                'action': 'buy',
                'position_size': 0.1,
                'symbol': 'BTC',
                'strategy': 'MA_Crossover'
            }
        elif position is not None and ma_short < ma_long:
            return {
                'action': 'sell',
                'symbol': 'BTC',
                'strategy': 'MA_Crossover'
            }
        
        return {'action': 'hold'}
    
    # 성능 평가기 초기화
    evaluator = PerformanceEvaluator(
        initial_capital=1_000_000,
        commission_rate=0.001,
        slippage_rate=0.0005
    )
    
    print("=== 성능 평가 시스템 테스트 ===")
    
    # 단순 백테스트
    print("\n1. 단순 백테스트")
    price_history = []
    
    def strategy_with_history(row, position, capital, **kwargs):
        price_history.append(row['close'])
        return simple_strategy(row, position, capital, price_history=price_history, **kwargs)
    
    simple_result = evaluator.run_backtest(
        strategy_with_history,
        sample_data,
        method=BacktestMethod.SIMPLE,
        symbol='BTC',
        strategy='MA_Crossover'
    )
    
    print(f"총 수익률: {simple_result.performance_metrics.total_return:.2%}")
    print(f"샤프 비율: {simple_result.performance_metrics.sharpe_ratio:.2f}")
    print(f"최대 낙폭: {simple_result.performance_metrics.max_drawdown:.2%}")
    print(f"승률: {simple_result.performance_metrics.win_rate:.1%}")
    print(f"총 거래 수: {simple_result.performance_metrics.total_trades}")
    
    # 성능 리포트 생성
    report = evaluator.generate_performance_report(simple_result)
    print(f"\n=== 성능 리포트 ===")
    print(report)
    
    # 시각화 생성
    evaluator.create_visualizations(simple_result)
    
    # 워크 포워드 백테스트
    print("\n2. 워크 포워드 백테스트")
    price_history = []
    
    wf_result = evaluator.run_backtest(
        strategy_with_history,
        sample_data,
        method=BacktestMethod.WALK_FORWARD,
        window_size=126,  # 6개월
        step_size=21,     # 1개월
        symbol='BTC',
        strategy='MA_Crossover_WF'
    )
    
    print(f"워크 포워드 총 수익률: {wf_result.performance_metrics.total_return:.2%}")
    print(f"워크 포워드 샤프 비율: {wf_result.performance_metrics.sharpe_ratio:.2f}")
    
    # 전략 비교
    comparison_df = evaluator.compare_strategies([simple_result, wf_result])
    print(f"\n=== 전략 비교 ===")
    print(comparison_df.to_string(index=False))
    
    # 실시간 모니터링 시뮬레이션
    print("\n3. 실시간 모니터링")
    current_value = simple_result.final_capital
    
    for i in range(5):
        # 시뮬레이션된 일일 수익률
        daily_return = np.random.normal(0, 0.02)
        current_value *= (1 + daily_return)
        
        evaluator.update_real_time_metrics(current_value, daily_return)
        
        print(f"일 {i+1}: 포트폴리오 가치 {current_value:,.0f}원, 일일 수익률 {daily_return:.2%}")
    
    # 성과 요약
    summary = evaluator.get_performance_summary()
    print(f"\n=== 성과 요약 ===")
    print(f"총 백테스트 수: {summary['total_backtests']}")
    print(f"성과 알림 수: {summary['performance_alerts']}")
    
    if summary['recent_alerts']:
        print("최근 알림:")
        for alert in summary['recent_alerts']:
            print(f"  - {alert['message']} ({alert['severity']})")
    
    print("\n성능 평가 시스템 테스트 완료!")
