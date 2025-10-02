#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 시스템
오류 발생 시 다양한 채널을 통해 알림을 전송하고 에스컬레이션을 관리합니다.
"""

import smtplib
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import asyncio

from .error_detector import ErrorEvent, ErrorSeverity, ErrorCategory
from .error_classifier import ClassificationResult, PriorityLevel
from .auto_recovery import RecoveryAttempt, RecoveryStatus

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """알림 채널"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"

class NotificationStatus(Enum):
    """알림 상태"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ESCALATED = "escalated"

@dataclass
class NotificationMessage:
    """알림 메시지"""
    message_id: str
    error_event: ErrorEvent
    classification: ClassificationResult
    channel: NotificationChannel
    recipient: str
    message: str
    priority: PriorityLevel
    status: NotificationStatus
    sent_time: Optional[datetime]
    retry_count: int = 0
    max_retries: int = 3

class NotificationManager:
    """알림 관리자"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.notification_queue = []
        self.notification_history = []
        self.escalation_timers = {}
        self.channel_handlers = self._initialize_channel_handlers()
        self.recipient_config = self._load_recipient_config()
        self.message_templates = self._load_message_templates()
        self.notification_callbacks = []
        
        # 알림 제한 설정
        self.rate_limits = {
            NotificationChannel.TELEGRAM: {'max_per_hour': 30, 'max_per_day': 200},
            NotificationChannel.EMAIL: {'max_per_hour': 10, 'max_per_day': 50},
            NotificationChannel.SMS: {'max_per_hour': 5, 'max_per_day': 20}
        }
        
        self.sent_notifications = {
            channel: [] for channel in NotificationChannel
        }
    
    def _initialize_channel_handlers(self) -> Dict[NotificationChannel, Callable]:
        """채널 핸들러 초기화"""
        return {
            NotificationChannel.TELEGRAM: self._send_telegram_notification,
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.SMS: self._send_sms_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.DASHBOARD: self._send_dashboard_notification
        }
    
    def _load_recipient_config(self) -> Dict[str, Dict[str, Any]]:
        """수신자 설정 로드"""
        return {
            'admin': {
                'telegram': ['@admin_bot'],
                'email': ['admin@company.com'],
                'sms': ['+82-10-0000-0000']
            },
            'dev_team': {
                'telegram': ['@dev_team_bot'],
                'email': ['dev@company.com']
            },
            'senior_dev': {
                'telegram': ['@senior_dev_bot'],
                'email': ['senior@company.com'],
                'sms': ['+82-10-0000-0001']
            },
            'system_admin': {
                'telegram': ['@sysadmin_bot'],
                'email': ['sysadmin@company.com'],
                'sms': ['+82-10-0000-0002']
            }
        }
    
    def _load_message_templates(self) -> Dict[str, str]:
        """메시지 템플릿 로드"""
        return {
            'critical_error': """
🚨 치명적 오류 발생 🚨

오류 유형: {category}
심각도: {severity}
발생 시간: {timestamp}
오류 메시지: {message}

상세 정보:
{details}

즉시 확인 및 조치가 필요합니다.
시스템 상태: {system_status}
""",
            'high_priority_error': """
⚠️ 중요 오류 발생 ⚠️

오류 유형: {category}
발생 시간: {timestamp}
오류 메시지: {message}

자동 복구 시도 중입니다.
복구 상태: {recovery_status}
""",
            'recovery_success': """
✅ 자동 복구 성공 ✅

오류 유형: {category}
복구 시간: {recovery_time}초
복구 방법: {recovery_method}

시스템이 정상적으로 복구되었습니다.
""",
            'recovery_failed': """
❌ 자동 복구 실패 ❌

오류 유형: {category}
복구 시도: {attempt_count}회
실패 원인: {failure_reason}

수동 개입이 필요합니다.
""",
            'escalation': """
📢 에스컬레이션 알림 📢

오류 유형: {category}
에스컬레이션 사유: {escalation_reason}
대기 시간: {wait_time}분

상급자 개입이 필요합니다.
"""
        }
    
    def send_notification(self, error: ErrorEvent, classification: ClassificationResult, 
                         recovery_attempt: Optional[RecoveryAttempt] = None):
        """알림 전송"""
        
        # 알림 채널 결정
        channels = self._determine_notification_channels(error, classification)
        
        # 수신자 결정
        recipients = self._determine_recipients(error, classification)
        
        # 메시지 생성
        message = self._generate_notification_message(error, classification, recovery_attempt)
        
        # 각 채널별로 알림 전송
        for channel in channels:
            for recipient in recipients:
                if self._should_send_notification(channel, recipient, error):
                    notification = self._create_notification(
                        error, classification, channel, recipient, message
                    )
                    self._queue_notification(notification)
        
        # 에스컬레이션 타이머 설정
        if classification.escalation_timeout > 0:
            self._set_escalation_timer(error, classification)
    
    def _determine_notification_channels(self, error: ErrorEvent, 
                                       classification: ClassificationResult) -> List[NotificationChannel]:
        """알림 채널 결정"""
        channels = []
        
        for channel_name in classification.notification_channels:
            try:
                channel = NotificationChannel(channel_name)
                channels.append(channel)
            except ValueError:
                logger.warning(f"알 수 없는 알림 채널: {channel_name}")
        
        return channels
    
    def _determine_recipients(self, error: ErrorEvent, 
                            classification: ClassificationResult) -> List[str]:
        """수신자 결정"""
        recipients = []
        
        # 기본 수신자 (에스컬레이션 연락처)
        for contact in classification.escalation_contacts:
            if contact in self.recipient_config:
                recipients.append(contact)
        
        # 우선순위에 따른 추가 수신자
        if classification.priority in [PriorityLevel.P0, PriorityLevel.P1]:
            recipients.extend(['admin', 'dev_team'])
        
        return list(set(recipients))  # 중복 제거
    
    def _generate_notification_message(self, error: ErrorEvent, 
                                     classification: ClassificationResult,
                                     recovery_attempt: Optional[RecoveryAttempt] = None) -> str:
        """알림 메시지 생성"""
        
        # 기본 메시지 템플릿 선택
        if classification.priority == PriorityLevel.P0:
            template_key = 'critical_error'
        elif classification.priority == PriorityLevel.P1:
            template_key = 'high_priority_error'
        elif recovery_attempt:
            if recovery_attempt.status == RecoveryStatus.SUCCESS:
                template_key = 'recovery_success'
            else:
                template_key = 'recovery_failed'
        else:
            template_key = 'high_priority_error'
        
        template = self.message_templates.get(template_key, self.message_templates['high_priority_error'])
        
        # 메시지 변수 설정
        message_vars = {
            'category': error.category.value,
            'severity': error.severity.value,
            'timestamp': error.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'message': error.message,
            'details': json.dumps(error.details, indent=2, ensure_ascii=False),
            'system_status': '정상' if classification.action_type.value == 'auto_recover' else '주의',
            'recovery_status': recovery_attempt.status.value if recovery_attempt else 'N/A',
            'recovery_time': (recovery_attempt.end_time - recovery_attempt.start_time).total_seconds() if recovery_attempt else 0,
            'recovery_method': recovery_attempt.recovery_method if recovery_attempt else 'N/A',
            'attempt_count': recovery_attempt.attempt_id if recovery_attempt else 'N/A',
            'failure_reason': recovery_attempt.error_message if recovery_attempt else 'N/A',
            'escalation_reason': '자동 복구 실패',
            'wait_time': classification.escalation_timeout // 60
        }
        
        return template.format(**message_vars)
    
    def _should_send_notification(self, channel: NotificationChannel, 
                                recipient: str, error: ErrorEvent) -> bool:
        """알림 전송 여부 결정"""
        
        # Rate limit 체크
        if not self._check_rate_limit(channel):
            logger.warning(f"Rate limit 초과: {channel.value}")
            return False
        
        # 중복 알림 방지 (최근 5분 내 동일한 오류)
        if self._is_duplicate_notification(channel, recipient, error):
            logger.info(f"중복 알림 방지: {error.error_id}")
            return False
        
        return True
    
    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Rate limit 체크"""
        if channel not in self.rate_limits:
            return True
        
        limit_config = self.rate_limits[channel]
        sent_notifications = self.sent_notifications[channel]
        
        # 1시간 내 전송된 알림 수 체크
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_count = len([
            n for n in sent_notifications 
            if n.sent_time and n.sent_time > hour_ago
        ])
        
        if recent_count >= limit_config['max_per_hour']:
            return False
        
        # 1일 내 전송된 알림 수 체크
        day_ago = datetime.now() - timedelta(days=1)
        daily_count = len([
            n for n in sent_notifications 
            if n.sent_time and n.sent_time > day_ago
        ])
        
        if daily_count >= limit_config['max_per_day']:
            return False
        
        return True
    
    def _is_duplicate_notification(self, channel: NotificationChannel, 
                                 recipient: str, error: ErrorEvent) -> bool:
        """중복 알림 체크"""
        recent_time = datetime.now() - timedelta(minutes=5)
        
        for notification in self.notification_history:
            if (notification.channel == channel and 
                notification.recipient == recipient and
                notification.error_event.category == error.category and
                notification.error_event.severity == error.severity and
                notification.sent_time and 
                notification.sent_time > recent_time):
                return True
        
        return False
    
    def _create_notification(self, error: ErrorEvent, classification: ClassificationResult,
                           channel: NotificationChannel, recipient: str, message: str) -> NotificationMessage:
        """알림 메시지 생성"""
        return NotificationMessage(
            message_id=f"notif_{int(time.time() * 1000)}",
            error_event=error,
            classification=classification,
            channel=channel,
            recipient=recipient,
            message=message,
            priority=classification.priority,
            status=NotificationStatus.PENDING,
            sent_time=None
        )
    
    def _queue_notification(self, notification: NotificationMessage):
        """알림 큐에 추가"""
        self.notification_queue.append(notification)
        logger.info(f"알림 큐에 추가: {notification.channel.value} -> {notification.recipient}")
    
    def _set_escalation_timer(self, error: ErrorEvent, classification: ClassificationResult):
        """에스컬레이션 타이머 설정"""
        timer_id = f"{error.category.value}_{error.error_id}"
        
        def escalation_callback():
            self._handle_escalation(error, classification)
        
        # 기존 타이머가 있으면 취소
        if timer_id in self.escalation_timers:
            self.escalation_timers[timer_id].cancel()
        
        # 새 타이머 설정
        timer = threading.Timer(classification.escalation_timeout, escalation_callback)
        timer.start()
        self.escalation_timers[timer_id] = timer
        
        logger.info(f"에스컬레이션 타이머 설정: {timer_id} - {classification.escalation_timeout}초")
    
    def _handle_escalation(self, error: ErrorEvent, classification: ClassificationResult):
        """에스컬레이션 처리"""
        logger.warning(f"에스컬레이션 발생: {error.error_id}")
        
        # 에스컬레이션 알림 전송
        escalation_message = self.message_templates['escalation'].format(
            category=error.category.value,
            escalation_reason='자동 복구 실패 또는 시간 초과',
            wait_time=classification.escalation_timeout // 60
        )
        
        # 상급자에게 에스컬레이션 알림
        escalation_recipients = ['senior_dev', 'system_admin']
        for recipient in escalation_recipients:
            if recipient in self.recipient_config:
                notification = NotificationMessage(
                    message_id=f"escalation_{int(time.time() * 1000)}",
                    error_event=error,
                    classification=classification,
                    channel=NotificationChannel.TELEGRAM,
                    recipient=recipient,
                    message=escalation_message,
                    priority=PriorityLevel.P0,
                    status=NotificationStatus.PENDING,
                    sent_time=None
                )
                self._queue_notification(notification)
    
    # 채널별 알림 전송 메서드들
    def _send_telegram_notification(self, notification: NotificationMessage) -> bool:
        """텔레그램 알림 전송"""
        try:
            bot_token = self.config.get('telegram_bot_token')
            if not bot_token:
                logger.error("텔레그램 봇 토큰이 설정되지 않음")
                return False
            
            chat_id = self.recipient_config.get(notification.recipient, {}).get('telegram', [None])[0]
            if not chat_id:
                logger.error(f"수신자 {notification.recipient}의 텔레그램 채팅 ID 없음")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': notification.message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            success = response.status_code == 200
            
            if success:
                logger.info(f"텔레그램 알림 전송 성공: {notification.recipient}")
            else:
                logger.error(f"텔레그램 알림 전송 실패: {response.text}")
            
            return success
        
        except Exception as e:
            logger.error(f"텔레그램 알림 전송 중 오류: {e}")
            return False
    
    def _send_email_notification(self, notification: NotificationMessage) -> bool:
        """이메일 알림 전송"""
        try:
            smtp_config = self.config.get('smtp', {})
            if not smtp_config:
                logger.error("SMTP 설정이 없음")
                return False
            
            email_addresses = self.recipient_config.get(notification.recipient, {}).get('email', [])
            if not email_addresses:
                logger.error(f"수신자 {notification.recipient}의 이메일 주소 없음")
                return False
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email')
            msg['To'] = ', '.join(email_addresses)
            msg['Subject'] = f"[{notification.priority.value.upper()}] 자동매매 시스템 오류 알림"
            
            msg.attach(MIMEText(notification.message, 'plain', 'utf-8'))
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                if smtp_config.get('use_tls'):
                    server.starttls()
                
                if smtp_config.get('username') and smtp_config.get('password'):
                    server.login(smtp_config['username'], smtp_config['password'])
                
                server.send_message(msg)
            
            logger.info(f"이메일 알림 전송 성공: {notification.recipient}")
            return True
        
        except Exception as e:
            logger.error(f"이메일 알림 전송 중 오류: {e}")
            return False
    
    def _send_sms_notification(self, notification: NotificationMessage) -> bool:
        """SMS 알림 전송"""
        try:
            sms_config = self.config.get('sms', {})
            if not sms_config:
                logger.error("SMS 설정이 없음")
                return False
            
            phone_numbers = self.recipient_config.get(notification.recipient, {}).get('sms', [])
            if not phone_numbers:
                logger.error(f"수신자 {notification.recipient}의 전화번호 없음")
                return False
            
            # SMS API 호출 (실제 구현에서는 SMS 서비스 API 사용)
            for phone in phone_numbers:
                sms_data = {
                    'to': phone,
                    'message': notification.message[:160],  # SMS 길이 제한
                    'api_key': sms_config.get('api_key')
                }
                
                response = requests.post(sms_config['url'], data=sms_data, timeout=10)
                success = response.status_code == 200
                
                if success:
                    logger.info(f"SMS 알림 전송 성공: {phone}")
                else:
                    logger.error(f"SMS 알림 전송 실패: {response.text}")
            
            return True
        
        except Exception as e:
            logger.error(f"SMS 알림 전송 중 오류: {e}")
            return False
    
    def _send_webhook_notification(self, notification: NotificationMessage) -> bool:
        """웹훅 알림 전송"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                logger.error("웹훅 URL이 설정되지 않음")
                return False
            
            webhook_data = {
                'error_id': notification.error_event.error_id,
                'category': notification.error_event.category.value,
                'severity': notification.error_event.severity.value,
                'priority': notification.priority.value,
                'message': notification.message,
                'timestamp': notification.error_event.timestamp.isoformat(),
                'details': notification.error_event.details
            }
            
            response = requests.post(webhook_url, json=webhook_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                logger.info("웹훅 알림 전송 성공")
            else:
                logger.error(f"웹훅 알림 전송 실패: {response.text}")
            
            return success
        
        except Exception as e:
            logger.error(f"웹훅 알림 전송 중 오류: {e}")
            return False
    
    def _send_dashboard_notification(self, notification: NotificationMessage) -> bool:
        """대시보드 알림 전송"""
        try:
            # 대시보드 API 호출 (실제 구현에서는 대시보드 시스템과 연동)
            dashboard_data = {
                'type': 'error_notification',
                'error_id': notification.error_event.error_id,
                'category': notification.error_event.category.value,
                'severity': notification.error_event.severity.value,
                'priority': notification.priority.value,
                'message': notification.message,
                'timestamp': notification.error_event.timestamp.isoformat()
            }
            
            # 실제 구현에서는 대시보드 시스템의 API 호출
            logger.info(f"대시보드 알림: {notification.message}")
            return True
        
        except Exception as e:
            logger.error(f"대시보드 알림 전송 중 오류: {e}")
            return False
    
    def process_notification_queue(self):
        """알림 큐 처리"""
        while self.notification_queue:
            notification = self.notification_queue.pop(0)
            
            try:
                # 알림 전송
                handler = self.channel_handlers.get(notification.channel)
                if handler:
                    success = handler(notification)
                    
                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_time = datetime.now()
                        self.sent_notifications[notification.channel].append(notification)
                    else:
                        notification.status = NotificationStatus.FAILED
                        notification.retry_count += 1
                        
                        # 재시도
                        if notification.retry_count < notification.max_retries:
                            self.notification_queue.append(notification)
                            time.sleep(5)  # 5초 후 재시도
                else:
                    logger.error(f"알 수 없는 알림 채널 핸들러: {notification.channel}")
                    notification.status = NotificationStatus.FAILED
                
                # 히스토리에 추가
                self.notification_history.append(notification)
                
            except Exception as e:
                logger.error(f"알림 처리 중 오류: {e}")
                notification.status = NotificationStatus.FAILED
                self.notification_history.append(notification)
    
    def get_notification_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """알림 통계 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_notifications = [
            n for n in self.notification_history
            if n.sent_time and n.sent_time > cutoff_time
        ]
        
        stats = {
            'total_sent': len([n for n in recent_notifications if n.status == NotificationStatus.SENT]),
            'total_failed': len([n for n in recent_notifications if n.status == NotificationStatus.FAILED]),
            'by_channel': {},
            'by_priority': {},
            'by_recipient': {},
            'success_rate': 0
        }
        
        # 채널별 통계
        for channel in NotificationChannel:
            channel_notifications = [n for n in recent_notifications if n.channel == channel]
            stats['by_channel'][channel.value] = {
                'total': len(channel_notifications),
                'sent': len([n for n in channel_notifications if n.status == NotificationStatus.SENT]),
                'failed': len([n for n in channel_notifications if n.status == NotificationStatus.FAILED])
            }
        
        # 우선순위별 통계
        for priority in PriorityLevel:
            priority_notifications = [n for n in recent_notifications if n.priority == priority]
            stats['by_priority'][priority.value] = len(priority_notifications)
        
        # 수신자별 통계
        all_recipients = set(n.recipient for n in recent_notifications)
        for recipient in all_recipients:
            recipient_notifications = [n for n in recent_notifications if n.recipient == recipient]
            stats['by_recipient'][recipient] = len(recipient_notifications)
        
        # 성공률 계산
        total_processed = len(recent_notifications)
        if total_processed > 0:
            stats['success_rate'] = stats['total_sent'] / total_processed
        
        return stats
