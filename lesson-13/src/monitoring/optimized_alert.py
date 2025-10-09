#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화된 알림 시스템

최적화 포인트:
1. 규칙 우선순위 시스템
2. 적응형 임계값 (동적 조정)
3. 알림 집계 (중복 방지)
4. 스마트 쿨다운 (상황별 다른 쿨다운)
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Set
import logging
from threading import Thread, Event, Lock
import queue
import time
import numpy as np
from collections import defaultdict


class AlertLevel(Enum):
    """알림 레벨"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AlertType(Enum):
    """알림 타입"""
    PERFORMANCE = "performance"
    RISK = "risk"
    SYSTEM = "system"
    TRADE = "trade"


@dataclass
class Alert:
    """알림"""
    timestamp: datetime
    level: AlertLevel
    alert_type: AlertType
    title: str
    message: str
    data: Dict = None
    priority: int = 0  # 우선순위 (높을수록 중요)


@dataclass
class AdaptiveRule:
    """적응형 알림 규칙"""
    name: str
    condition: Callable
    alert_type: AlertType
    level: AlertLevel
    priority: int = 0
    
    # 적응형 임계값
    threshold_value: float = 0.0
    adaptation_rate: float = 0.1  # 임계값 조정 속도
    
    # 쿨다운
    base_cooldown: int = 300  # 기본 5분
    cooldown_multiplier: float = 1.0  # 레벨별 배수
    
    # 상태
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    consecutive_triggers: int = 0
    
    # 히스토리 (적응형 학습용)
    trigger_history: List[datetime] = field(default_factory=list)


class OptimizedAlertSystem:
    """최적화된 알림 시스템"""
    
    def __init__(self, 
                 base_cooldown: int = 300,
                 max_alerts_per_minute: int = 10,
                 aggregation_window: int = 60):
        """
        Args:
            base_cooldown: 기본 쿨다운 시간 (초)
            max_alerts_per_minute: 분당 최대 알림 수
            aggregation_window: 알림 집계 윈도우 (초)
        """
        self.base_cooldown = base_cooldown
        self.max_alerts_per_minute = max_alerts_per_minute
        self.aggregation_window = aggregation_window
        
        self.logger = logging.getLogger(__name__)
        
        # 알림 규칙 (우선순위 큐)
        self.rules: List[AdaptiveRule] = []
        self.rules_lock = Lock()
        
        # 알림 히스토리
        self.alerts: List[Alert] = []
        self.alerts_lock = Lock()
        
        # 알림 큐 (우선순위)
        self.alert_queue = queue.PriorityQueue()
        
        # 알림 집계
        self._alert_aggregator: Dict[str, List[Alert]] = defaultdict(list)
        self._aggregator_lock = Lock()
        
        # 속도 제한
        self._alert_timestamps: List[datetime] = []
        self._rate_limit_lock = Lock()
        
        # 알림 핸들러
        self.handlers: List[Callable] = []
        
        # 제어
        self._stop_event = Event()
        self._alert_thread: Optional[Thread] = None
        
        # 성능 메트릭
        self.stats = {
            'total_alerts': 0,
            'suppressed_alerts': 0,
            'aggregated_alerts': 0,
            'avg_processing_time': 0
        }
        
        # 기본 규칙 등록
        self._register_adaptive_rules()
        
        self.logger.info("최적화된 알림 시스템 초기화")
    
    def _register_adaptive_rules(self):
        """적응형 규칙 등록"""
        
        # 위험 낙폭 (CRITICAL) - 최고 우선순위
        self.add_rule(AdaptiveRule(
            name="critical_drawdown",
            condition=lambda m: hasattr(m, 'current_drawdown') and m.current_drawdown < -0.10,
            alert_type=AlertType.RISK,
            level=AlertLevel.CRITICAL,
            priority=100,
            threshold_value=-0.10,
            cooldown_multiplier=0.5  # 더 짧은 쿨다운
        ))
        
        # 높은 낙폭 (WARNING)
        self.add_rule(AdaptiveRule(
            name="high_drawdown",
            condition=lambda m: hasattr(m, 'current_drawdown') and m.current_drawdown < -0.05,
            alert_type=AlertType.RISK,
            level=AlertLevel.WARNING,
            priority=80,
            threshold_value=-0.05,
            adaptation_rate=0.05  # 천천히 적응
        ))
        
        # 낮은 샤프 비율
        self.add_rule(AdaptiveRule(
            name="low_sharpe",
            condition=lambda m: hasattr(m, 'sharpe_ratio') and m.sharpe_ratio < 0,
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING,
            priority=60,
            threshold_value=0.0
        ))
        
        # 높은 레버리지
        self.add_rule(AdaptiveRule(
            name="high_leverage",
            condition=lambda m: hasattr(m, 'leverage') and m.leverage > 2.0,
            alert_type=AlertType.RISK,
            level=AlertLevel.ERROR,
            priority=90,
            threshold_value=2.0
        ))
    
    def start(self):
        """알림 시스템 시작"""
        if self._alert_thread and self._alert_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._alert_thread = Thread(target=self._alert_loop, daemon=True)
        self._alert_thread.start()
        
        self.logger.info("최적화된 알림 시스템 시작")
    
    def stop(self):
        """알림 시스템 중지"""
        self._stop_event.set()
        
        if self._alert_thread:
            self._alert_thread.join(timeout=5)
        
        # 남은 집계 알림 플러시
        self._flush_aggregated_alerts()
        
        self.logger.info("최적화된 알림 시스템 중지")
    
    def _alert_loop(self):
        """알림 처리 루프"""
        while not self._stop_event.is_set():
            try:
                # 우선순위 큐에서 알림 가져오기 (타임아웃 1초)
                priority, alert = self.alert_queue.get(timeout=1)
                
                # 속도 제한 확인
                if self._check_rate_limit():
                    # 알림 전송
                    start_time = time.time()
                    self._send_alert(alert)
                    elapsed = time.time() - start_time
                    
                    # 성능 메트릭 업데이트
                    self._update_processing_time(elapsed)
                else:
                    # 속도 제한 초과 - 억제
                    self.stats['suppressed_alerts'] += 1
                    self.logger.warning(f"알림 속도 제한 초과: {alert.title}")
                
            except queue.Empty:
                # 집계 알림 처리
                self._process_aggregated_alerts()
                continue
            except Exception as e:
                self.logger.error(f"알림 처리 오류: {e}")
    
    def check_metrics(self, metrics):
        """메트릭 확인 및 알림 생성 (최적화)"""
        now = datetime.now()
        
        with self.rules_lock:
            # 우선순위순으로 정렬
            sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            try:
                # 조건 확인
                if rule.condition(metrics):
                    # 스마트 쿨다운 체크
                    if self._check_smart_cooldown(rule, now):
                        continue
                    
                    # 알림 생성
                    alert = self._create_alert_from_rule(rule, metrics)
                    
                    # 규칙 상태 업데이트
                    self._update_rule_state(rule, now)
                    
                    # 집계 가능한 알림인지 확인
                    if self._should_aggregate(alert):
                        self._aggregate_alert(alert)
                    else:
                        # 즉시 전송 (우선순위 큐에 추가)
                        self.alert_queue.put((-rule.priority, alert))
                
                else:
                    # 조건 충족 안 함 - 연속 트리거 리셋
                    rule.consecutive_triggers = 0
                    
            except Exception as e:
                self.logger.error(f"규칙 '{rule.name}' 확인 오류: {e}")
    
    def _check_smart_cooldown(self, rule: AdaptiveRule, now: datetime) -> bool:
        """스마트 쿨다운 확인"""
        if not rule.last_triggered:
            return False
        
        # 레벨별 쿨다운 배수
        level_multipliers = {
            AlertLevel.INFO: 2.0,
            AlertLevel.WARNING: 1.5,
            AlertLevel.ERROR: 1.0,
            AlertLevel.CRITICAL: 0.5
        }
        
        cooldown = (
            self.base_cooldown * 
            rule.cooldown_multiplier * 
            level_multipliers.get(rule.level, 1.0)
        )
        
        # 연속 트리거 시 쿨다운 증가 (exponential backoff)
        if rule.consecutive_triggers > 1:
            cooldown *= (1.5 ** (rule.consecutive_triggers - 1))
        
        elapsed = (now - rule.last_triggered).total_seconds()
        return elapsed < cooldown
    
    def _check_rate_limit(self) -> bool:
        """속도 제한 확인"""
        with self._rate_limit_lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)
            
            # 1분 이내 알림 필터링
            self._alert_timestamps = [
                ts for ts in self._alert_timestamps if ts > cutoff
            ]
            
            # 제한 확인
            if len(self._alert_timestamps) >= self.max_alerts_per_minute:
                return False
            
            self._alert_timestamps.append(now)
            return True
    
    def _should_aggregate(self, alert: Alert) -> bool:
        """알림 집계 여부 확인"""
        # CRITICAL은 즉시 전송
        if alert.level == AlertLevel.CRITICAL:
            return False
        
        # INFO는 집계
        if alert.level == AlertLevel.INFO:
            return True
        
        # WARNING/ERROR는 조건부 집계
        return alert.alert_type in [AlertType.PERFORMANCE, AlertType.TRADE]
    
    def _aggregate_alert(self, alert: Alert):
        """알림 집계"""
        with self._aggregator_lock:
            key = f"{alert.alert_type.value}_{alert.level.value}"
            self._alert_aggregator[key].append(alert)
            
            self.stats['aggregated_alerts'] += 1
    
    def _process_aggregated_alerts(self):
        """집계된 알림 처리"""
        with self._aggregator_lock:
            for key, alerts in self._alert_aggregator.items():
                if not alerts:
                    continue
                
                # 오래된 알림 플러시
                first_alert_time = alerts[0].timestamp
                if (datetime.now() - first_alert_time).total_seconds() > self.aggregation_window:
                    self._flush_aggregated_key(key)
    
    def _flush_aggregated_key(self, key: str):
        """특정 키의 집계 알림 플러시"""
        alerts = self._alert_aggregator[key]
        
        if len(alerts) == 1:
            # 단일 알림
            self.alert_queue.put((-alerts[0].priority, alerts[0]))
        else:
            # 여러 알림 집계
            aggregated = Alert(
                timestamp=datetime.now(),
                level=alerts[0].level,
                alert_type=alerts[0].alert_type,
                title=f"📦 집계 알림 ({len(alerts)}개)",
                message=f"{alerts[0].title} 외 {len(alerts)-1}개 알림",
                priority=alerts[0].priority
            )
            self.alert_queue.put((-aggregated.priority, aggregated))
        
        # 집계 초기화
        self._alert_aggregator[key] = []
    
    def _flush_aggregated_alerts(self):
        """모든 집계 알림 플러시"""
        with self._aggregator_lock:
            for key in list(self._alert_aggregator.keys()):
                if self._alert_aggregator[key]:
                    self._flush_aggregated_key(key)
    
    def _create_alert_from_rule(self, rule: AdaptiveRule, metrics) -> Alert:
        """규칙으로부터 알림 생성"""
        # 규칙별 메시지
        messages = {
            "critical_drawdown": ("🚨 위험! 심각한 낙폭", f"현재 낙폭: {metrics.current_drawdown:.2%}"),
            "high_drawdown": ("⚠️ 높은 낙폭 감지", f"현재 낙폭: {metrics.current_drawdown:.2%}"),
            "low_sharpe": ("📉 낮은 샤프 비율", f"현재 샤프: {metrics.sharpe_ratio:.2f}"),
            "high_leverage": ("⚠️ 높은 레버리지", f"현재 레버리지: {metrics.leverage:.2f}x")
        }
        
        title, message = messages.get(rule.name, (f"알림: {rule.name}", "조건 충족"))
        
        return Alert(
            timestamp=datetime.now(),
            level=rule.level,
            alert_type=rule.alert_type,
            title=title,
            message=message,
            priority=rule.priority,
            data={'rule_name': rule.name, 'trigger_count': rule.trigger_count}
        )
    
    def _update_rule_state(self, rule: AdaptiveRule, now: datetime):
        """규칙 상태 업데이트"""
        rule.last_triggered = now
        rule.trigger_count += 1
        rule.consecutive_triggers += 1
        rule.trigger_history.append(now)
        
        # 히스토리 제한 (최근 100개)
        if len(rule.trigger_history) > 100:
            rule.trigger_history = rule.trigger_history[-100:]
    
    def _send_alert(self, alert: Alert):
        """알림 전송"""
        with self.alerts_lock:
            self.alerts.append(alert)
            
            # 히스토리 제한
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]
        
        self.stats['total_alerts'] += 1
        
        # 로그
        emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }[alert.level]
        
        self.logger.info(f"{emoji} {alert.title}: {alert.message}")
        
        # 핸들러 실행
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"알림 핸들러 오류: {e}")
    
    def _update_processing_time(self, elapsed: float):
        """처리 시간 업데이트"""
        alpha = 0.1
        if self.stats['avg_processing_time'] == 0:
            self.stats['avg_processing_time'] = elapsed
        else:
            self.stats['avg_processing_time'] = (
                alpha * elapsed + (1 - alpha) * self.stats['avg_processing_time']
            )
    
    def add_rule(self, rule: AdaptiveRule):
        """알림 규칙 추가"""
        with self.rules_lock:
            self.rules.append(rule)
        
        self.logger.info(f"알림 규칙 추가: {rule.name} (우선순위: {rule.priority})")
    
    def add_handler(self, handler: Callable):
        """알림 핸들러 추가"""
        self.handlers.append(handler)
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """최근 알림 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.alerts_lock:
            return [a for a in self.alerts if a.timestamp >= cutoff_time]
    
    def get_stats(self) -> Dict:
        """알림 시스템 통계"""
        return {
            **self.stats,
            'active_rules': len(self.rules),
            'suppression_rate': (
                self.stats['suppressed_alerts'] / 
                max(1, self.stats['total_alerts'] + self.stats['suppressed_alerts'])
            ) * 100,
            'aggregation_rate': (
                self.stats['aggregated_alerts'] / 
                max(1, self.stats['total_alerts'])
            ) * 100
        }

