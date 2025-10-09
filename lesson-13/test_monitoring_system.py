#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모니터링 시스템 테스트
"""

import sys
sys.path.append('.')

import time
from datetime import datetime

from src.monitoring import (
    RealtimeDataCollector,
    PerformanceTracker,
    AlertSystem,
    AlertLevel,
    AlertType,
    MonitoringDashboard
)


def test_data_collector():
    """데이터 수집기 테스트"""
    print("="*60)
    print("1. 데이터 수집기 테스트")
    print("="*60)
    
    collector = RealtimeDataCollector(
        symbols=['KRW-BTC', 'KRW-ETH'],
        update_interval=1
    )
    
    collector.start()
    print("✅ 데이터 수집 시작")
    
    time.sleep(3)
    
    # 최신 데이터 확인
    btc_data = collector.get_latest_market_data('KRW-BTC')
    if btc_data:
        print(f"✅ BTC 가격: {btc_data.price:,.0f}원")
    
    # 히스토리 확인
    history = collector.get_market_history('KRW-BTC', minutes=1)
    print(f"✅ 히스토리: {len(history)}개 데이터")
    
    collector.stop()
    print("✅ 데이터 수집 중지\n")


def test_performance_tracker():
    """성능 추적기 테스트"""
    print("="*60)
    print("2. 성능 추적기 테스트")
    print("="*60)
    
    tracker = PerformanceTracker(initial_capital=1_000_000)
    
    # 거래 추가
    tracker.add_trade({
        'timestamp': datetime.now(),
        'symbol': 'KRW-BTC',
        'side': 'buy',
        'price': 50_000_000,
        'quantity': 0.01,
        'pnl': 100_000
    })
    print("✅ 거래 추가")
    
    # 성과 업데이트
    metrics = tracker.update({}, {})
    
    # 요약 조회
    summary = tracker.get_performance_summary()
    print(f"✅ 총 수익률: {summary.get('returns', {}).get('total', '0%')}")
    print(f"✅ 샤프 비율: {summary.get('efficiency', {}).get('sharpe_ratio', '0.00')}\n")


def test_alert_system():
    """알림 시스템 테스트"""
    print("="*60)
    print("3. 알림 시스템 테스트")
    print("="*60)
    
    alert_system = AlertSystem(cooldown_seconds=10)
    
    alert_system.start()
    print("✅ 알림 시스템 시작")
    
    # 커스텀 알림 전송
    alert_system.send_custom_alert(
        level=AlertLevel.INFO,
        alert_type=AlertType.SYSTEM,
        title="테스트 알림",
        message="시스템이 정상 작동 중입니다"
    )
    print("✅ 알림 전송")
    
    time.sleep(2)
    
    # 알림 조회
    recent_alerts = alert_system.get_recent_alerts(minutes=1)
    print(f"✅ 최근 알림: {len(recent_alerts)}개")
    
    alert_system.stop()
    print("✅ 알림 시스템 중지\n")


def test_integrated_system():
    """통합 시스템 테스트"""
    print("="*60)
    print("4. 통합 시스템 테스트")
    print("="*60)
    
    # 컴포넌트 생성
    collector = RealtimeDataCollector(['KRW-BTC'], update_interval=1)
    tracker = PerformanceTracker(initial_capital=1_000_000)
    alert_system = AlertSystem(cooldown_seconds=10)
    
    # 대시보드 생성 (시작은 안 함)
    dashboard = MonitoringDashboard(
        data_collector=collector,
        performance_tracker=tracker,
        alert_system=alert_system,
        port=5001  # 테스트용 포트
    )
    
    # 템플릿 생성 테스트
    dashboard.create_dashboard_template()
    print("✅ 대시보드 템플릿 생성")
    
    # 시작
    collector.start()
    alert_system.start()
    print("✅ 통합 시스템 시작")
    
    # 몇 초간 실행
    print("⏱️  5초간 실행 중...")
    for i in range(5):
        market_data = collector.market_data
        strategy_performance = collector.strategy_performance
        
        metrics = tracker.update(market_data, strategy_performance)
        alert_system.check_metrics(metrics)
        
        time.sleep(1)
        print(f"  {i+1}/5 완료")
    
    # 중지
    collector.stop()
    alert_system.stop()
    print("✅ 통합 시스템 중지\n")


def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("모니터링 시스템 테스트 시작")
    print("="*60 + "\n")
    
    try:
        # 1. 데이터 수집기
        test_data_collector()
        
        # 2. 성능 추적기
        test_performance_tracker()
        
        # 3. 알림 시스템
        test_alert_system()
        
        # 4. 통합 시스템
        test_integrated_system()
        
        print("="*60)
        print("✅ 모든 테스트 통과!")
        print("="*60)
        
        print("\n다음 명령으로 실제 시스템을 실행하세요:")
        print("  python realtime_monitoring_system.py")
        print("\n웹 대시보드 접속:")
        print("  http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

