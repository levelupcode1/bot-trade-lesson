#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
실시간 가격 데이터 수집기 사용 예제

이 파일은 realtime_price_collector.py와 data_analyzer.py의 
다양한 사용법을 보여주는 예제입니다.
"""

import time
import threading
from datetime import datetime
from realtime_price_collector import UpbitWebSocketCollector
from data_analyzer import RealtimeDataAnalyzer

def example_basic_collection():
    """기본 데이터 수집 예제"""
    print("=" * 60)
    print("📊 기본 실시간 데이터 수집 예제")
    print("=" * 60)
    
    # 수집할 마켓 설정
    markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
    
    # 데이터 수집기 생성
    collector = UpbitWebSocketCollector(
        markets=markets,
        data_dir="example_data",
        save_format="csv"
    )
    
    # 콜백 함수 정의
    def on_ticker(data):
        print(f"📈 {data['market']}: {data['trade_price']:,}원 "
              f"({data['signed_change_rate']:+.2%})")
    
    def on_error(error):
        print(f"❌ 오류: {error}")
    
    def on_connect():
        print("✅ 연결 성공!")
    
    # 콜백 등록
    collector.set_callbacks(
        on_ticker=on_ticker,
        on_error=on_error,
        on_connect=on_connect
    )
    
    try:
        print("🚀 데이터 수집 시작... (10초간)")
        collector.start()
        time.sleep(10)  # 10초간 수집
        collector.stop()
        print("⏹️  데이터 수집 완료!")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지됨")
        collector.stop()

def example_advanced_collection():
    """고급 데이터 수집 예제"""
    print("\n" + "=" * 60)
    print("🔧 고급 실시간 데이터 수집 예제")
    print("=" * 60)
    
    # 더 많은 마켓 설정
    markets = [
        'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT',
        'KRW-LINK', 'KRW-LTC', 'KRW-BCH', 'KRW-EOS', 'KRW-TRX'
    ]
    
    # 고급 설정으로 수집기 생성
    collector = UpbitWebSocketCollector(
        markets=markets,
        data_dir="advanced_data",
        save_format="json"
    )
    
    # 고급 설정
    collector.buffer_size = 50      # 버퍼 크기 조정
    collector.save_interval = 20    # 저장 간격 조정
    collector.max_reconnect_attempts = 15  # 재연결 시도 횟수 증가
    
    # 통계 수집용 변수
    data_count = {market: 0 for market in markets}
    start_time = time.time()
    
    def on_ticker(data):
        market = data['market']
        data_count[market] += 1
        
        # 10개마다 출력
        if data_count[market] % 10 == 0:
            print(f"📊 {market}: {data_count[market]}개 수집됨")
    
    def on_error(error):
        print(f"❌ 오류 발생: {error}")
    
    def on_connect():
        print("✅ 고급 수집기 연결 성공!")
        print(f"📋 수집 마켓: {len(collector.markets)}개")
    
    # 콜백 등록
    collector.set_callbacks(
        on_ticker=on_ticker,
        on_error=on_error,
        on_connect=on_connect
    )
    
    try:
        print("🚀 고급 데이터 수집 시작... (30초간)")
        collector.start()
        time.sleep(30)  # 30초간 수집
        collector.stop()
        
        # 수집 통계 출력
        print("\n📈 수집 통계:")
        total_data = sum(data_count.values())
        elapsed_time = time.time() - start_time
        
        for market, count in data_count.items():
            if count > 0:
                print(f"  {market}: {count}개 ({count/elapsed_time:.1f}개/초)")
        
        print(f"  총 수집: {total_data}개 ({total_data/elapsed_time:.1f}개/초)")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지됨")
        collector.stop()

def example_data_analysis():
    """데이터 분석 예제"""
    print("\n" + "=" * 60)
    print("📊 데이터 분석 예제")
    print("=" * 60)
    
    # 분석기 생성
    analyzer = RealtimeDataAnalyzer("example_data")
    
    # 데이터 로드
    print("📁 데이터 로드 중...")
    data = analyzer.load_data()
    
    if data.empty:
        print("❌ 분석할 데이터가 없습니다.")
        print("먼저 example_basic_collection()을 실행하세요.")
        return
    
    print(f"✅ {len(data)}개 레코드 로드 완료")
    
    # 기본 통계
    print("\n📈 기본 통계:")
    stats = analyzer.get_basic_statistics()
    for market, market_stats in stats.items():
        print(f"\n{market}:")
        print(f"  데이터 수: {market_stats['count']:,}개")
        print(f"  가격 범위: {market_stats['price_range']['min']:,.0f}원 ~ {market_stats['price_range']['max']:,.0f}원")
        print(f"  평균 가격: {market_stats['price_range']['mean']:,.0f}원")
        print(f"  변동률 범위: {market_stats['change_rate_range']['min']:.2%} ~ {market_stats['change_rate_range']['max']:.2%}")
    
    # 마켓별 요약
    print("\n📋 마켓별 요약:")
    summary = analyzer.get_market_summary()
    print(summary)
    
    # 변동성 분석
    print("\n📊 변동성 분석:")
    for market in data['market'].unique():
        volatility = analyzer.analyze_volatility(market)
        if volatility:
            print(f"\n{market}:")
            print(f"  일일 변동성: {volatility['daily_volatility']:.2%}")
            print(f"  최대 변동률: {volatility['max_change']:.2%}")
            print(f"  최소 변동률: {volatility['min_change']:.2%}")
            print(f"  평균 절대 변동률: {volatility['avg_abs_change']:.2%}")
    
    # 차트 생성
    print("\n📈 차트 생성 중...")
    first_market = data['market'].iloc[0]
    analyzer.create_price_chart(first_market, f"example_chart_{first_market}.png")
    
    # 상관관계 히트맵
    print("🔗 상관관계 히트맵 생성 중...")
    analyzer.create_correlation_heatmap("example_correlation.png")
    
    # 분석 보고서
    print("📄 분석 보고서 생성 중...")
    analyzer.export_analysis_report("example_report.html")
    
    print("\n✅ 분석 완료!")
    print("생성된 파일:")
    print("- example_chart_*.png: 가격 차트")
    print("- example_correlation.png: 상관관계 히트맵")
    print("- example_report.html: 분석 보고서")

def example_custom_callback():
    """커스텀 콜백 함수 예제"""
    print("\n" + "=" * 60)
    print("🎯 커스텀 콜백 함수 예제")
    print("=" * 60)
    
    # 가격 알림을 위한 임계값 설정
    price_thresholds = {
        'KRW-BTC': 50000000,  # 5천만원
        'KRW-ETH': 3000000,   # 300만원
        'KRW-XRP': 500        # 500원
    }
    
    # 변동률 임계값
    change_threshold = 0.05  # 5%
    
    def custom_ticker_callback(data):
        market = data['market']
        price = data['trade_price']
        change_rate = data['signed_change_rate']
        
        # 가격 임계값 체크
        if market in price_thresholds:
            threshold = price_thresholds[market]
            if price >= threshold:
                print(f"🚨 {market} 가격 알림: {price:,}원 (임계값: {threshold:,}원)")
        
        # 변동률 임계값 체크
        if abs(change_rate) >= change_threshold:
            direction = "상승" if change_rate > 0 else "하락"
            print(f"📈 {market} 급변동: {change_rate:+.2%} {direction}")
        
        # 일반 정보 출력 (5개마다)
        if hash(data['timestamp']) % 5 == 0:
            print(f"📊 {market}: {price:,}원 ({change_rate:+.2%})")
    
    def custom_error_callback(error):
        print(f"❌ 커스텀 오류 처리: {error}")
        # 여기에 슬랙 알림, 이메일 발송 등 추가 가능
    
    def custom_connect_callback():
        print("✅ 커스텀 연결 성공!")
        print("🎯 가격 알림 및 급변동 감지 활성화")
    
    # 수집기 생성
    collector = UpbitWebSocketCollector(
        markets=['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
        data_dir="custom_data",
        save_format="csv"
    )
    
    # 커스텀 콜백 등록
    collector.set_callbacks(
        on_ticker=custom_ticker_callback,
        on_error=custom_error_callback,
        on_connect=custom_connect_callback
    )
    
    try:
        print("🚀 커스텀 콜백 수집 시작... (20초간)")
        collector.start()
        time.sleep(20)  # 20초간 수집
        collector.stop()
        print("⏹️  커스텀 수집 완료!")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지됨")
        collector.stop()

def example_multi_threading():
    """멀티스레딩 예제"""
    print("\n" + "=" * 60)
    print("🧵 멀티스레딩 수집 예제")
    print("=" * 60)
    
    def collect_market_group(markets, group_name, duration=15):
        """특정 마켓 그룹을 수집하는 함수"""
        collector = UpbitWebSocketCollector(
            markets=markets,
            data_dir=f"thread_data_{group_name}",
            save_format="csv"
        )
        
        def on_ticker(data):
            print(f"[{group_name}] {data['market']}: {data['trade_price']:,}원")
        
        collector.set_callbacks(on_ticker=on_ticker)
        
        try:
            collector.start()
            time.sleep(duration)
            collector.stop()
            print(f"✅ {group_name} 그룹 수집 완료")
        except Exception as e:
            print(f"❌ {group_name} 그룹 오류: {e}")
    
    # 마켓 그룹 분할
    major_coins = ['KRW-BTC', 'KRW-ETH']
    alt_coins = ['KRW-XRP', 'KRW-ADA', 'KRW-DOT']
    defi_coins = ['KRW-LINK', 'KRW-UNI', 'KRW-AAVE']
    
    # 스레드 생성
    threads = [
        threading.Thread(target=collect_market_group, args=(major_coins, "Major", 15)),
        threading.Thread(target=collect_market_group, args=(alt_coins, "Alt", 15)),
        threading.Thread(target=collect_market_group, args=(defi_coins, "DeFi", 15))
    ]
    
    try:
        print("🚀 멀티스레딩 수집 시작...")
        
        # 모든 스레드 시작
        for thread in threads:
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        print("✅ 모든 스레드 수집 완료!")
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지됨")

def main():
    """메인 함수 - 모든 예제 실행"""
    print("🎯 실시간 가격 데이터 수집기 예제 모음")
    print("=" * 60)
    
    examples = [
        ("기본 데이터 수집", example_basic_collection),
        ("고급 데이터 수집", example_advanced_collection),
        ("데이터 분석", example_data_analysis),
        ("커스텀 콜백", example_custom_callback),
        ("멀티스레딩", example_multi_threading)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
    
    print("\n0. 모든 예제 실행")
    print("q. 종료")
    
    while True:
        try:
            choice = input("\n실행할 예제를 선택하세요 (0-5, q): ").strip()
            
            if choice.lower() == 'q':
                print("👋 프로그램을 종료합니다.")
                break
            elif choice == '0':
                # 모든 예제 실행
                for name, func in examples:
                    print(f"\n{'='*20} {name} {'='*20}")
                    func()
                    time.sleep(2)
            elif choice.isdigit() and 1 <= int(choice) <= len(examples):
                # 특정 예제 실행
                name, func = examples[int(choice) - 1]
                print(f"\n{'='*20} {name} {'='*20}")
                func()
            else:
                print("❌ 잘못된 선택입니다. 다시 입력하세요.")
                
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
