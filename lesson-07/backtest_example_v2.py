#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 백테스트 사용 예제 v2
"""

import pandas as pd
import numpy as np
from volatility_breakout_backtest_v2 import VolatilityBreakoutBacktest, create_sample_data

def main():
    """백테스트 실행 예제"""
    
    print("="*60)
    print("변동성 돌파 전략 백테스트 예제 v2")
    print("="*60)
    
    # 1. 샘플 데이터 생성
    print("\n1. 데이터 생성 중...")
    data = create_sample_data('2023-01-01', '2023-12-31')
    print(f"데이터 생성 완료: {len(data)}개 레코드")
    print(f"기간: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")
    
    # 2. 백테스트 설정
    print("\n2. 백테스트 설정")
    backtest = VolatilityBreakoutBacktest(
        k_value=0.5,           # K값 (더 낮게 설정)
        stop_loss=-0.015,      # 손절 -1.5%
        take_profit=0.025,     # 익절 +2.5%
        position_size=0.05,    # 포지션 크기 5%
        volume_filter=1.2,     # 거래량 필터 1.2배 (완화)
        rsi_threshold=40,      # RSI 임계값 40 (완화)
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
    backtest.plot_results('backtest_results_v2.png')
    
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
    
    # 다양한 전략 설정으로 테스트 (더 유연한 조건)
    strategies = [
        {
            'name': '보수적 전략',
            'params': {
                'k_value': 0.3,  # 더 낮은 K값으로 돌파 조건 완화
                'stop_loss': -0.01,
                'take_profit': 0.02,
                'position_size': 0.03,
                'volume_filter': 1.0,  # 거래량 필터 완화
                'rsi_threshold': 40,   # RSI 임계값 완화
                'max_holding_days': 3
            }
        },
        {
            'name': '공격적 전략',
            'params': {
                'k_value': 0.6,
                'stop_loss': -0.02,
                'take_profit': 0.03,
                'position_size': 0.08,
                'volume_filter': 1.0,  # 거래량 필터 완화
                'rsi_threshold': 50,   # RSI 필터 제거
                'max_holding_days': 1
            }
        },
        {
            'name': '균형 전략',
            'params': {
                'k_value': 0.5,
                'stop_loss': -0.015,
                'take_profit': 0.025,
                'position_size': 0.05,
                'volume_filter': 1.2,  # 거래량 필터 완화
                'rsi_threshold': 35,   # RSI 임계값 완화
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

if __name__ == "__main__":
    # 기본 예제 실행
    main()
    
    # 실제 데이터 테스트 예제 실행
    test_with_real_data()
