#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오류 분류 엔진
감지된 오류를 분석하여 우선순위를 결정하고 적절한 대응 전략을 수립합니다.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict, Counter
import json

from .error_detector import ErrorEvent, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class PriorityLevel(Enum):
    """우선순위 레벨"""
    P0 = 0  # 즉시 처리 (치명적)
    P1 = 1  # 높음 (중요)
    P2 = 2  # 중간
    P3 = 3  # 낮음
    P4 = 4  # 정보

class ActionType(Enum):
    """대응 액션 타입"""
    AUTO_RECOVER = "auto_recover"
    MANUAL_INTERVENTION = "manual_intervention"
    ESCALATE = "escalate"
    MONITOR = "monitor"
    IGNORE = "ignore"

@dataclass
class ClassificationResult:
    """분류 결과"""
    priority: PriorityLevel
    action_type: ActionType
    auto_recovery_attempts: int
    escalation_timeout: int  # 초
    notification_channels: List[str]
    business_impact: str
    estimated_recovery_time: int  # 초
    recovery_strategy: str
    escalation_contacts: List[str]

class ErrorClassifier:
    """오류 분류 엔진"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classification_rules = self._load_classification_rules()
        self.error_patterns = self._load_error_patterns()
        self.business_rules = self._load_business_rules()
        self.error_history = defaultdict(list)
        self.pattern_frequency = Counter()
        
    def classify_error(self, error: ErrorEvent) -> ClassificationResult:
        """오류 분류 및 대응 전략 결정"""
        
        # 1. 기본 분류 규칙 적용
        base_classification = self._apply_basic_rules(error)
        
        # 2. 패턴 기반 분류
        pattern_classification = self._apply_pattern_rules(error)
        
        # 3. 비즈니스 규칙 적용
        business_classification = self._apply_business_rules(error)
        
        # 4. 히스토리 기반 조정
        history_adjustment = self._apply_history_analysis(error)
        
        # 5. 최종 분류 결과 결정
        final_result = self._combine_classifications(
            base_classification,
            pattern_classification,
            business_classification,
            history_adjustment
        )
        
        # 6. 히스토리 업데이트
        self._update_history(error, final_result)
        
        return final_result
    
    def _load_classification_rules(self) -> Dict[str, Any]:
        """기본 분류 규칙 로드"""
        return {
            # 심각도별 기본 우선순위
            ErrorSeverity.CRITICAL: {
                'priority': PriorityLevel.P0,
                'action_type': ActionType.AUTO_RECOVER,
                'auto_recovery_attempts': 3,
                'escalation_timeout': 300,  # 5분
                'notification_channels': ['telegram', 'sms', 'email'],
                'business_impact': '시스템 전체 중단 가능성',
                'estimated_recovery_time': 600,  # 10분
                'escalation_contacts': ['admin', 'dev_team']
            },
            ErrorSeverity.HIGH: {
                'priority': PriorityLevel.P1,
                'action_type': ActionType.AUTO_RECOVER,
                'auto_recovery_attempts': 2,
                'escalation_timeout': 900,  # 15분
                'notification_channels': ['telegram', 'email'],
                'business_impact': '서비스 품질 저하',
                'estimated_recovery_time': 1800,  # 30분
                'escalation_contacts': ['dev_team']
            },
            ErrorSeverity.MEDIUM: {
                'priority': PriorityLevel.P2,
                'action_type': ActionType.AUTO_RECOVER,
                'auto_recovery_attempts': 1,
                'escalation_timeout': 1800,  # 30분
                'notification_channels': ['email'],
                'business_impact': '성능 저하',
                'estimated_recovery_time': 3600,  # 1시간
                'escalation_contacts': []
            },
            ErrorSeverity.LOW: {
                'priority': PriorityLevel.P3,
                'action_type': ActionType.MONITOR,
                'auto_recovery_attempts': 0,
                'escalation_timeout': 0,
                'notification_channels': [],
                'business_impact': '최소한의 영향',
                'estimated_recovery_time': 7200,  # 2시간
                'escalation_contacts': []
            }
        }
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """오류 패턴 규칙 로드"""
        return {
            # API 관련 패턴
            'api_auth_failure': {
                'patterns': [r'invalid.*key', r'401', r'unauthorized', r'access.*denied'],
                'adjustments': {
                    'priority': PriorityLevel.P0,
                    'action_type': ActionType.MANUAL_INTERVENTION,
                    'escalation_timeout': 60  # 1분
                }
            },
            'api_rate_limit': {
                'patterns': [r'429', r'rate.*limit', r'too.*many.*requests'],
                'adjustments': {
                    'action_type': ActionType.AUTO_RECOVER,
                    'auto_recovery_attempts': 5,
                    'estimated_recovery_time': 300
                }
            },
            'api_server_error': {
                'patterns': [r'500', r'502', r'503', r'504', r'server.*error'],
                'adjustments': {
                    'priority': PriorityLevel.P1,
                    'auto_recovery_attempts': 3,
                    'escalation_timeout': 600
                }
            },
            
            # 데이터 관련 패턴
            'data_corruption': {
                'patterns': [r'corrupt', r'invalid.*data', r'price.*error'],
                'adjustments': {
                    'priority': PriorityLevel.P0,
                    'action_type': ActionType.MANUAL_INTERVENTION,
                    'business_impact': '잘못된 거래 실행 위험'
                }
            },
            'data_missing': {
                'patterns': [r'missing.*data', r'null.*value', r'empty.*response'],
                'adjustments': {
                    'priority': PriorityLevel.P1,
                    'auto_recovery_attempts': 2
                }
            },
            
            # 리소스 관련 패턴
            'memory_exhaustion': {
                'patterns': [r'memory.*full', r'out.*of.*memory', r'memory.*error'],
                'adjustments': {
                    'priority': PriorityLevel.P1,
                    'action_type': ActionType.AUTO_RECOVER,
                    'auto_recovery_attempts': 1,
                    'estimated_recovery_time': 120
                }
            },
            'disk_full': {
                'patterns': [r'disk.*full', r'no.*space', r'disk.*error'],
                'adjustments': {
                    'priority': PriorityLevel.P1,
                    'action_type': ActionType.AUTO_RECOVER
                }
            },
            
            # 로직 관련 패턴
            'calculation_error': {
                'patterns': [r'calculation.*error', r'divide.*by.*zero', r'math.*error'],
                'adjustments': {
                    'priority': PriorityLevel.P0,
                    'action_type': ActionType.MANUAL_INTERVENTION,
                    'business_impact': '잘못된 거래 계산 위험'
                }
            },
            'strategy_error': {
                'patterns': [r'strategy.*error', r'signal.*error', r'trading.*logic'],
                'adjustments': {
                    'priority': PriorityLevel.P1,
                    'action_type': ActionType.AUTO_RECOVER,
                    'auto_recovery_attempts': 1
                }
            }
        }
    
    def _load_business_rules(self) -> Dict[str, Any]:
        """비즈니스 규칙 로드"""
        return {
            'trading_hours': {
                'active_hours': [(9, 18)],  # 오전 9시 ~ 오후 6시
                'adjustments': {
                    'escalation_timeout_multiplier': 0.5,  # 거래 시간에는 더 빠른 대응
                    'notification_channels': ['telegram', 'sms', 'email']
                }
            },
            'weekend_handling': {
                'adjustments': {
                    'escalation_timeout_multiplier': 2.0,  # 주말에는 더 느린 대응
                    'notification_channels': ['email']
                }
            },
            'high_volatility': {
                'triggers': ['price_change_5min > 0.05'],  # 5분 내 5% 이상 변동
                'adjustments': {
                    'priority_boost': 1,  # 우선순위 1단계 상승
                    'escalation_timeout_multiplier': 0.3
                }
            }
        }
    
    def _apply_basic_rules(self, error: ErrorEvent) -> ClassificationResult:
        """기본 분류 규칙 적용"""
        base_rule = self.classification_rules.get(error.severity, {})
        
        return ClassificationResult(
            priority=base_rule.get('priority', PriorityLevel.P3),
            action_type=base_rule.get('action_type', ActionType.MONITOR),
            auto_recovery_attempts=base_rule.get('auto_recovery_attempts', 0),
            escalation_timeout=base_rule.get('escalation_timeout', 0),
            notification_channels=base_rule.get('notification_channels', []),
            business_impact=base_rule.get('business_impact', '알 수 없음'),
            estimated_recovery_time=base_rule.get('estimated_recovery_time', 3600),
            recovery_strategy='',
            escalation_contacts=base_rule.get('escalation_contacts', [])
        )
    
    def _apply_pattern_rules(self, error: ErrorEvent) -> Dict[str, Any]:
        """패턴 기반 분류 적용"""
        adjustments = {}
        
        # 오류 메시지에서 패턴 매칭
        error_text = f"{error.message} {json.dumps(error.details)}".lower()
        
        for pattern_name, pattern_rule in self.error_patterns.items():
            for pattern in pattern_rule['patterns']:
                if re.search(pattern, error_text, re.IGNORECASE):
                    adjustments.update(pattern_rule['adjustments'])
                    self.pattern_frequency[pattern_name] += 1
                    break
        
        return adjustments
    
    def _apply_business_rules(self, error: ErrorEvent) -> Dict[str, Any]:
        """비즈니스 규칙 적용"""
        adjustments = {}
        current_time = datetime.now()
        
        # 거래 시간 규칙
        current_hour = current_time.hour
        trading_rules = self.business_rules.get('trading_hours', {})
        
        if trading_rules.get('active_hours'):
            is_trading_hour = any(
                start <= current_hour < end 
                for start, end in trading_rules['active_hours']
            )
            
            if is_trading_hour:
                trading_adjustments = trading_rules.get('adjustments', {})
                adjustments.update(trading_adjustments)
        
        # 주말 처리
        if current_time.weekday() >= 5:  # 토요일(5) 또는 일요일(6)
            weekend_adjustments = self.business_rules.get('weekend_handling', {}).get('adjustments', {})
            adjustments.update(weekend_adjustments)
        
        # 고변동성 규칙 (실제 구현에서는 시장 데이터 확인 필요)
        # if self._is_high_volatility():
        #     volatility_adjustments = self.business_rules.get('high_volatility', {}).get('adjustments', {})
        #     adjustments.update(volatility_adjustments)
        
        return adjustments
    
    def _apply_history_analysis(self, error: ErrorEvent) -> Dict[str, Any]:
        """히스토리 기반 분석 적용"""
        adjustments = {}
        
        # 최근 1시간 내 동일한 오류 발생 빈도
        recent_errors = [
            e for e in self.error_history[error.category]
            if e.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_errors) > 5:  # 1시간 내 5회 이상 발생
            adjustments['priority_boost'] = 1  # 우선순위 상승
            adjustments['escalation_timeout_multiplier'] = 0.5  # 더 빠른 에스컬레이션
        
        # 동일한 패턴의 반복 발생
        error_pattern = f"{error.category.value}_{error.severity.value}"
        pattern_count = self.pattern_frequency.get(error_pattern, 0)
        
        if pattern_count > 10:  # 동일한 패턴이 10회 이상 발생
            adjustments['action_type'] = ActionType.ESCALATE
            adjustments['escalation_contacts'] = ['senior_dev', 'system_admin']
        
        return adjustments
    
    def _combine_classifications(self, base: ClassificationResult, 
                               pattern: Dict[str, Any], 
                               business: Dict[str, Any], 
                               history: Dict[str, Any]) -> ClassificationResult:
        """분류 결과 통합"""
        
        # 우선순위 조정
        priority = base.priority.value
        if 'priority_boost' in pattern:
            priority = max(0, priority - pattern['priority_boost'])
        if 'priority_boost' in history:
            priority = max(0, priority - history['priority_boost'])
        
        # 액션 타입 결정
        action_type = base.action_type
        if 'action_type' in pattern:
            action_type = ActionType(pattern['action_type'])
        if 'action_type' in history:
            action_type = ActionType(history['action_type'])
        
        # 에스컬레이션 타임아웃 조정
        escalation_timeout = base.escalation_timeout
        multipliers = []
        
        for adjustment in [pattern, business, history]:
            if 'escalation_timeout_multiplier' in adjustment:
                multipliers.append(adjustment['escalation_timeout_multiplier'])
        
        if multipliers:
            escalation_timeout = int(escalation_timeout * min(multipliers))
        
        # 알림 채널 통합
        notification_channels = set(base.notification_channels)
        for adjustment in [pattern, business, history]:
            if 'notification_channels' in adjustment:
                notification_channels.update(adjustment['notification_channels'])
        
        # 복구 전략 결정
        recovery_strategy = self._determine_recovery_strategy(
            base, pattern, business, history
        )
        
        return ClassificationResult(
            priority=PriorityLevel(priority),
            action_type=action_type,
            auto_recovery_attempts=pattern.get('auto_recovery_attempts', base.auto_recovery_attempts),
            escalation_timeout=escalation_timeout,
            notification_channels=list(notification_channels),
            business_impact=pattern.get('business_impact', base.business_impact),
            estimated_recovery_time=pattern.get('estimated_recovery_time', base.estimated_recovery_time),
            recovery_strategy=recovery_strategy,
            escalation_contacts=history.get('escalation_contacts', base.escalation_contacts)
        )
    
    def _determine_recovery_strategy(self, base: ClassificationResult,
                                   pattern: Dict[str, Any],
                                   business: Dict[str, Any],
                                   history: Dict[str, Any]) -> str:
        """복구 전략 결정"""
        
        # 오류 카테고리별 기본 전략
        strategies = {
            ErrorCategory.API_FAILURE: "API 재연결 및 백업 키 전환",
            ErrorCategory.DATA_INTEGRITY: "데이터 검증 강화 및 백업 데이터 사용",
            ErrorCategory.RESOURCE_SHORTAGE: "리소스 정리 및 최적화",
            ErrorCategory.LOGIC_ERROR: "전략 비활성화 및 안전 모드 전환",
            ErrorCategory.PERFORMANCE_DEGRADATION: "성능 최적화 및 부하 분산"
        }
        
        return strategies.get(
            base.priority.value,  # 여기서는 ErrorCategory를 사용해야 함
            "기본 복구 절차 수행"
        )
    
    def _update_history(self, error: ErrorEvent, classification: ClassificationResult):
        """히스토리 업데이트"""
        self.error_history[error.category].append(error)
        
        # 히스토리 크기 제한 (최근 1000개만 유지)
        if len(self.error_history[error.category]) > 1000:
            self.error_history[error.category] = self.error_history[error.category][-1000:]
    
    def get_classification_summary(self, hours: int = 24) -> Dict[str, Any]:
        """분류 요약 통계"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        summary = {
            'total_errors': 0,
            'by_category': defaultdict(int),
            'by_priority': defaultdict(int),
            'by_action_type': defaultdict(int),
            'top_patterns': dict(self.pattern_frequency.most_common(10)),
            'escalation_rate': 0,
            'auto_recovery_success_rate': 0
        }
        
        for category, errors in self.error_history.items():
            recent_errors = [e for e in errors if e.timestamp > cutoff_time]
            summary['total_errors'] += len(recent_errors)
            summary['by_category'][category.value] = len(recent_errors)
        
        return dict(summary)
