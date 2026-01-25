#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 봇 자동매매 모니터링 시스템 메인 실행 파일
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler

# 모듈 import
from config.config_manager import ConfigManager
from templates.message_templates import (
    WelcomeTemplate,
    StatusTemplate,
    ProfitTemplate,
    TradingControlTemplate
)
from handlers.command_handlers import (
    initialize_handlers,
    start_command,
    status_command,
    profit_command,
    start_trading_command,
    stop_trading_command
)

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    # 봇 토큰 확인
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        logger.error("환경 변수를 설정한 후 다시 실행하세요.")
        return
    
    try:
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        logger.info("설정 관리자 초기화 완료")
        
        # 템플릿 초기화 (정적 메서드이므로 클래스 자체 사용)
        templates = {
            'welcome': WelcomeTemplate,
            'status': StatusTemplate,
            'profit': ProfitTemplate,
            'trading_control': TradingControlTemplate
        }
        logger.info("템플릿 초기화 완료")
        
        # 핸들러 초기화
        initialize_handlers(config_manager, templates)
        logger.info("핸들러 초기화 완료")
        
        # Application 생성
        application = Application.builder().token(bot_token).build()
        logger.info("텔레그램 봇 Application 생성 완료")
        
        # 명령어 핸들러 등록
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("profit", profit_command))
        application.add_handler(CommandHandler("start_trading", start_trading_command))
        application.add_handler(CommandHandler("stop_trading", stop_trading_command))
        logger.info("명령어 핸들러 등록 완료")
        
        # 봇 시작
        logger.info("텔레그램 봇 시작...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
