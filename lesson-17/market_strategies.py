"""
market_strategies.py - 시장 상황별 전략 구현

상승장, 하락장, 횡보장에 따라 다른 전략을 적용합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np


class BaseStrategy(ABC):
    """전략 기본 클래스"""
    
    def __init__(self, name: str):
        """
        초기화
        
        Args:
            name: 전략 이름
        """
        self.name = name
        self.position = None
        
    @abstractmethod
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """
        매매 신호 생성
        
        Args:
            market_data: OHLCV 데이터
        
        Returns:
            신호 딕셔너리 {'action': 'BUY'/'SELL'/'HOLD', 'confidence': 0.0~1.0, ...}
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            account_balance: 계좌 잔고
            risk_percent: 리스크 비율
        
        Returns:
            투자 금액
        """
        pass


class TrendFollowingStrategy(BaseStrategy):
    """
    추세 추종 전략 (상승장용)
    
    특징:
    - 이동평균선 골든 크로스 시 매수
    - 추세 지속 시 보유
    - 데드 크로스 시 매도
    - 적극적인 포지션 사이징
    """
    
    def __init__(self):
        super().__init__("추세 추종 전략")
        self.ma_short_period = 20
        self.ma_long_period = 50
    
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """추세 추종 신호 생성"""
        close = market_data['close']
        
        # 이동평균선 계산
        ma_short = close.rolling(window=self.ma_short_period).mean()
        ma_long = close.rolling(window=self.ma_long_period).mean()
        
        current_price = close.iloc[-1]
        current_ma_short = ma_short.iloc[-1]
        current_ma_long = ma_long.iloc[-1]
        
        prev_ma_short = ma_short.iloc[-2]
        prev_ma_long = ma_long.iloc[-2]
        
        # 골든 크로스 (매수)
        if prev_ma_short <= prev_ma_long and current_ma_short > current_ma_long:
            return {
                'action': 'BUY',
                'confidence': 0.9,
                'entry_price': current_price,
                'stop_loss': current_ma_long * 0.95,  # MA 아래 5%
                'take_profit': current_price * 1.15,   # 15% 목표
                'reason': '골든 크로스 - 추세 전환 시그널'
            }
        
        # 추세 지속 (보유)
        elif current_ma_short > current_ma_long and current_price > current_ma_short:
            return {
                'action': 'HOLD',
                'confidence': 0.7,
                'reason': '상승 추세 지속 중'
            }
        
        # 데드 크로스 (매도)
        elif prev_ma_short >= prev_ma_long and current_ma_short < current_ma_long:
            return {
                'action': 'SELL',
                'confidence': 0.9,
                'reason': '데드 크로스 - 추세 전환'
            }
        
        # 추세 이탈 (매도)
        elif current_price < current_ma_short:
            return {
                'action': 'SELL',
                'confidence': 0.6,
                'reason': '단기 이평선 이탈'
            }
        
        return {'action': 'HOLD', 'confidence': 0.5, 'reason': '관망'}
    
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """추세 추종 포지션 크기"""
        # 상승장에서는 적극적으로 (3-5%)
        return account_balance * min(0.05, risk_percent * 1.5)


class RangeTradingStrategy(BaseStrategy):
    """
    레인지 트레이딩 전략 (횡보장용)
    
    특징:
    - 지지선 근처에서 매수
    - 저항선 근처에서 매도
    - RSI 과매수/과매도 활용
    - 볼린저 밴드 활용
    """
    
    def __init__(self):
        super().__init__("레인지 트레이딩 전략")
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.bb_period = 20
        self.bb_std = 2
    
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """레인지 트레이딩 신호 생성"""
        close = market_data['close']
        high = market_data['high']
        low = market_data['low']
        
        # RSI 계산
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        current_price = close.iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        # 볼린저 밴드
        bb_middle = close.rolling(window=self.bb_period).mean()
        bb_std_dev = close.rolling(window=self.bb_period).std()
        bb_upper = bb_middle + (bb_std_dev * self.bb_std)
        bb_lower = bb_middle - (bb_std_dev * self.bb_std)
        
        # 지지선/저항선 (최근 20일)
        support = low.iloc[-20:].min()
        resistance = high.iloc[-20:].max()
        
        # 매수 신호: RSI 과매도 + 볼린저 하단
        if current_rsi < self.rsi_oversold and current_price < bb_lower.iloc[-1]:
            return {
                'action': 'BUY',
                'confidence': 0.8,
                'entry_price': current_price,
                'stop_loss': support * 0.98,
                'take_profit': bb_middle.iloc[-1],
                'reason': f'RSI 과매도({current_rsi:.1f}) + 볼린저 하단'
            }
        
        # 매도 신호: RSI 과매수 + 볼린저 상단
        elif current_rsi > self.rsi_overbought and current_price > bb_upper.iloc[-1]:
            return {
                'action': 'SELL',
                'confidence': 0.8,
                'reason': f'RSI 과매수({current_rsi:.1f}) + 볼린저 상단'
            }
        
        # 중립 구간 (보유)
        elif self.rsi_oversold < current_rsi < self.rsi_overbought:
            return {
                'action': 'HOLD',
                'confidence': 0.6,
                'reason': '레인지 내 정상 범위'
            }
        
        return {'action': 'HOLD', 'confidence': 0.5, 'reason': '관망'}
    
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """레인지 포지션 크기"""
        # 횡보장에서는 보수적으로 (2-3%)
        return account_balance * min(0.03, risk_percent)


class VolatilityBreakoutStrategy(BaseStrategy):
    """
    변동성 돌파 전략 (횡보장 → 추세 전환용)
    
    특징:
    - 래리 윌리엄스 변동성 돌파
    - 목표가 = 시가 + (전일 변동폭 × K)
    - 단기 수익 실현
    """
    
    def __init__(self, k: float = 0.5):
        super().__init__("변동성 돌파 전략")
        self.k = k  # 변동성 계수
    
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """변동성 돌파 신호 생성"""
        close = market_data['close']
        high = market_data['high']
        low = market_data['low']
        open_price = market_data['open']
        
        # 전일 변동폭
        prev_high = high.iloc[-2]
        prev_low = low.iloc[-2]
        prev_range = prev_high - prev_low
        
        # 목표가 = 시가 + (전일 변동폭 × k)
        today_open = open_price.iloc[-1]
        target_price = today_open + (prev_range * self.k)
        
        current_price = close.iloc[-1]
        
        # 돌파 매수
        if current_price > target_price:
            return {
                'action': 'BUY',
                'confidence': 0.85,
                'entry_price': current_price,
                'stop_loss': today_open,
                'take_profit': current_price * 1.10,
                'reason': f'변동성 돌파 (목표가: {target_price:,.0f}원)'
            }
        
        # 목표가 근처 (관망)
        elif current_price > target_price * 0.95:
            return {
                'action': 'HOLD',
                'confidence': 0.6,
                'reason': '목표가 근접'
            }
        
        return {'action': 'HOLD', 'confidence': 0.5, 'reason': '돌파 대기'}
    
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """변동성 돌파 포지션 크기"""
        return account_balance * min(0.04, risk_percent * 1.2)


class DefensiveStrategy(BaseStrategy):
    """
    방어 전략 (하락장용)
    
    특징:
    - 매도 우선
    - 현금 보유 확대
    - 극히 제한적 진입 (단기 반등만)
    - 타이트한 손절
    """
    
    def __init__(self):
        super().__init__("방어 전략")
        self.ma_period = 20
    
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """방어적 신호 생성"""
        close = market_data['close']
        
        # 이동평균선
        ma_20 = close.rolling(window=20).mean()
        ma_50 = close.rolling(window=50).mean()
        
        current_price = close.iloc[-1]
        
        # 모든 포지션 청산 권장
        if current_price < ma_20.iloc[-1] and current_price < ma_50.iloc[-1]:
            return {
                'action': 'SELL',
                'confidence': 0.9,
                'reason': '하락 추세 확인 - 현금 보유 권장'
            }
        
        # 단기 반등 (극히 제한적 진입)
        elif current_price > ma_20.iloc[-1] * 1.05:
            # RSI로 재확인
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            
            if rsi.iloc[-1] < 30:  # 극심한 과매도
                return {
                    'action': 'BUY',
                    'confidence': 0.5,
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.97,  # 타이트한 손절
                    'take_profit': current_price * 1.05,  # 작은 목표
                    'reason': '극심한 과매도 단기 반등 시도'
                }
        
        return {
            'action': 'HOLD',
            'confidence': 0.8,
            'reason': '현금 보유 - 하락장 방어'
        }
    
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """방어 포지션 크기"""
        # 하락장에서는 극히 보수적 (1% 이하)
        return account_balance * min(0.01, risk_percent * 0.5)


class MomentumScalpingStrategy(BaseStrategy):
    """
    모멘텀 스캘핑 전략 (고변동성 상승장용)
    
    특징:
    - 단기 모멘텀 추종
    - 빠른 진입/청산
    - 작은 목표 수익
    """
    
    def __init__(self):
        super().__init__("모멘텀 스캘핑 전략")
        self.momentum_period = 10
    
    def generate_signal(self, market_data: pd.DataFrame) -> Dict:
        """모멘텀 스캘핑 신호"""
        close = market_data['close']
        volume = market_data['volume']
        
        # 단기 모멘텀 (ROC)
        if len(close) >= self.momentum_period:
            roc = (close.iloc[-1] - close.iloc[-self.momentum_period]) / close.iloc[-self.momentum_period]
        else:
            roc = 0
        
        # 거래량 급증 확인
        avg_volume = volume.rolling(window=20).mean()
        volume_surge = volume.iloc[-1] > avg_volume.iloc[-1] * 1.5
        
        current_price = close.iloc[-1]
        
        # 강한 모멘텀 + 거래량 급증
        if roc > 0.03 and volume_surge:  # 3% 이상 상승 + 거래량
            return {
                'action': 'BUY',
                'confidence': 0.7,
                'entry_price': current_price,
                'stop_loss': current_price * 0.98,
                'take_profit': current_price * 1.03,
                'reason': f'강한 모멘텀({roc*100:.1f}%) + 거래량 급증'
            }
        
        # 모멘텀 약화
        elif roc < 0:
            return {
                'action': 'SELL',
                'confidence': 0.7,
                'reason': '모멘텀 약화'
            }
        
        return {'action': 'HOLD', 'confidence': 0.5, 'reason': '관망'}
    
    def calculate_position_size(self, account_balance: float, 
                               risk_percent: float) -> float:
        """스캘핑 포지션 크기"""
        # 빠른 회전으로 중간 크기 (2-3%)
        return account_balance * min(0.03, risk_percent)

