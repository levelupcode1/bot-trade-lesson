#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 시각화 모듈
matplotlib, seaborn을 활용한 차트 및 그래프 생성
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
from dataclasses import dataclass

# 한글 폰트 설정 (메모리 참조: 한글 폰트 문제 방지)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChartConfig:
    """차트 설정 클래스"""
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 100
    style: str = 'seaborn-v0_8'
    color_palette: str = 'viridis'
    save_path: str = "charts/"
    show_grid: bool = True
    tight_layout: bool = True

class TradingVisualizer:
    """거래 데이터 시각화 클래스"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
        self.logger = logging.getLogger(__name__)
        
        # 차트 저장 디렉토리 생성
        Path(self.config.save_path).mkdir(parents=True, exist_ok=True)
        
        # 스타일 설정
        plt.style.use(self.config.style)
        sns.set_palette(self.config.color_palette)
    
    def create_equity_curve(self, account_df: pd.DataFrame, 
                          title: str = "Portfolio Equity Curve",
                          save_file: Optional[str] = None) -> plt.Figure:
        """자산 곡선 차트 생성"""
        if account_df.empty:
            self.logger.warning("계좌 데이터가 없어 자산 곡선을 생성할 수 없습니다")
            return None
        
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        # 자산 곡선 그리기
        ax.plot(account_df['date'], account_df['balance'], 
                linewidth=2, color='blue', label='Portfolio Value')
        
        # 누적 수익률 추가 (오른쪽 축)
        ax2 = ax.twinx()
        ax2.plot(account_df['date'], account_df['cumulative_return_pct'], 
                 linewidth=1, color='green', alpha=0.7, label='Cumulative Return %')
        ax2.set_ylabel('Cumulative Return (%)', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        
        # 설정
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value (KRW)')
        ax.grid(self.config.show_grid, alpha=0.3)
        
        # 날짜 포맷
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 범례
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"자산 곡선 차트 저장: {save_path}")
        
        return fig
    
    def create_drawdown_chart(self, account_df: pd.DataFrame,
                            title: str = "Drawdown Analysis",
                            save_file: Optional[str] = None) -> plt.Figure:
        """낙폭 차트 생성"""
        if account_df.empty:
            self.logger.warning("계좌 데이터가 없어 낙폭 차트를 생성할 수 없습니다")
            return None
        
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        # 낙폭 차트 (음수 영역을 빨간색으로)
        ax.fill_between(account_df['date'], account_df['drawdown_pct'], 0,
                       color='red', alpha=0.3, label='Drawdown')
        ax.plot(account_df['date'], account_df['drawdown_pct'], 
                color='red', linewidth=1)
        
        # 설정
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(self.config.show_grid, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 날짜 포맷
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 범례
        ax.legend()
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"낙폭 차트 저장: {save_path}")
        
        return fig
    
    def create_trade_distribution(self, trades_df: pd.DataFrame,
                                title: str = "Trade Distribution Analysis",
                                save_file: Optional[str] = None) -> plt.Figure:
        """거래 분포 히스토그램 생성"""
        if trades_df.empty:
            self.logger.warning("거래 데이터가 없어 분포 차트를 생성할 수 없습니다")
            return None
        
        # 매도 거래만 분석 (실제 손익이 발생하는 거래)
        sell_trades = trades_df[trades_df['side'] == 'SELL'].copy()
        if sell_trades.empty:
            self.logger.warning("매도 거래 데이터가 없습니다")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 1. P&L 분포
        ax1 = axes[0, 0]
        ax1.hist(sell_trades['pnl'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Break-even')
        ax1.set_title('P&L Distribution')
        ax1.set_xlabel('P&L (KRW)')
        ax1.set_ylabel('Frequency')
        ax1.grid(self.config.show_grid, alpha=0.3)
        ax1.legend()
        
        # 2. 보유 기간 분포
        ax2 = axes[0, 1]
        ax2.hist(sell_trades['holding_period'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title('Holding Period Distribution')
        ax2.set_xlabel('Holding Period (minutes)')
        ax2.set_ylabel('Frequency')
        ax2.grid(self.config.show_grid, alpha=0.3)
        
        # 3. 거래 크기 분포
        ax3 = axes[1, 0]
        trade_sizes = sell_trades['amount'] * sell_trades['price']
        ax3.hist(trade_sizes, bins=20, alpha=0.7, color='orange', edgecolor='black')
        ax3.set_title('Trade Size Distribution')
        ax3.set_xlabel('Trade Size (KRW)')
        ax3.set_ylabel('Frequency')
        ax3.grid(self.config.show_grid, alpha=0.3)
        
        # 4. 승/패 비율
        ax4 = axes[1, 1]
        win_loss = sell_trades['pnl'].apply(lambda x: 'Win' if x > 0 else 'Loss')
        win_loss_counts = win_loss.value_counts()
        
        colors = ['green' if x == 'Win' else 'red' for x in win_loss_counts.index]
        bars = ax4.bar(win_loss_counts.index, win_loss_counts.values, color=colors, alpha=0.7)
        ax4.set_title('Win/Loss Ratio')
        ax4.set_ylabel('Number of Trades')
        ax4.grid(self.config.show_grid, alpha=0.3)
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}\n({height/len(sell_trades)*100:.1f}%)',
                    ha='center', va='bottom')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"거래 분포 차트 저장: {save_path}")
        
        return fig
    
    def create_monthly_heatmap(self, account_df: pd.DataFrame,
                             title: str = "Monthly Returns Heatmap",
                             save_file: Optional[str] = None) -> plt.Figure:
        """월별 성과 히트맵 생성"""
        if account_df.empty or len(account_df) < 30:
            self.logger.warning("월별 히트맵을 생성하기 위한 충분한 데이터가 없습니다")
            return None
        
        # 월별 수익률 계산
        account_df['year_month'] = account_df['date'].dt.to_period('M')
        monthly_data = account_df.groupby('year_month').agg({
            'balance': ['first', 'last']
        }).reset_index()
        
        monthly_data.columns = ['year_month', 'first_balance', 'last_balance']
        monthly_data['monthly_return'] = (monthly_data['last_balance'] / monthly_data['first_balance'] - 1) * 100
        
        # 피벗 테이블 생성
        monthly_data['year'] = monthly_data['year_month'].dt.year
        monthly_data['month'] = monthly_data['year_month'].dt.month
        
        pivot_data = monthly_data.pivot(index='year', columns='month', values='monthly_return')
        
        fig, ax = plt.subplots(figsize=(12, 6), dpi=self.config.dpi)
        
        # 히트맵 생성
        sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                   cbar_kws={'label': 'Monthly Return (%)'}, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"월별 히트맵 저장: {save_path}")
        
        return fig
    
    def create_risk_return_scatter(self, symbol_metrics: Dict[str, Any],
                                 title: str = "Risk vs Return Analysis",
                                 save_file: Optional[str] = None) -> plt.Figure:
        """리스크-수익 스캐터 플롯 생성"""
        if not symbol_metrics:
            self.logger.warning("심볼별 메트릭 데이터가 없습니다")
            return None
        
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        # 데이터 추출
        symbols = list(symbol_metrics.keys())
        returns = [metrics.total_return for metrics in symbol_metrics.values()]
        risks = [metrics.max_drawdown for metrics in symbol_metrics.values()]
        
        # 색상 맵 (수익률에 따라)
        colors = plt.cm.viridis(np.linspace(0, 1, len(symbols)))
        
        # 스캐터 플롯
        scatter = ax.scatter(risks, returns, c=colors, s=100, alpha=0.7, edgecolors='black')
        
        # 각 점에 심볼 이름 표시
        for i, symbol in enumerate(symbols):
            ax.annotate(symbol, (risks[i], returns[i]), 
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=10, fontweight='bold')
        
        # 설정
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Max Drawdown (%)')
        ax.set_ylabel('Total Return (%)')
        ax.grid(self.config.show_grid, alpha=0.3)
        
        # 기준선 추가
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        
        # 색상바
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Return Level')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"리스크-수익 스캐터 플롯 저장: {save_path}")
        
        return fig
    
    def create_strategy_comparison(self, strategy_metrics: Dict[str, Any],
                                 title: str = "Strategy Performance Comparison",
                                 save_file: Optional[str] = None) -> plt.Figure:
        """전략별 성과 비교 차트"""
        if not strategy_metrics:
            self.logger.warning("전략별 메트릭 데이터가 없습니다")
            return None
        
        strategies = list(strategy_metrics.keys())
        
        # 비교할 지표들
        metrics_to_compare = ['total_return', 'win_rate', 'sharpe_ratio', 'max_drawdown']
        metric_labels = ['Total Return (%)', 'Win Rate (%)', 'Sharpe Ratio', 'Max Drawdown (%)']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(strategies)))
        
        for i, (metric, label) in enumerate(zip(metrics_to_compare, metric_labels)):
            ax = axes[i//2, i%2]
            
            values = [getattr(strategy_metrics[strategy], metric) for strategy in strategies]
            
            bars = ax.bar(strategies, values, color=colors, alpha=0.7, edgecolor='black')
            ax.set_title(label)
            ax.set_ylabel(label)
            ax.grid(self.config.show_grid, alpha=0.3)
            
            # 막대 위에 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
            
            # x축 레이블 회전
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"전략 비교 차트 저장: {save_path}")
        
        return fig
    
    def create_daily_returns_histogram(self, account_df: pd.DataFrame,
                                     title: str = "Daily Returns Distribution",
                                     save_file: Optional[str] = None) -> plt.Figure:
        """일일 수익률 히스토그램 생성"""
        if account_df.empty or 'daily_return_pct' not in account_df.columns:
            self.logger.warning("일일 수익률 데이터가 없습니다")
            return None
        
        daily_returns = account_df['daily_return_pct'].dropna()
        
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        # 히스토그램
        n, bins, patches = ax.hist(daily_returns, bins=30, alpha=0.7, 
                                 color='skyblue', edgecolor='black')
        
        # 통계 정보 추가
        mean_return = daily_returns.mean()
        std_return = daily_returns.std()
        
        ax.axvline(x=mean_return, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_return:.2f}%')
        ax.axvline(x=mean_return + std_return, color='orange', linestyle='--', alpha=0.7,
                  label=f'+1σ: {mean_return + std_return:.2f}%')
        ax.axvline(x=mean_return - std_return, color='orange', linestyle='--', alpha=0.7,
                  label=f'-1σ: {mean_return - std_return:.2f}%')
        
        # 정규분포 곡선 추가
        x = np.linspace(daily_returns.min(), daily_returns.max(), 100)
        normal_curve = ((1/(std_return * np.sqrt(2 * np.pi))) * 
                       np.exp(-0.5 * ((x - mean_return) / std_return) ** 2))
        normal_curve = normal_curve * len(daily_returns) * (bins[1] - bins[0])
        ax.plot(x, normal_curve, 'r-', linewidth=2, alpha=0.8, label='Normal Distribution')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Daily Return (%)')
        ax.set_ylabel('Frequency')
        ax.grid(self.config.show_grid, alpha=0.3)
        ax.legend()
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"일일 수익률 히스토그램 저장: {save_path}")
        
        return fig
    
    def create_correlation_heatmap(self, account_df: pd.DataFrame,
                                 title: str = "Performance Metrics Correlation",
                                 save_file: Optional[str] = None) -> plt.Figure:
        """성과 지표 상관관계 히트맵"""
        if account_df.empty:
            self.logger.warning("계좌 데이터가 없습니다")
            return None
        
        # 상관관계 분석할 컬럼들
        correlation_columns = ['balance', 'daily_return_pct', 'cumulative_return_pct', 'drawdown_pct']
        available_columns = [col for col in correlation_columns if col in account_df.columns]
        
        if len(available_columns) < 2:
            self.logger.warning("상관관계 분석을 위한 충분한 컬럼이 없습니다")
            return None
        
        correlation_data = account_df[available_columns].corr()
        
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self.config.dpi)
        
        # 히트맵 생성
        sns.heatmap(correlation_data, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                   square=True, cbar_kws={'label': 'Correlation Coefficient'}, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"상관관계 히트맵 저장: {save_path}")
        
        return fig
    
    def create_comprehensive_dashboard(self, trades_df: pd.DataFrame, 
                                     account_df: pd.DataFrame,
                                     title: str = "Trading Dashboard",
                                     save_file: Optional[str] = None) -> plt.Figure:
        """종합 대시보드 생성"""
        fig = plt.figure(figsize=(20, 16), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=20, fontweight='bold')
        
        # 3x3 그리드 레이아웃
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 자산 곡선 (큰 차트)
        ax1 = fig.add_subplot(gs[0, :2])
        if not account_df.empty:
            ax1.plot(account_df['date'], account_df['balance'], linewidth=2, color='blue')
            ax1.set_title('Portfolio Value', fontweight='bold')
            ax1.set_ylabel('Balance (KRW)')
            ax1.grid(True, alpha=0.3)
        
        # 2. 일일 수익률
        ax2 = fig.add_subplot(gs[0, 2])
        if not account_df.empty and 'daily_return_pct' in account_df.columns:
            daily_returns = account_df['daily_return_pct'].dropna()
            ax2.hist(daily_returns, bins=20, alpha=0.7, color='green')
            ax2.set_title('Daily Returns', fontweight='bold')
            ax2.set_xlabel('Return (%)')
            ax2.grid(True, alpha=0.3)
        
        # 3. 낙폭 차트
        ax3 = fig.add_subplot(gs[1, :2])
        if not account_df.empty:
            ax3.fill_between(account_df['date'], account_df['drawdown_pct'], 0,
                           color='red', alpha=0.3)
            ax3.plot(account_df['date'], account_df['drawdown_pct'], color='red')
            ax3.set_title('Drawdown', fontweight='bold')
            ax3.set_ylabel('Drawdown (%)')
            ax3.grid(True, alpha=0.3)
        
        # 4. 거래 P&L 분포
        ax4 = fig.add_subplot(gs[1, 2])
        if not trades_df.empty:
            sell_trades = trades_df[trades_df['side'] == 'SELL']
            if not sell_trades.empty:
                ax4.hist(sell_trades['pnl'], bins=15, alpha=0.7, color='orange')
                ax4.axvline(x=0, color='red', linestyle='--')
                ax4.set_title('P&L Distribution', fontweight='bold')
                ax4.set_xlabel('P&L (KRW)')
                ax4.grid(True, alpha=0.3)
        
        # 5. 심볼별 거래 수
        ax5 = fig.add_subplot(gs[2, 0])
        if not trades_df.empty:
            symbol_counts = trades_df['symbol'].value_counts()
            ax5.bar(symbol_counts.index, symbol_counts.values, alpha=0.7)
            ax5.set_title('Trades by Symbol', fontweight='bold')
            ax5.set_ylabel('Number of Trades')
            plt.setp(ax5.get_xticklabels(), rotation=45)
        
        # 6. 전략별 거래 수
        ax6 = fig.add_subplot(gs[2, 1])
        if not trades_df.empty:
            strategy_counts = trades_df['strategy'].value_counts()
            ax6.bar(strategy_counts.index, strategy_counts.values, alpha=0.7)
            ax6.set_title('Trades by Strategy', fontweight='bold')
            ax6.set_ylabel('Number of Trades')
            plt.setp(ax6.get_xticklabels(), rotation=45)
        
        # 7. 시간대별 거래
        ax7 = fig.add_subplot(gs[2, 2])
        if not trades_df.empty:
            trades_df['hour'] = trades_df['created_at'].dt.hour
            hourly_counts = trades_df['hour'].value_counts().sort_index()
            ax7.bar(hourly_counts.index, hourly_counts.values, alpha=0.7)
            ax7.set_title('Trades by Hour', fontweight='bold')
            ax7.set_xlabel('Hour')
            ax7.set_ylabel('Number of Trades')
        
        if save_file:
            save_path = Path(self.config.save_path) / f"{save_file}.png"
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
            self.logger.info(f"종합 대시보드 저장: {save_path}")
        
        return fig

# 사용 예시
if __name__ == "__main__":
    from data_processor import TradingDataProcessor, DataConfig
    from performance_metrics import PerformanceAnalyzer
    
    # 설정 및 데이터 로드
    config = DataConfig()
    processor = TradingDataProcessor(config)
    
    trades = processor.load_trade_data()
    account = processor.load_account_history()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data(trades)
        processed_account = processor.preprocess_account_data(account)
        
        # 시각화 생성
        visualizer = TradingVisualizer()
        
        # 개별 차트 생성
        visualizer.create_equity_curve(processed_account, save_file="equity_curve")
        visualizer.create_drawdown_chart(processed_account, save_file="drawdown")
        visualizer.create_trade_distribution(processed_trades, save_file="trade_distribution")
        visualizer.create_daily_returns_histogram(processed_account, save_file="daily_returns")
        
        # 종합 대시보드 생성
        visualizer.create_comprehensive_dashboard(processed_trades, processed_account, 
                                                save_file="comprehensive_dashboard")
        
        print("모든 차트가 생성되었습니다.")
        
        # 차트 표시
        plt.show()
    else:
        print("시각화할 데이터가 없습니다.")

