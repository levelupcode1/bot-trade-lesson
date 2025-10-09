#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시장 상황 분석 모듈
변동성 구간별, 트렌드/사이드웨이스, 시간대별 최적화를 위한 시장 상황 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import json
import warnings
from scipy import stats
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import ta  # Technical Analysis library

warnings.filterwarnings('ignore')

class MarketRegime(Enum):
    """시장 체제"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"

class VolatilityRegime(Enum):
    """변동성 체제"""
    VERY_LOW = "very_low"    # < 1%
    LOW = "low"              # 1-3%
    MEDIUM = "medium"        # 3-7%
    HIGH = "high"            # 7-15%
    VERY_HIGH = "very_high"  # > 15%

class TrendStrength(Enum):
    """추세 강도"""
    VERY_WEAK = "very_weak"  # < 0.3
    WEAK = "weak"            # 0.3-0.5
    MODERATE = "moderate"    # 0.5-0.7
    STRONG = "strong"        # 0.7-0.8
    VERY_STRONG = "very_strong"  # > 0.8

@dataclass
class MarketCondition:
    """시장 상황"""
    timestamp: datetime
    regime: MarketRegime
    volatility_regime: VolatilityRegime
    trend_strength: TrendStrength
    trend_direction: int  # 1: 상승, -1: 하락, 0: 횡보
    volatility: float
    momentum: float
    volume_profile: str  # high, medium, low
    support_resistance_levels: List[float] = field(default_factory=list)
    technical_indicators: Dict[str, float] = field(default_factory=dict)

@dataclass
class MarketRegimeTransition:
    """시장 체제 전환"""
    from_regime: MarketRegime
    to_regime: MarketRegime
    transition_date: datetime
    confidence: float
    trigger_factors: List[str] = field(default_factory=list)

@dataclass
class OptimizationSignal:
    """최적화 신호"""
    strategy_type: str
    parameter_adjustments: Dict[str, float]
    confidence: float
    expected_improvement: float
    reasoning: str

class MarketConditionAnalyzer:
    """시장 상황 분석기"""
    
    def __init__(self, lookback_period: int = 252):
        self.lookback_period = lookback_period
        self.logger = logging.getLogger(__name__)
        
        # 분석 결과 저장
        self.market_conditions: List[MarketCondition] = []
        self.regime_transitions: List[MarketRegimeTransition] = []
        self.optimization_signals: List[OptimizationSignal] = []
        
        # 임계값 설정
        self.volatility_thresholds = {
            VolatilityRegime.VERY_LOW: 0.01,
            VolatilityRegime.LOW: 0.03,
            VolatilityRegime.MEDIUM: 0.07,
            VolatilityRegime.HIGH: 0.15,
            VolatilityRegime.VERY_HIGH: float('inf')
        }
        
        self.trend_strength_thresholds = {
            TrendStrength.VERY_WEAK: 0.3,
            TrendStrength.WEAK: 0.5,
            TrendStrength.MODERATE: 0.7,
            TrendStrength.STRONG: 0.8,
            TrendStrength.VERY_STRONG: float('inf')
        }
        
        self.logger.info("시장 상황 분석기 초기화 완료")
    
    def analyze_market_conditions(self, data: pd.DataFrame) -> List[MarketCondition]:
        """시장 상황 종합 분석"""
        self.logger.info("시장 상황 분석 시작")
        
        conditions = []
        
        # 각 시점별로 분석
        for i in range(self.lookback_period, len(data)):
            analysis_date = data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i
            window_data = data.iloc[i-self.lookback_period:i+1].copy()
            
            try:
                # 기본 시장 상황 분석
                condition = self._analyze_single_period(window_data, analysis_date)
                conditions.append(condition)
                
            except Exception as e:
                self.logger.warning(f"시점 {i} 분석 실패: {e}")
                continue
        
        self.market_conditions = conditions
        
        # 체제 전환 분석
        self._analyze_regime_transitions()
        
        # 최적화 신호 생성
        self._generate_optimization_signals()
        
        self.logger.info(f"시장 상황 분석 완료: {len(conditions)}개 시점")
        
        return conditions
    
    def _analyze_single_period(self, data: pd.DataFrame, timestamp: datetime) -> MarketCondition:
        """단일 시점 분석"""
        # 변동성 분석
        volatility_regime, volatility = self._analyze_volatility_regime(data)
        
        # 추세 분석
        trend_strength, trend_direction = self._analyze_trend(data)
        
        # 모멘텀 분석
        momentum = self._analyze_momentum(data)
        
        # 거래량 프로필 분석
        volume_profile = self._analyze_volume_profile(data)
        
        # 지지/저항 레벨 분석
        support_resistance = self._find_support_resistance_levels(data)
        
        # 기술적 지표 계산
        technical_indicators = self._calculate_technical_indicators(data)
        
        # 종합 시장 체제 결정
        regime = self._determine_market_regime(
            volatility_regime, trend_strength, trend_direction, momentum
        )
        
        return MarketCondition(
            timestamp=timestamp,
            regime=regime,
            volatility_regime=volatility_regime,
            trend_strength=trend_strength,
            trend_direction=trend_direction,
            volatility=volatility,
            momentum=momentum,
            volume_profile=volume_profile,
            support_resistance_levels=support_resistance,
            technical_indicators=technical_indicators
        )
    
    def _analyze_volatility_regime(self, data: pd.DataFrame) -> Tuple[VolatilityRegime, float]:
        """변동성 체제 분석"""
        returns = data['close'].pct_change().dropna()
        
        # 단기 변동성 (5일)
        short_volatility = returns.tail(5).std() * np.sqrt(252)
        
        # 중기 변동성 (20일)
        medium_volatility = returns.tail(20).std() * np.sqrt(252)
        
        # 장기 변동성 (60일)
        long_volatility = returns.tail(60).std() * np.sqrt(252)
        
        # 가중 평균 변동성 (단기 50%, 중기 30%, 장기 20%)
        weighted_volatility = (
            short_volatility * 0.5 +
            medium_volatility * 0.3 +
            long_volatility * 0.2
        )
        
        # 변동성 체제 결정
        for regime, threshold in self.volatility_thresholds.items():
            if weighted_volatility < threshold:
                return regime, weighted_volatility
        
        return VolatilityRegime.VERY_HIGH, weighted_volatility
    
    def _analyze_trend(self, data: pd.DataFrame) -> Tuple[TrendStrength, int]:
        """추세 분석"""
        prices = data['close'].values
        
        # 다중 기간 이동평균
        ma_5 = pd.Series(prices).rolling(5).mean()
        ma_20 = pd.Series(prices).rolling(20).mean()
        ma_50 = pd.Series(prices).rolling(50).mean()
        
        # 추세 방향 결정
        recent_5 = ma_5.iloc[-1]
        recent_20 = ma_20.iloc[-1]
        recent_50 = ma_50.iloc[-1]
        
        # 추세 방향 (1: 상승, -1: 하락, 0: 횡보)
        if recent_5 > recent_20 > recent_50:
            trend_direction = 1
        elif recent_5 < recent_20 < recent_50:
            trend_direction = -1
        else:
            trend_direction = 0
        
        # 추세 강도 계산 (ADX 유사)
        trend_strength = self._calculate_trend_strength(data)
        
        # 추세 강도 등급 결정
        for strength, threshold in self.trend_strength_thresholds.items():
            if trend_strength < threshold:
                return strength, trend_direction
        
        return TrendStrength.VERY_STRONG, trend_direction
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """추세 강도 계산 (ADX 유사)"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # True Range 계산
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement 계산
        dm_plus = high.diff()
        dm_minus = -low.diff()
        
        dm_plus[dm_plus < 0] = 0
        dm_minus[dm_minus < 0] = 0
        
        # DM+와 DM- 중 하나만 양수일 때만 유효
        dm_plus[dm_plus <= dm_minus] = 0
        dm_minus[dm_minus <= dm_plus] = 0
        
        # 14일 평활화
        tr_smooth = tr.rolling(14).mean()
        dm_plus_smooth = dm_plus.rolling(14).mean()
        dm_minus_smooth = dm_minus.rolling(14).mean()
        
        # DI 계산
        di_plus = 100 * (dm_plus_smooth / tr_smooth)
        di_minus = 100 * (dm_minus_smooth / tr_smooth)
        
        # DX 계산
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        
        # ADX 계산 (최근값)
        adx = dx.rolling(14).mean().iloc[-1]
        
        return adx / 100 if not pd.isna(adx) else 0
    
    def _analyze_momentum(self, data: pd.DataFrame) -> float:
        """모멘텀 분석"""
        prices = data['close']
        
        # 다중 기간 모멘텀
        momentum_5 = (prices.iloc[-1] - prices.iloc[-6]) / prices.iloc[-6] if len(prices) > 5 else 0
        momentum_20 = (prices.iloc[-1] - prices.iloc[-21]) / prices.iloc[-21] if len(prices) > 20 else 0
        momentum_60 = (prices.iloc[-1] - prices.iloc[-61]) / prices.iloc[-61] if len(prices) > 60 else 0
        
        # 가중 평균 모멘텀
        weighted_momentum = (
            momentum_5 * 0.5 +
            momentum_20 * 0.3 +
            momentum_60 * 0.2
        )
        
        return weighted_momentum
    
    def _analyze_volume_profile(self, data: pd.DataFrame) -> str:
        """거래량 프로필 분석"""
        volume = data['volume']
        
        # 거래량 이동평균
        vol_ma_20 = volume.rolling(20).mean()
        recent_volume = volume.iloc[-5:].mean()
        avg_volume = vol_ma_20.iloc[-1]
        
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > 1.5:
            return "high"
        elif volume_ratio < 0.7:
            return "low"
        else:
            return "medium"
    
    def _find_support_resistance_levels(self, data: pd.DataFrame) -> List[float]:
        """지지/저항 레벨 찾기"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        levels = []
        
        # 고점 찾기 (저항)
        peaks, _ = find_peaks(high, distance=10, prominence=np.std(high) * 0.5)
        if len(peaks) > 0:
            resistance_levels = high[peaks]
            levels.extend(resistance_levels.tolist())
        
        # 저점 찾기 (지지)
        valleys, _ = find_peaks(-low, distance=10, prominence=np.std(low) * 0.5)
        if len(valleys) > 0:
            support_levels = low[valleys]
            levels.extend(support_levels.tolist())
        
        # 현재 가격 근처의 레벨만 반환
        current_price = close[-1]
        nearby_levels = [level for level in levels if abs(level - current_price) / current_price < 0.1]
        
        return nearby_levels[:5]  # 최대 5개 레벨
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """기술적 지표 계산"""
        indicators = {}
        
        try:
            # RSI
            indicators['rsi'] = ta.momentum.RSIIndicator(data['close']).rsi().iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(data['close'])
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd.macd_diff().iloc[-1]
            
            # 볼린저 밴드
            bb = ta.volatility.BollingerBands(data['close'])
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']
            
            # 스토캐스틱
            stoch = ta.momentum.StochasticOscillator(data['high'], data['low'], data['close'])
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
            
            # 윌리엄스 %R
            indicators['williams_r'] = ta.momentum.WilliamsRIndicator(data['high'], data['low'], data['close']).williams_r().iloc[-1]
            
            # CCI
            indicators['cci'] = ta.trend.CCIIndicator(data['high'], data['low'], data['close']).cci().iloc[-1]
            
        except Exception as e:
            self.logger.warning(f"기술적 지표 계산 실패: {e}")
        
        return indicators
    
    def _determine_market_regime(self, 
                               volatility_regime: VolatilityRegime,
                               trend_strength: TrendStrength,
                               trend_direction: int,
                               momentum: float) -> MarketRegime:
        """시장 체제 결정"""
        # 고변동성 시장
        if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.VERY_HIGH]:
            return MarketRegime.HIGH_VOLATILITY
        
        # 저변동성 시장
        if volatility_regime in [VolatilityRegime.VERY_LOW, VolatilityRegime.LOW]:
            return MarketRegime.LOW_VOLATILITY
        
        # 강한 추세 시장
        if trend_strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
            if trend_direction == 1:
                return MarketRegime.BULL_MARKET
            elif trend_direction == -1:
                return MarketRegime.BEAR_MARKET
            else:
                return MarketRegime.TRENDING
        
        # 약한 추세 시장
        if trend_strength in [TrendStrength.WEAK, TrendStrength.VERY_WEAK]:
            # 모멘텀 기반 판단
            if abs(momentum) < 0.02:
                return MarketRegime.SIDEWAYS
            else:
                return MarketRegime.MEAN_REVERTING
        
        # 중간 강도 추세
        return MarketRegime.TRENDING
    
    def _analyze_regime_transitions(self):
        """체제 전환 분석"""
        if len(self.market_conditions) < 2:
            return
        
        transitions = []
        
        for i in range(1, len(self.market_conditions)):
            prev_condition = self.market_conditions[i-1]
            curr_condition = self.market_conditions[i]
            
            # 체제 변화 감지
            if prev_condition.regime != curr_condition.regime:
                confidence = self._calculate_transition_confidence(prev_condition, curr_condition)
                trigger_factors = self._identify_trigger_factors(prev_condition, curr_condition)
                
                transition = MarketRegimeTransition(
                    from_regime=prev_condition.regime,
                    to_regime=curr_condition.regime,
                    transition_date=curr_condition.timestamp,
                    confidence=confidence,
                    trigger_factors=trigger_factors
                )
                
                transitions.append(transition)
        
        self.regime_transitions = transitions
        self.logger.info(f"체제 전환 {len(transitions)}개 감지")
    
    def _calculate_transition_confidence(self, 
                                       prev_condition: MarketCondition,
                                       curr_condition: MarketCondition) -> float:
        """전환 신뢰도 계산"""
        confidence_factors = []
        
        # 변동성 변화
        vol_change = abs(curr_condition.volatility - prev_condition.volatility)
        vol_confidence = min(1.0, vol_change / 0.05)  # 5% 변화를 최대 신뢰도로
        confidence_factors.append(vol_confidence)
        
        # 모멘텀 변화
        momentum_change = abs(curr_condition.momentum - prev_condition.momentum)
        momentum_confidence = min(1.0, momentum_change / 0.1)  # 10% 변화를 최대 신뢰도로
        confidence_factors.append(momentum_confidence)
        
        # 추세 강도 변화
        strength_change = abs(curr_condition.trend_strength.value - prev_condition.trend_strength.value)
        strength_confidence = min(1.0, strength_change / 4)  # 4단계 변화를 최대 신뢰도로
        confidence_factors.append(strength_confidence)
        
        return np.mean(confidence_factors)
    
    def _identify_trigger_factors(self, 
                                prev_condition: MarketCondition,
                                curr_condition: MarketCondition) -> List[str]:
        """전환 요인 식별"""
        factors = []
        
        # 변동성 변화
        if abs(curr_condition.volatility - prev_condition.volatility) > 0.02:
            if curr_condition.volatility > prev_condition.volatility:
                factors.append("변동성 증가")
            else:
                factors.append("변동성 감소")
        
        # 추세 변화
        if prev_condition.trend_direction != curr_condition.trend_direction:
            if curr_condition.trend_direction == 1:
                factors.append("상승 추세 전환")
            elif curr_condition.trend_direction == -1:
                factors.append("하락 추세 전환")
            else:
                factors.append("횡보 전환")
        
        # 거래량 변화
        if prev_condition.volume_profile != curr_condition.volume_profile:
            if curr_condition.volume_profile == "high":
                factors.append("거래량 급증")
            elif curr_condition.volume_profile == "low":
                factors.append("거래량 감소")
        
        # 모멘텀 변화
        momentum_change = curr_condition.momentum - prev_condition.momentum
        if abs(momentum_change) > 0.05:
            if momentum_change > 0:
                factors.append("모멘텀 강화")
            else:
                factors.append("모멘텀 약화")
        
        return factors
    
    def _generate_optimization_signals(self):
        """최적화 신호 생성"""
        signals = []
        
        for condition in self.market_conditions:
            # 시장 상황별 최적화 신호 생성
            regime_signals = self._generate_regime_based_signals(condition)
            signals.extend(regime_signals)
        
        self.optimization_signals = signals
        self.logger.info(f"최적화 신호 {len(signals)}개 생성")
    
    def _generate_regime_based_signals(self, condition: MarketCondition) -> List[OptimizationSignal]:
        """체제 기반 최적화 신호 생성"""
        signals = []
        
        if condition.regime == MarketRegime.HIGH_VOLATILITY:
            # 고변동성 시장: 변동성 돌파 전략 파라미터 조정
            signals.append(OptimizationSignal(
                strategy_type="volatility_breakout",
                parameter_adjustments={
                    "k": 0.7,  # 높은 k값으로 노이즈 필터링
                    "stop_loss": 0.03,  # 넓은 손절
                    "take_profit": 0.05  # 높은 익절
                },
                confidence=0.8,
                expected_improvement=0.15,
                reasoning="고변동성 시장에서 노이즈 필터링 및 넓은 손절/익절 적용"
            ))
        
        elif condition.regime == MarketRegime.LOW_VOLATILITY:
            # 저변동성 시장: 평균 회귀 전략 강화
            signals.append(OptimizationSignal(
                strategy_type="mean_reversion",
                parameter_adjustments={
                    "threshold": 1.0,  # 낮은 임계값
                    "stop_loss": 0.015,  # 좁은 손절
                    "take_profit": 0.025  # 낮은 익절
                },
                confidence=0.7,
                expected_improvement=0.10,
                reasoning="저변동성 시장에서 민감한 평균 회귀 신호 활용"
            ))
        
        elif condition.regime == MarketRegime.BULL_MARKET:
            # 상승 시장: 모멘텀 전략 강화
            signals.append(OptimizationSignal(
                strategy_type="momentum",
                parameter_adjustments={
                    "period": 5,  # 짧은 기간
                    "threshold": 0.01,  # 낮은 임계값
                    "stop_loss": 0.025  # 넓은 손절
                },
                confidence=0.9,
                expected_improvement=0.20,
                reasoning="상승 시장에서 강한 모멘텀 추종"
            ))
        
        elif condition.regime == MarketRegime.BEAR_MARKET:
            # 하락 시장: 방어적 전략
            signals.append(OptimizationSignal(
                strategy_type="volatility_breakout",
                parameter_adjustments={
                    "k": 0.3,  # 낮은 k값으로 빠른 반응
                    "stop_loss": 0.015,  # 좁은 손절
                    "take_profit": 0.02  # 낮은 익절
                },
                confidence=0.8,
                expected_improvement=0.12,
                reasoning="하락 시장에서 빠른 손절과 낮은 익절 목표"
            ))
        
        elif condition.regime == MarketRegime.SIDEWAYS:
            # 횡보 시장: 평균 회귀 전략
            signals.append(OptimizationSignal(
                strategy_type="bollinger_bands",
                parameter_adjustments={
                    "period": 20,
                    "std_dev": 2.0,
                    "stop_loss": 0.02,
                    "take_profit": 0.03
                },
                confidence=0.75,
                expected_improvement=0.08,
                reasoning="횡보 시장에서 볼린저 밴드 평균 회귀 활용"
            ))
        
        return signals
    
    def get_current_market_condition(self) -> Optional[MarketCondition]:
        """현재 시장 상황 반환"""
        if self.market_conditions:
            return self.market_conditions[-1]
        return None
    
    def get_regime_transition_probability(self, 
                                        from_regime: MarketRegime,
                                        to_regime: MarketRegime) -> float:
        """체제 전환 확률 계산"""
        if not self.regime_transitions:
            return 0.0
        
        total_transitions = len(self.regime_transitions)
        matching_transitions = len([
            t for t in self.regime_transitions 
            if t.from_regime == from_regime and t.to_regime == to_regime
        ])
        
        return matching_transitions / total_transitions if total_transitions > 0 else 0.0
    
    def get_optimization_recommendations(self, 
                                       strategy_type: str,
                                       current_parameters: Dict[str, float]) -> List[OptimizationSignal]:
        """특정 전략에 대한 최적화 추천"""
        recommendations = []
        
        for signal in self.optimization_signals:
            if signal.strategy_type == strategy_type:
                # 현재 파라미터와 비교하여 변경사항 계산
                adjustments = {}
                for param, new_value in signal.parameter_adjustments.items():
                    if param in current_parameters:
                        current_value = current_parameters[param]
                        if abs(new_value - current_value) / current_value > 0.1:  # 10% 이상 변화
                            adjustments[param] = new_value
                
                if adjustments:
                    signal.parameter_adjustments = adjustments
                    recommendations.append(signal)
        
        return recommendations
    
    def get_market_regime_summary(self) -> Dict[str, Any]:
        """시장 체제 요약"""
        if not self.market_conditions:
            return {"message": "분석된 시장 상황이 없습니다."}
        
        # 체제별 분포
        regime_counts = {}
        for condition in self.market_conditions:
            regime = condition.regime.value
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # 변동성 체제별 분포
        vol_regime_counts = {}
        for condition in self.market_conditions:
            vol_regime = condition.volatility_regime.value
            vol_regime_counts[vol_regime] = vol_regime_counts.get(vol_regime, 0) + 1
        
        # 평균 지표
        avg_volatility = np.mean([c.volatility for c in self.market_conditions])
        avg_momentum = np.mean([c.momentum for c in self.market_conditions])
        
        # 최근 체제 전환
        recent_transitions = self.regime_transitions[-5:] if len(self.regime_transitions) > 5 else self.regime_transitions
        
        return {
            "total_periods": len(self.market_conditions),
            "regime_distribution": regime_counts,
            "volatility_regime_distribution": vol_regime_counts,
            "average_volatility": avg_volatility,
            "average_momentum": avg_momentum,
            "total_transitions": len(self.regime_transitions),
            "recent_transitions": [
                {
                    "from": t.from_regime.value,
                    "to": t.to_regime.value,
                    "date": t.transition_date.isoformat(),
                    "confidence": t.confidence,
                    "triggers": t.trigger_factors
                }
                for t in recent_transitions
            ],
            "optimization_signals_count": len(self.optimization_signals)
        }
    
    def save_analysis_results(self, filename: str = None):
        """분석 결과 저장"""
        if filename is None:
            filename = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "market_conditions": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "regime": c.regime.value,
                    "volatility_regime": c.volatility_regime.value,
                    "trend_strength": c.trend_strength.value,
                    "trend_direction": c.trend_direction,
                    "volatility": c.volatility,
                    "momentum": c.momentum,
                    "volume_profile": c.volume_profile,
                    "support_resistance_levels": c.support_resistance_levels,
                    "technical_indicators": c.technical_indicators
                }
                for c in self.market_conditions
            ],
            "regime_transitions": [
                {
                    "from_regime": t.from_regime.value,
                    "to_regime": t.to_regime.value,
                    "transition_date": t.transition_date.isoformat(),
                    "confidence": t.confidence,
                    "trigger_factors": t.trigger_factors
                }
                for t in self.regime_transitions
            ],
            "optimization_signals": [
                {
                    "strategy_type": s.strategy_type,
                    "parameter_adjustments": s.parameter_adjustments,
                    "confidence": s.confidence,
                    "expected_improvement": s.expected_improvement,
                    "reasoning": s.reasoning
                }
                for s in self.optimization_signals
            ],
            "summary": self.get_market_regime_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"분석 결과 저장 완료: {filename}")

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=365, freq='D')
    
    # 다양한 시장 상황을 시뮬레이션
    prices = []
    current_price = 100
    
    for i in range(365):
        if i < 100:  # 상승 시장
            change = np.random.normal(0.002, 0.02)
        elif i < 200:  # 하락 시장
            change = np.random.normal(-0.001, 0.025)
        elif i < 300:  # 고변동성 시장
            change = np.random.normal(0.0005, 0.04)
        else:  # 횡보 시장
            change = np.random.normal(0, 0.015)
        
        current_price *= (1 + change)
        prices.append(current_price)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': [p * (1 + np.random.randn() * 0.005) for p in prices],
        'high': [p * (1 + abs(np.random.randn()) * 0.01) for p in prices],
        'low': [p * (1 - abs(np.random.randn()) * 0.01) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, 365)
    })
    
    # 시장 상황 분석기 초기화
    analyzer = MarketConditionAnalyzer(lookback_period=60)
    
    # 시장 상황 분석
    print("=== 시장 상황 분석 ===")
    conditions = analyzer.analyze_market_conditions(sample_data)
    
    print(f"분석된 시점 수: {len(conditions)}")
    print(f"체제 전환 수: {len(analyzer.regime_transitions)}")
    print(f"최적화 신호 수: {len(analyzer.optimization_signals)}")
    
    # 현재 시장 상황
    current_condition = analyzer.get_current_market_condition()
    if current_condition:
        print(f"\n현재 시장 상황:")
        print(f"  체제: {current_condition.regime.value}")
        print(f"  변동성 체제: {current_condition.volatility_regime.value}")
        print(f"  추세 강도: {current_condition.trend_strength.value}")
        print(f"  변동성: {current_condition.volatility:.2%}")
        print(f"  모멘텀: {current_condition.momentum:.2%}")
    
    # 최적화 신호 확인
    print(f"\n최적화 신호 (최근 5개):")
    for signal in analyzer.optimization_signals[-5:]:
        print(f"  전략: {signal.strategy_type}")
        print(f"    파라미터 조정: {signal.parameter_adjustments}")
        print(f"    신뢰도: {signal.confidence:.2f}")
        print(f"    예상 개선: {signal.expected_improvement:.1%}")
        print(f"    근거: {signal.reasoning}")
        print()
    
    # 시장 체제 요약
    summary = analyzer.get_market_regime_summary()
    print("=== 시장 체제 요약 ===")
    print(f"총 분석 기간: {summary['total_periods']}일")
    print(f"평균 변동성: {summary['average_volatility']:.2%}")
    print(f"평균 모멘텀: {summary['average_momentum']:.2%}")
    print(f"체제 전환 횟수: {summary['total_transitions']}")
    
    print("\n체제별 분포:")
    for regime, count in summary['regime_distribution'].items():
        percentage = count / summary['total_periods'] * 100
        print(f"  {regime}: {count}일 ({percentage:.1f}%)")
    
    # 체제 전환 확률
    print(f"\n체제 전환 확률:")
    for from_regime in MarketRegime:
        for to_regime in MarketRegime:
            if from_regime != to_regime:
                prob = analyzer.get_regime_transition_probability(from_regime, to_regime)
                if prob > 0:
                    print(f"  {from_regime.value} → {to_regime.value}: {prob:.1%}")
    
    # 분석 결과 저장
    analyzer.save_analysis_results()
