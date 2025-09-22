#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 백테스트 사용 예제 - 최적화 버전
"""

import pandas as pd
import numpy as np
from volatility_breakout_backtest_optimized import VolatilityBreakoutBacktest, create_sample_data

def main():
    """백테스트 실행 예제"""
    
    print("="*60)
    print("변동성 돌파 전략 백테스트 예제 - 최적화 버전")
    print("="*60)
    
    # 1. 샘플 데이터 생성
    print("\n1. 데이터 생성 중...")
    data = create_sample_data('2023-01-01', '2023-12-31')
    print(f"데이터 생성 완료: {len(data)}개 레코드")
    print(f"기간: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")
    
    # 2. 백테스트 설정
    print("\n2. 백테스트 설정")
    backtest = VolatilityBreakoutBacktest(
        k_value=0.7,           # K값
        stop_loss=-0.015,      # 손절 -1.5%
        take_profit=0.025,     # 익절 +2.5%
        position_size=0.05,    # 포지션 크기 5%
        volume_filter=1.5,     # 거래량 필터 1.5배
        rsi_threshold=30,      # RSI 임계값 30
        max_holding_days=2,    # 최대 보유 2일
        transaction_cost=0.001 # 거래 비용 0.1%
    )
    
    # 3. 데이터 로딩
    print("\n3. 데이터 로딩 중...")
    backtest.load_data(data)
    
    # 4. 백테스트 실행
    print("\n4. 백테스트 실행 중...")
    results = backtest.run_backtest()
    
    # 5. 결과 출력
    print("\n5. 백테스트 결과")
    backtest.print_performance()
    
    # 6. 차트 생성
    print("\n6. 차트 생성 중...")
    backtest.plot_results('backtest_results_optimized.png')
    
    # 7. 거래 내역 상세 정보
    if results['trades']:
        print("\n7. 거래 내역 상세")
        trades_df = backtest.get_trade_summary()
        print(trades_df.head(10))
        
        # 8. 매개변수 최적화 예제
        print("\n8. 매개변수 최적화 예제")
        print("최적화 중... (시간이 걸릴 수 있습니다)")
        
        optimization_results = backtest.optimize_parameters(
            k_values=[0.6, 0.7, 0.8],
            stop_losses=[-0.01, -0.015, -0.02],
            take_profits=[0.02, 0.025, 0.03]
        )
        
        if optimization_results['best_params']:
            print("\n최적 매개변수:")
            for param, value in optimization_results['best_params'].items():
                print(f"  {param}: {value}")
            
            print("\n최적 성과:")
            best_perf = optimization_results['best_performance']
            print(f"  총 수익률: {best_perf['total_return_pct']:.2f}%")
            print(f"  샤프 비율: {best_perf['sharpe_ratio']:.2f}")
            print(f"  최대 낙폭: {best_perf['max_drawdown_pct']:.2f}%")
            print(f"  승률: {best_perf['win_rate']:.1%}")
    
    print("\n백테스트 완료!")

def test_with_real_data():
    """실제 데이터로 테스트하는 예제"""
    print("\n" + "="*60)
    print("실제 데이터 테스트 예제")
    print("="*60)
    
    # 실제 데이터 파일이 있는 경우 사용
    # data = pd.read_csv('bitcoin_data.csv', index_col=0, parse_dates=True)
    
    # 샘플 데이터로 대체
    data = create_sample_data('2022-01-01', '2023-12-31', base_price=30000000, volatility=0.03)
    
    # 다양한 전략 설정으로 테스트
    strategies = [
        {
            'name': '보수적 전략',
            'params': {
                'k_value': 0.5,
                'stop_loss': -0.01,
                'take_profit': 0.02,
                'position_size': 0.03,
                'volume_filter': 1.0,
                'rsi_threshold': 40,
                'max_holding_days': 3
            }
        },
        {
            'name': '공격적 전략',
            'params': {
                'k_value': 0.8,
                'stop_loss': -0.02,
                'take_profit': 0.03,
                'position_size': 0.08,
                'volume_filter': 1.0,
                'rsi_threshold': 50,
                'max_holding_days': 1
            }
        },
        {
            'name': '균형 전략',
            'params': {
                'k_value': 0.7,
                'stop_loss': -0.015,
                'take_profit': 0.025,
                'position_size': 0.05,
                'volume_filter': 1.5,
                'rsi_threshold': 30,
                'max_holding_days': 2
            }
        }
    ]
    
    results_comparison = []
    
    for strategy in strategies:
        print(f"\n{strategy['name']} 테스트 중...")
        
        backtest = VolatilityBreakoutBacktest(**strategy['params'])
        backtest.load_data(data)
        results = backtest.run_backtest()
        
        performance = results['performance']
        results_comparison.append({
            '전략': strategy['name'],
            '총 수익률(%)': f"{performance.get('total_return_pct', 0):.2f}",
            '샤프 비율': f"{performance.get('sharpe_ratio', 0):.2f}",
            '최대 낙폭(%)': f"{performance.get('max_drawdown_pct', 0):.2f}",
            '승률(%)': f"{performance.get('win_rate', 0):.1%}",
            '총 거래': performance.get('total_trades', 0)
        })
    
    # 결과 비교
    print("\n전략별 성과 비교:")
    comparison_df = pd.DataFrame(results_comparison)
    print(comparison_df.to_string(index=False))

def performance_comparison():
    """성능 비교 테스트"""
    print("\n" + "="*60)
    print("성능 비교 테스트")
    print("="*60)
    
    import time
    
    # 대용량 데이터 생성
    print("대용량 데이터 생성 중...")
    large_data = create_sample_data('2020-01-01', '2023-12-31', base_price=50000000, volatility=0.025)
    print(f"데이터 크기: {len(large_data)}개 레코드")
    
    # 백테스트 실행 시간 측정
    start_time = time.time()
    
    backtest = VolatilityBreakoutBacktest(
        k_value=0.7,
        stop_loss=-0.015,
        take_profit=0.025,
        position_size=0.05,
        volume_filter=1.5,
        rsi_threshold=30
    )
    
    backtest.load_data(large_data)
    results = backtest.run_backtest()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n백테스트 실행 시간: {execution_time:.2f}초")
    print(f"거래 횟수: {len(results['trades'])}회")
    print(f"총 수익률: {results['performance']['total_return_pct']:.2f}%")
    print(f"샤프 비율: {results['performance']['sharpe_ratio']:.2f}")

def parameter_sensitivity_analysis():
    """매개변수 민감도 분석"""
    print("\n" + "="*60)
    print("매개변수 민감도 분석")
    print("="*60)
    
    # 기본 데이터
    data = create_sample_data('2023-01-01', '2023-12-31')
    
    # K값 민감도 분석
    k_values = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    k_results = []
    
    print("K값 민감도 분석 중...")
    for k in k_values:
        backtest = VolatilityBreakoutBacktest(
            k_value=k,
            stop_loss=-0.015,
            take_profit=0.025,
            position_size=0.05,
            volume_filter=1.5,
            rsi_threshold=30
        )
        
        backtest.load_data(data)
        results = backtest.run_backtest()
        
        k_results.append({
            'K값': k,
            '총 수익률(%)': f"{results['performance']['total_return_pct']:.2f}",
            '샤프 비율': f"{results['performance']['sharpe_ratio']:.2f}",
            '최대 낙폭(%)': f"{results['performance']['max_drawdown_pct']:.2f}",
            '승률(%)': f"{results['performance']['win_rate']:.1%}",
            '총 거래': results['performance']['total_trades']
        })
    
    print("\nK값별 성과:")
    k_df = pd.DataFrame(k_results)
    print(k_df.to_string(index=False))
    
    # 손절/익절 비율 민감도 분석
    print("\n손절/익절 비율 민감도 분석 중...")
    stop_take_combinations = [
        (-0.01, 0.02), (-0.015, 0.025), (-0.02, 0.03),
        (-0.01, 0.03), (-0.015, 0.035), (-0.02, 0.04)
    ]
    
    stop_take_results = []
    for stop_loss, take_profit in stop_take_combinations:
        backtest = VolatilityBreakoutBacktest(
            k_value=0.7,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=0.05,
            volume_filter=1.5,
            rsi_threshold=30
        )
        
        backtest.load_data(data)
        results = backtest.run_backtest()
        
        stop_take_results.append({
            '손절(%)': f"{stop_loss*100:.1f}",
            '익절(%)': f"{take_profit*100:.1f}",
            '총 수익률(%)': f"{results['performance']['total_return_pct']:.2f}",
            '샤프 비율': f"{results['performance']['sharpe_ratio']:.2f}",
            '승률(%)': f"{results['performance']['win_rate']:.1%}",
            '총 거래': results['performance']['total_trades']
        })
    
    print("\n손절/익절 비율별 성과:")
    stop_take_df = pd.DataFrame(stop_take_results)
    print(stop_take_df.to_string(index=False))

if __name__ == "__main__":
    # 기본 예제 실행
    main()
    
    # 실제 데이터 테스트 예제 실행
    test_with_real_data()
    
    # 성능 비교 테스트 실행
    performance_comparison()
    
    # 매개변수 민감도 분석 실행
    parameter_sensitivity_analysis()
