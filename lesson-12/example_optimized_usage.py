#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화된 자동매매 데이터 분석 시스템 사용 예제
다양한 시나리오별 사용법과 성능 비교
"""

import time
from trading_analyzer_optimized import OptimizedTradingAnalyzer, OptimizedAnalysisConfig
from data_processor_optimized import DataConfig
from performance_benchmark import PerformanceBenchmark, BenchmarkConfig

def example_basic_optimized_analysis():
    """기본 최적화된 분석 예제"""
    print("=== 기본 최적화된 분석 예제 ===")
    
    # 최적화된 설정
    config = OptimizedAnalysisConfig(
        enable_parallel_processing=True,
        enable_caching=True,
        enable_batch_processing=True,
        max_memory_usage_mb=600,
        chart_quality="high"
    )
    
    # 분석기 생성 및 실행
    analyzer = OptimizedTradingAnalyzer(config)
    
    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    total_time = time.time() - start_time
    
    if 'error' not in results:
        print(f"✅ 분석 완료: {total_time:.3f}초")
        
        # 성능 정보 출력
        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            print(f"📊 효율성 점수: {perf['efficiency_score']:.1f}/100")
            print(f"💾 최대 메모리: {perf['peak_memory_mb']:.1f}MB")
        
        # 요약 출력
        summary = analyzer.get_analysis_summary()
        print(summary)
    else:
        print(f"❌ 분석 실패: {results['error']}")
    
    # 리소스 정리
    analyzer.cleanup_resources()

def example_large_data_analysis():
    """대용량 데이터 분석 예제"""
    print("\n=== 대용량 데이터 분석 예제 ===")
    
    # 대용량 데이터 설정
    data_config = DataConfig(
        db_path="data/large_trading.db",
        data_period_days=180,  # 6개월 데이터
        chunk_size=10000,      # 큰 청크 크기
        max_memory_usage=0.7   # 메모리 사용률 제한
    )
    
    analysis_config = OptimizedAnalysisConfig(
        data_config=data_config,
        enable_parallel_processing=True,
        enable_caching=True,
        enable_batch_processing=True,
        max_memory_usage_mb=1000,
        max_processing_time_seconds=600,  # 10분 타임아웃
        chunk_size=10000
    )
    
    analyzer = OptimizedTradingAnalyzer(analysis_config)
    
    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    total_time = time.time() - start_time
    
    if 'error' not in results:
        print(f"✅ 대용량 분석 완료: {total_time:.3f}초")
        
        # 데이터 요약
        data_summary = results.get('data_summary', {})
        print(f"📈 처리된 거래: {data_summary.get('trades_count', 0):,}건")
        print(f"📊 계좌 기록: {data_summary.get('account_records', 0):,}건")
        
        # 성능 정보
        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            print(f"⚡ 효율성 점수: {perf['efficiency_score']:.1f}/100")
            print(f"💾 최대 메모리: {perf['peak_memory_mb']:.1f}MB")
    else:
        print(f"❌ 대용량 분석 실패: {results['error']}")
    
    analyzer.cleanup_resources()

def example_performance_benchmark():
    """성능 벤치마크 예제"""
    print("\n=== 성능 벤치마크 예제 ===")
    
    # 벤치마크 설정
    config = BenchmarkConfig(
        test_data_sizes=[1000, 5000, 10000],  # 테스트 크기
        iterations=1,  # 빠른 테스트
        memory_limit_mb=800
    )
    
    # 벤치마크 실행
    benchmark = PerformanceBenchmark(config)
    
    start_time = time.time()
    results = benchmark.run_comprehensive_benchmark()
    benchmark_time = time.time() - start_time
    
    print(f"⏱️ 벤치마크 완료: {benchmark_time:.3f}초")
    
    # 결과 분석
    successful_tests = [r for r in results['results'] if r.get('success', False)]
    failed_tests = [r for r in results['results'] if not r.get('success', False)]
    
    print(f"✅ 성공한 테스트: {len(successful_tests)}")
    print(f"❌ 실패한 테스트: {len(failed_tests)}")
    
    # 성능 개선 통계
    if successful_tests:
        original_results = [r for r in successful_tests if r['version'] == 'original']
        optimized_results = [r for r in successful_tests if r['version'] == 'optimized']
        
        if original_results and optimized_results:
            avg_time_original = sum(r['execution_time'] for r in original_results) / len(original_results)
            avg_time_optimized = sum(r['execution_time'] for r in optimized_results) / len(optimized_results)
            
            improvement = ((avg_time_original - avg_time_optimized) / avg_time_original) * 100
            print(f"🚀 평균 성능 개선: {improvement:.1f}%")

def example_memory_optimization():
    """메모리 최적화 예제"""
    print("\n=== 메모리 최적화 예제 ===")
    
    # 메모리 제한이 있는 설정
    config = OptimizedAnalysisConfig(
        max_memory_usage_mb=400,  # 낮은 메모리 제한
        chunk_size=2000,          # 작은 청크 크기
        enable_caching=True,      # 캐싱으로 메모리 절약
        enable_batch_processing=True
    )
    
    analyzer = OptimizedTradingAnalyzer(config)
    
    # 메모리 사용량 모니터링
    import psutil
    process = psutil.Process()
    
    print(f"📊 시작 메모리: {process.memory_info().rss / 1024 / 1024:.1f}MB")
    
    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    total_time = time.time() - start_time
    
    print(f"📊 분석 후 메모리: {process.memory_info().rss / 1024 / 1024:.1f}MB")
    
    if 'error' not in results:
        print(f"✅ 메모리 최적화 분석 완료: {total_time:.3f}초")
        
        # 성능 정보
        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            print(f"💾 최대 메모리: {perf['peak_memory_mb']:.1f}MB")
            print(f"📈 평균 메모리: {perf['average_memory_mb']:.1f}MB")
    else:
        print(f"❌ 메모리 최적화 분석 실패: {results['error']}")
    
    analyzer.cleanup_resources()

def example_custom_configuration():
    """커스텀 설정 예제"""
    print("\n=== 커스텀 설정 예제 ===")
    
    # 특정 요구사항에 맞는 설정
    data_config = DataConfig(
        db_path="data/custom_trading.db",
        data_period_days=60,
        symbols=["KRW-BTC", "KRW-ETH"],  # 특정 코인만
        strategies=["volatility_breakout"],  # 특정 전략만
        chunk_size=5000,
        max_memory_usage=0.6
    )
    
    analysis_config = OptimizedAnalysisConfig(
        data_config=data_config,
        enable_performance_analysis=True,
        enable_statistical_analysis=False,  # 통계 분석 비활성화
        enable_visualization=True,
        enable_report_generation=True,
        enable_parallel_processing=True,
        enable_caching=True,
        max_memory_usage_mb=500,
        report_formats=["html"],  # HTML만 생성
        chart_quality="medium"
    )
    
    analyzer = OptimizedTradingAnalyzer(analysis_config)
    
    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    total_time = time.time() - start_time
    
    if 'error' not in results:
        print(f"✅ 커스텀 설정 분석 완료: {total_time:.3f}초")
        
        # 결과 요약
        summary = analyzer.get_analysis_summary()
        print(summary)
    else:
        print(f"❌ 커스텀 설정 분석 실패: {results['error']}")
    
    analyzer.cleanup_resources()

def example_error_handling():
    """오류 처리 예제"""
    print("\n=== 오류 처리 예제 ===")
    
    # 의도적으로 오류를 발생시킬 수 있는 설정
    config = OptimizedAnalysisConfig(
        max_memory_usage_mb=100,  # 매우 낮은 메모리 제한
        max_processing_time_seconds=10,  # 짧은 타임아웃
        enable_error_recovery=True
    )
    
    analyzer = OptimizedTradingAnalyzer(config)
    
    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    total_time = time.time() - start_time
    
    print(f"⏱️ 오류 처리 테스트 완료: {total_time:.3f}초")
    
    if 'error' in results:
        print(f"⚠️ 예상된 오류 발생: {results['error']}")
        
        # 오류 정보 확인
        if 'error_info' in results:
            error_info = results['error_info']
            print(f"🔍 오류 유형: {error_info.error_type}")
            print(f"📝 오류 메시지: {error_info.error_message}")
            print(f"🚨 심각도: {error_info.severity.value}")
            print(f"📂 카테고리: {error_info.category.value}")
    else:
        print("✅ 오류 없이 완료")
    
    analyzer.cleanup_resources()

def main():
    """메인 실행 함수"""
    print("🚀 최적화된 자동매매 분석 시스템 예제")
    print("=" * 50)
    
    try:
        # 1. 기본 최적화된 분석
        example_basic_optimized_analysis()
        
        # 2. 대용량 데이터 분석
        example_large_data_analysis()
        
        # 3. 성능 벤치마크
        example_performance_benchmark()
        
        # 4. 메모리 최적화
        example_memory_optimization()
        
        # 5. 커스텀 설정
        example_custom_configuration()
        
        # 6. 오류 처리
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ 모든 예제 실행 완료!")
        
    except Exception as e:
        print(f"❌ 예제 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()









