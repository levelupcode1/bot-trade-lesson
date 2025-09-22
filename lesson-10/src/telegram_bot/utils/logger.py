#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로깅 유틸리티 모듈
구조화된 로깅 시스템 제공
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

# 인코딩 유틸리티 임포트
from .encoding_utils import setup_windows_encoding, setup_logging_encoding

# Windows 환경에서 인코딩 설정
setup_windows_encoding()

class StructuredLogger:
    """구조화된 로깅 클래스"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        구조화된 로거 초기화
        
        Args:
            name: 로거 이름
            config: 로깅 설정
        """
        self.name = name
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 로깅 설정 반환"""
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'logs/bot.log',
            'max_file_size': '10MB',
            'backup_count': 5,
            'console_output': True
        }
    
    def _setup_logger(self) -> None:
        """로거 설정"""
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 로그 레벨 설정
        level = getattr(logging, self.config.get('level', 'INFO').upper())
        self.logger.setLevel(level)
        
        # 포맷터 설정
        formatter = logging.Formatter(self.config.get('format'))
        
        # 파일 핸들러 설정
        if 'file' in self.config:
            self._setup_file_handler(formatter)
        
        # 콘솔 핸들러 설정
        if self.config.get('console_output', True):
            self._setup_console_handler(formatter)
        
        # 프로파게이션 방지
        self.logger.propagate = False
    
    def _setup_file_handler(self, formatter: logging.Formatter) -> None:
        """파일 핸들러 설정"""
        log_file = Path(self.config['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 크기 설정
        max_bytes = self._parse_size(self.config.get('max_file_size', '10MB'))
        backup_count = self.config.get('backup_count', 5)
        
        # 로테이팅 파일 핸들러
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _setup_console_handler(self, formatter: logging.Formatter) -> None:
        """콘솔 핸들러 설정"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        # 로깅 인코딩 설정 적용
        setup_logging_encoding()
        self.logger.addHandler(handler)
    
    def _parse_size(self, size_str: str) -> int:
        """크기 문자열을 바이트로 변환"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def log_structured(self, level: str, message: str, **kwargs) -> None:
        """
        구조화된 로그 기록
        
        Args:
            level: 로그 레벨
            message: 로그 메시지
            **kwargs: 추가 데이터
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'message': message,
            'logger': self.name,
            **kwargs
        }
        
        # JSON 형태로 로그 기록
        json_message = json.dumps(log_data, ensure_ascii=False)
        
        log_level = getattr(logging, level.upper())
        self.logger.log(log_level, json_message)
    
    def info(self, message: str, **kwargs) -> None:
        """정보 로그"""
        self.log_structured('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """경고 로그"""
        self.log_structured('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """오류 로그"""
        self.log_structured('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """디버그 로그"""
        self.log_structured('DEBUG', message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """중요 로그"""
        self.log_structured('CRITICAL', message, **kwargs)
    
    def log_exception(self, message: str, exception: Exception, **kwargs) -> None:
        """
        예외 로그 기록
        
        Args:
            message: 로그 메시지
            exception: 예외 객체
            **kwargs: 추가 데이터
        """
        self.error(
            message,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback=traceback.format_exc(),
            **kwargs
        )
    
    def log_user_action(self, user_id: int, action: str, **kwargs) -> None:
        """
        사용자 액션 로그
        
        Args:
            user_id: 사용자 ID
            action: 액션 이름
            **kwargs: 추가 데이터
        """
        self.info(
            f"사용자 액션: {action}",
            user_id=user_id,
            action=action,
            **kwargs
        )
    
    def log_bot_event(self, event_type: str, **kwargs) -> None:
        """
        봇 이벤트 로그
        
        Args:
            event_type: 이벤트 타입
            **kwargs: 추가 데이터
        """
        self.info(
            f"봇 이벤트: {event_type}",
            event_type=event_type,
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """
        성능 로그
        
        Args:
            operation: 작업 이름
            duration: 소요 시간 (초)
            **kwargs: 추가 데이터
        """
        self.info(
            f"성능 측정: {operation}",
            operation=operation,
            duration=duration,
            **kwargs
        )

class LoggerFactory:
    """로거 팩토리 클래스"""
    
    _loggers: Dict[str, StructuredLogger] = {}
    _default_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
        """
        로거 인스턴스 반환 (싱글톤)
        
        Args:
            name: 로거 이름
            config: 로깅 설정
            
        Returns:
            구조화된 로거 인스턴스
        """
        if name not in cls._loggers:
            logger_config = config or cls._default_config
            cls._loggers[name] = StructuredLogger(name, logger_config)
        
        return cls._loggers[name]
    
    @classmethod
    def set_default_config(cls, config: Dict[str, Any]) -> None:
        """
        기본 설정 설정
        
        Args:
            config: 기본 로깅 설정
        """
        cls._default_config = config
    
    @classmethod
    def setup_root_logger(cls, config: Dict[str, Any]) -> None:
        """
        루트 로거 설정
        
        Args:
            config: 로깅 설정
        """
        cls.set_default_config(config)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.get('level', 'INFO').upper()))
        
        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 포맷터 설정
        formatter = logging.Formatter(config.get('format'))
        
        # 콘솔 핸들러
        if config.get('console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            # 로깅 인코딩 설정 적용
            setup_logging_encoding()
            root_logger.addHandler(console_handler)

# 편의 함수들
def get_logger(name: str) -> StructuredLogger:
    """로거 인스턴스 반환"""
    return LoggerFactory.get_logger(name)

def setup_logging(config: Dict[str, Any]) -> None:
    """로깅 시스템 설정"""
    LoggerFactory.setup_root_logger(config)

def log_user_action(user_id: int, action: str, **kwargs) -> None:
    """사용자 액션 로그"""
    logger = get_logger('user_actions')
    logger.log_user_action(user_id, action, **kwargs)

def log_bot_event(event_type: str, **kwargs) -> None:
    """봇 이벤트 로그"""
    logger = get_logger('bot_events')
    logger.log_bot_event(event_type, **kwargs)

def log_performance(operation: str, duration: float, **kwargs) -> None:
    """성능 로그"""
    logger = get_logger('performance')
    logger.log_performance(operation, duration, **kwargs)
