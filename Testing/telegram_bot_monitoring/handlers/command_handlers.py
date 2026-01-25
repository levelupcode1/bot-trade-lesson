#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
명령어 핸들러 모듈
텔레그램 봇 명령어 처리
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.config_manager import ConfigManager
    from ..templates.message_templates import (
        WelcomeTemplate,
        StatusTemplate,
        ProfitTemplate,
        TradingControlTemplate
    )

logger = logging.getLogger(__name__)

# 전역 설정 관리자 (실제 구현에서는 의존성 주입 사용)
_config_manager = None
_templates = None


def initialize_handlers(config_manager, templates):
    """핸들러 초기화 (설정 관리자 및 템플릿 주입)"""
    global _config_manager, _templates
    _config_manager = config_manager
    _templates = templates
    logger.info("명령어 핸들러 초기화 완료")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start 명령어 핸들러
    
    봇 시작 및 환영 메시지 표시
    """
    try:
        user = update.effective_user
        user_name = user.first_name or user.username or '사용자'
        
        # 템플릿을 사용하여 메시지 포맷팅
        message = _templates['welcome'].format({
            'user_name': user_name
        })
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"/start 명령어 실행: {user_name} (ID: {user.id})")
        
    except Exception as e:
        logger.error(f"/start 명령어 처리 오류: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ 명령어 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /status 명령어 핸들러
    
    시스템 상태 조회
    """
    try:
        # 설정 관리자에서 상태 정보 가져오기
        status_data = _config_manager.get_status()
        
        # 템플릿을 사용하여 메시지 포맷팅
        message = _templates['status'].format(status_data)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"/status 명령어 실행: 사용자 ID {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"/status 명령어 처리 오류: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ 상태 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /profit 명령어 핸들러
    
    수익률 정보 조회
    """
    try:
        # 설정 관리자에서 수익 정보 가져오기
        profit_data = _config_manager.get_profit_info()
        
        # 템플릿을 사용하여 메시지 포맷팅
        message = _templates['profit'].format(profit_data)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"/profit 명령어 실행: 사용자 ID {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"/profit 명령어 처리 오류: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ 수익률 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


async def start_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start_trading 명령어 핸들러
    
    자동매매 시작
    """
    try:
        # 거래 시스템 시작
        success = _config_manager.start_trading()
        
        # 템플릿을 사용하여 메시지 포맷팅
        message = _templates['trading_control'].format(
            action='start',
            success=success,
            message="거래 시스템이 활성화되었습니다." if success else "거래 시스템이 이미 실행 중이거나 시작할 수 없습니다."
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"/start_trading 명령어 실행: 사용자 ID {update.effective_user.id}, 성공: {success}")
        
    except Exception as e:
        logger.error(f"/start_trading 명령어 처리 오류: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ 거래 시작 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


async def stop_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /stop_trading 명령어 핸들러
    
    자동매매 중지
    """
    try:
        # 거래 시스템 중지
        success = _config_manager.stop_trading()
        
        # 템플릿을 사용하여 메시지 포맷팅
        message = _templates['trading_control'].format(
            action='stop',
            success=success,
            message="거래 시스템이 중지되었습니다." if success else "거래 시스템이 이미 중지되어 있거나 중지할 수 없습니다."
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"/stop_trading 명령어 실행: 사용자 ID {update.effective_user.id}, 성공: {success}")
        
    except Exception as e:
        logger.error(f"/stop_trading 명령어 처리 오류: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ 거래 중지 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
