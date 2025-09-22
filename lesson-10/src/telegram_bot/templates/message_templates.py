#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메시지 템플릿 모듈
다양한 메시지 템플릿 구현
"""

from typing import Dict, Any, List
from datetime import datetime
from .base_template import MessageTemplate

class WelcomeTemplate(MessageTemplate):
    """환영 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """환영 메시지 포맷팅"""
        user_name = data.get('user_name', '사용자')
        bot_name = data.get('bot_name', 'CryptoAutoTrader 봇')
        
        text = f"🎉 *{bot_name}에 오신 것을 환영합니다!*\n\n"
        text += f"안녕하세요, {user_name}님!\n\n"
        text += "이 봇은 암호화폐 자동매매 시스템의 알림과 제어를 담당합니다.\n\n"
        text += "**주요 기능:**\n"
        text += "• 🚀 자동매매 시작/중지\n"
        text += "• 📊 실시간 거래 현황\n"
        text += "• 💰 수익률 모니터링\n"
        text += "• ⚠️ 리스크 알림\n"
        text += "• 📈 성과 분석\n\n"
        text += "도움이 필요하시면 `/help` 명령어를 사용하세요.\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━"
        
        return text

class HelpTemplate(MessageTemplate):
    """도움말 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """도움말 메시지 포맷팅"""
        commands = data.get('commands', [])
        categories = data.get('categories', {})
        
        text = "📖 *명령어 도움말*\n\n"
        
        if categories:
            for category, category_commands in categories.items():
                text += f"**{category}:**\n"
                for command in category_commands:
                    text += f"• `{command['command']}` - {command['description']}\n"
                text += "\n"
        else:
            for command in commands:
                text += f"• `{command['command']}` - {command['description']}\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "💡 **팁**: 인라인 키보드를 사용하면 더 쉽게 명령을 실행할 수 있습니다."
        
        return text

class StatusTemplate(MessageTemplate):
    """상태 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """상태 메시지 포맷팅"""
        system_status = data.get('system_status', 'unknown')
        trading_status = data.get('trading_status', 'unknown')
        uptime = data.get('uptime', 'N/A')
        last_update = data.get('last_update')
        
        # 상태 이모지
        system_emoji = self._get_status_emoji('active' if system_status == 'running' else 'inactive')
        trading_emoji = self._get_status_emoji('active' if trading_status == 'running' else 'inactive')
        
        text = f"📊 *시스템 상태*\n\n"
        text += f"**시스템**: {system_emoji} `{system_status}`\n"
        text += f"**거래**: {trading_emoji} `{trading_status}`\n"
        text += f"**가동시간**: `{uptime}`\n"
        
        if last_update:
            text += f"**마지막 업데이트**: `{self._format_timestamp(last_update)}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        return text

class TradeTemplate(MessageTemplate):
    """거래 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """거래 메시지 포맷팅"""
        symbol = data.get('symbol', 'N/A')
        side = data.get('side', 'N/A')
        amount = data.get('amount', 0)
        price = data.get('price', 0)
        total_value = data.get('total_value', 0)
        timestamp = data.get('timestamp')
        strategy = data.get('strategy', 'N/A')
        order_id = data.get('order_id', 'N/A')
        
        # 거래 방향 이모지
        side_emoji = self._get_status_emoji(side.lower())
        
        text = f"{side_emoji} *거래 실행*\n\n"
        text += f"**심볼**: `{symbol}`\n"
        text += f"**액션**: `{side}`\n"
        text += f"**수량**: `{self._format_number(amount, 8)}`\n"
        text += f"**가격**: `{self._format_currency(price)}`\n"
        text += f"**총액**: `{self._format_currency(total_value)}`\n"
        text += f"**전략**: `{strategy}`\n"
        text += f"**주문ID**: `{order_id}`\n"
        
        if timestamp:
            text += f"**시간**: `{self._format_timestamp(timestamp)}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        return text

class PnLTemplate(MessageTemplate):
    """손익 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """손익 메시지 포맷팅"""
        realized_pnl = data.get('realized_pnl', 0)
        unrealized_pnl = data.get('unrealized_pnl', 0)
        total_pnl = data.get('total_pnl', 0)
        total_return = data.get('total_return', 0)
        period = data.get('period', 'N/A')
        strategy = data.get('strategy', 'N/A')
        
        # 손익 이모지
        if total_pnl > 0:
            pnl_emoji = self._get_status_emoji('profit')
        else:
            pnl_emoji = self._get_status_emoji('loss')
        
        text = f"{pnl_emoji} *손익 현황*\n\n"
        text += f"**실현 손익**: `{self._format_currency(realized_pnl, use_separator=True)}`\n"
        text += f"**미실현 손익**: `{self._format_currency(unrealized_pnl, use_separator=True)}`\n"
        text += f"**총 손익**: `{self._format_currency(total_pnl, use_separator=True)}`\n"
        text += f"**총 수익률**: `{self._format_percentage(total_return)}`\n"
        text += f"**기간**: `{period}`\n"
        text += f"**전략**: `{strategy}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        return text

class PositionTemplate(MessageTemplate):
    """포지션 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """포지션 메시지 포맷팅"""
        positions = data.get('positions', [])
        total_value = data.get('total_value', 0)
        total_pnl = data.get('total_pnl', 0)
        
        if not positions:
            return "📊 *포지션 현황*\n\n현재 열린 포지션이 없습니다."
        
        text = f"📊 *포지션 현황*\n\n"
        
        # 포지션 목록
        for i, position in enumerate(positions[:5], 1):  # 최대 5개만 표시
            symbol = position.get('symbol', 'N/A')
            side = position.get('side', 'N/A')
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            pnl = position.get('pnl', 0)
            
            side_emoji = self._get_status_emoji(side.lower())
            pnl_emoji = self._get_status_emoji('profit' if pnl > 0 else 'loss')
            
            text += f"{i}. {side_emoji} `{symbol}`\n"
            text += f"   수량: `{self._format_number(amount, 8)}`\n"
            text += f"   진입가: `{self._format_currency(entry_price)}`\n"
            text += f"   현재가: `{self._format_currency(current_price)}`\n"
            text += f"   손익: {pnl_emoji} `{self._format_currency(pnl)}`\n\n"
        
        if len(positions) > 5:
            text += f"... 및 {len(positions) - 5}개 더\n\n"
        
        # 요약
        text += f"**총 포지션 수**: `{len(positions)}`\n"
        text += f"**총 평가액**: `{self._format_currency(total_value)}`\n"
        text += f"**총 미실현 손익**: `{self._format_currency(total_pnl)}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        return text

class AlertTemplate(MessageTemplate):
    """알림 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """알림 메시지 포맷팅"""
        alert_type = data.get('alert_type', 'info')
        title = data.get('title', '알림')
        message = data.get('message', '')
        timestamp = data.get('timestamp')
        priority = data.get('priority', 'normal')
        
        # 알림 타입별 이모지
        if alert_type == 'trade':
            emoji = '🚀'
        elif alert_type == 'profit':
            emoji = '📈'
        elif alert_type == 'loss':
            emoji = '📉'
        elif alert_type == 'risk':
            emoji = '⚠️'
        elif alert_type == 'error':
            emoji = '❌'
        else:
            emoji = 'ℹ️'
        
        # 우선순위별 강조
        if priority == 'critical':
            text = f"🚨 *{title}* 🚨\n\n"
        else:
            text = f"{emoji} *{title}*\n\n"
        
        text += f"{message}\n"
        
        if timestamp:
            text += f"**시간**: `{self._format_timestamp(timestamp)}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        return text

class ReportTemplate(MessageTemplate):
    """리포트 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """리포트 메시지 포맷팅"""
        report_type = data.get('report_type', 'daily')
        period = data.get('period', 'N/A')
        total_return = data.get('total_return', 0)
        trade_count = data.get('trade_count', 0)
        win_rate = data.get('win_rate', 0)
        max_drawdown = data.get('max_drawdown', 0)
        total_volume = data.get('total_volume', 0)
        top_strategy = data.get('top_strategy', 'N/A')
        
        if report_type == 'daily':
            emoji = '📊'
            title = '일일 거래 리포트'
        elif report_type == 'weekly':
            emoji = '📈'
            title = '주간 거래 리포트'
        elif report_type == 'monthly':
            emoji = '📋'
            title = '월간 거래 리포트'
        else:
            emoji = '📊'
            title = '거래 리포트'
        
        text = f"{emoji} *{title}*\n\n"
        text += f"**기간**: `{period}`\n"
        text += f"**총 수익률**: `{self._format_percentage(total_return)}`\n"
        text += f"**거래 횟수**: `{trade_count}회`\n"
        text += f"**승률**: `{self._format_percentage(win_rate)}`\n"
        text += f"**최대 낙폭**: `{self._format_percentage(max_drawdown)}`\n"
        text += f"**총 거래량**: `{self._format_currency(total_volume)}`\n"
        text += f"**인기 전략**: `{top_strategy}`\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += "*자동매매 시스템이 정상 운영 중입니다* 🤖"
        
        return text
