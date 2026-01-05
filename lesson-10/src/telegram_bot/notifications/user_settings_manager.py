"""
사용자 알림 설정 관리자
사용자별 알림 설정을 저장, 로드, 관리하는 시스템
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict, field
import logging

from .notification_manager import NotificationType, NotificationPriority, UserNotificationSettings


@dataclass
class NotificationCooldownSettings:
    """알림 쿨다운 설정"""
    trade_execution: int = 300      # 5분
    profit_achievement: int = 3600  # 1시간
    loss_limit: int = 1800          # 30분
    system_error: int = 3600        # 1시간
    status_report: int = 86400      # 24시간
    config_change: int = 300        # 5분
    risk_warning: int = 900         # 15분


@dataclass
class QuietHoursSettings:
    """조용한 시간 설정"""
    enabled: bool = False
    start_time: str = "22:00"  # HH:MM 형식
    end_time: str = "08:00"    # HH:MM 형식
    timezone: str = "Asia/Seoul"


@dataclass
class UserNotificationPreferences:
    """사용자 알림 선호도 설정"""
    user_id: str
    enabled_types: Set[NotificationType] = field(default_factory=set)
    priority_threshold: NotificationPriority = NotificationPriority.LOW
    cooldown_settings: NotificationCooldownSettings = field(default_factory=NotificationCooldownSettings)
    quiet_hours: QuietHoursSettings = field(default_factory=QuietHoursSettings)
    batch_mode: bool = False
    summary_mode: bool = False
    language: str = "ko"
    timezone: str = "Asia/Seoul"
    
    # 개인화 설정
    preferred_notification_count: int = 10  # 시간당 최대 알림 수
    critical_only_mode: bool = False        # CRITICAL 알림만 받기
    auto_snooze_enabled: bool = True        # 자동 스누즈 기능
    snooze_duration: int = 30               # 스누즈 시간 (분)
    
    # 알림 방식 설정
    use_emoji: bool = True                  # 이모지 사용 여부
    include_charts: bool = False            # 차트 포함 여부
    detailed_mode: bool = False             # 상세 모드 여부
    
    # 시간대별 설정
    work_hours_preference: bool = True      # 업무 시간 선호
    weekend_mode: bool = False              # 주말 모드 (알림 감소)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        # 기본 활성화 타입 설정
        if not self.enabled_types:
            self.enabled_types = {
                NotificationType.TRADE_EXECUTION,
                NotificationType.LOSS_LIMIT,
                NotificationType.SYSTEM_ERROR,
                NotificationType.RISK_WARNING
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        
        # Enum을 문자열로 변환
        data['enabled_types'] = [t.value for t in self.enabled_types]
        data['priority_threshold'] = self.priority_threshold.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserNotificationPreferences':
        """딕셔너리에서 객체 생성"""
        # Enum 변환
        if 'enabled_types' in data and isinstance(data['enabled_types'], list):
            data['enabled_types'] = {NotificationType(t) for t in data['enabled_types']}
        
        if 'priority_threshold' in data and isinstance(data['priority_threshold'], int):
            data['priority_threshold'] = NotificationPriority(data['priority_threshold'])
        
        # datetime 변환
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # 중첩 객체 변환
        if 'cooldown_settings' in data and isinstance(data['cooldown_settings'], dict):
            data['cooldown_settings'] = NotificationCooldownSettings(**data['cooldown_settings'])
        
        if 'quiet_hours' in data and isinstance(data['quiet_hours'], dict):
            data['quiet_hours'] = QuietHoursSettings(**data['quiet_hours'])
        
        return cls(**data)


class UserSettingsManager:
    """사용자 설정 관리자"""
    
    def __init__(self, settings_dir: str = "data/user_settings"):
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # 메모리 캐시
        self._cache: Dict[str, UserNotificationPreferences] = {}
        self._cache_expiry = 3600  # 1시간
        self._last_cache_update: Dict[str, float] = {}
        
        # 기본 설정 템플릿
        self._default_preferences = self._create_default_preferences()
    
    def _create_default_preferences(self) -> UserNotificationPreferences:
        """기본 사용자 설정 생성"""
        return UserNotificationPreferences(
            user_id="default",
            enabled_types={
                NotificationType.TRADE_EXECUTION,
                NotificationType.LOSS_LIMIT,
                NotificationType.SYSTEM_ERROR,
                NotificationType.RISK_WARNING
            },
            priority_threshold=NotificationPriority.LOW,
            cooldown_settings=NotificationCooldownSettings(),
            quiet_hours=QuietHoursSettings(),
            batch_mode=False,
            summary_mode=False
        )
    
    def get_user_settings(self, user_id: str) -> UserNotificationPreferences:
        """사용자 설정 조회 (캐시 우선)"""
        # 캐시 확인
        if self._is_cache_valid(user_id):
            return self._cache[user_id]
        
        # 파일에서 로드
        settings = self._load_user_settings(user_id)
        
        # 캐시에 저장
        self._cache[user_id] = settings
        self._last_cache_update[user_id] = datetime.now().timestamp()
        
        return settings
    
    def save_user_settings(self, user_id: str, preferences: UserNotificationPreferences) -> bool:
        """사용자 설정 저장"""
        try:
            # 업데이트 시간 설정
            preferences.updated_at = datetime.now()
            
            # 파일에 저장
            file_path = self.settings_dir / f"{user_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preferences.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 캐시 업데이트
            self._cache[user_id] = preferences
            self._last_cache_update[user_id] = datetime.now().timestamp()
            
            self.logger.info(f"사용자 {user_id} 설정 저장 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 저장 실패: {e}")
            return False
    
    def update_user_settings(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """사용자 설정 부분 업데이트"""
        try:
            # 현재 설정 로드
            current_settings = self.get_user_settings(user_id)
            
            # 업데이트 적용
            updated_settings = self._apply_updates(current_settings, updates)
            
            # 저장
            return self.save_user_settings(user_id, updated_settings)
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 업데이트 실패: {e}")
            return False
    
    def _load_user_settings(self, user_id: str) -> UserNotificationPreferences:
        """파일에서 사용자 설정 로드"""
        file_path = self.settings_dir / f"{user_id}.json"
        
        if not file_path.exists():
            # 기본 설정으로 새 사용자 생성
            default_settings = UserNotificationPreferences(user_id=user_id)
            self.save_user_settings(user_id, default_settings)
            return default_settings
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return UserNotificationPreferences.from_dict(data)
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 로드 실패: {e}")
            # 오류 시 기본 설정 반환
            return UserNotificationPreferences(user_id=user_id)
    
    def _apply_updates(self, current_settings: UserNotificationPreferences, updates: Dict[str, Any]) -> UserNotificationPreferences:
        """설정 업데이트 적용"""
        # 새 설정 객체 생성 (복사)
        updated_data = current_settings.to_dict()
        
        # 업데이트 적용
        for key, value in updates.items():
            if key in updated_data:
                updated_data[key] = value
        
        # 객체로 변환
        return UserNotificationPreferences.from_dict(updated_data)
    
    def _is_cache_valid(self, user_id: str) -> bool:
        """캐시 유효성 확인"""
        if user_id not in self._cache:
            return False
        
        if user_id not in self._last_cache_update:
            return False
        
        current_time = datetime.now().timestamp()
        cache_age = current_time - self._last_cache_update[user_id]
        
        return cache_age < self._cache_expiry
    
    def delete_user_settings(self, user_id: str) -> bool:
        """사용자 설정 삭제"""
        try:
            # 파일 삭제
            file_path = self.settings_dir / f"{user_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            # 캐시에서 제거
            if user_id in self._cache:
                del self._cache[user_id]
            
            if user_id in self._last_cache_update:
                del self._last_cache_update[user_id]
            
            self.logger.info(f"사용자 {user_id} 설정 삭제 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 삭제 실패: {e}")
            return False
    
    def list_all_users(self) -> List[str]:
        """모든 사용자 ID 목록 조회"""
        try:
            user_files = list(self.settings_dir.glob("*.json"))
            user_ids = [f.stem for f in user_files]
            return user_ids
        except Exception as e:
            self.logger.error(f"사용자 목록 조회 실패: {e}")
            return []
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """설정 요약 정보"""
        try:
            user_ids = self.list_all_users()
            
            summary = {
                "total_users": len(user_ids),
                "active_users": 0,
                "notification_types_usage": {},
                "priority_distribution": {},
                "feature_usage": {
                    "batch_mode": 0,
                    "summary_mode": 0,
                    "quiet_hours": 0,
                    "critical_only": 0
                }
            }
            
            # 통계 수집
            for user_id in user_ids:
                try:
                    settings = self.get_user_settings(user_id)
                    
                    # 활성 사용자 (최근 7일 내 업데이트)
                    if (datetime.now() - settings.updated_at).days <= 7:
                        summary["active_users"] += 1
                    
                    # 알림 타입 사용 통계
                    for notification_type in settings.enabled_types:
                        type_name = notification_type.value
                        summary["notification_types_usage"][type_name] = \
                            summary["notification_types_usage"].get(type_name, 0) + 1
                    
                    # 우선순위 분포
                    priority_name = settings.priority_threshold.name
                    summary["priority_distribution"][priority_name] = \
                        summary["priority_distribution"].get(priority_name, 0) + 1
                    
                    # 기능 사용 통계
                    if settings.batch_mode:
                        summary["feature_usage"]["batch_mode"] += 1
                    if settings.summary_mode:
                        summary["feature_usage"]["summary_mode"] += 1
                    if settings.quiet_hours.enabled:
                        summary["feature_usage"]["quiet_hours"] += 1
                    if settings.critical_only_mode:
                        summary["feature_usage"]["critical_only"] += 1
                        
                except Exception as e:
                    self.logger.warning(f"사용자 {user_id} 통계 수집 실패: {e}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"설정 요약 생성 실패: {e}")
            return {"error": str(e)}
    
    def reset_user_settings(self, user_id: str) -> bool:
        """사용자 설정을 기본값으로 리셋"""
        try:
            default_settings = UserNotificationPreferences(user_id=user_id)
            return self.save_user_settings(user_id, default_settings)
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 리셋 실패: {e}")
            return False
    
    def export_user_settings(self, user_id: str, export_path: str) -> bool:
        """사용자 설정 내보내기"""
        try:
            settings = self.get_user_settings(user_id)
            
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.now().isoformat(),
                "settings": settings.to_dict()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"사용자 {user_id} 설정 내보내기 완료: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 내보내기 실패: {e}")
            return False
    
    def import_user_settings(self, user_id: str, import_path: str) -> bool:
        """사용자 설정 가져오기"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            settings_data = import_data.get("settings", {})
            settings_data["user_id"] = user_id  # 사용자 ID 강제 설정
            
            settings = UserNotificationPreferences.from_dict(settings_data)
            return self.save_user_settings(user_id, settings)
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 가져오기 실패: {e}")
            return False
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self._last_cache_update.clear()
        self.logger.info("사용자 설정 캐시 초기화 완료")
    
    def validate_settings(self, preferences: UserNotificationPreferences) -> List[str]:
        """설정 유효성 검증"""
        errors = []
        
        try:
            # 시간 형식 검증
            if preferences.quiet_hours.enabled:
                try:
                    datetime.strptime(preferences.quiet_hours.start_time, "%H:%M")
                    datetime.strptime(preferences.quiet_hours.end_time, "%H:%M")
                except ValueError:
                    errors.append("조용한 시간 형식이 올바르지 않습니다 (HH:MM 형식)")
            
            # 쿨다운 시간 검증
            cooldown_settings = preferences.cooldown_settings
            if cooldown_settings.trade_execution < 0:
                errors.append("거래 실행 쿨다운 시간은 0 이상이어야 합니다")
            if cooldown_settings.profit_achievement < 0:
                errors.append("수익률 달성 쿨다운 시간은 0 이상이어야 합니다")
            
            # 알림 수 제한 검증
            if preferences.preferred_notification_count < 1:
                errors.append("시간당 최대 알림 수는 1 이상이어야 합니다")
            if preferences.preferred_notification_count > 100:
                errors.append("시간당 최대 알림 수는 100 이하여야 합니다")
            
            # 스누즈 시간 검증
            if preferences.snooze_duration < 1:
                errors.append("스누즈 시간은 1분 이상이어야 합니다")
            if preferences.snooze_duration > 1440:  # 24시간
                errors.append("스누즈 시간은 24시간 이하여야 합니다")
            
        except Exception as e:
            errors.append(f"설정 검증 중 오류: {e}")
        
        return errors













