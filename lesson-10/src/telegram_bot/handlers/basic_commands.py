#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기본 명령어 핸들러
/start, /help, /status 등의 기본 명령어 처리
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import List
import asyncio
from datetime import datetime

from .base_handler import BaseHandler

class StartCommandHandler(BaseHandler):
    """시작 명령어 핸들러"""
    
    @property
    def command_name(self) -> str:
        return "start"
    
    @property
    def description(self) -> str:
        return "봇을 시작하고 환영 메시지를 표시합니다"
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args: List[str]) -> None:
        """시작 명령어 실행"""
        try:
            # 사용자 정보 가져오기
            user_info = self.get_user_info(update)
            user_name = user_info['first_name'] or user_info['username'] or '사용자'
            
            # 환영 메시지 데이터
            welcome_data = {
                'user_name': user_name,
                'bot_name': 'CryptoAutoTrader 봇'
            }
            
            # 메인 메뉴 키보드 생성
            keyboard = self.response_builder.create_main_menu_keyboard()
            
            # 메시지 빌드 및 전송
            message_data = self.response_builder.build_message('welcome', welcome_data, keyboard)
            await self.send_message(update, **message_data)
            
            # 성공 로그
            self.log_command_usage(update, args, success=True)
            
        except Exception as e:
            await self.handle_execution_error(update, e)

class HelpCommandHandler(BaseHandler):
    """도움말 명령어 핸들러"""
    
    @property
    def command_name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "사용 가능한 명령어 목록을 표시합니다"
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args: List[str]) -> None:
        """도움말 명령어 실행"""
        try:
            # 명령어 카테고리별 분류
            categories = {
                "기본 명령어": [
                    {"command": "/start", "description": "봇 시작 및 환영 메시지"},
                    {"command": "/help", "description": "도움말 표시"},
                    {"command": "/status", "description": "시스템 상태 확인"}
                ],
                "거래 명령어": [
                    {"command": "/trades", "description": "거래 내역 조회"},
                    {"command": "/positions", "description": "포지션 현황 확인"},
                    {"command": "/pnl", "description": "수익률 확인"},
                    {"command": "/start_trading", "description": "자동매매 시작"},
                    {"command": "/stop_trading", "description": "자동매매 중지"}
                ],
                "설정 명령어": [
                    {"command": "/settings", "description": "설정 메뉴 열기"},
                    {"command": "/reload_config", "description": "설정 파일 재로드"}
                ]
            }
            
            # 도움말 메시지 데이터
            help_data = {
                'categories': categories
            }
            
            # 메시지 빌드 및 전송
            message_data = self.response_builder.build_message('help', help_data)
            await self.send_message(update, **message_data)
            
            # 성공 로그
            self.log_command_usage(update, args, success=True)
            
        except Exception as e:
            await self.handle_execution_error(update, e)

class StatusCommandHandler(BaseHandler):
    """상태 명령어 핸들러"""
    
    @property
    def command_name(self) -> str:
        return "status"
    
    @property
    def description(self) -> str:
        return "시스템 및 거래 상태를 확인합니다"
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args: List[str]) -> None:
        """상태 명령어 실행"""
        try:
            # 실제 구현에서는 외부 시스템에서 상태 정보를 가져와야 함
            # 여기서는 모의 데이터 사용
            status_data = await self._get_system_status()
            
            # 상태 메시지 빌드 및 전송
            message_data = self.response_builder.build_message('status', status_data)
            await self.send_message(update, **message_data)
            
            # 성공 로그
            self.log_command_usage(update, args, success=True)
            
        except Exception as e:
            await self.handle_execution_error(update, e)
    
    async def _get_system_status(self) -> dict:
        """시스템 상태 정보 가져오기 (모의 구현)"""
        # 실제 구현에서는 외부 시스템 API 호출
        return {
            'system_status': 'running',
            'trading_status': 'stopped',
            'uptime': '2일 14시간 32분',
            'last_update': datetime.now()
        }

class CallbackQueryHandler(BaseHandler):
    """콜백 쿼리 핸들러"""
    
    def __init__(self):
        super().__init__()
        self.callback_handlers = {
            'start_trading': self._handle_start_trading,
            'stop_trading': self._handle_stop_trading,
            'status': self._handle_status,
            'positions': self._handle_positions,
            'pnl': self._handle_pnl,
            'settings': self._handle_settings,
            'help': self._handle_help,
            'main_menu': self._handle_main_menu
        }
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """콜백 쿼리 처리"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            # 콜백 데이터 파싱
            if callback_data in self.callback_handlers:
                await self.callback_handlers[callback_data](update, context)
            else:
                await self._handle_unknown_callback(update, context, callback_data)
            
            # 쿼리 답변
            await query.answer()
            
        except Exception as e:
            self.logger.error(f"콜백 쿼리 처리 오류: {e}")
            await query.answer("처리 중 오류가 발생했습니다.")
    
    async def _handle_start_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """거래 시작 콜백 처리"""
        # 실제 구현에서는 거래 시스템 시작
        await self.send_success_message(update, "자동매매를 시작했습니다.")
    
    async def _handle_stop_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """거래 중지 콜백 처리"""
        # 실제 구현에서는 거래 시스템 중지
        await self.send_success_message(update, "자동매매를 중지했습니다.")
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """상태 확인 콜백 처리"""
        status_handler = StatusCommandHandler()
        await status_handler.execute(update, context, [])
    
    async def _handle_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """포지션 현황 콜백 처리"""
        # 실제 구현에서는 포지션 데이터 조회
        positions_data = {
            'positions': [],
            'total_value': 0,
            'total_pnl': 0
        }
        
        message_data = self.response_builder.build_message('position', positions_data)
        await self.send_message(update, **message_data)
    
    async def _handle_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """수익률 확인 콜백 처리"""
        # 실제 구현에서는 수익률 데이터 조회
        pnl_data = {
            'realized_pnl': 0,
            'unrealized_pnl': 0,
            'total_pnl': 0,
            'total_return': 0,
            'period': '1일',
            'strategy': 'N/A'
        }
        
        message_data = self.response_builder.build_message('pnl', pnl_data)
        await self.send_message(update, **message_data)
    
    async def _handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """설정 메뉴 콜백 처리"""
        keyboard = self.response_builder.create_settings_keyboard()
        message_data = {
            'text': '⚙️ *설정 메뉴*\n\n설정을 변경하려면 옵션을 선택하세요.',
            'parse_mode': 'Markdown',
            'reply_markup': keyboard
        }
        await self.send_message(update, **message_data)
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """도움말 콜백 처리"""
        help_handler = HelpCommandHandler()
        await help_handler.execute(update, context, [])
    
    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """메인 메뉴 콜백 처리"""
        keyboard = self.response_builder.create_main_menu_keyboard()
        message_data = {
            'text': '🏠 *메인 메뉴*\n\n원하는 기능을 선택하세요.',
            'parse_mode': 'Markdown',
            'reply_markup': keyboard
        }
        await self.send_message(update, **message_data)
    
    async def _handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     callback_data: str) -> None:
        """알 수 없는 콜백 처리"""
        await self.send_error_message(update, f"알 수 없는 명령입니다: {callback_data}")
    
    # BaseHandler의 추상 메서드 구현 (사용되지 않음)
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args: List[str]) -> None:
        pass
    
    @property
    def command_name(self) -> str:
        return "callback_query"
    
    @property
    def description(self) -> str:
        return "콜백 쿼리 처리"
