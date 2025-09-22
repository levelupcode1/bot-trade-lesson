#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기본 템플릿 클래스
모든 메시지 템플릿의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import re

class MessageTemplate(ABC):
    """메시지 템플릿 추상 클래스"""
    
    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        """
        메시지 포맷팅
        
        Args:
            data: 포맷팅할 데이터
            
        Returns:
            포맷팅된 메시지
        """
        pass
    
    def _format_timestamp(self, timestamp: Optional[datetime] = None, 
                         format_str: str = "%Y-%m-%d %H:%M:%S KST") -> str:
        """
        타임스탬프 포맷팅
        
        Args:
            timestamp: 타임스탬프 (None이면 현재 시간)
            format_str: 포맷 문자열
            
        Returns:
            포맷팅된 타임스탬프
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if isinstance(timestamp, str):
            # ISO 형식 문자열인 경우 파싱
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return timestamp
        
        return timestamp.strftime(format_str)
    
    def _format_number(self, number: Any, decimal_places: int = 2, 
                      use_separator: bool = True) -> str:
        """
        숫자 포맷팅
        
        Args:
            number: 포맷팅할 숫자
            decimal_places: 소수점 자릿수
            use_separator: 천 단위 구분자 사용 여부
            
        Returns:
            포맷팅된 숫자 문자열
        """
        try:
            num = float(number)
            if use_separator:
                return f"{num:,.{decimal_places}f}"
            else:
                return f"{num:.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(number)
    
    def _format_percentage(self, number: Any, decimal_places: int = 2) -> str:
        """
        백분율 포맷팅
        
        Args:
            number: 포맷팅할 숫자
            decimal_places: 소수점 자릿수
            
        Returns:
            포맷팅된 백분율 문자열
        """
        try:
            num = float(number)
            return f"{num:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return f"{number}%"
    
    def _escape_markdown(self, text: str) -> str:
        """
        Markdown 특수문자 이스케이프
        
        Args:
            text: 이스케이프할 텍스트
            
        Returns:
            이스케이프된 텍스트
        """
        # Markdown 특수문자
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _truncate_text(self, text: str, max_length: int = 100, 
                      suffix: str = "...") -> str:
        """
        텍스트 자르기
        
        Args:
            text: 자를 텍스트
            max_length: 최대 길이
            suffix: 접미사
            
        Returns:
            잘린 텍스트
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    def _format_currency(self, amount: Any, currency: str = "KRW", 
                        decimal_places: int = 0) -> str:
        """
        통화 포맷팅
        
        Args:
            amount: 금액
            currency: 통화 코드
            decimal_places: 소수점 자릿수
            
        Returns:
            포맷팅된 통화 문자열
        """
        try:
            num = float(amount)
            
            if currency == "KRW":
                return f"{num:,.{decimal_places}f}원"
            elif currency == "USD":
                return f"${num:,.{decimal_places}f}"
            elif currency == "BTC":
                return f"{num:.{decimal_places}f} BTC"
            else:
                return f"{num:,.{decimal_places}f} {currency}"
                
        except (ValueError, TypeError):
            return f"{amount} {currency}"
    
    def _get_status_emoji(self, status: str) -> str:
        """
        상태에 따른 이모지 반환
        
        Args:
            status: 상태 문자열
            
        Returns:
            해당하는 이모지
        """
        status_emojis = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'running': '🔄',
            'stopped': '⏹️',
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'active': '🟢',
            'inactive': '🔴',
            'buy': '🟢',
            'sell': '🔴',
            'profit': '📈',
            'loss': '📉'
        }
        
        return status_emojis.get(status.lower(), '📌')
    
    def _format_table(self, data: list, headers: list = None, 
                     max_width: int = 30) -> str:
        """
        테이블 형태로 포맷팅
        
        Args:
            data: 테이블 데이터 (리스트의 리스트)
            headers: 헤더 리스트
            max_width: 최대 열 너비
            
        Returns:
            포맷팅된 테이블 문자열
        """
        if not data:
            return "데이터가 없습니다."
        
        # 헤더가 있으면 추가
        if headers:
            data = [headers] + data
        
        # 각 열의 최대 너비 계산
        col_widths = []
        for col_idx in range(len(data[0])):
            max_width_col = max(
                len(str(row[col_idx])) for row in data
                if col_idx < len(row)
            )
            col_widths.append(min(max_width_col, max_width))
        
        # 테이블 생성
        lines = []
        for row_idx, row in enumerate(data):
            formatted_row = []
            for col_idx, cell in enumerate(row):
                if col_idx < len(col_widths):
                    cell_str = str(cell)
                    if len(cell_str) > col_widths[col_idx]:
                        cell_str = cell_str[:col_widths[col_idx] - 3] + "..."
                    formatted_row.append(cell_str.ljust(col_widths[col_idx]))
            
            lines.append(" | ".join(formatted_row))
            
            # 헤더 아래에 구분선 추가
            if headers and row_idx == 0:
                separator = "-+-".join("-" * width for width in col_widths)
                lines.append(separator)
        
        return "\n".join(lines)

class ErrorTemplate(MessageTemplate):
    """오류 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """오류 메시지 포맷팅"""
        error_type = data.get('error_type', 'Unknown')
        message = data.get('message', '알 수 없는 오류가 발생했습니다.')
        timestamp = data.get('timestamp')
        
        emoji = self._get_status_emoji('error')
        
        text = f"{emoji} *오류 발생*\n\n"
        text += f"**오류 유형**: `{error_type}`\n"
        text += f"**메시지**: {message}\n"
        
        if timestamp:
            text += f"**시간**: `{self._format_timestamp(timestamp)}`\n"
        
        return text

class SuccessTemplate(MessageTemplate):
    """성공 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """성공 메시지 포맷팅"""
        operation = data.get('operation', '작업')
        message = data.get('message', '성공적으로 완료되었습니다.')
        timestamp = data.get('timestamp')
        
        emoji = self._get_status_emoji('success')
        
        text = f"{emoji} *{operation} 완료*\n\n"
        text += f"{message}\n"
        
        if timestamp:
            text += f"**시간**: `{self._format_timestamp(timestamp)}`\n"
        
        return text

class InfoTemplate(MessageTemplate):
    """정보 메시지 템플릿"""
    
    def format(self, data: Dict[str, Any]) -> str:
        """정보 메시지 포맷팅"""
        title = data.get('title', '정보')
        message = data.get('message', '')
        timestamp = data.get('timestamp')
        
        emoji = self._get_status_emoji('info')
        
        text = f"{emoji} *{title}*\n\n"
        text += f"{message}\n"
        
        if timestamp:
            text += f"**시간**: `{self._format_timestamp(timestamp)}`\n"
        
        return text
