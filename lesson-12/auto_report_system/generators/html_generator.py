#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 리포트 생성기
"""

from .base_generator import BaseReportGenerator
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HTMLReportGenerator(BaseReportGenerator):
    """HTML 리포트 생성 클래스"""
    
    def generate(self, report_type: str, data: Dict[str, Any]) -> str:
        """HTML 리포트 생성"""
        try:
            filepath = self._get_output_filename(report_type, 'html')
            
            analysis = data.get('analysis', {})
            insights = data.get('insights', [])
            timestamp = data.get('timestamp', datetime.now())
            
            html_content = self._generate_html(report_type, analysis, insights, timestamp)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML 리포트 생성: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"HTML 생성 오류: {e}", exc_info=True)
            return ""
    
    def _generate_html(self, report_type: str, analysis: Dict[str, Any], 
                       insights: list, timestamp: datetime) -> str:
        """HTML 콘텐츠 생성"""
        
        title_map = {
            'daily': '📊 일간 거래 리포트',
            'weekly': '📈 주간 성과 리포트',
            'monthly': '📅 월간 종합 리포트',
            'alert': '🚨 긴급 알림 리포트'
        }
        
        title = title_map.get(report_type, '거래 리포트')
        
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(title, timestamp)}
        {self._generate_summary(analysis)}
        {self._generate_performance(analysis)}
        {self._generate_insights(insights)}
        {self._generate_footer()}
    </div>
</body>
</html>
"""
    
    def _get_css(self) -> str:
        """CSS 스타일"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-top: 10px;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #007bff;
            background-color: #f8f9fa;
        }
        .section h2 {
            color: #333;
            margin-top: 0;
            font-size: 1.8em;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .positive {
            color: #28a745 !important;
        }
        .negative {
            color: #dc3545 !important;
        }
        .neutral {
            color: #6c757d !important;
        }
        .insight-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .insight-box h3 {
            margin-top: 0;
            font-size: 1.3em;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            background-color: #007bff;
            color: white;
            border-radius: 4px;
            font-size: 0.8em;
            margin: 2px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }
        """
    
    def _generate_header(self, title: str, timestamp: datetime) -> str:
        """헤더 생성"""
        time_str = timestamp.strftime("%Y년 %m월 %d일 %H:%M")
        return f"""
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">생성 시간: {time_str}</div>
        </div>
        """
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """요약 섹션"""
        total_return = analysis.get('total_return', 0)
        win_rate = analysis.get('win_rate', 0)
        total_trades = analysis.get('total_trades', 0)
        max_dd = abs(analysis.get('max_drawdown', 0))
        
        return_class = 'positive' if total_return >= 0 else 'negative'
        
        return f"""
        <div class="section">
            <h2>📊 핵심 지표</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value {return_class}">{total_return:.2f}%</div>
                    <div class="metric-label">총 수익률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_trades}</div>
                    <div class="metric-label">총 거래 수</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{win_rate:.1f}%</div>
                    <div class="metric-label">승률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value negative">{max_dd:.2f}%</div>
                    <div class="metric-label">최대 낙폭</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_performance(self, analysis: Dict[str, Any]) -> str:
        """성과 섹션"""
        sharpe = analysis.get('sharpe_ratio', 0)
        sortino = analysis.get('sortino_ratio', 0)
        profit_factor = analysis.get('profit_factor', 0)
        
        return f"""
        <div class="section">
            <h2>📈 성과 분석</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{sharpe:.2f}</div>
                    <div class="metric-label">샤프 비율</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{sortino:.2f}</div>
                    <div class="metric-label">소르티노 비율</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{profit_factor:.2f}</div>
                    <div class="metric-label">프로핏 팩터</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_insights(self, insights: list) -> str:
        """인사이트 섹션"""
        if not insights:
            return ""
        
        insights_html = '<div class="section"><h2>💡 핵심 인사이트</h2>'
        
        for insight in insights[:5]:  # 상위 5개만
            impact_class = {
                'high': 'negative',
                'medium': 'neutral',
                'low': 'positive'
            }.get(insight.get('impact', 'low'), 'neutral')
            
            insights_html += f"""
            <div class="insight-box">
                <h3>{insight.get('title', '인사이트')}</h3>
                <p><strong>설명:</strong> {insight.get('description', '')}</p>
                <p><strong>권장사항:</strong> {insight.get('recommendation', '')}</p>
                <span class="badge {impact_class}">영향도: {insight.get('impact', 'low')}</span>
            </div>
            """
        
        insights_html += '</div>'
        return insights_html
    
    def _generate_footer(self) -> str:
        """푸터 생성"""
        return """
        <div class="footer">
            <p>본 리포트는 자동매매 시스템에 의해 자동 생성되었습니다.</p>
            <p>투자에 참고하시되, 투자 결정은 신중히 하시기 바랍니다.</p>
        </div>
        """

