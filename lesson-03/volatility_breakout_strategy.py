#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 (Volatility Breakout Strategy)
일일 변동폭이 설정한 기준값을 넘을 때 매수 신호를 생성하고,
손절과 익절 로직을 포함한 자동매매 시스템
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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('volatility_breakout.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class OHLCData:
    """OHLC 데이터 구조"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'date': self.date.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

@dataclass
class TradeSignal:
    """거래 신호 구조"""
    timestamp: datetime
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    reason: str
    breakout_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'price': self.price,
            'reason': self.reason,
            'breakout_level': self.breakout_level
        }

@dataclass
class Position:
    """포지션 정보 구조"""
    entry_time: datetime
    entry_price: float
    quantity: float
    position_size: float
    stop_loss: float
    take_profit: float
    time_stop: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'position_size': self.position_size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'time_stop': self.time_stop.isoformat()
        }

class DataCollector:
    """데이터 수집 클래스"""
    
    def __init__(self):
        """초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_bitcoin_ohlc_data(self, days: int = 30) -> List[OHLCData]:
        """비트코인 OHLC 데이터 수집 (CoinGecko API 사용)"""
        try:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
            params = {
                "vs_currency": "krw",
                "days": days
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                ohlc_list = []
                
                for item in data:
                    timestamp_ms, open_price, high_price, low_price, close_price = item
                    date = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    ohlc_data = OHLCData(
                        date=date,
                        open=float(open_price),
                        high=float(high_price),
                        low=float(low_price),
                        close=float(close_price),
                        volume=0.0  # CoinGecko OHLC API는 거래량을 제공하지 않음
                    )
                    ohlc_list.append(ohlc_data)
                
                # 날짜순으로 정렬
                ohlc_list.sort(key=lambda x: x.date)
                logging.info(f"비트코인 OHLC 데이터 {len(ohlc_list)}개 수집 완료")
                return ohlc_list
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

class VolatilityBreakoutStrategy:
    """변동성 돌파 전략 클래스"""
    
    def __init__(self, initial_capital: float = 10000000):
        """초기화"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position: Optional[Position] = None
        self.trade_history: List[Dict[str, Any]] = []
        self.signals: List[TradeSignal] = []
        
        # 전략 파라미터
        self.breakout_multiplier = 0.5  # 돌파선 계산 계수
        self.stop_loss_percent = 0.02   # 손절 비율 (-2%)
        self.take_profit_percent = 0.03 # 익절 비율 (+3%)
        self.max_position_size = 0.05   # 최대 포지션 크기 (5%)
        self.time_stop_hours = 24       # 시간 손절 (24시간)
        
        # 데이터 수집기
        self.data_collector = DataCollector()
        
        # matplotlib 한글 폰트 설정
        self.setup_korean_font()
        
        logging.info(f"변동성 돌파 전략 초기화 완료 (초기 자본: {initial_capital:,.0f}원)")
    
    def setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            font_path = 'C:/Windows/Fonts/malgun.ttf'
            if not font_manager.findfont(font_manager.FontProperties(fname=font_path)):
                plt.rcParams['font.family'] = 'DejaVu Sans'
            else:
                font_prop = font_manager.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
            logging.info("한글 폰트 설정 완료")
        except Exception as e:
            logging.warning(f"한글 폰트 설정 실패: {e}")
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def calculate_breakout_level(self, prev_high: float, prev_low: float) -> float:
        """돌파선 계산: 전일 고가 + (전일 고가 - 전일 저가) * 0.5"""
        volatility = prev_high - prev_low
        breakout_level = prev_high + (volatility * self.breakout_multiplier)
        return breakout_level
    
    def check_buy_signal(self, current_price: float, prev_high: float, prev_low: float) -> bool:
        """매수 신호 확인: 현재가가 돌파선을 위로 넘는지"""
        breakout_level = self.calculate_breakout_level(prev_high, prev_low)
        return current_price > breakout_level
    
    def check_sell_signal(self, current_price: float, position: Position) -> Tuple[bool, str]:
        """매도 신호 확인: 손절, 익절, 시간 손절"""
        current_time = datetime.now()
        
        # 손절 확인
        if current_price <= position.stop_loss:
            return True, "손절"
        
        # 익절 확인
        if current_price >= position.take_profit:
            return True, "익절"
        
        # 시간 손절 확인
        if current_time >= position.time_stop:
            return True, "시간 손절"
        
        return False, ""
    
    def calculate_position_size(self, entry_price: float) -> float:
        """포지션 크기 계산 (자본의 5%로 제한)"""
        max_amount = self.current_capital * self.max_position_size
        quantity = max_amount / entry_price
        return quantity
    
    def execute_buy(self, price: float, breakout_level: float) -> bool:
        """매수 실행"""
        if self.position is not None:
            logging.warning("이미 포지션이 존재합니다. 매수 불가")
            return False
        
        try:
            # 포지션 크기 계산
            quantity = self.calculate_position_size(price)
            position_size = quantity * price
            
            # 손절가, 익절가, 시간 손절 계산
            stop_loss = price * (1 - self.stop_loss_percent)
            take_profit = price * (1 + self.take_profit_percent)
            time_stop = datetime.now() + timedelta(hours=self.time_stop_hours)
            
            # 포지션 생성
            self.position = Position(
                entry_time=datetime.now(),
                entry_price=price,
                quantity=quantity,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                time_stop=time_stop
            )
            
            # 자본 차감
            self.current_capital -= position_size
            
            # 거래 신호 기록
            signal = TradeSignal(
                timestamp=datetime.now(),
                signal_type="BUY",
                price=price,
                reason="돌파선 돌파",
                breakout_level=breakout_level
            )
            self.signals.append(signal)
            
            logging.info(f"매수 실행: 가격 {price:,.0f}원, 수량 {quantity:.6f}, "
                        f"손절가 {stop_loss:,.0f}원, 익절가 {take_profit:,.0f}원")
            return True
            
        except Exception as e:
            logging.error(f"매수 실행 오류: {e}")
            return False
    
    def execute_sell(self, price: float, reason: str) -> bool:
        """매도 실행"""
        if self.position is None:
            logging.warning("매도할 포지션이 없습니다.")
            return False
        
        try:
            # 수익/손실 계산
            pnl = (price - self.position.entry_price) * self.position.quantity
            pnl_percent = (pnl / self.position.position_size) * 100
            
            # 자본 복원
            sell_amount = self.position.quantity * price
            self.current_capital += sell_amount
            
            # 거래 기록
            trade_record = {
                'entry_time': self.position.entry_time,
                'exit_time': datetime.now(),
                'entry_price': self.position.entry_price,
                'exit_price': price,
                'quantity': self.position.quantity,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'reason': reason,
                'position_size': self.position.position_size
            }
            self.trade_history.append(trade_record)
            
            # 거래 신호 기록
            signal = TradeSignal(
                timestamp=datetime.now(),
                signal_type="SELL",
                price=price,
                reason=reason,
                breakout_level=0.0
            )
            self.signals.append(signal)
            
            logging.info(f"매도 실행: 가격 {price:,.0f}원, {reason}, "
                        f"수익률 {pnl_percent:+.2f}%, 수익/손실 {pnl:+,.0f}원")
            
            # 포지션 초기화
            self.position = None
            return True
            
        except Exception as e:
            logging.error(f"매도 실행 오류: {e}")
            return False
    
    def run_strategy(self, days: int = 30) -> Dict[str, Any]:
        """전략 실행"""
        logging.info("변동성 돌파 전략 실행 시작")
        
        try:
            # 데이터 수집
            ohlc_data = self.data_collector.get_bitcoin_ohlc_data(days)
            if len(ohlc_data) < 2:
                logging.error("충분한 데이터가 수집되지 않았습니다.")
                return {}
            
            # 현재 가격 조회
            current_price = self.data_collector.get_current_bitcoin_price()
            if current_price is None:
                logging.error("현재 가격을 조회할 수 없습니다.")
                return {}
            
            # 전일 데이터
            prev_data = ohlc_data[-2]
            prev_high = prev_data.high
            prev_low = prev_data.low
            
            # 돌파선 계산
            breakout_level = self.calculate_breakout_level(prev_high, prev_low)
            
            logging.info(f"현재 가격: {current_price:,.0f}원")
            logging.info(f"전일 고가: {prev_high:,.0f}원, 전일 저가: {prev_low:,.0f}원")
            logging.info(f"돌파선: {breakout_level:,.0f}원")
            
            # 매수 신호 확인
            if self.check_buy_signal(current_price, prev_high, prev_low):
                if self.execute_buy(current_price, breakout_level):
                    logging.info("매수 신호 실행 완료")
                else:
                    logging.error("매수 신호 실행 실패")
            
            # 기존 포지션이 있는 경우 매도 신호 확인
            if self.position is not None:
                should_sell, reason = self.check_sell_signal(current_price, self.position)
                if should_sell:
                    if self.execute_sell(current_price, reason):
                        logging.info(f"매도 신호 실행 완료: {reason}")
                    else:
                        logging.error("매도 신호 실행 실패")
            
            # 전략 실행 결과 반환
            result = {
                'current_price': current_price,
                'breakout_level': breakout_level,
                'has_position': self.position is not None,
                'current_capital': self.current_capital,
                'total_trades': len(self.trade_history),
                'signals_generated': len(self.signals)
            }
            
            if self.position:
                result['position_info'] = self.position.to_dict()
            
            return result
            
        except Exception as e:
            logging.error(f"전략 실행 오류: {e}")
            return {}
    
    def run_backtest(self, days: int = 90) -> Dict[str, Any]:
        """백테스팅 실행"""
        logging.info(f"백테스팅 시작 (기간: {days}일)")
        
        try:
            # 데이터 수집
            ohlc_data = self.data_collector.get_bitcoin_ohlc_data(days)
            if len(ohlc_data) < 2:
                logging.error("백테스팅을 위한 충분한 데이터가 없습니다.")
                return {}
            
            # 백테스팅용 변수 초기화
            test_capital = self.initial_capital
            test_position = None
            test_trades = []
            test_signals = []
            
            # 일별 전략 실행
            for i in range(1, len(ohlc_data)):
                current_data = ohlc_data[i]
                prev_data = ohlc_data[i-1]
                
                current_price = current_data.close
                prev_high = prev_data.high
                prev_low = prev_data.low
                
                # 돌파선 계산
                breakout_level = self.calculate_breakout_level(prev_high, prev_low)
                
                # 매수 신호 확인
                if test_position is None and self.check_buy_signal(current_price, prev_high, prev_low):
                    # 매수 실행
                    quantity = (test_capital * self.max_position_size) / current_price
                    position_size = quantity * current_price
                    
                    test_position = {
                        'entry_time': current_data.date,
                        'entry_price': current_price,
                        'quantity': quantity,
                        'position_size': position_size,
                        'stop_loss': current_price * (1 - self.stop_loss_percent),
                        'take_profit': current_price * (1 + self.take_profit_percent),
                        'time_stop': current_data.date + timedelta(hours=self.time_stop_hours)
                    }
                    
                    test_capital -= position_size
                    
                    # 신호 기록
                    test_signals.append({
                        'date': current_data.date,
                        'type': 'BUY',
                        'price': current_price,
                        'reason': '돌파선 돌파'
                    })
                
                # 기존 포지션이 있는 경우 매도 신호 확인
                if test_position is not None:
                    should_sell = False
                    sell_reason = ""
                    
                    # 손절 확인
                    if current_price <= test_position['stop_loss']:
                        should_sell = True
                        sell_reason = "손절"
                    # 익절 확인
                    elif current_price >= test_position['take_profit']:
                        should_sell = True
                        sell_reason = "익절"
                    # 시간 손절 확인
                    elif current_data.date >= test_position['time_stop']:
                        should_sell = True
                        sell_reason = "시간 손절"
                    
                    if should_sell:
                        # 매도 실행
                        sell_amount = test_position['quantity'] * current_price
                        test_capital += sell_amount
                        
                        # 수익/손실 계산
                        pnl = (current_price - test_position['entry_price']) * test_position['quantity']
                        pnl_percent = (pnl / test_position['position_size']) * 100
                        
                        # 거래 기록
                        trade_record = {
                            'entry_time': test_position['entry_time'],
                            'exit_time': current_data.date,
                            'entry_price': test_position['entry_price'],
                            'exit_price': current_price,
                            'quantity': test_position['quantity'],
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'reason': sell_reason
                        }
                        test_trades.append(trade_record)
                        
                        # 신호 기록
                        test_signals.append({
                            'date': current_data.date,
                            'type': 'SELL',
                            'price': current_price,
                            'reason': sell_reason
                        })
                        
                        # 포지션 초기화
                        test_position = None
            
            # 백테스팅 결과 분석
            total_return = ((test_capital - self.initial_capital) / self.initial_capital) * 100
            win_trades = len([t for t in test_trades if t['pnl'] > 0])
            loss_trades = len([t for t in test_trades if t['pnl'] < 0])
            win_rate = (win_trades / len(test_trades)) * 100 if test_trades else 0
            
            avg_win = np.mean([t['pnl'] for t in test_trades if t['pnl'] > 0]) if win_trades > 0 else 0
            avg_loss = np.mean([t['pnl'] for t in test_trades if t['pnl'] < 0]) if loss_trades > 0 else 0
            
            max_drawdown = self.calculate_max_drawdown(test_trades)
            
            backtest_result = {
                'initial_capital': self.initial_capital,
                'final_capital': test_capital,
                'total_return': total_return,
                'total_trades': len(test_trades),
                'win_trades': win_trades,
                'loss_trades': loss_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_drawdown': max_drawdown,
                'trades': test_trades,
                'signals': test_signals
            }
            
            logging.info(f"백테스팅 완료: 총 수익률 {total_return:+.2f}%, 승률 {win_rate:.1f}%")
            return backtest_result
            
        except Exception as e:
            logging.error(f"백테스팅 오류: {e}")
            return {}
    
    def calculate_max_drawdown(self, trades: List[Dict[str, Any]]) -> float:
        """최대 낙폭 계산"""
        if not trades:
            return 0.0
        
        peak = self.initial_capital
        max_dd = 0.0
        
        for trade in trades:
            current_capital = self.initial_capital + trade['pnl']
            if current_capital > peak:
                peak = current_capital
            
            drawdown = (peak - current_capital) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100  # 퍼센트로 반환
    
    def plot_backtest_results(self, backtest_result: Dict[str, Any]):
        """백테스팅 결과 시각화"""
        if not backtest_result or 'trades' not in backtest_result:
            logging.warning("백테스팅 결과가 없어서 차트를 생성할 수 없습니다.")
            return
        
        try:
            # 차트 생성
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            # 거래 기록
            trades = backtest_result['trades']
            if trades:
                # 자본 곡선
                dates = [trade['exit_time'] for trade in trades]
                capitals = [self.initial_capital + sum(t['pnl'] for t in trades[:i+1]) for i in range(len(trades))]
                
                ax1.plot(dates, capitals, linewidth=2, color='blue', label='자본 곡선')
                ax1.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.7, label='초기 자본')
                ax1.set_title('백테스팅 결과 - 자본 곡선', fontsize=14, fontweight='bold')
                ax1.set_ylabel('자본 (원)', fontsize=12)
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # 수익률 분포
                returns = [trade['pnl_percent'] for trade in trades]
                ax2.hist(returns, bins=20, alpha=0.7, color='green', edgecolor='black')
                ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='손익 분기점')
                ax2.set_title('거래별 수익률 분포', fontsize=14, fontweight='bold')
                ax2.set_xlabel('수익률 (%)', fontsize=12)
                ax2.set_ylabel('거래 횟수', fontsize=12)
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
            logging.info("백테스팅 결과 차트 생성 완료")
            
        except Exception as e:
            logging.error(f"차트 생성 오류: {e}")
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """전략 요약 정보"""
        summary = {
            'strategy_name': '변동성 돌파 전략',
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_return': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'has_position': self.position is not None,
            'total_trades': len(self.trade_history),
            'total_signals': len(self.signals),
            'parameters': {
                'breakout_multiplier': self.breakout_multiplier,
                'stop_loss_percent': self.stop_loss_percent * 100,
                'take_profit_percent': self.take_profit_percent * 100,
                'max_position_size': self.max_position_size * 100,
                'time_stop_hours': self.time_stop_hours
            }
        }
        
        if self.position:
            summary['current_position'] = self.position.to_dict()
        
        return summary

def main():
    """메인 함수"""
    print("🚀 변동성 돌파 전략 시스템")
    print("=" * 80)
    
    try:
        # 전략 초기화
        strategy = VolatilityBreakoutStrategy(initial_capital=10000000)  # 1천만원
        
        while True:
            print("\n📋 메뉴 선택:")
            print("1. 실시간 전략 실행")
            print("2. 백테스팅 실행")
            print("3. 전략 요약 정보")
            print("4. 백테스팅 결과 차트")
            print("5. 종료")
            
            choice = input("\n선택 (1-5): ").strip()
            
            if choice == "1":
                print("\n🔄 실시간 전략 실행 중...")
                result = strategy.run_strategy(days=30)
                if result:
                    print(f"✅ 전략 실행 완료")
                    print(f"  • 현재 가격: {result['current_price']:,.0f}원")
                    print(f"  • 돌파선: {result['breakout_level']:,.0f}원")
                    print(f"  • 포지션 보유: {'예' if result['has_position'] else '아니오'}")
                    print(f"  • 현재 자본: {result['current_capital']:,.0f}원")
                else:
                    print("❌ 전략 실행 실패")
            
            elif choice == "2":
                print("\n🔄 백테스팅 실행 중...")
                backtest_result = strategy.run_backtest(days=90)
                if backtest_result:
                    print(f"✅ 백테스팅 완료")
                    print(f"  • 초기 자본: {backtest_result['initial_capital']:,.0f}원")
                    print(f"  • 최종 자본: {backtest_result['final_capital']:,.0f}원")
                    print(f"  • 총 수익률: {backtest_result['total_return']:+.2f}%")
                    print(f"  • 총 거래: {backtest_result['total_trades']}회")
                    print(f"  • 승률: {backtest_result['win_rate']:.1f}%")
                    print(f"  • 최대 낙폭: {backtest_result['max_drawdown']:.2f}%")
                else:
                    print("❌ 백테스팅 실패")
            
            elif choice == "3":
                print("\n📊 전략 요약 정보:")
                summary = strategy.get_strategy_summary()
                print(f"  • 전략명: {summary['strategy_name']}")
                print(f"  • 초기 자본: {summary['initial_capital']:,.0f}원")
                print(f"  • 현재 자본: {summary['current_capital']:,.0f}원")
                print(f"  • 총 수익률: {summary['total_return']:+.2f}%")
                print(f"  • 총 거래: {summary['total_trades']}회")
                print(f"  • 총 신호: {summary['total_signals']}개")
                print(f"  • 포지션 보유: {'예' if summary['has_position'] else '아니오'}")
            
            elif choice == "4":
                print("\n📈 백테스팅 결과 차트 생성 중...")
                backtest_result = strategy.run_backtest(days=90)
                if backtest_result:
                    strategy.plot_backtest_results(backtest_result)
                else:
                    print("❌ 백테스팅 결과가 없어서 차트를 생성할 수 없습니다.")
            
            elif choice == "5":
                print("\n⏹️ 시스템을 종료합니다...")
                break
            
            else:
                print("❌ 잘못된 선택입니다. 1-5 중에서 선택하세요.")
                
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류가 발생했습니다: {e}")
    finally:
        print("\n👋 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
