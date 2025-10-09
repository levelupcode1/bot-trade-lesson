#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
암호화폐 자동매매 시스템 최적화 모듈
"""

from .parameter_optimizer import (
    ParameterOptimizer,
    OptimizationMethod,
    ParameterType,
    OptimizationResult,
    StrategyConfig
)

from .multi_strategy_manager import (
    MultiStrategyManager,
    StrategyType,
    WeightAllocationMethod,
    StrategyConfig as MultiStrategyConfig,
    StrategyPerformance,
    MultiStrategyResult
)

from .market_condition_analyzer import (
    MarketConditionAnalyzer,
    MarketRegime,
    VolatilityRegime,
    TrendStrength,
    MarketCondition,
    MarketRegimeTransition,
    OptimizationSignal
)

from .risk_optimizer import (
    RiskOptimizer,
    RiskMetric,
    PositionSizingMethod,
    RiskLimit,
    RiskMetrics,
    PositionSize,
    RiskLimits,
    CorrelationMatrix
)

from .performance_evaluator import (
    PerformanceEvaluator,
    EvaluationMetric,
    BacktestMethod,
    PerformancePeriod,
    TradeRecord,
    PerformanceMetrics,
    BacktestResult
)

__version__ = "1.0.0"
__author__ = "CryptoAutoTrader Team"

__all__ = [
    # 파라미터 최적화
    "ParameterOptimizer",
    "OptimizationMethod", 
    "ParameterType",
    "OptimizationResult",
    "StrategyConfig",
    
    # 멀티 전략 관리
    "MultiStrategyManager",
    "StrategyType",
    "WeightAllocationMethod",
    "MultiStrategyConfig",
    "StrategyPerformance", 
    "MultiStrategyResult",
    
    # 시장 상황 분석
    "MarketConditionAnalyzer",
    "MarketRegime",
    "VolatilityRegime",
    "TrendStrength",
    "MarketCondition",
    "MarketRegimeTransition",
    "OptimizationSignal",
    
    # 리스크 관리
    "RiskOptimizer",
    "RiskMetric",
    "PositionSizingMethod",
    "RiskLimit",
    "RiskMetrics",
    "PositionSize",
    "RiskLimits",
    "CorrelationMatrix",
    
    # 성능 평가
    "PerformanceEvaluator",
    "EvaluationMetric",
    "BacktestMethod",
    "PerformancePeriod",
    "TradeRecord",
    "PerformanceMetrics",
    "BacktestResult"
]
