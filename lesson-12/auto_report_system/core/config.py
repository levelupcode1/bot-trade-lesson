#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 모듈
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """리포트 설정"""
    output_dir: str = "auto_reports"
    output_formats: List[str] = field(default_factory=lambda: ['html'])
    send_email: bool = False
    send_telegram: bool = False
    recipients: List[str] = field(default_factory=list)

@dataclass
class ScheduleConfig:
    """스케줄 설정"""
    daily_enabled: bool = True
    daily_hour: int = 23
    daily_minute: int = 0
    
    weekly_enabled: bool = True
    weekly_day: int = 6  # 일요일
    weekly_hour: int = 23
    weekly_minute: int = 30
    
    monthly_enabled: bool = True
    monthly_day: int = 1
    monthly_hour: int = 1
    monthly_minute: int = 0
    
    alert_enabled: bool = True
    alert_interval_minutes: int = 5

@dataclass
class AlertConfig:
    """알림 임계값 설정"""
    max_drawdown: float = 10.0
    daily_loss: float = 5.0
    win_rate_drop: float = 40.0

class ConfigManager:
    """설정 관리 클래스"""
    
    @staticmethod
    def load_config(config_path: str = None) -> Dict[str, Any]:
        """설정 파일 로드"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        if not Path(config_path).exists():
            logger.warning(f"설정 파일 없음: {config_path}, 기본 설정 사용")
            return ConfigManager.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"설정 파일 로드: {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"설정 로드 오류: {e}")
            return ConfigManager.get_default_config()
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'report': {
                'output_dir': 'auto_reports',
                'output_formats': ['html'],
                'send_email': False,
                'send_telegram': False,
                'recipients': []
            },
            'schedule': {
                'daily': {
                    'enabled': True,
                    'hour': 23,
                    'minute': 0
                },
                'weekly': {
                    'enabled': False,
                    'day_of_week': 6,
                    'hour': 23,
                    'minute': 30
                },
                'monthly': {
                    'enabled': False,
                    'day': 1,
                    'hour': 1,
                    'minute': 0
                },
                'alert': {
                    'enabled': True,
                    'interval_minutes': 5
                }
            },
            'alerts': {
                'max_drawdown': 10.0,
                'daily_loss': 5.0,
                'win_rate_drop': 40.0
            },
            'telegram': {
                'token': '',
                'chat_id': ''
            },
            'email': {
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_address': ''
            }
        }
    
    @staticmethod
    def save_default_config(config_path: str = None):
        """기본 설정 파일 생성"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        config = ConfigManager.get_default_config()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"기본 설정 파일 생성: {config_path}")
            
        except Exception as e:
            logger.error(f"설정 파일 저장 오류: {e}")

