#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 백테스트 클래스 - 최적화 버전
pandas를 활용한 효율적인 백테스트 시스템

주요 기능:
- 데이터 로딩 및 전처리
- 변동성 돌파 전략 실행
- 성과 분석 및 리스크 관리
- 결과 시각화
- 매개변수 최적화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정 (차트에서 한글 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class VolatilityBreakoutBacktest:
    """
    변동성 돌파 전략 백테스트 클래스
    
    변동성 돌파 전략:
    - 전일 고가와 저가의 차이에 K값을 곱한 돌파선을 계산
    - 현재가가 돌파선을 상향 돌파하면 매수
    - 거래량 필터와 RSI 필터를 추가하여 신호 품질 향상
    - 손절/익절과 최대 보유 기간으로 리스크 관리
    """
    
    def __init__(self, 
                 k_value: float = 0.7,
                 stop_loss: float = -0.015,
                 take_profit: float = 0.025,
                 position_size: float = 0.05,
                 volume_filter: float = 1.5,
                 rsi_threshold: float = 30,
                 rsi_period: int = 14,
                 volume_period: int = 20,
                 max_holding_days: int = 2,
                 transaction_cost: float = 0.001):
        """
        백테스트 초기화
        
        Args:
            k_value: 돌파선 계산을 위한 K값 (기본값: 0.7)
            stop_loss: 손절 비율 (기본값: -1.5%)
            take_profit: 익절 비율 (기본값: +2.5%)
            position_size: 포지션 크기 (자본 대비 비율, 기본값: 5%)
            volume_filter: 거래량 필터 (평균 대비 배수, 기본값: 1.5)
            rsi_threshold: RSI 임계값 (기본값: 30)
            rsi_period: RSI 계산 기간 (기본값: 14)
            volume_period: 거래량 평균 계산 기간 (기본값: 20)
            max_holding_days: 최대 보유 기간 (일, 기본값: 2)
            transaction_cost: 거래 비용 (기본값: 0.1%)
        """
        # 전략 매개변수
        self.k_value = k_value
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.volume_filter = volume_filter
        self.rsi_threshold = rsi_threshold
        self.rsi_period = rsi_period
        self.volume_period = volume_period
        self.max_holding_days = max_holding_days
        self.transaction_cost = transaction_cost
        
        # 데이터 및 결과 저장
        self.data = None
        self.trades = []
        self.performance = {}
        self.equity_curve = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, data: Union[pd.DataFrame, str]) -> None:
        """
        데이터 로딩 및 전처리
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame 또는 CSV 파일 경로
                필수 컬럼: ['open', 'high', 'low', 'close', 'volume']
                인덱스: DatetimeIndex
        """
        try:
            # CSV 파일인 경우 로딩
            if isinstance(data, str):
                self.data = pd.read_csv(data, index_col=0, parse_dates=True)
            else:
                self.data = data.copy()
            
            # 필수 컬럼 확인
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in self.data.columns for col in required_columns):
                raise ValueError(f"필수 컬럼이 누락되었습니다: {required_columns}")
            
            # 데이터 정렬 및 정제
            self.data = self.data[required_columns].copy()
            self.data = self.data.sort_index()
            
            # 데이터 검증
            self._validate_data()
            
            # 기술적 지표 계산 (pandas 벡터화 연산 활용)
            self._calculate_indicators()
            
            self.logger.info(f"데이터 로딩 완료: {len(self.data)}개 레코드")
            self.logger.info(f"기간: {self.data.index[0].strftime('%Y-%m-%d')} ~ {self.data.index[-1].strftime('%Y-%m-%d')}")
            
        except Exception as e:
            self.logger.error(f"데이터 로딩 오류: {e}")
            raise
    
    def _validate_data(self) -> None:
        """데이터 유효성 검사"""
        # 결측값 확인 및 처리
        missing_data = self.data.isnull().sum()
        if missing_data.any():
            self.logger.warning(f"결측값 발견: {missing_data[missing_data > 0].to_dict()}")
            self.data = self.data.fillna(method='ffill')
        
        # 가격 데이터 유효성 확인
        if (self.data[['open', 'high', 'low', 'close']] <= 0).any().any():
            raise ValueError("가격 데이터에 0 이하의 값이 있습니다")
        
        # OHLC 논리적 일관성 확인
        invalid_ohlc = (
            (self.data['high'] < self.data['low']) |
            (self.data['high'] < self.data['open']) |
            (self.data['high'] < self.data['close']) |
            (self.data['low'] > self.data['open']) |
            (self.data['low'] > self.data['close'])
        )
        
        if invalid_ohlc.any():
            self.logger.warning(f"OHLC 논리적 일관성 위반: {invalid_ohlc.sum()}개 레코드")
            # 잘못된 데이터 수정
            self.data.loc[invalid_ohlc, 'high'] = np.maximum(
                self.data.loc[invalid_ohlc, ['open', 'close']].max(axis=1),
                self.data.loc[invalid_ohlc, 'high']
            )
            self.data.loc[invalid_ohlc, 'low'] = np.minimum(
                self.data.loc[invalid_ohlc, ['open', 'close']].min(axis=1),
                self.data.loc[invalid_ohlc, 'low']
            )
    
    def _calculate_indicators(self) -> None:
        """기술적 지표 계산 (pandas 벡터화 연산 활용)"""
        # 돌파선 계산 (전일 고가 + (전일 고가 - 전일 저가) * K)
        self.data['prev_high'] = self.data['high'].shift(1)
        self.data['prev_low'] = self.data['low'].shift(1)
        self.data['breakout_line'] = (
            self.data['prev_high'] + 
            (self.data['prev_high'] - self.data['prev_low']) * self.k_value
        )
        
        # 거래량 평균 계산
        self.data['volume_ma'] = self.data['volume'].rolling(window=self.volume_period).mean()
        
        # RSI 계산
        self.data['rsi'] = self._calculate_rsi(self.data['close'], self.rsi_period)
        
        # 수익률 계산
        self.data['returns'] = self.data['close'].pct_change()
        
        # 변동성 계산 (20일 롤링 표준편차)
        self.data['volatility'] = self.data['returns'].rolling(window=20).std() * np.sqrt(252)
        
        self.logger.info("기술적 지표 계산 완료")
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) 계산
        
        Args:
            prices: 가격 시리즈
            period: RSI 계산 기간
            
        Returns:
            pd.Series: RSI 값
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 0으로 나누는 경우 방지
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def run_backtest(self) -> Dict:
        """
        백테스트 실행
        
        Returns:
            Dict: 백테스트 결과 (거래 내역, 성과 지표, 자본 곡선)
        """
        if self.data is None:
            raise ValueError("데이터가 로딩되지 않았습니다. load_data()를 먼저 호출하세요")
        
        self.logger.info("백테스트 시작")
        
        # 거래 내역 및 자본 곡선 초기화
        self.trades = []
        self.equity_curve = []
        position = None
        current_equity = 1.0  # 초기 자본 100%
        
        # 백테스트 실행
        for i, (date, row) in enumerate(self.data.iterrows()):
            if i < max(self.rsi_period, self.volume_period):  # 충분한 데이터 필요
                self.equity_curve.append({'date': date, 'equity': current_equity})
                continue
            
            current_price = row['close']
            
            # 포지션이 없는 경우 - 매수 신호 확인
            if position is None:
                if self._should_buy(row, i):
                    position = self._enter_position(date, current_price, row)
                    self.logger.info(f"매수: {date.strftime('%Y-%m-%d')} - 가격: {current_price:,.0f}")
            
            # 포지션이 있는 경우 - 매도 신호 확인
            else:
                if self._should_sell(position, row, date):
                    trade_return = self._exit_position(position, date, current_price, row)
                    current_equity *= (1 + trade_return)
                    self.logger.info(f"매도: {date.strftime('%Y-%m-%d')} - 가격: {current_price:,.0f} - 수익률: {trade_return:.2%}")
                    position = None
            
            # 자본 곡선 업데이트
            self.equity_curve.append({'date': date, 'equity': current_equity})
        
        # 마지막 포지션 정리
        if position is not None:
            last_date = self.data.index[-1]
            last_price = self.data['close'].iloc[-1]
            trade_return = self._exit_position(position, last_date, last_price, self.data.iloc[-1])
            current_equity *= (1 + trade_return)
            self.equity_curve.append({'date': last_date, 'equity': current_equity})
        
        # 자본 곡선을 DataFrame으로 변환
        self.equity_curve = pd.DataFrame(self.equity_curve).set_index('date')
        
        # 성과 분석
        self.performance = self._analyze_performance()
        
        self.logger.info(f"백테스트 완료: {len(self.trades)}개 거래")
        return {
            'trades': self.trades,
            'performance': self.performance,
            'equity_curve': self.equity_curve
        }
    
    def _should_buy(self, row: pd.Series, index: int) -> bool:
        """
        매수 신호 확인
        
        Args:
            row: 현재 행 데이터
            index: 현재 인덱스
            
        Returns:
            bool: 매수 신호 여부
        """
        # NaN 값 체크
        if (pd.isna(row['breakout_line']) or pd.isna(row['volume_ma']) or 
            pd.isna(row['rsi']) or pd.isna(row['close']) or pd.isna(row['volume'])):
            return False
        
        # 기본 조건: 현재가가 돌파선을 상향 돌파
        breakout_condition = row['close'] > row['breakout_line']
        
        # 거래량 필터: 현재 거래량이 평균의 volume_filter배 이상
        volume_condition = row['volume'] >= row['volume_ma'] * self.volume_filter
        
        # RSI 필터: RSI가 임계값 이하 (과매도 상태)
        rsi_condition = row['rsi'] <= self.rsi_threshold
        
        return breakout_condition and volume_condition and rsi_condition
    
    def _should_sell(self, position: Dict, row: pd.Series, current_date: datetime) -> bool:
        """
        매도 신호 확인
        
        Args:
            position: 현재 포지션 정보
            row: 현재 행 데이터
            current_date: 현재 날짜
            
        Returns:
            bool: 매도 신호 여부
        """
        entry_price = position['entry_price']
        current_price = row['close']
        entry_date = position['entry_date']
        
        # 수익률 계산
        returns = (current_price - entry_price) / entry_price
        
        # 손절 조건
        stop_loss_condition = returns <= self.stop_loss
        
        # 익절 조건
        take_profit_condition = returns >= self.take_profit
        
        # 시간 기반 청산
        holding_days = (current_date - entry_date).days
        time_condition = holding_days >= self.max_holding_days
        
        return stop_loss_condition or take_profit_condition or time_condition
    
    def _enter_position(self, date: datetime, price: float, row: pd.Series) -> Dict:
        """
        포지션 진입
        
        Args:
            date: 진입 날짜
            price: 진입 가격
            row: 현재 행 데이터
            
        Returns:
            Dict: 포지션 정보
        """
        position = {
            'entry_date': date,
            'entry_price': price,
            'position_size': self.position_size,
            'breakout_line': row['breakout_line'],
            'volume': row['volume'],
            'volume_ma': row['volume_ma'],
            'rsi': row['rsi'],
            'volatility': row['volatility']
        }
        return position
    
    def _exit_position(self, position: Dict, exit_date: datetime, exit_price: float, row: pd.Series) -> float:
        """
        포지션 청산
        
        Args:
            position: 포지션 정보
            exit_date: 청산 날짜
            exit_price: 청산 가격
            row: 현재 행 데이터
            
        Returns:
            float: 거래 수익률
        """
        entry_price = position['entry_price']
        returns = (exit_price - entry_price) / entry_price
        
        # 거래 비용 고려
        net_returns = returns - self.transaction_cost
        
        trade = {
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'returns': returns,
            'net_returns': net_returns,
            'holding_days': (exit_date - position['entry_date']).days,
            'position_size': position['position_size'],
            'breakout_line': position['breakout_line'],
            'volume': position['volume'],
            'volume_ma': position['volume_ma'],
            'rsi': position['rsi'],
            'volatility': position['volatility']
        }
        
        self.trades.append(trade)
        return net_returns
    
    def _analyze_performance(self) -> Dict:
        """성과 분석"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_returns': 0,
                'total_return_pct': 0,
                'avg_returns': 0,
                'returns_std': 0,
                'volatility_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_loss_ratio': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'avg_holding_days': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        # 기본 통계
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['net_returns'] > 0])
        losing_trades = len(trades_df[trades_df['net_returns'] < 0])
        
        # 수익률 통계
        total_returns = trades_df['net_returns'].sum()
        avg_returns = trades_df['net_returns'].mean()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 리스크 지표
        returns_std = trades_df['net_returns'].std()
        max_drawdown = self._calculate_max_drawdown(trades_df['net_returns'])
        
        # 샤프 비율 (연간화)
        sharpe_ratio = (avg_returns / returns_std * np.sqrt(252)) if returns_std > 0 else 0
        
        # 승패별 평균 수익률
        avg_win = trades_df[trades_df['net_returns'] > 0]['net_returns'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['net_returns'] < 0]['net_returns'].mean() if losing_trades > 0 else 0
        
        # 수익/손실 비율
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 최대 연속 승리/패배
        max_consecutive_wins = self._calculate_max_consecutive(trades_df['net_returns'] > 0)
        max_consecutive_losses = self._calculate_max_consecutive(trades_df['net_returns'] < 0)
        
        # 평균 보유 기간
        avg_holding_days = trades_df['holding_days'].mean()
        
        # 자본 곡선 기반 지표
        if self.equity_curve is not None and len(self.equity_curve) > 1:
            equity_returns = self.equity_curve['equity'].pct_change().dropna()
            total_return = (self.equity_curve['equity'].iloc[-1] - 1) * 100
            volatility = equity_returns.std() * np.sqrt(252) * 100
        else:
            total_return = total_returns * 100
            volatility = returns_std * 100
        
        performance = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_returns': total_returns,
            'total_return_pct': total_return,
            'avg_returns': avg_returns,
            'returns_std': returns_std,
            'volatility_pct': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_holding_days': avg_holding_days
        }
        
        return performance
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _calculate_max_consecutive(self, condition: pd.Series) -> int:
        """최대 연속 횟수 계산"""
        if not condition.any():
            return 0
        
        groups = (condition != condition.shift()).cumsum()
        consecutive_counts = condition.groupby(groups).sum()
        return consecutive_counts.max()
    
    def plot_results(self, save_path: Optional[str] = None, figsize: Tuple[int, int] = (15, 12)) -> None:
        """
        결과 시각화
        
        Args:
            save_path: 저장할 파일 경로
            figsize: 차트 크기
        """
        if self.data is None:
            self.logger.warning("데이터가 로딩되지 않았습니다. load_data()를 먼저 호출하세요")
            return
        
        if not self.trades:
            self.logger.warning(f"거래가 발생하지 않았습니다. 현재 설정: K={self.k_value}, 손절={self.stop_loss}, 익절={self.take_profit}")
            self.logger.info("매개변수를 조정하거나 데이터 기간을 확인해보세요")
            # 거래가 없어도 가격 차트는 표시
            self._plot_price_chart_only(save_path, figsize)
            return
        
        fig, axes = plt.subplots(4, 1, figsize=figsize)
        
        # 1. 가격 차트 및 거래 신호
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['close'], label='종가', linewidth=1, color='black')
        ax1.plot(self.data.index, self.data['breakout_line'], label='돌파선', alpha=0.7, linestyle='--', color='red')
        
        # 거래 신호 표시
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            buy_signals = trades_df['entry_date']
            sell_signals = trades_df['exit_date']
            buy_prices = trades_df['entry_price']
            sell_prices = trades_df['exit_price']
            
            ax1.scatter(buy_signals, buy_prices, color='green', marker='^', s=100, label='매수', zorder=5)
            ax1.scatter(sell_signals, sell_prices, color='red', marker='v', s=100, label='매도', zorder=5)
        
        ax1.set_title('변동성 돌파 전략 - 가격 차트 및 거래 신호', fontsize=14, fontweight='bold')
        ax1.set_ylabel('가격 (원)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 자본 곡선
        ax2 = axes[1]
        if self.equity_curve is not None and len(self.equity_curve) > 1:
            ax2.plot(self.equity_curve.index, self.equity_curve['equity'], linewidth=2, color='blue')
            ax2.axhline(y=1, color='black', linestyle='--', alpha=0.5)
            ax2.set_title('자본 곡선', fontsize=14, fontweight='bold')
            ax2.set_ylabel('누적 수익률')
            ax2.grid(True, alpha=0.3)
        
        # 3. 거래별 수익률
        ax3 = axes[2]
        if not trades_df.empty:
            colors = ['green' if x > 0 else 'red' for x in trades_df['net_returns']]
            bars = ax3.bar(range(len(trades_df)), trades_df['net_returns'] * 100, color=colors, alpha=0.7)
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.set_title('거래별 수익률', fontsize=14, fontweight='bold')
            ax3.set_ylabel('수익률 (%)')
            ax3.set_xlabel('거래 번호')
            ax3.grid(True, alpha=0.3)
            
            # 수익률 값 표시 (10개 이상인 경우 일부만 표시)
            if len(trades_df) <= 20:
                for i, (bar, ret) in enumerate(zip(bars, trades_df['net_returns'])):
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.3),
                            f'{ret*100:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
        
        # 4. RSI 및 거래량
        ax4 = axes[3]
        ax4_twin = ax4.twinx()
        
        # RSI
        ax4.plot(self.data.index, self.data['rsi'], label='RSI', color='purple', alpha=0.7)
        ax4.axhline(y=self.rsi_threshold, color='red', linestyle='--', alpha=0.5, label=f'RSI 임계값 ({self.rsi_threshold})')
        ax4.set_ylabel('RSI')
        ax4.set_ylim(0, 100)
        
        # 거래량
        ax4_twin.bar(self.data.index, self.data['volume'], alpha=0.3, color='gray', label='거래량')
        ax4_twin.set_ylabel('거래량')
        
        ax4.set_title('RSI 및 거래량', fontsize=14, fontweight='bold')
        ax4.set_xlabel('날짜')
        ax4.grid(True, alpha=0.3)
        
        # 범례 통합
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4_twin.get_legend_handles_labels()
        ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"차트 저장 완료: {save_path}")
        
        plt.show()
    
    def _plot_price_chart_only(self, save_path: Optional[str] = None, figsize: Tuple[int, int] = (15, 8)) -> None:
        """
        거래가 없을 때 가격 차트만 표시
        
        Args:
            save_path: 저장할 파일 경로
            figsize: 차트 크기
        """
        fig, axes = plt.subplots(2, 1, figsize=figsize)
        
        # 1. 가격 차트
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['close'], label='종가', linewidth=1, color='black')
        
        if 'breakout_line' in self.data.columns:
            ax1.plot(self.data.index, self.data['breakout_line'], label='돌파선', alpha=0.7, linestyle='--', color='red')
        
        ax1.set_title('변동성 돌파 전략 - 가격 차트 (거래 없음)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('가격 (원)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. RSI 및 거래량
        ax2 = axes[1]
        ax2_twin = ax2.twinx()
        
        # RSI
        if 'rsi' in self.data.columns:
            ax2.plot(self.data.index, self.data['rsi'], label='RSI', color='purple', alpha=0.7)
            ax2.axhline(y=self.rsi_threshold, color='red', linestyle='--', alpha=0.5, label=f'RSI 임계값 ({self.rsi_threshold})')
            ax2.set_ylabel('RSI')
            ax2.set_ylim(0, 100)
        
        # 거래량
        ax2_twin.bar(self.data.index, self.data['volume'], alpha=0.3, color='gray', label='거래량')
        ax2_twin.set_ylabel('거래량')
        
        ax2.set_title('RSI 및 거래량', fontsize=14, fontweight='bold')
        ax2.set_xlabel('날짜')
        ax2.grid(True, alpha=0.3)
        
        # 범례 통합
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"가격 차트 저장 완료: {save_path}")
        
        plt.show()
    
    def print_performance(self) -> None:
        """성과 지표 출력"""
        if not self.performance:
            self.logger.warning("성과 분석 결과가 없습니다")
            return
        
        print("\n" + "="*60)
        print("변동성 돌파 전략 백테스트 결과")
        print("="*60)
        
        print(f"📊 거래 통계:")
        print(f"  총 거래 횟수: {self.performance['total_trades']}회")
        print(f"  승리 거래: {self.performance['winning_trades']}회")
        print(f"  패배 거래: {self.performance['losing_trades']}회")
        print(f"  승률: {self.performance['win_rate']:.1%}")
        print(f"  평균 보유 기간: {self.performance['avg_holding_days']:.1f}일")
        
        print(f"\n💰 수익성 지표:")
        print(f"  총 수익률: {self.performance['total_return_pct']:.2f}%")
        print(f"  평균 수익률: {self.performance['avg_returns']:.2%}")
        print(f"  평균 승리: {self.performance['avg_win']:.2%}")
        print(f"  평균 손실: {self.performance['avg_loss']:.2%}")
        print(f"  수익/손실 비율: {self.performance['profit_loss_ratio']:.2f}")
        
        print(f"\n⚠️ 리스크 지표:")
        print(f"  변동성: {self.performance['volatility_pct']:.2f}%")
        print(f"  샤프 비율: {self.performance['sharpe_ratio']:.2f}")
        print(f"  최대 낙폭: {self.performance['max_drawdown_pct']:.2f}%")
        print(f"  최대 연속 승리: {self.performance['max_consecutive_wins']}회")
        print(f"  최대 연속 패배: {self.performance['max_consecutive_losses']}회")
        
        print("\n" + "="*60)
    
    def get_trade_summary(self) -> pd.DataFrame:
        """거래 내역 요약 반환"""
        if not self.trades:
            return pd.DataFrame()
        
        trades_df = pd.DataFrame(self.trades)
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        
        return trades_df[['entry_date', 'exit_date', 'entry_price', 'exit_price', 
                         'net_returns', 'holding_days', 'rsi', 'volatility']].round(4)
    
    def optimize_parameters(self, 
                          k_values: List[float] = [0.5, 0.6, 0.7, 0.8, 0.9],
                          stop_losses: List[float] = [-0.01, -0.015, -0.02, -0.025],
                          take_profits: List[float] = [0.02, 0.025, 0.03, 0.035]) -> Dict:
        """
        매개변수 최적화
        
        Args:
            k_values: 테스트할 K값 리스트
            stop_losses: 테스트할 손절 비율 리스트
            take_profits: 테스트할 익절 비율 리스트
            
        Returns:
            Dict: 최적 매개변수와 성과
        """
        self.logger.info("매개변수 최적화 시작")
        
        best_performance = None
        best_params = None
        results = []
        
        for k in k_values:
            for stop_loss in stop_losses:
                for take_profit in take_profits:
                    # 백테스트 실행
                    temp_backtest = VolatilityBreakoutBacktest(
                        k_value=k,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        position_size=self.position_size,
                        volume_filter=self.volume_filter,
                        rsi_threshold=self.rsi_threshold,
                        rsi_period=self.rsi_period,
                        volume_period=self.volume_period,
                        max_holding_days=self.max_holding_days,
                        transaction_cost=self.transaction_cost
                    )
                    
                    temp_backtest.data = self.data.copy()
                    temp_backtest._calculate_indicators()
                    
                    try:
                        temp_backtest.run_backtest()
                        performance = temp_backtest.performance
                        
                        results.append({
                            'k_value': k,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'total_return': performance['total_return_pct'],
                            'sharpe_ratio': performance['sharpe_ratio'],
                            'max_drawdown': performance['max_drawdown_pct'],
                            'win_rate': performance['win_rate'],
                            'total_trades': performance['total_trades']
                        })
                        
                        # 최적 성과 업데이트 (샤프 비율 기준)
                        if best_performance is None or performance['sharpe_ratio'] > best_performance['sharpe_ratio']:
                            best_performance = performance
                            best_params = {
                                'k_value': k,
                                'stop_loss': stop_loss,
                                'take_profit': take_profit
                            }
                    
                    except Exception as e:
                        self.logger.warning(f"매개변수 조합 실패: k={k}, stop_loss={stop_loss}, take_profit={take_profit}, 오류: {e}")
                        continue
        
        self.logger.info("매개변수 최적화 완료")
        
        return {
            'best_params': best_params,
            'best_performance': best_performance,
            'all_results': pd.DataFrame(results)
        }
    
    def diagnose_no_trades(self) -> None:
        """거래가 발생하지 않는 이유 진단"""
        if self.data is None:
            print("❌ 데이터가 로딩되지 않았습니다")
            return
        
        print("\n" + "="*60)
        print("거래 발생 안함 진단 리포트")
        print("="*60)
        
        # 기본 정보
        print(f"📊 데이터 정보:")
        print(f"  데이터 기간: {self.data.index[0].strftime('%Y-%m-%d')} ~ {self.data.index[-1].strftime('%Y-%m-%d')}")
        print(f"  총 레코드 수: {len(self.data)}개")
        print(f"  전략 설정: K={self.k_value}, 손절={self.stop_loss}, 익절={self.take_profit}")
        
        # 매수 조건 분석
        print(f"\n🔍 매수 조건 분석:")
        
        # 돌파 조건 확인
        breakout_condition = self.data['close'] > self.data['breakout_line']
        breakout_count = breakout_condition.sum()
        print(f"  돌파 조건 (가격 > 돌파선): {breakout_count}회")
        
        # 거래량 필터 확인
        volume_condition = self.data['volume'] >= self.data['volume_ma'] * self.volume_filter
        volume_count = volume_condition.sum()
        print(f"  거래량 필터 (거래량 ≥ 평균×{self.volume_filter}): {volume_count}회")
        
        # RSI 필터 확인
        rsi_condition = self.data['rsi'] <= self.rsi_threshold
        rsi_count = rsi_condition.sum()
        print(f"  RSI 필터 (RSI ≤ {self.rsi_threshold}): {rsi_count}회")
        
        # 모든 조건 동시 만족
        all_conditions = breakout_condition & volume_condition & rsi_condition
        all_conditions_count = all_conditions.sum()
        print(f"  모든 조건 동시 만족: {all_conditions_count}회")
        
        if all_conditions_count == 0:
            print(f"\n⚠️ 거래가 발생하지 않는 이유:")
            
            # 각 조건별로 몇 번씩 만족했는지 확인
            conditions_df = pd.DataFrame({
                '돌파조건': breakout_condition,
                '거래량필터': volume_condition,
                'RSI필터': rsi_condition
            })
            
            # 조건별 통계
            print(f"  돌파 조건만 만족: {(conditions_df['돌파조건'] & ~conditions_df['거래량필터'] & ~conditions_df['RSI필터']).sum()}회")
            print(f"  거래량 필터만 만족: {(~conditions_df['돌파조건'] & conditions_df['거래량필터'] & ~conditions_df['RSI필터']).sum()}회")
            print(f"  RSI 필터만 만족: {(~conditions_df['돌파조건'] & ~conditions_df['거래량필터'] & conditions_df['RSI필터']).sum()}회")
            print(f"  돌파+거래량 만족: {(conditions_df['돌파조건'] & conditions_df['거래량필터'] & ~conditions_df['RSI필터']).sum()}회")
            print(f"  돌파+RSI 만족: {(conditions_df['돌파조건'] & ~conditions_df['거래량필터'] & conditions_df['RSI필터']).sum()}회")
            print(f"  거래량+RSI 만족: {(~conditions_df['돌파조건'] & conditions_df['거래량필터'] & conditions_df['RSI필터']).sum()}회")
            
            # 권장사항
            print(f"\n💡 개선 권장사항:")
            if breakout_count == 0:
                print(f"  - K값을 낮춰보세요 (현재: {self.k_value} → 0.5 이하)")
            if volume_count == 0:
                print(f"  - 거래량 필터를 낮춰보세요 (현재: {self.volume_filter} → 1.0 이하)")
            if rsi_count == 0:
                print(f"  - RSI 임계값을 높여보세요 (현재: {self.rsi_threshold} → 50 이상)")
        
        # 데이터 품질 확인
        print(f"\n📈 데이터 품질 확인:")
        missing_data = self.data[['breakout_line', 'volume_ma', 'rsi']].isnull().sum()
        if missing_data.any():
            print(f"  결측값: {missing_data[missing_data > 0].to_dict()}")
        else:
            print(f"  결측값: 없음")
        
        # 가격 범위 확인
        price_range = self.data['close'].max() / self.data['close'].min()
        print(f"  가격 변동폭: {price_range:.2f}배")
        
        # 변동성 확인
        if 'volatility' in self.data.columns:
            avg_volatility = self.data['volatility'].mean()
            print(f"  평균 변동성: {avg_volatility:.2%}")
        
        print("\n" + "="*60)


def create_sample_data(start_date: str = '2023-01-01', 
                      end_date: str = '2023-12-31',
                      base_price: float = 50000000,
                      volatility: float = 0.02) -> pd.DataFrame:
    """
    샘플 데이터 생성 (테스트용)
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        base_price: 기준 가격
        volatility: 일일 변동성
        
    Returns:
        pd.DataFrame: OHLCV 데이터
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(42)
    
    # 기본 가격 설정
    prices = [base_price]
    
    # 랜덤 워크로 가격 생성 (더 현실적인 패턴)
    for i in range(len(dates) - 1):
        # 트렌드와 노이즈를 결합
        trend = 0.0001 * np.sin(i / 50)  # 장기 트렌드
        noise = np.random.normal(0, volatility)
        daily_return = trend + noise
        
        new_price = prices[-1] * (1 + daily_return)
        prices.append(max(new_price, base_price * 0.1))  # 최소 가격 제한
    
    # OHLCV 데이터 생성
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 더 현실적인 OHLC 생성
        daily_vol = abs(np.random.normal(0, 0.01))
        high = close * (1 + daily_vol)
        low = close * (1 - daily_vol)
        open_price = prices[i-1] if i > 0 else close
        
        # OHLC 논리적 일관성 보장
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # 거래량은 가격 변동성과 연관
        volume_base = 5000000
        volume_multiplier = 1 + abs(daily_vol) * 10
        volume = int(volume_base * volume_multiplier * np.random.uniform(0.5, 2.0))
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


if __name__ == "__main__":
    # 샘플 데이터 생성
    print("샘플 데이터 생성 중...")
    sample_data = create_sample_data()
    
    # 백테스트 실행
    print("백테스트 실행 중...")
    backtest = VolatilityBreakoutBacktest(
        k_value=0.7,
        stop_loss=-0.015,
        take_profit=0.025,
        position_size=0.05,
        volume_filter=1.5,
        rsi_threshold=30
    )
    
    # 데이터 로딩
    backtest.load_data(sample_data)
    
    # 백테스트 실행
    results = backtest.run_backtest()
    
    # 결과 출력
    backtest.print_performance()
    
    # 차트 생성
    backtest.plot_results('volatility_breakout_backtest_optimized_results.png')
    
    # 거래 내역 확인
    print("\n거래 내역:")
    print(backtest.get_trade_summary().head(10))
