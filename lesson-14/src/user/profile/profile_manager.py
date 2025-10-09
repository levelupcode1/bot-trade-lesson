"""
사용자 프로필 관리자
"""

from typing import Dict, Optional, Any
import json
import os
from pathlib import Path

from .user_profile import UserProfile, UserType
from .beginner_profile import BeginnerProfile
from .intermediate_profile import IntermediateProfile
from .advanced_profile import AdvancedProfile


class ProfileManager:
    """사용자 프로필 생성 및 관리"""
    
    PROFILE_CLASSES = {
        UserType.BEGINNER: BeginnerProfile,
        UserType.INTERMEDIATE: IntermediateProfile,
        UserType.ADVANCED: AdvancedProfile,
    }
    
    def __init__(self, profile_dir: str = "data/user_profiles"):
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_cache: Dict[str, UserProfile] = {}
    
    def create_profile(
        self,
        user_id: str,
        user_type: UserType,
        investment_amount: float,
        **kwargs
    ) -> UserProfile:
        """
        새로운 사용자 프로필 생성
        
        Args:
            user_id: 사용자 ID
            user_type: 사용자 유형
            investment_amount: 투자 금액
            **kwargs: 추가 설정
            
        Returns:
            생성된 사용자 프로필
        """
        profile_class = self.PROFILE_CLASSES.get(user_type)
        if not profile_class:
            raise ValueError(f"지원하지 않는 사용자 유형: {user_type}")
        
        profile = profile_class(user_id, investment_amount)
        
        # 추가 설정 적용
        if kwargs:
            self._apply_custom_settings(profile, kwargs)
        
        # 프로필 저장
        self.save_profile(profile)
        
        # 캐시에 추가
        self._profiles_cache[user_id] = profile
        
        return profile
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        저장된 프로필 로드
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            로드된 프로필 또는 None
        """
        # 캐시 확인
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]
        
        # 파일에서 로드
        profile_file = self.profile_dir / f"{user_id}.json"
        if not profile_file.exists():
            return None
        
        with open(profile_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 프로필 객체 생성
        user_type = UserType(data['user_type'])
        profile = self.create_profile(
            user_id=data['user_id'],
            user_type=user_type,
            investment_amount=data['investment_amount']
        )
        
        # 캐시에 추가
        self._profiles_cache[user_id] = profile
        
        return profile
    
    def save_profile(self, profile: UserProfile) -> None:
        """
        프로필을 파일로 저장
        
        Args:
            profile: 저장할 프로필
        """
        profile_file = self.profile_dir / f"{profile.user_id}.json"
        
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """
        프로필 업데이트
        
        Args:
            user_id: 사용자 ID
            updates: 업데이트할 내용
            
        Returns:
            업데이트된 프로필 또는 None
        """
        profile = self.load_profile(user_id)
        if not profile:
            return None
        
        self._apply_custom_settings(profile, updates)
        self.save_profile(profile)
        
        return profile
    
    def upgrade_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        사용자 프로필 업그레이드 (초보 -> 중급 -> 고급)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            업그레이드된 프로필 또는 None
        """
        profile = self.load_profile(user_id)
        if not profile:
            return None
        
        # 업그레이드 경로
        upgrade_path = {
            UserType.BEGINNER: UserType.INTERMEDIATE,
            UserType.INTERMEDIATE: UserType.ADVANCED,
        }
        
        new_type = upgrade_path.get(profile.user_type)
        if not new_type:
            return profile  # 이미 최고 레벨
        
        # 새 프로필 생성
        new_profile = self.create_profile(
            user_id=user_id,
            user_type=new_type,
            investment_amount=profile.investment_amount
        )
        
        return new_profile
    
    def _apply_custom_settings(
        self,
        profile: UserProfile,
        settings: Dict[str, Any]
    ) -> None:
        """커스텀 설정 적용"""
        for key, value in settings.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    
    def list_profiles(self) -> list[str]:
        """저장된 프로필 목록 반환"""
        profiles = []
        for file in self.profile_dir.glob("*.json"):
            profiles.append(file.stem)
        return profiles
    
    def delete_profile(self, user_id: str) -> bool:
        """
        프로필 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            삭제 성공 여부
        """
        profile_file = self.profile_dir / f"{user_id}.json"
        if profile_file.exists():
            profile_file.unlink()
            if user_id in self._profiles_cache:
                del self._profiles_cache[user_id]
            return True
        return False

