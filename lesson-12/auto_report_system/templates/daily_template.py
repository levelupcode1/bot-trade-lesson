#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일간 리포트 템플릿
"""

from .base_template import BaseReportTemplate

class DailyReportTemplate(BaseReportTemplate):
    """일간 리포트 템플릿"""
    
    def get_title(self) -> str:
        return "📊 일간 거래 리포트"
    
    def get_sections(self) -> list:
        return [
            {
                'id': 'summary',
                'title': '요약',
                'metrics': ['daily_return', 'total_trades', 'win_rate', 'today_pnl']
            },
            {
                'id': 'trading',
                'title': '거래 활동',
                'metrics': ['active_hours', 'symbol_breakdown']
            },
            {
                'id': 'performance',
                'title': '성과 지표',
                'metrics': ['profit_factor', 'max_drawdown']
            }
        ]

