"""
전략 레지스트리 - 전략 동적 로딩 및 관리
"""

from typing import Dict, List, Optional, Type, Callable
from abc import ABC, abstractmethod
import importlib
import inspect
from pathlib import Path


class BaseStrategy(ABC):
    """전략 기본 인터페이스"""
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """전략 실행"""
        pass


class StrategyMetadata:
    """전략 메타데이터"""
    
    def __init__(
        self,
        name: str,
        strategy_class: Type[BaseStrategy],
        level: str,
        description: str = "",
        required_permissions: List[str] = None
    ):
        self.name = name
        self.strategy_class = strategy_class
        self.level = level  # basic, advanced, expert
        self.description = description
        self.required_permissions = required_permissions or []


class StrategyRegistry:
    """전략 레지스트리 - 전략 등록 및 관리"""
    
    def __init__(self):
        self._strategies: Dict[str, StrategyMetadata] = {}
        self._level_strategies: Dict[str, List[str]] = {
            "basic": [],
            "advanced": [],
            "expert": []
        }
    
    def register(
        self,
        name: str,
        strategy_class: Type[BaseStrategy],
        level: str = "basic",
        description: str = "",
        required_permissions: List[str] = None
    ) -> None:
        """
        전략 등록
        
        Args:
            name: 전략 이름
            strategy_class: 전략 클래스
            level: 전략 레벨 (basic/advanced/expert)
            description: 전략 설명
            required_permissions: 필요 권한
        """
        if level not in self._level_strategies:
            raise ValueError(f"잘못된 전략 레벨: {level}")
        
        metadata = StrategyMetadata(
            name=name,
            strategy_class=strategy_class,
            level=level,
            description=description,
            required_permissions=required_permissions
        )
        
        self._strategies[name] = metadata
        self._level_strategies[level].append(name)
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """전략 클래스 가져오기"""
        metadata = self._strategies.get(name)
        return metadata.strategy_class if metadata else None
    
    def get_metadata(self, name: str) -> Optional[StrategyMetadata]:
        """전략 메타데이터 가져오기"""
        return self._strategies.get(name)
    
    def list_strategies(self, level: Optional[str] = None) -> List[str]:
        """
        전략 목록 반환
        
        Args:
            level: 레벨 필터 (None이면 전체)
            
        Returns:
            전략 이름 목록
        """
        if level:
            return self._level_strategies.get(level, [])
        return list(self._strategies.keys())
    
    def get_strategies_by_level(self, level: str) -> List[StrategyMetadata]:
        """레벨별 전략 메타데이터 목록"""
        strategy_names = self._level_strategies.get(level, [])
        return [self._strategies[name] for name in strategy_names]
    
    def is_registered(self, name: str) -> bool:
        """전략 등록 여부 확인"""
        return name in self._strategies
    
    def unregister(self, name: str) -> bool:
        """전략 등록 해제"""
        if name in self._strategies:
            metadata = self._strategies[name]
            self._level_strategies[metadata.level].remove(name)
            del self._strategies[name]
            return True
        return False
    
    def get_available_strategies_for_profile(
        self,
        allowed_strategies: List[str]
    ) -> List[StrategyMetadata]:
        """
        프로필에 허용된 전략 목록 반환
        
        Args:
            allowed_strategies: 허용된 전략 목록 (["*"]이면 전체)
            
        Returns:
            사용 가능한 전략 메타데이터 목록
        """
        if "*" in allowed_strategies:
            return list(self._strategies.values())
        
        available = []
        for strategy_name in allowed_strategies:
            if strategy_name in self._strategies:
                available.append(self._strategies[strategy_name])
        
        return available


# 글로벌 레지스트리 인스턴스
_global_registry = StrategyRegistry()


def register_strategy(
    name: str,
    level: str = "basic",
    description: str = "",
    required_permissions: List[str] = None
):
    """
    전략 등록 데코레이터
    
    Usage:
        @register_strategy("my_strategy", level="advanced")
        class MyStrategy(BaseStrategy):
            def execute(self):
                pass
    """
    def decorator(strategy_class: Type[BaseStrategy]):
        _global_registry.register(
            name=name,
            strategy_class=strategy_class,
            level=level,
            description=description,
            required_permissions=required_permissions
        )
        return strategy_class
    return decorator


def get_global_registry() -> StrategyRegistry:
    """글로벌 레지스트리 반환"""
    return _global_registry

