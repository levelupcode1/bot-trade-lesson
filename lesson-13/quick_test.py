#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 테스트 스크립트

최적화 시스템의 각 모듈이 정상적으로 작동하는지 빠르게 확인합니다.
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def test_imports():
    """모듈 임포트 테스트"""
    print("="*60)
    print("1. 모듈 임포트 테스트")
    print("="*60)
    
    try:
        from src.optimization import (
            ParameterOptimizer,
            MultiStrategyManager,
            MarketConditionAnalyzer,
            RiskOptimizer,
            PerformanceEvaluator
        )
        print("✅ 모든 모듈 임포트 성공!")
        return True
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        return False


def test_parameter_optimizer():
    """파라미터 최적화 테스트"""
    print("\n" + "="*60)
    print("2. 파라미터 최적화 테스트")
    print("="*60)
    
    try:
        from src.optimization import ParameterOptimizer, OptimizationMethod
        
        # 간단한 테스트 데이터 생성
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'open': np.random.uniform(49000000, 51000000, 100),
            'high': np.random.uniform(49500000, 51500000, 100),
            'low': np.random.uniform(48500000, 50500000, 100),
            'close': np.random.uniform(49000000, 51000000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        optimizer = ParameterOptimizer()
        print("✅ ParameterOptimizer 생성 성공!")
        return True
        
    except Exception as e:
        print(f"❌ ParameterOptimizer 테스트 실패: {e}")
        return False


def test_market_analyzer():
    """시장 분석기 테스트"""
    print("\n" + "="*60)
    print("3. 시장 분석기 테스트")
    print("="*60)
    
    try:
        from src.optimization import MarketConditionAnalyzer
        
        # 테스트 데이터
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'open': np.random.uniform(49000000, 51000000, 100),
            'high': np.random.uniform(49500000, 51500000, 100),
            'low': np.random.uniform(48500000, 50500000, 100),
            'close': np.random.uniform(49000000, 51000000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        analyzer = MarketConditionAnalyzer()
        conditions = analyzer.analyze_market_conditions(data)
        
        if conditions:
            condition = conditions[-1]  # 마지막 조건
            print(f"  시장 체제: {condition.market_regime.value}")
            print(f"  변동성 구간: {condition.volatility_regime.value}")
        print("✅ MarketConditionAnalyzer 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ MarketConditionAnalyzer 테스트 실패: {e}")
        return False


def test_multi_strategy_manager():
    """멀티 전략 관리자 테스트"""
    print("\n" + "="*60)
    print("4. 멀티 전략 관리자 테스트")
    print("="*60)
    
    try:
        from src.optimization.multi_strategy_manager import (
            MultiStrategyManager, 
            StrategyType, 
            StrategyConfig
        )
        
        manager = MultiStrategyManager(initial_capital=1_000_000)
        
        # StrategyConfig 객체 생성
        config = StrategyConfig(
            strategy_type=StrategyType.VOLATILITY_BREAKOUT,
            parameters={'k': 0.5, 'stop_loss': 0.02}
        )
        
        manager.add_strategy(
            strategy_id='vb_001',
            config=config
        )
        
        print(f"  추가된 전략 수: {len(manager.strategies)}")
        print("✅ MultiStrategyManager 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ MultiStrategyManager 테스트 실패: {e}")
        return False


def test_risk_optimizer():
    """리스크 최적화 테스트"""
    print("\n" + "="*60)
    print("5. 리스크 최적화 테스트")
    print("="*60)
    
    try:
        from src.optimization.risk_optimizer import (
            RiskOptimizer, 
            PositionSizingMethod,
            RiskLimits
        )
        
        # RiskLimits 생성
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
        
        # 포지션 사이징을 위한 데이터
        expected_returns = {'KRW-BTC': 0.05, 'KRW-ETH': 0.04}
        volatilities = {'KRW-BTC': 0.03, 'KRW-ETH': 0.04}
        correlations = {('KRW-BTC', 'KRW-ETH'): 0.7}
        
        positions = risk_optimizer.optimize_position_sizing(
            expected_returns=expected_returns,
            volatilities=volatilities,
            correlations=correlations,
            method=PositionSizingMethod.EQUAL_WEIGHT
        )
        
        print(f"  최적화된 포지션 수: {len(positions)}")
        for symbol, position in positions.items():
            print(f"  {symbol}: 크기={position.size:.4f}, 금액={position.amount:,.0f}원")
        print("✅ RiskOptimizer 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ RiskOptimizer 테스트 실패: {e}")
        return False


def test_performance_evaluator():
    """성능 평가기 테스트"""
    print("\n" + "="*60)
    print("6. 성능 평가기 테스트")
    print("="*60)
    
    try:
        from src.optimization import PerformanceEvaluator
        from src.optimization.performance_evaluator import TradeRecord
        from datetime import timedelta
        
        evaluator = PerformanceEvaluator()
        
        # 간단한 거래 데이터 생성
        now = datetime.now()
        trades = [
            TradeRecord(
                entry_time=now - timedelta(hours=2),
                exit_time=now,
                symbol='KRW-BTC',
                strategy='test_strategy',
                side='buy',
                quantity=0.01,
                entry_price=50_000_000,
                exit_price=51_000_000,
                pnl=100_000,
                pnl_rate=0.02,
                commission=250,
                slippage=50,
                holding_period=timedelta(hours=2)
            )
        ]
        
        print(f"  테스트 거래 수: {len(trades)}")
        print("✅ PerformanceEvaluator 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ PerformanceEvaluator 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("Lesson 13 최적화 시스템 빠른 테스트")
    print("="*60 + "\n")
    
    results = []
    
    # 각 테스트 실행
    results.append(("모듈 임포트", test_imports()))
    results.append(("파라미터 최적화", test_parameter_optimizer()))
    results.append(("시장 분석기", test_market_analyzer()))
    results.append(("멀티 전략 관리자", test_multi_strategy_manager()))
    results.append(("리스크 최적화", test_risk_optimizer()))
    results.append(("성능 평가기", test_performance_evaluator()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {name}: {status}")
    
    print(f"\n총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트를 통과했습니다!")
        print("다음 명령으로 전체 예제를 실행해보세요:")
        print("  python example_usage.py")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("README.md의 문제 해결 섹션을 참고하세요.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
