#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주간 리포트 템플릿
"""

from .base_template import BaseReportTemplate

class WeeklyReportTemplate(BaseReportTemplate):
    """주간 리포트 템플릿"""
    
    def get_title(self) -> str:
        return "📈 주간 성과 리포트"
    
    def get_sections(self) -> list:
        return [
            {
                'id': 'summary',
                'title': '주간 요약',
                'metrics': ['total_return', 'total_trades', 'win_rate', 'sharpe_ratio']
            },
            {
                'id': 'daily_analysis',
                'title': '일별 분석',
                'metrics': ['daily_returns', 'best_day', 'worst_day']
            },
            {
                'id': 'strategy',
                'title': '전략 평가',
                'metrics': ['strategy_analysis']
            },
            {
                'id': 'risk',
                'title': '리스크 분석',
                'metrics': ['max_drawdown', 'weekly_volatility']
            }
        ]

