#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import random
import hashlib
import hmac
import jwt
import uuid

class RetryStrategy(Enum):
    """재시도 전략 열거형"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    CUSTOM = "custom"

class ErrorSeverity(Enum):
    """오류 심각도 열거형"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorType(Enum):
    """오류 타입 열거형"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class RetryConfig:
    """재시도 설정 클래스"""
    
    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                 jitter: bool = True,
                 backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.backoff_factor = backoff_factor

class ErrorLogger:
    """고급 오류 로깅 클래스"""
    
    def __init__(self, log_file: str = "api_errors.log"):
        self.log_file = log_file
        self.setup_logging()
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_severity': {},
            'retry_success_rate': 0.0
        }
        self.lock = threading.Lock()
    
    def setup_logging(self):
        """로깅 설정"""
        # 파일 핸들러
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 로거 설정
        self.logger = logging.getLogger('APIErrorLogger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_error(self, 
                  error: Exception, 
                  context: str = "",
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  error_type: ErrorType = ErrorType.UNKNOWN,
                  retry_count: int = 0,
                  additional_data: Dict = None):
        """오류 로깅"""
        with self.lock:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type.value,
                'severity': severity.value,
                'context': context,
                'retry_count': retry_count,
                'error_message': str(error),
                'error_class': type(error).__name__,
                'additional_data': additional_data or {}
            }
            
            # 로그 레벨 결정
            log_level = self._get_log_level(severity)
            getattr(self.logger, log_level)(json.dumps(error_entry, ensure_ascii=False))
            
            # 통계 업데이트
            self._update_stats(error_type, severity)
    
    def _get_log_level(self, severity: ErrorSeverity) -> str:
        """심각도에 따른 로그 레벨 결정"""
        level_mapping = {
            ErrorSeverity.LOW: 'debug',
            ErrorSeverity.MEDIUM: 'info',
            ErrorSeverity.HIGH: 'warning',
            ErrorSeverity.CRITICAL: 'error'
        }
        return level_mapping[severity]
    
    def _update_stats(self, error_type: ErrorType, severity: ErrorSeverity):
        """오류 통계 업데이트"""
        self.error_stats['total_errors'] += 1
        
        # 오류 타입별 카운트
        error_type_key = error_type.value
        self.error_stats['errors_by_type'][error_type_key] = \
            self.error_stats['errors_by_type'].get(error_type_key, 0) + 1
        
        # 심각도별 카운트
        severity_key = severity.value
        self.error_stats['errors_by_severity'][severity_key] = \
            self.error_stats['errors_by_severity'].get(severity_key, 0) + 1
    
    def get_stats(self) -> Dict:
        """오류 통계 조회"""
        with self.lock:
            return self.error_stats.copy()
    
    def export_errors(self, hours: int = 24) -> List[Dict]:
        """지정된 시간 동안의 오류 내보내기"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error_entry = json.loads(line.strip())
                        error_time = datetime.fromisoformat(error_entry['timestamp'])
                        if error_time > cutoff_time:
                            errors.append(error_entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except FileNotFoundError:
            pass
        
        return errors

class AdvancedRetryManager:
    """고급 재시도 관리자"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.retry_stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'average_retry_time': 0.0
        }
        self.lock = threading.Lock()
    
    def should_retry(self, 
                    error: Exception, 
                    attempt_count: int,
                    custom_retry_check: Callable = None) -> bool:
        """재시도 여부 판단"""
        # 최대 재시도 횟수 초과
        if attempt_count >= self.config.max_retries:
            return False
        
        # 커스텀 재시도 체크
        if custom_retry_check and not custom_retry_check(error, attempt_count):
            return False
        
        # 오류 타입별 재시도 가능성 판단
        return self._is_retryable_error(error)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """재시도 가능한 오류인지 판단"""
        if isinstance(error, requests.exceptions.ConnectionError):
            return True
        elif isinstance(error, requests.exceptions.Timeout):
            return True
        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = error.response.status_code
            # 5xx 서버 오류는 재시도 가능
            if 500 <= status_code < 600:
                return True
            # 429 Rate Limit은 재시도 가능
            elif status_code == 429:
                return True
            # 4xx 클라이언트 오류는 재시도 불가
            else:
                return False
        else:
            return False
    
    def calculate_delay(self, attempt_count: int) -> float:
        """재시도 지연 시간 계산"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** attempt_count)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt_count + 1)
        elif self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        else:
            delay = self.config.base_delay
        
        # 최대 지연 시간 제한
        delay = min(delay, self.config.max_delay)
        
        # 지터 추가 (랜덤성)
        if self.config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return delay
    
    def execute_with_retry(self, 
                          func: Callable,
                          *args,
                          **kwargs) -> Any:
        """재시도 로직이 포함된 함수 실행"""
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                with self.lock:
                    self.retry_stats['total_attempts'] += 1
                
                result = func(*args, **kwargs)
                
                # 성공 시 통계 업데이트
                if attempt > 0:
                    with self.lock:
                        self.retry_stats['successful_retries'] += 1
                        self.retry_stats['average_retry_time'] = \
                            (self.retry_stats['average_retry_time'] + (time.time() - start_time)) / 2
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 재시도 여부 판단
                if not self.should_retry(e, attempt):
                    with self.lock:
                        self.retry_stats['failed_retries'] += 1
                    break
                
                # 재시도 지연
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    time.sleep(delay)
        
        # 모든 재시도 실패
        raise last_exception
    
    def get_stats(self) -> Dict:
        """재시도 통계 조회"""
        with self.lock:
            return self.retry_stats.copy()

class CircuitBreaker:
    """서킷 브레이커 패턴 구현"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """서킷 브레이커를 통한 함수 호출"""
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    def _on_success(self):
        """성공 시 처리"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """실패 시 처리"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

class APIRecoveryManager:
    """API 복구 관리자"""
    
    def __init__(self):
        self.error_logger = ErrorLogger()
        self.retry_manager = AdvancedRetryManager()
        self.circuit_breakers = {}
        self.recovery_strategies = {}
        self.setup_recovery_strategies()
    
    def setup_recovery_strategies(self):
        """복구 전략 설정"""
        self.recovery_strategies = {
            ErrorType.NETWORK: self._handle_network_error,
            ErrorType.AUTHENTICATION: self._handle_auth_error,
            ErrorType.RATE_LIMIT: self._handle_rate_limit_error,
            ErrorType.SERVER_ERROR: self._handle_server_error,
            ErrorType.TIMEOUT: self._handle_timeout_error
        }
    
    def _handle_network_error(self, error: Exception, context: str) -> bool:
        """네트워크 오류 처리"""
        self.error_logger.log_error(
            error, context, ErrorSeverity.MEDIUM, ErrorType.NETWORK
        )
        return True  # 재시도 가능
    
    def _handle_auth_error(self, error: Exception, context: str) -> bool:
        """인증 오류 처리"""
        self.error_logger.log_error(
            error, context, ErrorSeverity.HIGH, ErrorType.AUTHENTICATION
        )
        # API 키 재설정 로직
        return False  # 재시도 불가
    
    def _handle_rate_limit_error(self, error: Exception, context: str) -> bool:
        """Rate Limit 오류 처리"""
        self.error_logger.log_error(
            error, context, ErrorSeverity.MEDIUM, ErrorType.RATE_LIMIT
        )
        # Rate Limit 대기 로직
        time.sleep(60)  # 1분 대기
        return True  # 재시도 가능
    
    def _handle_server_error(self, error: Exception, context: str) -> bool:
        """서버 오류 처리"""
        self.error_logger.log_error(
            error, context, ErrorSeverity.HIGH, ErrorType.SERVER_ERROR
        )
        return True  # 재시도 가능
    
    def _handle_timeout_error(self, error: Exception, context: str) -> bool:
        """타임아웃 오류 처리"""
        self.error_logger.log_error(
            error, context, ErrorSeverity.MEDIUM, ErrorType.TIMEOUT
        )
        return True  # 재시도 가능
    
    def execute_with_recovery(self, 
                             func: Callable,
                             context: str = "",
                             *args,
                             **kwargs) -> Any:
        """복구 메커니즘이 포함된 함수 실행"""
        try:
            return self.retry_manager.execute_with_retry(func, *args, **kwargs)
        except Exception as e:
            # 오류 타입 분류
            error_type = self._classify_error(e)
            
            # 복구 전략 실행
            if error_type in self.recovery_strategies:
                can_retry = self.recovery_strategies[error_type](e, context)
                if can_retry:
                    return self.retry_manager.execute_with_retry(func, *args, **kwargs)
            
            # 복구 불가능한 오류
            self.error_logger.log_error(
                e, context, ErrorSeverity.CRITICAL, error_type
            )
            raise e
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """오류 타입 분류"""
        if isinstance(error, requests.exceptions.ConnectionError):
            return ErrorType.NETWORK
        elif isinstance(error, requests.exceptions.Timeout):
            return ErrorType.TIMEOUT
        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = error.response.status_code
            if status_code == 401:
                return ErrorType.AUTHENTICATION
            elif status_code == 403:
                return ErrorType.AUTHORIZATION
            elif status_code == 429:
                return ErrorType.RATE_LIMIT
            elif 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
            else:
                return ErrorType.CLIENT_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def get_health_status(self) -> Dict:
        """시스템 건강 상태 조회"""
        error_stats = self.error_logger.get_stats()
        retry_stats = self.retry_manager.get_stats()
        
        return {
            'error_stats': error_stats,
            'retry_stats': retry_stats,
            'circuit_breakers': {
                name: {
                    'state': cb.state,
                    'failure_count': cb.failure_count
                } for name, cb in self.circuit_breakers.items()
            }
        }

# 사용 예시
def main():
    """오류 처리 및 복구 메커니즘 테스트"""
    try:
        # 복구 관리자 생성
        recovery_manager = APIRecoveryManager()
        
        print("🚀 API 오류 처리 및 복구 메커니즘 테스트")
        print("=" * 60)
        
        # 1. 재시도 로직 테스트
        print("\n🔄 재시도 로직 테스트...")
        
        def flaky_api_call():
            """불안정한 API 호출 시뮬레이션"""
            import random
            if random.random() < 0.7:  # 70% 확률로 실패
                raise requests.exceptions.ConnectionError("네트워크 오류")
            return "API 호출 성공"
        
        try:
            result = recovery_manager.execute_with_recovery(
                flaky_api_call, "flaky_api_test"
            )
            print(f"✅ 결과: {result}")
        except Exception as e:
            print(f"❌ 최종 실패: {e}")
        
        # 2. 오류 로깅 테스트
        print("\n📝 오류 로깅 테스트...")
        
        test_errors = [
            (requests.exceptions.ConnectionError("연결 실패"), "connection_test"),
            (requests.exceptions.Timeout("타임아웃"), "timeout_test"),
            (requests.exceptions.HTTPError("HTTP 오류"), "http_test"),
            (ValueError("값 오류"), "value_test")
        ]
        
        for error, context in test_errors:
            try:
                raise error
            except Exception as e:
                recovery_manager.error_logger.log_error(
                    e, context, ErrorSeverity.MEDIUM, ErrorType.UNKNOWN
                )
                print(f"📝 오류 로깅: {context}")
        
        # 3. 통계 조회
        print("\n📊 시스템 상태 조회...")
        health_status = recovery_manager.get_health_status()
        
        print("오류 통계:")
        for key, value in health_status['error_stats'].items():
            print(f"  {key}: {value}")
        
        print("\n재시도 통계:")
        for key, value in health_status['retry_stats'].items():
            print(f"  {key}: {value}")
        
        # 4. 오류 내보내기
        print("\n📤 오류 내보내기...")
        recent_errors = recovery_manager.error_logger.export_errors(hours=1)
        print(f"최근 1시간 오류 수: {len(recent_errors)}")
        
        print("\n✅ 오류 처리 및 복구 메커니즘 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")

if __name__ == "__main__":
    main()
