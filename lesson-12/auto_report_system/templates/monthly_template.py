#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
월간 리포트 템플릿
"""

from .base_template import BaseReportTemplate

class MonthlyReportTemplate(BaseReportTemplate):
    """월간 리포트 템플릿"""
    
    def get_title(self) -> str:
        return "📅 월간 종합 리포트"
    
    def get_sections(self) -> list:
        return [
            {
                'id': 'summary',
                'title': '월간 요약',
                'metrics': ['total_return', 'annualized_return', 'total_trades', 'win_rate']
            },
            {
                'id': 'weekly_analysis',
                'title': '주별 분석',
                'metrics': ['weekly_returns', 'consistency_score']
            },
            {
                'id': 'strategy',
                'title': '전략 비교',
                'metrics': ['strategy_analysis']
            },
            {
                'id': 'symbol',
                'title': '코인별 성과',
                'metrics': ['symbol_analysis']
            },
            {
                'id': 'risk',
                'title': '리스크 지표',
                'metrics': ['max_drawdown', 'sharpe_ratio', 'sortino_ratio', 'calmar_ratio']
            }
        ]

