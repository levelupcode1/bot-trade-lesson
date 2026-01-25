#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메시지 템플릿 모듈
응답 메시지 포맷팅
"""

from typing import Dict, Any
from datetime import datetime


class WelcomeTemplate:
    """환영 메시지 템플릿"""
    
    @staticmethod
    def format(data: Dict[str, Any]) -> str:
        """
        환영 메시지 포맷팅
        
        Args:
            data: 메시지 데이터 (user_name 포함)
        
        Returns:
            포맷팅된 메시지 문자열
        """
        user_name = data.get('user_name', '사용자')
        
        message = f"""🚀 *자동매매 모니터링 봇에 오신 것을 환영합니다!*

안녕하세요, {user_name}님!

이 봇은 암호화폐 자동매매 시스템의 모니터링 및 제어를 담당합니다.

📊 *주요 기능:*
• /status - 시스템 상태 확인
• /profit - 수익률 조회
• /start_trading - 자동매매 시작
• /stop_trading - 자동매매 중지

💡 *시작하기:*
명령어를 입력하거나 /help로 도움말을 확인하세요.

⚠️ *주의사항:*
실제 자금을 사용하기 전에 충분한 테스트를 진행하세요.
"""
        return message


class StatusTemplate:
    """상태 메시지 템플릿"""
    
    @staticmethod
    def format(data: Dict[str, Any]) -> str:
        """
        상태 메시지 포맷팅
        
        Args:
            data: 상태 데이터
        
        Returns:
            포맷팅된 메시지 문자열
        """
        trading_status = data.get('trading_status', 'unknown')
        initial_capital = data.get('initial_capital', 0.0)
        current_capital = data.get('current_capital', 0.0)
        total_profit = data.get('total_profit', 0.0)
        total_trades = data.get('total_trades', 0)
        winning_trades = data.get('winning_trades', 0)
        win_rate = data.get('win_rate', 0.0)
        
        # 상태 이모지
        status_emoji = "🟢" if trading_status == 'running' else "🔴"
        status_text = "실행 중" if trading_status == 'running' else "중지됨"
        
        message = f"""📊 *시스템 상태*

**거래 상태**: {status_emoji} {status_text}

💰 *자본 정보:*
• 초기 자본: {initial_capital:,.0f}원
• 현재 자본: {current_capital:,.0f}원
• 총 손익: {total_profit:+,.0f}원

📈 *거래 통계:*
• 총 거래 수: {total_trades}건
• 수익 거래: {winning_trades}건
• 승률: {win_rate:.1f}%

━━━━━━━━━━━━━━━━━━━━
마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message


class ProfitTemplate:
    """수익률 메시지 템플릿"""
    
    @staticmethod
    def format(data: Dict[str, Any]) -> str:
        """
        수익률 메시지 포맷팅
        
        Args:
            data: 수익 정보 데이터
        
        Returns:
            포맷팅된 메시지 문자열
        """
        initial_capital = data.get('initial_capital', 0.0)
        current_capital = data.get('current_capital', 0.0)
        total_profit = data.get('total_profit', 0.0)
        total_return = data.get('total_return', 0.0)
        total_trades = data.get('total_trades', 0)
        winning_trades = data.get('winning_trades', 0)
        losing_trades = data.get('losing_trades', 0)
        win_rate = data.get('win_rate', 0.0)
        
        # 수익률 이모지
        profit_emoji = "📈" if total_return >= 0 else "📉"
        
        message = f"""💰 *수익률 분석*

{profit_emoji} *총 수익률: {total_return:+.2f}%*

💵 *자본 현황:*
• 초기 자본: {initial_capital:,.0f}원
• 현재 자본: {current_capital:,.0f}원
• 총 손익: {total_profit:+,.0f}원

📊 *거래 통계:*
• 총 거래: {total_trades}건
• 수익 거래: {winning_trades}건
• 손실 거래: {losing_trades}건
• 승률: {win_rate:.1f}%

━━━━━━━━━━━━━━━━━━━━
업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message


class TradingControlTemplate:
    """거래 제어 메시지 템플릿"""
    
    @staticmethod
    def format(action: str, success: bool, message: str = "") -> str:
        """
        거래 제어 메시지 포맷팅
        
        Args:
            action: 동작 ('start' 또는 'stop')
            success: 성공 여부
            message: 추가 메시지
        
        Returns:
            포맷팅된 메시지 문자열
        """
        if action == 'start':
            if success:
                emoji = "✅"
                status_text = "자동매매가 시작되었습니다!"
            else:
                emoji = "⚠️"
                status_text = "자동매매 시작 실패"
        else:  # stop
            if success:
                emoji = "🛑"
                status_text = "자동매매가 중지되었습니다!"
            else:
                emoji = "⚠️"
                status_text = "자동매매 중지 실패"
        
        result = f"""{emoji} *{status_text}*

{message if message else ''}

━━━━━━━━━━━━━━━━━━━━
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return result
