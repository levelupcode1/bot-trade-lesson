#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 시스템
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Callable
import logging
from threading import Thread, Event
import queue
import time


class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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


class AlertRule:
    """알림 규칙"""
    
    def __init__(self, name: str, condition: Callable, alert_type: AlertType, level: AlertLevel):
        """
        Args:
            name: 규칙 이름
            condition: 조건 함수 (metrics -> bool)
            alert_type: 알림 타입
            level: 알림 레벨
        """
        self.name = name
        self.condition = condition
        self.alert_type = alert_type
        self.level = level
        self.last_triggered: Optional[datetime] = None
        self.trigger_count = 0


class AlertSystem:
    """알림 시스템"""
    
    def __init__(self, cooldown_seconds: int = 300):
        """
        Args:
            cooldown_seconds: 동일 알림 재전송 대기 시간 (초)
        """
        self.cooldown_seconds = cooldown_seconds
        self.logger = logging.getLogger(__name__)
        
        # 알림 규칙
        self.rules: List[AlertRule] = []
        
        # 알림 히스토리
        self.alerts: List[Alert] = []
        
        # 알림 큐
        self.alert_queue = queue.Queue()
        
        # 알림 핸들러
        self.handlers: List[Callable] = []
        
        # 제어 플래그
        self._stop_event = Event()
        self._alert_thread: Optional[Thread] = None
        
        # 기본 규칙 등록
        self._register_default_rules()
        
        self.logger.info("알림 시스템 초기화 완료")
    
    def _register_default_rules(self):
        """기본 알림 규칙 등록"""
        
        # 성과 관련 규칙
        self.add_rule(AlertRule(
            name="high_drawdown",
            condition=lambda m: hasattr(m, 'current_drawdown') and m.current_drawdown < -0.05,
            alert_type=AlertType.RISK,
            level=AlertLevel.WARNING
        ))
        
        self.add_rule(AlertRule(
            name="critical_drawdown",
            condition=lambda m: hasattr(m, 'current_drawdown') and m.current_drawdown < -0.10,
            alert_type=AlertType.RISK,
            level=AlertLevel.CRITICAL
        ))
        
        self.add_rule(AlertRule(
            name="low_sharpe",
            condition=lambda m: hasattr(m, 'sharpe_ratio') and m.sharpe_ratio < 0,
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING
        ))
        
        self.add_rule(AlertRule(
            name="high_leverage",
            condition=lambda m: hasattr(m, 'leverage') and m.leverage > 2.0,
            alert_type=AlertType.RISK,
            level=AlertLevel.ERROR
        ))
        
        self.add_rule(AlertRule(
            name="low_win_rate",
            condition=lambda m: hasattr(m, 'win_rate') and m.total_trades > 20 and m.win_rate < 0.4,
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING
        ))
    
    def start(self):
        """알림 시스템 시작"""
        if self._alert_thread and self._alert_thread.is_alive():
            self.logger.warning("이미 실행 중입니다")
            return
        
        self._stop_event.clear()
        self._alert_thread = Thread(target=self._alert_loop, daemon=True)
        self._alert_thread.start()
        
        self.logger.info("알림 시스템 시작")
    
    def stop(self):
        """알림 시스템 중지"""
        self._stop_event.set()
        
        if self._alert_thread:
            self._alert_thread.join(timeout=5)
        
        self.logger.info("알림 시스템 중지")
    
    def _alert_loop(self):
        """알림 처리 루프"""
        while not self._stop_event.is_set():
            try:
                # 큐에서 알림 가져오기 (타임아웃 1초)
                alert = self.alert_queue.get(timeout=1)
                
                # 알림 전송
                self._send_alert(alert)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"알림 처리 오류: {e}")
    
    def check_metrics(self, metrics):
        """메트릭 확인 및 알림 생성"""
        now = datetime.now()
        
        for rule in self.rules:
            try:
                # 조건 확인
                if rule.condition(metrics):
                    # 쿨다운 체크
                    if rule.last_triggered:
                        elapsed = (now - rule.last_triggered).total_seconds()
                        if elapsed < self.cooldown_seconds:
                            continue  # 쿨다운 중
                    
                    # 알림 생성
                    alert = self._create_alert_from_rule(rule, metrics)
                    
                    # 규칙 상태 업데이트
                    rule.last_triggered = now
                    rule.trigger_count += 1
                    
                    # 알림 큐에 추가
                    try:
                        self.alert_queue.put_nowait(alert)
                    except queue.Full:
                        self.logger.warning("알림 큐가 가득 찼습니다")
                    
            except Exception as e:
                self.logger.error(f"규칙 '{rule.name}' 확인 오류: {e}")
    
    def _create_alert_from_rule(self, rule: AlertRule, metrics) -> Alert:
        """규칙으로부터 알림 생성"""
        
        # 규칙별 메시지 생성
        if rule.name == "high_drawdown":
            title = "⚠️ 높은 낙폭 감지"
            message = f"현재 낙폭: {metrics.current_drawdown:.2%}"
        
        elif rule.name == "critical_drawdown":
            title = "🚨 위험! 심각한 낙폭"
            message = f"현재 낙폭: {metrics.current_drawdown:.2%} - 즉시 확인 필요"
        
        elif rule.name == "low_sharpe":
            title = "📉 낮은 샤프 비율"
            message = f"현재 샤프 비율: {metrics.sharpe_ratio:.2f}"
        
        elif rule.name == "high_leverage":
            title = "⚠️ 높은 레버리지"
            message = f"현재 레버리지: {metrics.leverage:.2f}x"
        
        elif rule.name == "low_win_rate":
            title = "📊 낮은 승률"
            message = f"현재 승률: {metrics.win_rate:.2%} (총 거래: {metrics.total_trades})"
        
        else:
            title = f"알림: {rule.name}"
            message = "조건 충족"
        
        return Alert(
            timestamp=datetime.now(),
            level=rule.level,
            alert_type=rule.alert_type,
            title=title,
            message=message,
            data={
                'rule_name': rule.name,
                'trigger_count': rule.trigger_count
            }
        )
    
    def _send_alert(self, alert: Alert):
        """알림 전송"""
        # 알림 저장
        self.alerts.append(alert)
        
        # 히스토리 제한 (최근 1000개)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # 로그 출력
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emoji.get(alert.level, "📢")
        self.logger.info(f"{emoji} {alert.title}: {alert.message}")
        
        # 등록된 핸들러 실행
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"알림 핸들러 오류: {e}")
    
    def add_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        self.rules.append(rule)
        self.logger.info(f"알림 규칙 추가: {rule.name}")
    
    def add_handler(self, handler: Callable):
        """알림 핸들러 추가
        
        Args:
            handler: alert를 받는 콜백 함수
        """
        self.handlers.append(handler)
        self.logger.info("알림 핸들러 추가")
    
    def send_custom_alert(self, level: AlertLevel, alert_type: AlertType, title: str, message: str):
        """커스텀 알림 전송"""
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            alert_type=alert_type,
            title=title,
            message=message
        )
        
        try:
            self.alert_queue.put_nowait(alert)
        except queue.Full:
            self.logger.warning("알림 큐가 가득 찼습니다")
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """최근 알림 조회"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
    
    def get_alert_summary(self) -> Dict:
        """알림 요약"""
        recent_alerts = self.get_recent_alerts(60)
        
        summary = {
            'total': len(recent_alerts),
            'by_level': {},
            'by_type': {}
        }
        
        for alert in recent_alerts:
            # 레벨별
            level_key = alert.level.value
            if level_key not in summary['by_level']:
                summary['by_level'][level_key] = 0
            summary['by_level'][level_key] += 1
            
            # 타입별
            type_key = alert.alert_type.value
            if type_key not in summary['by_type']:
                summary['by_type'][type_key] = 0
            summary['by_type'][type_key] += 1
        
        return summary


# 텔레그램 알림 핸들러 (선택사항)
class TelegramHandler:
    """텔레그램 알림 핸들러"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, alert: Alert):
        """알림 전송"""
        try:
            # 실제 환경에서는 telegram API 호출
            # import requests
            # url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            # data = {
            #     "chat_id": self.chat_id,
            #     "text": f"{alert.title}\n\n{alert.message}"
            # }
            # requests.post(url, json=data)
            
            self.logger.info(f"[텔레그램] {alert.title}: {alert.message}")
        except Exception as e:
            self.logger.error(f"텔레그램 전송 실패: {e}")

