#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파라미터 최적화 엔진
변동성 돌파 전략, 이동평균 전략의 핵심 파라미터를 자동으로 최적화
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from datetime import datetime, timedelta
import json
import warnings
from scipy.optimize import minimize, differential_evolution
from sklearn.model_selection import TimeSeriesSplit
import itertools

warnings.filterwarnings('ignore')

class OptimizationMethod(Enum):
    """최적화 방법"""
    GRID_SEARCH = "grid_search"
    GENETIC_ALGORITHM = "genetic_algorithm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    ADAPTIVE_OPTIMIZATION = "adaptive_optimization"

class ParameterType(Enum):
    """파라미터 타입"""
    VOLATILITY_BREAKOUT_K = "volatility_breakout_k"
    MOVING_AVERAGE_SHORT = "ma_short"
    MOVING_AVERAGE_LONG = "ma_long"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    POSITION_SIZE = "position_size"

@dataclass
class ParameterRange:
    """파라미터 범위 정의"""
    min_value: float
    max_value: float
    step: float = None
    param_type: ParameterType = None
    
    def __post_init__(self):
        if self.step is None:
            self.step = (self.max_value - self.min_value) / 20

@dataclass
class OptimizationResult:
    """최적화 결과"""
    best_parameters: Dict[str, float]
    best_score: float
    optimization_time: float
    method: OptimizationMethod
    iterations: int
    convergence_history: List[float] = field(default_factory=list)
    parameter_history: List[Dict[str, float]] = field(default_factory=list)

@dataclass
class StrategyConfig:
    """전략 설정"""
    initial_capital: float = 1_000_000
    commission_rate: float = 0.0005  # 0.05%
    slippage_rate: float = 0.0001   # 0.01%
    max_position_size: float = 0.1  # 10%
    min_trade_size: float = 10000   # 1만원

class ParameterOptimizer:
    """파라미터 최적화 엔진"""
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        self.logger = logging.getLogger(__name__)
        
        # 파라미터 범위 정의
        self.parameter_ranges = {
            ParameterType.VOLATILITY_BREAKOUT_K: ParameterRange(0.2, 1.0, 0.05),
            ParameterType.MOVING_AVERAGE_SHORT: ParameterRange(3, 15, 1),
            ParameterType.MOVING_AVERAGE_LONG: ParameterRange(15, 50, 1),
            ParameterType.STOP_LOSS: ParameterRange(0.005, 0.05, 0.005),
            ParameterType.TAKE_PROFIT: ParameterRange(0.01, 0.1, 0.01),
            ParameterType.POSITION_SIZE: ParameterRange(0.02, 0.15, 0.01)
        }
        
        # 최적화 결과 저장
        self.optimization_history = []
        
        self.logger.info("파라미터 최적화 엔진 초기화 완료")
    
    def optimize_volatility_breakout_strategy(self, 
                                            data: pd.DataFrame, 
                                            method: OptimizationMethod = OptimizationMethod.GRID_SEARCH,
                                            cv_folds: int = 5) -> OptimizationResult:
        """변동성 돌파 전략 파라미터 최적화"""
        self.logger.info("변동성 돌파 전략 파라미터 최적화 시작")
        
        start_time = datetime.now()
        
        # 최적화할 파라미터 정의
        parameters_to_optimize = [
            ParameterType.VOLATILITY_BREAKOUT_K,
            ParameterType.STOP_LOSS,
            ParameterType.TAKE_PROFIT,
            ParameterType.POSITION_SIZE
        ]
        
        if method == OptimizationMethod.GRID_SEARCH:
            result = self._grid_search_optimization(data, parameters_to_optimize, cv_folds)
        elif method == OptimizationMethod.GENETIC_ALGORITHM:
            result = self._genetic_algorithm_optimization(data, parameters_to_optimize)
        elif method == OptimizationMethod.ADAPTIVE_OPTIMIZATION:
            result = self._adaptive_optimization(data, parameters_to_optimize)
        else:
            raise ValueError(f"지원하지 않는 최적화 방법: {method}")
        
        result.optimization_time = (datetime.now() - start_time).total_seconds()
        result.method = method
        
        self.optimization_history.append(result)
        self.logger.info(f"변동성 돌파 전략 최적화 완료: {result.best_score:.4f}")
        
        return result
    
    def optimize_moving_average_strategy(self, 
                                       data: pd.DataFrame, 
                                       method: OptimizationMethod = OptimizationMethod.GRID_SEARCH,
                                       cv_folds: int = 5) -> OptimizationResult:
        """이동평균 전략 파라미터 최적화"""
        self.logger.info("이동평균 전략 파라미터 최적화 시작")
        
        start_time = datetime.now()
        
        # 최적화할 파라미터 정의
        parameters_to_optimize = [
            ParameterType.MOVING_AVERAGE_SHORT,
            ParameterType.MOVING_AVERAGE_LONG,
            ParameterType.STOP_LOSS,
            ParameterType.TAKE_PROFIT,
            ParameterType.POSITION_SIZE
        ]
        
        if method == OptimizationMethod.GRID_SEARCH:
            result = self._grid_search_optimization(data, parameters_to_optimize, cv_folds)
        elif method == OptimizationMethod.GENETIC_ALGORITHM:
            result = self._genetic_algorithm_optimization(data, parameters_to_optimize)
        elif method == OptimizationMethod.ADAPTIVE_OPTIMIZATION:
            result = self._adaptive_optimization(data, parameters_to_optimize)
        else:
            raise ValueError(f"지원하지 않는 최적화 방법: {method}")
        
        result.optimization_time = (datetime.now() - start_time).total_seconds()
        result.method = method
        
        self.optimization_history.append(result)
        self.logger.info(f"이동평균 전략 최적화 완료: {result.best_score:.4f}")
        
        return result
    
    def _grid_search_optimization(self, 
                                 data: pd.DataFrame, 
                                 parameters: List[ParameterType],
                                 cv_folds: int) -> OptimizationResult:
        """그리드 서치 최적화"""
        self.logger.info("그리드 서치 최적화 시작")
        
        # 파라미터 조합 생성
        param_combinations = self._generate_parameter_combinations(parameters)
        
        best_score = -float('inf')
        best_parameters = {}
        convergence_history = []
        parameter_history = []
        
        total_combinations = len(param_combinations)
        self.logger.info(f"총 {total_combinations}개 파라미터 조합 테스트")
        
        for i, param_combo in enumerate(param_combinations):
            try:
                # 교차 검증으로 성능 평가
                cv_scores = self._cross_validate_parameters(data, param_combo, cv_folds)
                avg_score = np.mean(cv_scores)
                
                convergence_history.append(avg_score)
                parameter_history.append(param_combo.copy())
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_parameters = param_combo.copy()
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"진행률: {i+1}/{total_combinations} ({((i+1)/total_combinations)*100:.1f}%)")
                    
            except Exception as e:
                self.logger.warning(f"파라미터 조합 {param_combo} 평가 실패: {e}")
                continue
        
        return OptimizationResult(
            best_parameters=best_parameters,
            best_score=best_score,
            optimization_time=0,  # 나중에 설정
            method=OptimizationMethod.GRID_SEARCH,
            iterations=total_combinations,
            convergence_history=convergence_history,
            parameter_history=parameter_history
        )
    
    def _genetic_algorithm_optimization(self, 
                                      data: pd.DataFrame, 
                                      parameters: List[ParameterType]) -> OptimizationResult:
        """유전 알고리즘 최적화"""
        self.logger.info("유전 알고리즘 최적화 시작")
        
        # 파라미터 범위 정의
        bounds = []
        param_names = []
        
        for param_type in parameters:
            param_range = self.parameter_ranges[param_type]
            bounds.append([param_range.min_value, param_range.max_value])
            param_names.append(param_type.value)
        
        def objective_function(params):
            """목적 함수 (최소화를 위해 음수 반환)"""
            try:
                param_dict = dict(zip(param_names, params))
                # 파라미터 검증
                if not self._validate_parameters(param_dict, parameters):
                    return float('inf')
                
                score = self._evaluate_parameters(data, param_dict)
                return -score  # 최소화를 위해 음수 반환
                
            except Exception as e:
                self.logger.warning(f"파라미터 평가 실패: {e}")
                return float('inf')
        
        # 유전 알고리즘 실행
        result = differential_evolution(
            objective_function,
            bounds,
            maxiter=100,
            popsize=15,
            seed=42,
            workers=-1  # 모든 CPU 코어 사용
        )
        
        best_parameters = dict(zip(param_names, result.x))
        best_score = -result.fun
        
        return OptimizationResult(
            best_parameters=best_parameters,
            best_score=best_score,
            optimization_time=0,  # 나중에 설정
            method=OptimizationMethod.GENETIC_ALGORITHM,
            iterations=result.nit,
            convergence_history=[]
        )
    
    def _adaptive_optimization(self, 
                             data: pd.DataFrame, 
                             parameters: List[ParameterType]) -> OptimizationResult:
        """적응적 최적화 (시장 상황별 파라미터 조정)"""
        self.logger.info("적응적 최적화 시작")
        
        # 시장 상황 분석
        market_conditions = self._analyze_market_conditions(data)
        
        best_score = -float('inf')
        best_parameters = {}
        
        # 각 시장 상황별로 최적화
        for condition_name, condition_data in market_conditions.items():
            self.logger.info(f"시장 상황 '{condition_name}' 최적화 중...")
            
            # 해당 시장 상황에서 최적 파라미터 찾기
            condition_result = self._grid_search_optimization(
                condition_data, parameters, cv_folds=3
            )
            
            if condition_result.best_score > best_score:
                best_score = condition_result.best_score
                best_parameters = condition_result.best_parameters.copy()
        
        return OptimizationResult(
            best_parameters=best_parameters,
            best_score=best_score,
            optimization_time=0,  # 나중에 설정
            method=OptimizationMethod.ADAPTIVE_OPTIMIZATION,
            iterations=len(market_conditions),
            convergence_history=[]
        )
    
    def _generate_parameter_combinations(self, parameters: List[ParameterType]) -> List[Dict[str, float]]:
        """파라미터 조합 생성"""
        param_values = {}
        
        for param_type in parameters:
            param_range = self.parameter_ranges[param_type]
            if param_type in [ParameterType.MOVING_AVERAGE_SHORT, ParameterType.MOVING_AVERAGE_LONG]:
                # 정수 값으로 생성
                values = list(range(int(param_range.min_value), int(param_range.max_value) + 1, int(param_range.step)))
            else:
                # 실수 값으로 생성
                values = np.arange(param_range.min_value, param_range.max_value + param_range.step, param_range.step)
            
            param_values[param_type.value] = values
        
        # 조합 생성
        combinations = []
        for combo in itertools.product(*param_values.values()):
            param_dict = dict(zip(param_values.keys(), combo))
            
            # 이동평균 파라미터 검증 (단기 < 장기)
            if (ParameterType.MOVING_AVERAGE_SHORT.value in param_dict and 
                ParameterType.MOVING_AVERAGE_LONG.value in param_dict):
                if param_dict[ParameterType.MOVING_AVERAGE_SHORT.value] >= param_dict[ParameterType.MOVING_AVERAGE_LONG.value]:
                    continue
            
            # 손절/익절 비율 검증 (익절 > 손절 * 1.5)
            if (ParameterType.STOP_LOSS.value in param_dict and 
                ParameterType.TAKE_PROFIT.value in param_dict):
                if param_dict[ParameterType.TAKE_PROFIT.value] <= param_dict[ParameterType.STOP_LOSS.value] * 1.5:
                    continue
            
            combinations.append(param_dict)
        
        return combinations
    
    def _cross_validate_parameters(self, 
                                  data: pd.DataFrame, 
                                  parameters: Dict[str, float], 
                                  cv_folds: int) -> List[float]:
        """교차 검증으로 파라미터 평가"""
        # 시계열 교차 검증
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        scores = []
        
        for train_idx, test_idx in tscv.split(data):
            train_data = data.iloc[train_idx].copy()
            test_data = data.iloc[test_idx].copy()
            
            try:
                score = self._evaluate_parameters(test_data, parameters)
                scores.append(score)
            except Exception as e:
                self.logger.warning(f"교차 검증 평가 실패: {e}")
                scores.append(0)
        
        return scores
    
    def _evaluate_parameters(self, data: pd.DataFrame, parameters: Dict[str, float]) -> float:
        """파라미터 평가 (샤프 비율 기반)"""
        try:
            # 백테스팅 실행
            trades = self._run_backtest(data, parameters)
            
            if not trades or len(trades) < 10:  # 최소 거래 수 확인
                return 0
            
            # 성과 지표 계산
            returns = [trade['return_rate'] for trade in trades]
            total_return = np.prod([1 + r for r in returns]) - 1
            
            if len(returns) > 1:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # 연간화
            else:
                sharpe_ratio = 0
            
            # 승률 계산
            win_rate = len([r for r in returns if r > 0]) / len(returns)
            
            # 최대 낙폭 계산
            cumulative_returns = np.cumprod([1 + r for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # 종합 점수 계산 (샤프 비율 60%, 승률 25%, 최대 낙폭 15%)
            composite_score = (
                sharpe_ratio * 0.6 +
                win_rate * 0.25 +
                (1 + max_drawdown) * 0.15  # 낙폭이 작을수록 높은 점수
            )
            
            return composite_score
            
        except Exception as e:
            self.logger.warning(f"파라미터 평가 실패: {e}")
            return 0
    
    def _run_backtest(self, data: pd.DataFrame, parameters: Dict[str, float]) -> List[Dict[str, Any]]:
        """백테스팅 실행"""
        trades = []
        position = None
        capital = self.config.initial_capital
        
        for i in range(1, len(data)):
            current_price = data.iloc[i]['close']
            prev_high = data.iloc[i-1]['high']
            prev_low = data.iloc[i-1]['low']
            
            # 매수 조건 확인
            if position is None:
                # 변동성 돌파 전략
                if 'volatility_breakout_k' in parameters:
                    k = parameters['volatility_breakout_k']
                    breakout_line = prev_high + (prev_high - prev_low) * k
                    
                    if current_price > breakout_line:
                        # 포지션 진입
                        position_size = capital * parameters.get('position_size', 0.05)
                        quantity = position_size / current_price
                        
                        position = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'entry_time': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                            'capital_used': position_size
                        }
                
                # 이동평균 전략
                elif 'ma_short' in parameters and 'ma_long' in parameters:
                    short_ma = data['close'].rolling(parameters['ma_short']).mean().iloc[i]
                    long_ma = data['close'].rolling(parameters['ma_long']).mean().iloc[i]
                    prev_short_ma = data['close'].rolling(parameters['ma_short']).mean().iloc[i-1]
                    prev_long_ma = data['close'].rolling(parameters['ma_long']).mean().iloc[i-1]
                    
                    # 골든 크로스 (단기선이 장기선을 상향 돌파)
                    if (short_ma > long_ma and prev_short_ma <= prev_long_ma):
                        position_size = capital * parameters.get('position_size', 0.05)
                        quantity = position_size / current_price
                        
                        position = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'entry_time': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                            'capital_used': position_size
                        }
            
            # 매도 조건 확인
            if position is not None:
                entry_price = position['entry_price']
                return_rate = (current_price - entry_price) / entry_price
                
                stop_loss = parameters.get('stop_loss', 0.02)
                take_profit = parameters.get('take_profit', 0.03)
                
                should_exit = False
                exit_reason = ""
                
                if return_rate <= -stop_loss:
                    should_exit = True
                    exit_reason = "stop_loss"
                elif return_rate >= take_profit:
                    should_exit = True
                    exit_reason = "take_profit"
                
                if should_exit:
                    # 거래 완료
                    trade = {
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'return_rate': return_rate,
                        'exit_reason': exit_reason,
                        'capital_used': position['capital_used']
                    }
                    trades.append(trade)
                    
                    # 자본 업데이트
                    capital = capital * (1 + return_rate)
                    position = None
        
        return trades
    
    def _validate_parameters(self, parameters: Dict[str, float], param_types: List[ParameterType]) -> bool:
        """파라미터 유효성 검증"""
        try:
            for param_type in param_types:
                if param_type.value not in parameters:
                    return False
                
                value = parameters[param_type.value]
                param_range = self.parameter_ranges[param_type]
                
                if not (param_range.min_value <= value <= param_range.max_value):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """시장 상황 분석 및 데이터 분할"""
        conditions = {}
        
        # 변동성 기반 분할
        returns = data['close'].pct_change().dropna()
        volatility = returns.rolling(20).std()
        
        low_vol_mask = volatility <= volatility.quantile(0.33)
        high_vol_mask = volatility >= volatility.quantile(0.67)
        
        if low_vol_mask.any():
            conditions['low_volatility'] = data[low_vol_mask]
        if high_vol_mask.any():
            conditions['high_volatility'] = data[high_vol_mask]
        
        # 추세 기반 분할
        short_ma = data['close'].rolling(10).mean()
        long_ma = data['close'].rolling(30).mean()
        
        uptrend_mask = short_ma > long_ma
        downtrend_mask = short_ma < long_ma
        
        if uptrend_mask.any():
            conditions['uptrend'] = data[uptrend_mask]
        if downtrend_mask.any():
            conditions['downtrend'] = data[downtrend_mask]
        
        return conditions
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """최적화 요약 정보 반환"""
        if not self.optimization_history:
            return {"message": "최적화 이력이 없습니다."}
        
        summary = {
            "total_optimizations": len(self.optimization_history),
            "best_results": [],
            "optimization_methods": {},
            "average_optimization_time": 0
        }
        
        total_time = 0
        method_counts = {}
        
        for result in self.optimization_history:
            total_time += result.optimization_time
            method_name = result.method.value
            
            if method_name not in method_counts:
                method_counts[method_name] = 0
            method_counts[method_name] += 1
            
            summary["best_results"].append({
                "method": method_name,
                "score": result.best_score,
                "time": result.optimization_time,
                "iterations": result.iterations
            })
        
        summary["optimization_methods"] = method_counts
        summary["average_optimization_time"] = total_time / len(self.optimization_history)
        
        return summary
    
    def save_optimization_results(self, filename: str = None):
        """최적화 결과 저장"""
        if filename is None:
            filename = f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = {
            "optimization_history": [
                {
                    "best_parameters": result.best_parameters,
                    "best_score": result.best_score,
                    "optimization_time": result.optimization_time,
                    "method": result.method.value,
                    "iterations": result.iterations
                }
                for result in self.optimization_history
            ],
            "parameter_ranges": {
                param_type.value: {
                    "min": param_range.min_value,
                    "max": param_range.max_value,
                    "step": param_range.step
                }
                for param_type, param_range in self.parameter_ranges.items()
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"최적화 결과 저장 완료: {filename}")

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
    
    # 최적화 엔진 초기화
    optimizer = ParameterOptimizer()
    
    # 변동성 돌파 전략 최적화
    print("=== 변동성 돌파 전략 최적화 ===")
    vb_result = optimizer.optimize_volatility_breakout_strategy(
        sample_data, 
        method=OptimizationMethod.GRID_SEARCH
    )
    
    print(f"최적 파라미터: {vb_result.best_parameters}")
    print(f"최적 점수: {vb_result.best_score:.4f}")
    print(f"최적화 시간: {vb_result.optimization_time:.2f}초")
    
    # 이동평균 전략 최적화
    print("\n=== 이동평균 전략 최적화 ===")
    ma_result = optimizer.optimize_moving_average_strategy(
        sample_data,
        method=OptimizationMethod.GRID_SEARCH
    )
    
    print(f"최적 파라미터: {ma_result.best_parameters}")
    print(f"최적 점수: {ma_result.best_score:.4f}")
    print(f"최적화 시간: {ma_result.optimization_time:.2f}초")
    
    # 최적화 요약
    summary = optimizer.get_optimization_summary()
    print(f"\n=== 최적화 요약 ===")
    print(f"총 최적화 횟수: {summary['total_optimizations']}")
    print(f"평균 최적화 시간: {summary['average_optimization_time']:.2f}초")
    
    # 결과 저장
    optimizer.save_optimization_results()
