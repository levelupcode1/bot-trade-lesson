#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 시각화 모듈 (최적화 버전)
메모리 효율성과 성능을 위한 최적화된 시각화
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
import gc
import psutil
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import io
import base64

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChartConfig:
    """차트 설정 클래스 (최적화 버전)"""
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 100
    style: str = 'seaborn-v0_8'
    color_palette: str = 'viridis'
    save_path: str = "charts/"
    show_grid: bool = True
    tight_layout: bool = True
    
    # 최적화 설정
    max_figures: int = 10  # 최대 열 수 있는 figure 수
    memory_limit_mb: int = 500  # 메모리 제한 (MB)
    enable_caching: bool = True  # 차트 캐싱 사용
    batch_size: int = 1000  # 배치 처리 크기
    compression_quality: int = 95  # 이미지 압축 품질

class MemoryOptimizedChartManager:
    """메모리 최적화된 차트 관리자"""
    
    def __init__(self, config: ChartConfig):
        self.config = config
        self.active_figures = []
        self.process = psutil.Process()
        self.lock = threading.Lock()
        
    def get_memory_usage_mb(self) -> float:
        """현재 메모리 사용량 (MB) 반환"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def check_memory_and_cleanup(self) -> None:
        """메모리 사용량 확인 및 정리"""
        current_memory = self.get_memory_usage_mb()
        
        if current_memory > self.config.memory_limit_mb:
            logger.warning(f"메모리 사용량이 {current_memory:.1f}MB로 제한을 초과했습니다. 정리 중...")
            self.cleanup_old_figures()
            gc.collect()
    
    def cleanup_old_figures(self) -> None:
        """오래된 figure 정리"""
        with self.lock:
            while len(self.active_figures) > self.config.max_figures:
                old_fig = self.active_figures.pop(0)
                plt.close(old_fig)
                logger.debug("오래된 figure 정리됨")
    
    def register_figure(self, fig) -> None:
        """figure 등록"""
        with self.lock:
            self.active_figures.append(fig)
            self.cleanup_old_figures()
    
    def close_all_figures(self) -> None:
        """모든 figure 닫기"""
        with self.lock:
            for fig in self.active_figures:
                plt.close(fig)
            self.active_figures.clear()
            gc.collect()

class OptimizedTradingVisualizer:
    """최적화된 거래 데이터 시각화 클래스"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
        self.logger = logging.getLogger(__name__)
        self.chart_manager = MemoryOptimizedChartManager(self.config)
        
        # 차트 저장 디렉토리 생성
        Path(self.config.save_path).mkdir(parents=True, exist_ok=True)
        
        # 스타일 설정
        plt.style.use(self.config.style)
        sns.set_palette(self.config.color_palette)
        
        # matplotlib 백엔드 최적화
        plt.rcParams['figure.max_open_warning'] = 0  # 경고 비활성화
        
    def _create_optimized_figure(self, figsize: Tuple[int, int] = None, 
                               dpi: int = None) -> plt.Figure:
        """최적화된 figure 생성"""
        if figsize is None:
            figsize = self.config.figure_size
        if dpi is None:
            dpi = self.config.dpi
            
        # 메모리 확인
        self.chart_manager.check_memory_and_cleanup()
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # figure 등록
        self.chart_manager.register_figure(fig)
        
        return fig, ax
    
    def _save_figure_optimized(self, fig: plt.Figure, filename: str, 
                             format: str = 'png') -> str:
        """최적화된 figure 저장"""
        try:
            save_path = Path(self.config.save_path) / f"{filename}.{format}"
            
            # 압축 옵션 설정
            save_kwargs = {
                'dpi': self.config.dpi,
                'bbox_inches': 'tight',
                'facecolor': 'white',
                'edgecolor': 'none'
            }
            
            if format == 'png':
                save_kwargs['optimize'] = True
                save_kwargs['compress_level'] = 6
            
            fig.savefig(save_path, **save_kwargs)
            
            # figure 닫기 (메모리 절약)
            plt.close(fig)
            
            self.logger.info(f"최적화된 차트 저장: {save_path}")
            return str(save_path)
            
        except Exception as e:
            self.logger.error(f"차트 저장 오류: {e}")
            plt.close(fig)
            return ""
    
    @lru_cache(maxsize=32)
    def _get_cached_colors(self, n_colors: int) -> List[str]:
        """캐시된 색상 팔레트 반환"""
        return sns.color_palette(self.config.color_palette, n_colors).as_hex()
    
    def create_equity_curve_optimized(self, account_df: pd.DataFrame, 
                                    title: str = "Portfolio Equity Curve",
                                    save_file: Optional[str] = None,
                                    use_sampling: bool = True) -> plt.Figure:
        """최적화된 자산 곡선 차트 생성"""
        if account_df.empty:
            self.logger.warning("계좌 데이터가 없어 자산 곡선을 생성할 수 없습니다")
            return None
        
        # 대용량 데이터 샘플링
        if use_sampling and len(account_df) > 10000:
            sample_indices = np.linspace(0, len(account_df)-1, 10000, dtype=int)
            df_sampled = account_df.iloc[sample_indices].copy()
            self.logger.info(f"대용량 데이터 샘플링: {len(account_df)} -> {len(df_sampled)}")
        else:
            df_sampled = account_df.copy()
        
        fig, ax = self._create_optimized_figure()
        
        # 자산 곡선 그리기 (최적화된 방식)
        ax.plot(df_sampled['date'], df_sampled['balance'], 
                linewidth=1.5, color='blue', alpha=0.8, label='Portfolio Value')
        
        # 누적 수익률 추가 (오른쪽 축)
        ax2 = ax.twinx()
        ax2.plot(df_sampled['date'], df_sampled['cumulative_return_pct'], 
                 linewidth=1, color='green', alpha=0.7, label='Cumulative Return %')
        ax2.set_ylabel('Cumulative Return (%)', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        
        # 설정
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value (KRW)')
        ax.grid(self.config.show_grid, alpha=0.3)
        
        # 날짜 포맷 (최적화)
        if len(df_sampled) > 100:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 범례
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            self._save_figure_optimized(fig, save_file)
        
        return fig
    
    def create_drawdown_chart_optimized(self, account_df: pd.DataFrame,
                                      title: str = "Drawdown Analysis",
                                      save_file: Optional[str] = None) -> plt.Figure:
        """최적화된 낙폭 차트 생성"""
        if account_df.empty:
            self.logger.warning("계좌 데이터가 없어 낙폭 차트를 생성할 수 없습니다")
            return None
        
        # 대용량 데이터 샘플링
        if len(account_df) > 10000:
            sample_indices = np.linspace(0, len(account_df)-1, 10000, dtype=int)
            df_sampled = account_df.iloc[sample_indices].copy()
        else:
            df_sampled = account_df.copy()
        
        fig, ax = self._create_optimized_figure()
        
        # 낙폭 차트 (최적화된 방식)
        ax.fill_between(df_sampled['date'], df_sampled['drawdown_pct'], 0,
                       color='red', alpha=0.3, label='Drawdown')
        ax.plot(df_sampled['date'], df_sampled['drawdown_pct'], 
                color='red', linewidth=1, alpha=0.8)
        
        # 설정
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(self.config.show_grid, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 날짜 포맷
        if len(df_sampled) > 100:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        ax.legend()
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            self._save_figure_optimized(fig, save_file)
        
        return fig
    
    def create_trade_distribution_optimized(self, trades_df: pd.DataFrame,
                                         title: str = "Trade Distribution Analysis",
                                         save_file: Optional[str] = None) -> plt.Figure:
        """최적화된 거래 분포 히스토그램 생성"""
        if trades_df.empty:
            self.logger.warning("거래 데이터가 없어 분포 차트를 생성할 수 없습니다")
            return None
        
        # 매도 거래만 분석
        sell_trades = trades_df[trades_df['side'] == 'SELL'].copy()
        if sell_trades.empty:
            self.logger.warning("매도 거래 데이터가 없습니다")
            return None
        
        # 대용량 데이터 샘플링
        if len(sell_trades) > 10000:
            sell_trades = sell_trades.sample(n=10000, random_state=42)
            self.logger.info(f"거래 데이터 샘플링: {len(sell_trades)}건")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 색상 팔레트 캐싱
        colors = self._get_cached_colors(4)
        
        # 1. P&L 분포 (최적화된 히스토그램)
        ax1 = axes[0, 0]
        pnl_data = sell_trades['pnl'].values
        n_bins = min(50, len(pnl_data) // 10)  # 동적 bin 수
        
        counts, bins, patches = ax1.hist(pnl_data, bins=n_bins, alpha=0.7, 
                                        color=colors[0], edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Break-even')
        ax1.set_title('P&L Distribution')
        ax1.set_xlabel('P&L (KRW)')
        ax1.set_ylabel('Frequency')
        ax1.grid(self.config.show_grid, alpha=0.3)
        ax1.legend()
        
        # 2. 보유 기간 분포
        ax2 = axes[0, 1]
        holding_data = sell_trades['holding_period'].values
        n_bins_holding = min(30, len(holding_data) // 10)
        
        ax2.hist(holding_data, bins=n_bins_holding, alpha=0.7, 
                color=colors[1], edgecolor='black')
        ax2.set_title('Holding Period Distribution')
        ax2.set_xlabel('Holding Period (minutes)')
        ax2.set_ylabel('Frequency')
        ax2.grid(self.config.show_grid, alpha=0.3)
        
        # 3. 거래 크기 분포
        ax3 = axes[1, 0]
        trade_sizes = (sell_trades['amount'] * sell_trades['price']).values
        n_bins_size = min(30, len(trade_sizes) // 10)
        
        ax3.hist(trade_sizes, bins=n_bins_size, alpha=0.7, 
                color=colors[2], edgecolor='black')
        ax3.set_title('Trade Size Distribution')
        ax3.set_xlabel('Trade Size (KRW)')
        ax3.set_ylabel('Frequency')
        ax3.grid(self.config.show_grid, alpha=0.3)
        
        # 4. 승/패 비율 (최적화된 막대 차트)
        ax4 = axes[1, 1]
        win_loss = (sell_trades['pnl'] > 0).map({True: 'Win', False: 'Loss'})
        win_loss_counts = win_loss.value_counts()
        
        bars = ax4.bar(win_loss_counts.index, win_loss_counts.values, 
                      color=[colors[3] if x == 'Win' else 'red' for x in win_loss_counts.index], 
                      alpha=0.7)
        ax4.set_title('Win/Loss Ratio')
        ax4.set_ylabel('Number of Trades')
        ax4.grid(self.config.show_grid, alpha=0.3)
        
        # 막대 위에 값 표시 (최적화)
        for bar, value in zip(bars, win_loss_counts.values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value}\n({value/len(sell_trades)*100:.1f}%)',
                    ha='center', va='bottom', fontsize=10)
        
        if self.config.tight_layout:
            plt.tight_layout()
        
        if save_file:
            self._save_figure_optimized(fig, save_file)
        
        return fig
    
    def create_comprehensive_dashboard_optimized(self, trades_df: pd.DataFrame, 
                                               account_df: pd.DataFrame,
                                               title: str = "Trading Dashboard",
                                               save_file: Optional[str] = None) -> plt.Figure:
        """최적화된 종합 대시보드 생성"""
        fig = plt.figure(figsize=(20, 16), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=20, fontweight='bold')
        
        # 3x3 그리드 레이아웃
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 색상 팔레트 캐싱
        colors = self._get_cached_colors(8)
        
        # 1. 자산 곡선 (큰 차트) - 샘플링 적용
        ax1 = fig.add_subplot(gs[0, :2])
        if not account_df.empty:
            if len(account_df) > 5000:
                sample_indices = np.linspace(0, len(account_df)-1, 5000, dtype=int)
                df_sampled = account_df.iloc[sample_indices]
            else:
                df_sampled = account_df
            
            ax1.plot(df_sampled['date'], df_sampled['balance'], 
                    linewidth=2, color=colors[0])
            ax1.set_title('Portfolio Value', fontweight='bold')
            ax1.set_ylabel('Balance (KRW)')
            ax1.grid(True, alpha=0.3)
        
        # 2. 일일 수익률 히스토그램
        ax2 = fig.add_subplot(gs[0, 2])
        if not account_df.empty and 'daily_return_pct' in account_df.columns:
            daily_returns = account_df['daily_return_pct'].dropna()
            if len(daily_returns) > 0:
                n_bins = min(20, len(daily_returns) // 5)
                ax2.hist(daily_returns, bins=n_bins, alpha=0.7, color=colors[1])
                ax2.set_title('Daily Returns', fontweight='bold')
                ax2.set_xlabel('Return (%)')
                ax2.grid(True, alpha=0.3)
        
        # 3. 낙폭 차트 - 샘플링 적용
        ax3 = fig.add_subplot(gs[1, :2])
        if not account_df.empty:
            if len(account_df) > 5000:
                sample_indices = np.linspace(0, len(account_df)-1, 5000, dtype=int)
                df_sampled = account_df.iloc[sample_indices]
            else:
                df_sampled = account_df
            
            ax3.fill_between(df_sampled['date'], df_sampled['drawdown_pct'], 0,
                           color=colors[2], alpha=0.3)
            ax3.plot(df_sampled['date'], df_sampled['drawdown_pct'], 
                    color=colors[2], linewidth=1)
            ax3.set_title('Drawdown', fontweight='bold')
            ax3.set_ylabel('Drawdown (%)')
            ax3.grid(True, alpha=0.3)
        
        # 4. 거래 P&L 분포
        ax4 = fig.add_subplot(gs[1, 2])
        if not trades_df.empty:
            sell_trades = trades_df[trades_df['side'] == 'SELL']
            if not sell_trades.empty:
                # 샘플링 적용
                if len(sell_trades) > 2000:
                    sell_trades = sell_trades.sample(n=2000, random_state=42)
                
                pnl_data = sell_trades['pnl'].values
                n_bins = min(15, len(pnl_data) // 10)
                ax4.hist(pnl_data, bins=n_bins, alpha=0.7, color=colors[3])
                ax4.axvline(x=0, color='red', linestyle='--')
                ax4.set_title('P&L Distribution', fontweight='bold')
                ax4.set_xlabel('P&L (KRW)')
                ax4.grid(True, alpha=0.3)
        
        # 5. 심볼별 거래 수 (최적화된 막대 차트)
        ax5 = fig.add_subplot(gs[2, 0])
        if not trades_df.empty:
            symbol_counts = trades_df['symbol'].value_counts()
            if len(symbol_counts) > 0:
                bars = ax5.bar(symbol_counts.index, symbol_counts.values, 
                              color=colors[4], alpha=0.7)
                ax5.set_title('Trades by Symbol', fontweight='bold')
                ax5.set_ylabel('Number of Trades')
                plt.setp(ax5.get_xticklabels(), rotation=45)
                ax5.grid(True, alpha=0.3)
                
                # 막대 위에 값 표시 (최적화)
                for bar, value in zip(bars, symbol_counts.values):
                    height = bar.get_height()
                    ax5.text(bar.get_x() + bar.get_width()/2., height,
                            str(value), ha='center', va='bottom', fontsize=9)
        
        # 6. 전략별 거래 수
        ax6 = fig.add_subplot(gs[2, 1])
        if not trades_df.empty:
            strategy_counts = trades_df['strategy'].value_counts()
            if len(strategy_counts) > 0:
                bars = ax6.bar(strategy_counts.index, strategy_counts.values, 
                              color=colors[5], alpha=0.7)
                ax6.set_title('Trades by Strategy', fontweight='bold')
                ax6.set_ylabel('Number of Trades')
                plt.setp(ax6.get_xticklabels(), rotation=45)
                ax6.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, strategy_counts.values):
                    height = bar.get_height()
                    ax6.text(bar.get_x() + bar.get_width()/2., height,
                            str(value), ha='center', va='bottom', fontsize=9)
        
        # 7. 시간대별 거래 (최적화)
        ax7 = fig.add_subplot(gs[2, 2])
        if not trades_df.empty:
            trades_df['hour'] = trades_df['created_at'].dt.hour
            hourly_counts = trades_df['hour'].value_counts().sort_index()
            if len(hourly_counts) > 0:
                ax7.bar(hourly_counts.index, hourly_counts.values, 
                       color=colors[6], alpha=0.7)
                ax7.set_title('Trades by Hour', fontweight='bold')
                ax7.set_xlabel('Hour')
                ax7.set_ylabel('Number of Trades')
                ax7.grid(True, alpha=0.3)
        
        if save_file:
            self._save_figure_optimized(fig, save_file)
        
        return fig
    
    def create_batch_charts(self, chart_configs: List[Dict[str, Any]]) -> List[str]:
        """배치 차트 생성 (병렬 처리)"""
        saved_files = []
        
        def create_single_chart(config: Dict[str, Any]) -> str:
            try:
                chart_type = config['type']
                data = config['data']
                filename = config.get('filename', f'chart_{chart_type}')
                
                if chart_type == 'equity_curve':
                    fig = self.create_equity_curve_optimized(data, save_file=filename)
                elif chart_type == 'drawdown':
                    fig = self.create_drawdown_chart_optimized(data, save_file=filename)
                elif chart_type == 'trade_distribution':
                    fig = self.create_trade_distribution_optimized(data, save_file=filename)
                elif chart_type == 'dashboard':
                    fig = self.create_comprehensive_dashboard_optimized(
                        data['trades'], data['account'], save_file=filename
                    )
                else:
                    return ""
                
                return filename if fig else ""
                
            except Exception as e:
                self.logger.error(f"배치 차트 생성 오류: {e}")
                return ""
        
        # 병렬 처리로 차트 생성
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(create_single_chart, config) for config in chart_configs]
                
                for future in futures:
                    try:
                        result = future.result(timeout=60)
                        if result:
                            saved_files.append(result)
                    except Exception as e:
                        self.logger.error(f"배치 차트 결과 처리 오류: {e}")
                        
        except Exception as e:
            self.logger.error(f"배치 차트 생성 오류: {e}")
        
        return saved_files
    
    def cleanup_resources(self) -> None:
        """리소스 정리"""
        self.chart_manager.close_all_figures()
        gc.collect()
        self.logger.info("시각화 리소스 정리 완료")
    
    def get_memory_stats(self) -> Dict[str, float]:
        """메모리 통계 반환"""
        return {
            'current_memory_mb': self.chart_manager.get_memory_usage_mb(),
            'memory_limit_mb': self.config.memory_limit_mb,
            'active_figures': len(self.chart_manager.active_figures),
            'max_figures': self.config.max_figures
        }

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
        
        # 최적화된 시각화 생성
        start_time = time.time()
        
        chart_config = ChartConfig(
            save_path="optimized_charts/",
            memory_limit_mb=300,
            max_figures=5,
            enable_caching=True
        )
        
        visualizer = OptimizedTradingVisualizer(chart_config)
        
        # 개별 차트 생성
        visualizer.create_equity_curve_optimized(processed_account, save_file="equity_curve")
        visualizer.create_drawdown_chart_optimized(processed_account, save_file="drawdown")
        visualizer.create_trade_distribution_optimized(processed_trades, save_file="trade_distribution")
        
        # 종합 대시보드 생성
        visualizer.create_comprehensive_dashboard_optimized(
            processed_trades, processed_account, save_file="dashboard"
        )
        
        visualization_time = time.time() - start_time
        
        # 메모리 통계 출력
        memory_stats = visualizer.get_memory_stats()
        
        print("=== 최적화된 시각화 결과 ===")
        print(f"시각화 시간: {visualization_time:.3f}초")
        print(f"거래 데이터: {len(processed_trades):,}건")
        print(f"계좌 데이터: {len(processed_account):,}건")
        print(f"현재 메모리 사용량: {memory_stats['current_memory_mb']:.1f}MB")
        print(f"활성 figure 수: {memory_stats['active_figures']}")
        
        # 리소스 정리
        visualizer.cleanup_resources()
        print("최적화된 시각화 완료!")
    else:
        print("시각화할 데이터가 없습니다.")



