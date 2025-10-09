#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전략 최적화 시스템 실행 예제

이 스크립트는 lesson-13의 최적화 시스템을 실제로 실행하는 예제입니다.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
sys.path.append('.')

from src.optimization import (
    ParameterOptimizer,
    MultiStrategyManager,
    MarketConditionAnalyzer,
    RiskOptimizer,
    PerformanceEvaluator,
    OptimizationMethod,
    StrategyType,
    WeightAllocationMethod,
    PositionSizingMethod,
    BacktestMethod,
    StrategyConfig
)


def generate_sample_data(days: int = 365) -> pd.DataFrame:
    """샘플 가격 데이터 생성"""
    print("샘플 데이터 생성 중...")
    
    # 날짜 범위 생성
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # 랜덤 가격 데이터 생성 (기하 브라운 운동)
    np.random.seed(42)
    returns = np.random.normal(0.0001, 0.02, len(dates))
    price = 50000000  # 시작 가격 5천만원
    prices = [price]
    
    for ret in returns[1:]:
        price = price * (1 + ret)
        prices.append(price)
    
    # OHLCV 데이터 생성
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(dates))
    })
    
    df.set_index('timestamp', inplace=True)
    
    print(f"데이터 생성 완료: {len(df)} 행")
    return df


def example_1_parameter_optimization():
    """예제 1: 파라미터 최적화"""
    print("\n" + "="*60)
    print("예제 1: 파라미터 최적화")
    print("="*60)
    
    # 데이터 생성
    data = generate_sample_data(180)  # 6개월 데이터
    
    # 설정 생성
    config = StrategyConfig(
        initial_capital=1_000_000,
        commission_rate=0.0005,
        slippage_rate=0.0001,
        max_position_size=0.1
    )
    
    # 최적화 엔진 생성
    optimizer = ParameterOptimizer(config)
    
    # Grid Search로 변동성 돌파 전략 최적화
    print("\n1-1. Grid Search로 변동성 돌파 전략 최적화 중...")
    result_grid = optimizer.optimize_volatility_breakout_strategy(
        data=data,
        method=OptimizationMethod.GRID_SEARCH,
        cv_folds=3
    )
    
    print(f"\n[Grid Search 결과]")
    print(f"  최적 k값: {result_grid.best_parameters.get('k', 0):.2f}")
    print(f"  최적 손절: {result_grid.best_parameters.get('stop_loss', 0):.2%}")
    print(f"  최적 익절: {result_grid.best_parameters.get('take_profit', 0):.2%}")
    print(f"  최고 점수: {result_grid.best_score:.2%}")
    print(f"  최적화 시간: {result_grid.optimization_time:.2f}초")
    print(f"  총 반복 횟수: {result_grid.iterations}")
    
    # Genetic Algorithm으로 이동평균 전략 최적화
    print("\n1-2. Genetic Algorithm으로 이동평균 전략 최적화 중...")
    result_ga = optimizer.optimize_ma_crossover_strategy(
        data=data,
        method=OptimizationMethod.GENETIC_ALGORITHM,
        cv_folds=3
    )
    
    print(f"\n[Genetic Algorithm 결과]")
    print(f"  최적 단기 기간: {result_ga.best_parameters.get('short_period', 0):.0f}")
    print(f"  최적 장기 기간: {result_ga.best_parameters.get('long_period', 0):.0f}")
    print(f"  최적 손절: {result_ga.best_parameters.get('stop_loss', 0):.2%}")
    print(f"  최고 점수: {result_ga.best_score:.2%}")
    print(f"  최적화 시간: {result_ga.optimization_time:.2f}초")


def example_2_market_analysis():
    """예제 2: 시장 상황 분석"""
    print("\n" + "="*60)
    print("예제 2: 시장 상황 분석")
    print("="*60)
    
    # 데이터 생성
    data = generate_sample_data(90)  # 3개월 데이터
    
    # 분석기 생성
    analyzer = MarketConditionAnalyzer()
    
    # 시장 상황 분석
    print("\n2-1. 현재 시장 상황 분석 중...")
    conditions = analyzer.analyze_market_conditions(data)
    
    if conditions:
        condition = conditions[-1]  # 마지막 조건 사용
        print(f"\n[시장 상황 분석 결과]")
        print(f"  시장 체제: {condition.market_regime.value}")
        print(f"  변동성 구간: {condition.volatility_regime.value}")
        print(f"  트렌드 강도: {condition.trend_strength.value}")
        print(f"  현재 변동성: {condition.current_volatility:.2%}")
        print(f"  트렌드 점수: {condition.trend_score:.2f}")
    
    # 최적 전략 제안
    print("\n2-2. 최적 전략 제안...")
    signal = analyzer.generate_optimization_signal(data)
    
    print(f"\n[전략 제안]")
    print(f"  추천 전략: {signal.recommended_strategy}")
    print(f"  권장 파라미터: {signal.recommended_params}")
    print(f"  리스크 레벨: {signal.risk_level}")
    print(f"  신뢰도: {signal.confidence:.2%}")


def example_3_multi_strategy():
    """예제 3: 멀티 전략 관리"""
    print("\n" + "="*60)
    print("예제 3: 멀티 전략 관리")
    print("="*60)
    
    # 데이터 생성
    data = generate_sample_data(180)  # 6개월 데이터
    
    # 멀티 전략 관리자 생성
    manager = MultiStrategyManager(
        initial_capital=1_000_000,
        commission_rate=0.0005
    )
    
    # 전략 추가
    print("\n3-1. 전략 추가 중...")
    
    from src.optimization.multi_strategy_manager import StrategyConfig as MSConfig
    
    vb_config = MSConfig(
        strategy_type=StrategyType.VOLATILITY_BREAKOUT,
        parameters={'k': 0.5, 'stop_loss': 0.02, 'take_profit': 0.05}
    )
    manager.add_strategy(strategy_id='vb_001', config=vb_config)
    print("  - 변동성 돌파 전략 추가 완료")
    
    ma_config = MSConfig(
        strategy_type=StrategyType.MA_CROSSOVER,
        parameters={'short_period': 5, 'long_period': 20}
    )
    manager.add_strategy(strategy_id='ma_001', config=ma_config)
    print("  - 이동평균 교차 전략 추가 완료")
    
    # 가중치 최적화
    print("\n3-2. 전략 가중치 최적화 중...")
    weight_result = manager.optimize_weights(
        data=data,
        method=WeightAllocationMethod.RISK_PARITY,
        lookback_period=90
    )
    
    print(f"\n[가중치 최적화 결과]")
    for strategy, weight in weight_result.optimal_weights.items():
        print(f"  {strategy}: {weight:.2%}")
    print(f"  예상 수익률: {weight_result.expected_return:.2%}")
    print(f"  예상 변동성: {weight_result.expected_volatility:.2%}")
    print(f"  샤프 비율: {weight_result.sharpe_ratio:.2f}")
    
    # 백테스트 실행
    print("\n3-3. 멀티 전략 백테스트 실행 중...")
    backtest = manager.run_multi_strategy_backtest(
        data=data,
        rebalance_period=30
    )
    
    print(f"\n[백테스트 결과]")
    print(f"  총 수익률: {backtest.total_return:.2%}")
    print(f"  연간 수익률: {backtest.annual_return:.2%}")
    print(f"  최대 낙폭: {backtest.max_drawdown:.2%}")
    print(f"  샤프 비율: {backtest.sharpe_ratio:.2f}")
    print(f"  승률: {backtest.win_rate:.2%}")


def example_4_risk_optimization():
    """예제 4: 리스크 관리 최적화"""
    print("\n" + "="*60)
    print("예제 4: 리스크 관리 최적화")
    print("="*60)
    
    # 데이터 생성
    data = generate_sample_data(90)
    
    # 리스크 최적화기 생성
    from src.optimization.risk_optimizer import RiskLimits
    
    limits = RiskLimits(
        max_position_size=0.15,
        daily_loss_limit=0.02,
        weekly_loss_limit=0.05,
        monthly_loss_limit=0.10
    )
    
    risk_optimizer = RiskOptimizer(
        initial_capital=1_000_000,
        risk_limits=limits
    )
    
    # 포지션 사이징을 위한 데이터 준비
    print("\n4-1. 포지션 크기 최적화...")
    
    # 예상 수익률과 변동성 계산
    returns = data['close'].pct_change().dropna()
    expected_returns = {
        'KRW-BTC': returns.mean() * 252,  # 연간화
        'KRW-ETH': returns.mean() * 0.8 * 252  # 예시
    }
    volatilities = {
        'KRW-BTC': returns.std() * np.sqrt(252),  # 연간화
        'KRW-ETH': returns.std() * 1.2 * np.sqrt(252)  # 예시
    }
    correlations = {
        ('KRW-BTC', 'KRW-ETH'): 0.7
    }
    
    # Kelly Criterion
    positions_kelly = risk_optimizer.optimize_position_sizing(
        expected_returns=expected_returns,
        volatilities=volatilities,
        correlations=correlations,
        method=PositionSizingMethod.KELLY_CRITERION
    )
    
    print(f"\n[Kelly Criterion]")
    for symbol, position in positions_kelly.items():
        print(f"  {symbol}: 크기={position.size:.4f}, 금액={position.amount:,.0f}원")
    
    # Risk Parity
    positions_parity = risk_optimizer.optimize_position_sizing(
        expected_returns=expected_returns,
        volatilities=volatilities,
        correlations=correlations,
        method=PositionSizingMethod.RISK_PARITY
    )
    
    print(f"\n[Risk Parity]")
    for symbol, position in positions_parity.items():
        print(f"  {symbol}: 크기={position.size:.4f}, 금액={position.amount:,.0f}원")
    
    # 리스크 메트릭 계산
    print("\n4-2. 리스크 메트릭 계산...")
    
    # 포트폴리오 리스크 메트릭 계산
    returns_dict = {
        'KRW-BTC': returns,
        'KRW-ETH': returns * 0.9  # 예시
    }
    
    metrics = risk_optimizer.calculate_portfolio_risk_metrics(
        returns_data=returns_dict,
        weights={'KRW-BTC': 0.6, 'KRW-ETH': 0.4}
    )
    
    print(f"\n[리스크 메트릭]")
    print(f"  VaR (95%): {metrics.var_95:.2%}")
    print(f"  CVaR (95%): {metrics.cvar_95:.2%}")
    print(f"  최대 낙폭: {metrics.max_drawdown:.2%}")
    print(f"  변동성: {metrics.volatility:.2%}")
    print(f"  샤프 비율: {metrics.sharpe_ratio:.2f}")


def example_5_performance_evaluation():
    """예제 5: 성능 평가"""
    print("\n" + "="*60)
    print("예제 5: 성능 평가")
    print("="*60)
    
    # 데이터 생성
    data = generate_sample_data(365)  # 1년 데이터
    
    # 평가기 생성
    evaluator = PerformanceEvaluator()
    
    # 간단한 전략 정의 (변동성 돌파)
    class SimpleStrategy:
        def __init__(self):
            self.k = 0.5
            self.stop_loss = 0.02
            self.take_profit = 0.05
        
        def generate_signals(self, data):
            # 간단한 시그널 생성
            signals = pd.Series(0, index=data.index)
            volatility = data['close'].pct_change().rolling(20).std()
            
            for i in range(20, len(data)):
                if data['close'].iloc[i] > data['close'].iloc[i-1] * (1 + volatility.iloc[i] * self.k):
                    signals.iloc[i] = 1  # 매수
                elif data['close'].iloc[i] < data['close'].iloc[i-1] * (1 - volatility.iloc[i] * self.k):
                    signals.iloc[i] = -1  # 매도
            
            return signals
    
    strategy = SimpleStrategy()
    
    # 백테스트 실행
    print("\n5-1. Walk-Forward 백테스트 실행 중...")
    backtest_result = evaluator.run_backtest(
        strategy=strategy,
        data=data,
        method=BacktestMethod.WALK_FORWARD,
        train_period=180,
        test_period=30
    )
    
    print(f"\n[백테스트 결과]")
    print(f"  총 거래 수: {len(backtest_result.trades)}")
    print(f"  승리 거래: {sum(1 for t in backtest_result.trades if t.profit > 0)}")
    print(f"  손실 거래: {sum(1 for t in backtest_result.trades if t.profit < 0)}")
    
    # 성능 메트릭 계산
    print("\n5-2. 성능 메트릭 계산 중...")
    metrics = evaluator.calculate_performance_metrics(
        trades=backtest_result.trades,
        equity_curve=backtest_result.equity_curve
    )
    
    print(f"\n[성능 메트릭]")
    print(f"\n수익률 지표:")
    print(f"  총 수익률: {metrics.total_return:.2%}")
    print(f"  연간 수익률: {metrics.annual_return:.2%}")
    print(f"  월간 평균 수익률: {metrics.monthly_return:.2%}")
    
    print(f"\n리스크 지표:")
    print(f"  최대 낙폭: {metrics.max_drawdown:.2%}")
    print(f"  변동성: {metrics.volatility:.2%}")
    print(f"  VaR (95%): {metrics.var_95:.2%}")
    
    print(f"\n효율성 지표:")
    print(f"  샤프 비율: {metrics.sharpe_ratio:.2f}")
    print(f"  소르티노 비율: {metrics.sortino_ratio:.2f}")
    print(f"  칼마 비율: {metrics.calmar_ratio:.2f}")
    
    print(f"\n안정성 지표:")
    print(f"  승률: {metrics.win_rate:.2%}")
    print(f"  수익 팩터: {metrics.profit_factor:.2f}")
    print(f"  평균 승리/손실: {metrics.avg_win_loss_ratio:.2f}")


def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("Lesson 13: 전략 최적화 시스템 예제")
    print("="*60)
    
    try:
        # 예제 1: 파라미터 최적화
        example_1_parameter_optimization()
        
        # 예제 2: 시장 상황 분석
        example_2_market_analysis()
        
        # 예제 3: 멀티 전략 관리
        example_3_multi_strategy()
        
        # 예제 4: 리스크 관리 최적화
        example_4_risk_optimization()
        
        # 예제 5: 성능 평가
        example_5_performance_evaluation()
        
        print("\n" + "="*60)
        print("모든 예제 실행 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

