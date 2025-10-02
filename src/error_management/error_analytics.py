#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오류 통계 및 분석 시스템
오류 데이터를 수집, 분석하고 인사이트를 제공합니다.
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import statistics
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
from dataclasses_json import dataclass_json

from .error_detector import ErrorEvent, ErrorSeverity, ErrorCategory
from .error_classifier import ClassificationResult, PriorityLevel, ActionType
from .auto_recovery import RecoveryAttempt, RecoveryStatus
from .notification_system import NotificationMessage, NotificationStatus

logger = logging.getLogger(__name__)

@dataclass_json
@dataclass
class ErrorTrend:
    """오류 트렌드 데이터"""
    timestamp: datetime
    category: str
    severity: str
    count: int
    avg_response_time: float
    recovery_rate: float

@dataclass_json
@dataclass
class ErrorInsight:
    """오류 인사이트"""
    insight_type: str
    title: str
    description: str
    severity: str
    recommendations: List[str]
    confidence: float

class ErrorAnalytics:
    """오류 분석 시스템"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'error_analytics.db')
        self.retention_days = config.get('retention_days', 90)
        
        self._initialize_database()
        self.analytics_cache = {}
        self.cache_ttl = 300  # 5분
        
    def _initialize_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recovery_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_id TEXT UNIQUE NOT NULL,
                    error_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    recovery_method TEXT,
                    result_details TEXT,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (error_id) REFERENCES error_events (error_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    error_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sent_time DATETIME,
                    retry_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (error_id) REFERENCES error_events (error_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 인덱스 생성
            conn.execute('CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_events (timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_error_category ON error_events (category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_recovery_error_id ON recovery_attempts (error_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_notification_error_id ON notifications (error_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics (timestamp)')
            
            conn.commit()
    
    def store_error_event(self, error: ErrorEvent):
        """오류 이벤트 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO error_events 
                    (error_id, timestamp, category, severity, message, details, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error.error_id,
                    error.timestamp,
                    error.category.value,
                    error.severity.value,
                    error.message,
                    json.dumps(error.details),
                    error.source
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"오류 이벤트 저장 실패: {e}")
    
    def store_recovery_attempt(self, attempt: RecoveryAttempt):
        """복구 시도 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO recovery_attempts 
                    (attempt_id, error_id, status, start_time, end_time, 
                     recovery_method, result_details, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    attempt.attempt_id,
                    attempt.error_event.error_id,
                    attempt.status.value,
                    attempt.start_time,
                    attempt.end_time,
                    attempt.recovery_method,
                    json.dumps(attempt.result_details),
                    attempt.error_message
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"복구 시도 저장 실패: {e}")
    
    def store_notification(self, notification: NotificationMessage):
        """알림 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO notifications 
                    (message_id, error_id, channel, recipient, status, sent_time, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification.message_id,
                    notification.error_event.error_id,
                    notification.channel.value,
                    notification.recipient,
                    notification.status.value,
                    notification.sent_time,
                    notification.retry_count
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"알림 저장 실패: {e}")
    
    def store_system_metric(self, metric_name: str, metric_value: float, timestamp: datetime = None):
        """시스템 메트릭 저장"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO system_metrics (timestamp, metric_name, metric_value)
                    VALUES (?, ?, ?)
                ''', (timestamp, metric_name, metric_value))
                conn.commit()
        except Exception as e:
            logger.error(f"시스템 메트릭 저장 실패: {e}")
    
    def get_error_trends(self, hours: int = 24, granularity: str = 'hour') -> List[ErrorTrend]:
        """오류 트렌드 분석"""
        cache_key = f"error_trends_{hours}_{granularity}"
        
        if cache_key in self.analytics_cache:
            cached_data, cache_time = self.analytics_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return cached_data
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 시간 그룹핑 설정
                if granularity == 'hour':
                    time_format = "strftime('%Y-%m-%d %H:00:00', timestamp)"
                elif granularity == 'day':
                    time_format = "strftime('%Y-%m-%d 00:00:00', timestamp)"
                else:
                    time_format = "strftime('%Y-%m-%d %H:%M:00', timestamp)"
                
                query = '''
                    SELECT 
                        {} as time_bucket,
                        category,
                        severity,
                        COUNT(*) as count,
                        AVG(CASE WHEN details LIKE '%response_time%' 
                            THEN json_extract(details, '$.response_time') 
                            ELSE NULL END) as avg_response_time
                    FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY time_bucket, category, severity
                    ORDER BY time_bucket
                '''.format(time_format, hours)
                
                cursor = conn.execute(query)
                trends = []
                
                for row in cursor.fetchall():
                    trend = ErrorTrend(
                        timestamp=datetime.fromisoformat(row[0]),
                        category=row[1],
                        severity=row[2],
                        count=row[3],
                        avg_response_time=row[4] or 0.0,
                        recovery_rate=0.0  # 별도 계산 필요
                    )
                    trends.append(trend)
                
                # 복구율 계산
                for trend in trends:
                    trend.recovery_rate = self._calculate_recovery_rate(
                        trend.category, trend.severity, trend.timestamp
                    )
                
                self.analytics_cache[cache_key] = (trends, time.time())
                return trends
        
        except Exception as e:
            logger.error(f"오류 트렌드 분석 실패: {e}")
            return []
    
    def _calculate_recovery_rate(self, category: str, severity: str, timestamp: datetime) -> float:
        """복구율 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 해당 시간대의 오류 수
                error_count = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE category = ? AND severity = ? 
                    AND timestamp >= ? AND timestamp < ?
                ''', (category, severity, timestamp, timestamp + timedelta(hours=1))).fetchone()[0]
                
                if error_count == 0:
                    return 0.0
                
                # 성공한 복구 시도 수
                success_count = conn.execute('''
                    SELECT COUNT(*) FROM recovery_attempts ra
                    JOIN error_events ee ON ra.error_id = ee.error_id
                    WHERE ee.category = ? AND ee.severity = ?
                    AND ra.start_time >= ? AND ra.start_time < ?
                    AND ra.status = 'success'
                ''', (category, severity, timestamp, timestamp + timedelta(hours=1))).fetchone()[0]
                
                return success_count / error_count
        
        except Exception as e:
            logger.error(f"복구율 계산 실패: {e}")
            return 0.0
    
    def get_error_insights(self, hours: int = 24) -> List[ErrorInsight]:
        """오류 인사이트 생성"""
        insights = []
        
        # 1. 오류 증가 트렌드 분석
        trend_insight = self._analyze_error_trends(hours)
        if trend_insight:
            insights.append(trend_insight)
        
        # 2. 복구 성공률 분석
        recovery_insight = self._analyze_recovery_performance(hours)
        if recovery_insight:
            insights.append(recovery_insight)
        
        # 3. 알림 효과성 분석
        notification_insight = self._analyze_notification_effectiveness(hours)
        if notification_insight:
            insights.append(notification_insight)
        
        # 4. 시스템 리소스 관련 인사이트
        resource_insight = self._analyze_resource_correlation(hours)
        if resource_insight:
            insights.append(resource_insight)
        
        # 5. 시간대별 패턴 분석
        temporal_insight = self._analyze_temporal_patterns(hours)
        if temporal_insight:
            insights.append(temporal_insight)
        
        return insights
    
    def _analyze_error_trends(self, hours: int) -> Optional[ErrorInsight]:
        """오류 트렌드 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 최근 24시간과 이전 24시간 비교
                current_errors = conn.execute('''
                    SELECT category, COUNT(*) as count
                    FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY category
                '''.format(hours)).fetchall()
                
                previous_errors = conn.execute('''
                    SELECT category, COUNT(*) as count
                    FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    AND timestamp < datetime('now', '-{} hours')
                    GROUP BY category
                '''.format(hours * 2, hours)).fetchall()
                
                current_dict = dict(current_errors)
                previous_dict = dict(previous_errors)
                
                significant_changes = []
                for category in current_dict:
                    current_count = current_dict[category]
                    previous_count = previous_dict.get(category, 0)
                    
                    if previous_count > 0:
                        change_rate = (current_count - previous_count) / previous_count
                        if abs(change_rate) > 0.5:  # 50% 이상 변화
                            significant_changes.append({
                                'category': category,
                                'change_rate': change_rate,
                                'current': current_count,
                                'previous': previous_count
                            })
                
                if significant_changes:
                    # 가장 큰 변화를 찾음
                    max_change = max(significant_changes, key=lambda x: abs(x['change_rate']))
                    
                    if max_change['change_rate'] > 0:
                        return ErrorInsight(
                            insight_type='trend_increase',
                            title=f"{max_change['category']} 오류 급증",
                            description=f"{max_change['category']} 오류가 {max_change['change_rate']:.1%} 증가했습니다.",
                            severity='high',
                            recommendations=[
                                '해당 카테고리의 모니터링 강화',
                                '근본 원인 분석 수행',
                                '예방 조치 수립'
                            ],
                            confidence=min(abs(max_change['change_rate']), 1.0)
                        )
                    else:
                        return ErrorInsight(
                            insight_type='trend_decrease',
                            title=f"{max_change['category']} 오류 감소",
                            description=f"{max_change['category']} 오류가 {abs(max_change['change_rate']):.1%} 감소했습니다.",
                            severity='low',
                            recommendations=[
                                '현재 운영 상태 유지',
                                '최적화 방안 확산 적용'
                            ],
                            confidence=min(abs(max_change['change_rate']), 1.0)
                        )
        
        except Exception as e:
            logger.error(f"오류 트렌드 분석 실패: {e}")
        
        return None
    
    def _analyze_recovery_performance(self, hours: int) -> Optional[ErrorInsight]:
        """복구 성능 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 복구 성공률 계산
                total_attempts = conn.execute('''
                    SELECT COUNT(*) FROM recovery_attempts 
                    WHERE start_time >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                successful_attempts = conn.execute('''
                    SELECT COUNT(*) FROM recovery_attempts 
                    WHERE start_time >= datetime('now', '-{} hours')
                    AND status = 'success'
                '''.format(hours)).fetchone()[0]
                
                if total_attempts > 0:
                    success_rate = successful_attempts / total_attempts
                    
                    if success_rate < 0.7:  # 70% 미만
                        return ErrorInsight(
                            insight_type='recovery_performance',
                            title='자동 복구 성공률 저하',
                            description=f'자동 복구 성공률이 {success_rate:.1%}로 낮습니다.',
                            severity='high',
                            recommendations=[
                                '복구 로직 개선 검토',
                                '복구 전략 다양화',
                                '수동 개입 프로세스 강화'
                            ],
                            confidence=1.0 - success_rate
                        )
        
        except Exception as e:
            logger.error(f"복구 성능 분석 실패: {e}")
        
        return None
    
    def _analyze_notification_effectiveness(self, hours: int) -> Optional[ErrorInsight]:
        """알림 효과성 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 알림 전송 성공률
                total_notifications = conn.execute('''
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                successful_notifications = conn.execute('''
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= datetime('now', '-{} hours')
                    AND status = 'sent'
                '''.format(hours)).fetchone()[0]
                
                if total_notifications > 0:
                    success_rate = successful_notifications / total_notifications
                    
                    if success_rate < 0.9:  # 90% 미만
                        return ErrorInsight(
                            insight_type='notification_effectiveness',
                            title='알림 전송 성공률 저하',
                            description=f'알림 전송 성공률이 {success_rate:.1%}로 낮습니다.',
                            severity='medium',
                            recommendations=[
                                '알림 채널 상태 점검',
                                'Rate limit 설정 검토',
                                '백업 알림 채널 설정'
                            ],
                            confidence=1.0 - success_rate
                        )
        
        except Exception as e:
            logger.error(f"알림 효과성 분석 실패: {e}")
        
        return None
    
    def _analyze_resource_correlation(self, hours: int) -> Optional[ErrorInsight]:
        """리소스 상관관계 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 리소스 관련 오류와 시스템 메트릭 상관관계 분석
                resource_errors = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE category = 'resource_shortage'
                    AND timestamp >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                if resource_errors > 10:  # 충분한 데이터가 있을 때
                    # 평균 메모리 사용률과 오류 수 상관관계
                    memory_errors = conn.execute('''
                        SELECT COUNT(*) FROM error_events ee
                        JOIN system_metrics sm ON date(ee.timestamp) = date(sm.timestamp)
                        WHERE ee.category = 'resource_shortage'
                        AND ee.details LIKE '%memory%'
                        AND sm.metric_name = 'memory_usage'
                        AND ee.timestamp >= datetime('now', '-{} hours')
                    '''.format(hours)).fetchone()[0]
                    
                    if memory_errors > 5:
                        return ErrorInsight(
                            insight_type='resource_correlation',
                            title='메모리 사용률과 오류 상관관계 발견',
                            description='메모리 사용률이 높을 때 리소스 관련 오류가 증가합니다.',
                            severity='medium',
                            recommendations=[
                                '메모리 사용률 임계값 조정',
                                '메모리 정리 프로세스 강화',
                                '시스템 리소스 모니터링 개선'
                            ],
                            confidence=0.8
                        )
        
        except Exception as e:
            logger.error(f"리소스 상관관계 분석 실패: {e}")
        
        return None
    
    def _analyze_temporal_patterns(self, hours: int) -> Optional[ErrorInsight]:
        """시간대별 패턴 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 시간대별 오류 분포 분석
                hourly_errors = conn.execute('''
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY hour
                    ORDER BY count DESC
                '''.format(hours)).fetchall()
                
                if hourly_errors:
                    max_hour, max_count = hourly_errors[0]
                    avg_count = sum(count for _, count in hourly_errors) / len(hourly_errors)
                    
                    if max_count > avg_count * 1.5:  # 평균의 1.5배 이상
                        return ErrorInsight(
                            insight_type='temporal_pattern',
                            title=f'{max_hour}시 오류 집중 발생',
                            description=f'{max_hour}시에 오류가 집중적으로 발생합니다.',
                            severity='medium',
                            recommendations=[
                                f'{max_hour}시 모니터링 강화',
                                '시간대별 대응 전략 수립',
                                '예방적 조치 스케줄링'
                            ],
                            confidence=0.7
                        )
        
        except Exception as e:
            logger.error(f"시간대별 패턴 분석 실패: {e}")
        
        return None
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """일일 리포트 생성"""
        if date is None:
            date = datetime.now().date()
        
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기본 통계
                total_errors = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE timestamp >= ? AND timestamp <= ?
                ''', (start_time, end_time)).fetchone()[0]
                
                # 카테고리별 통계
                category_stats = {}
                for category in ErrorCategory:
                    count = conn.execute('''
                        SELECT COUNT(*) FROM error_events 
                        WHERE timestamp >= ? AND timestamp <= ?
                        AND category = ?
                    ''', (start_time, end_time, category.value)).fetchone()[0]
                    category_stats[category.value] = count
                
                # 심각도별 통계
                severity_stats = {}
                for severity in ErrorSeverity:
                    count = conn.execute('''
                        SELECT COUNT(*) FROM error_events 
                        WHERE timestamp >= ? AND timestamp <= ?
                        AND severity = ?
                    ''', (start_time, end_time, severity.value)).fetchone()[0]
                    severity_stats[severity.value] = count
                
                # 복구 통계
                recovery_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                        AVG(CASE WHEN end_time IS NOT NULL 
                            THEN (julianday(end_time) - julianday(start_time)) * 24 * 60 
                            ELSE NULL END) as avg_recovery_time_minutes
                    FROM recovery_attempts 
                    WHERE start_time >= ? AND start_time <= ?
                ''', (start_time, end_time)).fetchone()
                
                # 알림 통계
                notification_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_notifications,
                        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                        COUNT(DISTINCT channel) as channels_used
                    FROM notifications 
                    WHERE created_at >= ? AND created_at <= ?
                ''', (start_time, end_time)).fetchone()
                
                report = {
                    'date': date.isoformat(),
                    'summary': {
                        'total_errors': total_errors,
                        'total_recovery_attempts': recovery_stats[0] or 0,
                        'total_notifications': notification_stats[0] or 0
                    },
                    'error_breakdown': {
                        'by_category': category_stats,
                        'by_severity': severity_stats
                    },
                    'recovery_performance': {
                        'success_rate': (recovery_stats[1] / recovery_stats[0]) if recovery_stats[0] > 0 else 0,
                        'avg_recovery_time_minutes': recovery_stats[2] or 0
                    },
                    'notification_performance': {
                        'success_rate': (notification_stats[1] / notification_stats[0]) if notification_stats[0] > 0 else 0,
                        'channels_used': notification_stats[2] or 0
                    },
                    'insights': self.get_error_insights(24)
                }
                
                return report
        
        except Exception as e:
            logger.error(f"일일 리포트 생성 실패: {e}")
            return {}
    
    def cleanup_old_data(self):
        """오래된 데이터 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                # 오래된 오류 이벤트 삭제
                conn.execute('''
                    DELETE FROM error_events 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # 오래된 복구 시도 삭제
                conn.execute('''
                    DELETE FROM recovery_attempts 
                    WHERE start_time < ?
                ''', (cutoff_date,))
                
                # 오래된 알림 삭제
                conn.execute('''
                    DELETE FROM notifications 
                    WHERE created_at < ?
                ''', (cutoff_date,))
                
                # 오래된 시스템 메트릭 삭제
                conn.execute('''
                    DELETE FROM system_metrics 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                conn.commit()
                
                logger.info(f"{self.retention_days}일 이전 데이터 정리 완료")
        
        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")
    
    def get_system_health_score(self, hours: int = 24) -> Dict[str, Any]:
        """시스템 헬스 스코어 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 오류 발생 빈도 (낮을수록 좋음)
                error_count = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                # 복구 성공률 (높을수록 좋음)
                recovery_success_rate = self._calculate_recovery_success_rate(hours)
                
                # 알림 전송 성공률 (높을수록 좋음)
                notification_success_rate = self._calculate_notification_success_rate(hours)
                
                # 치명적 오류 비율 (낮을수록 좋음)
                critical_error_rate = self._calculate_critical_error_rate(hours)
                
                # 헬스 스코어 계산 (0-100)
                health_score = max(0, 100 - (
                    error_count * 2 +  # 오류 수 * 2점 감점
                    (1 - recovery_success_rate) * 30 +  # 복구 실패율 * 30점 감점
                    (1 - notification_success_rate) * 20 +  # 알림 실패율 * 20점 감점
                    critical_error_rate * 50  # 치명적 오류 비율 * 50점 감점
                ))
                
                return {
                    'health_score': min(100, max(0, health_score)),
                    'error_count': error_count,
                    'recovery_success_rate': recovery_success_rate,
                    'notification_success_rate': notification_success_rate,
                    'critical_error_rate': critical_error_rate,
                    'status': self._get_health_status(health_score)
                }
        
        except Exception as e:
            logger.error(f"헬스 스코어 계산 실패: {e}")
            return {'health_score': 0, 'status': 'error'}
    
    def _calculate_recovery_success_rate(self, hours: int) -> float:
        """복구 성공률 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute('''
                    SELECT COUNT(*) FROM recovery_attempts 
                    WHERE start_time >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                successful = conn.execute('''
                    SELECT COUNT(*) FROM recovery_attempts 
                    WHERE start_time >= datetime('now', '-{} hours')
                    AND status = 'success'
                '''.format(hours)).fetchone()[0]
                
                return successful / total if total > 0 else 1.0
        except:
            return 1.0
    
    def _calculate_notification_success_rate(self, hours: int) -> float:
        """알림 성공률 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute('''
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                successful = conn.execute('''
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= datetime('now', '-{} hours')
                    AND status = 'sent'
                '''.format(hours)).fetchone()[0]
                
                return successful / total if total > 0 else 1.0
        except:
            return 1.0
    
    def _calculate_critical_error_rate(self, hours: int) -> float:
        """치명적 오류 비율 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                '''.format(hours)).fetchone()[0]
                
                critical = conn.execute('''
                    SELECT COUNT(*) FROM error_events 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    AND severity = 'critical'
                '''.format(hours)).fetchone()[0]
                
                return critical / total if total > 0 else 0.0
        except:
            return 0.0
    
    def _get_health_status(self, score: float) -> str:
        """헬스 상태 결정"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
