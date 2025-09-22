#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 (Volatility Breakout Strategy)

전략 설명:
1. 일일 고가, 저가, 시가, 종가 데이터 수집
2. 돌파선 계산: 전일 고가 + (전일 고가 - 전일 저가) * 0.5
3. 매수 조건: 현재가가 돌파선을 위로 넘기면
4. 매도 조건: 손절(-2%), 익절(+3%), 시간 손절(24시간)
5. 포지션 크기: 자본의 5%로 제한
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json

class VolatilityBreakoutStrategy:
    """변동성 돌파 전략 클래스"""
    
    def __init__(self, initial_capital: float = 10000000, position_size_ratio: float = 0.05):
        """
        변동성 돌파 전략 초기화
        
        Args:
            initial_capital: 초기 자본 (기본값: 10,000,000원)
            position_size_ratio: 포지션 크기 비율 (기본값: 0.05 = 5%)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_ratio = position_size_ratio
        
        # 거래 설정
        self.stop_loss_ratio = 0.02  # 2% 손절
        self.take_profit_ratio = 0.03  # 3% 익절
        self.time_stop_hours = 24  # 24시간 시간 손절
        
        # 포지션 관리
        self.position = None  # 현재 포지션 정보
        self.trades = []  # 거래 내역
        self.daily_data = []  # 일일 데이터
        
        # 로깅 설정
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('volatility_breakout.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_ohlc_data(self, symbol: str = "KRW-BTC", days: int = 30) -> pd.DataFrame:
        """
        CoinGecko API를 사용하여 OHLC 데이터 수집
        
        Args:
            symbol: 거래 심볼 (기본값: "KRW-BTC")
            days: 수집할 일수 (기본값: 30일)
            
        Returns:
            OHLC 데이터가 포함된 DataFrame
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "krw",
                "days": days,
                "interval": "daily"
            }
            
            self.logger.info(f"OHLC 데이터 수집 중... (심볼: {symbol}, 일수: {days})")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # OHLC 데이터 생성
            ohlc_data = []
            for i, (timestamp, price) in enumerate(data['prices']):
                date = datetime.fromtimestamp(timestamp / 1000)
                
                # 간단한 OHLC 시뮬레이션 (실제로는 더 정교한 데이터가 필요)
                high = price * (1 + np.random.uniform(0, 0.05))  # 고가
                low = price * (1 - np.random.uniform(0, 0.05))   # 저가
                open_price = price * (1 + np.random.uniform(-0.02, 0.02))  # 시가
                close = price  # 종가
                
                ohlc_data.append({
                    'date': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': np.random.uniform(1000, 5000)  # 거래량
                })
            
            df = pd.DataFrame(ohlc_data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            self.logger.info(f"OHLC 데이터 수집 완료: {len(df)}개 데이터")
            return df
            
        except Exception as e:
            self.logger.error(f"OHLC 데이터 수집 오류: {e}")
            return pd.DataFrame()
    
    def calculate_breakout_line(self, high: float, low: float) -> float:
        """
        돌파선 계산
        
        Args:
            high: 전일 고가
            low: 전일 저가
            
        Returns:
            돌파선 가격
        """
        return high + (high - low) * 0.5
    
    def check_buy_signal(self, current_price: float, breakout_line: float) -> bool:
        """
        매수 신호 확인
        
        Args:
            current_price: 현재 가격
            breakout_line: 돌파선 가격
            
        Returns:
            매수 신호 여부
        """
        return current_price > breakout_line
    
    def check_sell_signal(self, entry_price: float, current_price: float, 
                         entry_time: datetime) -> Tuple[bool, str]:
        """
        매도 신호 확인
        
        Args:
            entry_price: 진입 가격
            current_price: 현재 가격
            entry_time: 진입 시간
            
        Returns:
            (매도 신호 여부, 매도 사유)
        """
        # 손절 확인
        if current_price <= entry_price * (1 - self.stop_loss_ratio):
            return True, "손절"
        
        # 익절 확인
        if current_price >= entry_price * (1 + self.take_profit_ratio):
            return True, "익절"
        
        # 시간 손절 확인
        if datetime.now() - entry_time >= timedelta(hours=self.time_stop_hours):
            return True, "시간 손절"
        
        return False, ""
    
    def calculate_position_size(self, price: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            price: 진입 가격
            
        Returns:
            매수할 수량
        """
        position_value = self.current_capital * self.position_size_ratio
        return position_value / price
    
    def enter_position(self, price: float, quantity: float, reason: str = "돌파 매수"):
        """
        포지션 진입
        
        Args:
            price: 진입 가격
            quantity: 수량
            reason: 진입 사유
        """
        self.position = {
            'entry_price': price,
            'quantity': quantity,
            'entry_time': datetime.now(),
            'entry_reason': reason
        }
        
        self.logger.info(f"포지션 진입: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
    
    def exit_position(self, price: float, reason: str):
        """
        포지션 청산
        
        Args:
            price: 청산 가격
            reason: 청산 사유
        """
        if not self.position:
            return
        
        entry_price = self.position['entry_price']
        quantity = self.position['quantity']
        
        # 수익/손실 계산
        pnl = (price - entry_price) * quantity
        pnl_ratio = (price / entry_price - 1) * 100
        
        # 자본 업데이트
        self.current_capital += pnl
        
        # 거래 기록
        trade = {
            'entry_time': self.position['entry_time'],
            'exit_time': datetime.now(),
            'entry_price': entry_price,
            'exit_price': price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_ratio': pnl_ratio,
            'reason': reason
        }
        self.trades.append(trade)
        
        self.logger.info(f"포지션 청산: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
        self.logger.info(f"수익/손실: {pnl:,.0f}원 ({pnl_ratio:+.2f}%)")
        
        # 포지션 초기화
        self.position = None
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """
        백테스팅 실행
        
        Args:
            data: OHLC 데이터
            
        Returns:
            백테스팅 결과
        """
        self.logger.info("백테스팅 시작...")
        
        for i in range(1, len(data)):
            current_data = data.iloc[i]
            previous_data = data.iloc[i-1]
            
            # 돌파선 계산
            breakout_line = self.calculate_breakout_line(
                previous_data['high'], 
                previous_data['low']
            )
            
            current_price = current_data['close']
            
            # 포지션이 없는 경우
            if not self.position:
                # 매수 신호 확인
                if self.check_buy_signal(current_price, breakout_line):
                    quantity = self.calculate_position_size(current_price)
                    self.enter_position(current_price, quantity)
            
            # 포지션이 있는 경우
            else:
                # 매도 신호 확인
                should_sell, sell_reason = self.check_sell_signal(
                    self.position['entry_price'],
                    current_price,
                    self.position['entry_time']
                )
                
                if should_sell:
                    self.exit_position(current_price, sell_reason)
        
        # 마지막 포지션 청산
        if self.position:
            last_price = data.iloc[-1]['close']
            self.exit_position(last_price, "백테스팅 종료")
        
        # 결과 분석
        return self.analyze_results()
    
    def analyze_results(self) -> Dict:
        """
        백테스팅 결과 분석
        
        Returns:
            분석 결과 딕셔너리
        """
        if not self.trades:
            return {"error": "거래 내역이 없습니다."}
        
        # 기본 통계
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if t['pnl'] < 0])
        
        # 수익률 계산
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_return = (total_pnl / self.initial_capital) * 100
        
        # 승률 계산
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # 평균 수익/손실
        avg_win = np.mean([t['pnl'] for t in self.trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in self.trades if t['pnl'] < 0]) if losing_trades > 0 else 0
        
        # 최대 손실
        max_loss = min(t['pnl'] for t in self.trades)
        
        # 샤프 비율 (간단한 계산)
        returns = [t['pnl_ratio'] for t in self.trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_loss': max_loss,
            'sharpe_ratio': sharpe_ratio,
            'trades': self.trades
        }
        
        return results
    
    def print_results(self, results: Dict):
        """
        결과 출력
        
        Args:
            results: 분석 결과
        """
        if "error" in results:
            print(f"오류: {results['error']}")
            return
        
        print("\n" + "="*60)
        print("변동성 돌파 전략 백테스팅 결과")
        print("="*60)
        
        print(f"초기 자본: {results['initial_capital']:,.0f}원")
        print(f"최종 자본: {results['final_capital']:,.0f}원")
        print(f"총 수익/손실: {results['total_pnl']:,.0f}원")
        print(f"총 수익률: {results['total_return']:+.2f}%")
        
        print(f"\n거래 통계:")
        print(f"총 거래 횟수: {results['total_trades']}회")
        print(f"승리 거래: {results['winning_trades']}회")
        print(f"패배 거래: {results['losing_trades']}회")
        print(f"승률: {results['win_rate']:.2f}%")
        
        print(f"\n수익 분석:")
        print(f"평균 승리: {results['avg_win']:,.0f}원")
        print(f"평균 손실: {results['avg_loss']:,.0f}원")
        print(f"최대 손실: {results['max_loss']:,.0f}원")
        print(f"샤프 비율: {results['sharpe_ratio']:.2f}")
        
        print("\n거래 내역:")
        print("-" * 60)
        for i, trade in enumerate(results['trades'], 1):
            print(f"{i:2d}. {trade['entry_time'].strftime('%m/%d %H:%M')} - "
                  f"{trade['exit_time'].strftime('%m/%d %H:%M')} | "
                  f"{trade['entry_price']:,.0f} → {trade['exit_price']:,.0f} | "
                  f"{trade['pnl']:+,.0f}원 ({trade['pnl_ratio']:+.2f}%) | "
                  f"{trade['reason']}")
        
        print("="*60)

def main():
    """메인 함수"""
    print("변동성 돌파 전략 백테스팅")
    print("-" * 40)
    
    # 전략 초기화
    strategy = VolatilityBreakoutStrategy(
        initial_capital=10000000,  # 1천만원
        position_size_ratio=0.05   # 5%
    )
    
    # 데이터 수집
    print("데이터 수집 중...")
    data = strategy.get_ohlc_data(symbol="KRW-BTC", days=30)
    
    if data.empty:
        print("데이터 수집에 실패했습니다.")
        return
    
    # 백테스팅 실행
    print("백테스팅 실행 중...")
    results = strategy.run_backtest(data)
    
    # 결과 출력
    strategy.print_results(results)
    
    # 결과를 JSON 파일로 저장
    with open('backtest_results.json', 'w', encoding='utf-8') as f:
        # datetime 객체를 문자열로 변환
        json_results = results.copy()
        for trade in json_results['trades']:
            trade['entry_time'] = trade['entry_time'].isoformat()
            trade['exit_time'] = trade['exit_time'].isoformat()
        
        json.dump(json_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과가 'backtest_results.json' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()