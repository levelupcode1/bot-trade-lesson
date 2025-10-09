#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 모니터링 시스템 통합 실행

구현 기능:
1. 실시간 데이터 수집기
2. 성능 지표 계산 엔진
3. 알림 시스템
4. 웹 대시보드
5. 데이터 저장 및 분석
"""

import sys
sys.path.append('.')

import logging
import time
from datetime import datetime
import signal
import pandas as pd

from src.monitoring import (
    RealtimeDataCollector,
    PerformanceTracker,
    AlertSystem,
    AlertLevel,
    AlertType,
    MonitoringDashboard
)


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class RealtimeMonitoringSystem:
    """실시간 모니터링 시스템 통합"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 1. 데이터 수집기 초기화
        self.data_collector = RealtimeDataCollector(
            symbols=['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            update_interval=1  # 1초마다 업데이트
        )
        
        # 2. 성능 추적기 초기화
        self.performance_tracker = PerformanceTracker(
            initial_capital=1_000_000
        )
        
        # 3. 알림 시스템 초기화
        self.alert_system = AlertSystem(
            cooldown_seconds=300  # 5분 쿨다운
        )
        
        # 4. 웹 대시보드 초기화
        self.dashboard = MonitoringDashboard(
            data_collector=self.data_collector,
            performance_tracker=self.performance_tracker,
            alert_system=self.alert_system,
            port=5000
        )
        
        # 종료 플래그
        self.running = False
        
        self.logger.info("실시간 모니터링 시스템 초기화 완료")
    
    def start(self):
        """시스템 시작"""
        self.logger.info("="*80)
        self.logger.info("실시간 모니터링 시스템 시작")
        self.logger.info("="*80)
        
        # 대시보드 템플릿 생성
        self.dashboard.create_dashboard_template()
        
        # 1. 데이터 수집 시작
        self.data_collector.start()
        self.logger.info("✅ 데이터 수집기 시작")
        
        # 2. 알림 시스템 시작
        self.alert_system.start()
        self.logger.info("✅ 알림 시스템 시작")
        
        # 3. 웹 대시보드 시작
        self.dashboard.start()
        self.logger.info(f"✅ 웹 대시보드 시작: http://localhost:5000")
        
        # 4. 모니터링 루프 시작
        self.running = True
        self._monitoring_loop()
    
    def _monitoring_loop(self):
        """메인 모니터링 루프"""
        self.logger.info("\n📊 실시간 모니터링 중...")
        self.logger.info("(Ctrl+C로 종료)\n")
        
        update_count = 0
        
        try:
            while self.running:
                # 최신 데이터 가져오기
                market_data = self.data_collector.market_data
                strategy_performance = self.data_collector.strategy_performance
                
                # 성능 지표 업데이트
                metrics = self.performance_tracker.update(
                    market_data, strategy_performance
                )
                
                # 알림 규칙 확인
                self.alert_system.check_metrics(metrics)
                
                # 주기적 로그 출력 (10초마다)
                update_count += 1
                if update_count % 10 == 0:
                    self._print_status(metrics)
                
                # 주기적 데이터 저장 (60초마다)
                if update_count % 60 == 0:
                    self._save_data()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("\n중지 신호 수신...")
            self.stop()
    
    def _print_status(self, metrics):
        """상태 출력"""
        if metrics:
            self.logger.info("─" * 80)
            self.logger.info(f"📈 수익률: {metrics.total_return:.2%} | "
                           f"샤프: {metrics.sharpe_ratio:.2f} | "
                           f"낙폭: {metrics.current_drawdown:.2%} | "
                           f"승률: {metrics.win_rate:.2%}")
            self.logger.info("─" * 80)
    
    def _save_data(self):
        """데이터 저장"""
        try:
            # 시장 데이터 저장
            market_df = self.data_collector.export_to_dataframe('market')
            if not market_df.empty:
                filename = f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                market_df.to_csv(filename, index=False, encoding='utf-8')
                self.logger.info(f"💾 시장 데이터 저장: {filename}")
            
            # 성과 데이터 저장
            performance_df = self.data_collector.export_to_dataframe('performance')
            if not performance_df.empty:
                filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                performance_df.to_csv(filename, index=False, encoding='utf-8')
                self.logger.info(f"💾 성과 데이터 저장: {filename}")
            
        except Exception as e:
            self.logger.error(f"데이터 저장 오류: {e}")
    
    def stop(self):
        """시스템 종료"""
        self.logger.info("\n실시간 모니터링 시스템 종료 중...")
        
        self.running = False
        
        # 데이터 수집 중지
        self.data_collector.stop()
        self.logger.info("✅ 데이터 수집기 중지")
        
        # 알림 시스템 중지
        self.alert_system.stop()
        self.logger.info("✅ 알림 시스템 중지")
        
        # 대시보드 중지
        self.dashboard.stop()
        self.logger.info("✅ 웹 대시보드 중지")
        
        # 최종 데이터 저장
        self._save_data()
        
        # 성과 요약 출력
        self._print_final_summary()
        
        self.logger.info("="*80)
        self.logger.info("실시간 모니터링 시스템 종료 완료")
        self.logger.info("="*80)
    
    def _print_final_summary(self):
        """최종 요약 출력"""
        summary = self.performance_tracker.get_performance_summary()
        
        self.logger.info("\n" + "="*80)
        self.logger.info("최종 성과 요약")
        self.logger.info("="*80)
        
        if summary:
            self.logger.info(f"\n📊 수익률:")
            for key, value in summary.get('returns', {}).items():
                self.logger.info(f"  {key}: {value}")
            
            self.logger.info(f"\n⚠️ 리스크:")
            for key, value in summary.get('risk', {}).items():
                self.logger.info(f"  {key}: {value}")
            
            self.logger.info(f"\n💹 효율성:")
            for key, value in summary.get('efficiency', {}).items():
                self.logger.info(f"  {key}: {value}")
            
            self.logger.info(f"\n📈 거래:")
            for key, value in summary.get('trading', {}).items():
                self.logger.info(f"  {key}: {value}")
        
        # 알림 요약
        alert_summary = self.alert_system.get_alert_summary()
        
        self.logger.info(f"\n🔔 알림 요약 (최근 1시간):")
        self.logger.info(f"  총 알림: {alert_summary.get('total', 0)}")
        
        if alert_summary.get('by_level'):
            self.logger.info(f"  레벨별:")
            for level, count in alert_summary['by_level'].items():
                self.logger.info(f"    {level}: {count}")


def main():
    """메인 실행"""
    # 시스템 생성
    system = RealtimeMonitoringSystem()
    
    # 종료 시그널 핸들러
    def signal_handler(sig, frame):
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 시스템 시작
    system.start()


if __name__ == "__main__":
    main()

