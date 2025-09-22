#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 백테스트 클래스
pandas를 활용한 효율적인 백테스트 시스템
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class VolatilityBreakoutBacktest:
    """
    변동성 돌파 전략 백테스트 클래스
    
    주요 기능:
    - 데이터 로딩 및 전처리
    - 변동성 돌파 전략 실행
    - 성과 분석 및 리스크 관리
    - 결과 시각화
    """
    
    def __init__(self, 
                 k_value: float = 0.7,
                 stop_loss: float = -0.015,
                 take_profit: float = 0.025,
                 position_size: float = 0.05,
                 volume_filter: float = 1.5,
                 rsi_threshold: float = 30,
                 max_holding_days: int = 2):
        """
        백테스트 초기화
        
        Args:
            k_value: 돌파선 계산을 위한 K값 (기본값: 0.7)
            stop_loss: 손절 비율 (기본값: -1.5%)
            take_profit: 익절 비율 (기본값: +2.5%)
            position_size: 포지션 크기 (자본 대비 비율, 기본값: 5%)
            volume_filter: 거래량 필터 (평균 대비 배수, 기본값: 1.5)
            rsi_threshold: RSI 임계값 (기본값: 30)
            max_holding_days: 최대 보유 기간 (일, 기본값: 2)
        """
        self.k_value = k_value
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.volume_filter = volume_filter
        self.rsi_threshold = rsi_threshold
        self.max_holding_days = max_holding_days
        
        # 데이터 저장
        self.data = None
        self.trades = []
        self.performance = {}
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, data: pd.DataFrame) -> None:
        """
        데이터 로딩 및 전처리
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
                컬럼: ['open', 'high', 'low', 'close', 'volume']
                인덱스: DatetimeIndex
        """
        try:
            # 필수 컬럼 확인
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"필수 컬럼이 누락되었습니다: {required_columns}")
            
            # 데이터 복사 및 정렬
            self.data = data[required_columns].copy()
            self.data = self.data.sort_index()
            
            # 데이터 검증
            self._validate_data()
            
            # 기술적 지표 계산
            self._calculate_indicators()
            
            self.logger.info(f"데이터 로딩 완료: {len(self.data)}개 레코드")
            
        except Exception as e:
            self.logger.error(f"데이터 로딩 오류: {e}")
            raise
    
    def _validate_data(self) -> None:
        """데이터 유효성 검사"""
        # 결측값 확인
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
    
    def _calculate_indicators(self) -> None:
        """기술적 지표 계산"""
        # 돌파선 계산
        self.data['prev_high'] = self.data['high'].shift(1)
        self.data['prev_low'] = self.data['low'].shift(1)
        self.data['breakout_line'] = (
            self.data['prev_high'] + 
            (self.data['prev_high'] - self.data['prev_low']) * self.k_value
        )
        
        # 거래량 평균 계산 (20일)
        self.data['volume_ma'] = self.data['volume'].rolling(window=20).mean()
        
        # RSI 계산
        self.data['rsi'] = self._calculate_rsi(self.data['close'])
        
        # 수익률 계산
        self.data['returns'] = self.data['close'].pct_change()
        
        self.logger.info("기술적 지표 계산 완료")
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def run_backtest(self) -> Dict:
        """
        백테스트 실행
        
        Returns:
            Dict: 백테스트 결과 (거래 내역, 성과 지표)
        """
        if self.data is None:
            raise ValueError("데이터가 로딩되지 않았습니다. load_data()를 먼저 호출하세요")
        
        self.logger.info("백테스트 시작")
        
        # 거래 내역 초기화
        self.trades = []
        position = None
        
        # 백테스트 실행
        for i, (date, row) in enumerate(self.data.iterrows()):
            if i < 2:  # 최소 데이터 필요
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
                    self._exit_position(position, date, current_price, row)
                    self.logger.info(f"매도: {date.strftime('%Y-%m-%d')} - 가격: {current_price:,.0f}")
                    position = None
        
        # 마지막 포지션 정리
        if position is not None:
            last_date = self.data.index[-1]
            last_price = self.data['close'].iloc[-1]
            self._exit_position(position, last_date, last_price, self.data.iloc[-1])
        
        # 성과 분석
        self.performance = self._analyze_performance()
        
        self.logger.info(f"백테스트 완료: {len(self.trades)}개 거래")
        return {
            'trades': self.trades,
            'performance': self.performance
        }
    
    def _should_buy(self, row: pd.Series, index: int) -> bool:
        """매수 신호 확인"""
        # 기본 조건: 현재가가 돌파선을 상향 돌파
        breakout_condition = row['close'] > row['breakout_line']
        
        # 거래량 필터: 현재 거래량이 평균의 volume_filter배 이상
        volume_condition = row['volume'] >= row['volume_ma'] * self.volume_filter
        
        # RSI 필터: RSI가 임계값 이하
        rsi_condition = row['rsi'] <= self.rsi_threshold
        
        return breakout_condition and volume_condition and rsi_condition
    
    def _should_sell(self, position: Dict, row: pd.Series, current_date: datetime) -> bool:
        """매도 신호 확인"""
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
        """포지션 진입"""
        position = {
            'entry_date': date,
            'entry_price': price,
            'position_size': self.position_size,
            'breakout_line': row['breakout_line'],
            'volume': row['volume'],
            'rsi': row['rsi']
        }
        return position
    
    def _exit_position(self, position: Dict, exit_date: datetime, exit_price: float, row: pd.Series) -> None:
        """포지션 청산"""
        entry_price = position['entry_price']
        returns = (exit_price - entry_price) / entry_price
        
        # 거래 비용 고려 (0.1% 수수료)
        transaction_cost = 0.001
        net_returns = returns - transaction_cost
        
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
            'rsi': position['rsi']
        }
        
        self.trades.append(trade)
    
    def _analyze_performance(self) -> Dict:
        """성과 분석"""
        if not self.trades:
            return {}
        
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
        
        performance = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_returns': total_returns,
            'avg_returns': avg_returns,
            'returns_std': returns_std,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio
        }
        
        return performance
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def plot_results(self, save_path: Optional[str] = None) -> None:
        """결과 시각화"""
        if self.data is None or not self.trades:
            self.logger.warning("시각화할 데이터가 없습니다")
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # 1. 가격 차트 및 거래 신호
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['close'], label='종가', linewidth=1)
        ax1.plot(self.data.index, self.data['breakout_line'], label='돌파선', alpha=0.7, linestyle='--')
        
        # 거래 신호 표시
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            buy_signals = trades_df['entry_date']
            sell_signals = trades_df['exit_date']
            buy_prices = trades_df['entry_price']
            sell_prices = trades_df['exit_price']
            
            ax1.scatter(buy_signals, buy_prices, color='red', marker='^', s=100, label='매수', zorder=5)
            ax1.scatter(sell_signals, sell_prices, color='blue', marker='v', s=100, label='매도', zorder=5)
        
        ax1.set_title('변동성 돌파 전략 - 가격 차트 및 거래 신호', fontsize=14, fontweight='bold')
        ax1.set_ylabel('가격 (원)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 누적 수익률
        ax2 = axes[1]
        if not trades_df.empty:
            cumulative_returns = (1 + trades_df['net_returns']).cumprod()
            ax2.plot(trades_df['exit_date'], cumulative_returns, marker='o', linewidth=2)
            ax2.axhline(y=1, color='black', linestyle='--', alpha=0.5)
            ax2.set_title('누적 수익률', fontsize=14, fontweight='bold')
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
            
            # 수익률 값 표시
            for i, (bar, ret) in enumerate(zip(bars, trades_df['net_returns'])):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.3),
                        f'{ret*100:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"차트 저장 완료: {save_path}")
        
        plt.show()
    
    def print_performance(self) -> None:
        """성과 지표 출력"""
        if not self.performance:
            self.logger.warning("성과 분석 결과가 없습니다")
            return
        
        print("\n" + "="*50)
        print("변동성 돌파 전략 백테스트 결과")
        print("="*50)
        
        print(f"총 거래 횟수: {self.performance['total_trades']}회")
        print(f"승리 거래: {self.performance['winning_trades']}회")
        print(f"패배 거래: {self.performance['losing_trades']}회")
        print(f"승률: {self.performance['win_rate']:.1%}")
        print(f"총 수익률: {self.performance['total_returns']:.1%}")
        print(f"평균 수익률: {self.performance['avg_returns']:.1%}")
        print(f"수익률 표준편차: {self.performance['returns_std']:.1%}")
        print(f"샤프 비율: {self.performance['sharpe_ratio']:.2f}")
        print(f"최대 낙폭: {self.performance['max_drawdown']:.1%}")
        print(f"평균 승리: {self.performance['avg_win']:.1%}")
        print(f"평균 손실: {self.performance['avg_loss']:.1%}")
        print(f"수익/손실 비율: {self.performance['profit_loss_ratio']:.2f}")
        
        print("\n" + "="*50)


def create_sample_data(start_date: str = '2023-01-01', end_date: str = '2023-12-31') -> pd.DataFrame:
    """
    샘플 데이터 생성 (테스트용)
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
    
    Returns:
        pd.DataFrame: OHLCV 데이터
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(42)
    
    # 기본 가격 설정
    base_price = 50000000  # 5천만원
    prices = [base_price]
    
    # 랜덤 워크로 가격 생성
    for i in range(len(dates) - 1):
        daily_return = np.random.normal(0, 0.02)  # 2% 일일 변동성
        new_price = prices[-1] * (1 + daily_return)
        prices.append(new_price)
    
    # OHLCV 데이터 생성
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 간단한 OHLC 생성
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = prices[i-1] if i > 0 else close
        volume = np.random.randint(1000000, 10000000)
        
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
    backtest.plot_results('volatility_breakout_backtest_results.png')


