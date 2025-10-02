#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
봇 초기화 모듈
텔레그램 봇의 초기화 및 설정 관리
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from typing import Optional, Dict, Any
import asyncio
import logging
from pathlib import Path
import os

from ..config.config_manager import ConfigManager
from ..utils.logger import get_logger, setup_logging
from ..handlers.simple_handlers import (
    start_command, help_command, handle_text_message
)
from ..handlers.trading_handlers import (
    trades_command, profit_command, status_command, settings_command,
    stop_trading_command, start_trading_command, handle_trading_callback
)
from ..notifications.notification_service import NotificationService

class BotInitializer:
    """텔레그램 봇 초기화 클래스 (python-telegram-bot 20.x)"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.application: Optional[Application] = None
        self.config_manager = ConfigManager(config_dir)
        self.logger = get_logger(__name__)
        self.config: Dict[str, Any] = {}
        self.notification_service: Optional[NotificationService] = None
        
    async def initialize(self) -> None:
        """봇 초기화"""
        try:
            self._load_configuration()
            self._setup_logging()
            self._create_application()
            self._register_handlers()
            await self._initialize_notification_service()
            self.logger.info("텔레그램 봇 초기화 완료")
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
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                bot_config = self.config.get('bot', {})
                bot_token = bot_config.get('token')

            if not bot_token:
                raise ValueError("봇 토큰이 설정되지 않았습니다. TELEGRAM_BOT_TOKEN 환경 변수를 설정하거나 설정 파일에 토큰을 추가하세요.")

            self.application = Application.builder().token(bot_token).build()
            self.logger.info("텔레그램 애플리케이션 생성 완료")
        except Exception as e:
            self.logger.error(f"애플리케이션 생성 오류: {e}")
            raise
    
    def _register_handlers(self) -> None:
        """핸들러 등록 (20.x 방식)"""
        try:
            # 기본 명령어 핸들러
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))

            # 거래 관련 명령어 핸들러
            self.application.add_handler(CommandHandler("trades", trades_command))
            self.application.add_handler(CommandHandler("profit", profit_command))
            self.application.add_handler(CommandHandler("status", status_command))
            self.application.add_handler(CommandHandler("settings", settings_command))

            # 거래 제어 명령어 핸들러
            self.application.add_handler(CommandHandler("stop", stop_trading_command))
            self.application.add_handler(CommandHandler("stop_trading", stop_trading_command))
            self.application.add_handler(CommandHandler("start_trading", start_trading_command))

            # 콜백 쿼리 핸들러 (인라인 키보드)
            self.application.add_handler(CallbackQueryHandler(handle_trading_callback))

            # 일반 텍스트 메시지 핸들러 (filters 사용)
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
            )

            self.logger.info("핸들러 등록 완료")
        except Exception as e:
            self.logger.error(f"핸들러 등록 오류: {e}")
            raise
    
    async def _initialize_notification_service(self) -> None:
        """알림 서비스 초기화"""
        try:
            if self.application and self.application.bot:
                self.notification_service = NotificationService(
                    telegram_bot=self.application.bot,
                    settings_dir="data/user_settings"
                )
                # 알림 서비스 시작
                await self.notification_service.start()
                self.logger.info("알림 서비스 초기화 및 시작 완료")
        except Exception as e:
            self.logger.error(f"알림 서비스 초기화 오류: {e}")
            raise

    async def run(self) -> None:
        """봇 실행 (20.x 방식)"""
        try:
            if not self.application:
                raise RuntimeError("봇이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
            
            self.logger.info("텔레그램 봇 폴링 시작")
            await self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            self.logger.error(f"봇 시작 오류: {e}")
            raise

    async def stop(self) -> None:
        """봇 중지 (20.x 방식)"""
        try:
            # 알림 서비스 중지
            if self.notification_service:
                await self.notification_service.stop()
            
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
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
