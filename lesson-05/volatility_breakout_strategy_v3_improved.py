#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 구현 (개선된 버전)
5차시 세 번째 프롬프트 - 코드 품질 개선

개선 사항:
1. 성능: 데이터 처리 최적화, 메모리 효율성 개선
2. 가독성: 타입 힌트 추가, 상수 분리, 함수 분할
3. 안정성: 예외 처리 강화, 입력 검증, 설정 검증
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import requests
import time
import logging
from dataclasses import dataclass
from enum import Enum
import warnings

# 한글 폰트 설정 (Windows)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 경고 메시지 필터링
warnings.filterwarnings('ignore', category=FutureWarning)

class TradeReason(Enum):
    """거래 사유 열거형"""
    PROFIT_TAKING = "익절"
    STOP_LOSS = "손절"
    TIME_STOP = "시간 손절"
    BACKTEST_END = "백테스트 종료"

@dataclass
class TradeRecord:
    """거래 기록 데이터 클래스"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    profit_rate: float
    profit_amount: float
    reason: TradeReason
    holding_time: timedelta

@dataclass
class StrategyConfig:
    """전략 설정 데이터 클래스"""
    initial_capital: float = 1_000_000
    position_size_ratio: float = 0.05
    profit_target: float = 0.03  # 3%
    stop_loss: float = 0.02  # 2%
    time_stop_hours: int = 24
    breakout_multiplier: float = 0.5
    api_timeout: int = 10
    max_retries: int = 3

class VolatilityBreakoutStrategy:
    """
    변동성 돌파 전략 클래스 (개선된 버전)
    
    전략 설명:
    - 일일 고가, 저가, 시가, 종가 데이터 사용
    - 돌파선 = 전일 고가 + (전일 고가 - 전일 저가) × 0.5
    - 매수: 현재가가 돌파선을 위로 넘을 때
    - 매도: 손절(-2%), 익절(+3%), 시간 손절(24시간)
    - 포지션 크기: 자본의 5%로 제한
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        전략 초기화
        
        Args:
            config: 전략 설정 객체
        """
        self.config = config or StrategyConfig()
        self._validate_config()
        
        self.current_capital = self.config.initial_capital
        self.position: Optional[Dict] = None
        self.trades: List[TradeRecord] = []
        self.entry_time: Optional[datetime] = None
        
        # 로깅 설정
        self._setup_logging()
        
        self.logger.info(f"변동성 돌파 전략 초기화 완료 - 초기 자본: {self.config.initial_capital:,}원")
    
    def _validate_config(self) -> None:
        """설정 값 검증"""
        if self.config.initial_capital <= 0:
            raise ValueError("초기 자본은 0보다 커야 합니다.")
        if not 0 < self.config.position_size_ratio <= 1:
            raise ValueError("포지션 크기 비율은 0과 1 사이여야 합니다.")
        if self.config.profit_target <= 0:
            raise ValueError("익절 목표는 0보다 커야 합니다.")
        if self.config.stop_loss <= 0:
            raise ValueError("손절 기준은 0보다 커야 합니다.")
        if self.config.time_stop_hours <= 0:
            raise ValueError("시간 손절 시간은 0보다 커야 합니다.")
    
    def _setup_logging(self) -> None:
        """로깅 설정"""
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 핸들러가 이미 있는지 확인
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # 파일 핸들러
            file_handler = logging.FileHandler('volatility_breakout_v3.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def calculate_breakout_line(self, prev_high: float, prev_low: float) -> float:
        """
        돌파선 계산
        
        Args:
            prev_high: 전일 고가
            prev_low: 전일 저가
            
        Returns:
            돌파선 가격
        """
        if prev_high <= prev_low:
            raise ValueError("고가는 저가보다 커야 합니다.")
        
        volatility = prev_high - prev_low
        breakout_line = prev_high + (volatility * self.config.breakout_multiplier)
        return breakout_line
    
    def should_buy(self, current_price: float, prev_high: float, prev_low: float) -> bool:
        """
        매수 조건 확인
        
        Args:
            current_price: 현재가
            prev_high: 전일 고가
            prev_low: 전일 저가
            
        Returns:
            매수 여부
        """
        if self.position is not None:
            return False
        
        try:
            breakout_line = self.calculate_breakout_line(prev_high, prev_low)
            
            if current_price > breakout_line:
                self.logger.info(f"매수 신호 발생! 현재가: {current_price:,.0f}원, 돌파선: {breakout_line:,.0f}원")
                return True
            
            return False
        except ValueError as e:
            self.logger.error(f"돌파선 계산 오류: {e}")
            return False
    
    def should_sell(self, current_price: float, entry_price: float, entry_time: datetime) -> Tuple[bool, Optional[TradeReason]]:
        """
        매도 조건 확인
        
        Args:
            current_price: 현재가
            entry_price: 진입가
            entry_time: 진입 시간
            
        Returns:
            (매도 여부, 매도 사유)
        """
        if self.position is None:
            return False, None
        
        try:
            # 수익률 계산
            profit_rate = (current_price - entry_price) / entry_price
            
            # 익절 조건
            if profit_rate >= self.config.profit_target:
                self.logger.info(f"익절 신호 발생! 수익률: {profit_rate*100:.2f}%")
                return True, TradeReason.PROFIT_TAKING
            
            # 손절 조건
            if profit_rate <= -self.config.stop_loss:
                self.logger.info(f"손절 신호 발생! 수익률: {profit_rate*100:.2f}%")
                return True, TradeReason.STOP_LOSS
            
            # 시간 손절 조건
            if datetime.now() - entry_time >= timedelta(hours=self.config.time_stop_hours):
                self.logger.info(f"시간 손절 신호 발생! 보유 시간: {datetime.now() - entry_time}")
                return True, TradeReason.TIME_STOP
            
            return False, None
        except Exception as e:
            self.logger.error(f"매도 조건 확인 오류: {e}")
            return False, None
    
    def execute_buy(self, price: float, timestamp: datetime) -> None:
        """
        매수 실행
        
        Args:
            price: 매수가격
            timestamp: 거래 시간
        """
        if price <= 0:
            raise ValueError("가격은 0보다 커야 합니다.")
        
        position_value = self.current_capital * self.config.position_size_ratio
        quantity = position_value / price
        
        self.position = {
            'entry_price': price,
            'quantity': quantity,
            'entry_time': timestamp,
            'position_value': position_value
        }
        
        self.entry_time = timestamp
        
        self.logger.info(f"매수 실행 - 가격: {price:,.0f}원, 수량: {quantity:.6f}, 포지션 가치: {position_value:,.0f}원")
    
    def execute_sell(self, price: float, timestamp: datetime, reason: TradeReason) -> None:
        """
        매도 실행
        
        Args:
            price: 매도가격
            timestamp: 거래 시간
            reason: 매도 사유
        """
        if self.position is None:
            self.logger.warning("매도할 포지션이 없습니다.")
            return
        
        if price <= 0:
            raise ValueError("가격은 0보다 커야 합니다.")
        
        entry_price = self.position['entry_price']
        quantity = self.position['quantity']
        entry_time = self.position['entry_time']
        
        # 수익률 계산
        profit_rate = (price - entry_price) / entry_price
        profit_amount = (price - entry_price) * quantity
        
        # 거래 기록 저장
        trade = TradeRecord(
            entry_time=entry_time,
            exit_time=timestamp,
            entry_price=entry_price,
            exit_price=price,
            quantity=quantity,
            profit_rate=profit_rate,
            profit_amount=profit_amount,
            reason=reason,
            holding_time=timestamp - entry_time
        )
        
        self.trades.append(trade)
        
        # 자본 업데이트
        self.current_capital += profit_amount
        
        # 포지션 초기화
        self.position = None
        self.entry_time = None
        
        self.logger.info(f"매도 실행 - 가격: {price:,.0f}원, 수익률: {profit_rate*100:.2f}%, 수익금: {profit_amount:,.0f}원, 사유: {reason.value}")
    
    def get_crypto_data(self, symbol: str = 'bitcoin', days: int = 30) -> Optional[pd.DataFrame]:
        """
        암호화폐 데이터 가져오기 (CoinGecko API 사용)
        
        Args:
            symbol: 암호화폐 심볼
            days: 가져올 일수
            
        Returns:
            OHLCV 데이터 또는 None
        """
        for attempt in range(self.config.max_retries):
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
                params = {
                    'vs_currency': 'krw',
                    'days': days,
                    'interval': 'daily'
                }
                
                response = requests.get(url, params=params, timeout=self.config.api_timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # 데이터 변환
                prices = data['prices']
                volumes = data['total_volumes']
                
                df = pd.DataFrame(prices, columns=['timestamp', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['volume'] = [v[1] for v in volumes]
                
                # OHLC 데이터 생성 (개선된 방법)
                df = self._generate_ohlc_data(df)
                
                self.logger.info(f"{symbol} 데이터 {len(df)}일 수집 완료")
                return df
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API 요청 실패 (시도 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    self.logger.error(f"데이터 수집 최종 실패: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"데이터 처리 오류: {e}")
                return None
        
        return None
    
    def _generate_ohlc_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        OHLC 데이터 생성 (개선된 방법)
        
        Args:
            df: 기본 데이터프레임
            
        Returns:
            OHLC 데이터가 포함된 데이터프레임
        """
        # 더 현실적인 OHLC 데이터 생성
        df['open'] = df['close'].shift(1)
        df.loc[0, 'open'] = df.loc[0, 'close']
        
        # 변동성 기반 고가/저가 생성
        volatility = df['close'].pct_change().abs().fillna(0.02)
        high_multiplier = 1 + volatility * np.random.uniform(0.3, 0.8, len(df))
        low_multiplier = 1 - volatility * np.random.uniform(0.3, 0.8, len(df))
        
        df['high'] = df['close'] * high_multiplier
        df['low'] = df['close'] * low_multiplier
        
        # 고가는 종가보다 높고, 저가는 종가보다 낮도록 보정
        df['high'] = np.maximum(df['high'], df['close'])
        df['low'] = np.minimum(df['low'], df['close'])
        
        df = df.dropna()
        df = df.reset_index(drop=True)
        
        return df
    
    def backtest(self, data: pd.DataFrame) -> None:
        """
        백테스트 실행
        
        Args:
            data: OHLCV 데이터
        """
        if data is None or len(data) < 2:
            raise ValueError("백테스트를 위한 충분한 데이터가 없습니다.")
        
        self.logger.info("백테스트 시작")
        
        try:
            for i in range(1, len(data)):
                current_row = data.iloc[i]
                prev_row = data.iloc[i-1]
                
                current_price = current_row['close']
                prev_high = prev_row['high']
                prev_low = prev_row['low']
                timestamp = current_row['timestamp']
                
                # 매도 조건 확인 (포지션이 있는 경우)
                if self.position is not None:
                    should_sell, sell_reason = self.should_sell(
                        current_price, 
                        self.position['entry_price'], 
                        self.position['entry_time']
                    )
                    
                    if should_sell and sell_reason:
                        self.execute_sell(current_price, timestamp, sell_reason)
                
                # 매수 조건 확인 (포지션이 없는 경우)
                if self.position is None:
                    if self.should_buy(current_price, prev_high, prev_low):
                        self.execute_buy(current_price, timestamp)
            
            # 마지막에 포지션이 있다면 강제 매도
            if self.position is not None:
                last_price = data.iloc[-1]['close']
                last_time = data.iloc[-1]['timestamp']
                self.execute_sell(last_price, last_time, TradeReason.BACKTEST_END)
            
            self.logger.info("백테스트 완료")
            
        except Exception as e:
            self.logger.error(f"백테스트 실행 중 오류: {e}")
            raise
    
    def calculate_performance(self) -> Dict[str, Union[str, int, float]]:
        """
        성과 분석
        
        Returns:
            성과 지표 딕셔너리
        """
        if not self.trades:
            return {"메시지": "거래 기록이 없습니다."}
        
        try:
            total_trades = len(self.trades)
            winning_trades = len([t for t in self.trades if t.profit_rate > 0])
            losing_trades = len([t for t in self.trades if t.profit_rate < 0])
            
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            
            total_profit = sum([t.profit_amount for t in self.trades])
            total_return = (self.current_capital - self.config.initial_capital) / self.config.initial_capital * 100
            
            profit_rates = [t.profit_rate for t in self.trades]
            avg_profit = np.mean(profit_rates) * 100
            avg_winning = np.mean([t.profit_rate for t in self.trades if t.profit_rate > 0]) * 100 if winning_trades > 0 else 0
            avg_losing = np.mean([t.profit_rate for t in self.trades if t.profit_rate < 0]) * 100 if losing_trades > 0 else 0
            
            # 최대 손실 (MDD) 계산
            cumulative_returns = np.cumprod([1 + t.profit_rate for t in self.trades])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
            
            performance = {
                "초기 자본": f"{self.config.initial_capital:,.0f}원",
                "최종 자본": f"{self.current_capital:,.0f}원",
                "총 수익금": f"{total_profit:,.0f}원",
                "총 수익률": f"{total_return:.2f}%",
                "총 거래 횟수": total_trades,
                "승률": f"{win_rate:.2f}%",
                "평균 수익률": f"{avg_profit:.2f}%",
                "평균 승리 수익률": f"{avg_winning:.2f}%",
                "평균 손실 수익률": f"{avg_losing:.2f}%",
                "최대 손실률": f"{max_drawdown:.2f}%"
            }
            
            return performance
            
        except Exception as e:
            self.logger.error(f"성과 분석 오류: {e}")
            return {"오류": f"성과 분석 실패: {e}"}
    
    def plot_results(self, data: pd.DataFrame) -> None:
        """
        결과 시각화
        
        Args:
            data: OHLCV 데이터
        """
        try:
            plt.figure(figsize=(15, 10))
            
            # 가격 차트
            plt.subplot(2, 1, 1)
            plt.plot(data['timestamp'], data['close'], label='종가', linewidth=1)
            plt.plot(data['timestamp'], data['high'], label='고가', alpha=0.7, linewidth=0.5)
            plt.plot(data['timestamp'], data['low'], label='저가', alpha=0.7, linewidth=0.5)
            
            # 거래 포인트 표시
            for trade in self.trades:
                plt.axvline(x=trade.entry_time, color='green', alpha=0.3, linestyle='--')
                plt.axvline(x=trade.exit_time, color='red', alpha=0.3, linestyle='--')
            
            plt.title('변동성 돌파 전략 - 가격 차트', fontsize=16, fontweight='bold')
            plt.xlabel('날짜', fontsize=12)
            plt.ylabel('가격 (원)', fontsize=12)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 수익률 차트
            plt.subplot(2, 1, 2)
            if self.trades:
                trade_numbers = range(1, len(self.trades) + 1)
                returns = [t.profit_rate * 100 for t in self.trades]
                
                colors = ['green' if r > 0 else 'red' for r in returns]
                plt.bar(trade_numbers, returns, color=colors, alpha=0.7)
                
                plt.title('거래별 수익률', fontsize=16, fontweight='bold')
                plt.xlabel('거래 번호', fontsize=12)
                plt.ylabel('수익률 (%)', fontsize=12)
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('volatility_breakout_strategy_v3_results.png', dpi=300, bbox_inches='tight')
            plt.show()
            
        except Exception as e:
            self.logger.error(f"차트 생성 오류: {e}")
            raise

def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("변동성 돌파 전략 백테스트 (개선된 버전)")
    print("=" * 60)
    
    try:
        # 전략 설정
        config = StrategyConfig(
            initial_capital=1_000_000,  # 100만원
            position_size_ratio=0.05,   # 5%
            profit_target=0.03,         # 3%
            stop_loss=0.02,             # 2%
            time_stop_hours=24          # 24시간
        )
        
        # 전략 초기화
        strategy = VolatilityBreakoutStrategy(config)
        
        # 데이터 수집
        print("데이터 수집 중...")
        data = strategy.get_crypto_data('bitcoin', days=90)
        
        if data is None:
            print("데이터 수집에 실패했습니다.")
            return
        
        print(f"수집된 데이터: {len(data)}일")
        print(f"기간: {data['timestamp'].min()} ~ {data['timestamp'].max()}")
        
        # 백테스트 실행
        print("\n백테스트 실행 중...")
        strategy.backtest(data)
        
        # 성과 분석
        print("\n" + "=" * 60)
        print("성과 분석 결과")
        print("=" * 60)
        
        performance = strategy.calculate_performance()
        for key, value in performance.items():
            print(f"{key}: {value}")
        
        # 거래 내역 출력
        if strategy.trades:
            print("\n" + "=" * 60)
            print("거래 내역")
            print("=" * 60)
            
            for i, trade in enumerate(strategy.trades, 1):
                print(f"거래 {i}:")
                print(f"  진입: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} - {trade.entry_price:,.0f}원")
                print(f"  청산: {trade.exit_time.strftime('%Y-%m-%d %H:%M')} - {trade.exit_price:,.0f}원")
                print(f"  수익률: {trade.profit_rate*100:.2f}%")
                print(f"  수익금: {trade.profit_amount:,.0f}원")
                print(f"  사유: {trade.reason.value}")
                print(f"  보유시간: {trade.holding_time}")
                print()
        
        # 차트 생성
        print("결과 차트 생성 중...")
        strategy.plot_results(data)
        
        print("백테스트 완료!")
        
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {e}")
        logging.error(f"메인 함수 오류: {e}")

if __name__ == "__main__":
    main()
