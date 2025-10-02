#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 분석 시스템 오류 처리 모듈 (최적화 버전)
포괄적인 예외 처리, 복구 메커니즘, 로깅 시스템
"""

import logging
import traceback
import sys
import os
import gc
import psutil
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import functools
import warnings
from pathlib import Path
import json
import sqlite3
import pandas as pd
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """오류 심각도 레벨"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """오류 카테고리"""
    DATA = "DATA"
    MEMORY = "MEMORY"
    PERFORMANCE = "PERFORMANCE"
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    CALCULATION = "CALCULATION"
    VISUALIZATION = "VISUALIZATION"
    SYSTEM = "SYSTEM"

@dataclass
class ErrorInfo:
    """오류 정보 클래스"""
    timestamp: datetime = field(default_factory=datetime.now)
    error_type: str = ""
    error_message: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    recovery_attempted: bool = False
    recovery_successful: bool = False
    system_state: Dict[str, Any] = field(default_factory=dict)

class SystemMonitor:
    """시스템 모니터링 클래스"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        self.system_stats = []
        self.max_stats_history = 1000
    
    def start_monitoring(self, interval: float = 5.0):
        """시스템 모니터링 시작"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("시스템 모니터링 시작")
    
    def stop_monitoring(self):
        """시스템 모니터링 중지"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("시스템 모니터링 중지")
    
    def _monitor_loop(self, interval: float):
        """모니터링 루프"""
        while self.monitoring:
            try:
                stats = self.get_system_stats()
                self.system_stats.append(stats)
                
                # 히스토리 크기 제한
                if len(self.system_stats) > self.max_stats_history:
                    self.system_stats = self.system_stats[-self.max_stats_history:]
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"시스템 모니터링 오류: {e}")
                time.sleep(interval)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            return {
                'timestamp': datetime.now(),
                'memory_mb': memory_info.rss / 1024 / 1024,
                'memory_percent': self.process.memory_percent(),
                'cpu_percent': cpu_percent,
                'thread_count': self.process.num_threads(),
                'open_files': len(self.process.open_files()),
                'connections': len(self.process.connections())
            }
        except Exception as e:
            logger.error(f"시스템 상태 조회 오류: {e}")
            return {
                'timestamp': datetime.now(),
                'memory_mb': 0,
                'memory_percent': 0,
                'cpu_percent': 0,
                'thread_count': 0,
                'open_files': 0,
                'connections': 0
            }
    
    def get_current_stats(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        return self.get_system_stats()
    
    def get_stats_history(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """지정된 시간 동안의 시스템 상태 히스토리 반환"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [stats for stats in self.system_stats if stats['timestamp'] >= cutoff_time]

class RecoveryManager:
    """복구 관리자 클래스"""
    
    def __init__(self):
        self.recovery_strategies = {}
        self.recovery_history = []
        self.max_recovery_history = 100
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """복구 전략 등록"""
        self.recovery_strategies[error_type] = strategy
        logger.debug(f"복구 전략 등록: {error_type}")
    
    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """복구 시도"""
        recovery_attempted = False
        recovery_successful = False
        
        try:
            # 복구 전략 찾기
            strategy = self.recovery_strategies.get(error_info.error_type)
            if strategy:
                recovery_attempted = True
                logger.info(f"복구 시도: {error_info.error_type}")
                
                # 복구 실행
                result = strategy(error_info)
                recovery_successful = bool(result)
                
                if recovery_successful:
                    logger.info(f"복구 성공: {error_info.error_type}")
                else:
                    logger.warning(f"복구 실패: {error_info.error_type}")
            else:
                logger.debug(f"복구 전략 없음: {error_info.error_type}")
            
            # 복구 히스토리 기록
            recovery_record = {
                'timestamp': datetime.now(),
                'error_type': error_info.error_type,
                'attempted': recovery_attempted,
                'successful': recovery_successful
            }
            self.recovery_history.append(recovery_record)
            
            # 히스토리 크기 제한
            if len(self.recovery_history) > self.max_recovery_history:
                self.recovery_history = self.recovery_history[-self.max_recovery_history:]
            
            return recovery_successful
            
        except Exception as e:
            logger.error(f"복구 시도 중 오류: {e}")
            return False
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """복구 통계 반환"""
        if not self.recovery_history:
            return {'total_attempts': 0, 'success_rate': 0.0}
        
        total_attempts = len(self.recovery_history)
        successful_recoveries = sum(1 for record in self.recovery_history if record['successful'])
        success_rate = successful_recoveries / total_attempts if total_attempts > 0 else 0.0
        
        return {
            'total_attempts': total_attempts,
            'successful_recoveries': successful_recoveries,
            'success_rate': success_rate
        }

class OptimizedErrorHandler:
    """최적화된 오류 처리 클래스"""
    
    def __init__(self, log_file: str = "logs/error_handler.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 컴포넌트 초기화
        self.system_monitor = SystemMonitor()
        self.recovery_manager = RecoveryManager()
        self.error_history = []
        self.max_error_history = 500
        
        # 로깅 설정
        self._setup_logging()
        
        # 기본 복구 전략 등록
        self._register_default_recovery_strategies()
        
        # 시스템 모니터링 시작
        self.system_monitor.start_monitoring()
        
        logger.info("최적화된 오류 처리 시스템 초기화 완료")
    
    def _setup_logging(self):
        """로깅 설정"""
        # 파일 핸들러
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 로거에 핸들러 추가
        error_logger = logging.getLogger('error_handler')
        error_logger.addHandler(file_handler)
        error_logger.setLevel(logging.INFO)
    
    def _register_default_recovery_strategies(self):
        """기본 복구 전략 등록"""
        
        def memory_cleanup_recovery(error_info: ErrorInfo) -> bool:
            """메모리 정리 복구"""
            try:
                gc.collect()
                logger.info("메모리 정리 복구 실행")
                return True
            except Exception as e:
                logger.error(f"메모리 정리 복구 실패: {e}")
                return False
        
        def database_connection_recovery(error_info: ErrorInfo) -> bool:
            """데이터베이스 연결 복구"""
            try:
                # 데이터베이스 연결 재시도 로직
                context = error_info.context
                db_path = context.get('db_path')
                if db_path and Path(db_path).exists():
                    # 연결 테스트
                    with sqlite3.connect(db_path, timeout=5) as conn:
                        conn.execute("SELECT 1")
                    logger.info("데이터베이스 연결 복구 성공")
                    return True
                return False
            except Exception as e:
                logger.error(f"데이터베이스 연결 복구 실패: {e}")
                return False
        
        def data_validation_recovery(error_info: ErrorInfo) -> bool:
            """데이터 검증 복구"""
            try:
                context = error_info.context
                data = context.get('data')
                if data is not None:
                    # 데이터 정리 및 검증
                    if isinstance(data, pd.DataFrame):
                        data_cleaned = data.dropna()
                        context['cleaned_data'] = data_cleaned
                        logger.info("데이터 검증 복구 성공")
                        return True
                return False
            except Exception as e:
                logger.error(f"데이터 검증 복구 실패: {e}")
                return False
        
        # 복구 전략 등록
        self.recovery_manager.register_recovery_strategy("MemoryError", memory_cleanup_recovery)
        self.recovery_manager.register_recovery_strategy("sqlite3.OperationalError", database_connection_recovery)
        self.recovery_manager.register_recovery_strategy("ValueError", data_validation_recovery)
        self.recovery_manager.register_recovery_strategy("KeyError", data_validation_recovery)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.SYSTEM) -> ErrorInfo:
        """오류 처리"""
        try:
            # 오류 정보 생성
            error_info = ErrorInfo(
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                context=context or {},
                stack_trace=traceback.format_exc(),
                system_state=self.system_monitor.get_current_stats()
            )
            
            # 로깅
            self._log_error(error_info)
            
            # 복구 시도
            recovery_successful = self.recovery_manager.attempt_recovery(error_info)
            error_info.recovery_attempted = True
            error_info.recovery_successful = recovery_successful
            
            # 오류 히스토리 저장
            self._store_error_history(error_info)
            
            # 심각도에 따른 추가 처리
            self._handle_by_severity(error_info)
            
            return error_info
            
        except Exception as e:
            logger.critical(f"오류 처리 중 예외 발생: {e}")
            return ErrorInfo(
                error_type="CriticalError",
                error_message=f"오류 처리 실패: {e}",
                severity=ErrorSeverity.CRITICAL
            )
    
    def _log_error(self, error_info: ErrorInfo):
        """오류 로깅"""
        error_logger = logging.getLogger('error_handler')
        
        log_message = (
            f"[{error_info.severity.value}] {error_info.error_type}: {error_info.error_message} "
            f"| Category: {error_info.category.value} | "
            f"Context: {error_info.context}"
        )
        
        # 심각도에 따른 로그 레벨
        if error_info.severity == ErrorSeverity.CRITICAL:
            error_logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            error_logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            error_logger.warning(log_message)
        else:
            error_logger.info(log_message)
        
        # 스택 트레이스 로깅 (심각한 오류만)
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            error_logger.debug(f"Stack trace:\n{error_info.stack_trace}")
    
    def _store_error_history(self, error_info: ErrorInfo):
        """오류 히스토리 저장"""
        self.error_history.append(error_info)
        
        # 히스토리 크기 제한
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
    
    def _handle_by_severity(self, error_info: ErrorInfo):
        """심각도에 따른 추가 처리"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            # 치명적 오류: 시스템 상태 저장 및 알림
            self._save_critical_state(error_info)
            logger.critical("치명적 오류 발생 - 시스템 상태 저장됨")
        
        elif error_info.severity == ErrorSeverity.HIGH:
            # 높은 심각도: 추가 모니터링
            self.system_monitor.start_monitoring(interval=1.0)  # 1초 간격 모니터링
    
    def _save_critical_state(self, error_info: ErrorInfo):
        """치명적 상태 저장"""
        try:
            state_file = Path("logs/critical_state.json")
            critical_state = {
                'timestamp': datetime.now().isoformat(),
                'error_info': {
                    'error_type': error_info.error_type,
                    'error_message': error_info.error_message,
                    'severity': error_info.severity.value,
                    'category': error_info.category.value,
                    'context': error_info.context
                },
                'system_state': error_info.system_state,
                'recovery_stats': self.recovery_manager.get_recovery_stats(),
                'error_history_summary': self.get_error_summary()
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(critical_state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.critical(f"치명적 상태 저장 실패: {e}")
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """안전한 함수 실행"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'args': str(args)[:200],  # 길이 제한
                'kwargs': str(kwargs)[:200]
            }
            self.handle_error(e, context=context)
            return None
    
    def retry_with_backoff(self, func: Callable, max_retries: int = 3, 
                          backoff_factor: float = 2.0, *args, **kwargs) -> Any:
        """백오프를 사용한 재시도"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"실행 실패 (시도 {attempt + 1}/{max_retries + 1}), {wait_time}초 후 재시도")
                    time.sleep(wait_time)
                    
                    # 재시도 전 복구 시도
                    context = {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'max_retries': max_retries
                    }
                    self.handle_error(e, context=context, severity=ErrorSeverity.LOW)
                else:
                    logger.error(f"모든 재시도 실패: {func.__name__}")
        
        # 모든 재시도 실패
        context = {
            'function': func.__name__,
            'max_retries': max_retries,
            'final_error': str(last_exception)
        }
        self.handle_error(last_exception, context=context, severity=ErrorSeverity.HIGH)
        return None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """오류 요약 통계"""
        if not self.error_history:
            return {'total_errors': 0}
        
        # 카테고리별 통계
        category_counts = {}
        severity_counts = {}
        error_type_counts = {}
        
        for error in self.error_history:
            category = error.category.value
            severity = error.severity.value
            error_type = error.error_type
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        # 최근 오류 (24시간)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = [e for e in self.error_history if e.timestamp >= recent_cutoff]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors_24h': len(recent_errors),
            'category_breakdown': category_counts,
            'severity_breakdown': severity_counts,
            'error_type_breakdown': error_type_counts,
            'recovery_stats': self.recovery_manager.get_recovery_stats(),
            'system_stats': self.system_monitor.get_current_stats()
        }
    
    def get_system_health_report(self) -> str:
        """시스템 건강 상태 리포트"""
        error_summary = self.get_error_summary()
        recovery_stats = self.recovery_manager.get_recovery_stats()
        current_stats = self.system_monitor.get_current_stats()
        
        report = f"""
=== 시스템 건강 상태 리포트 ===
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 오류 통계
- 총 오류 수: {error_summary['total_errors']}
- 최근 24시간 오류: {error_summary['recent_errors_24h']}
- 복구 시도: {recovery_stats['total_attempts']}
- 복구 성공률: {recovery_stats['success_rate']:.1%}

💻 시스템 상태
- 메모리 사용량: {current_stats['memory_mb']:.1f}MB ({current_stats['memory_percent']:.1f}%)
- CPU 사용률: {current_stats['cpu_percent']:.1f}%
- 스레드 수: {current_stats['thread_count']}
- 열린 파일 수: {current_stats['open_files']}
- 네트워크 연결 수: {current_stats['connections']}

⚠️ 오류 카테고리 분포
"""
        
        for category, count in error_summary.get('category_breakdown', {}).items():
            report += f"- {category}: {count}건\n"
        
        report += "\n🚨 심각도 분포\n"
        for severity, count in error_summary.get('severity_breakdown', {}).items():
            report += f"- {severity}: {count}건\n"
        
        return report.strip()
    
    def cleanup_resources(self):
        """리소스 정리"""
        self.system_monitor.stop_monitoring()
        logger.info("오류 처리 시스템 리소스 정리 완료")

# 데코레이터들
def handle_errors(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM):
    """오류 처리 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 전역 오류 핸들러 인스턴스 찾기 (실제 구현에서는 의존성 주입 사용)
            error_handler = getattr(wrapper, '_error_handler', None)
            if not error_handler:
                error_handler = OptimizedErrorHandler()
                wrapper._error_handler = error_handler
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                error_handler.handle_error(e, context=context, severity=severity, category=category)
                return None
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """재시도 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = getattr(wrapper, '_error_handler', None)
            if not error_handler:
                error_handler = OptimizedErrorHandler()
                wrapper._error_handler = error_handler
            
            return error_handler.retry_with_backoff(
                func, max_retries=max_retries, backoff_factor=backoff_factor, *args, **kwargs
            )
        return wrapper
    return decorator

# 사용 예시
if __name__ == "__main__":
    import time
    
    # 오류 처리 시스템 초기화
    error_handler = OptimizedErrorHandler()
    
    # 테스트 함수들
    def test_memory_error():
        """메모리 오류 테스트"""
        raise MemoryError("테스트 메모리 오류")
    
    def test_database_error():
        """데이터베이스 오류 테스트"""
        raise sqlite3.OperationalError("테스트 데이터베이스 오류")
    
    def test_calculation_error():
        """계산 오류 테스트"""
        data = pd.DataFrame({'col1': [1, 2, np.nan, 4]})
        return data['nonexistent_col'].mean()  # KeyError 발생
    
    @handle_errors(severity=ErrorSeverity.LOW, category=ErrorCategory.CALCULATION)
    def test_decorator_function():
        """데코레이터 테스트 함수"""
        raise ValueError("데코레이터 테스트 오류")
    
    @retry_on_failure(max_retries=2, backoff_factor=1.5)
    def test_retry_function():
        """재시도 테스트 함수"""
        import random
        if random.random() < 0.7:  # 70% 확률로 실패
            raise RuntimeError("재시도 테스트 오류")
        return "성공!"
    
    # 오류 테스트 실행
    print("=== 오류 처리 시스템 테스트 ===")
    
    # 1. 메모리 오류 처리
    error_handler.handle_error(
        MemoryError("테스트 메모리 오류"),
        context={'test': 'memory_error'},
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.MEMORY
    )
    
    # 2. 데이터베이스 오류 처리
    error_handler.handle_error(
        sqlite3.OperationalError("데이터베이스 연결 실패"),
        context={'db_path': 'test.db', 'operation': 'connect'},
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DATABASE
    )
    
    # 3. 안전한 실행
    result = error_handler.safe_execute(test_memory_error)
    print(f"안전한 실행 결과: {result}")
    
    # 4. 재시도 실행
    result = error_handler.retry_with_backoff(test_retry_function)
    print(f"재시도 실행 결과: {result}")
    
    # 5. 데코레이터 테스트
    result = test_decorator_function()
    print(f"데코레이터 함수 결과: {result}")
    
    # 6. 재시도 데코레이터 테스트
    result = test_retry_function()
    print(f"재시도 데코레이터 결과: {result}")
    
    # 7. 시스템 상태 모니터링
    time.sleep(2)
    stats = error_handler.system_monitor.get_current_stats()
    print(f"시스템 상태: {stats}")
    
    # 8. 오류 요약
    summary = error_handler.get_error_summary()
    print(f"오류 요약: {summary}")
    
    # 9. 시스템 건강 리포트
    health_report = error_handler.get_system_health_report()
    print(health_report)
    
    # 리소스 정리
    error_handler.cleanup_resources()
    print("테스트 완료!")



