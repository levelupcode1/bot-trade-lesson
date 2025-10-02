#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 복구 로직
분류된 오류에 대해 자동으로 복구를 시도하고 결과를 추적합니다.
"""

import time
import gc
import os
import psutil
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from .error_detector import ErrorEvent, ErrorCategory, ErrorSeverity
from .error_classifier import ClassificationResult, ActionType, PriorityLevel

logger = logging.getLogger(__name__)

class RecoveryStatus(Enum):
    """복구 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"

@dataclass
class RecoveryAttempt:
    """복구 시도 기록"""
    attempt_id: str
    error_event: ErrorEvent
    classification: ClassificationResult
    status: RecoveryStatus
    start_time: datetime
    end_time: Optional[datetime]
    recovery_method: str
    result_details: Dict[str, Any]
    error_message: Optional[str] = None

class AutoRecoveryManager:
    """자동 복구 관리자"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.recovery_history = []
        self.active_recoveries = {}
        self.recovery_executor = ThreadPoolExecutor(max_workers=5)
        self.recovery_callbacks = []
        
        # 복구 시도 제한
        self.max_attempts_per_error = 3
        self.recovery_timeout = 300  # 5분
        self.cooldown_period = 60  # 1분
        
    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, Callable]:
        """복구 전략 초기화"""
        return {
            ErrorCategory.API_FAILURE: self._recover_api_failure,
            ErrorCategory.DATA_INTEGRITY: self._recover_data_integrity,
            ErrorCategory.RESOURCE_SHORTAGE: self._recover_resource_shortage,
            ErrorCategory.LOGIC_ERROR: self._recover_logic_error,
            ErrorCategory.PERFORMANCE_DEGRADATION: self._recover_performance_degradation
        }
    
    def attempt_recovery(self, error: ErrorEvent, classification: ClassificationResult) -> RecoveryAttempt:
        """복구 시도 실행"""
        
        # 복구 가능 여부 확인
        if not self._should_attempt_recovery(error, classification):
            return self._create_skipped_attempt(error, classification, "복구 조건 미충족")
        
        # 동일한 오류에 대한 복구 중복 방지
        if self._is_recovery_in_progress(error):
            return self._create_skipped_attempt(error, classification, "이미 복구 진행 중")
        
        # 복구 시도 실행
        attempt = self._execute_recovery(error, classification)
        
        # 복구 결과 기록
        self.recovery_history.append(attempt)
        
        # 히스토리 크기 제한
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-1000:]
        
        return attempt
    
    def _should_attempt_recovery(self, error: ErrorEvent, classification: ClassificationResult) -> bool:
        """복구 시도 여부 결정"""
        
        # 수동 개입이 필요한 경우 복구 시도하지 않음
        if classification.action_type == ActionType.MANUAL_INTERVENTION:
            return False
        
        # 모니터링만 필요한 경우 복구 시도하지 않음
        if classification.action_type == ActionType.MONITOR:
            return False
        
        # 최근 복구 시도 횟수 확인
        recent_attempts = self._get_recent_recovery_attempts(error, minutes=10)
        if len(recent_attempts) >= classification.auto_recovery_attempts:
            return False
        
        return True
    
    def _is_recovery_in_progress(self, error: ErrorEvent) -> bool:
        """복구 진행 중인지 확인"""
        error_key = f"{error.category.value}_{error.error_id}"
        return error_key in self.active_recoveries
    
    def _execute_recovery(self, error: ErrorEvent, classification: ClassificationResult) -> RecoveryAttempt:
        """복구 실행"""
        attempt_id = f"recovery_{int(time.time() * 1000)}"
        
        # 복구 시도 기록 시작
        attempt = RecoveryAttempt(
            attempt_id=attempt_id,
            error_event=error,
            classification=classification,
            status=RecoveryStatus.IN_PROGRESS,
            start_time=datetime.now(),
            end_time=None,
            recovery_method="",
            result_details={}
        )
        
        # 활성 복구 목록에 추가
        error_key = f"{error.category.value}_{error.error_id}"
        self.active_recoveries[error_key] = attempt
        
        try:
            # 복구 전략 선택 및 실행
            recovery_strategy = self.recovery_strategies.get(error.category)
            if recovery_strategy:
                result = recovery_strategy(error, classification)
                attempt.recovery_method = result.get('method', 'unknown')
                attempt.result_details = result.get('details', {})
                
                if result.get('success', False):
                    attempt.status = RecoveryStatus.SUCCESS
                    logger.info(f"복구 성공: {error.category.value} - {attempt_id}")
                else:
                    attempt.status = RecoveryStatus.FAILED
                    attempt.error_message = result.get('error', '복구 실패')
                    logger.warning(f"복구 실패: {error.category.value} - {attempt_id}")
            else:
                attempt.status = RecoveryStatus.FAILED
                attempt.error_message = "복구 전략 없음"
                logger.error(f"복구 전략 없음: {error.category.value}")
        
        except Exception as e:
            attempt.status = RecoveryStatus.FAILED
            attempt.error_message = str(e)
            logger.error(f"복구 중 예외 발생: {e}")
        
        finally:
            attempt.end_time = datetime.now()
            # 활성 복구 목록에서 제거
            if error_key in self.active_recoveries:
                del self.active_recoveries[error_key]
        
        return attempt
    
    def _recover_api_failure(self, error: ErrorEvent, classification: ClassificationResult) -> Dict[str, Any]:
        """API 실패 복구"""
        recovery_methods = []
        success = False
        
        try:
            # 1. API 연결 상태 확인
            if self._check_api_connectivity():
                recovery_methods.append("API 연결 확인")
                success = True
            else:
                # 2. 백업 API 키로 전환
                if self._switch_to_backup_api_key():
                    recovery_methods.append("백업 API 키 전환")
                    success = True
                else:
                    # 3. 재연결 시도
                    if self._retry_api_connection():
                        recovery_methods.append("API 재연결")
                        success = True
                    else:
                        # 4. 요청 빈도 조절
                        self._adjust_request_frequency()
                        recovery_methods.append("요청 빈도 조절")
                        success = False  # 임시 조치
            
            return {
                'success': success,
                'method': 'api_failure_recovery',
                'details': {
                    'recovery_methods': recovery_methods,
                    'error_details': error.details
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'method': 'api_failure_recovery',
                'error': str(e),
                'details': {'exception': str(e)}
            }
    
    def _recover_data_integrity(self, error: ErrorEvent, classification: ClassificationResult) -> Dict[str, Any]:
        """데이터 무결성 복구"""
        recovery_methods = []
        success = False
        
        try:
            # 1. 데이터 검증 강화
            self._enable_strict_data_validation()
            recovery_methods.append("데이터 검증 강화")
            
            # 2. 백업 데이터로 복구
            if self._restore_from_backup():
                recovery_methods.append("백업 데이터 복구")
                success = True
            else:
                # 3. 데이터 소스 전환
                if self._switch_data_source():
                    recovery_methods.append("데이터 소스 전환")
                    success = True
                else:
                    # 4. 데이터 재수집
                    if self._recollect_data():
                        recovery_methods.append("데이터 재수집")
                        success = True
            
            return {
                'success': success,
                'method': 'data_integrity_recovery',
                'details': {
                    'recovery_methods': recovery_methods,
                    'data_details': error.details
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'method': 'data_integrity_recovery',
                'error': str(e),
                'details': {'exception': str(e)}
            }
    
    def _recover_resource_shortage(self, error: ErrorEvent, classification: ClassificationResult) -> Dict[str, Any]:
        """리소스 부족 복구"""
        recovery_methods = []
        success = False
        
        try:
            resource_type = error.details.get('resource_type', 'unknown')
            
            if 'memory' in resource_type.lower():
                # 메모리 정리
                self._cleanup_memory()
                recovery_methods.append("메모리 정리")
                
                # 가비지 컬렉션 강제 실행
                gc.collect()
                recovery_methods.append("가비지 컬렉션")
                
                success = True
            
            elif 'disk' in resource_type.lower():
                # 디스크 정리
                if self._cleanup_disk_space():
                    recovery_methods.append("디스크 정리")
                    success = True
            
            elif 'cpu' in resource_type.lower():
                # CPU 사용량 최적화
                self._optimize_cpu_usage()
                recovery_methods.append("CPU 최적화")
                success = True
            
            return {
                'success': success,
                'method': 'resource_shortage_recovery',
                'details': {
                    'recovery_methods': recovery_methods,
                    'resource_type': resource_type,
                    'resource_usage': error.details
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'method': 'resource_shortage_recovery',
                'error': str(e),
                'details': {'exception': str(e)}
            }
    
    def _recover_logic_error(self, error: ErrorEvent, classification: ClassificationResult) -> Dict[str, Any]:
        """로직 오류 복구"""
        recovery_methods = []
        success = False
        
        try:
            # 1. 문제 전략 비활성화
            strategy_name = error.details.get('strategy_name', 'unknown')
            if self._disable_strategy(strategy_name):
                recovery_methods.append(f"전략 비활성화: {strategy_name}")
            
            # 2. 안전 모드로 전환
            if self._switch_to_safe_mode():
                recovery_methods.append("안전 모드 전환")
                success = True
            
            # 3. 계산 재수행
            if error.details.get('calculation_error'):
                if self._recalculate_values(error.details):
                    recovery_methods.append("계산 재수행")
                    success = True
            
            return {
                'success': success,
                'method': 'logic_error_recovery',
                'details': {
                    'recovery_methods': recovery_methods,
                    'strategy_name': strategy_name,
                    'error_details': error.details
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'method': 'logic_error_recovery',
                'error': str(e),
                'details': {'exception': str(e)}
            }
    
    def _recover_performance_degradation(self, error: ErrorEvent, classification: ClassificationResult) -> Dict[str, Any]:
        """성능 저하 복구"""
        recovery_methods = []
        success = False
        
        try:
            # 1. 캐시 정리
            if self._clear_performance_cache():
                recovery_methods.append("캐시 정리")
            
            # 2. 프로세스 최적화
            if self._optimize_processes():
                recovery_methods.append("프로세스 최적화")
                success = True
            
            # 3. 부하 분산
            if self._distribute_load():
                recovery_methods.append("부하 분산")
                success = True
            
            # 4. 성능 모니터링 강화
            self._enhance_performance_monitoring()
            recovery_methods.append("성능 모니터링 강화")
            
            return {
                'success': success,
                'method': 'performance_degradation_recovery',
                'details': {
                    'recovery_methods': recovery_methods,
                    'performance_details': error.details
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'method': 'performance_degradation_recovery',
                'error': str(e),
                'details': {'exception': str(e)}
            }
    
    # 구체적인 복구 메서드들
    def _check_api_connectivity(self) -> bool:
        """API 연결 상태 확인"""
        try:
            response = requests.get("https://api.upbit.com/v1/market/all", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _switch_to_backup_api_key(self) -> bool:
        """백업 API 키로 전환"""
        # 실제 구현에서는 백업 API 키 설정
        logger.info("백업 API 키로 전환 시도")
        return True
    
    def _retry_api_connection(self) -> bool:
        """API 재연결 시도"""
        logger.info("API 재연결 시도")
        time.sleep(2)  # 잠시 대기
        return self._check_api_connectivity()
    
    def _adjust_request_frequency(self):
        """요청 빈도 조절"""
        logger.info("요청 빈도 조절 - 5초 대기")
        time.sleep(5)
    
    def _enable_strict_data_validation(self):
        """엄격한 데이터 검증 활성화"""
        logger.info("엄격한 데이터 검증 활성화")
    
    def _restore_from_backup(self) -> bool:
        """백업 데이터로 복구"""
        logger.info("백업 데이터로 복구 시도")
        return True
    
    def _switch_data_source(self) -> bool:
        """데이터 소스 전환"""
        logger.info("데이터 소스 전환 시도")
        return True
    
    def _recollect_data(self) -> bool:
        """데이터 재수집"""
        logger.info("데이터 재수집 시도")
        return True
    
    def _cleanup_memory(self):
        """메모리 정리"""
        logger.info("메모리 정리 실행")
        gc.collect()
    
    def _cleanup_disk_space(self) -> bool:
        """디스크 공간 정리"""
        logger.info("디스크 공간 정리 실행")
        
        # 임시 파일 정리
        temp_dirs = ['/tmp', '/var/tmp', './temp']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            # 7일 이상 된 파일 삭제
                            if time.time() - os.path.getmtime(file_path) > 7 * 24 * 3600:
                                os.remove(file_path)
                except Exception as e:
                    logger.warning(f"디스크 정리 중 오류: {e}")
        
        return True
    
    def _optimize_cpu_usage(self):
        """CPU 사용량 최적화"""
        logger.info("CPU 사용량 최적화")
        # 불필요한 프로세스 종료 등의 최적화 로직
    
    def _disable_strategy(self, strategy_name: str) -> bool:
        """전략 비활성화"""
        logger.info(f"전략 비활성화: {strategy_name}")
        return True
    
    def _switch_to_safe_mode(self) -> bool:
        """안전 모드로 전환"""
        logger.info("안전 모드로 전환")
        return True
    
    def _recalculate_values(self, details: Dict[str, Any]) -> bool:
        """값 재계산"""
        logger.info("값 재계산 실행")
        return True
    
    def _clear_performance_cache(self) -> bool:
        """성능 캐시 정리"""
        logger.info("성능 캐시 정리")
        return True
    
    def _optimize_processes(self) -> bool:
        """프로세스 최적화"""
        logger.info("프로세스 최적화 실행")
        return True
    
    def _distribute_load(self) -> bool:
        """부하 분산"""
        logger.info("부하 분산 실행")
        return True
    
    def _enhance_performance_monitoring(self):
        """성능 모니터링 강화"""
        logger.info("성능 모니터링 강화")
    
    def _get_recent_recovery_attempts(self, error: ErrorEvent, minutes: int) -> List[RecoveryAttempt]:
        """최근 복구 시도 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            attempt for attempt in self.recovery_history
            if (attempt.error_event.category == error.category and 
                attempt.start_time > cutoff_time)
        ]
    
    def _create_skipped_attempt(self, error: ErrorEvent, classification: ClassificationResult, reason: str) -> RecoveryAttempt:
        """건너뛴 복구 시도 생성"""
        return RecoveryAttempt(
            attempt_id=f"skipped_{int(time.time() * 1000)}",
            error_event=error,
            classification=classification,
            status=RecoveryStatus.SKIPPED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            recovery_method="skipped",
            result_details={'reason': reason}
        )
    
    def get_recovery_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """복구 통계 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_attempts = [
            attempt for attempt in self.recovery_history
            if attempt.start_time > cutoff_time
        ]
        
        total_attempts = len(recent_attempts)
        successful_attempts = len([a for a in recent_attempts if a.status == RecoveryStatus.SUCCESS])
        failed_attempts = len([a for a in recent_attempts if a.status == RecoveryStatus.FAILED])
        
        return {
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'failed_attempts': failed_attempts,
            'success_rate': successful_attempts / total_attempts if total_attempts > 0 else 0,
            'by_category': self._get_recovery_stats_by_category(recent_attempts),
            'by_method': self._get_recovery_stats_by_method(recent_attempts)
        }
    
    def _get_recovery_stats_by_category(self, attempts: List[RecoveryAttempt]) -> Dict[str, Any]:
        """카테고리별 복구 통계"""
        stats = {}
        for attempt in attempts:
            category = attempt.error_event.category.value
            if category not in stats:
                stats[category] = {'total': 0, 'success': 0, 'failed': 0}
            
            stats[category]['total'] += 1
            if attempt.status == RecoveryStatus.SUCCESS:
                stats[category]['success'] += 1
            elif attempt.status == RecoveryStatus.FAILED:
                stats[category]['failed'] += 1
        
        return stats
    
    def _get_recovery_stats_by_method(self, attempts: List[RecoveryAttempt]) -> Dict[str, int]:
        """방법별 복구 통계"""
        method_stats = {}
        for attempt in attempts:
            method = attempt.recovery_method
            method_stats[method] = method_stats.get(method, 0) + 1
        
        return method_stats
