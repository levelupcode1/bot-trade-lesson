#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 오류 감지 모듈
실시간으로 시스템의 다양한 오류를 감지하고 분류합니다.
"""

import time
import psutil
import requests
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import statistics
from collections import deque, defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """오류 심각도 정의"""
    CRITICAL = "critical"    # 치명적 - 즉시 대응 필요
    HIGH = "high"           # 중요 - 빠른 대응 필요
    MEDIUM = "medium"       # 중간 - 적절한 대응 필요
    LOW = "low"            # 경미 - 모니터링 필요

class ErrorCategory(Enum):
    """오류 카테고리 정의"""
    API_FAILURE = "api_failure"
    DATA_INTEGRITY = "data_integrity"
    RESOURCE_SHORTAGE = "resource_shortage"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"

@dataclass
class ErrorEvent:
    """오류 이벤트 데이터 구조"""
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    source: str
    error_id: str = ""
    
    def __post_init__(self):
        if not self.error_id:
            self.error_id = f"{self.category.value}_{int(time.time() * 1000)}"

class ErrorDetector:
    """오류 감지 메인 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.error_queue = queue.Queue()
        self.running = False
        self.detectors = {}
        self.metrics_history = defaultdict(lambda: deque(maxlen=100))
        self.error_callbacks = []
        
        # 임계값 설정
        self.thresholds = {
            'api_response_time': 5.0,  # API 응답 시간 임계값 (초)
            'api_failure_rate': 0.1,   # API 실패율 임계값 (10%)
            'memory_usage': 80.0,      # 메모리 사용률 임계값 (%)
            'cpu_usage': 85.0,         # CPU 사용률 임계값 (%)
            'disk_usage': 90.0,        # 디스크 사용률 임계값 (%)
            'data_validation_failure': 0.05,  # 데이터 검증 실패율
            'logic_error_count': 1,    # 로직 오류 개수
            'performance_threshold': 2.0  # 성능 저하 임계값 (배수)
        }
        
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """오류 감지기 초기화"""
        self.detectors = {
            ErrorCategory.API_FAILURE: APIFailureDetector(self.thresholds),
            ErrorCategory.DATA_INTEGRITY: DataIntegrityDetector(self.thresholds),
            ErrorCategory.RESOURCE_SHORTAGE: ResourceDetector(self.thresholds),
            ErrorCategory.LOGIC_ERROR: LogicErrorDetector(self.thresholds),
            ErrorCategory.PERFORMANCE_DEGRADATION: PerformanceDetector(self.thresholds)
        }
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.running = True
        logger.info("오류 감지 시스템 시작")
        
        # 각 감지기별 모니터링 스레드 시작
        threads = []
        for category, detector in self.detectors.items():
            thread = threading.Thread(
                target=self._monitor_category,
                args=(category, detector),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # 메인 처리 스레드
        main_thread = threading.Thread(target=self._process_errors, daemon=True)
        main_thread.start()
        
        return threads + [main_thread]
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        logger.info("오류 감지 시스템 중지")
    
    def _monitor_category(self, category: ErrorCategory, detector):
        """카테고리별 모니터링"""
        while self.running:
            try:
                errors = detector.detect()
                for error in errors:
                    self.error_queue.put(error)
                
                time.sleep(detector.check_interval)
            except Exception as e:
                logger.error(f"{category.value} 감지기 오류: {e}")
                time.sleep(5)
    
    def _process_errors(self):
        """오류 이벤트 처리"""
        while self.running:
            try:
                if not self.error_queue.empty():
                    error = self.error_queue.get(timeout=1)
                    self._handle_error(error)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"오류 처리 중 예외 발생: {e}")
    
    def _handle_error(self, error: ErrorEvent):
        """개별 오류 이벤트 처리"""
        # 메트릭 기록
        self.metrics_history[f"{error.category.value}_{error.severity.value}"].append(error.timestamp)
        
        # 콜백 함수 호출
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"오류 콜백 실행 실패: {e}")
        
        logger.warning(f"오류 감지: {error.category.value} - {error.severity.value} - {error.message}")
    
    def add_error_callback(self, callback: Callable[[ErrorEvent], None]):
        """오류 콜백 함수 등록"""
        self.error_callbacks.append(callback)
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """오류 통계 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {}
        for key, timestamps in self.metrics_history.items():
            recent_errors = [ts for ts in timestamps if ts > cutoff_time]
            stats[key] = {
                'count': len(recent_errors),
                'rate_per_hour': len(recent_errors) / hours if hours > 0 else 0
            }
        
        return stats

class BaseDetector:
    """기본 감지기 클래스"""
    
    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds
        self.check_interval = 1  # 기본 체크 간격 (초)
        self.history = deque(maxlen=100)
    
    def detect(self) -> List[ErrorEvent]:
        """오류 감지 (서브클래스에서 구현)"""
        raise NotImplementedError

class APIFailureDetector(BaseDetector):
    """API 호출 실패 감지기"""
    
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__(thresholds)
        self.check_interval = 2
        self.failure_count = 0
        self.total_requests = 0
        self.response_times = deque(maxlen=50)
    
    def detect(self) -> List[ErrorEvent]:
        errors = []
        
        # API 응답 시간 체크
        if self.response_times:
            avg_response_time = statistics.mean(self.response_times)
            if avg_response_time > self.thresholds['api_response_time']:
                errors.append(ErrorEvent(
                    timestamp=datetime.now(),
                    category=ErrorCategory.API_FAILURE,
                    severity=ErrorSeverity.HIGH,
                    message=f"API 응답 시간 지연: {avg_response_time:.2f}초",
                    details={'avg_response_time': avg_response_time},
                    source='api_monitor'
                ))
        
        # API 실패율 체크
        if self.total_requests > 10:  # 최소 요청 수 확보 후 체크
            failure_rate = self.failure_count / self.total_requests
            if failure_rate > self.thresholds['api_failure_rate']:
                severity = ErrorSeverity.CRITICAL if failure_rate > 0.5 else ErrorSeverity.HIGH
                errors.append(ErrorEvent(
                    timestamp=datetime.now(),
                    category=ErrorCategory.API_FAILURE,
                    severity=severity,
                    message=f"API 실패율 높음: {failure_rate:.2%}",
                    details={'failure_rate': failure_rate, 'total_requests': self.total_requests},
                    source='api_monitor'
                ))
        
        return errors
    
    def record_api_call(self, response_time: float, success: bool):
        """API 호출 결과 기록"""
        self.response_times.append(response_time)
        self.total_requests += 1
        if not success:
            self.failure_count += 1

class DataIntegrityDetector(BaseDetector):
    """데이터 무결성 오류 감지기"""
    
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__(thresholds)
        self.check_interval = 5
        self.validation_failures = 0
        self.total_validations = 0
        self.last_valid_price = None
    
    def detect(self) -> List[ErrorEvent]:
        errors = []
        
        # 데이터 검증 실패율 체크
        if self.total_validations > 20:
            failure_rate = self.validation_failures / self.total_validations
            if failure_rate > self.thresholds['data_validation_failure']:
                errors.append(ErrorEvent(
                    timestamp=datetime.now(),
                    category=ErrorCategory.DATA_INTEGRITY,
                    severity=ErrorSeverity.HIGH,
                    message=f"데이터 검증 실패율 높음: {failure_rate:.2%}",
                    details={'failure_rate': failure_rate, 'total_validations': self.total_validations},
                    source='data_validator'
                ))
        
        return errors
    
    def record_data_validation(self, success: bool, data: Dict[str, Any] = None):
        """데이터 검증 결과 기록"""
        self.total_validations += 1
        if not success:
            self.validation_failures += 1
        
        # 가격 데이터 특별 검증
        if data and 'price' in data:
            self._validate_price_data(data['price'])
    
    def _validate_price_data(self, price: float):
        """가격 데이터 검증"""
        if price is None or price <= 0:
            self.validation_failures += 1
            return
        
        if self.last_valid_price:
            # 가격 급변 감지 (50% 이상 변동)
            price_change = abs(price - self.last_valid_price) / self.last_valid_price
            if price_change > 0.5:
                logger.warning(f"가격 급변 감지: {price_change:.2%}")
        
        self.last_valid_price = price

class ResourceDetector(BaseDetector):
    """시스템 리소스 감지기"""
    
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__(thresholds)
        self.check_interval = 10
    
    def detect(self) -> List[ErrorEvent]:
        errors = []
        
        # 메모리 사용률 체크
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.thresholds['memory_usage']:
            severity = ErrorSeverity.CRITICAL if memory_percent > 95 else ErrorSeverity.HIGH
            errors.append(ErrorEvent(
                timestamp=datetime.now(),
                category=ErrorCategory.RESOURCE_SHORTAGE,
                severity=severity,
                message=f"메모리 사용률 높음: {memory_percent:.1f}%",
                details={'memory_percent': memory_percent},
                source='system_monitor'
            ))
        
        # CPU 사용률 체크
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.thresholds['cpu_usage']:
            errors.append(ErrorEvent(
                timestamp=datetime.now(),
                category=ErrorCategory.RESOURCE_SHORTAGE,
                severity=ErrorSeverity.MEDIUM,
                message=f"CPU 사용률 높음: {cpu_percent:.1f}%",
                details={'cpu_percent': cpu_percent},
                source='system_monitor'
            ))
        
        # 디스크 사용률 체크
        disk_percent = psutil.disk_usage('/').percent
        if disk_percent > self.thresholds['disk_usage']:
            errors.append(ErrorEvent(
                timestamp=datetime.now(),
                category=ErrorCategory.RESOURCE_SHORTAGE,
                severity=ErrorSeverity.HIGH,
                message=f"디스크 사용률 높음: {disk_percent:.1f}%",
                details={'disk_percent': disk_percent},
                source='system_monitor'
            ))
        
        return errors

class LogicErrorDetector(BaseDetector):
    """로직 오류 감지기"""
    
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__(thresholds)
        self.check_interval = 30
        self.logic_errors = 0
        self.last_check_time = datetime.now()
    
    def detect(self) -> List[ErrorEvent]:
        errors = []
        
        # 로직 오류 카운트 체크
        if self.logic_errors >= self.thresholds['logic_error_count']:
            errors.append(ErrorEvent(
                timestamp=datetime.now(),
                category=ErrorCategory.LOGIC_ERROR,
                severity=ErrorSeverity.CRITICAL,
                message=f"로직 오류 발생: {self.logic_errors}개",
                details={'error_count': self.logic_errors},
                source='logic_validator'
            ))
            self.logic_errors = 0  # 리셋
        
        return errors
    
    def record_logic_error(self, error_details: Dict[str, Any]):
        """로직 오류 기록"""
        self.logic_errors += 1
        logger.error(f"로직 오류 발생: {error_details}")

class PerformanceDetector(BaseDetector):
    """성능 저하 감지기"""
    
    def __init__(self, thresholds: Dict[str, float]):
        super().__init__(thresholds)
        self.check_interval = 60
        self.performance_metrics = deque(maxlen=20)
        self.baseline_performance = None
    
    def detect(self) -> List[ErrorEvent]:
        errors = []
        
        if len(self.performance_metrics) < 5:
            return errors
        
        # 현재 성능과 기준 성능 비교
        current_performance = statistics.mean(list(self.performance_metrics)[-5:])
        
        if self.baseline_performance:
            performance_ratio = current_performance / self.baseline_performance
            if performance_ratio > self.thresholds['performance_threshold']:
                errors.append(ErrorEvent(
                    timestamp=datetime.now(),
                    category=ErrorCategory.PERFORMANCE_DEGRADATION,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"성능 저하 감지: 기준 대비 {performance_ratio:.2f}배",
                    details={'performance_ratio': performance_ratio, 'current': current_performance, 'baseline': self.baseline_performance},
                    source='performance_monitor'
                ))
        else:
            # 기준 성능 설정
            self.baseline_performance = current_performance
        
        return errors
    
    def record_performance_metric(self, metric: float):
        """성능 메트릭 기록"""
        self.performance_metrics.append(metric)
