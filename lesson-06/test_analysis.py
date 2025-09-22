#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
한글 폰트 테스트용 간단한 분석 스크립트
"""

from data_analyzer import RealtimeDataAnalyzer

def main():
    """간단한 분석 테스트"""
    try:
        print("📊 실시간 데이터 분석 테스트 시작...")
        
        # 분석기 생성
        analyzer = RealtimeDataAnalyzer("realtime_data")
        
        # 데이터 로드
        print("📁 데이터 로드 중...")
        data = analyzer.load_data()
        
        if data.empty:
            print("❌ 분석할 데이터가 없습니다.")
            print("먼저 realtime_price_collector.py를 실행하여 데이터를 수집하세요.")
            return
        
        print(f"✅ {len(data)}개 레코드 로드 완료")
        
        # 기본 통계 출력
        print("\n📈 기본 통계:")
        stats = analyzer.get_basic_statistics()
        for market, market_stats in stats.items():
            print(f"\n{market}:")
            print(f"  데이터 수: {market_stats['count']:,}개")
            print(f"  가격 범위: {market_stats['price_range']['min']:,.0f}원 ~ {market_stats['price_range']['max']:,.0f}원")
            print(f"  평균 가격: {market_stats['price_range']['mean']:,.0f}원")
            print(f"  변동률 범위: {market_stats['change_rate_range']['min']:.2%} ~ {market_stats['change_rate_range']['max']:.2%}")
        
        # 마켓별 요약 테이블
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
        
        # 분석 보고서 생성 (차트 없이)
        print("📄 분석 보고서 생성 중...")
        analyzer.export_analysis_report("test_analysis_report.html")
        
        print("\n✅ 모든 분석이 완료되었습니다!")
        print("생성된 파일:")
        print("- test_analysis_report.html: 분석 보고서")
        
    except Exception as e:
        print(f"❌ 분석 오류: {e}")

if __name__ == "__main__":
    main()
