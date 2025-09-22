#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기본 핸들러 클래스
모든 명령어 핸들러의 기본 클래스
"""

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..templates.response_builder import ResponseBuilder
from ..utils.logger import get_logger

class BaseHandler(ABC):
    """기본 핸들러 추상 클래스"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.response_builder = ResponseBuilder()
    
    @abstractmethod
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args: List[str]) -> None:
        """
        명령어 실행
        
        Args:
            update: 텔레그램 업데이트 객체
            context: 컨텍스트 객체
            args: 명령어 인자
        """
        pass
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """명령어 이름"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """명령어 설명"""
        pass
    
    @property
    def required_permission(self) -> str:
        """필요 권한 (기본: user)"""
        return "user"
    
    async def send_message(self, update: Update, text: str, 
                          keyboard: Optional[InlineKeyboardMarkup] = None,
                          parse_mode: str = "Markdown") -> None:
        """
        메시지 전송
        
        Args:
            update: 텔레그램 업데이트 객체
            text: 전송할 텍스트
            keyboard: 인라인 키보드 (선택사항)
            parse_mode: 파싱 모드
        """
        try:
            message_params = {
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            if keyboard:
                message_params['reply_markup'] = keyboard
            
            await update.message.reply_text(**message_params)
            
            # 로깅
            self.logger.log_user_action(
                user_id=update.effective_user.id,
                action=f"command_{self.command_name}",
                chat_id=update.effective_chat.id,
                message_length=len(text)
            )
            
        except Exception as e:
            self.logger.error(f"메시지 전송 오류: {e}")
            await self.send_error_message(update, "메시지 전송 중 오류가 발생했습니다.")
    
    async def send_error_message(self, update: Update, error_message: str) -> None:
        """
        오류 메시지 전송
        
        Args:
            update: 텔레그램 업데이트 객체
            error_message: 오류 메시지
        """
        try:
            error_data = {
                'error_type': 'CommandError',
                'message': error_message,
                'timestamp': datetime.now()
            }
            
            message_data = self.response_builder.build_message('error', error_data)
            await update.message.reply_text(**message_data)
            
        except Exception as e:
            self.logger.error(f"오류 메시지 전송 실패: {e}")
            # 최후의 수단으로 간단한 텍스트 전송
            try:
                await update.message.reply_text("❌ 오류가 발생했습니다.")
            except:
                pass
    
    async def send_success_message(self, update: Update, message: str) -> None:
        """
        성공 메시지 전송
        
        Args:
            update: 텔레그램 업데이트 객체
            message: 성공 메시지
        """
        try:
            success_data = {
                'operation': self.command_name,
                'message': message,
                'timestamp': datetime.now()
            }
            
            message_data = self.response_builder.build_message('success', success_data)
            await update.message.reply_text(**message_data)
            
        except Exception as e:
            self.logger.error(f"성공 메시지 전송 오류: {e}")
            await self.send_error_message(update, "메시지 전송 중 오류가 발생했습니다.")
    
    async def send_info_message(self, update: Update, title: str, message: str) -> None:
        """
        정보 메시지 전송
        
        Args:
            update: 텔레그램 업데이트 객체
            title: 제목
            message: 메시지 내용
        """
        try:
            info_data = {
                'title': title,
                'message': message,
                'timestamp': datetime.now()
            }
            
            message_data = self.response_builder.build_message('info', info_data)
            await update.message.reply_text(**message_data)
            
        except Exception as e:
            self.logger.error(f"정보 메시지 전송 오류: {e}")
            await self.send_error_message(update, "메시지 전송 중 오류가 발생했습니다.")
    
    def validate_args(self, args: List[str], expected_count: int, 
                     description: str = "인자") -> bool:
        """
        인자 개수 검증
        
        Args:
            args: 명령어 인자
            expected_count: 예상 인자 개수
            description: 인자 설명
            
        Returns:
            검증 결과
        """
        if len(args) != expected_count:
            self.logger.warning(f"인자 개수 불일치: 예상 {expected_count}, 실제 {len(args)}")
            return False
        return True
    
    def get_user_info(self, update: Update) -> Dict[str, Any]:
        """
        사용자 정보 추출
        
        Args:
            update: 텔레그램 업데이트 객체
            
        Returns:
            사용자 정보 딕셔너리
        """
        user = update.effective_user
        chat = update.effective_chat
        
        return {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'chat_id': chat.id,
            'chat_type': chat.type,
            'is_private': chat.type == 'private'
        }
    
    def log_command_usage(self, update: Update, args: List[str], 
                         success: bool = True, error: Optional[str] = None) -> None:
        """
        명령어 사용 로그
        
        Args:
            update: 텔레그램 업데이트 객체
            args: 명령어 인자
            success: 성공 여부
            error: 오류 메시지 (실패 시)
        """
        user_info = self.get_user_info(update)
        
        log_data = {
            'command': self.command_name,
            'args': args,
            'success': success,
            'user_id': user_info['user_id'],
            'chat_id': user_info['chat_id'],
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
        
        if success:
            self.logger.info(f"명령어 실행 성공: {self.command_name}", **log_data)
        else:
            self.logger.warning(f"명령어 실행 실패: {self.command_name}", **log_data)
    
    async def handle_permission_error(self, update: Update) -> None:
        """
        권한 오류 처리
        
        Args:
            update: 텔레그램 업데이트 객체
        """
        await self.send_error_message(
            update, 
            f"명령어 `/{self.command_name}`을 실행할 권한이 없습니다."
        )
        
        self.log_command_usage(update, [], success=False, error="Permission denied")
    
    async def handle_validation_error(self, update: Update, error_message: str) -> None:
        """
        검증 오류 처리
        
        Args:
            update: 텔레그램 업데이트 객체
            error_message: 오류 메시지
        """
        await self.send_error_message(update, error_message)
        
        self.log_command_usage(update, [], success=False, error=f"Validation error: {error_message}")
    
    async def handle_execution_error(self, update: Update, error: Exception) -> None:
        """
        실행 오류 처리
        
        Args:
            update: 텔레그램 업데이트 객체
            error: 예외 객체
        """
        error_message = f"명령어 실행 중 오류가 발생했습니다: {str(error)}"
        await self.send_error_message(update, error_message)
        
        self.log_command_usage(update, [], success=False, error=str(error))
        self.logger.log_exception(f"명령어 실행 오류: {self.command_name}", error)
