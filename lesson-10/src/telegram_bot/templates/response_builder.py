#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
응답 메시지 빌더
메시지 템플릿과 키보드를 조합하여 응답 메시지 생성
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional, Any
import logging

from .message_templates import (
    WelcomeTemplate, HelpTemplate, StatusTemplate, TradeTemplate,
    PnLTemplate, PositionTemplate, AlertTemplate, ReportTemplate
)
from .base_template import ErrorTemplate, SuccessTemplate, InfoTemplate

class ResponseBuilder:
    """응답 메시지 빌더 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = {
            'welcome': WelcomeTemplate(),
            'help': HelpTemplate(),
            'status': StatusTemplate(),
            'trade': TradeTemplate(),
            'pnl': PnLTemplate(),
            'position': PositionTemplate(),
            'alert': AlertTemplate(),
            'report': ReportTemplate(),
            'error': ErrorTemplate(),
            'success': SuccessTemplate(),
            'info': InfoTemplate()
        }
    
    def register_template(self, name: str, template) -> None:
        """
        템플릿 등록
        
        Args:
            name: 템플릿 이름
            template: 템플릿 인스턴스
        """
        self.templates[name] = template
        self.logger.info(f"템플릿 등록: {name}")
    
    def build_message(self, template_name: str, data: Dict[str, Any], 
                     keyboard: Optional[InlineKeyboardMarkup] = None) -> Dict[str, Any]:
        """
        메시지 빌드
        
        Args:
            template_name: 템플릿 이름
            data: 템플릿 데이터
            keyboard: 인라인 키보드 (선택사항)
            
        Returns:
            메시지 데이터 딕셔너리
        """
        try:
            if template_name not in self.templates:
                raise ValueError(f"템플릿을 찾을 수 없습니다: {template_name}")
            
            template = self.templates[template_name]
            text = template.format(data)
            
            message_data = {
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            if keyboard:
                message_data['reply_markup'] = keyboard
            
            return message_data
            
        except Exception as e:
            self.logger.error(f"메시지 빌드 오류: {e}")
            return self._build_error_message(str(e))
    
    def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
        """
        인라인 키보드 생성
        
        Args:
            buttons: 버튼 배열 (2차원 리스트)
            
        Returns:
            인라인 키보드 마크업
        """
        keyboard_buttons = []
        
        for row in buttons:
            button_row = []
            for button in row:
                if 'text' in button and 'callback_data' in button:
                    button_row.append(
                        InlineKeyboardButton(
                            text=button['text'],
                            callback_data=button['callback_data']
                        )
                    )
                elif 'text' in button and 'url' in button:
                    button_row.append(
                        InlineKeyboardButton(
                            text=button['text'],
                            url=button['url']
                        )
                    )
            if button_row:
                keyboard_buttons.append(button_row)
        
        return InlineKeyboardMarkup(keyboard_buttons)
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """메인 메뉴 키보드 생성"""
        buttons = [
            [
                {'text': '🚀 거래 시작', 'callback_data': 'start_trading'},
                {'text': '⏹️ 거래 중지', 'callback_data': 'stop_trading'}
            ],
            [
                {'text': '📊 현재 상태', 'callback_data': 'status'},
                {'text': '💰 포지션 현황', 'callback_data': 'positions'}
            ],
            [
                {'text': '📈 수익률 확인', 'callback_data': 'pnl'},
                {'text': '⚙️ 설정 변경', 'callback_data': 'settings'}
            ],
            [
                {'text': '❓ 도움말', 'callback_data': 'help'}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_settings_keyboard(self) -> InlineKeyboardMarkup:
        """설정 키보드 생성"""
        buttons = [
            [
                {'text': '🔔 알림 설정', 'callback_data': 'settings_notifications'},
                {'text': '🎯 전략 설정', 'callback_data': 'settings_strategy'}
            ],
            [
                {'text': '⚠️ 리스크 설정', 'callback_data': 'settings_risk'},
                {'text': '🔒 보안 설정', 'callback_data': 'settings_security'}
            ],
            [
                {'text': '⬅️ 메인 메뉴', 'callback_data': 'main_menu'}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_trading_control_keyboard(self) -> InlineKeyboardMarkup:
        """거래 제어 키보드 생성"""
        buttons = [
            [
                {'text': '▶️ 거래 시작', 'callback_data': 'start_trading'},
                {'text': '⏸️ 일시 중지', 'callback_data': 'pause_trading'}
            ],
            [
                {'text': '⏹️ 거래 중지', 'callback_data': 'stop_trading'},
                {'text': '🔄 상태 새로고침', 'callback_data': 'status'}
            ],
            [
                {'text': '⬅️ 메인 메뉴', 'callback_data': 'main_menu'}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_pagination_keyboard(self, current_page: int, total_pages: int, 
                                 base_callback: str, extra_buttons: List[Dict] = None) -> InlineKeyboardMarkup:
        """
        페이지네이션 키보드 생성
        
        Args:
            current_page: 현재 페이지
            total_pages: 전체 페이지 수
            base_callback: 기본 콜백 데이터
            extra_buttons: 추가 버튼들
            
        Returns:
            페이지네이션 키보드
        """
        buttons = []
        
        # 페이지네이션 버튼
        if total_pages > 1:
            nav_buttons = []
            
            if current_page > 1:
                nav_buttons.append({
                    'text': '⬅️ 이전',
                    'callback_data': f'{base_callback}_page_{current_page - 1}'
                })
            
            nav_buttons.append({
                'text': f'{current_page}/{total_pages}',
                'callback_data': 'current_page'
            })
            
            if current_page < total_pages:
                nav_buttons.append({
                    'text': '다음 ➡️',
                    'callback_data': f'{base_callback}_page_{current_page + 1}'
                })
            
            buttons.append(nav_buttons)
        
        # 추가 버튼들
        if extra_buttons:
            buttons.append(extra_buttons)
        
        # 메인 메뉴 버튼
        buttons.append([{'text': '🏠 메인 메뉴', 'callback_data': 'main_menu'}])
        
        return self.create_inline_keyboard(buttons)
    
    def create_confirmation_keyboard(self, action: str, confirm_callback: str, 
                                   cancel_callback: str = 'main_menu') -> InlineKeyboardMarkup:
        """
        확인 키보드 생성
        
        Args:
            action: 수행할 액션
            confirm_callback: 확인 콜백 데이터
            cancel_callback: 취소 콜백 데이터
            
        Returns:
            확인 키보드
        """
        buttons = [
            [
                {'text': f'✅ {action} 확인', 'callback_data': confirm_callback},
                {'text': '❌ 취소', 'callback_data': cancel_callback}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_notification_settings_keyboard(self, current_settings: Dict[str, bool]) -> InlineKeyboardMarkup:
        """
        알림 설정 키보드 생성
        
        Args:
            current_settings: 현재 알림 설정
            
        Returns:
            알림 설정 키보드
        """
        buttons = []
        
        # 알림 설정 토글 버튼들
        settings = [
            ('trade_execution', '거래 실행 알림'),
            ('pnl_alerts', '수익률 알림'),
            ('risk_warnings', '리스크 경고'),
            ('system_errors', '시스템 오류'),
            ('daily_reports', '일일 리포트')
        ]
        
        for setting_key, setting_name in settings:
            current_value = current_settings.get(setting_key, True)
            toggle_text = '🔔' if current_value else '🔕'
            buttons.append([{
                'text': f'{toggle_text} {setting_name}',
                'callback_data': f'toggle_notification_{setting_key}'
            }])
        
        # 뒤로가기 버튼
        buttons.append([{'text': '⬅️ 설정 메뉴', 'callback_data': 'settings'}])
        
        return self.create_inline_keyboard(buttons)
    
    def create_strategy_selection_keyboard(self, available_strategies: List[Dict]) -> InlineKeyboardMarkup:
        """
        전략 선택 키보드 생성
        
        Args:
            available_strategies: 사용 가능한 전략 목록
            
        Returns:
            전략 선택 키보드
        """
        buttons = []
        
        for strategy in available_strategies:
            strategy_name = strategy.get('name', 'Unknown')
            strategy_id = strategy.get('id', 'unknown')
            is_active = strategy.get('active', False)
            
            status_icon = '✅' if is_active else '⭕'
            buttons.append([{
                'text': f'{status_icon} {strategy_name}',
                'callback_data': f'select_strategy_{strategy_id}'
            }])
        
        # 뒤로가기 버튼
        buttons.append([{'text': '⬅️ 설정 메뉴', 'callback_data': 'settings'}])
        
        return self.create_inline_keyboard(buttons)
    
    def _build_error_message(self, error: str) -> Dict[str, Any]:
        """
        오류 메시지 빌드
        
        Args:
            error: 오류 메시지
            
        Returns:
            오류 메시지 데이터
        """
        return {
            'text': f"❌ *오류가 발생했습니다*\n\n`{error}`\n\n문제가 지속되면 관리자에게 문의하세요.",
            'parse_mode': 'Markdown'
        }
    
    def create_quick_actions_keyboard(self) -> InlineKeyboardMarkup:
        """빠른 액션 키보드 생성"""
        buttons = [
            [
                {'text': '📊 상태', 'callback_data': 'quick_status'},
                {'text': '💰 수익률', 'callback_data': 'quick_pnl'}
            ],
            [
                {'text': '🔄 새로고침', 'callback_data': 'refresh'},
                {'text': '⚙️ 설정', 'callback_data': 'settings'}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_emergency_controls_keyboard(self) -> InlineKeyboardMarkup:
        """긴급 제어 키보드 생성"""
        buttons = [
            [
                {'text': '🚨 긴급 중지', 'callback_data': 'emergency_stop'},
                {'text': '⚠️ 리스크 확인', 'callback_data': 'risk_check'}
            ],
            [
                {'text': '📞 관리자 호출', 'callback_data': 'call_admin'},
                {'text': '📊 시스템 상태', 'callback_data': 'system_status'}
            ]
        ]
        
        return self.create_inline_keyboard(buttons)
