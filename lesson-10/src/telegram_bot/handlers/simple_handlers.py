#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 핸들러 구현
python-telegram-bot 20.x 비동기 방식
"""

from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """시작 명령어 핸들러"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    user_name = update.effective_user.first_name or update.effective_user.username or '사용자'
    
    welcome_message = f"""
🚀 *CryptoAutoTrader 봇에 오신 것을 환영합니다!*

안녕하세요, {user_name}님!

이 봇은 암호화폐 자동매매 시스템의 알림 및 제어 기능을 제공합니다.

📊 *주요 기능:*
• 실시간 거래 내역 조회
• 수익률 및 성과 분석
• 시스템 상태 모니터링
• 원격 거래 제어
• 설정 변경

💡 *시작하기:*
아래 버튼을 눌러 기능을 바로 사용하거나,
/help 명령어로 상세 도움말을 확인하세요.

⚠️ *주의사항:*
실제 자금을 사용하기 전에 충분한 테스트를 진행하세요.
"""
    
    # 인라인 키보드
    keyboard = [
        [
            InlineKeyboardButton("📊 거래내역", callback_data="show_trades"),
            InlineKeyboardButton("💰 수익률", callback_data="show_profit")
        ],
        [
            InlineKeyboardButton("🖥️ 상태", callback_data="show_status"),
            InlineKeyboardButton("⚙️ 설정", callback_data="show_settings")
        ],
        [
            InlineKeyboardButton("❓ 도움말", callback_data="show_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """도움말 명령어 핸들러"""
    help_message = """
📚 *CryptoAutoTrader 봇 도움말*

🔹 *기본 명령어:*
• /start - 봇 시작 및 메인 메뉴
• /help - 이 도움말 표시

🔹 *거래 관련 명령어:*
• /trades - 최근 거래 내역 조회
• /profit - 수익률 및 성과 분석
• /status - 시스템 상태 확인

🔹 *거래 제어 명령어:*
• /start_trading - 자동매매 시작
• /stop 또는 /stop_trading - 자동매매 중지

🔹 *설정 명령어:*
• /settings - 시스템 설정 메뉴

💡 *사용 팁:*
• 인라인 버튼을 클릭하여 더 쉽게 사용하세요
• 명령어는 대소문자를 구분하지 않습니다
• /start 명령어로 메인 메뉴를 언제든 열 수 있습니다

⚠️ *주의사항:*
• 실제 거래 전 충분한 테스트 필수
• 리스크 관리 설정을 반드시 확인하세요
• API 키는 절대 공유하지 마세요

📞 *지원:*
문제가 발생하면 /status로 시스템 상태를 먼저 확인하세요.
"""
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# status_command는 trading_handlers.py에서 구현됨

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """일반 텍스트 메시지 핸들러"""
    message_text = update.message.text
    
    # 명령어가 아닌 일반 메시지에 대한 응답
    response_message = """
안녕하세요! 👋

도움이 필요하시면 다음 명령어를 사용하세요:

• /start - 봇 시작하기
• /help - 도움말 보기
• /status - 시스템 상태 확인

또는 직접 명령어를 입력해보세요!
"""
    
    await update.message.reply_text(
        response_message,
        parse_mode='Markdown'
    )

# callback_query_handler는 trading_handlers.py에서 구현됨 (handle_trading_callback)