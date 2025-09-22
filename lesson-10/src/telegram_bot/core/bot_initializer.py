#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
봇 초기화 모듈
텔레그램 봇의 초기화 및 설정 관리
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import TEXT
from typing import Optional, Dict, Any
import asyncio
import logging
from pathlib import Path

from ..config.config_manager import ConfigManager
from ..utils.logger import get_logger, setup_logging
from ..handlers.basic_commands import (
    StartCommandHandler, HelpCommandHandler, StatusCommandHandler, CallbackQueryHandler
)

class BotInitializer:
    """텔레그램 봇 초기화 클래스"""
    
    def __init__(self, config_dir: str = "config"):
        """
        봇 초기화자 초기화
        
        Args:
            config_dir: 설정 파일 디렉토리
        """
        self.config_dir = config_dir
        self.application: Optional[Application] = None
        self.config_manager = ConfigManager(config_dir)
        self.logger = get_logger(__name__)
        self.config: Dict[str, Any] = {}
        
    def initialize(self) -> Application:
        """
        봇 초기화
        
        Returns:
            초기화된 텔레그램 애플리케이션
        """
        try:
            # 1. 설정 로드
            self._load_configuration()
            
            # 2. 로깅 시스템 설정
            self._setup_logging()
            
            # 3. 텔레그램 애플리케이션 생성
            self._create_application()
            
            # 4. 핸들러 등록
            self._register_handlers()
            
            # 5. 미들웨어 설정
            self._setup_middleware()
            
            self.logger.info("텔레그램 봇 초기화 완료")
            return self.application
            
        except Exception as e:
            self.logger.error(f"봇 초기화 오류: {e}")
            raise
    
    def _load_configuration(self) -> None:
        """설정 파일 로드"""
        try:
            # 봇 설정 로드
            self.config = self.config_manager.load_config('bot_config')
            
            # 설정 유효성 검증
            if not self.config_manager.validate_config('bot_config'):
                raise ValueError("봇 설정이 유효하지 않습니다")
            
            self.logger.info("설정 파일 로드 완료")
            
        except Exception as e:
            self.logger.error(f"설정 로드 오류: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """로깅 시스템 설정"""
        try:
            logging_config = self.config.get('logging', {})
            setup_logging(logging_config)
            
            self.logger.info("로깅 시스템 설정 완료")
            
        except Exception as e:
            self.logger.error(f"로깅 설정 오류: {e}")
            raise
    
    def _create_application(self) -> None:
        """텔레그램 애플리케이션 생성"""
        try:
            bot_config = self.config.get('bot', {})
            bot_token = bot_config.get('token')
            
            if not bot_token:
                raise ValueError("봇 토큰이 설정되지 않았습니다")
            
            # 애플리케이션 생성
            self.application = Application.builder().token(bot_token).build()
            
            self.logger.info("텔레그램 애플리케이션 생성 완료")
            
        except Exception as e:
            self.logger.error(f"애플리케이션 생성 오류: {e}")
            raise
    
    def _register_handlers(self) -> None:
        """핸들러 등록"""
        try:
            # 기본 명령어 핸들러
            start_handler = StartCommandHandler()
            help_handler = HelpCommandHandler()
            status_handler = StatusCommandHandler()
            callback_handler = CallbackQueryHandler()
            
            # 명령어 핸들러 등록
            self.application.add_handler(CommandHandler("start", start_handler.execute))
            self.application.add_handler(CommandHandler("help", help_handler.execute))
            self.application.add_handler(CommandHandler("status", status_handler.execute))
            
            # 콜백 쿼리 핸들러
            self.application.add_handler(CallbackQueryHandler(callback_handler.handle))
            
            # 일반 텍스트 메시지 핸들러
            self.application.add_handler(MessageHandler(TEXT, self._handle_text_message))
            
            self.logger.info("핸들러 등록 완료")
            
        except Exception as e:
            self.logger.error(f"핸들러 등록 오류: {e}")
            raise
    
    def _setup_middleware(self) -> None:
        """미들웨어 설정"""
        try:
            # Updater에서는 미들웨어 설정이 간단함
            self.logger.info("미들웨어 설정 완료")
            
        except Exception as e:
            self.logger.error(f"미들웨어 설정 오류: {e}")
            raise
    
    
    def _handle_text_message(self, update, context) -> None:
        """일반 텍스트 메시지 처리"""
        try:
            message_text = update.message.text
            
            # 명령어가 아닌 일반 메시지 처리
            if not message_text.startswith('/'):
                # 간단한 응답
                update.message.reply_text(
                    "안녕하세요! 도움이 필요하시면 /help 명령어를 사용하세요."
                )
            
        except Exception as e:
            self.logger.error(f"텍스트 메시지 처리 오류: {e}")
    
    
    def start_bot(self) -> None:
        """봇 시작"""
        try:
            if not self.application:
                raise RuntimeError("봇이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
            
            # 폴링 시작 (동기적으로 실행)
            self.application.run_polling()
            
        except Exception as e:
            self.logger.error(f"봇 시작 오류: {e}")
            raise
    
    def stop_bot(self) -> None:
        """봇 중지"""
        try:
            if self.application:
                self.application.stop()
                self.logger.info("봇 중지 완료")
            
        except Exception as e:
            self.logger.error(f"봇 중지 오류: {e}")
    
    def reload_config(self) -> bool:
        """설정 재로드"""
        try:
            success = self.config_manager.reload_config('bot_config')
            if success:
                self.config = self.config_manager.load_config('bot_config')
                self.logger.info("설정 재로드 완료")
            return success
            
        except Exception as e:
            self.logger.error(f"설정 재로드 오류: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        설정 값 조회
        
        Args:
            key: 설정 키 (점 표기법 지원)
            default: 기본값
            
        Returns:
            설정 값
        """
        return self.config_manager.get_config_value('bot_config', key, default)
