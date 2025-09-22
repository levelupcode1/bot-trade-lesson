#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 백테스트 사용 예제
"""

import pandas as pd
import numpy as np
from volatility_breakout_backtest import VolatilityBreakoutBacktest, create_sample_data

def main():
    """백테스트 실행 예제"""
    
    print("="*60)
    print("변동성 돌파 전략 백테스트 예제")
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
        max_holding_days=2     # 최대 보유 2일
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
    backtest.plot_results('backtest_results.png')
    
    # 7. 거래 내역 상세 정보
    if results['trades']:
        print("\n7. 거래 내역 상세")
        trades_df = pd.DataFrame(results['trades'])
        print(trades_df[['entry_date', 'exit_date', 'entry_price', 'exit_price', 
                        'returns', 'holding_days']].head(10))
    
    print("\n백테스트 완료!")

if __name__ == "__main__":
    main()


