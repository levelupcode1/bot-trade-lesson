#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리포트 템플릿 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseReportTemplate(ABC):
    """리포트 템플릿 기본 클래스"""
    
    @abstractmethod
    def get_title(self) -> str:
        """리포트 제목"""
        pass
    
    @abstractmethod
    def get_sections(self) -> list:
        """리포트 섹션 구성"""
        pass
    
    def format_metric(self, value: float, is_percentage: bool = False, 
                     decimals: int = 2) -> str:
        """메트릭 포맷팅"""
        if is_percentage:
            return f"{value:.{decimals}f}%"
        return f"{value:.{decimals}f}"
    
    def format_currency(self, value: float) -> str:
        """통화 포맷팅"""
        return f"₩{value:,.0f}"
    
    def get_emoji_by_value(self, value: float, threshold_positive: float = 0) -> str:
        """값에 따른 이모지 반환"""
        if value > threshold_positive:
            return "📈"
        elif value < 0:
            return "📉"
        return "➖"
    
    def get_color_class(self, value: float) -> str:
        """값에 따른 색상 클래스"""
        if value > 0:
            return "positive"
        elif value < 0:
            return "negative"
        return "neutral"

