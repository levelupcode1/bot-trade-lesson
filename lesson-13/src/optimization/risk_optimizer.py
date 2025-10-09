#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리스크 관리 최적화 모듈
포지션 사이징, 손실 한계, 상관관계 분석을 통한 리스크 최적화
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
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr
import seaborn as sns
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

class RiskMetric(Enum):
    """리스크 지표"""
    VAR = "value_at_risk"  # VaR
    CVAR = "conditional_var"  # CVaR
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"

class PositionSizingMethod(Enum):
    """포지션 사이징 방법"""
    EQUAL_WEIGHT = "equal_weight"
    VOLATILITY_PARITY = "volatility_parity"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    FIXED_FRACTIONAL = "fixed_fractional"
    ADAPTIVE_SIZING = "adaptive_sizing"

class RiskLimit(Enum):
    """리스크 한계"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    WEEKLY_LOSS_LIMIT = "weekly_loss_limit"
    MONTHLY_LOSS_LIMIT = "monthly_loss_limit"
    MAX_POSITION_SIZE = "max_position_size"
    MAX_CORRELATION = "max_correlation"
    MAX_LEVERAGE = "max_leverage"

@dataclass
class RiskMetrics:
    """리스크 지표"""
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # 95% CVaR
    cvar_99: float  # 99% CVaR
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    volatility: float
    skewness: float
    kurtosis: float

@dataclass
class PositionSize:
    """포지션 크기"""
    symbol: str
    weight: float
    dollar_amount: float
    quantity: float
    risk_contribution: float
    expected_return: float
    volatility: float

@dataclass
class RiskLimits:
    """리스크 한계"""
    daily_loss_limit: float = 0.02  # 2%
    weekly_loss_limit: float = 0.05  # 5%
    monthly_loss_limit: float = 0.10  # 10%
    max_position_size: float = 0.20  # 20%
    max_correlation: float = 0.70  # 70%
    max_leverage: float = 1.0  # 100%

@dataclass
class CorrelationMatrix:
    """상관관계 행렬"""
    symbols: List[str]
    correlation_matrix: np.ndarray
    average_correlation: float
    max_correlation: float
    diversification_ratio: float

class RiskOptimizer:
    """리스크 관리 최적화기"""
    
    def __init__(self, 
                 initial_capital: float = 1_000_000,
                 risk_limits: RiskLimits = None):
        self.initial_capital = initial_capital
        self.risk_limits = risk_limits or RiskLimits()
        self.logger = logging.getLogger(__name__)
        
        # 포지션 및 성과 추적
        self.positions: Dict[str, PositionSize] = {}
        self.daily_returns: List[float] = []
        self.portfolio_value_history: List[float] = []
        
        # 리스크 지표 계산 결과
        self.risk_metrics_history: List[RiskMetrics] = []
        self.correlation_matrices: List[CorrelationMatrix] = []
        
        self.logger.info("리스크 최적화기 초기화 완료")
    
    def optimize_position_sizing(self, 
                               expected_returns: Dict[str, float],
                               volatilities: Dict[str, float],
                               correlations: Dict[Tuple[str, str], float],
                               method: PositionSizingMethod = PositionSizingMethod.RISK_PARITY) -> Dict[str, PositionSize]:
        """포지션 사이징 최적화"""
        self.logger.info(f"포지션 사이징 최적화 시작 (방법: {method.value})")
        
        symbols = list(expected_returns.keys())
        
        if method == PositionSizingMethod.EQUAL_WEIGHT:
            weights = self._equal_weight_sizing(symbols)
        elif method == PositionSizingMethod.VOLATILITY_PARITY:
            weights = self._volatility_parity_sizing(symbols, volatilities)
        elif method == PositionSizingMethod.RISK_PARITY:
            weights = self._risk_parity_sizing(symbols, volatilities, correlations)
        elif method == PositionSizingMethod.KELLY_CRITERION:
            weights = self._kelly_criterion_sizing(symbols, expected_returns, volatilities)
        elif method == PositionSizingMethod.FIXED_FRACTIONAL:
            weights = self._fixed_fractional_sizing(symbols, expected_returns, volatilities)
        elif method == PositionSizingMethod.ADAPTIVE_SIZING:
            weights = self._adaptive_sizing(symbols, expected_returns, volatilities, correlations)
        else:
            raise ValueError(f"지원하지 않는 포지션 사이징 방법: {method}")
        
        # 포지션 크기 계산
        positions = self._calculate_position_sizes(
            weights, expected_returns, volatilities, correlations
        )
        
        self.positions = positions
        
        self.logger.info(f"포지션 사이징 최적화 완료: {len(positions)}개 포지션")
        
        return positions
    
    def _equal_weight_sizing(self, symbols: List[str]) -> Dict[str, float]:
        """동일 가중치 사이징"""
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}
    
    def _volatility_parity_sizing(self, symbols: List[str], volatilities: Dict[str, float]) -> Dict[str, float]:
        """변동성 패리티 사이징"""
        inverse_volatilities = {}
        for symbol in symbols:
            if symbol in volatilities and volatilities[symbol] > 0:
                inverse_volatilities[symbol] = 1 / volatilities[symbol]
            else:
                inverse_volatilities[symbol] = 1
        
        total_inverse_vol = sum(inverse_volatilities.values())
        weights = {symbol: inv_vol / total_inverse_vol 
                  for symbol, inv_vol in inverse_volatilities.items()}
        
        return weights
    
    def _risk_parity_sizing(self, 
                          symbols: List[str], 
                          volatilities: Dict[str, float],
                          correlations: Dict[Tuple[str, str], float]) -> Dict[str, float]:
        """리스크 패리티 사이징"""
        n = len(symbols)
        
        # 초기 가중치 (동일 가중치)
        weights = np.array([1.0 / n] * n)
        
        # 상관관계 행렬 구성
        corr_matrix = np.eye(n)
        for i, symbol_i in enumerate(symbols):
            for j, symbol_j in enumerate(symbols):
                if i != j:
                    key = (symbol_i, symbol_j) if (symbol_i, symbol_j) in correlations else (symbol_j, symbol_i)
                    if key in correlations:
                        corr_matrix[i, j] = correlations[key]
        
        # 변동성 벡터
        vols = np.array([volatilities.get(symbol, 0.02) for symbol in symbols])
        
        # 리스크 패리티 최적화
        def risk_parity_objective(w):
            # 포트폴리오 변동성
            portfolio_vol = np.sqrt(w.T @ (vols * corr_matrix * vols.T) @ w)
            
            # 각 자산의 리스크 기여도
            risk_contributions = (w * vols * (corr_matrix @ (vols * w))) / portfolio_vol
            
            # 리스크 기여도의 분산 최소화
            target_contribution = 1.0 / n
            return np.sum((risk_contributions - target_contribution) ** 2)
        
        # 제약 조건
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        bounds = [(0, self.risk_limits.max_position_size) for _ in range(n)]
        
        # 최적화
        result = minimize(
            risk_parity_objective,
            weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            weights = result.x
        else:
            self.logger.warning("리스크 패리티 최적화 실패, 동일 가중치 사용")
            weights = np.array([1.0 / n] * n)
        
        return {symbols[i]: weights[i] for i in range(n)}
    
    def _kelly_criterion_sizing(self, 
                              symbols: List[str],
                              expected_returns: Dict[str, float],
                              volatilities: Dict[str, float]) -> Dict[str, float]:
        """켈리 기준 사이징"""
        weights = {}
        
        for symbol in symbols:
            if symbol in expected_returns and symbol in volatilities:
                expected_return = expected_returns[symbol]
                volatility = volatilities[symbol]
                
                if volatility > 0:
                    # 켈리 비율 계산: f = (μ - r) / σ²
                    kelly_ratio = expected_return / (volatility ** 2)
                    
                    # 켈리 비율을 포지션 크기로 변환 (최대 20%로 제한)
                    position_size = min(kelly_ratio, self.risk_limits.max_position_size)
                    position_size = max(0, position_size)  # 음수 제거
                    
                    weights[symbol] = position_size
                else:
                    weights[symbol] = 0
            else:
                weights[symbol] = 0
        
        # 정규화
        total_weight = sum(weights.values())
        if total_weight > 0:
            for symbol in weights:
                weights[symbol] /= total_weight
        
        return weights
    
    def _fixed_fractional_sizing(self, 
                               symbols: List[str],
                               expected_returns: Dict[str, float],
                               volatilities: Dict[str, float]) -> Dict[str, float]:
        """고정 분수 사이징"""
        weights = {}
        
        for symbol in symbols:
            if symbol in expected_returns and symbol in volatilities:
                expected_return = expected_returns[symbol]
                volatility = volatilities[symbol]
                
                if volatility > 0:
                    # 리스크 조정 수익률 기반 포지션 크기
                    risk_adjusted_return = expected_return / volatility
                    
                    # 포지션 크기 = 리스크 조정 수익률 * 고정 분수 (예: 2%)
                    position_size = risk_adjusted_return * 0.02
                    
                    # 제한 적용
                    position_size = min(position_size, self.risk_limits.max_position_size)
                    position_size = max(0, position_size)
                    
                    weights[symbol] = position_size
                else:
                    weights[symbol] = 0
            else:
                weights[symbol] = 0
        
        # 정규화
        total_weight = sum(weights.values())
        if total_weight > 0:
            for symbol in weights:
                weights[symbol] /= total_weight
        
        return weights
    
    def _adaptive_sizing(self, 
                        symbols: List[str],
                        expected_returns: Dict[str, float],
                        volatilities: Dict[str, float],
                        correlations: Dict[Tuple[str, str], float]) -> Dict[str, float]:
        """적응적 사이징"""
        # 기본 리스크 패리티 가중치
        risk_parity_weights = self._risk_parity_sizing(symbols, volatilities, correlations)
        
        # 수익률 기반 조정
        adjusted_weights = {}
        
        for symbol in symbols:
            base_weight = risk_parity_weights[symbol]
            
            if symbol in expected_returns:
                expected_return = expected_returns[symbol]
                
                # 수익률에 따른 가중치 조정 (최대 ±50%)
                return_multiplier = 1 + (expected_return * 10)  # 10% 수익률 = 100% 가중치 증가
                return_multiplier = max(0.5, min(1.5, return_multiplier))  # 50%-150% 범위
                
                adjusted_weight = base_weight * return_multiplier
            else:
                adjusted_weight = base_weight
            
            adjusted_weights[symbol] = adjusted_weight
        
        # 정규화
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            for symbol in adjusted_weights:
                adjusted_weights[symbol] /= total_weight
        
        return adjusted_weights
    
    def _calculate_position_sizes(self, 
                                weights: Dict[str, float],
                                expected_returns: Dict[str, float],
                                volatilities: Dict[str, float],
                                correlations: Dict[Tuple[str, str], float]) -> Dict[str, PositionSize]:
        """포지션 크기 계산"""
        positions = {}
        
        for symbol, weight in weights.items():
            dollar_amount = self.initial_capital * weight
            
            # 리스크 기여도 계산
            risk_contribution = self._calculate_risk_contribution(
                symbol, weights, volatilities, correlations
            )
            
            position = PositionSize(
                symbol=symbol,
                weight=weight,
                dollar_amount=dollar_amount,
                quantity=0,  # 실제 거래 시 계산
                risk_contribution=risk_contribution,
                expected_return=expected_returns.get(symbol, 0),
                volatility=volatilities.get(symbol, 0)
            )
            
            positions[symbol] = position
        
        return positions
    
    def _calculate_risk_contribution(self, 
                                   symbol: str,
                                   weights: Dict[str, float],
                                   volatilities: Dict[str, float],
                                   correlations: Dict[Tuple[str, str], float]) -> float:
        """리스크 기여도 계산"""
        if symbol not in weights or symbol not in volatilities:
            return 0
        
        symbol_vol = volatilities[symbol]
        symbol_weight = weights[symbol]
        
        # 다른 자산과의 상관관계 고려
        correlation_effect = 0
        for other_symbol, other_weight in weights.items():
            if other_symbol != symbol:
                other_vol = volatilities.get(other_symbol, 0)
                
                # 상관관계 찾기
                corr_key = (symbol, other_symbol) if (symbol, other_symbol) in correlations else (other_symbol, symbol)
                correlation = correlations.get(corr_key, 0)
                
                correlation_effect += other_weight * other_vol * correlation
        
        # 리스크 기여도 = 자산 가중치 * 자산 변동성 * (자산 변동성 + 상관관계 효과)
        risk_contribution = symbol_weight * symbol_vol * (symbol_vol + correlation_effect)
        
        return risk_contribution
    
    def calculate_portfolio_risk_metrics(self, 
                                       returns: pd.Series,
                                       confidence_levels: List[float] = [0.95, 0.99]) -> RiskMetrics:
        """포트폴리오 리스크 지표 계산"""
        if len(returns) < 30:
            self.logger.warning("리스크 지표 계산을 위한 충분한 데이터가 없습니다.")
            return self._get_default_risk_metrics()
        
        # VaR 및 CVaR 계산
        var_95 = np.percentile(returns, (1 - 0.95) * 100)
        var_99 = np.percentile(returns, (1 - 0.99) * 100)
        
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()
        
        # 최대 낙폭 계산
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 샤프 비율
        excess_returns = returns - 0.02 / 252  # 무위험 수익률 가정 (연 2%)
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252)
        
        # Sortino 비율
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns.mean() / downside_volatility * np.sqrt(252) if downside_volatility > 0 else 0
        
        # Calmar 비율
        annual_return = returns.mean() * 252
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 기타 통계
        volatility = returns.std() * np.sqrt(252)
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        risk_metrics = RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            volatility=volatility,
            skewness=skewness,
            kurtosis=kurtosis
        )
        
        return risk_metrics
    
    def analyze_correlations(self, returns_data: Dict[str, pd.Series]) -> CorrelationMatrix:
        """상관관계 분석"""
        symbols = list(returns_data.keys())
        
        if len(symbols) < 2:
            return CorrelationMatrix(
                symbols=symbols,
                correlation_matrix=np.array([[1.0]]),
                average_correlation=0,
                max_correlation=0,
                diversification_ratio=1.0
            )
        
        # 상관관계 행렬 계산
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr().values
        
        # 평균 상관관계 (대각선 제외)
        mask = ~np.eye(correlation_matrix.shape[0], dtype=bool)
        average_correlation = correlation_matrix[mask].mean()
        
        # 최대 상관관계 (대각선 제외)
        max_correlation = correlation_matrix[mask].max()
        
        # 분산화 비율 계산
        # 분산화 비율 = 가중 평균 변동성 / 포트폴리오 변동성
        weights = np.array([1.0 / len(symbols)] * len(symbols))  # 동일 가중치 가정
        individual_volatilities = returns_df.std().values
        
        weighted_avg_volatility = np.sum(weights * individual_volatilities)
        portfolio_volatility = np.sqrt(weights.T @ correlation_matrix @ (individual_volatilities * weights))
        
        diversification_ratio = weighted_avg_volatility / portfolio_volatility if portfolio_volatility > 0 else 1.0
        
        correlation_matrix_obj = CorrelationMatrix(
            symbols=symbols,
            correlation_matrix=correlation_matrix,
            average_correlation=average_correlation,
            max_correlation=max_correlation,
            diversification_ratio=diversification_ratio
        )
        
        self.correlation_matrices.append(correlation_matrix_obj)
        
        return correlation_matrix_obj
    
    def check_risk_limits(self, 
                         current_positions: Dict[str, PositionSize],
                         daily_returns: List[float]) -> Dict[RiskLimit, bool]:
        """리스크 한계 확인"""
        risk_violations = {}
        
        # 일일 손실 한계 확인
        if daily_returns:
            daily_return = daily_returns[-1] if daily_returns else 0
            risk_violations[RiskLimit.DAILY_LOSS_LIMIT] = daily_return < -self.risk_limits.daily_loss_limit
        
        # 주간 손실 한계 확인
        if len(daily_returns) >= 5:
            weekly_return = np.prod([1 + r for r in daily_returns[-5:]]) - 1
            risk_violations[RiskLimit.WEEKLY_LOSS_LIMIT] = weekly_return < -self.risk_limits.weekly_loss_limit
        
        # 월간 손실 한계 확인
        if len(daily_returns) >= 20:
            monthly_return = np.prod([1 + r for r in daily_returns[-20:]]) - 1
            risk_violations[RiskLimit.MONTHLY_LOSS_LIMIT] = monthly_return < -self.risk_limits.monthly_loss_limit
        
        # 최대 포지션 크기 확인
        max_position_violation = any(
            pos.weight > self.risk_limits.max_position_size 
            for pos in current_positions.values()
        )
        risk_violations[RiskLimit.MAX_POSITION_SIZE] = max_position_violation
        
        # 최대 상관관계 확인
        if len(current_positions) >= 2:
            symbols = list(current_positions.keys())
            max_correlation = 0
            
            # 실제 상관관계 계산이 필요한 경우
            # 여기서는 간단히 포지션 크기 기반으로 추정
            weights = [pos.weight for pos in current_positions.values()]
            correlation_estimate = np.var(weights) / (np.mean(weights) ** 2) if np.mean(weights) > 0 else 0
            
            risk_violations[RiskLimit.MAX_CORRELATION] = correlation_estimate > self.risk_limits.max_correlation
        
        return risk_violations
    
    def optimize_risk_budget(self, 
                           expected_returns: Dict[str, float],
                           volatilities: Dict[str, float],
                           correlations: Dict[Tuple[str, str], float],
                           target_volatility: float = 0.15) -> Dict[str, float]:
        """리스크 예산 최적화"""
        self.logger.info(f"리스크 예산 최적화 시작 (목표 변동성: {target_volatility:.1%})")
        
        symbols = list(expected_returns.keys())
        n = len(symbols)
        
        # 상관관계 행렬 구성
        corr_matrix = np.eye(n)
        for i, symbol_i in enumerate(symbols):
            for j, symbol_j in enumerate(symbols):
                if i != j:
                    key = (symbol_i, symbol_j) if (symbol_i, symbol_j) in correlations else (symbol_j, symbol_i)
                    if key in correlations:
                        corr_matrix[i, j] = correlations[key]
        
        # 변동성 벡터
        vols = np.array([volatilities.get(symbol, 0.02) for symbol in symbols])
        
        # 목적 함수: 샤프 비율 최대화
        def objective(w):
            portfolio_return = np.sum(w * np.array([expected_returns.get(symbol, 0) for symbol in symbols]))
            portfolio_vol = np.sqrt(w.T @ (vols * corr_matrix * vols.T) @ w)
            
            if portfolio_vol > 0:
                return -portfolio_return / portfolio_vol  # 최소화를 위해 음수
            else:
                return 1e6
        
        # 제약 조건
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # 가중치 합 = 1
            {'type': 'eq', 'fun': lambda w: np.sqrt(w.T @ (vols * corr_matrix * vols.T) @ w) - target_volatility}  # 목표 변동성
        ]
        
        bounds = [(0, self.risk_limits.max_position_size) for _ in range(n)]
        
        # 초기값 (동일 가중치)
        x0 = np.array([1.0 / n] * n)
        
        # 최적화
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            weights = result.x
            self.logger.info("리스크 예산 최적화 성공")
        else:
            self.logger.warning("리스크 예산 최적화 실패, 동일 가중치 사용")
            weights = np.array([1.0 / n] * n)
        
        return {symbols[i]: weights[i] for i in range(n)}
    
    def _get_default_risk_metrics(self) -> RiskMetrics:
        """기본 리스크 지표 반환"""
        return RiskMetrics(
            var_95=0,
            var_99=0,
            cvar_95=0,
            cvar_99=0,
            max_drawdown=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            volatility=0,
            skewness=0,
            kurtosis=0
        )
    
    def update_portfolio_performance(self, daily_return: float, portfolio_value: float):
        """포트폴리오 성과 업데이트"""
        self.daily_returns.append(daily_return)
        self.portfolio_value_history.append(portfolio_value)
        
        # 리스크 지표 재계산 (30일 이상 데이터가 있을 때)
        if len(self.daily_returns) >= 30:
            returns_series = pd.Series(self.daily_returns)
            risk_metrics = self.calculate_portfolio_risk_metrics(returns_series)
            self.risk_metrics_history.append(risk_metrics)
    
    def get_risk_dashboard(self) -> Dict[str, Any]:
        """리스크 대시보드 데이터"""
        dashboard = {
            "portfolio_summary": {
                "total_positions": len(self.positions),
                "total_capital": self.initial_capital,
                "current_portfolio_value": self.portfolio_value_history[-1] if self.portfolio_value_history else self.initial_capital,
                "total_return": (self.portfolio_value_history[-1] / self.initial_capital - 1) if self.portfolio_value_history else 0
            },
            "risk_limits": {
                "daily_loss_limit": self.risk_limits.daily_loss_limit,
                "weekly_loss_limit": self.risk_limits.weekly_loss_limit,
                "monthly_loss_limit": self.risk_limits.monthly_loss_limit,
                "max_position_size": self.risk_limits.max_position_size,
                "max_correlation": self.risk_limits.max_correlation
            },
            "current_positions": {},
            "risk_violations": {},
            "recent_risk_metrics": None
        }
        
        # 현재 포지션 정보
        for symbol, position in self.positions.items():
            dashboard["current_positions"][symbol] = {
                "weight": position.weight,
                "dollar_amount": position.dollar_amount,
                "risk_contribution": position.risk_contribution,
                "expected_return": position.expected_return,
                "volatility": position.volatility
            }
        
        # 리스크 한계 위반 확인
        if self.daily_returns:
            violations = self.check_risk_limits(self.positions, self.daily_returns)
            dashboard["risk_violations"] = {limit.value: violated for limit, violated in violations.items()}
        
        # 최근 리스크 지표
        if self.risk_metrics_history:
            latest_metrics = self.risk_metrics_history[-1]
            dashboard["recent_risk_metrics"] = {
                "var_95": latest_metrics.var_95,
                "var_99": latest_metrics.var_99,
                "max_drawdown": latest_metrics.max_drawdown,
                "sharpe_ratio": latest_metrics.sharpe_ratio,
                "sortino_ratio": latest_metrics.sortino_ratio,
                "volatility": latest_metrics.volatility
            }
        
        return dashboard
    
    def save_risk_analysis(self, filename: str = None):
        """리스크 분석 결과 저장"""
        if filename is None:
            filename = f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        analysis_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "risk_limits": {
                "daily_loss_limit": self.risk_limits.daily_loss_limit,
                "weekly_loss_limit": self.risk_limits.weekly_loss_limit,
                "monthly_loss_limit": self.risk_limits.monthly_loss_limit,
                "max_position_size": self.risk_limits.max_position_size,
                "max_correlation": self.risk_limits.max_correlation
            },
            "current_positions": {
                symbol: {
                    "weight": pos.weight,
                    "dollar_amount": pos.dollar_amount,
                    "risk_contribution": pos.risk_contribution,
                    "expected_return": pos.expected_return,
                    "volatility": pos.volatility
                }
                for symbol, pos in self.positions.items()
            },
            "risk_metrics_history": [
                {
                    "var_95": metrics.var_95,
                    "var_99": metrics.var_99,
                    "cvar_95": metrics.cvar_95,
                    "cvar_99": metrics.cvar_99,
                    "max_drawdown": metrics.max_drawdown,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "sortino_ratio": metrics.sortino_ratio,
                    "calmar_ratio": metrics.calmar_ratio,
                    "volatility": metrics.volatility,
                    "skewness": metrics.skewness,
                    "kurtosis": metrics.kurtosis
                }
                for metrics in self.risk_metrics_history
            ],
            "correlation_matrices": [
                {
                    "symbols": matrix.symbols,
                    "average_correlation": matrix.average_correlation,
                    "max_correlation": matrix.max_correlation,
                    "diversification_ratio": matrix.diversification_ratio
                }
                for matrix in self.correlation_matrices
            ],
            "dashboard": self.get_risk_dashboard()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"리스크 분석 결과 저장 완료: {filename}")

# 사용 예시
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터 생성
    np.random.seed(42)
    
    # 5개 자산의 수익률 데이터 생성
    symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']
    n_days = 252
    
    returns_data = {}
    expected_returns = {}
    volatilities = {}
    
    for symbol in symbols:
        # 각 자산별로 다른 특성의 수익률 생성
        if symbol == 'BTC':
            returns = np.random.normal(0.001, 0.03, n_days)  # 높은 변동성
        elif symbol == 'ETH':
            returns = np.random.normal(0.0008, 0.035, n_days)  # 매우 높은 변동성
        elif symbol == 'ADA':
            returns = np.random.normal(0.0005, 0.025, n_days)  # 중간 변동성
        elif symbol == 'DOT':
            returns = np.random.normal(0.0003, 0.02, n_days)  # 낮은 변동성
        else:  # LINK
            returns = np.random.normal(0.0004, 0.022, n_days)  # 낮은 변동성
        
        returns_data[symbol] = pd.Series(returns)
        expected_returns[symbol] = np.mean(returns) * 252  # 연간화
        volatilities[symbol] = np.std(returns) * np.sqrt(252)  # 연간화
    
    # 상관관계 생성
    correlations = {}
    for i, symbol1 in enumerate(symbols):
        for j, symbol2 in enumerate(symbols):
            if i != j:
                # 암호화폐 간 상관관계 (0.3-0.7)
                correlation = np.random.uniform(0.3, 0.7)
                correlations[(symbol1, symbol2)] = correlation
    
    # 리스크 최적화기 초기화
    optimizer = RiskOptimizer(
        initial_capital=1_000_000,
        risk_limits=RiskLimits(
            daily_loss_limit=0.02,
            weekly_loss_limit=0.05,
            monthly_loss_limit=0.10,
            max_position_size=0.30,  # 30%로 증가
            max_correlation=0.80
        )
    )
    
    print("=== 리스크 관리 최적화 ===")
    
    # 다양한 포지션 사이징 방법 테스트
    sizing_methods = [
        PositionSizingMethod.EQUAL_WEIGHT,
        PositionSizingMethod.VOLATILITY_PARITY,
        PositionSizingMethod.RISK_PARITY,
        PositionSizingMethod.KELLY_CRITERION,
        PositionSizingMethod.ADAPTIVE_SIZING
    ]
    
    results = {}
    
    for method in sizing_methods:
        print(f"\n--- {method.value} ---")
        
        positions = optimizer.optimize_position_sizing(
            expected_returns, volatilities, correlations, method
        )
        
        # 포지션 정보 출력
        total_weight = 0
        for symbol, position in positions.items():
            print(f"{symbol}: {position.weight:.1%} (리스크 기여도: {position.risk_contribution:.3f})")
            total_weight += position.weight
        
        print(f"총 가중치: {total_weight:.1%}")
        
        # 포트폴리오 리스크 지표 계산
        portfolio_returns = []
        for i in range(n_days):
            daily_return = sum(
                positions[symbol].weight * returns_data[symbol].iloc[i]
                for symbol in symbols
            )
            portfolio_returns.append(daily_return)
        
        portfolio_returns_series = pd.Series(portfolio_returns)
        risk_metrics = optimizer.calculate_portfolio_risk_metrics(portfolio_returns_series)
        
        results[method.value] = {
            'positions': positions,
            'risk_metrics': risk_metrics
        }
        
        print(f"포트폴리오 변동성: {risk_metrics.volatility:.1%}")
        print(f"샤프 비율: {risk_metrics.sharpe_ratio:.2f}")
        print(f"최대 낙폭: {risk_metrics.max_drawdown:.1%}")
        print(f"VaR (95%): {risk_metrics.var_95:.1%}")
    
    # 상관관계 분석
    print(f"\n=== 상관관계 분석 ===")
    correlation_matrix = optimizer.analyze_correlations(returns_data)
    
    print(f"평균 상관관계: {correlation_matrix.average_correlation:.3f}")
    print(f"최대 상관관계: {correlation_matrix.max_correlation:.3f}")
    print(f"분산화 비율: {correlation_matrix.diversification_ratio:.2f}")
    
    # 리스크 예산 최적화
    print(f"\n=== 리스크 예산 최적화 ===")
    target_volatility = 0.15  # 15%
    risk_budget_weights = optimizer.optimize_risk_budget(
        expected_returns, volatilities, correlations, target_volatility
    )
    
    print(f"목표 변동성: {target_volatility:.1%}")
    print("리스크 예산 최적화 결과:")
    for symbol, weight in risk_budget_weights.items():
        print(f"  {symbol}: {weight:.1%}")
    
    # 리스크 한계 확인
    print(f"\n=== 리스크 한계 확인 ===")
    sample_daily_returns = portfolio_returns[:30]  # 최근 30일
    violations = optimizer.check_risk_limits(positions, sample_daily_returns)
    
    for limit, violated in violations.items():
        status = "위반" if violated else "정상"
        print(f"{limit.value}: {status}")
    
    # 리스크 대시보드
    dashboard = optimizer.get_risk_dashboard()
    print(f"\n=== 리스크 대시보드 ===")
    print(f"총 포지션 수: {dashboard['portfolio_summary']['total_positions']}")
    print(f"현재 포트폴리오 가치: {dashboard['portfolio_summary']['current_portfolio_value']:,.0f}원")
    print(f"총 수익률: {dashboard['portfolio_summary']['total_return']:.1%}")
    
    # 분석 결과 저장
    optimizer.save_risk_analysis()
    
    print("\n리스크 관리 최적화 완료!")
