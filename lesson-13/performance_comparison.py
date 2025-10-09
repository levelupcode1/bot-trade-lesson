#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화 전후 성능 비교

기존 vs 최적화된 모니터링 시스템 성능 비교
"""

import sys
sys.path.append('.')

import time
import psutil
import os
from datetime import datetime
import numpy as np
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def measure_performance(system_type: str, duration: int = 30):
    """시스템 성능 측정
    
    Args:
        system_type: 'original' or 'optimized'
        duration: 측정 시간 (초)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"{system_type.upper()} 시스템 성능 측정 ({duration}초)")
    logger.info(f"{'='*60}")
    
    # 프로세스 정보
    process = psutil.Process(os.getpid())
    
    # 초기 상태
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    cpu_samples = []
    memory_samples = []
    update_times = []
    
    # 시스템 초기화
    if system_type == 'original':
        from src.monitoring import (
            RealtimeDataCollector,
            PerformanceTracker,
            AlertSystem
        )
        
        collector = RealtimeDataCollector(
            symbols=['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            update_interval=1
        )
        tracker = PerformanceTracker(initial_capital=1_000_000)
        alert_system = AlertSystem(cooldown_seconds=300)
        
    else:  # optimized
        from src.monitoring.optimized_collector import OptimizedDataCollector
        from src.monitoring.optimized_tracker import OptimizedPerformanceTracker
        from src.monitoring.optimized_alert import OptimizedAlertSystem
        
        collector = OptimizedDataCollector(
            symbols=['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            update_interval=1,
            buffer_size=10000,
            batch_size=100
        )
        tracker = OptimizedPerformanceTracker(initial_capital=1_000_000)
        alert_system = OptimizedAlertSystem(
            base_cooldown=300,
            max_alerts_per_minute=10
        )
    
    # 시스템 시작
    collector.start()
    alert_system.start()
    
    logger.info("측정 시작...")
    start_time = time.time()
    
    # 측정 루프
    for i in range(duration):
        loop_start = time.time()
        
        # CPU 사용률
        cpu_percent = process.cpu_percent(interval=0.1)
        cpu_samples.append(cpu_percent)
        
        # 메모리 사용량
        memory_mb = process.memory_info().rss / 1024 / 1024
        memory_samples.append(memory_mb)
        
        # 업데이트 시간
        update_start = time.time()
        
        if system_type == 'original':
            market_data = collector.market_data
            strategy_perf = collector.strategy_performance
            metrics = tracker.update(market_data, strategy_perf)
        else:
            all_data = collector.get_all_latest_data()
            equity = tracker.current_capital
            metrics = tracker.update(equity)
        
        alert_system.check_metrics(metrics)
        
        update_time = time.time() - update_start
        update_times.append(update_time)
        
        # 1초 대기
        elapsed = time.time() - loop_start
        sleep_time = max(0, 1 - elapsed)
        time.sleep(sleep_time)
        
        if (i + 1) % 10 == 0:
            logger.info(f"  진행: {i+1}/{duration}초")
    
    # 시스템 중지
    collector.stop()
    alert_system.stop()
    
    # 최종 메모리
    final_memory = process.memory_info().rss / 1024 / 1024
    
    # 통계 계산
    results = {
        'duration': duration,
        'avg_cpu': np.mean(cpu_samples),
        'peak_cpu': np.max(cpu_samples),
        'avg_memory': np.mean(memory_samples),
        'peak_memory': np.max(memory_samples),
        'memory_increase': final_memory - initial_memory,
        'avg_update_time': np.mean(update_times) * 1000,  # ms
        'max_update_time': np.max(update_times) * 1000,
        'min_update_time': np.min(update_times) * 1000
    }
    
    # 시스템별 추가 통계
    if system_type == 'optimized':
        collector_stats = collector.get_stats()
        tracker_stats = tracker.get_stats()
        alert_stats = alert_system.get_stats()
        
        results.update({
            'buffer_usage': collector_stats.get('buffer_usage', 0),
            'cache_hits': tracker_stats.get('cache_hits', 0),
            'suppression_rate': alert_stats.get('suppression_rate', 0)
        })
    
    # 결과 출력
    logger.info(f"\n{'='*60}")
    logger.info(f"{system_type.upper()} 시스템 측정 결과")
    logger.info(f"{'='*60}")
    logger.info(f"평균 CPU 사용률: {results['avg_cpu']:.1f}%")
    logger.info(f"최대 CPU 사용률: {results['peak_cpu']:.1f}%")
    logger.info(f"평균 메모리 사용: {results['avg_memory']:.1f}MB")
    logger.info(f"최대 메모리 사용: {results['peak_memory']:.1f}MB")
    logger.info(f"메모리 증가: {results['memory_increase']:.1f}MB")
    logger.info(f"평균 업데이트 시간: {results['avg_update_time']:.2f}ms")
    logger.info(f"최대 업데이트 시간: {results['max_update_time']:.2f}ms")
    
    if system_type == 'optimized':
        logger.info(f"버퍼 사용률: {results.get('buffer_usage', 0):.1f}%")
        logger.info(f"캐시 히트: {results.get('cache_hits', 0)}")
        logger.info(f"알림 억제율: {results.get('suppression_rate', 0):.1f}%")
    
    return results


def compare_systems():
    """시스템 비교"""
    logger.info("\n" + "="*80)
    logger.info("모니터링 시스템 성능 비교")
    logger.info("="*80)
    
    # 측정 시간
    duration = 30  # 30초
    
    # 기존 시스템 측정
    logger.info("\n[1/2] 기존 시스템 측정 중...")
    original_results = measure_performance('original', duration)
    
    # 잠시 대기
    time.sleep(5)
    
    # 최적화된 시스템 측정
    logger.info("\n[2/2] 최적화된 시스템 측정 중...")
    optimized_results = measure_performance('optimized', duration)
    
    # 비교 분석
    logger.info("\n" + "="*80)
    logger.info("성능 비교 분석")
    logger.info("="*80)
    
    # 개선율 계산
    improvements = {}
    
    for key in ['avg_cpu', 'avg_memory', 'memory_increase', 'avg_update_time']:
        if key in original_results and key in optimized_results:
            original_val = original_results[key]
            optimized_val = optimized_results[key]
            
            if original_val > 0:
                improvement = ((original_val - optimized_val) / original_val) * 100
                improvements[key] = improvement
    
    # 결과 출력
    logger.info("\n📊 개선율:")
    logger.info(f"  CPU 사용률: {improvements.get('avg_cpu', 0):+.1f}%")
    logger.info(f"  메모리 사용: {improvements.get('avg_memory', 0):+.1f}%")
    logger.info(f"  메모리 증가: {improvements.get('memory_increase', 0):+.1f}%")
    logger.info(f"  처리 속도: {improvements.get('avg_update_time', 0):+.1f}%")
    
    # 추가 최적화 지표
    logger.info("\n🚀 최적화 기능:")
    logger.info(f"  버퍼 사용률: {optimized_results.get('buffer_usage', 0):.1f}%")
    logger.info(f"  캐시 효율: {optimized_results.get('cache_hits', 0)} 히트")
    logger.info(f"  알림 억제율: {optimized_results.get('suppression_rate', 0):.1f}%")
    
    # 평가
    logger.info("\n✅ 최적화 효과:")
    
    if improvements.get('avg_cpu', 0) > 10:
        logger.info(f"  ✅ CPU 사용률 {improvements['avg_cpu']:.0f}% 감소 - 우수")
    
    if improvements.get('avg_memory', 0) > 20:
        logger.info(f"  ✅ 메모리 사용 {improvements['avg_memory']:.0f}% 감소 - 우수")
    
    if improvements.get('avg_update_time', 0) > 30:
        logger.info(f"  ✅ 처리 속도 {improvements['avg_update_time']:.0f}% 향상 - 우수")
    
    # 전체 평가
    avg_improvement = np.mean(list(improvements.values()))
    
    logger.info(f"\n🎯 전체 성능 개선: {avg_improvement:+.1f}%")
    
    if avg_improvement > 30:
        logger.info("  ⭐⭐⭐ 매우 우수한 최적화!")
    elif avg_improvement > 20:
        logger.info("  ⭐⭐ 우수한 최적화!")
    elif avg_improvement > 10:
        logger.info("  ⭐ 양호한 최적화")
    else:
        logger.info("  📌 추가 최적화 필요")
    
    # 결과 저장
    import json
    
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'duration': duration,
        'original': original_results,
        'optimized': optimized_results,
        'improvements': improvements,
        'average_improvement': avg_improvement
    }
    
    with open('performance_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n💾 결과 저장: performance_comparison.json")


if __name__ == "__main__":
    compare_systems()

