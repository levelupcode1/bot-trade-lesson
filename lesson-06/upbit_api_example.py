#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업비트 API 통합 클래스 사용 예시
"""

import time
import json
from datetime import datetime, timedelta
from upbit_api_integration import UpbitAPI

def example_market_data():
    """시장 데이터 조회 예시"""
    print("=" * 50)
    print("📊 시장 데이터 조회 예시")
    print("=" * 50)
    
    # API 클라이언트 생성 (인증 없이)
    api = UpbitAPI()
    
    try:
        # 1. 전체 마켓 코드 조회
        print("\n1️⃣ 전체 마켓 코드 조회")
        markets = api.get_markets()
        print(f"총 {len(markets)}개 마켓 발견")
        
        # KRW 마켓만 필터링
        krw_markets = [m for m in markets if m['market'].startswith('KRW-')]
        print(f"KRW 마켓: {len(krw_markets)}개")
        
        # 상위 5개 마켓 출력
        print("\n상위 5개 KRW 마켓:")
        for i, market in enumerate(krw_markets[:5]):
            print(f"  {i+1}. {market['market']} - {market['korean_name']}")
        
        # 2. 현재가 정보 조회
        print("\n2️⃣ 현재가 정보 조회")
        top_markets = [m['market'] for m in krw_markets[:5]]
        tickers = api.get_ticker(top_markets)
        
        print("\n현재가 정보:")
        for ticker in tickers:
            market = ticker['market']
            price = ticker['trade_price']
            change_rate = ticker['signed_change_rate']
            change_price = ticker['signed_change_price']
            
            print(f"  {market}: {price:,.0f}원 ({change_rate:+.2%}, {change_price:+,.0f}원)")
        
        # 3. 캔들 데이터 조회
        print("\n3️⃣ 캔들 데이터 조회 (비트코인 1일 차트)")
        candles = api.get_candles('KRW-BTC', count=10, unit='days')
        
        print("\n비트코인 최근 10일 가격:")
        for candle in candles:
            date = candle['candle_date_time_kst'][:10]
            open_price = candle['opening_price']
            close_price = candle['trade_price']
            high_price = candle['high_price']
            low_price = candle['low_price']
            volume = candle['candle_acc_trade_volume']
            
            print(f"  {date}: {open_price:,.0f} → {close_price:,.0f}원 "
                  f"(고: {high_price:,.0f}, 저: {low_price:,.0f}, 거래량: {volume:,.0f})")
        
        # 4. 호가 정보 조회
        print("\n4️⃣ 호가 정보 조회 (비트코인)")
        orderbook = api.get_orderbook(['KRW-BTC'])
        
        if orderbook:
            ob = orderbook[0]
            print(f"\n{ob['market']} 호가 정보:")
            
            # 매수 호가 (상위 5개)
            print("  매수 호가:")
            for i, bid in enumerate(ob['orderbook_units'][:5]):
                price = bid['bid_price']
                size = bid['bid_size']
                print(f"    {i+1}. {price:,.0f}원 - {size:.8f} BTC")
            
            # 매도 호가 (상위 5개)
            print("  매도 호가:")
            for i, ask in enumerate(ob['orderbook_units'][:5]):
                price = ask['ask_price']
                size = ask['ask_size']
                print(f"    {i+1}. {price:,.0f}원 - {size:.8f} BTC")
        
        # 5. 체결 내역 조회
        print("\n5️⃣ 체결 내역 조회 (비트코인 최근 10건)")
        trades = api.get_trades_ticks('KRW-BTC', count=10)
        
        print("\n최근 체결 내역:")
        for trade in trades:
            timestamp = trade['timestamp']
            price = trade['trade_price']
            volume = trade['trade_volume']
            side = trade['ask_bid']
            
            side_text = "매수" if side == "BID" else "매도"
            print(f"  {timestamp}: {price:,.0f}원 - {volume:.8f} BTC ({side_text})")
        
        # 6. 편의 메서드 사용
        print("\n6️⃣ 편의 메서드 사용")
        
        # 현재가 조회
        btc_price = api.get_current_price('KRW-BTC')
        print(f"비트코인 현재가: {btc_price:,.0f}원")
        
        # 마켓 요약 정보
        summary = api.get_market_summary(['KRW-BTC', 'KRW-ETH'])
        print("\n마켓 요약 정보:")
        for market, info in summary.items():
            print(f"  {market}: {info['price']:,.0f}원 "
                  f"({info['change_rate']:+.2%}, 거래량: {info['volume']:,.0f})")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def example_account_data():
    """계좌 데이터 조회 예시 (인증 필요)"""
    print("\n" + "=" * 50)
    print("💰 계좌 데이터 조회 예시")
    print("=" * 50)
    
    # API 클라이언트 생성 (인증 필요)
    api = UpbitAPI()
    
    if not api.authenticated:
        print("⚠️  API 키가 설정되지 않았습니다.")
        print("환경변수 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정하거나")
        print("UpbitAPI(access_key='your_key', secret_key='your_secret')로 설정하세요.")
        return
    
    try:
        # 1. 계좌 조회
        print("\n1️⃣ 전체 계좌 조회")
        accounts = api.get_accounts()
        
        print(f"총 {len(accounts)}개 계좌")
        print("\n계좌 정보:")
        for account in accounts:
            currency = account['currency']
            balance = float(account['balance'])
            locked = float(account['locked'])
            avg_buy_price = float(account['avg_buy_price'])
            
            if balance > 0 or locked > 0:
                print(f"  {currency}:")
                print(f"    보유량: {balance:.8f}")
                print(f"    잠김량: {locked:.8f}")
                print(f"    평균매수가: {avg_buy_price:,.0f}원")
                print(f"    평가금액: {balance * avg_buy_price:,.0f}원")
        
        # 2. 잔고 조회 (편의 메서드)
        print("\n2️⃣ 특정 통화 잔고 조회")
        
        # KRW 잔고
        krw_balance = api.get_balance('KRW')
        if krw_balance:
            print(f"KRW 잔고: {float(krw_balance['balance']):,.0f}원")
        else:
            print("KRW 잔고: 0원")
        
        # 3. 주문 리스트 조회
        print("\n3️⃣ 주문 리스트 조회")
        orders = api.get_orders(limit=10)
        
        if orders:
            print(f"최근 주문 {len(orders)}건:")
            for order in orders:
                market = order['market']
                side = order['side']
                state = order['state']
                volume = order['volume']
                price = order['price']
                created_at = order['created_at']
                
                side_text = "매수" if side == "bid" else "매도"
                state_text = {"wait": "대기", "done": "완료", "cancel": "취소"}.get(state, state)
                
                print(f"  {market} {side_text} {volume}@{price}원 - {state_text} ({created_at})")
        else:
            print("주문 내역이 없습니다.")
        
        # 4. 요청 통계
        print("\n4️⃣ API 요청 통계")
        stats = api.get_request_stats()
        print(f"총 요청 수: {stats['total_requests']}회")
        print(f"인증 상태: {'인증됨' if stats['authenticated'] else '미인증'}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def example_order_management():
    """주문 관리 예시 (인증 필요)"""
    print("\n" + "=" * 50)
    print("📋 주문 관리 예시")
    print("=" * 50)
    
    # API 클라이언트 생성 (인증 필요)
    api = UpbitAPI()
    
    if not api.authenticated:
        print("⚠️  API 키가 설정되지 않았습니다.")
        print("실제 주문을 위해서는 API 키가 필요합니다.")
        return
    
    try:
        # 주의: 실제 주문은 위험하므로 예시만 제공
        print("⚠️  주의: 실제 주문은 위험합니다. 테스트용으로만 사용하세요.")
        
        # 1. 주문 생성 예시 (실제로는 실행하지 않음)
        print("\n1️⃣ 주문 생성 예시 (실행하지 않음)")
        print("매수 주문 예시:")
        print("  api.create_order(")
        print("      market='KRW-BTC',")
        print("      side='bid',")
        print("      volume='0.001',")
        print("      price='160000000',")
        print("      ord_type='limit'")
        print("  )")
        
        print("\n매도 주문 예시:")
        print("  api.create_order(")
        print("      market='KRW-BTC',")
        print("      side='ask',")
        print("      volume='0.001',")
        print("      price='170000000',")
        print("      ord_type='limit'")
        print("  )")
        
        # 2. 주문 취소 예시
        print("\n2️⃣ 주문 취소 예시 (실행하지 않음)")
        print("  api.cancel_order('order-uuid-here')")
        
        # 3. 주문 조회 예시
        print("\n3️⃣ 주문 조회 예시")
        orders = api.get_orders(limit=5)
        
        if orders:
            print("최근 주문 5건:")
            for order in orders:
                print(f"  {order['market']} {order['side']} {order['volume']}@{order['price']}원 - {order['state']}")
        else:
            print("주문 내역이 없습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def example_error_handling():
    """오류 처리 예시"""
    print("\n" + "=" * 50)
    print("⚠️  오류 처리 예시")
    print("=" * 50)
    
    api = UpbitAPI()
    
    try:
        # 잘못된 마켓 코드로 요청
        print("\n1️⃣ 잘못된 마켓 코드로 요청")
        try:
            api.get_ticker(['INVALID-MARKET'])
        except Exception as e:
            print(f"예상된 오류: {e}")
        
        # 존재하지 않는 통화 잔고 조회
        print("\n2️⃣ 존재하지 않는 통화 잔고 조회")
        try:
            balance = api.get_balance('INVALID-CURRENCY')
            print(f"잔고: {balance}")
        except Exception as e:
            print(f"예상된 오류: {e}")
        
        # 요청 제한 테스트
        print("\n3️⃣ 요청 제한 테스트")
        print("연속 요청으로 인한 제한 처리...")
        
        for i in range(5):
            try:
                api.get_ticker(['KRW-BTC'])
                print(f"요청 {i+1}: 성공")
            except Exception as e:
                print(f"요청 {i+1}: {e}")
            time.sleep(0.1)  # 짧은 간격으로 요청
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 업비트 API 통합 클래스 사용 예시")
    print("=" * 50)
    
    try:
        # 1. 시장 데이터 조회 예시
        example_market_data()
        
        # 2. 계좌 데이터 조회 예시
        example_account_data()
        
        # 3. 주문 관리 예시
        example_order_management()
        
        # 4. 오류 처리 예시
        example_error_handling()
        
        print("\n✅ 모든 예시가 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
