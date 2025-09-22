#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 모듈
YAML 기반 설정 파일 로드 및 관리
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

class ConfigManager:
    """설정 관리 클래스"""
    
    def __init__(self, config_dir: str = "config"):
        """
        설정 관리자 초기화
        
        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._config_cache: Dict[str, Any] = {}
        self._last_modified: Dict[str, float] = {}
        
    def load_config(self, config_name: str, auto_reload: bool = False) -> Dict[str, Any]:
        """
        설정 파일 로드
        
        Args:
            config_name: 설정 파일 이름 (확장자 제외)
            auto_reload: 자동 리로드 여부
            
        Returns:
            설정 데이터 딕셔너리
        """
        try:
            config_path = self.config_dir / f"{config_name}.yaml"
            
            if not config_path.exists():
                self.logger.warning(f"설정 파일이 존재하지 않습니다: {config_path}")
                return self._get_default_config(config_name)
            
            # 파일 수정 시간 확인 (자동 리로드용)
            if auto_reload:
                current_mtime = config_path.stat().st_mtime
                cached_mtime = self._last_modified.get(config_name, 0)
                
                if current_mtime <= cached_mtime and config_name in self._config_cache:
                    return self._config_cache[config_name]
            
            # 환경변수 치환을 위한 로더 설정
            class EnvLoader(yaml.SafeLoader):
                def construct_env_vars(self, node):
                    """환경변수 치환"""
                    value = self.construct_scalar(node)
                    if value.startswith('${') and value.endswith('}'):
                        env_var = value[2:-1]
                        return os.getenv(env_var, value)
                    return value
            
            EnvLoader.add_constructor('!env', EnvLoader.construct_env_vars)
            
            # YAML 파일 로드
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f, Loader=EnvLoader)
            
            # 환경변수 치환 처리
            config = self._replace_env_vars(config)
            
            # 캐시에 저장
            self._config_cache[config_name] = config
            self._last_modified[config_name] = config_path.stat().st_mtime
            
            self.logger.info(f"설정 로드 완료: {config_name}")
            return config
            
        except Exception as e:
            self.logger.error(f"설정 로드 오류: {e}")
            return self._get_default_config(config_name)
    
    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        설정 파일 저장
        
        Args:
            config_name: 설정 파일 이름
            config: 설정 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            config_path = self.config_dir / f"{config_name}.yaml"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # 캐시 업데이트
            self._config_cache[config_name] = config
            self._last_modified[config_name] = config_path.stat().st_mtime
            
            self.logger.info(f"설정 저장 완료: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"설정 저장 오류: {e}")
            return False
    
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        설정 값 조회 (점 표기법 지원)
        
        Args:
            config_name: 설정 파일 이름
            key: 설정 키 (예: 'bot.token')
            default: 기본값
            
        Returns:
            설정 값
        """
        config = self._config_cache.get(config_name)
        if not config:
            config = self.load_config(config_name)
        
        keys = key.split('.')
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def update_config_value(self, config_name: str, key: str, value: Any) -> bool:
        """
        설정 값 업데이트
        
        Args:
            config_name: 설정 파일 이름
            key: 설정 키 (점 표기법 지원)
            value: 새로운 값
            
        Returns:
            업데이트 성공 여부
        """
        try:
            config = self.load_config(config_name)
            
            keys = key.split('.')
            current = config
            
            # 중첩된 딕셔너리 생성
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # 값 설정
            current[keys[-1]] = value
            
            return self.save_config(config_name, config)
            
        except Exception as e:
            self.logger.error(f"설정 값 업데이트 오류: {e}")
            return False
    
    def reload_config(self, config_name: str) -> bool:
        """
        설정 재로드
        
        Args:
            config_name: 설정 파일 이름
            
        Returns:
            재로드 성공 여부
        """
        try:
            # 캐시에서 제거하여 강제 리로드
            if config_name in self._config_cache:
                del self._config_cache[config_name]
            if config_name in self._last_modified:
                del self._last_modified[config_name]
            
            self.load_config(config_name)
            self.logger.info(f"설정 재로드 완료: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"설정 재로드 오류: {e}")
            return False
    
    def _replace_env_vars(self, obj: Any) -> Any:
        """
        환경변수 치환 처리
        
        Args:
            obj: 처리할 객체
            
        Returns:
            환경변수가 치환된 객체
        """
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        else:
            return obj
    
    def _get_default_config(self, config_name: str) -> Dict[str, Any]:
        """
        기본 설정 반환
        
        Args:
            config_name: 설정 파일 이름
            
        Returns:
            기본 설정 딕셔너리
        """
        default_configs = {
            'bot_config': {
                'bot': {
                    'token': '',
                    'username': 'crypto_auto_trader_bot',
                    'description': '암호화폐 자동매매 시스템 알림 봇'
                },
                'update': {
                    'use_webhook': False,
                    'polling_interval': 1.0
                },
                'message': {
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                },
                'rate_limit': {
                    'max_messages_per_minute': 30,
                    'max_commands_per_minute': 10
                },
                'logging': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'security': {
                    'enabled': True,
                    'allowed_users': [],
                    'admin_users': [],
                    'chat_whitelist': []
                },
                'notifications': {
                    'enabled': True,
                    'trade_execution': True,
                    'pnl_alerts': True,
                    'risk_warnings': True,
                    'system_errors': True,
                    'daily_reports': True
                }
            }
        }
        
        return default_configs.get(config_name, {})
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        모든 설정 파일 로드
        
        Returns:
            모든 설정을 포함한 딕셔너리
        """
        all_configs = {}
        
        for config_file in self.config_dir.glob("*.yaml"):
            config_name = config_file.stem
            all_configs[config_name] = self.load_config(config_name)
        
        return all_configs
    
    def validate_config(self, config_name: str) -> bool:
        """
        설정 유효성 검증
        
        Args:
            config_name: 설정 파일 이름
            
        Returns:
            유효성 검증 결과
        """
        try:
            config = self.load_config(config_name)
            
            # 필수 설정 항목 검증
            required_fields = {
                'bot_config': ['bot.token', 'bot.username']
            }
            
            required = required_fields.get(config_name, [])
            for field in required:
                if not self.get_config_value(config_name, field):
                    self.logger.error(f"필수 설정 누락: {field}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"설정 유효성 검증 오류: {e}")
            return False
