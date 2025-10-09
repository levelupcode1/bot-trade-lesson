"""
전략 동적 로더
"""

from typing import Dict, List, Optional, Any
import importlib
import inspect
from pathlib import Path
import logging

from .strategy_registry import StrategyRegistry, BaseStrategy, get_global_registry
from ..user.profile.user_profile import UserProfile


logger = logging.getLogger(__name__)


class StrategyLoader:
    """전략 동적 로딩 시스템"""
    
    def __init__(self, registry: Optional[StrategyRegistry] = None):
        self.registry = registry or get_global_registry()
        self._loaded_modules: Dict[str, Any] = {}
    
    def load_strategies_from_directory(self, directory: str) -> int:
        """
        디렉토리에서 전략 자동 로드
        
        Args:
            directory: 전략 파일이 있는 디렉토리 경로
            
        Returns:
            로드된 전략 수
        """
        path = Path(directory)
        if not path.exists():
            logger.warning(f"디렉토리를 찾을 수 없습니다: {directory}")
            return 0
        
        count = 0
        for py_file in path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                # 모듈 동적 로드
                module_name = py_file.stem
                module_path = f"src.strategy.{path.name}.{module_name}"
                
                module = importlib.import_module(module_path)
                self._loaded_modules[module_name] = module
                
                # 전략 클래스 찾기 및 등록
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseStrategy) and 
                        obj is not BaseStrategy):
                        
                        # 이미 등록되어 있지 않으면 등록
                        if not self.registry.is_registered(name):
                            level = self._determine_strategy_level(path.name)
                            self.registry.register(
                                name=name,
                                strategy_class=obj,
                                level=level,
                                description=obj.__doc__ or ""
                            )
                            count += 1
                            logger.info(f"전략 로드: {name} (레벨: {level})")
                
            except Exception as e:
                logger.error(f"전략 로드 실패 ({py_file.name}): {e}")
        
        return count
    
    def load_all_strategies(self) -> int:
        """모든 전략 디렉토리에서 전략 로드"""
        total_count = 0
        
        # 기본 전략
        count = self.load_strategies_from_directory("src/strategy/basic")
        logger.info(f"기본 전략 {count}개 로드 완료")
        total_count += count
        
        # 고급 전략
        count = self.load_strategies_from_directory("src/strategy/advanced")
        logger.info(f"고급 전략 {count}개 로드 완료")
        total_count += count
        
        # 전문 전략
        count = self.load_strategies_from_directory("src/strategy/expert")
        logger.info(f"전문 전략 {count}개 로드 완료")
        total_count += count
        
        return total_count
    
    def load_custom_strategy(
        self,
        file_path: str,
        strategy_name: Optional[str] = None
    ) -> bool:
        """
        커스텀 전략 파일 로드
        
        Args:
            file_path: 전략 파일 경로
            strategy_name: 전략 이름 (None이면 파일명 사용)
            
        Returns:
            로드 성공 여부
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"파일을 찾을 수 없습니다: {file_path}")
                return False
            
            # 동적 모듈 로드
            spec = importlib.util.spec_from_file_location(path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self._loaded_modules[path.stem] = module
            
            # 전략 클래스 찾기
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseStrategy) and 
                    obj is not BaseStrategy):
                    
                    final_name = strategy_name or name
                    self.registry.register(
                        name=final_name,
                        strategy_class=obj,
                        level="expert",  # 커스텀은 expert 레벨
                        description=obj.__doc__ or "커스텀 전략"
                    )
                    logger.info(f"커스텀 전략 로드: {final_name}")
                    return True
            
            logger.warning(f"전략 클래스를 찾을 수 없습니다: {file_path}")
            return False
            
        except Exception as e:
            logger.error(f"커스텀 전략 로드 실패: {e}")
            return False
    
    def get_strategies_for_profile(
        self,
        profile: UserProfile
    ) -> List[str]:
        """
        프로필에 허용된 전략 목록 반환
        
        Args:
            profile: 사용자 프로필
            
        Returns:
            전략 이름 목록
        """
        available_strategies = self.registry.get_available_strategies_for_profile(
            profile.allowed_strategies
        )
        return [metadata.name for metadata in available_strategies]
    
    def create_strategy_instance(
        self,
        strategy_name: str,
        profile: UserProfile,
        **kwargs
    ) -> Optional[BaseStrategy]:
        """
        전략 인스턴스 생성
        
        Args:
            strategy_name: 전략 이름
            profile: 사용자 프로필
            **kwargs: 전략 초기화 인자
            
        Returns:
            전략 인스턴스 또는 None
        """
        # 권한 확인
        if not self._can_use_strategy(strategy_name, profile):
            logger.warning(f"전략 사용 권한 없음: {strategy_name}")
            return None
        
        # 전략 클래스 가져오기
        strategy_class = self.registry.get_strategy(strategy_name)
        if not strategy_class:
            logger.error(f"전략을 찾을 수 없습니다: {strategy_name}")
            return None
        
        try:
            # 인스턴스 생성
            instance = strategy_class(**kwargs)
            logger.info(f"전략 인스턴스 생성: {strategy_name}")
            return instance
        except Exception as e:
            logger.error(f"전략 인스턴스 생성 실패: {e}")
            return None
    
    def _can_use_strategy(
        self,
        strategy_name: str,
        profile: UserProfile
    ) -> bool:
        """전략 사용 가능 여부 확인"""
        if "*" in profile.allowed_strategies:
            return True
        return strategy_name in profile.allowed_strategies
    
    def _determine_strategy_level(self, directory_name: str) -> str:
        """디렉토리 이름으로 전략 레벨 결정"""
        level_map = {
            "basic": "basic",
            "advanced": "advanced",
            "expert": "expert"
        }
        return level_map.get(directory_name, "basic")

