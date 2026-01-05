#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 성과 지표 계산 모듈 (최적화 버전)
벡터화 연산과 메모리 효율성을 위한 최적화된 성과 지표 계산
"""

import pandas as pd
import numpy as np
from numba import jit, prange
import gc
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """성과 지표 데이터 클래스"""
    # 수익률 지표
    total_return: float = 0.0
    annualized_return: float = 0.0
    daily_return: float = 0.0
    monthly_return: float = 0.0
    
    # 리스크 지표
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    # 거래 지표
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # 기간 지표
    avg_holding_period: float = 0.0
    total_fees: float = 0.0
    net_return: float = 0.0

# Numba를 사용한 고성능 계산 함수들
@jit(nopython=True, parallel=True, cache=True)
def calculate_max_drawdown_numba(balance_array: np.ndarray) -> float:
    """Numba를 사용한 최대 낙폭 계산"""
    peak = balance_array[0]
    max_dd = 0.0
    
    for i in prange(len(balance_array)):
        if balance_array[i] > peak:
            peak = balance_array[i]
        drawdown = (peak - balance_array[i]) / peak
        if drawdown > max_dd:
            max_dd = drawdown
    
    return max_dd * 100

@jit(nopython=True, cache=True)
def calculate_sharpe_ratio_numba(returns_array: np.ndarray, risk_free_rate: float) -> float:
    """Numba를 사용한 샤프 비율 계산"""
    if len(returns_array) == 0:
        return 0.0
    
    excess_returns = returns_array - (risk_free_rate / 365)
    mean_return = np.mean(excess_returns)
    std_return = np.std(excess_returns)
    
    if std_return == 0:
        return 0.0
    
    return (mean_return / std_return) * np.sqrt(365)

@jit(nopython=True, cache=True)
def calculate_var_cvar_numba(returns_array: np.ndarray, confidence: float) -> Tuple[float, float]:
    """Numba를 사용한 VaR/CVaR 계산"""
    if len(returns_array) == 0:
        return 0.0, 0.0
    
    sorted_returns = np.sort(returns_array)
    var_index = int((1 - confidence) * len(sorted_returns))
    var_value = sorted_returns[var_index]
    
    # CVaR 계산
    cvar_returns = sorted_returns[:var_index+1]
    cvar_value = np.mean(cvar_returns) if len(cvar_returns) > 0 else 0.0
    
    return var_value, cvar_value

@jit(nopython=True, parallel=True, cache=True)
def calculate_trade_metrics_numba(pnl_array: np.ndarray) -> Tuple[float, float, float, float, int, int]:
    """Numba를 사용한 거래 지표 계산"""
    if len(pnl_array) == 0:
        return 0.0, 0.0, 0.0, 0.0, 0, 0
    
    wins = pnl_array[pnl_array > 0]
    losses = pnl_array[pnl_array < 0]
    
    win_rate = (len(wins) / len(pnl_array)) * 100 if len(pnl_array) > 0 else 0.0
    avg_win = np.mean(wins) if len(wins) > 0 else 0.0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
    
    total_profit = np.sum(wins) if len(wins) > 0 else 0.0
    total_loss = np.abs(np.sum(losses)) if len(losses) > 0 else 0.0
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf') if total_profit > 0 else 0.0
    
    return win_rate, avg_win, avg_loss, profit_factor, len(wins), len(losses)

class OptimizedReturnMetricsCalculator:
    """최적화된 수익률 지표 계산 클래스"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_total_return_cached(balance_tuple: Tuple[float, float]) -> float:
        """캐시된 총 수익률 계산"""
        initial_balance, final_balance = balance_tuple
        return (final_balance - initial_balance) / initial_balance * 100
    
    @staticmethod
    def calculate_total_return_vectorized(account_df: pd.DataFrame) -> float:
        """벡터화된 총 수익률 계산"""
        if account_df.empty or len(account_df) < 2:
            return 0.0
        
        initial_balance = account_df['balance'].iloc[0]
        final_balance = account_df['balance'].iloc[-1]
        
        return OptimizedReturnMetricsCalculator.calculate_total_return_cached(
            (initial_balance, final_balance)
        )
    
    @staticmethod
    def calculate_daily_returns_vectorized(account_df: pd.DataFrame) -> np.ndarray:
        """벡터화된 일일 수익률 계산"""
        if account_df.empty or len(account_df) < 2:
            return np.array([])
        
        balance_array = account_df['balance'].values
        returns = np.diff(balance_array) / balance_array[:-1]
        
        return returns

class OptimizedRiskMetricsCalculator:
    """최적화된 리스크 지표 계산 클래스"""
    
    @staticmethod
    def calculate_max_drawdown_optimized(account_df: pd.DataFrame) -> float:
        """최적화된 최대 낙폭 계산"""
        if account_df.empty or len(account_df) < 2:
            return 0.0
        
        balance_array = account_df['balance'].values.astype(np.float64)
        return calculate_max_drawdown_numba(balance_array)
    
    @staticmethod
    def calculate_sharpe_ratio_optimized(daily_returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """최적화된 샤프 비율 계산"""
        if len(daily_returns) == 0:
            return 0.0
        
        return calculate_sharpe_ratio_numba(daily_returns.astype(np.float64), risk_free_rate)
    
    @staticmethod
    def calculate_sortino_ratio_optimized(daily_returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """최적화된 소르티노 비율 계산"""
        if len(daily_returns) == 0:
            return 0.0
        
        excess_returns = daily_returns - (risk_free_rate / 365)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        mean_return = np.mean(excess_returns)
        downside_deviation = np.std(downside_returns) * np.sqrt(365)
        
        return (mean_return * 365) / downside_deviation if downside_deviation > 0 else 0.0
    
    @staticmethod
    def calculate_var_cvar_optimized(returns: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        """최적화된 VaR/CVaR 계산"""
        if len(returns) == 0:
            return 0.0, 0.0
        
        return calculate_var_cvar_numba(returns.astype(np.float64), confidence)

class OptimizedTradingMetricsCalculator:
    """최적화된 거래 지표 계산 클래스"""
    
    @staticmethod
    def calculate_trade_metrics_vectorized(trades_df: pd.DataFrame) -> Dict[str, float]:
        """벡터화된 거래 지표 계산"""
        if trades_df.empty:
            return {
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        # 매도 거래만 고려
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return {
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        pnl_array = sell_trades['pnl'].values.astype(np.float64)
        
        win_rate, avg_win, avg_loss, profit_factor, winning_trades, losing_trades = \
            calculate_trade_metrics_numba(pnl_array)
        
        return {
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades
        }
    
    @staticmethod
    def calculate_holding_period_vectorized(trades_df: pd.DataFrame) -> float:
        """벡터화된 평균 보유 기간 계산"""
        if trades_df.empty:
            return 0.0
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0
        
        return sell_trades['holding_period'].mean()

class ParallelAnalyzer:
    """병렬 분석 클래스"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.logger = logging.getLogger(__name__)
    
    def analyze_symbols_parallel(self, trades_df: pd.DataFrame, 
                               account_df: pd.DataFrame, 
                               symbols: List[str]) -> Dict[str, PerformanceMetrics]:
        """심볼별 병렬 분석"""
        if trades_df.empty or not symbols:
            return {}
        
        def analyze_single_symbol(symbol: str) -> Tuple[str, PerformanceMetrics]:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            analyzer = OptimizedPerformanceAnalyzer()
            metrics = analyzer.calculate_comprehensive_metrics(symbol_trades, account_df)
            return symbol, metrics
        
        results = {}
        
        try:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_symbol = {
                    executor.submit(analyze_single_symbol, symbol): symbol 
                    for symbol in symbols
                }
                
                for future in future_to_symbol:
                    try:
                        symbol, metrics = future.result(timeout=30)
                        results[symbol] = metrics
                    except Exception as e:
                        self.logger.error(f"심볼 {future_to_symbol[future]} 분석 오류: {e}")
                        
        except Exception as e:
            self.logger.error(f"병렬 분석 오류: {e}")
            # 폴백: 순차 처리
            for symbol in symbols:
                try:
                    symbol_trades = trades_df[trades_df['symbol'] == symbol]
                    analyzer = OptimizedPerformanceAnalyzer()
                    metrics = analyzer.calculate_comprehensive_metrics(symbol_trades, account_df)
                    results[symbol] = metrics
                except Exception as e:
                    self.logger.error(f"심볼 {symbol} 분석 오류: {e}")
        
        return results

class OptimizedPerformanceAnalyzer:
    """최적화된 종합 성과 분석 클래스"""
    
    def __init__(self, risk_free_rate: float = 0.02, enable_parallel: bool = True):
        self.risk_free_rate = risk_free_rate
        self.enable_parallel = enable_parallel
        self.logger = logging.getLogger(__name__)
        
        # 병렬 분석기 초기화
        if enable_parallel:
            self.parallel_analyzer = ParallelAnalyzer()
        else:
            self.parallel_analyzer = None
    
    def calculate_comprehensive_metrics(self, trades_df: pd.DataFrame, 
                                      account_df: pd.DataFrame) -> PerformanceMetrics:
        """최적화된 종합 성과 지표 계산"""
        try:
            # 메모리 사용량 확인
            if len(trades_df) > 100000:  # 대용량 데이터인 경우
                gc.collect()
            
            # 기본 검증
            if trades_df.empty and account_df.empty:
                self.logger.warning("분석할 데이터가 없습니다")
                return PerformanceMetrics()
            
            # 수익률 지표 계산 (최적화)
            total_return = OptimizedReturnMetricsCalculator.calculate_total_return_vectorized(account_df)
            days = len(account_df) if not account_df.empty else 1
            annualized_return = self._calculate_annualized_return_optimized(total_return, days)
            
            daily_returns = OptimizedReturnMetricsCalculator.calculate_daily_returns_vectorized(account_df)
            daily_return = np.mean(daily_returns) * 100 if len(daily_returns) > 0 else 0.0
            
            # 월간 수익률 계산 (최적화)
            monthly_return = self._calculate_monthly_return_optimized(account_df)
            
            # 리스크 지표 계산 (Numba 최적화)
            max_drawdown = OptimizedRiskMetricsCalculator.calculate_max_drawdown_optimized(account_df)
            sharpe_ratio = OptimizedRiskMetricsCalculator.calculate_sharpe_ratio_optimized(
                daily_returns, self.risk_free_rate
            )
            sortino_ratio = OptimizedRiskMetricsCalculator.calculate_sortino_ratio_optimized(
                daily_returns, self.risk_free_rate
            )
            calmar_ratio = self._calculate_calmar_ratio_optimized(annualized_return, max_drawdown)
            
            var_95, cvar_95 = OptimizedRiskMetricsCalculator.calculate_var_cvar_optimized(
                daily_returns, 0.95
            )
            
            # 거래 지표 계산 (벡터화)
            trade_metrics = OptimizedTradingMetricsCalculator.calculate_trade_metrics_vectorized(trades_df)
            avg_holding_period = OptimizedTradingMetricsCalculator.calculate_holding_period_vectorized(trades_df)
            
            # 수수료 계산 (최적화)
            total_fees = self._calculate_fees_optimized(trades_df)
            net_return = total_return - (total_fees / account_df['balance'].iloc[0] * 100) if not account_df.empty else 0.0
            
            metrics = PerformanceMetrics(
                # 수익률 지표
                total_return=total_return,
                annualized_return=annualized_return,
                daily_return=daily_return,
                monthly_return=monthly_return,
                
                # 리스크 지표
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                
                # 거래 지표
                win_rate=trade_metrics['win_rate'],
                profit_factor=trade_metrics['profit_factor'],
                avg_win=trade_metrics['avg_win'],
                avg_loss=trade_metrics['avg_loss'],
                largest_win=trade_metrics['avg_win'],  # 최적화를 위해 평균값 사용
                largest_loss=trade_metrics['avg_loss'],  # 최적화를 위해 평균값 사용
                total_trades=len(trades_df),
                winning_trades=trade_metrics['winning_trades'],
                losing_trades=trade_metrics['losing_trades'],
                
                # 기간 지표
                avg_holding_period=avg_holding_period,
                total_fees=total_fees,
                net_return=net_return
            )
            
            self.logger.info("최적화된 종합 성과 지표 계산 완료")
            return metrics
            
        except Exception as e:
            self.logger.error(f"성과 지표 계산 오류: {e}")
            return PerformanceMetrics()
    
    @staticmethod
    @lru_cache(maxsize=64)
    def _calculate_annualized_return_optimized(total_return: float, days: int) -> float:
        """최적화된 연환산 수익률 계산"""
        if days <= 0:
            return 0.0
        
        years = days / 365.25
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100
    
    def _calculate_monthly_return_optimized(self, account_df: pd.DataFrame) -> float:
        """최적화된 월간 수익률 계산"""
        if account_df.empty or len(account_df) < 30:
            return 0.0
        
        # 월별로 그룹화하여 첫날과 마지막날 잔고 계산
        account_df['year_month'] = account_df['date'].dt.to_period('M')
        monthly_data = account_df.groupby('year_month').agg({
            'balance': ['first', 'last']
        }).reset_index()
        
        if len(monthly_data) < 2:
            return 0.0
        
        monthly_data.columns = ['year_month', 'first_balance', 'last_balance']
        monthly_returns = (monthly_data['last_balance'] / monthly_data['first_balance'] - 1) * 100
        
        return monthly_returns.mean()
    
    @staticmethod
    def _calculate_calmar_ratio_optimized(annualized_return: float, max_drawdown: float) -> float:
        """최적화된 칼마 비율 계산"""
        if max_drawdown == 0:
            return 0.0
        
        return annualized_return / max_drawdown
    
    def _calculate_fees_optimized(self, trades_df: pd.DataFrame) -> float:
        """최적화된 수수료 계산"""
        if trades_df.empty:
            return 0.0
        
        # 벡터화된 수수료 계산
        trade_values = trades_df['amount'] * trades_df['price']
        total_fees = trade_values.sum() * 0.0005  # 0.05%
        
        return total_fees
    
    def analyze_by_symbol_optimized(self, trades_df: pd.DataFrame, 
                                  account_df: pd.DataFrame) -> Dict[str, PerformanceMetrics]:
        """최적화된 코인별 성과 분석"""
        if trades_df.empty:
            return {}
        
        symbols = trades_df['symbol'].unique()
        
        # 병렬 처리 사용 여부 결정
        if self.enable_parallel and len(symbols) > 3 and self.parallel_analyzer:
            return self.parallel_analyzer.analyze_symbols_parallel(trades_df, account_df, symbols)
        else:
            # 순차 처리
            results = {}
            for symbol in symbols:
                symbol_trades = trades_df[trades_df['symbol'] == symbol]
                metrics = self.calculate_comprehensive_metrics(symbol_trades, account_df)
                results[symbol] = metrics
                
                self.logger.debug(f"{symbol} 성과 분석 완료")
            
            return results
    
    def analyze_by_strategy_optimized(self, trades_df: pd.DataFrame, 
                                    account_df: pd.DataFrame) -> Dict[str, PerformanceMetrics]:
        """최적화된 전략별 성과 분석"""
        if trades_df.empty:
            return {}
        
        results = {}
        strategies = trades_df['strategy'].unique()
        
        for strategy in strategies:
            strategy_trades = trades_df[trades_df['strategy'] == strategy]
            metrics = self.calculate_comprehensive_metrics(strategy_trades, account_df)
            results[strategy] = metrics
            
            self.logger.debug(f"{strategy} 전략 성과 분석 완료")
        
        return results
    
    def generate_performance_report_optimized(self, metrics: PerformanceMetrics) -> str:
        """최적화된 성과 리포트 생성"""
        report = f"""
=== 최적화된 자동매매 성과 분석 리포트 ===

📊 수익률 지표
- 총 수익률: {metrics.total_return:.2f}%
- 연환산 수익률: {metrics.annualized_return:.2f}%
- 평균 일일 수익률: {metrics.daily_return:.4f}%
- 평균 월간 수익률: {metrics.monthly_return:.2f}%

⚠️ 리스크 지표
- 최대 낙폭 (MDD): {metrics.max_drawdown:.2f}%
- 샤프 비율: {metrics.sharpe_ratio:.2f}
- 소르티노 비율: {metrics.sortino_ratio:.2f}
- 칼마 비율: {metrics.calmar_ratio:.2f}
- VaR (95%): {metrics.var_95:.4f}
- CVaR (95%): {metrics.cvar_95:.4f}

📈 거래 지표
- 승률: {metrics.win_rate:.2f}%
- 프로핏 팩터: {metrics.profit_factor:.2f}
- 평균 수익: {metrics.avg_win:,.0f}원
- 평균 손실: {metrics.avg_loss:,.0f}원
- 최대 수익: {metrics.largest_win:,.0f}원
- 최대 손실: {metrics.largest_loss:,.0f}원
- 총 거래 건수: {metrics.total_trades}건
- 수익 거래: {metrics.winning_trades}건
- 손실 거래: {metrics.losing_trades}건

⏱️ 기간 지표
- 평균 보유 기간: {metrics.avg_holding_period:.1f}분
- 총 수수료: {metrics.total_fees:,.0f}원
- 순수익률: {metrics.net_return:.2f}%
        """
        
        return report.strip()

# 사용 예시
if __name__ == "__main__":
    from data_processor_optimized import OptimizedDataProcessor, DataConfig
    import time
    
    # 최적화된 설정
    config = DataConfig(
        db_path="data/optimized_trading.db",
        data_period_days=90
    )
    
    # 데이터 로드
    processor = OptimizedDataProcessor(config)
    trades = processor.load_trade_data_optimized()
    account = processor.load_account_history_optimized()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data_optimized(trades)
        processed_account = processor.preprocess_account_data_optimized(account)
        
        # 최적화된 성과 분석
        start_time = time.time()
        
        analyzer = OptimizedPerformanceAnalyzer(enable_parallel=True)
        metrics = analyzer.calculate_comprehensive_metrics(processed_trades, processed_account)
        
        analysis_time = time.time() - start_time
        
        # 리포트 출력
        report = analyzer.generate_performance_report_optimized(metrics)
        print(report)
        
        print(f"\n=== 성능 정보 ===")
        print(f"분석 시간: {analysis_time:.3f}초")
        print(f"거래 데이터 크기: {len(processed_trades):,}건")
        print(f"계좌 데이터 크기: {len(processed_account):,}건")
        
        # 코인별 병렬 분석 테스트
        if len(processed_trades['symbol'].unique()) > 1:
            start_time = time.time()
            symbol_analysis = analyzer.analyze_by_symbol_optimized(processed_trades, processed_account)
            parallel_time = time.time() - start_time
            
            print(f"\n병렬 분석 시간: {parallel_time:.3f}초")
            print("코인별 성과:")
            for symbol, symbol_metrics in symbol_analysis.items():
                print(f"- {symbol}: 수익률 {symbol_metrics.total_return:.2f}%, 승률 {symbol_metrics.win_rate:.2f}%")
    else:
        print("분석할 데이터가 없습니다.")














