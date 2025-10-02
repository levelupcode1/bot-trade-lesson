#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오류 관리 시스템 테스트
"""

import time
import sys
import os
from datetime import datetime
from typing import Dict, Any
import logging

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_system import ErrorManagementSystem
from error_detector import ErrorCategory, ErrorSeverity

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_error_management_system():
    """오류 관리 시스템 테스트"""
    
    # 테스트 설정
    config = {
        'database_path': 'test_error_management.db',
        'retention_days': 7,
        'telegram_bot_token': 'test_token',
        'smtp': {
            'host': 'localhost',
            'port': 587,
            'use_tls': False,
            'username': 'test@example.com',
            'password': 'test_password',
            'from_email': 'test@example.com'
        },
        'sms': {
            'url': 'http://localhost:8000/sms',
            'api_key': 'test_api_key'
        },
        'webhook_url': 'http://localhost:8000/webhook'
    }
    
    logger.info("오류 관리 시스템 테스트 시작")
    
    try:
        # 시스템 초기화
        system = ErrorManagementSystem(config)
        
        # 시스템 시작
        system.start()
        logger.info("시스템 시작 완료")
        
        # 잠시 대기 (시스템 초기화 시간)
        time.sleep(2)
        
        # 테스트 오류 발생
        logger.info("테스트 오류 발생 중...")
        
        # 1. API 실패 테스트
        logger.info("1. API 실패 테스트")
        system.trigger_test_error(ErrorCategory.API_FAILURE, ErrorSeverity.CRITICAL)
        time.sleep(3)
        
        # 2. 데이터 무결성 오류 테스트
        logger.info("2. 데이터 무결성 오류 테스트")
        system.trigger_test_error(ErrorCategory.DATA_INTEGRITY, ErrorSeverity.HIGH)
        time.sleep(3)
        
        # 3. 리소스 부족 테스트
        logger.info("3. 리소스 부족 테스트")
        system.trigger_test_error(ErrorCategory.RESOURCE_SHORTAGE, ErrorSeverity.MEDIUM)
        time.sleep(3)
        
        # 4. 로직 오류 테스트
        logger.info("4. 로직 오류 테스트")
        system.trigger_test_error(ErrorCategory.LOGIC_ERROR, ErrorSeverity.HIGH)
        time.sleep(3)
        
        # 5. 성능 저하 테스트
        logger.info("5. 성능 저하 테스트")
        system.trigger_test_error(ErrorCategory.PERFORMANCE_DEGRADATION, ErrorSeverity.MEDIUM)
        time.sleep(3)
        
        # 시스템 상태 조회
        logger.info("시스템 상태 조회")
        status = system.get_system_status()
        logger.info(f"시스템 상태: {status['system_status']}")
        logger.info(f"헬스 스코어: {status['health_score']['health_score']:.1f}")
        logger.info(f"활성 스레드 수: {status['active_threads']}")
        
        # 통계 정보 출력
        logger.info("=== 오류 통계 ===")
        error_stats = status['error_statistics']
        for key, value in error_stats.items():
            logger.info(f"{key}: {value}")
        
        logger.info("=== 복구 통계 ===")
        recovery_stats = status['recovery_statistics']
        logger.info(f"총 복구 시도: {recovery_stats['total_attempts']}")
        logger.info(f"성공한 복구: {recovery_stats['successful_attempts']}")
        logger.info(f"복구 성공률: {recovery_stats['success_rate']:.2%}")
        
        logger.info("=== 알림 통계 ===")
        notification_stats = status['notification_statistics']
        logger.info(f"총 알림: {notification_stats['total_sent'] + notification_stats['total_failed']}")
        logger.info(f"성공한 알림: {notification_stats['total_sent']}")
        logger.info(f"실패한 알림: {notification_stats['total_failed']}")
        logger.info(f"알림 성공률: {notification_stats['success_rate']:.2%}")
        
        # 추가 테스트 시간
        logger.info("추가 모니터링 시간 (10초)...")
        time.sleep(10)
        
        # 최종 상태 조회
        final_status = system.get_system_status()
        logger.info("=== 최종 시스템 상태 ===")
        logger.info(f"헬스 스코어: {final_status['health_score']['health_score']:.1f}")
        logger.info(f"헬스 상태: {final_status['health_score']['status']}")
        
        # 시스템 중지
        logger.info("시스템 중지 중...")
        system.stop()
        logger.info("시스템 중지 완료")
        
        logger.info("✅ 모든 테스트 완료!")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_individual_components():
    """개별 컴포넌트 테스트"""
    logger.info("개별 컴포넌트 테스트 시작")
    
    try:
        from error_detector import ErrorDetector, ErrorEvent, ErrorCategory, ErrorSeverity
        from error_classifier import ErrorClassifier
        from auto_recovery import AutoRecoveryManager
        from notification_system import NotificationManager
        from error_analytics import ErrorAnalytics
        
        config = {'database_path': 'test_components.db'}
        
        # 1. 오류 감지기 테스트
        logger.info("1. 오류 감지기 테스트")
        detector = ErrorDetector(config)
        
        # API 실패 감지기 테스트
        api_detector = detector.detectors[ErrorCategory.API_FAILURE]
        api_detector.record_api_call(6.0, False)  # 6초 응답, 실패
        api_detector.record_api_call(2.0, False)  # 2초 응답, 실패
        api_detector.record_api_call(1.0, True)   # 1초 응답, 성공
        
        errors = api_detector.detect()
        logger.info(f"API 감지기에서 {len(errors)}개 오류 감지")
        
        # 2. 오류 분류기 테스트
        logger.info("2. 오류 분류기 테스트")
        classifier = ErrorClassifier(config)
        
        test_error = ErrorEvent(
            timestamp=datetime.now(),
            category=ErrorCategory.API_FAILURE,
            severity=ErrorSeverity.CRITICAL,
            message="API 호출 실패",
            details={'status_code': 401},
            source='test'
        )
        
        classification = classifier.classify_error(test_error)
        logger.info(f"분류 결과: 우선순위 {classification.priority.value}, 액션 {classification.action_type.value}")
        
        # 3. 복구 관리자 테스트
        logger.info("3. 복구 관리자 테스트")
        recovery_manager = AutoRecoveryManager(config)
        
        recovery_attempt = recovery_manager.attempt_recovery(test_error, classification)
        logger.info(f"복구 시도: {recovery_attempt.status.value}")
        
        # 4. 알림 관리자 테스트
        logger.info("4. 알림 관리자 테스트")
        notification_manager = NotificationManager(config)
        
        notification_manager.send_notification(test_error, classification, recovery_attempt)
        logger.info("알림 전송 요청 완료")
        
        # 5. 분석 시스템 테스트
        logger.info("5. 분석 시스템 테스트")
        analytics = ErrorAnalytics(config)
        
        analytics.store_error_event(test_error)
        analytics.store_recovery_attempt(recovery_attempt)
        
        health_score = analytics.get_system_health_score(1)
        logger.info(f"헬스 스코어: {health_score['health_score']:.1f}")
        
        logger.info("✅ 개별 컴포넌트 테스트 완료!")
        
    except Exception as e:
        logger.error(f"개별 컴포넌트 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("자동 오류 감지 및 수정 시스템 테스트")
    print("=" * 60)
    
    # 개별 컴포넌트 테스트
    test_individual_components()
    
    print("\n" + "=" * 60)
    
    # 통합 시스템 테스트
    test_error_management_system()
    
    print("\n" + "=" * 60)
    print("모든 테스트 완료!")
