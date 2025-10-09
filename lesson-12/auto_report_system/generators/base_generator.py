#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리포트 생성기 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseReportGenerator(ABC):
    """리포트 생성기 기본 클래스"""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.output_dir if hasattr(config, 'output_dir') else "reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate(self, report_type: str, data: Dict[str, Any]) -> str:
        """
        리포트 생성
        
        Args:
            report_type: 리포트 유형 (daily, weekly, monthly, alert)
            data: 리포트 데이터
            
        Returns:
            생성된 파일 경로
        """
        pass
    
    def _get_output_filename(self, report_type: str, extension: str) -> Path:
        """출력 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{report_type}_report_{timestamp}.{extension}"

