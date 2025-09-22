#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이동평균 크로스오버 전략 (Moving Average Crossover Strategy)

전략 설명:
- 단기 이동평균(5일)과 장기 이동평균(20일) 사용
- 단기선이 장기선을 위로 넘을 때 매수
- 단기선이 장기선을 아래로 넘을 때 매도
- 거래량이 평균보다 1.5배 이상일 때만 신호 생성
- 최대 포지션 크기는 자본의 10%로 제한
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json
import sys

class MovingAverageCrossoverStrategy:
    """이동평균 크로스오버 전략 클래스"""
    
    def __init__(self, initial_capital: float = 10000000, position_size_ratio: float = 0.10):
        """
        이동평균 크로스오버 전략 초기화
        
        Args:
            initial_capital: 초기 자본 (기본값: 10,000,000원)
            position_size_ratio: 포지션 크기 비율 (기본값: 0.10 = 10%)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size_ratio = position_size_ratio
        
        # 이동평균 설정
        self.short_period = 5   # 단기 이동평균 (5일)
        self.long_period = 20   # 장기 이동평균 (20일)
        
        # 거래량 필터 설정
        self.volume_multiplier = 1.5  # 거래량 평균의 1.5배
        
        # 포지션 관리
        self.position = None  # 현재 포지션 정보
        self.trades = []  # 거래 내역
        self.daily_data = []  # 일일 데이터
        
        # 로깅 설정
        self.setup_logging()
        
        # 전략 상태
        self.last_signal = None  # 마지막 신호 ('buy', 'sell', None)
        
    def setup_logging(self):
        """로깅 설정"""
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('ma_crossover.log', encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info("로깅 시스템 초기화 완료")
        except Exception as e:
            print(f"로깅 설정 오류: {e}")
            sys.exit(1)
    
    def get_ohlc_data(self, symbol: str = "KRW-BTC", days: int = 60) -> pd.DataFrame:
        """
        CoinGecko API를 사용하여 OHLC 데이터 수집
        
        Args:
            symbol: 거래 심볼 (기본값: "KRW-BTC")
            days: 수집할 일수 (기본값: 60일)
            
        Returns:
            OHLC 데이터가 포함된 DataFrame
        """
        try:
            self.logger.info(f"OHLC 데이터 수집 시작 (심볼: {symbol}, 일수: {days})")
            
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "krw",
                "days": days,
                "interval": "daily"
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'prices' not in data or not data['prices']:
                raise ValueError("가격 데이터가 없습니다.")
            
            # OHLC 데이터 생성
            ohlc_data = []
            for i, (timestamp, price) in enumerate(data['prices']):
                try:
                    date = datetime.fromtimestamp(timestamp / 1000)
                    
                    # 더 현실적인 OHLC 시뮬레이션
                    volatility = np.random.uniform(0.02, 0.08)  # 2-8% 변동성
                    trend = np.random.uniform(-0.01, 0.01)  # -1% ~ +1% 트렌드
                    
                    open_price = price * (1 + trend)
                    high = max(open_price, price) * (1 + volatility * np.random.uniform(0.3, 1.0))
                    low = min(open_price, price) * (1 - volatility * np.random.uniform(0.3, 1.0))
                    close = price
                    
                    # 거래량 생성 (가격 변동과 연관)
                    price_change = abs(close - open_price) / open_price
                    base_volume = 1000
                    volume = base_volume * (1 + price_change * 10) * np.random.uniform(0.5, 2.0)
                    
                    ohlc_data.append({
                        'date': date,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': volume
                    })
                    
                except Exception as e:
                    self.logger.warning(f"데이터 처리 오류 (인덱스 {i}): {e}")
                    continue
            
            if not ohlc_data:
                raise ValueError("유효한 데이터가 없습니다.")
            
            df = pd.DataFrame(ohlc_data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # 데이터 유효성 검사
            if len(df) < self.long_period:
                raise ValueError(f"데이터가 부족합니다. 최소 {self.long_period}일 필요, 현재 {len(df)}일")
            
            self.logger.info(f"OHLC 데이터 수집 완료: {len(df)}개 데이터")
            return df
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 오류: {e}")
            raise
        except Exception as e:
            self.logger.error(f"데이터 수집 오류: {e}")
            raise
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        이동평균 계산
        
        Args:
            data: OHLC 데이터
            
        Returns:
            이동평균이 추가된 DataFrame
        """
        try:
            df = data.copy()
            
            # 단기 이동평균 계산
            df['ma_short'] = df['close'].rolling(window=self.short_period).mean()
            
            # 장기 이동평균 계산
            df['ma_long'] = df['close'].rolling(window=self.long_period).mean()
            
            # 거래량 이동평균 계산
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            # 크로스오버 신호 계산
            df['ma_cross'] = np.where(
                df['ma_short'] > df['ma_long'], 1,  # 단기선이 장기선 위
                np.where(df['ma_short'] < df['ma_long'], -1, 0)  # 단기선이 장기선 아래
            )
            
            # 크로스오버 포인트 찾기
            df['cross_up'] = (df['ma_cross'] == 1) & (df['ma_cross'].shift(1) != 1)
            df['cross_down'] = (df['ma_cross'] == -1) & (df['ma_cross'].shift(1) != -1)
            
            self.logger.info("이동평균 계산 완료")
            return df
            
        except Exception as e:
            self.logger.error(f"이동평균 계산 오류: {e}")
            raise
    
    def check_volume_filter(self, current_volume: float, avg_volume: float) -> bool:
        """
        거래량 필터 확인
        
        Args:
            current_volume: 현재 거래량
            avg_volume: 평균 거래량
            
        Returns:
            거래량 필터 통과 여부
        """
        if avg_volume == 0:
            return False
        
        return current_volume >= avg_volume * self.volume_multiplier
    
    def check_buy_signal(self, data: pd.Series) -> bool:
        """
        매수 신호 확인
        
        Args:
            data: 현재 데이터 (Series)
            
        Returns:
            매수 신호 여부
        """
        try:
            # 이동평균 크로스오버 확인
            if not data['cross_up']:
                return False
            
            # 거래량 필터 확인
            if not self.check_volume_filter(data['volume'], data['volume_ma']):
                self.logger.info(f"거래량 부족으로 매수 신호 무시 (현재: {data['volume']:.0f}, 평균: {data['volume_ma']:.0f})")
                return False
            
            # 이동평균이 유효한지 확인
            if pd.isna(data['ma_short']) or pd.isna(data['ma_long']):
                return False
            
            self.logger.info(f"매수 신호 발생: 단기MA={data['ma_short']:.0f}, 장기MA={data['ma_long']:.0f}")
            return True
            
        except Exception as e:
            self.logger.error(f"매수 신호 확인 오류: {e}")
            return False
    
    def check_sell_signal(self, data: pd.Series) -> bool:
        """
        매도 신호 확인
        
        Args:
            data: 현재 데이터 (Series)
            
        Returns:
            매도 신호 여부
        """
        try:
            # 이동평균 크로스오버 확인
            if not data['cross_down']:
                return False
            
            # 이동평균이 유효한지 확인
            if pd.isna(data['ma_short']) or pd.isna(data['ma_long']):
                return False
            
            self.logger.info(f"매도 신호 발생: 단기MA={data['ma_short']:.0f}, 장기MA={data['ma_long']:.0f}")
            return True
            
        except Exception as e:
            self.logger.error(f"매도 신호 확인 오류: {e}")
            return False
    
    def calculate_position_size(self, price: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            price: 진입 가격
            
        Returns:
            매수할 수량
        """
        try:
            position_value = self.current_capital * self.position_size_ratio
            quantity = position_value / price
            
            # 최소/최대 수량 제한
            min_quantity = 0.001  # 최소 0.001개
            max_quantity = position_value / (price * 0.5)  # 최대 자본의 50%까지
            
            quantity = max(min_quantity, min(quantity, max_quantity))
            
            self.logger.info(f"포지션 크기 계산: {quantity:.6f}개 (가격: {price:,.0f}원)")
            return quantity
            
        except Exception as e:
            self.logger.error(f"포지션 크기 계산 오류: {e}")
            return 0.001
    
    def enter_position(self, price: float, quantity: float, reason: str = "이동평균 크로스오버 매수"):
        """
        포지션 진입
        
        Args:
            price: 진입 가격
            quantity: 수량
            reason: 진입 사유
        """
        try:
            if self.position is not None:
                self.logger.warning("이미 포지션이 있습니다. 진입 무시")
                return
            
            self.position = {
                'entry_price': price,
                'quantity': quantity,
                'entry_time': datetime.now(),
                'entry_reason': reason
            }
            
            self.last_signal = 'buy'
            self.logger.info(f"포지션 진입: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
            
        except Exception as e:
            self.logger.error(f"포지션 진입 오류: {e}")
    
    def exit_position(self, price: float, reason: str):
        """
        포지션 청산
        
        Args:
            price: 청산 가격
            reason: 청산 사유
        """
        try:
            if self.position is None:
                self.logger.warning("포지션이 없습니다. 청산 무시")
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
                'reason': reason,
                'holding_days': (datetime.now() - self.position['entry_time']).days
            }
            self.trades.append(trade)
            
            self.last_signal = 'sell'
            self.logger.info(f"포지션 청산: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
            self.logger.info(f"수익/손실: {pnl:,.0f}원 ({pnl_ratio:+.2f}%)")
            
            # 포지션 초기화
            self.position = None
            
        except Exception as e:
            self.logger.error(f"포지션 청산 오류: {e}")
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """
        백테스팅 실행
        
        Args:
            data: OHLC 데이터
            
        Returns:
            백테스팅 결과
        """
        try:
            self.logger.info("백테스팅 시작...")
            
            # 이동평균 계산
            df = self.calculate_moving_averages(data)
            
            # 백테스팅 실행
            for i in range(self.long_period, len(df)):
                current_data = df.iloc[i]
                
                # 포지션이 없는 경우
                if self.position is None:
                    # 매수 신호 확인
                    if self.check_buy_signal(current_data):
                        quantity = self.calculate_position_size(current_data['close'])
                        if quantity > 0:
                            self.enter_position(current_data['close'], quantity)
                
                # 포지션이 있는 경우
                else:
                    # 매도 신호 확인
                    if self.check_sell_signal(current_data):
                        self.exit_position(current_data['close'], "이동평균 크로스오버 매도")
            
            # 마지막 포지션 청산
            if self.position:
                last_price = df.iloc[-1]['close']
                self.exit_position(last_price, "백테스팅 종료")
            
            self.logger.info("백테스팅 완료")
            
            # 결과 분석
            return self.analyze_results()
            
        except Exception as e:
            self.logger.error(f"백테스팅 실행 오류: {e}")
            return {"error": f"백테스팅 실행 오류: {e}"}
    
    def analyze_results(self) -> Dict:
        """
        백테스팅 결과 분석
        
        Returns:
            분석 결과 딕셔너리
        """
        try:
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
            
            # 평균 보유 기간
            avg_holding_days = np.mean([t['holding_days'] for t in self.trades])
            
            # 샤프 비율 (간단한 계산)
            returns = [t['pnl_ratio'] for t in self.trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
            
            # 최대 연속 손실
            consecutive_losses = 0
            max_consecutive_losses = 0
            for trade in self.trades:
                if trade['pnl'] < 0:
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0
            
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
                'avg_holding_days': avg_holding_days,
                'max_consecutive_losses': max_consecutive_losses,
                'sharpe_ratio': sharpe_ratio,
                'trades': self.trades
            }
            
            self.logger.info("결과 분석 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"결과 분석 오류: {e}")
            return {"error": f"결과 분석 오류: {e}"}
    
    def print_results(self, results: Dict):
        """
        결과 출력
        
        Args:
            results: 분석 결과
        """
        try:
            if "error" in results:
                print(f"오류: {results['error']}")
                return
            
            print("\n" + "="*70)
            print("이동평균 크로스오버 전략 백테스팅 결과")
            print("="*70)
            
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
            print(f"평균 보유 기간: {results['avg_holding_days']:.1f}일")
            print(f"최대 연속 손실: {results['max_consecutive_losses']}회")
            print(f"샤프 비율: {results['sharpe_ratio']:.2f}")
            
            print(f"\n거래 내역:")
            print("-" * 70)
            for i, trade in enumerate(results['trades'], 1):
                print(f"{i:2d}. {trade['entry_time'].strftime('%m/%d %H:%M')} - "
                      f"{trade['exit_time'].strftime('%m/%d %H:%M')} | "
                      f"{trade['entry_price']:,.0f} → {trade['exit_price']:,.0f} | "
                      f"{trade['pnl']:+,.0f}원 ({trade['pnl_ratio']:+.2f}%) | "
                      f"{trade['holding_days']}일 | {trade['reason']}")
            
            print("="*70)
            
        except Exception as e:
            self.logger.error(f"결과 출력 오류: {e}")
            print(f"결과 출력 오류: {e}")

def main():
    """메인 함수"""
    try:
        print("이동평균 크로스오버 전략 백테스팅")
        print("-" * 50)
        
        # 전략 초기화
        strategy = MovingAverageCrossoverStrategy(
            initial_capital=10000000,  # 1천만원
            position_size_ratio=0.10   # 10%
        )
        
        # 데이터 수집
        print("데이터 수집 중...")
        data = strategy.get_ohlc_data(symbol="KRW-BTC", days=60)
        
        if data.empty:
            print("데이터 수집에 실패했습니다.")
            return
        
        # 백테스팅 실행
        print("백테스팅 실행 중...")
        results = strategy.run_backtest(data)
        
        # 결과 출력
        strategy.print_results(results)
        
        # 결과를 JSON 파일로 저장
        try:
            with open('ma_crossover_results.json', 'w', encoding='utf-8') as f:
                # datetime 객체를 문자열로 변환
                json_results = results.copy()
                for trade in json_results['trades']:
                    trade['entry_time'] = trade['entry_time'].isoformat()
                    trade['exit_time'] = trade['exit_time'].isoformat()
                
                json.dump(json_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n결과가 'ma_crossover_results.json' 파일에 저장되었습니다.")
            
        except Exception as e:
            strategy.logger.error(f"결과 저장 오류: {e}")
            print(f"결과 저장 오류: {e}")
        
    except Exception as e:
        print(f"프로그램 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()