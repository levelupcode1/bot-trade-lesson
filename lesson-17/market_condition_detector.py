"""
market_condition_detector.py - 시장 상황 자동 감지 시스템

시장을 분석하여 상승장, 하락장, 횡보장을 자동으로 판단합니다.
"""

from typing import Dict, Tuple
from enum import Enum
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime


class MarketTrend(Enum):
    """시장 추세"""
    STRONG_BULL = "강한 상승장"     # 명확한 상승 추세
    BULL = "상승장"                # 상승 추세
    SIDEWAYS = "횡보장"            # 방향성 없음
    BEAR = "하락장"                # 하락 추세
    STRONG_BEAR = "강한 하락장"    # 명확한 하락 추세


class Volatility(Enum):
    """변동성 수준"""
    VERY_LOW = "매우 낮음"    # < 1%
    LOW = "낮음"              # 1-2%
    NORMAL = "보통"           # 2-4%
    HIGH = "높음"             # 4-6%
    VERY_HIGH = "매우 높음"   # > 6%


@dataclass
class MarketCondition:
    """시장 상황 종합"""
    trend: MarketTrend
    volatility: Volatility
    trend_strength: float      # 0.0 ~ 1.0
    momentum: float            # -1.0 ~ 1.0
    volume_profile: str        # 'increasing', 'decreasing', 'stable'
    support_resistance: Dict   # 지지/저항선 정보
    confidence: float          # 신뢰도 0.0 ~ 1.0
    timestamp: datetime
    
    def get_recommended_strategy(self) -> str:
        """
        시장 상황에 따른 추천 전략 반환
        
        Returns:
            추천 전략명
        """
        if self.trend in [MarketTrend.STRONG_BULL, MarketTrend.BULL]:
            if self.volatility in [Volatility.LOW, Volatility.NORMAL]:
                return "trend_following"  # 추세 추종
            else:
                return "momentum_scalping"  # 모멘텀 스캘핑
        
        elif self.trend == MarketTrend.SIDEWAYS:
            if self.volatility == Volatility.LOW:
                return "range_trading"  # 레인지 트레이딩
            else:
                return "volatility_breakout"  # 변동성 돌파
        
        else:  # BEAR or STRONG_BEAR
            if self.volatility in [Volatility.HIGH, Volatility.VERY_HIGH]:
                return "defensive"  # 방어 전략
            else:
                return "wait"  # 현금 보유
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (
            f"시장 상황 분석 ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})\n"
            f"  추세: {self.trend.value} (강도: {self.trend_strength:.2f})\n"
            f"  변동성: {self.volatility.value}\n"
            f"  모멘텀: {self.momentum:+.2f}\n"
            f"  거래량: {self.volume_profile}\n"
            f"  신뢰도: {self.confidence:.2f}\n"
            f"  추천 전략: {self.get_recommended_strategy()}"
        )


class MarketConditionDetector:
    """
    시장 상황 자동 감지기
    
    다양한 기술적 지표를 활용하여 시장 상황을 종합 분석합니다:
    - 추세 분석 (이동평균, 고점/저점 패턴)
    - 변동성 분석 (ATR, 볼린저 밴드)
    - 모멘텀 분석 (RSI, MACD)
    - 거래량 분석
    """
    
    def __init__(self, lookback_period: int = 50):
        """
        초기화
        
        Args:
            lookback_period: 분석 기간 (일)
        """
        self.lookback_period = lookback_period
        
        # 추세 판단 기준
        self.trend_thresholds = {
            'strong_bull': 0.15,    # 15% 이상 상승
            'bull': 0.05,           # 5% 이상 상승
            'sideways': 0.05,       # -5% ~ 5%
            'bear': -0.05,          # -5% 이하 하락
            'strong_bear': -0.15,   # -15% 이하 하락
        }
        
        # 변동성 기준 (일일 변동률 기준)
        self.volatility_thresholds = {
            'very_low': 0.01,   # 1%
            'low': 0.02,        # 2%
            'normal': 0.04,     # 4%
            'high': 0.06,       # 6%
        }
    
    def detect_market_condition(self, 
                               price_data: pd.DataFrame) -> MarketCondition:
        """
        시장 상황 종합 분석
        
        Args:
            price_data: OHLCV 데이터 
                       컬럼: open, high, low, close, volume
        
        Returns:
            MarketCondition 객체
        """
        # 1. 추세 분석
        trend, trend_strength = self._analyze_trend(price_data)
        
        # 2. 변동성 분석
        volatility = self._analyze_volatility(price_data)
        
        # 3. 모멘텀 분석
        momentum = self._analyze_momentum(price_data)
        
        # 4. 거래량 프로필
        volume_profile = self._analyze_volume(price_data)
        
        # 5. 지지/저항선
        support_resistance = self._find_support_resistance(price_data)
        
        # 6. 신뢰도 계산
        confidence = self._calculate_confidence(
            trend_strength, volatility, volume_profile
        )
        
        return MarketCondition(
            trend=trend,
            volatility=volatility,
            trend_strength=trend_strength,
            momentum=momentum,
            volume_profile=volume_profile,
            support_resistance=support_resistance,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _analyze_trend(self, price_data: pd.DataFrame) -> Tuple[MarketTrend, float]:
        """
        추세 분석
        
        방법:
        1. 이동평균선 배열 (단기 > 중기 > 장기 = 상승)
        2. 가격 변화율
        3. 고점/저점 패턴
        
        Returns:
            (추세, 추세 강도)
        """
        close = price_data['close']
        high = price_data['high']
        low = price_data['low']
        
        # 이동평균선 계산
        ma_short = close.rolling(window=10).mean()    # 단기
        ma_medium = close.rolling(window=20).mean()   # 중기
        ma_long = close.rolling(window=50).mean()     # 장기
        
        # 현재 가격 vs 이동평균
        current_price = close.iloc[-1]
        
        # 이동평균선 배열 확인
        ma_alignment = 0
        if ma_short.iloc[-1] > ma_medium.iloc[-1] > ma_long.iloc[-1]:
            ma_alignment = 1  # 상승 배열
        elif ma_short.iloc[-1] < ma_medium.iloc[-1] < ma_long.iloc[-1]:
            ma_alignment = -1  # 하락 배열
        
        # 가격 변화율 (최근 20일)
        if len(close) < 20:
            price_change = 0
        else:
            price_change = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]
        
        # 고점/저점 패턴 분석
        if len(high) >= 10:
            highs = high.rolling(window=5).max()
            lows = low.rolling(window=5).min()
            
            higher_highs = (highs.iloc[-1] > highs.iloc[-5]) and (highs.iloc[-5] > highs.iloc[-10])
            higher_lows = (lows.iloc[-1] > lows.iloc[-5]) and (lows.iloc[-5] > lows.iloc[-10])
            lower_highs = (highs.iloc[-1] < highs.iloc[-5]) and (highs.iloc[-5] < highs.iloc[-10])
            lower_lows = (lows.iloc[-1] < lows.iloc[-5]) and (lows.iloc[-5] < lows.iloc[-10])
        else:
            higher_highs = False
            higher_lows = False
            lower_highs = False
            lower_lows = False
        
        # 추세 판단
        if price_change > self.trend_thresholds['strong_bull'] and ma_alignment == 1:
            trend = MarketTrend.STRONG_BULL
            strength = min(1.0, abs(price_change) / 0.20)
        elif price_change > self.trend_thresholds['bull'] and (ma_alignment == 1 or higher_highs):
            trend = MarketTrend.BULL
            strength = min(0.8, abs(price_change) / 0.10)
        elif price_change < self.trend_thresholds['strong_bear'] and ma_alignment == -1:
            trend = MarketTrend.STRONG_BEAR
            strength = min(1.0, abs(price_change) / 0.20)
        elif price_change < self.trend_thresholds['bear'] and (ma_alignment == -1 or lower_lows):
            trend = MarketTrend.BEAR
            strength = min(0.8, abs(price_change) / 0.10)
        else:
            trend = MarketTrend.SIDEWAYS
            strength = 1.0 - min(abs(price_change) / 0.05, 1.0)  # 변화가 작을수록 강한 횡보
        
        return trend, strength
    
    def _analyze_volatility(self, price_data: pd.DataFrame) -> Volatility:
        """
        변동성 분석
        
        방법:
        1. 일일 수익률 표준편차
        2. ATR (Average True Range)
        """
        close = price_data['close']
        high = price_data['high']
        low = price_data['low']
        
        # 일일 수익률 표준편차
        returns = close.pct_change()
        volatility_std = returns.std()
        
        # ATR 계산
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        atr_percent = atr / close.iloc[-1]
        
        # 변동성 수준 판단
        avg_volatility = (volatility_std + atr_percent) / 2
        
        if avg_volatility < self.volatility_thresholds['very_low']:
            return Volatility.VERY_LOW
        elif avg_volatility < self.volatility_thresholds['low']:
            return Volatility.LOW
        elif avg_volatility < self.volatility_thresholds['normal']:
            return Volatility.NORMAL
        elif avg_volatility < self.volatility_thresholds['high']:
            return Volatility.HIGH
        else:
            return Volatility.VERY_HIGH
    
    def _analyze_momentum(self, price_data: pd.DataFrame) -> float:
        """
        모멘텀 분석
        
        Returns:
            -1.0 (강한 하락) ~ 1.0 (강한 상승)
        """
        close = price_data['close']
        
        # RSI 계산
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # 0으로 나누기 방지
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi_normalized = (rsi.iloc[-1] - 50) / 50  # -1 ~ 1로 정규화
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        macd_histogram = macd - signal
        macd_normalized = np.tanh(macd_histogram.iloc[-1] / close.iloc[-1] * 100)
        
        # 가격 모멘텀 (ROC - Rate of Change)
        if len(close) >= 10:
            roc = (close.iloc[-1] - close.iloc[-10]) / close.iloc[-10]
            roc_normalized = np.tanh(roc * 10)  # -1 ~ 1로 정규화
        else:
            roc_normalized = 0
        
        # 종합 모멘텀 (가중 평균)
        momentum = (rsi_normalized * 0.3 + macd_normalized * 0.4 + roc_normalized * 0.3)
        
        return np.clip(momentum, -1.0, 1.0)
    
    def _analyze_volume(self, price_data: pd.DataFrame) -> str:
        """
        거래량 프로필 분석
        
        Returns:
            'increasing', 'decreasing', 'stable'
        """
        volume = price_data['volume']
        
        # 최근 거래량 vs 평균 거래량
        recent_volume = volume.iloc[-5:].mean()
        avg_volume = volume.iloc[-20:].mean()
        
        # 거래량 추세
        volume_ma_short = volume.rolling(window=5).mean()
        volume_ma_long = volume.rolling(window=20).mean()
        
        volume_trend = volume_ma_short.iloc[-1] / (volume_ma_long.iloc[-1] + 1e-10)
        
        if volume_trend > 1.2:
            return 'increasing'
        elif volume_trend < 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _find_support_resistance(self, price_data: pd.DataFrame) -> Dict:
        """
        지지선/저항선 찾기
        
        방법:
        1. 최근 고점/저점
        2. 피벗 포인트
        3. 이동평균선
        """
        close = price_data['close']
        high = price_data['high']
        low = price_data['low']
        
        current_price = close.iloc[-1]
        
        # 최근 20일 고점/저점
        recent_high = high.iloc[-20:].max()
        recent_low = low.iloc[-20:].min()
        
        # 피벗 포인트 (전일 기준)
        if len(high) >= 2:
            pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
            resistance1 = 2 * pivot - low.iloc[-2]
            support1 = 2 * pivot - high.iloc[-2]
        else:
            pivot = current_price
            resistance1 = current_price * 1.05
            support1 = current_price * 0.95
        
        # 주요 이동평균선
        ma_50 = close.rolling(window=50).mean().iloc[-1]
        ma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None
        
        return {
            'current_price': current_price,
            'resistance_levels': [recent_high, resistance1],
            'support_levels': [recent_low, support1],
            'ma_50': ma_50,
            'ma_200': ma_200,
            'pivot': pivot
        }
    
    def _calculate_confidence(self, 
                            trend_strength: float,
                            volatility: Volatility,
                            volume_profile: str) -> float:
        """
        신뢰도 계산
        
        Returns:
            0.0 ~ 1.0
        """
        confidence = trend_strength
        
        # 변동성이 너무 높으면 신뢰도 감소
        if volatility in [Volatility.VERY_HIGH, Volatility.HIGH]:
            confidence *= 0.8
        
        # 거래량이 감소하면 신뢰도 감소
        if volume_profile == 'decreasing':
            confidence *= 0.9
        elif volume_profile == 'increasing':
            confidence *= 1.1
        
        return min(1.0, confidence)

