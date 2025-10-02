#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 오류 감지 및 수정 시스템 - 메인 실행 파일
"""

import time
import threading
import signal
import sys
from datetime import datetime
from typing import Dict, Any
import logging
import json

from .error_detector import ErrorDetector, ErrorEvent, ErrorCategory, ErrorSeverity
from .error_classifier import ErrorClassifier, ClassificationResult
from .auto_recovery import AutoRecoveryManager, RecoveryAttempt
from .notification_system import NotificationManager, NotificationMessage
from .error_analytics import ErrorAnalytics

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_management.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ErrorManagementSystem:
    """통합 오류 관리 시스템"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        # 각 모듈 초기화
        self.detector = ErrorDetector(config)
        self.classifier = ErrorClassifier(config)
        self.recovery_manager = AutoRecoveryManager(config)
        self.notification_manager = NotificationManager(config)
        self.analytics = ErrorAnalytics(config)
        
        # 오류 처리 콜백 등록
        self.detector.add_error_callback(self._handle_error_detected)
        
        # 스레드 관리
        self.threads = []
        
        logger.info("오류 관리 시스템 초기화 완료")
    
    def _handle_error_detected(self, error: ErrorEvent):
        """오류 감지 시 처리"""
        logger.info(f"오류 감지됨: {error.category.value} - {error.severity.value}")
        
        try:
            # 1. 오류 분류
            classification = self.classifier.classify_error(error)
            logger.info(f"오류 분류 완료: 우선순위 {classification.priority.value}")
            
            # 2. 오류 이벤트 저장
            self.analytics.store_error_event(error)
            
            # 3. 자동 복구 시도
            recovery_attempt = None
            if classification.action_type.value in ['auto_recover', 'monitor']:
                recovery_attempt = self.recovery_manager.attempt_recovery(error, classification)
                self.analytics.store_recovery_attempt(recovery_attempt)
                logger.info(f"복구 시도 완료: {recovery_attempt.status.value}")
            
            # 4. 알림 전송
            self.notification_manager.send_notification(error, classification, recovery_attempt)
            
            # 5. 알림 큐 처리
            self.notification_manager.process_notification_queue()
            
            # 6. 알림 저장
            for notification in self.notification_manager.notification_queue:
                self.analytics.store_notification(notification)
            
            logger.info(f"오류 처리 완료: {error.error_id}")
            
        except Exception as e:
            logger.error(f"오류 처리 중 예외 발생: {e}")
    
    def start(self):
        """시스템 시작"""
        if self.running:
            logger.warning("시스템이 이미 실행 중입니다")
            return
        
        self.running = True
        logger.info("오류 관리 시스템 시작")
        
        try:
            # 1. 오류 감지 스레드 시작
            detector_threads = self.detector.start_monitoring()
            self.threads.extend(detector_threads)
            
            # 2. 알림 처리 스레드 시작
            notification_thread = threading.Thread(
                target=self._notification_worker,
                daemon=True
            )
            notification_thread.start()
            self.threads.append(notification_thread)
            
            # 3. 시스템 메트릭 수집 스레드 시작
            metrics_thread = threading.Thread(
                target=self._metrics_worker,
                daemon=True
            )
            metrics_thread.start()
            self.threads.append(metrics_thread)
            
            # 4. 데이터 정리 스레드 시작
            cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True
            )
            cleanup_thread.start()
            self.threads.append(cleanup_thread)
            
            # 5. 리포트 생성 스레드 시작
            report_thread = threading.Thread(
                target=self._report_worker,
                daemon=True
            )
            report_thread.start()
            self.threads.append(report_thread)
            
            logger.info("모든 워커 스레드 시작 완료")
            
        except Exception as e:
            logger.error(f"시스템 시작 중 오류 발생: {e}")
            self.stop()
            raise
    
    def stop(self):
        """시스템 중지"""
        if not self.running:
            return
        
        logger.info("오류 관리 시스템 중지 중...")
        self.running = False
        
        # 감지기 중지
        self.detector.stop_monitoring()
        
        # 모든 스레드 종료 대기
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("오류 관리 시스템 중지 완료")
    
    def _notification_worker(self):
        """알림 처리 워커"""
        while self.running:
            try:
                self.notification_manager.process_notification_queue()
                time.sleep(1)
            except Exception as e:
                logger.error(f"알림 워커 오류: {e}")
                time.sleep(5)
    
    def _metrics_worker(self):
        """시스템 메트릭 수집 워커"""
        while self.running:
            try:
                # 시스템 메트릭 수집
                import psutil
                
                # 메모리 사용률
                memory_percent = psutil.virtual_memory().percent
                self.analytics.store_system_metric('memory_usage', memory_percent)
                
                # CPU 사용률
                cpu_percent = psutil.cpu_percent(interval=1)
                self.analytics.store_system_metric('cpu_usage', cpu_percent)
                
                # 디스크 사용률
                disk_percent = psutil.disk_usage('/').percent
                self.analytics.store_system_metric('disk_usage', disk_percent)
                
                time.sleep(30)  # 30초마다 수집
                
            except Exception as e:
                logger.error(f"메트릭 워커 오류: {e}")
                time.sleep(60)
    
    def _cleanup_worker(self):
        """데이터 정리 워커"""
        while self.running:
            try:
                # 매일 새벽 2시에 데이터 정리
                now = datetime.now()
                if now.hour == 2 and now.minute < 5:
                    logger.info("오래된 데이터 정리 시작")
                    self.analytics.cleanup_old_data()
                    logger.info("데이터 정리 완료")
                
                time.sleep(300)  # 5분마다 체크
                
            except Exception as e:
                logger.error(f"정리 워커 오류: {e}")
                time.sleep(3600)
    
    def _report_worker(self):
        """리포트 생성 워커"""
        while self.running:
            try:
                # 매일 오후 6시에 일일 리포트 생성
                now = datetime.now()
                if now.hour == 18 and now.minute < 5:
                    logger.info("일일 리포트 생성 시작")
                    report = self.analytics.generate_daily_report()
                    
                    # 리포트를 파일로 저장
                    with open(f'daily_report_{now.date().isoformat()}.json', 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                    
                    logger.info("일일 리포트 생성 완료")
                
                time.sleep(300)  # 5분마다 체크
                
            except Exception as e:
                logger.error(f"리포트 워커 오류: {e}")
                time.sleep(3600)
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        try:
            # 오류 통계
            error_stats = self.detector.get_error_statistics(24)
            
            # 복구 통계
            recovery_stats = self.recovery_manager.get_recovery_statistics(24)
            
            # 알림 통계
            notification_stats = self.notification_manager.get_notification_statistics(24)
            
            # 헬스 스코어
            health_score = self.analytics.get_system_health_score(24)
            
            return {
                'system_status': 'running' if self.running else 'stopped',
                'timestamp': datetime.now().isoformat(),
                'error_statistics': error_stats,
                'recovery_statistics': recovery_stats,
                'notification_statistics': notification_stats,
                'health_score': health_score,
                'active_threads': len([t for t in self.threads if t.is_alive()])
            }
        
        except Exception as e:
            logger.error(f"시스템 상태 조회 오류: {e}")
            return {'system_status': 'error', 'error': str(e)}
    
    def trigger_test_error(self, category: ErrorCategory, severity: ErrorSeverity):
        """테스트용 오류 발생"""
        test_error = ErrorEvent(
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            message=f"테스트 오류 - {category.value}",
            details={'test': True, 'triggered_by': 'manual'},
            source='test_system'
        )
        
        logger.info(f"테스트 오류 발생: {category.value} - {severity.value}")
        self._handle_error_detected(test_error)

def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.info(f"시그널 {signum} 수신, 시스템 종료 중...")
    if 'system' in globals():
        system.stop()
    sys.exit(0)

def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 설정 로드
    config = {
        'database_path': 'error_management.db',
        'retention_days': 90,
        'telegram_bot_token': 'YOUR_BOT_TOKEN',  # 실제 토큰으로 교체 필요
        'smtp': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': 'your_email@gmail.com',
            'password': 'your_password',
            'from_email': 'your_email@gmail.com'
        },
        'sms': {
            'url': 'https://api.sms-service.com/send',
            'api_key': 'YOUR_SMS_API_KEY'
        },
        'webhook_url': 'https://your-webhook-url.com/notifications'
    }
    
    # 시스템 초기화 및 시작
    global system
    system = ErrorManagementSystem(config)
    
    try:
        system.start()
        
        logger.info("오류 관리 시스템이 실행 중입니다. Ctrl+C로 종료할 수 있습니다.")
        
        # 메인 루프
        while True:
            time.sleep(10)
            
            # 10분마다 상태 출력
            if int(time.time()) % 600 == 0:
                status = system.get_system_status()
                logger.info(f"시스템 상태: {status['system_status']}")
                logger.info(f"헬스 스코어: {status['health_score']['health_score']:.1f}")
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
    finally:
        system.stop()

if __name__ == "__main__":
    main()
