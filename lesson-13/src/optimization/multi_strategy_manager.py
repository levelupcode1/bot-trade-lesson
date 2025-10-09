#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티 전략 관리 시스템
여러 거래 전략을 조합하고 가중치를 할당하여 최적의 성과를 달성
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
import joblib

warnings.filterwarnings('ignore')

class StrategyType(Enum):
    """전략 타입"""
    VOLATILITY_BREAKOUT = "volatility_breakout"
    MOVING_AVERAGE_CROSSOVER = "moving_average_crossover"
    RSI_MEAN_REVERSION = "rsi_mean_reversion"
    BOLLINGER_BANDS = "bollinger_bands"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"

class WeightAllocationMethod(Enum):
    """가중치 할당 방법"""
    EQUAL_WEIGHT = "equal_weight"
    PERFORMANCE_BASED = "performance_based"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    MACHINE_LEARNING = "machine_learning"
    DYNAMIC_ADJUSTMENT = "dynamic_adjustment"

@dataclass
class StrategyConfig:
    """개별 전략 설정"""
    strategy_type: StrategyType
    parameters: Dict[str, float]
    enabled: bool = True
    min_weight: float = 0.0
    max_weight: float = 1.0
    lookback_period: int = 30  # 성과 평가 기간

@dataclass
class StrategyPerformance:
    """전략 성과"""
    strategy_type: StrategyType
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_return: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float

@dataclass
class MultiStrategyResult:
    """멀티 전략 결과"""
    combined_return: float
    combined_sharpe: float
    combined_max_drawdown: float
    strategy_weights: Dict[str, float]
    individual_performances: Dict[str, StrategyPerformance]
    rebalance_history: List[Dict[str, Any]] = field(default_factory=list)

class MultiStrategyManager:
    """멀티 전략 관리 시스템"""
    
    def __init__(self, initial_capital: float = 1_000_000):
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
        # 전략 설정
        self.strategies: Dict[str, StrategyConfig] = {}
        
        # 성과 추적
        self.performance_history = []
        self.weight_history = []
        
        # 머신러닝 모델 (동적 가중치 조정용)
        self.ml_model = None
        self.feature_importance = {}
        
        self.logger.info("멀티 전략 관리 시스템 초기화 완료")
    
    def add_strategy(self, strategy_id: str, config: StrategyConfig):
        """전략 추가"""
        self.strategies[strategy_id] = config
        self.logger.info(f"전략 추가: {strategy_id} ({config.strategy_type.value})")
    
    def remove_strategy(self, strategy_id: str):
        """전략 제거"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            self.logger.info(f"전략 제거: {strategy_id}")
    
    def optimize_portfolio_weights(self, 
                                 data: pd.DataFrame, 
                                 method: WeightAllocationMethod = WeightAllocationMethod.PERFORMANCE_BASED,
                                 rebalance_frequency: int = 30) -> MultiStrategyResult:
        """포트폴리오 가중치 최적화"""
        self.logger.info(f"포트폴리오 가중치 최적화 시작 (방법: {method.value})")
        
        if not self.strategies:
            raise ValueError("최적화할 전략이 없습니다.")
        
        # 개별 전략 성과 계산
        individual_performances = self._calculate_individual_performances(data)
        
        if method == WeightAllocationMethod.EQUAL_WEIGHT:
            weights = self._equal_weight_allocation()
        elif method == WeightAllocationMethod.PERFORMANCE_BASED:
            weights = self._performance_based_allocation(individual_performances)
        elif method == WeightAllocationMethod.VOLATILITY_ADJUSTED:
            weights = self._volatility_adjusted_allocation(individual_performances)
        elif method == WeightAllocationMethod.MACHINE_LEARNING:
            weights = self._ml_based_allocation(data, individual_performances)
        elif method == WeightAllocationMethod.DYNAMIC_ADJUSTMENT:
            weights = self._dynamic_adjustment_allocation(data, individual_performances, rebalance_frequency)
        else:
            raise ValueError(f"지원하지 않는 가중치 할당 방법: {method}")
        
        # 조합된 성과 계산
        combined_performance = self._calculate_combined_performance(data, weights, individual_performances)
        
        result = MultiStrategyResult(
            combined_return=combined_performance['total_return'],
            combined_sharpe=combined_performance['sharpe_ratio'],
            combined_max_drawdown=combined_performance['max_drawdown'],
            strategy_weights=weights,
            individual_performances=individual_performances,
            rebalance_history=self.weight_history
        )
        
        self.logger.info(f"포트폴리오 최적화 완료 - 조합 수익률: {combined_performance['total_return']:.2f}%")
        
        return result
    
    def _calculate_individual_performances(self, data: pd.DataFrame) -> Dict[str, StrategyPerformance]:
        """개별 전략 성과 계산"""
        performances = {}
        
        for strategy_id, config in self.strategies.items():
            if not config.enabled:
                continue
            
            try:
                # 전략별 백테스팅 실행
                trades = self._run_strategy_backtest(data, config)
                
                if not trades or len(trades) < 5:
                    self.logger.warning(f"전략 {strategy_id}의 거래 수가 부족합니다.")
                    continue
                
                # 성과 지표 계산
                returns = [trade['return_rate'] for trade in trades]
                total_return = np.prod([1 + r for r in returns]) - 1
                
                if len(returns) > 1:
                    avg_return = np.mean(returns)
                    volatility = np.std(returns)
                    sharpe_ratio = avg_return / volatility * np.sqrt(252) if volatility > 0 else 0
                    
                    # Sortino 비율 (하방 변동성만 고려)
                    downside_returns = [r for r in returns if r < 0]
                    downside_volatility = np.std(downside_returns) if downside_returns else 0
                    sortino_ratio = avg_return / downside_volatility * np.sqrt(252) if downside_volatility > 0 else 0
                else:
                    avg_return = total_return
                    volatility = 0
                    sharpe_ratio = 0
                    sortino_ratio = 0
                
                # 최대 낙폭 계산
                cumulative_returns = np.cumprod([1 + r for r in returns])
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = np.min(drawdown)
                
                # Calmar 비율
                calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
                
                # 승률
                win_rate = len([r for r in returns if r > 0]) / len(returns)
                
                performances[strategy_id] = StrategyPerformance(
                    strategy_type=config.strategy_type,
                    total_return=total_return,
                    sharpe_ratio=sharpe_ratio,
                    max_drawdown=max_drawdown,
                    win_rate=win_rate,
                    total_trades=len(trades),
                    avg_return=avg_return,
                    volatility=volatility,
                    calmar_ratio=calmar_ratio,
                    sortino_ratio=sortino_ratio
                )
                
            except Exception as e:
                self.logger.error(f"전략 {strategy_id} 성과 계산 실패: {e}")
                continue
        
        return performances
    
    def _run_strategy_backtest(self, data: pd.DataFrame, config: StrategyConfig) -> List[Dict[str, Any]]:
        """개별 전략 백테스팅"""
        trades = []
        position = None
        
        if config.strategy_type == StrategyType.VOLATILITY_BREAKOUT:
            trades = self._volatility_breakout_backtest(data, config.parameters)
        elif config.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
            trades = self._ma_crossover_backtest(data, config.parameters)
        elif config.strategy_type == StrategyType.RSI_MEAN_REVERSION:
            trades = self._rsi_mean_reversion_backtest(data, config.parameters)
        elif config.strategy_type == StrategyType.BOLLINGER_BANDS:
            trades = self._bollinger_bands_backtest(data, config.parameters)
        elif config.strategy_type == StrategyType.MOMENTUM:
            trades = self._momentum_backtest(data, config.parameters)
        elif config.strategy_type == StrategyType.MEAN_REVERSION:
            trades = self._mean_reversion_backtest(data, config.parameters)
        
        return trades
    
    def _volatility_breakout_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """변동성 돌파 전략 백테스팅"""
        trades = []
        position = None
        
        for i in range(1, len(data)):
            current_price = data.iloc[i]['close']
            prev_high = data.iloc[i-1]['high']
            prev_low = data.iloc[i-1]['low']
            
            # 매수 조건
            if position is None:
                k = params.get('k', 0.5)
                breakout_line = prev_high + (prev_high - prev_low) * k
                
                if current_price > breakout_line:
                    position = {
                        'entry_price': current_price,
                        'entry_time': i
                    }
            
            # 매도 조건
            elif position is not None:
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                stop_loss = params.get('stop_loss', 0.02)
                take_profit = params.get('take_profit', 0.03)
                
                if return_rate <= -stop_loss or return_rate >= take_profit:
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'return_rate': return_rate,
                        'entry_time': position['entry_time'],
                        'exit_time': i
                    })
                    position = None
        
        return trades
    
    def _ma_crossover_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """이동평균 교차 전략 백테스팅"""
        trades = []
        position = None
        
        short_period = int(params.get('short_period', 5))
        long_period = int(params.get('long_period', 20))
        
        # 이동평균 계산
        short_ma = data['close'].rolling(short_period).mean()
        long_ma = data['close'].rolling(long_period).mean()
        
        for i in range(long_period, len(data)):
            current_price = data.iloc[i]['close']
            
            # 매수 조건 (골든 크로스)
            if position is None:
                if (short_ma.iloc[i] > long_ma.iloc[i] and 
                    short_ma.iloc[i-1] <= long_ma.iloc[i-1]):
                    position = {
                        'entry_price': current_price,
                        'entry_time': i
                    }
            
            # 매도 조건 (데드 크로스)
            elif position is not None:
                if (short_ma.iloc[i] < long_ma.iloc[i] and 
                    short_ma.iloc[i-1] >= long_ma.iloc[i-1]):
                    entry_price = position['entry_price']
                    return_rate = (current_price - entry_price) / entry_price
                    
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'return_rate': return_rate,
                        'entry_time': position['entry_time'],
                        'exit_time': i
                    })
                    position = None
        
        return trades
    
    def _rsi_mean_reversion_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """RSI 평균 회귀 전략 백테스팅"""
        trades = []
        position = None
        
        rsi_period = int(params.get('rsi_period', 14))
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        # RSI 계산
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        for i in range(rsi_period, len(data)):
            current_price = data.iloc[i]['close']
            current_rsi = rsi.iloc[i]
            
            # 매수 조건 (과매도)
            if position is None and current_rsi < oversold:
                position = {
                    'entry_price': current_price,
                    'entry_time': i
                }
            
            # 매도 조건 (과매수)
            elif position is not None and current_rsi > overbought:
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return_rate': return_rate,
                    'entry_time': position['entry_time'],
                    'exit_time': i
                })
                position = None
        
        return trades
    
    def _bollinger_bands_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """볼린저 밴드 전략 백테스팅"""
        trades = []
        position = None
        
        period = int(params.get('period', 20))
        std_dev = params.get('std_dev', 2)
        
        # 볼린저 밴드 계산
        sma = data['close'].rolling(period).mean()
        std = data['close'].rolling(period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        for i in range(period, len(data)):
            current_price = data.iloc[i]['close']
            current_upper = upper_band.iloc[i]
            current_lower = lower_band.iloc[i]
            current_sma = sma.iloc[i]
            
            # 매수 조건 (하단 밴드 터치)
            if position is None and current_price <= current_lower:
                position = {
                    'entry_price': current_price,
                    'entry_time': i
                }
            
            # 매도 조건 (상단 밴드 터치 또는 중간선 복귀)
            elif position is not None and (current_price >= current_upper or current_price >= current_sma):
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return_rate': return_rate,
                    'entry_time': position['entry_time'],
                    'exit_time': i
                })
                position = None
        
        return trades
    
    def _momentum_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """모멘텀 전략 백테스팅"""
        trades = []
        position = None
        
        period = int(params.get('period', 10))
        threshold = params.get('threshold', 0.02)
        
        # 모멘텀 계산
        momentum = data['close'].pct_change(period)
        
        for i in range(period, len(data)):
            current_price = data.iloc[i]['close']
            current_momentum = momentum.iloc[i]
            
            # 매수 조건 (양의 모멘텀)
            if position is None and current_momentum > threshold:
                position = {
                    'entry_price': current_price,
                    'entry_time': i
                }
            
            # 매도 조건 (모멘텀 소실)
            elif position is not None and current_momentum < 0:
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return_rate': return_rate,
                    'entry_time': position['entry_time'],
                    'exit_time': i
                })
                position = None
        
        return trades
    
    def _mean_reversion_backtest(self, data: pd.DataFrame, params: Dict[str, float]) -> List[Dict[str, Any]]:
        """평균 회귀 전략 백테스팅"""
        trades = []
        position = None
        
        period = int(params.get('period', 20))
        threshold = params.get('threshold', 1.5)
        
        # Z-score 계산
        sma = data['close'].rolling(period).mean()
        std = data['close'].rolling(period).std()
        z_score = (data['close'] - sma) / std
        
        for i in range(period, len(data)):
            current_price = data.iloc[i]['close']
            current_z_score = z_score.iloc[i]
            
            # 매수 조건 (음의 Z-score)
            if position is None and current_z_score < -threshold:
                position = {
                    'entry_price': current_price,
                    'entry_time': i
                }
            
            # 매도 조건 (평균 복귀)
            elif position is not None and current_z_score > 0:
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return_rate': return_rate,
                    'entry_time': position['entry_time'],
                    'exit_time': i
                })
                position = None
        
        return trades
    
    def _equal_weight_allocation(self) -> Dict[str, float]:
        """동일 가중치 할당"""
        enabled_strategies = [s for s in self.strategies.values() if s.enabled]
        if not enabled_strategies:
            return {}
        
        weight = 1.0 / len(enabled_strategies)
        return {strategy_id: weight for strategy_id, config in self.strategies.items() if config.enabled}
    
    def _performance_based_allocation(self, performances: Dict[str, StrategyPerformance]) -> Dict[str, float]:
        """성과 기반 가중치 할당"""
        if not performances:
            return self._equal_weight_allocation()
        
        # 샤프 비율 기반 가중치 계산
        sharpe_ratios = {}
        for strategy_id, perf in performances.items():
            sharpe_ratios[strategy_id] = max(0, perf.sharpe_ratio)  # 음수 샤프 비율 제외
        
        total_sharpe = sum(sharpe_ratios.values())
        if total_sharpe == 0:
            return self._equal_weight_allocation()
        
        weights = {}
        for strategy_id, sharpe in sharpe_ratios.items():
            weights[strategy_id] = sharpe / total_sharpe
        
        # 가중치 정규화 및 제약 조건 적용
        weights = self._apply_weight_constraints(weights)
        
        return weights
    
    def _volatility_adjusted_allocation(self, performances: Dict[str, StrategyPerformance]) -> Dict[str, float]:
        """변동성 조정 가중치 할당"""
        if not performances:
            return self._equal_weight_allocation()
        
        # 변동성 역비례 가중치 계산
        inverse_volatilities = {}
        for strategy_id, perf in performances.items():
            if perf.volatility > 0:
                inverse_volatilities[strategy_id] = 1 / perf.volatility
            else:
                inverse_volatilities[strategy_id] = 1
        
        total_inverse_vol = sum(inverse_volatilities.values())
        if total_inverse_vol == 0:
            return self._equal_weight_allocation()
        
        weights = {}
        for strategy_id, inv_vol in inverse_volatilities.items():
            weights[strategy_id] = inv_vol / total_inverse_vol
        
        weights = self._apply_weight_constraints(weights)
        
        return weights
    
    def _ml_based_allocation(self, data: pd.DataFrame, performances: Dict[str, StrategyPerformance]) -> Dict[str, float]:
        """머신러닝 기반 가중치 할당"""
        if not performances:
            return self._equal_weight_allocation()
        
        try:
            # 특성 추출
            features = self._extract_features(data)
            
            if self.ml_model is None:
                # 모델 훈련
                self._train_ml_model(features, performances)
            
            # 예측 기반 가중치 계산
            predictions = self.ml_model.predict(features.iloc[-1:].values.reshape(1, -1))[0]
            
            # 예측값을 가중치로 변환
            weights = {}
            strategy_ids = list(performances.keys())
            
            for i, strategy_id in enumerate(strategy_ids):
                if i < len(predictions):
                    weights[strategy_id] = max(0, predictions[i])
                else:
                    weights[strategy_id] = 0
            
            # 정규화
            total_weight = sum(weights.values())
            if total_weight > 0:
                for strategy_id in weights:
                    weights[strategy_id] /= total_weight
            
            weights = self._apply_weight_constraints(weights)
            
            return weights
            
        except Exception as e:
            self.logger.warning(f"머신러닝 기반 가중치 할당 실패: {e}")
            return self._performance_based_allocation(performances)
    
    def _dynamic_adjustment_allocation(self, 
                                     data: pd.DataFrame, 
                                     performances: Dict[str, StrategyPerformance],
                                     rebalance_frequency: int) -> Dict[str, float]:
        """동적 조정 가중치 할당"""
        if not performances:
            return self._equal_weight_allocation()
        
        # 최근 성과 기반 가중치
        recent_performance_weights = self._performance_based_allocation(performances)
        
        # 시장 상황 분석
        market_features = self._analyze_market_conditions(data)
        
        # 시장 상황에 따른 가중치 조정
        adjusted_weights = {}
        for strategy_id, weight in recent_performance_weights.items():
            strategy_type = self.strategies[strategy_id].strategy_type
            
            # 시장 상황별 가중치 배수
            multiplier = self._get_market_condition_multiplier(strategy_type, market_features)
            adjusted_weights[strategy_id] = weight * multiplier
        
        # 정규화
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            for strategy_id in adjusted_weights:
                adjusted_weights[strategy_id] /= total_weight
        
        weights = self._apply_weight_constraints(adjusted_weights)
        
        # 가중치 이력 저장
        self.weight_history.append({
            'timestamp': datetime.now(),
            'weights': weights.copy(),
            'market_features': market_features
        })
        
        return weights
    
    def _apply_weight_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """가중치 제약 조건 적용"""
        constrained_weights = {}
        
        for strategy_id, weight in weights.items():
            if strategy_id in self.strategies:
                config = self.strategies[strategy_id]
                constrained_weight = max(config.min_weight, min(config.max_weight, weight))
                constrained_weights[strategy_id] = constrained_weight
        
        # 정규화
        total_weight = sum(constrained_weights.values())
        if total_weight > 0:
            for strategy_id in constrained_weights:
                constrained_weights[strategy_id] /= total_weight
        
        return constrained_weights
    
    def _calculate_combined_performance(self, 
                                      data: pd.DataFrame, 
                                      weights: Dict[str, float],
                                      performances: Dict[str, StrategyPerformance]) -> Dict[str, float]:
        """조합된 성과 계산"""
        if not weights or not performances:
            return {'total_return': 0, 'sharpe_ratio': 0, 'max_drawdown': 0}
        
        # 가중 평균 성과 계산
        total_return = sum(weights.get(sid, 0) * perf.total_return 
                          for sid, perf in performances.items())
        
        # 가중 평균 변동성 계산
        total_volatility = np.sqrt(sum(
            (weights.get(sid, 0) * perf.volatility) ** 2
            for sid, perf in performances.items()
        ))
        
        # 샤프 비율 계산
        sharpe_ratio = total_return / total_volatility * np.sqrt(252) if total_volatility > 0 else 0
        
        # 최대 낙폭 (근사치)
        max_drawdown = sum(weights.get(sid, 0) * abs(perf.max_drawdown)
                          for sid, perf in performances.items())
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    
    def _extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """특성 추출"""
        features = pd.DataFrame(index=data.index)
        
        # 가격 관련 특성
        features['price_change'] = data['close'].pct_change()
        features['volatility'] = data['close'].pct_change().rolling(20).std()
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        
        # 기술적 지표
        features['rsi'] = self._calculate_rsi(data['close'], 14)
        features['ma_ratio'] = data['close'] / data['close'].rolling(20).mean()
        
        # 시장 상황
        features['trend'] = (data['close'] > data['close'].rolling(20).mean()).astype(int)
        features['momentum'] = data['close'].pct_change(10)
        
        return features.dropna()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _train_ml_model(self, features: pd.DataFrame, performances: Dict[str, StrategyPerformance]):
        """머신러닝 모델 훈련"""
        try:
            # 타겟 변수 생성 (성과 기반)
            targets = []
            for strategy_id, perf in performances.items():
                # 샤프 비율을 타겟으로 사용
                targets.append(max(0, perf.sharpe_ratio))
            
            if not targets or len(targets) != len(self.strategies):
                return
            
            # 랜덤 포레스트 모델 훈련
            self.ml_model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # 특성과 타겟 준비
            X = features.values
            y = np.array(targets)
            
            if len(X) > 0 and len(y) > 0:
                self.ml_model.fit(X, y)
                
                # 특성 중요도 저장
                self.feature_importance = dict(zip(
                    features.columns, 
                    self.ml_model.feature_importances_
                ))
                
                self.logger.info("머신러닝 모델 훈련 완료")
            
        except Exception as e:
            self.logger.error(f"머신러닝 모델 훈련 실패: {e}")
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """시장 상황 분석"""
        recent_data = data.tail(30)  # 최근 30일 데이터
        
        conditions = {
            'volatility_level': recent_data['close'].pct_change().std(),
            'trend_direction': 1 if recent_data['close'].iloc[-1] > recent_data['close'].iloc[0] else -1,
            'volume_trend': recent_data['volume'].mean() / data['volume'].rolling(60).mean().iloc[-1],
            'price_position': (recent_data['close'].iloc[-1] - recent_data['close'].min()) / 
                            (recent_data['close'].max() - recent_data['close'].min())
        }
        
        return conditions
    
    def _get_market_condition_multiplier(self, strategy_type: StrategyType, market_features: Dict[str, Any]) -> float:
        """시장 상황에 따른 전략별 가중치 배수"""
        multipliers = {
            StrategyType.VOLATILITY_BREAKOUT: 1.0,
            StrategyType.MOVING_AVERAGE_CROSSOVER: 1.0,
            StrategyType.RSI_MEAN_REVERSION: 1.0,
            StrategyType.BOLLINGER_BANDS: 1.0,
            StrategyType.MOMENTUM: 1.0,
            StrategyType.MEAN_REVERSION: 1.0
        }
        
        volatility = market_features.get('volatility_level', 0.02)
        trend = market_features.get('trend_direction', 0)
        
        # 변동성에 따른 조정
        if strategy_type == StrategyType.VOLATILITY_BREAKOUT:
            multipliers[strategy_type] = 1.0 + (volatility - 0.02) * 10
        elif strategy_type == StrategyType.MEAN_REVERSION:
            multipliers[strategy_type] = 1.0 + (0.02 - volatility) * 10
        
        # 추세에 따른 조정
        if strategy_type == StrategyType.MOMENTUM:
            multipliers[strategy_type] = 1.0 + trend * 0.2
        elif strategy_type == StrategyType.MEAN_REVERSION:
            multipliers[strategy_type] = 1.0 - trend * 0.2
        
        return max(0.1, min(2.0, multipliers[strategy_type]))
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """전략 성과 요약"""
        summary = {
            'total_strategies': len(self.strategies),
            'enabled_strategies': len([s for s in self.strategies.values() if s.enabled]),
            'strategy_types': list(set(config.strategy_type.value for config in self.strategies.values())),
            'weight_history_count': len(self.weight_history),
            'performance_history_count': len(self.performance_history)
        }
        
        return summary
    
    def save_strategy_config(self, filename: str = None):
        """전략 설정 저장"""
        if filename is None:
            filename = f"strategy_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        config_data = {
            'strategies': {
                strategy_id: {
                    'strategy_type': config.strategy_type.value,
                    'parameters': config.parameters,
                    'enabled': config.enabled,
                    'min_weight': config.min_weight,
                    'max_weight': config.max_weight,
                    'lookback_period': config.lookback_period
                }
                for strategy_id, config in self.strategies.items()
            },
            'initial_capital': self.initial_capital,
            'created_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"전략 설정 저장 완료: {filename}")

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터 생성
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=365, freq='D')
    prices = 100 + np.cumsum(np.random.randn(365) * 0.02)
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(365) * 0.01),
        'high': prices * (1 + np.abs(np.random.randn(365)) * 0.02),
        'low': prices * (1 - np.abs(np.random.randn(365)) * 0.02),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 365)
    })
    
    # 멀티 전략 매니저 초기화
    manager = MultiStrategyManager(initial_capital=1_000_000)
    
    # 전략 추가
    manager.add_strategy('vb_strategy', StrategyConfig(
        strategy_type=StrategyType.VOLATILITY_BREAKOUT,
        parameters={'k': 0.5, 'stop_loss': 0.02, 'take_profit': 0.03},
        min_weight=0.1,
        max_weight=0.5
    ))
    
    manager.add_strategy('ma_strategy', StrategyConfig(
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        parameters={'short_period': 5, 'long_period': 20},
        min_weight=0.1,
        max_weight=0.5
    ))
    
    manager.add_strategy('rsi_strategy', StrategyConfig(
        strategy_type=StrategyType.RSI_MEAN_REVERSION,
        parameters={'rsi_period': 14, 'oversold': 30, 'overbought': 70},
        min_weight=0.05,
        max_weight=0.3
    ))
    
    # 포트폴리오 최적화 실행
    print("=== 멀티 전략 포트폴리오 최적화 ===")
    
    # 성과 기반 최적화
    result = manager.optimize_portfolio_weights(
        sample_data,
        method=WeightAllocationMethod.PERFORMANCE_BASED
    )
    
    print(f"조합 수익률: {result.combined_return:.2%}")
    print(f"조합 샤프 비율: {result.combined_sharpe:.2f}")
    print(f"조합 최대 낙폭: {result.combined_max_drawdown:.2%}")
    print("\n전략별 가중치:")
    for strategy_id, weight in result.strategy_weights.items():
        print(f"  {strategy_id}: {weight:.2%}")
    
    print("\n개별 전략 성과:")
    for strategy_id, perf in result.individual_performances.items():
        print(f"  {strategy_id}:")
        print(f"    수익률: {perf.total_return:.2%}")
        print(f"    샤프 비율: {perf.sharpe_ratio:.2f}")
        print(f"    승률: {perf.win_rate:.1%}")
        print(f"    거래 수: {perf.total_trades}")
    
    # 동적 조정 최적화
    print("\n=== 동적 조정 최적화 ===")
    dynamic_result = manager.optimize_portfolio_weights(
        sample_data,
        method=WeightAllocationMethod.DYNAMIC_ADJUSTMENT,
        rebalance_frequency=30
    )
    
    print(f"동적 조정 수익률: {dynamic_result.combined_return:.2%}")
    print(f"동적 조정 샤프 비율: {dynamic_result.combined_sharpe:.2f}")
    
    # 요약 정보
    summary = manager.get_strategy_performance_summary()
    print(f"\n=== 전략 요약 ===")
    print(f"총 전략 수: {summary['total_strategies']}")
    print(f"활성 전략 수: {summary['enabled_strategies']}")
    print(f"전략 타입: {summary['strategy_types']}")
    
    # 설정 저장
    manager.save_strategy_config()
