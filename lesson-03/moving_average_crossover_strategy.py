#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이동평균 크로스오버 전략 (Moving Average Crossover Strategy)
단기 이동평균(5일)과 장기 이동평균(20일)을 사용하여 매수/매도 신호를 생성하는 자동매매 시스템
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
import matplotlib
matplotlib.use('Qt5Agg')  # Qt5 백엔드 사용
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ma_crossover.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class PriceData:
    """가격 데이터 구조"""
    date: datetime
    price: float
    volume: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'date': self.date.isoformat(),
            'price': self.price,
            'volume': self.volume
        }

@dataclass
class TradeSignal:
    """거래 신호 구조"""
    timestamp: datetime
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    short_ma: float
    long_ma: float
    volume: float
    avg_volume: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'price': self.price,
            'short_ma': self.short_ma,
            'long_ma': self.long_ma,
            'volume': self.volume,
            'avg_volume': self.avg_volume,
            'reason': self.reason
        }

@dataclass
class Position:
    """포지션 정보 구조"""
    entry_time: datetime
    entry_price: float
    quantity: float
    position_size: float
    short_ma_at_entry: float
    long_ma_at_entry: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'position_size': self.position_size,
            'short_ma_at_entry': self.short_ma_at_entry,
            'long_ma_at_entry': self.long_ma_at_entry
        }

class DataCollector:
    """데이터 수집 클래스"""
    
    def __init__(self):
        """초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_bitcoin_price_data(self, days: int = 30) -> List[PriceData]:
        """비트코인 가격 및 거래량 데이터 수집 (CoinGecko API 사용)"""
        try:
            # 일별 가격 데이터 수집
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "krw",
                "days": days
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                price_list = []
                
                # 가격 데이터 처리
                if "prices" in data and data["prices"]:
                    for timestamp_ms, price in data["prices"]:
                        date = datetime.fromtimestamp(timestamp_ms / 1000)
                        
                        price_data = PriceData(
                            date=date,
                            price=float(price),
                            volume=0.0  # 기본값 설정
                        )
                        price_list.append(price_data)
                
                # 거래량 데이터 처리 (가능한 경우)
                if "total_volumes" in data and data["total_volumes"]:
                    for i, (timestamp_ms, volume) in enumerate(data["total_volumes"]):
                        if i < len(price_list):
                            price_list[i].volume = float(volume)
                
                # 날짜순으로 정렬
                price_list.sort(key=lambda x: x.date)
                
                # 거래량이 0인 경우 평균값으로 대체
                if price_list:
                    avg_volume = np.mean([p.volume for p in price_list if p.volume > 0])
                    if avg_volume > 0:
                        for price_data in price_list:
                            if price_data.volume == 0:
                                price_data.volume = avg_volume
                
                logging.info(f"비트코인 가격 데이터 {len(price_list)}개 수집 완료")
                return price_list
            else:
                logging.error(f"API 호출 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"데이터 수집 오류: {e}")
            return []
    
    def get_current_bitcoin_price(self) -> Optional[float]:
        """현재 비트코인 가격 조회"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "krw"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "bitcoin" in data and "krw" in data["bitcoin"]:
                    return float(data["bitcoin"]["krw"])
            return None
            
        except Exception as e:
            logging.error(f"현재 가격 조회 오류: {e}")
            return None

class MovingAverageCalculator:
    """이동평균 계산 클래스"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """단순이동평균 (Simple Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i-period+1:i+1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """지수가동평균 (Exponential Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        ema_values = []
        multiplier = 2 / (period + 1)
        
        # 첫 번째 EMA는 SMA로 계산
        first_ema = sum(prices[:period]) / period
        ema_values.append(first_ema)
        
        # 나머지 EMA 계산
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def calculate_volume_ma(volumes: List[float], period: int) -> List[float]:
        """거래량 이동평균 계산"""
        if len(volumes) < period:
            return []
        
        volume_ma_values = []
        for i in range(period - 1, len(volumes)):
            volume_ma = sum(volumes[i-period+1:i+1]) / period
            volume_ma_values.append(volume_ma)
        
        return volume_ma_values

class MovingAverageCrossoverStrategy:
    """이동평균 크로스오버 전략 클래스"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20, volume_threshold: float = 1.2):
        """
        전략 초기화
        
        Args:
            short_period: 단기 이동평균 기간 (기본값: 5일)
            long_period: 장기 이동평균 기간 (기본값: 20일)
            volume_threshold: 거래량 임계값 (평균 거래량의 배수)
        """
        self.short_period = short_period
        self.long_period = long_period
        self.volume_threshold = volume_threshold
        
        self.data_collector = DataCollector()
        self.ma_calculator = MovingAverageCalculator()
        
        self.price_data: List[PriceData] = []
        self.trade_signals: List[TradeSignal] = []
        self.current_position: Optional[Position] = None
        
        # 한글 폰트 설정
        self.setup_korean_font()
    
    def setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # macOS에서 사용 가능한 한글 폰트들
                korean_fonts = ['AppleGothic', 'Malgun Gothic', 'NanumGothic', 'Arial Unicode MS']
            elif system == "Windows":
                # Windows에서 사용 가능한 한글 폰트들
                korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum', 'Batang']
            else:  # Linux
                # Linux에서 사용 가능한 한글 폰트들
                korean_fonts = ['NanumGothic', 'DejaVu Sans', 'Liberation Sans']
            
            # 사용 가능한 폰트 찾기
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            
            for font in korean_fonts:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    plt.rcParams['axes.unicode_minus'] = False
                    logging.info(f"한글 폰트 설정: {font}")
                    return font
            
            # 한글 폰트를 찾지 못한 경우 기본 설정
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            logging.warning("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            return None
            
        except Exception as e:
            logging.warning(f"한글 폰트 설정 실패, 기본 폰트 사용: {e}")
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
    
    def load_data(self, days: int = 30) -> bool:
        """데이터 로드"""
        try:
            self.price_data = self.data_collector.get_bitcoin_price_data(days)
            if not self.price_data:
                logging.error("데이터 로드 실패")
                return False
            
            logging.info(f"데이터 로드 완료: {len(self.price_data)}개")
            return True
            
        except Exception as e:
            logging.error(f"데이터 로드 오류: {e}")
            return False
    
    def calculate_indicators(self) -> Tuple[List[float], List[float], List[float]]:
        """기술적 지표 계산"""
        if len(self.price_data) < self.long_period:
            return [], [], []
        
        prices = [p.price for p in self.price_data]
        volumes = [p.volume for p in self.price_data]
        
        # 이동평균 계산
        short_ma = self.ma_calculator.calculate_sma(prices, self.short_period)
        long_ma = self.ma_calculator.calculate_sma(prices, self.long_period)
        volume_ma = self.ma_calculator.calculate_volume_ma(volumes, self.long_period)
        
        return short_ma, long_ma, volume_ma
    
    def generate_signals(self) -> List[TradeSignal]:
        """거래 신호 생성"""
        if len(self.price_data) < self.long_period:
            return []
        
        short_ma, long_ma, volume_ma = self.calculate_indicators()
        
        if not short_ma or not long_ma:
            return []
        
        signals = []
        
        # 신호 생성 (크로스오버 지점 찾기)
        for i in range(1, len(short_ma)):
            current_idx = i + self.long_period - 1
            if current_idx >= len(self.price_data):
                break
                
            current_price = self.price_data[current_idx].price
            current_volume = self.price_data[current_idx].volume
            current_avg_volume = volume_ma[i] if i < len(volume_ma) else current_volume
            
            # 골든 크로스 (단기 > 장기)
            if (short_ma[i] > long_ma[i] and 
                short_ma[i-1] <= long_ma[i-1] and
                current_volume > current_avg_volume * self.volume_threshold):
                
                signal = TradeSignal(
                    timestamp=self.price_data[current_idx].date,
                    signal_type='BUY',
                    price=current_price,
                    short_ma=short_ma[i],
                    long_ma=long_ma[i],
                    volume=current_volume,
                    avg_volume=current_avg_volume,
                    reason=f"골든 크로스 (단기: {short_ma[i]:.0f}, 장기: {long_ma[i]:.0f})"
                )
                signals.append(signal)
                logging.info(f"매수 신호: {signal.timestamp} - {signal.reason}")
            
            # 데드 크로스 (단기 < 장기)
            elif (short_ma[i] < long_ma[i] and 
                  short_ma[i-1] >= long_ma[i-1]):
                
                signal = TradeSignal(
                    timestamp=self.price_data[current_idx].date,
                    signal_type='SELL',
                    price=current_price,
                    short_ma=short_ma[i],
                    long_ma=long_ma[i],
                    volume=current_volume,
                    avg_volume=current_avg_volume,
                    reason=f"데드 크로스 (단기: {short_ma[i]:.0f}, 장기: {long_ma[i]:.0f})"
                )
                signals.append(signal)
                logging.info(f"매도 신호: {signal.timestamp} - {signal.reason}")
        
        self.trade_signals = signals
        return signals
    
    def backtest_strategy(self) -> Dict[str, Any]:
        """전략 백테스트"""
        if not self.trade_signals:
            logging.warning("거래 신호가 없습니다.")
            return {}
        
        initial_balance = 1000000  # 100만원
        balance = initial_balance
        position = None
        trades = []
        
        for signal in self.trade_signals:
            if signal.signal_type == 'BUY' and position is None:
                # 매수
                position = {
                    'entry_time': signal.timestamp,
                    'entry_price': signal.price,
                    'quantity': balance / signal.price
                }
                balance = 0
                logging.info(f"매수: {signal.timestamp} - 가격: {signal.price:,.0f}원")
                
            elif signal.signal_type == 'SELL' and position is not None:
                # 매도
                profit = (signal.price - position['entry_price']) * position['quantity']
                balance = signal.price * position['quantity']
                
                trade = {
                    'entry_time': position['entry_time'],
                    'exit_time': signal.timestamp,
                    'entry_price': position['entry_price'],
                    'exit_price': signal.price,
                    'quantity': position['quantity'],
                    'profit': profit,
                    'return_rate': (profit / (position['entry_price'] * position['quantity'])) * 100
                }
                trades.append(trade)
                
                logging.info(f"매도: {signal.timestamp} - 가격: {signal.price:,.0f}원, 수익: {profit:,.0f}원")
                position = None
        
        # 최종 수익률 계산
        total_return = ((balance - initial_balance) / initial_balance) * 100
        win_trades = [t for t in trades if t['profit'] > 0]
        win_rate = len(win_trades) / len(trades) * 100 if trades else 0
        
        result = {
            'initial_balance': initial_balance,
            'final_balance': balance,
            'total_return': total_return,
            'total_trades': len(trades),
            'win_trades': len(win_trades),
            'win_rate': win_rate,
            'trades': trades
        }
        
        logging.info(f"백테스트 완료 - 총 수익률: {total_return:.2f}%, 승률: {win_rate:.2f}%")
        return result
    
    def create_chart(self, save_path: str = "bitcoin_ma_strategy.png"):
        """전략 차트 생성"""
        if not self.price_data:
            logging.error("차트를 그릴 데이터가 없습니다.")
            return
        
        short_ma, long_ma, volume_ma = self.calculate_indicators()
        
        if not short_ma or not long_ma:
            logging.error("이동평균 계산 실패")
            return
        
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 가격 차트 - 이동평균과 같은 길이로 맞춤
            start_idx = self.long_period - 1
            dates = [p.date for p in self.price_data[start_idx:]]
            prices = [p.price for p in self.price_data[start_idx:]]
            
            # 배열 길이 확인 및 조정
            min_length = min(len(dates), len(short_ma), len(long_ma))
            dates = dates[:min_length]
            prices = prices[:min_length]
            short_ma = short_ma[:min_length]
            long_ma = long_ma[:min_length]
            
            ax1.plot(dates, prices, label='비트코인 가격', linewidth=2, color='black')
            ax1.plot(dates, short_ma, label=f'{self.short_period}일 이동평균', linewidth=1.5, color='red')
            ax1.plot(dates, long_ma, label=f'{self.long_period}일 이동평균', linewidth=1.5, color='blue')
            
            # 거래 신호 표시
            for signal in self.trade_signals:
                if signal.signal_type == 'BUY':
                    ax1.scatter(signal.timestamp, signal.price, color='green', marker='^', s=100, zorder=5)
                else:
                    ax1.scatter(signal.timestamp, signal.price, color='red', marker='v', s=100, zorder=5)
            
            # 한글 폰트 적용
            current_font = plt.rcParams['font.family']
            ax1.set_title('비트코인 이동평균 크로스오버 전략', fontsize=16, fontweight='bold', fontfamily=current_font)
            ax1.set_ylabel('가격 (원)', fontsize=12, fontfamily=current_font)
            ax1.legend(prop={'family': current_font})
            ax1.grid(True, alpha=0.3)
            
            # 거래량 차트 - 같은 길이로 맞춤
            volumes = [p.volume for p in self.price_data[start_idx:]]
            volumes = volumes[:min_length]
            volume_ma = volume_ma[:min_length] if len(volume_ma) >= min_length else volume_ma
            
            ax2.bar(dates, volumes, alpha=0.6, color='gray', label='거래량')
            if len(volume_ma) == min_length:
                ax2.plot(dates, volume_ma, color='orange', linewidth=2, label=f'{self.long_period}일 거래량 평균')
            ax2.set_ylabel('거래량', fontsize=12, fontfamily=current_font)
            ax2.set_xlabel('날짜', fontsize=12, fontfamily=current_font)
            ax2.legend(prop={'family': current_font})
            ax2.grid(True, alpha=0.3)
            
            # x축 날짜 포맷
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.show()
            
            logging.info(f"차트 저장 완료: {save_path}")
            
        except Exception as e:
            logging.error(f"차트 생성 오류: {e}")
    
    def run_strategy(self, days: int = 30):
        """전략 실행"""
        logging.info("=== 이동평균 크로스오버 전략 시작 ===")
        
        # 1. 데이터 로드
        if not self.load_data(days):
            return
        
        # 2. 거래 신호 생성
        signals = self.generate_signals()
        if not signals:
            logging.warning("거래 신호가 생성되지 않았습니다.")
            return
        
        # 3. 백테스트 실행
        result = self.backtest_strategy()
        if result:
            logging.info(f"총 거래 횟수: {result['total_trades']}")
            logging.info(f"승률: {result['win_rate']:.2f}%")
            logging.info(f"총 수익률: {result['total_return']:.2f}%")
        
        # 4. 차트 생성
        self.create_chart()
        
        logging.info("=== 전략 실행 완료 ===")

def main():
    """메인 함수"""
    try:
        # 전략 설정
        strategy = MovingAverageCrossoverStrategy(
            short_period=5,
            long_period=20,
            volume_threshold=1.2
        )
        
        # 전략 실행
        strategy.run_strategy(days=30)
        
    except KeyboardInterrupt:
        logging.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logging.error(f"실행 오류: {e}")

if __name__ == "__main__":
    main()
