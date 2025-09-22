#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래 발생 안함 문제 진단 및 해결 스크립트
"""

import pandas as pd
import numpy as np
from volatility_breakout_backtest_optimized import VolatilityBreakoutBacktest, create_sample_data

def test_basic_backtest():
    """기본 백테스트 테스트"""
    print("="*60)
    print("기본 백테스트 테스트")
    print("="*60)
    
    # 샘플 데이터 생성
    data = create_sample_data('2023-01-01', '2023-12-31')
    
    # 기본 설정으로 백테스트
    backtest = VolatilityBreakoutBacktest(
        k_value=0.7,
        stop_loss=-0.015,
        take_profit=0.025,
        position_size=0.05,
        volume_filter=1.5,
        rsi_threshold=30
    )
    
    # 데이터 로딩
    backtest.load_data(data)
    
    # 백테스트 실행
    results = backtest.run_backtest()
    
    # 결과 확인
    print(f"거래 횟수: {len(results['trades'])}")
    
    if len(results['trades']) == 0:
        print("❌ 거래가 발생하지 않았습니다. 진단을 시작합니다...")
        backtest.diagnose_no_trades()
    else:
        print("✅ 거래가 정상적으로 발생했습니다.")
        backtest.print_performance()
    
    # 차트 생성
    backtest.plot_results('debug_basic_results.png')

def test_relaxed_conditions():
    """완화된 조건으로 테스트"""
    print("\n" + "="*60)
    print("완화된 조건으로 테스트")
    print("="*60)
    
    # 샘플 데이터 생성
    data = create_sample_data('2023-01-01', '2023-12-31')
    
    # 완화된 설정으로 백테스트
    backtest = VolatilityBreakoutBacktest(
        k_value=0.5,        # K값 낮춤 (더 쉬운 돌파)
        stop_loss=-0.01,    # 손절 완화
        take_profit=0.02,   # 익절 완화
        position_size=0.05,
        volume_filter=1.0,  # 거래량 필터 완화
        rsi_threshold=50,   # RSI 임계값 완화
        max_holding_days=3  # 보유 기간 연장
    )
    
    # 데이터 로딩
    backtest.load_data(data)
    
    # 백테스트 실행
    results = backtest.run_backtest()
    
    # 결과 확인
    print(f"거래 횟수: {len(results['trades'])}")
    
    if len(results['trades']) == 0:
        print("❌ 여전히 거래가 발생하지 않았습니다.")
        backtest.diagnose_no_trades()
    else:
        print("✅ 완화된 조건으로 거래가 발생했습니다.")
        backtest.print_performance()
    
    # 차트 생성
    backtest.plot_results('debug_relaxed_results.png')

def test_very_relaxed_conditions():
    """매우 완화된 조건으로 테스트"""
    print("\n" + "="*60)
    print("매우 완화된 조건으로 테스트")
    print("="*60)
    
    # 샘플 데이터 생성
    data = create_sample_data('2023-01-01', '2023-12-31')
    
    # 매우 완화된 설정으로 백테스트
    backtest = VolatilityBreakoutBacktest(
        k_value=0.3,        # K값 매우 낮춤
        stop_loss=-0.005,   # 손절 매우 완화
        take_profit=0.01,   # 익절 매우 완화
        position_size=0.05,
        volume_filter=0.5,  # 거래량 필터 매우 완화
        rsi_threshold=70,   # RSI 임계값 매우 완화
        max_holding_days=5  # 보유 기간 더 연장
    )
    
    # 데이터 로딩
    backtest.load_data(data)
    
    # 백테스트 실행
    results = backtest.run_backtest()
    
    # 결과 확인
    print(f"거래 횟수: {len(results['trades'])}")
    
    if len(results['trades']) == 0:
        print("❌ 매우 완화된 조건에서도 거래가 발생하지 않았습니다.")
        backtest.diagnose_no_trades()
    else:
        print("✅ 매우 완화된 조건으로 거래가 발생했습니다.")
        backtest.print_performance()
    
    # 차트 생성
    backtest.plot_results('debug_very_relaxed_results.png')

def test_different_data_periods():
    """다른 데이터 기간으로 테스트"""
    print("\n" + "="*60)
    print("다른 데이터 기간으로 테스트")
    print("="*60)
    
    # 더 긴 기간의 데이터 생성
    data = create_sample_data('2022-01-01', '2023-12-31', volatility=0.03)
    
    # 기본 설정으로 백테스트
    backtest = VolatilityBreakoutBacktest(
        k_value=0.7,
        stop_loss=-0.015,
        take_profit=0.025,
        position_size=0.05,
        volume_filter=1.5,
        rsi_threshold=30
    )
    
    # 데이터 로딩
    backtest.load_data(data)
    
    # 백테스트 실행
    results = backtest.run_backtest()
    
    # 결과 확인
    print(f"거래 횟수: {len(results['trades'])}")
    
    if len(results['trades']) == 0:
        print("❌ 더 긴 기간에서도 거래가 발생하지 않았습니다.")
        backtest.diagnose_no_trades()
    else:
        print("✅ 더 긴 기간에서 거래가 발생했습니다.")
        backtest.print_performance()
    
    # 차트 생성
    backtest.plot_results('debug_long_period_results.png')

def test_data_quality():
    """데이터 품질 확인"""
    print("\n" + "="*60)
    print("데이터 품질 확인")
    print("="*60)
    
    # 샘플 데이터 생성
    data = create_sample_data('2023-01-01', '2023-12-31')
    
    print("📊 생성된 데이터 정보:")
    print(f"  데이터 크기: {len(data)}")
    print(f"  기간: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"  컬럼: {list(data.columns)}")
    
    print("\n📈 가격 통계:")
    print(f"  최고가: {data['high'].max():,.0f}")
    print(f"  최저가: {data['low'].min():,.0f}")
    print(f"  평균가: {data['close'].mean():,.0f}")
    print(f"  가격 변동폭: {data['close'].max() / data['close'].min():.2f}배")
    
    print("\n📊 거래량 통계:")
    print(f"  최대 거래량: {data['volume'].max():,.0f}")
    print(f"  최소 거래량: {data['volume'].min():,.0f}")
    print(f"  평균 거래량: {data['volume'].mean():,.0f}")
    
    print("\n🔍 데이터 품질:")
    print(f"  결측값: {data.isnull().sum().sum()}개")
    print(f"  무한값: {np.isinf(data.select_dtypes(include=[np.number])).sum().sum()}개")
    
    # 기술적 지표 미리 계산해서 확인
    backtest = VolatilityBreakoutBacktest()
    backtest.data = data.copy()
    backtest._calculate_indicators()
    
    print("\n📊 기술적 지표 통계:")
    print(f"  돌파선 범위: {backtest.data['breakout_line'].min():,.0f} ~ {backtest.data['breakout_line'].max():,.0f}")
    print(f"  RSI 범위: {backtest.data['rsi'].min():.1f} ~ {backtest.data['rsi'].max():.1f}")
    print(f"  변동성 범위: {backtest.data['volatility'].min():.2%} ~ {backtest.data['volatility'].max():.2%}")
    
    # 돌파 조건 확인
    breakout_condition = backtest.data['close'] > backtest.data['breakout_line']
    print(f"\n🎯 돌파 조건 분석:")
    print(f"  돌파 발생: {breakout_condition.sum()}회")
    print(f"  돌파 비율: {breakout_condition.mean():.1%}")

def main():
    """메인 실행 함수"""
    print("거래 발생 안함 문제 진단 및 해결")
    
    # 1. 데이터 품질 확인
    test_data_quality()
    
    # 2. 기본 백테스트 테스트
    test_basic_backtest()
    
    # 3. 완화된 조건으로 테스트
    test_relaxed_conditions()
    
    # 4. 매우 완화된 조건으로 테스트
    test_very_relaxed_conditions()
    
    # 5. 다른 데이터 기간으로 테스트
    test_different_data_periods()
    
    print("\n" + "="*60)
    print("진단 완료!")
    print("="*60)
    print("💡 권장사항:")
    print("1. K값을 0.5 이하로 낮춰보세요")
    print("2. 거래량 필터를 1.0 이하로 낮춰보세요")
    print("3. RSI 임계값을 50 이상으로 높여보세요")
    print("4. 더 긴 기간의 데이터를 사용해보세요")
    print("5. 데이터의 변동성을 높여보세요")

if __name__ == "__main__":
    main()
