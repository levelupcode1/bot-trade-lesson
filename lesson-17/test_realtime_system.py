"""
test_realtime_system.py - 실시간 시스템 테스트

업비트 API 연결과 적응형 전략 시스템을 테스트합니다.
"""

import sys
from upbit_data_collector import UpbitDataCollector
from adaptive_strategy_system import AdaptiveStrategySystem


def test_upbit_connection():
    """업비트 API 연결 테스트"""
    print("\n" + "="*60)
    print("1️⃣ 업비트 API 연결 테스트")
    print("="*60)
    
    try:
        collector = UpbitDataCollector()
        
        # 마켓 리스트 조회
        print("\n원화 마켓 조회 중...")
        krw_markets = collector.get_krw_markets()
        print(f"✅ 총 {len(krw_markets)}개 원화 마켓 발견")
        print(f"예시: {krw_markets[:5]}")
        
        # 현재가 조회
        print("\n현재가 조회 중...")
        test_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        prices = collector.get_current_price(test_markets)
        
        for market, info in prices.items():
            print(f"\n{market}:")
            print(f"  가격: {info['price']:,.0f}원")
            print(f"  변동률: {info['change_rate']*100:+.2f}%")
            print(f"  거래량: {info['volume']:,.2f}")
        
        print("\n✅ 업비트 API 연결 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ 업비트 API 연결 실패: {e}")
        return False


def test_data_collection():
    """데이터 수집 테스트"""
    print("\n" + "="*60)
    print("2️⃣ 데이터 수집 테스트")
    print("="*60)
    
    try:
        collector = UpbitDataCollector()
        
        # 일봉 데이터 수집
        print("\nKRW-XRP 일봉 데이터 수집 중 (6개월)...")
        df = collector.get_candles_daily('KRW-XRP', count=180)
        
        if df.empty:
            print("❌ 데이터 수집 실패")
            return False
        
        print(f"✅ {len(df)}일 데이터 수집 완료")
        print(f"\n데이터 정보:")
        print(f"  기간: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]}")
        print(f"  시가: {df['open'].iloc[-1]:,.0f}원")
        print(f"  고가: {df['high'].iloc[-1]:,.0f}원")
        print(f"  저가: {df['low'].iloc[-1]:,.0f}원")
        print(f"  종가: {df['close'].iloc[-1]:,.0f}원")
        print(f"  거래량: {df['volume'].iloc[-1]:,.2f}")
        
        print("\n✅ 데이터 수집 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ 데이터 수집 실패: {e}")
        return False


def test_strategy_system():
    """전략 시스템 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 적응형 전략 시스템 테스트")
    print("="*60)
    
    try:
        # 데이터 수집
        print("\n데이터 수집 중...")
        collector = UpbitDataCollector()
        price_data = collector.get_candles_daily('KRW-XRP', count=180)
        
        if price_data.empty:
            print("❌ 데이터 수집 실패")
            return False
        
        # 전략 시스템 초기화
        print("전략 시스템 초기화 중...")
        system = AdaptiveStrategySystem(account_balance=1_000_000)
        
        # 전략 실행
        print("전략 분석 및 신호 생성 중...")
        signal = system.execute_strategy(price_data)
        
        # 결과 출력
        print("\n📈 시장 상황:")
        market_condition = signal['market_condition']
        print(f"  추세: {market_condition.trend.value}")
        print(f"  변동성: {market_condition.volatility.value}")
        print(f"  모멘텀: {market_condition.momentum:+.2f}")
        print(f"  신뢰도: {market_condition.confidence:.2f}")
        
        print("\n🎯 신호:")
        print(f"  전략: {signal['strategy']}")
        print(f"  신호: {signal['action']}")
        print(f"  신뢰도: {signal['confidence']:.2f}")
        print(f"  사유: {signal['reason']}")
        
        print("\n✅ 전략 시스템 정상 작동!")
        return True
        
    except Exception as e:
        print(f"\n❌ 전략 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🧪 실시간 적응형 시스템 테스트")
    print("="*60)
    print("\n이 테스트는 다음을 확인합니다:")
    print("  1. 업비트 API 연결")
    print("  2. 실시간 데이터 수집")
    print("  3. 적응형 전략 시스템 작동")
    
    results = []
    
    # 테스트 실행
    results.append(("업비트 API 연결", test_upbit_connection()))
    results.append(("데이터 수집", test_data_collection()))
    results.append(("전략 시스템", test_strategy_system()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 모든 테스트 통과!")
        print("\n실시간 봇을 실행할 준비가 되었습니다:")
        print("  python realtime_adaptive_bot.py")
    else:
        print("❌ 일부 테스트 실패")
        print("\n문제를 해결한 후 다시 시도하세요.")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

