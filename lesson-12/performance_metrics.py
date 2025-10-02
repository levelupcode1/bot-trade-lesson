#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 성과 지표 계산 모듈
수익률, 거래 지표, 리스크 지표를 종합적으로 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

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

class ReturnMetricsCalculator:
    """수익률 지표 계산 클래스"""
    
    @staticmethod
    def calculate_total_return(account_df: pd.DataFrame) -> float:
        """총 수익률 계산"""
        if account_df.empty or len(account_df) < 2:
            return 0.0
        
        initial_balance = account_df['balance'].iloc[0]
        final_balance = account_df['balance'].iloc[-1]
        
        return (final_balance - initial_balance) / initial_balance * 100
    
    @staticmethod
    def calculate_annualized_return(total_return: float, days: int) -> float:
        """연환산 수익률 계산"""
        if days <= 0:
            return 0.0
        
        years = days / 365.25
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100
    
    @staticmethod
    def calculate_daily_returns(account_df: pd.DataFrame) -> pd.Series:
        """일일 수익률 계산"""
        if account_df.empty or len(account_df) < 2:
            return pd.Series()
        
        return account_df['balance'].pct_change().dropna()
    
    @staticmethod
    def calculate_monthly_returns(account_df: pd.DataFrame) -> pd.Series:
        """월간 수익률 계산"""
        if account_df.empty:
            return pd.Series()
        
        # 월별로 그룹화하여 첫날과 마지막날 잔고 계산
        account_df['year_month'] = account_df['date'].dt.to_period('M')
        monthly_data = account_df.groupby('year_month').agg({
            'balance': ['first', 'last']
        }).reset_index()
        
        if len(monthly_data) < 2:
            return pd.Series()
        
        monthly_data.columns = ['year_month', 'first_balance', 'last_balance']
        monthly_returns = (monthly_data['last_balance'] / monthly_data['first_balance'] - 1) * 100
        
        return monthly_returns

class RiskMetricsCalculator:
    """리스크 지표 계산 클래스"""
    
    @staticmethod
    def calculate_max_drawdown(account_df: pd.DataFrame) -> float:
        """최대 낙폭(MDD) 계산"""
        if account_df.empty or len(account_df) < 2:
            return 0.0
        
        balance = account_df['balance'].values
        peak = balance[0]
        max_dd = 0.0
        
        for value in balance:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100
    
    @staticmethod
    def calculate_sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """샤프 비율 계산"""
        if daily_returns.empty:
            return 0.0
        
        excess_returns = daily_returns - (risk_free_rate / 365)
        if excess_returns.std() == 0:
            return 0.0
        
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(365)
    
    @staticmethod
    def calculate_sortino_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """소르티노 비율 계산 (하방 위험만 고려)"""
        if daily_returns.empty:
            return 0.0
        
        excess_returns = daily_returns - (risk_free_rate / 365)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        downside_deviation = downside_returns.std() * np.sqrt(365)
        return (excess_returns.mean() * 365) / downside_deviation
    
    @staticmethod
    def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        """칼마 비율 계산"""
        if max_drawdown == 0:
            return 0.0
        
        return annualized_return / max_drawdown
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
        """VaR (Value at Risk) 계산"""
        if returns.empty:
            return 0.0
        
        return np.percentile(returns, (1 - confidence) * 100)
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
        """CVaR (Conditional Value at Risk) 계산"""
        if returns.empty:
            return 0.0
        
        var = RiskMetricsCalculator.calculate_var(returns, confidence)
        return returns[returns <= var].mean()

class TradingMetricsCalculator:
    """거래 지표 계산 클래스"""
    
    @staticmethod
    def calculate_win_rate(trades_df: pd.DataFrame) -> float:
        """승률 계산"""
        if trades_df.empty:
            return 0.0
        
        # 매도 거래만 고려 (실제 손익이 발생하는 거래)
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0
        
        winning_trades = len(sell_trades[sell_trades['pnl'] > 0])
        return (winning_trades / len(sell_trades)) * 100
    
    @staticmethod
    def calculate_profit_factor(trades_df: pd.DataFrame) -> float:
        """프로핏 팩터 계산 (총 수익 / 총 손실)"""
        if trades_df.empty:
            return 0.0
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0
        
        total_profit = sell_trades[sell_trades['pnl'] > 0]['pnl'].sum()
        total_loss = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].sum())
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        return total_profit / total_loss
    
    @staticmethod
    def calculate_avg_win_loss(trades_df: pd.DataFrame) -> Tuple[float, float]:
        """평균 수익/손실 계산"""
        if trades_df.empty:
            return 0.0, 0.0
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0, 0.0
        
        wins = sell_trades[sell_trades['pnl'] > 0]
        losses = sell_trades[sell_trades['pnl'] < 0]
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0.0
        avg_loss = losses['pnl'].mean() if not losses.empty else 0.0
        
        return avg_win, avg_loss
    
    @staticmethod
    def calculate_largest_win_loss(trades_df: pd.DataFrame) -> Tuple[float, float]:
        """최대 수익/손실 계산"""
        if trades_df.empty:
            return 0.0, 0.0
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0, 0.0
        
        largest_win = sell_trades['pnl'].max() if not sell_trades.empty else 0.0
        largest_loss = sell_trades['pnl'].min() if not sell_trades.empty else 0.0
        
        return largest_win, largest_loss
    
    @staticmethod
    def calculate_avg_holding_period(trades_df: pd.DataFrame) -> float:
        """평균 보유 기간 계산 (분 단위)"""
        if trades_df.empty:
            return 0.0
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        if sell_trades.empty:
            return 0.0
        
        return sell_trades['holding_period'].mean()
    
    @staticmethod
    def calculate_trade_statistics(trades_df: pd.DataFrame) -> Dict:
        """거래 통계 계산"""
        if trades_df.empty:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        
        return {
            'total_trades': len(trades_df),
            'buy_trades': len(trades_df[trades_df['side'] == 'BUY']),
            'sell_trades': len(sell_trades),
            'winning_trades': len(sell_trades[sell_trades['pnl'] > 0]) if not sell_trades.empty else 0,
            'losing_trades': len(sell_trades[sell_trades['pnl'] < 0]) if not sell_trades.empty else 0
        }

class PerformanceAnalyzer:
    """종합 성과 분석 클래스"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_comprehensive_metrics(self, trades_df: pd.DataFrame, 
                                      account_df: pd.DataFrame) -> PerformanceMetrics:
        """종합 성과 지표 계산"""
        try:
            # 기본 검증
            if trades_df.empty and account_df.empty:
                self.logger.warning("분석할 데이터가 없습니다")
                return PerformanceMetrics()
            
            # 수익률 지표 계산
            total_return = ReturnMetricsCalculator.calculate_total_return(account_df)
            days = len(account_df) if not account_df.empty else 1
            annualized_return = ReturnMetricsCalculator.calculate_annualized_return(total_return, days)
            
            daily_returns = ReturnMetricsCalculator.calculate_daily_returns(account_df)
            monthly_returns = ReturnMetricsCalculator.calculate_monthly_returns(account_df)
            
            daily_return = daily_returns.mean() * 100 if not daily_returns.empty else 0.0
            monthly_return = monthly_returns.mean() if not monthly_returns.empty else 0.0
            
            # 리스크 지표 계산
            max_drawdown = RiskMetricsCalculator.calculate_max_drawdown(account_df)
            sharpe_ratio = RiskMetricsCalculator.calculate_sharpe_ratio(
                daily_returns, self.risk_free_rate
            )
            sortino_ratio = RiskMetricsCalculator.calculate_sortino_ratio(
                daily_returns, self.risk_free_rate
            )
            calmar_ratio = RiskMetricsCalculator.calculate_calmar_ratio(
                annualized_return, max_drawdown
            )
            
            var_95 = RiskMetricsCalculator.calculate_var(daily_returns, 0.95)
            cvar_95 = RiskMetricsCalculator.calculate_cvar(daily_returns, 0.95)
            
            # 거래 지표 계산
            win_rate = TradingMetricsCalculator.calculate_win_rate(trades_df)
            profit_factor = TradingMetricsCalculator.calculate_profit_factor(trades_df)
            avg_win, avg_loss = TradingMetricsCalculator.calculate_avg_win_loss(trades_df)
            largest_win, largest_loss = TradingMetricsCalculator.calculate_largest_win_loss(trades_df)
            
            trade_stats = TradingMetricsCalculator.calculate_trade_statistics(trades_df)
            avg_holding_period = TradingMetricsCalculator.calculate_avg_holding_period(trades_df)
            
            # 수수료 계산 (간단한 시뮬레이션: 거래 금액의 0.05%)
            if not trades_df.empty:
                total_trade_value = (trades_df['amount'] * trades_df['price']).sum()
                total_fees = total_trade_value * 0.0005  # 0.05%
            else:
                total_fees = 0.0
            
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
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                total_trades=trade_stats['total_trades'],
                winning_trades=trade_stats['winning_trades'],
                losing_trades=trade_stats['losing_trades'],
                
                # 기간 지표
                avg_holding_period=avg_holding_period,
                total_fees=total_fees,
                net_return=net_return
            )
            
            self.logger.info("종합 성과 지표 계산 완료")
            return metrics
            
        except Exception as e:
            self.logger.error(f"성과 지표 계산 오류: {e}")
            return PerformanceMetrics()
    
    def analyze_by_symbol(self, trades_df: pd.DataFrame, 
                         account_df: pd.DataFrame) -> Dict[str, PerformanceMetrics]:
        """코인별 성과 분석"""
        if trades_df.empty:
            return {}
        
        results = {}
        symbols = trades_df['symbol'].unique()
        
        for symbol in symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            metrics = self.calculate_comprehensive_metrics(symbol_trades, account_df)
            results[symbol] = metrics
            
            self.logger.info(f"{symbol} 성과 분석 완료")
        
        return results
    
    def analyze_by_strategy(self, trades_df: pd.DataFrame, 
                          account_df: pd.DataFrame) -> Dict[str, PerformanceMetrics]:
        """전략별 성과 분석"""
        if trades_df.empty:
            return {}
        
        results = {}
        strategies = trades_df['strategy'].unique()
        
        for strategy in strategies:
            strategy_trades = trades_df[trades_df['strategy'] == strategy]
            metrics = self.calculate_comprehensive_metrics(strategy_trades, account_df)
            results[strategy] = metrics
            
            self.logger.info(f"{strategy} 전략 성과 분석 완료")
        
        return results
    
    def analyze_by_time_period(self, trades_df: pd.DataFrame, 
                             account_df: pd.DataFrame) -> Dict[str, PerformanceMetrics]:
        """시간대별 성과 분석"""
        if trades_df.empty:
            return {}
        
        results = {}
        
        # 시간대별 분석
        trades_df['hour'] = trades_df['created_at'].dt.hour
        hourly_groups = trades_df.groupby('hour')
        
        for hour, group_trades in hourly_groups:
            metrics = self.calculate_comprehensive_metrics(group_trades, account_df)
            results[f"hour_{hour:02d}"] = metrics
        
        # 요일별 분석
        trades_df['day_of_week'] = trades_df['created_at'].dt.day_name()
        daily_groups = trades_df.groupby('day_of_week')
        
        for day, group_trades in daily_groups:
            metrics = self.calculate_comprehensive_metrics(group_trades, account_df)
            results[f"day_{day}"] = metrics
        
        self.logger.info("시간대별 성과 분석 완료")
        return results
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """성과 리포트 생성"""
        report = f"""
=== 자동매매 성과 분석 리포트 ===

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
    from data_processor import TradingDataProcessor, DataConfig
    
    # 설정 및 데이터 로드
    config = DataConfig()
    processor = TradingDataProcessor(config)
    
    trades = processor.load_trade_data()
    account = processor.load_account_history()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data(trades)
        processed_account = processor.preprocess_account_data(account)
        
        # 성과 분석
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.calculate_comprehensive_metrics(processed_trades, processed_account)
        
        # 리포트 출력
        report = analyzer.generate_performance_report(metrics)
        print(report)
        
        # 코인별 분석
        symbol_analysis = analyzer.analyze_by_symbol(processed_trades, processed_account)
        print(f"\n=== 코인별 분석 ===")
        for symbol, symbol_metrics in symbol_analysis.items():
            print(f"{symbol}: 수익률 {symbol_metrics.total_return:.2f}%, 승률 {symbol_metrics.win_rate:.2f}%")
    else:
        print("분석할 데이터가 없습니다.")

