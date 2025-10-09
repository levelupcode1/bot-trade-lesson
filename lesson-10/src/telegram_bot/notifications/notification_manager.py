"""
자동매매 시스템 알림 관리자
알림 큐, 우선순위 처리, 중복 방지, 사용자 설정 관리를 담당
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

from ..utils.logger import get_logger


class NotificationPriority(Enum):
    """알림 우선순위"""
    CRITICAL = 1  # 시스템 오류, 손실 한계 도달
    HIGH = 2      # 거래 실행, 긴급 상태 변경
    MEDIUM = 3    # 수익률 달성, 설정 변경
    LOW = 4       # 정기 보고, 일반 상태 업데이트


class NotificationType(Enum):
    """알림 타입"""
    TRADE_EXECUTION = "trade_execution"      # 거래 실행
    PROFIT_ACHIEVEMENT = "profit_achievement" # 수익률 달성
    LOSS_LIMIT = "loss_limit"                # 손실 한계 도달
    SYSTEM_ERROR = "system_error"            # 시스템 오류
    STATUS_REPORT = "status_report"          # 정기 상태 보고
    CONFIG_CHANGE = "config_change"          # 설정 변경
    RISK_WARNING = "risk_warning"            # 리스크 경고


@dataclass
class NotificationMessage:
    """알림 메시지 데이터 클래스"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    user_id: str
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """알림 ID 생성"""
        content = f"{self.type.value}_{self.user_id}_{self.timestamp.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class UserNotificationSettings:
    """사용자 알림 설정"""
    user_id: str
    enabled_types: Set[NotificationType]
    priority_threshold: NotificationPriority
    cooldown_settings: Dict[NotificationType, int]  # 초 단위
    quiet_hours: Dict[str, str]  # {"start": "22:00", "end": "08:00"}
    batch_mode: bool = False
    summary_mode: bool = False
    
    def __post_init__(self):
        if isinstance(self.enabled_types, list):
            self.enabled_types = set(self.enabled_types)
        if isinstance(self.priority_threshold, int):
            self.priority_threshold = NotificationPriority(self.priority_threshold)


class NotificationQueue:
    """우선순위 기반 알림 큐"""
    
    def __init__(self):
        self._queues = {
            priority: deque() for priority in NotificationPriority
        }
        self._size = 0
    
    def enqueue(self, notification: NotificationMessage):
        """알림을 큐에 추가"""
        self._queues[notification.priority].append(notification)
        self._size += 1
    
    def dequeue(self) -> Optional[NotificationMessage]:
        """가장 높은 우선순위 알림을 큐에서 제거"""
        for priority in NotificationPriority:
            if self._queues[priority]:
                self._size -= 1
                return self._queues[priority].popleft()
        return None
    
    def peek(self) -> Optional[NotificationMessage]:
        """가장 높은 우선순위 알림을 확인 (제거하지 않음)"""
        for priority in NotificationPriority:
            if self._queues[priority]:
                return self._queues[priority][0]
        return None
    
    def size(self) -> int:
        """큐 크기 반환"""
        return self._size
    
    def is_empty(self) -> bool:
        """큐가 비어있는지 확인"""
        return self._size == 0


class DuplicateFilter:
    """중복 알림 필터"""
    
    def __init__(self):
        self._recent_notifications: Dict[str, List[datetime]] = defaultdict(list)
        self._content_hashes: Set[str] = set()
        self._cleanup_interval = 3600  # 1시간마다 정리
        self._last_cleanup = time.time()
    
    def is_duplicate(self, notification: NotificationMessage) -> bool:
        """중복 알림인지 확인"""
        self._cleanup_if_needed()
        
        # 1. 내용 기반 중복 확인
        content_hash = self._get_content_hash(notification)
        if content_hash in self._content_hashes:
            return True
        
        # 2. 시간 기반 중복 확인
        user_key = f"{notification.user_id}_{notification.type.value}"
        recent_times = self._recent_notifications[user_key]
        
        # 설정된 쿨다운 시간 내 중복 확인
        cooldown_seconds = self._get_cooldown_seconds(notification.type)
        cutoff_time = datetime.now() - timedelta(seconds=cooldown_seconds)
        
        # 최근 알림 중 쿨다운 시간 내의 것들만 유지
        recent_times[:] = [t for t in recent_times if t > cutoff_time]
        
        # 쿨다운 시간 내에 동일한 타입의 알림이 있는지 확인
        if any(t > cutoff_time for t in recent_times):
            return True
        
        # 중복이 아니므로 기록에 추가
        recent_times.append(notification.timestamp)
        self._content_hashes.add(content_hash)
        
        return False
    
    def _get_content_hash(self, notification: NotificationMessage) -> str:
        """알림 내용의 해시 생성"""
        content = f"{notification.type.value}_{notification.title}_{notification.message}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cooldown_seconds(self, notification_type: NotificationType) -> int:
        """알림 타입별 쿨다운 시간 반환 (초)"""
        cooldown_map = {
            NotificationType.TRADE_EXECUTION: 300,      # 5분
            NotificationType.PROFIT_ACHIEVEMENT: 3600,  # 1시간
            NotificationType.LOSS_LIMIT: 1800,          # 30분
            NotificationType.SYSTEM_ERROR: 3600,        # 1시간
            NotificationType.STATUS_REPORT: 86400,      # 24시간
            NotificationType.CONFIG_CHANGE: 300,        # 5분
            NotificationType.RISK_WARNING: 900,         # 15분
        }
        return cooldown_map.get(notification_type, 300)
    
    def _cleanup_if_needed(self):
        """필요시 오래된 데이터 정리"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_data()
            self._last_cleanup = current_time
    
    def _cleanup_old_data(self):
        """오래된 데이터 정리"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # 시간 기반 데이터 정리
        for user_key in list(self._recent_notifications.keys()):
            recent_times = self._recent_notifications[user_key]
            recent_times[:] = [t for t in recent_times if t > cutoff_time]
            if not recent_times:
                del self._recent_notifications[user_key]
        
        # 내용 해시는 자동으로 정리됨 (메모리 사용량 제한)


class NotificationHistory:
    """알림 히스토리 관리"""
    
    def __init__(self, max_history: int = 1000):
        self._history: List[NotificationMessage] = []
        self._max_history = max_history
        self._user_history: Dict[str, List[str]] = defaultdict(list)
    
    def add_notification(self, notification: NotificationMessage):
        """알림 히스토리에 추가"""
        self._history.append(notification)
        self._user_history[notification.user_id].append(notification.id)
        
        # 히스토리 크기 제한
        if len(self._history) > self._max_history:
            old_notification = self._history.pop(0)
            self._user_history[old_notification.user_id].remove(old_notification.id)
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[NotificationMessage]:
        """사용자별 알림 히스토리 조회"""
        user_notification_ids = self._user_history.get(user_id, [])
        notifications = [n for n in self._history if n.id in user_notification_ids]
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_recent_notifications(self, limit: int = 100) -> List[NotificationMessage]:
        """최근 알림 조회"""
        return sorted(self._history, key=lambda x: x.timestamp, reverse=True)[:limit]


class NotificationManager:
    """알림 관리자 - 전체 알림 시스템의 중앙 제어"""
    
    def __init__(self, telegram_bot=None):
        self.logger = get_logger(__name__)
        self.telegram_bot = telegram_bot
        
        # 핵심 컴포넌트 초기화
        self.queue = NotificationQueue()
        self.duplicate_filter = DuplicateFilter()
        self.history = NotificationHistory()
        
        # 사용자 설정 저장소
        self.user_settings: Dict[str, UserNotificationSettings] = {}
        
        # 배치 처리 설정
        self.batch_interval = 30  # 30초마다 배치 처리
        self.batch_size = 10      # 한 번에 최대 10개 알림 처리
        
        # 실행 상태
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """알림 관리자 시작"""
        if self._running:
            self.logger.warning("알림 관리자가 이미 실행 중입니다")
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_notifications())
        self.logger.info("알림 관리자 시작됨")
    
    async def stop(self):
        """알림 관리자 중지"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self.logger.info("알림 관리자 중지됨")
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        user_id: str,
        title: str,
        message: str,
        priority: Optional[NotificationPriority] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """알림 전송 요청"""
        try:
            # 우선순위 설정
            if priority is None:
                priority = self._get_default_priority(notification_type)
            
            # 알림 메시지 생성
            notification = NotificationMessage(
                id="",  # 자동 생성됨
                type=notification_type,
                priority=priority,
                user_id=user_id,
                title=title,
                message=message,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # 사용자 설정 확인
            if not self._should_send_to_user(notification):
                self.logger.debug(f"사용자 {user_id} 설정에 따라 알림 건너뜀: {notification_type.value}")
                return False
            
            # 중복 확인
            if self.duplicate_filter.is_duplicate(notification):
                self.logger.debug(f"중복 알림 건너뜀: {notification.id}")
                return False
            
            # 큐에 추가
            self.queue.enqueue(notification)
            self.logger.info(f"알림 큐에 추가됨: {notification.id} ({notification_type.value})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"알림 전송 요청 실패: {e}")
            return False
    
    def set_user_settings(self, user_id: str, settings: UserNotificationSettings):
        """사용자 알림 설정 저장"""
        self.user_settings[user_id] = settings
        self.logger.info(f"사용자 {user_id} 알림 설정 업데이트됨")
    
    def get_user_settings(self, user_id: str) -> Optional[UserNotificationSettings]:
        """사용자 알림 설정 조회"""
        return self.user_settings.get(user_id)
    
    async def _process_notifications(self):
        """알림 처리 메인 루프"""
        while self._running:
            try:
                # 큐에서 알림 가져오기
                notifications_to_process = []
                for _ in range(self.batch_size):
                    notification = self.queue.dequeue()
                    if notification is None:
                        break
                    notifications_to_process.append(notification)
                
                # 알림 처리
                if notifications_to_process:
                    await self._process_batch(notifications_to_process)
                
                # 다음 배치까지 대기
                await asyncio.sleep(self.batch_interval)
                
            except Exception as e:
                self.logger.error(f"알림 처리 중 오류: {e}")
                await asyncio.sleep(5)  # 오류 시 잠시 대기
    
    async def _process_batch(self, notifications: List[NotificationMessage]):
        """배치 알림 처리"""
        for notification in notifications:
            try:
                # 텔레그램으로 전송
                success = await self._send_to_telegram(notification)
                
                if success:
                    # 히스토리에 추가
                    self.history.add_notification(notification)
                    self.logger.info(f"알림 전송 성공: {notification.id}")
                else:
                    # 재시도 로직
                    await self._handle_send_failure(notification)
                    
            except Exception as e:
                self.logger.error(f"알림 처리 실패 {notification.id}: {e}")
    
    async def _send_to_telegram(self, notification: NotificationMessage) -> bool:
        """텔레그램으로 알림 전송"""
        try:
            if not self.telegram_bot:
                self.logger.warning("텔레그램 봇이 설정되지 않음")
                return False
            
            # 메시지 포맷팅
            formatted_message = self._format_message(notification)
            
            # 텔레그램 전송
            await self.telegram_bot.send_message(
                chat_id=notification.user_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"텔레그램 전송 실패 {notification.id}: {e}")
            return False
    
    def _format_message(self, notification: NotificationMessage) -> str:
        """알림 메시지 포맷팅"""
        priority_emoji = {
            NotificationPriority.CRITICAL: "🚨",
            NotificationPriority.HIGH: "🔴",
            NotificationPriority.MEDIUM: "🟡",
            NotificationPriority.LOW: "🟢"
        }
        
        emoji = priority_emoji.get(notification.priority, "📢")
        timestamp = notification.timestamp.strftime("%H:%M:%S")
        
        return f"{emoji} *{notification.title}*\n\n{notification.message}\n\n⏰ {timestamp}"
    
    async def _handle_send_failure(self, notification: NotificationMessage):
        """전송 실패 처리"""
        notification.retry_count += 1
        
        if notification.retry_count < notification.max_retries:
            # 재시도를 위해 큐에 다시 추가
            self.queue.enqueue(notification)
            self.logger.warning(f"알림 재시도 예약: {notification.id} ({notification.retry_count}/{notification.max_retries})")
        else:
            # 최대 재시도 횟수 초과
            self.logger.error(f"알림 전송 최종 실패: {notification.id}")
            # 실패한 알림도 히스토리에 기록
            self.history.add_notification(notification)
    
    def _should_send_to_user(self, notification: NotificationMessage) -> bool:
        """사용자에게 알림을 보낼지 확인"""
        settings = self.user_settings.get(notification.user_id)
        if not settings:
            # 기본 설정으로 허용
            return True
        
        # 알림 타입 활성화 확인
        if notification.type not in settings.enabled_types:
            return False
        
        # 우선순위 임계값 확인
        if notification.priority.value > settings.priority_threshold.value:
            return False
        
        # 조용한 시간 확인
        if self._is_quiet_time(settings):
            # CRITICAL 알림은 조용한 시간에도 전송
            return notification.priority == NotificationPriority.CRITICAL
        
        return True
    
    def _is_quiet_time(self, settings: UserNotificationSettings) -> bool:
        """조용한 시간인지 확인"""
        if not settings.quiet_hours:
            return False
        
        try:
            current_time = datetime.now().time()
            start_time = datetime.strptime(settings.quiet_hours["start"], "%H:%M").time()
            end_time = datetime.strptime(settings.quiet_hours["end"], "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                # 자정을 넘나드는 경우 (예: 22:00 - 08:00)
                return current_time >= start_time or current_time <= end_time
        except Exception:
            return False
    
    def _get_default_priority(self, notification_type: NotificationType) -> NotificationPriority:
        """알림 타입별 기본 우선순위 반환"""
        priority_map = {
            NotificationType.TRADE_EXECUTION: NotificationPriority.HIGH,
            NotificationType.PROFIT_ACHIEVEMENT: NotificationPriority.MEDIUM,
            NotificationType.LOSS_LIMIT: NotificationPriority.CRITICAL,
            NotificationType.SYSTEM_ERROR: NotificationPriority.CRITICAL,
            NotificationType.STATUS_REPORT: NotificationPriority.LOW,
            NotificationType.CONFIG_CHANGE: NotificationPriority.MEDIUM,
            NotificationType.RISK_WARNING: NotificationPriority.HIGH,
        }
        return priority_map.get(notification_type, NotificationPriority.MEDIUM)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 정보 반환"""
        return {
            "total_size": self.queue.size(),
            "priority_breakdown": {
                priority.name: len(self.queue._queues[priority])
                for priority in NotificationPriority
            },
            "user_settings_count": len(self.user_settings),
            "history_size": len(self.history._history)
        }








