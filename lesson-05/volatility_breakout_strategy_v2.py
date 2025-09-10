#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 구현
5차시 두 번째 프롬프트 구현 코드
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import time
import logging

# 한글 폰트 설정 (Windows)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('volatility_breakout_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class VolatilityBreakoutStrategy:
    """
    변동성 돌파 전략 클래스 (개선된 파라미터)
    
    전략 설명:
    - 일일 고가, 저가, 시가, 종가 데이터 사용
    - 돌파선 = 전일 고가 + (전일 고가 - 전일 저가) × 0.7
    - 매수: 현재가가 돌파선을 위로 넘을 때
    - 매도: 손절(-1.5%), 익절(+2.5%), 시간 손절(2일)
    - 포지션 크기: 자본의 5%로 제한
    """
    
    def __init__(self, initial_capital=1000000, position_size_ratio=0.05):
        """
        전략 초기화
        
        Args:
            initial_capital (float): 초기 자본금
            position_size_ratio (float): 포지션 크기 비율 (기본 5%)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_ratio = position_size_ratio
        self.position = None  # 현재 포지션 정보
        self.trades = []  # 거래 기록
        self.entry_time = None  # 진입 시간
        
        logging.info(f"변동성 돌파 전략 초기화 완료 - 초기 자본: {initial_capital:,}원")
    
    def calculate_breakout_line(self, prev_high, prev_low):
        """
        돌파선 계산 (K값 0.7 적용)
        
        Args:
            prev_high (float): 전일 고가
            prev_low (float): 전일 저가
            
        Returns:
            float: 돌파선 가격
        """
        volatility = prev_high - prev_low
        breakout_line = prev_high + (volatility * 0.7)  # K값 0.5 → 0.7로 변경
        return breakout_line
    
    def should_buy(self, current_price, prev_high, prev_low):
        """
        매수 조건 확인
        
        Args:
            current_price (float): 현재가
            prev_high (float): 전일 고가
            prev_low (float): 전일 저가
            
        Returns:
            bool: 매수 여부
        """
        if self.position is not None:
            return False  # 이미 포지션이 있으면 매수하지 않음
        
        breakout_line = self.calculate_breakout_line(prev_high, prev_low)
        
        if current_price > breakout_line:
            logging.info(f"매수 신호 발생! 현재가: {current_price:,.0f}원, 돌파선: {breakout_line:,.0f}원")
            return True
        
        return False
    
    def should_sell(self, current_price, entry_price, entry_time, current_timestamp):
        """
        매도 조건 확인
        
        Args:
            current_price (float): 현재가
            entry_price (float): 진입가
            entry_time (datetime): 진입 시간
            current_timestamp (datetime): 현재 시간
            
        Returns:
            tuple: (매도 여부, 매도 사유)
        """
        if self.position is None:
            return False, None
        
        # 수익률 계산
        profit_rate = (current_price - entry_price) / entry_price
        
        # 익절 조건 (+2.5%)
        if profit_rate >= 0.025:
            logging.info(f"익절 신호 발생! 수익률: {profit_rate*100:.2f}%")
            return True, "익절"
        
        # 손절 조건 (-1.5%)
        if profit_rate <= -0.015:
            logging.info(f"손절 신호 발생! 수익률: {profit_rate*100:.2f}%")
            return True, "손절"
        
        # 시간 손절 조건 - 데이터 타입에 따라 다르게 적용
        holding_time = current_timestamp - entry_time
        
        # 일별 데이터인 경우 2일 이상, 시간별 데이터인 경우 24시간 이상
        if holding_time >= timedelta(days=2):
            logging.info(f"시간 손절 신호 발생! 보유 시간: {holding_time}")
            return True, "시간 손절"
        
        return False, None
    
    def execute_buy(self, price, timestamp):
        """
        매수 실행
        
        Args:
            price (float): 매수가격
            timestamp (datetime): 거래 시간
        """
        position_value = self.current_capital * self.position_size_ratio
        quantity = position_value / price
        
        self.position = {
            'entry_price': price,
            'quantity': quantity,
            'entry_time': timestamp,
            'position_value': position_value
        }
        
        self.entry_time = timestamp
        
        logging.info(f"매수 실행 - 가격: {price:,.0f}원, 수량: {quantity:.6f}, 포지션 가치: {position_value:,.0f}원")
    
    def execute_sell(self, price, timestamp, reason):
        """
        매도 실행
        
        Args:
            price (float): 매도가격
            timestamp (datetime): 거래 시간
            reason (str): 매도 사유
        """
        if self.position is None:
            return
        
        entry_price = self.position['entry_price']
        quantity = self.position['quantity']
        entry_time = self.position['entry_time']
        
        # 수익률 계산
        profit_rate = (price - entry_price) / entry_price
        profit_amount = (price - entry_price) * quantity
        
        # 거래 기록 저장
        trade = {
            'entry_time': entry_time,
            'exit_time': timestamp,
            'entry_price': entry_price,
            'exit_price': price,
            'quantity': quantity,
            'profit_rate': profit_rate,
            'profit_amount': profit_amount,
            'reason': reason,
            'holding_time': timestamp - entry_time
        }
        
        self.trades.append(trade)
        
        # 자본 업데이트
        self.current_capital += profit_amount
        
        # 포지션 초기화
        self.position = None
        self.entry_time = None
        
        logging.info(f"매도 실행 - 가격: {price:,.0f}원, 수익률: {profit_rate*100:.2f}%, 수익금: {profit_amount:,.0f}원, 사유: {reason}")
    
    def get_crypto_data(self, symbol='bitcoin', days=30, use_hourly=False):
        """
        암호화폐 데이터 가져오기 (무료 API 사용)
        
        Args:
            symbol (str): 암호화폐 심볼
            days (int): 가져올 일수
            use_hourly (bool): 시간별 데이터 사용 여부 (현재는 일별만 지원)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            # 무료 API 사용 (CoinGecko Simple Price API)
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'krw',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'bitcoin' not in data:
                logging.error("비트코인 데이터를 찾을 수 없습니다.")
                return None
            
            # 현재 가격 가져오기
            current_price = data['bitcoin']['krw']
            
            # 시뮬레이션 데이터 생성 (현실적인 가격 움직임)
            logging.info("시뮬레이션 데이터를 생성합니다...")
            
            # 날짜 범위 생성
            if use_hourly:
                # 시간별 데이터 (7일)
                date_range = pd.date_range(
                    end=pd.Timestamp.now(), 
                    periods=days*24, 
                    freq='H'
                )
            else:
                # 일별 데이터
                date_range = pd.date_range(
                    end=pd.Timestamp.now(), 
                    periods=days, 
                    freq='D'
                )
            
            # 가격 시뮬레이션 (현실적인 랜덤 워크)
            np.random.seed(42)  # 재현 가능한 결과를 위해 시드 설정
            
            # 초기 가격 (현재 가격의 80-120% 범위)
            initial_price = current_price * np.random.uniform(0.8, 1.2)
            prices = [initial_price]
            
            # 랜덤 워크로 가격 생성
            for i in range(1, len(date_range)):
                # 일일 변동률 (-5% ~ +5%)
                daily_return = np.random.normal(0, 0.02)  # 평균 0, 표준편차 2%
                new_price = prices[-1] * (1 + daily_return)
                prices.append(max(new_price, 1000))  # 최소 1000원
            
            # DataFrame 생성
            df = pd.DataFrame({
                'timestamp': date_range,
                'close': prices
            })
            
            # OHLC 데이터 생성
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
            
            # 거래량 생성 (가격 변동과 연관)
            df['volume'] = np.random.uniform(1000000, 5000000, len(df))
            
            df = df.dropna()
            df = df.reset_index(drop=True)
            
            data_type = "시간별" if use_hourly else "일별"
            logging.info(f"{symbol} {data_type} 시뮬레이션 데이터 {len(df)}개 생성 완료")
            logging.info(f"데이터 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
            logging.info(f"가격 범위: {df['close'].min():,.0f}원 ~ {df['close'].max():,.0f}원")
            return df
            
        except Exception as e:
            logging.error(f"데이터 수집 오류: {e}")
            return None
    
    def backtest(self, data):
        """
        백테스트 실행 - 실제 거래 로직 시뮬레이션
        
        매일 돌파선을 체크하고, 돌파 시 매수 후 24시간 내에 익절/손절/시간손절
        
        Args:
            data (pd.DataFrame): OHLCV 데이터
        """
        logging.info("백테스트 시작 - 일별 돌파선 체크 방식")
        
        for i in range(1, len(data)):
            current_row = data.iloc[i]
            prev_row = data.iloc[i-1]
            
            current_price = current_row['close']
            prev_high = prev_row['high']
            prev_low = prev_row['low']
            current_timestamp = current_row['timestamp']
            
            logging.info(f"Day {i}: {current_timestamp.strftime('%Y-%m-%d')} - 현재가: {current_price:,.0f}원")
            
            # 매도 조건 확인 (포지션이 있는 경우)
            if self.position is not None:
                should_sell, sell_reason = self.should_sell(
                    current_price, 
                    self.position['entry_price'], 
                    self.position['entry_time'],
                    current_timestamp  # 현재 시간 추가
                )
                
                if should_sell:
                    self.execute_sell(current_price, current_timestamp, sell_reason)
                    logging.info(f"매도 완료 - 사유: {sell_reason}")
            
            # 매수 조건 확인 (포지션이 없는 경우)
            if self.position is None:
                breakout_line = self.calculate_breakout_line(prev_high, prev_low)
                logging.info(f"돌파선: {breakout_line:,.0f}원 (전일 고가: {prev_high:,.0f}, 저가: {prev_low:,.0f})")
                
                if self.should_buy(current_price, prev_high, prev_low):
                    self.execute_buy(current_price, current_timestamp)
                    logging.info(f"매수 완료 - 진입가: {current_price:,.0f}원")
        
        # 마지막에 포지션이 있다면 강제 매도
        if self.position is not None:
            last_price = data.iloc[-1]['close']
            last_time = data.iloc[-1]['timestamp']
            self.execute_sell(last_price, last_time, "백테스트 종료")
            logging.info("백테스트 종료로 인한 강제 매도")
        
        logging.info(f"백테스트 완료 - 총 거래 횟수: {len(self.trades)}회")
    
    def calculate_performance(self):
        """
        성과 분석
        
        Returns:
            dict: 성과 지표
        """
        if not self.trades:
            return {"메시지": "거래 기록이 없습니다."}
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['profit_rate'] > 0])
        losing_trades = len([t for t in self.trades if t['profit_rate'] < 0])
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_profit = sum([t['profit_amount'] for t in self.trades])
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        avg_profit = np.mean([t['profit_rate'] for t in self.trades]) * 100
        avg_winning = np.mean([t['profit_rate'] for t in self.trades if t['profit_rate'] > 0]) * 100
        avg_losing = np.mean([t['profit_rate'] for t in self.trades if t['profit_rate'] < 0]) * 100
        
        performance = {
            "초기 자본": f"{self.initial_capital:,.0f}원",
            "최종 자본": f"{self.current_capital:,.0f}원",
            "총 수익금": f"{total_profit:,.0f}원",
            "총 수익률": f"{total_return:.2f}%",
            "총 거래 횟수": total_trades,
            "승률": f"{win_rate:.2f}%",
            "평균 수익률": f"{avg_profit:.2f}%",
            "평균 승리 수익률": f"{avg_winning:.2f}%",
            "평균 손실 수익률": f"{avg_losing:.2f}%"
        }
        
        return performance
    
    def plot_results(self, data):
        """
        결과 시각화
        
        Args:
            data (pd.DataFrame): OHLCV 데이터
        """
        plt.figure(figsize=(18, 12))
        
        # 가격 차트
        plt.subplot(2, 1, 1)
        plt.plot(data['timestamp'], data['close'], label='종가', linewidth=2, color='#1f77b4')
        plt.plot(data['timestamp'], data['high'], label='고가', alpha=0.6, linewidth=1, color='#ff7f0e')
        plt.plot(data['timestamp'], data['low'], label='저가', alpha=0.6, linewidth=1, color='#2ca02c')
        
        # 거래 포인트 표시
        for i, trade in enumerate(self.trades):
            # 매수 포인트 (초록색)
            plt.axvline(x=trade['entry_time'], color='green', alpha=0.7, linestyle='--', linewidth=2)
            plt.text(trade['entry_time'], plt.ylim()[1] * 0.95, f'매수{i+1}', 
                    rotation=90, fontsize=8, color='green', fontweight='bold')
            
            # 매도 포인트 (빨간색)
            plt.axvline(x=trade['exit_time'], color='red', alpha=0.7, linestyle='--', linewidth=2)
            plt.text(trade['exit_time'], plt.ylim()[1] * 0.85, f'매도{i+1}', 
                    rotation=90, fontsize=8, color='red', fontweight='bold')
        
        # 차트 설명 텍스트 추가
        explanation_text = """
        📊 변동성 돌파 전략 가격 차트
        
        🔵 파란선: 종가 (매일의 마지막 거래 가격)
        🟠 주황선: 고가 (매일의 최고 가격)  
        🟢 초록선: 저가 (매일의 최저 가격)
        
        📈 거래 신호:
        • 초록색 점선: 매수 진입 시점 (돌파선 돌파)
        • 빨간색 점선: 매도 청산 시점 (익절/손절/시간손절)
        
        💡 전략 원리:
        돌파선 = 전일 고가 + (전일 고가 - 전일 저가) × 0.7
        현재가가 돌파선을 넘으면 매수, 2일 내 익절(+2.5%)/손절(-1.5%)/시간손절
        """
        
        plt.text(0.02, 0.98, explanation_text, transform=plt.gca().transAxes, 
                fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='lightblue', alpha=0.8))
        
        plt.title('변동성 돌파 전략 - 가격 차트', fontsize=16, fontweight='bold')
        plt.xlabel('날짜', fontsize=12)
        plt.ylabel('가격 (원)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 수익률 차트
        plt.subplot(2, 1, 2)
        if self.trades:
            trade_numbers = range(1, len(self.trades) + 1)
            returns = [t['profit_rate'] * 100 for t in self.trades]
            
            colors = ['green' if r > 0 else 'red' for r in returns]
            bars = plt.bar(trade_numbers, returns, color=colors, alpha=0.7)
            
            # 각 막대 위에 수익률 표시
            for i, (bar, return_val) in enumerate(zip(bars, returns)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.3),
                        f'{return_val:.1f}%', ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=8, fontweight='bold')
            
            # 수익률 차트 설명 텍스트 추가
            performance_text = f"""
            📊 거래별 수익률 분석
            
            🟢 초록 막대: 수익 거래 (+)
            🔴 빨간 막대: 손실 거래 (-)
            
            📈 성과 요약:
            • 총 거래 횟수: {len(self.trades)}회
            • 수익 거래: {len([r for r in returns if r > 0])}회
            • 손실 거래: {len([r for r in returns if r < 0])}회
            • 평균 수익률: {np.mean(returns):.1f}%
            • 최대 수익률: {max(returns):.1f}%
            • 최대 손실률: {min(returns):.1f}%
            """
            
            plt.text(0.02, 0.98, performance_text, transform=plt.gca().transAxes, 
                    fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', 
                    facecolor='lightgreen', alpha=0.8))
            
            plt.title('거래별 수익률', fontsize=16, fontweight='bold')
            plt.xlabel('거래 번호', fontsize=12)
            plt.ylabel('수익률 (%)', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # 0% 기준선 추가
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        else:
            plt.text(0.5, 0.5, '거래 기록이 없습니다.', ha='center', va='center', 
                    transform=plt.gca().transAxes, fontsize=14, color='gray')
            plt.title('거래별 수익률', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('volatility_breakout_strategy_v2_results.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("변동성 돌파 전략 백테스트")
    print("=" * 60)
    
    # 전략 초기화
    strategy = VolatilityBreakoutStrategy(
        initial_capital=1000000,  # 100만원
        position_size_ratio=0.05  # 5%
    )
    
    # 데이터 수집 (시뮬레이션 데이터 사용)
    print("데이터 수집 중...")
    print("📊 현재 비트코인 가격을 기준으로 시뮬레이션 데이터를 생성합니다...")
    data = strategy.get_crypto_data('bitcoin', days=30, use_hourly=False)  # 30일간 일별 데이터
    
    if data is None:
        print("데이터 수집에 실패했습니다.")
        return
    
    print(f"수집된 데이터: {len(data)}일")
    print(f"기간: {data['timestamp'].min()} ~ {data['timestamp'].max()}")
    
    # 백테스트 실행
    print("\n백테스트 실행 중...")
    print("📊 매일 돌파선을 체크하고, 돌파 시 매수 후 2일 내 익절(+2.5%)/손절(-1.5%)/시간손절하는 로직으로 실행됩니다.")
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
            print(f"  진입: {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} - {trade['entry_price']:,.0f}원")
            print(f"  청산: {trade['exit_time'].strftime('%Y-%m-%d %H:%M')} - {trade['exit_price']:,.0f}원")
            print(f"  수익률: {trade['profit_rate']*100:.2f}%")
            print(f"  수익금: {trade['profit_amount']:,.0f}원")
            print(f"  사유: {trade['reason']}")
            print(f"  보유시간: {trade['holding_time']}")
            print()
    
    # 차트 생성
    print("결과 차트 생성 중...")
    strategy.plot_results(data)
    
    print("백테스트 완료!")

if __name__ == "__main__":
    main()
