#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리포트 스케줄러
APScheduler를 사용한 정기 리포트 생성
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReportScheduler:
    """리포트 스케줄러 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scheduler = None
        self.jobs = {}
        
        # APScheduler 확인
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
            
            self.scheduler = BlockingScheduler()
            self.CronTrigger = CronTrigger
            self.IntervalTrigger = IntervalTrigger
            
        except ImportError:
            logger.warning("apscheduler가 설치되지 않았습니다. 스케줄링 기능을 사용할 수 없습니다.")
    
    def add_daily_report(self, hour: int = 23, minute: int = 0):
        """일간 리포트 스케줄 추가"""
        if not self.scheduler:
            logger.warning("스케줄러가 초기화되지 않았습니다.")
            return
        
        trigger = self.CronTrigger(hour=hour, minute=minute)
        job = self.scheduler.add_job(
            self._generate_daily_report,
            trigger=trigger,
            id='daily_report',
            name='일간 리포트 생성',
            replace_existing=True
        )
        self.jobs['daily'] = job
        logger.info(f"일간 리포트 스케줄 추가: 매일 {hour:02d}:{minute:02d}")
    
    def add_weekly_report(self, day_of_week: int = 6, hour: int = 23, minute: int = 30):
        """주간 리포트 스케줄 추가"""
        if not self.scheduler:
            return
        
        trigger = self.CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        job = self.scheduler.add_job(
            self._generate_weekly_report,
            trigger=trigger,
            id='weekly_report',
            name='주간 리포트 생성',
            replace_existing=True
        )
        self.jobs['weekly'] = job
        logger.info(f"주간 리포트 스케줄 추가: 매주 {day_of_week}요일 {hour:02d}:{minute:02d}")
    
    def add_monthly_report(self, day: int = 1, hour: int = 1, minute: int = 0):
        """월간 리포트 스케줄 추가"""
        if not self.scheduler:
            return
        
        trigger = self.CronTrigger(day=day, hour=hour, minute=minute)
        job = self.scheduler.add_job(
            self._generate_monthly_report,
            trigger=trigger,
            id='monthly_report',
            name='월간 리포트 생성',
            replace_existing=True
        )
        self.jobs['monthly'] = job
        logger.info(f"월간 리포트 스케줄 추가: 매월 {day}일 {hour:02d}:{minute:02d}")
    
    def add_alert_monitor(self, interval_minutes: int = 5):
        """이상 상황 모니터링 스케줄 추가"""
        if not self.scheduler:
            return
        
        trigger = self.IntervalTrigger(minutes=interval_minutes)
        job = self.scheduler.add_job(
            self._check_alerts,
            trigger=trigger,
            id='alert_monitor',
            name='이상 상황 모니터링',
            replace_existing=True
        )
        self.jobs['alert'] = job
        logger.info(f"이상 상황 모니터링 추가: {interval_minutes}분 간격")
    
    def _generate_daily_report(self):
        """일간 리포트 생성"""
        from .report_manager import ReportManager
        manager = ReportManager(self.config)
        manager.generate_report('daily')
    
    def _generate_weekly_report(self):
        """주간 리포트 생성"""
        from .report_manager import ReportManager
        manager = ReportManager(self.config)
        manager.generate_report('weekly')
    
    def _generate_monthly_report(self):
        """월간 리포트 생성"""
        from .report_manager import ReportManager
        manager = ReportManager(self.config)
        manager.generate_report('monthly')
    
    def _check_alerts(self):
        """이상 상황 체크"""
        from analyzers.alert_analyzer import AlertAnalyzer
        from .report_manager import ReportManager
        
        analyzer = AlertAnalyzer(self.config)
        alerts = analyzer.check_anomalies()
        
        if alerts:
            manager = ReportManager(self.config)
            manager.generate_alert_report(alerts)
    
    def start(self):
        """스케줄러 시작"""
        if not self.scheduler:
            logger.error("스케줄러를 시작할 수 없습니다. apscheduler를 설치하세요.")
            return
        
        logger.info("리포트 스케줄러 시작")
        self.scheduler.start()
    
    def stop(self):
        """스케줄러 중지"""
        if self.scheduler:
            logger.info("리포트 스케줄러 중지")
            self.scheduler.shutdown()

