#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 리포트 생성기
reportlab을 사용한 PDF 생성
"""

from .base_generator import BaseReportGenerator
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFReportGenerator(BaseReportGenerator):
    """PDF 리포트 생성 클래스"""
    
    def generate(self, report_type: str, data: Dict[str, Any]) -> str:
        """PDF 리포트 생성"""
        try:
            # reportlab 라이브러리 확인
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib import colors
                from reportlab.lib.units import inch
            except ImportError:
                logger.warning("reportlab이 설치되지 않았습니다. PDF 생성을 건너뜁니다.")
                return ""
            
            filepath = self._get_output_filename(report_type, 'pdf')
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # 제목
            title_map = {
                'daily': '일간 거래 리포트',
                'weekly': '주간 성과 리포트',
                'monthly': '월간 종합 리포트',
                'alert': '긴급 알림 리포트'
            }
            title = title_map.get(report_type, '거래 리포트')
            
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 0.2*inch))
            
            # 요약 테이블
            analysis = data.get('analysis', {})
            summary_data = [
                ['지표', '값'],
                ['총 수익률', f"{analysis.get('total_return', 0):.2f}%"],
                ['거래 수', str(analysis.get('total_trades', 0))],
                ['승률', f"{analysis.get('win_rate', 0):.1f}%"],
                ['최대 낙폭', f"{analysis.get('max_drawdown', 0):.2f}%"]
            ]
            
            table = Table(summary_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.2*inch))
            
            # 인사이트
            insights = data.get('insights', [])
            if insights:
                story.append(Paragraph('핵심 인사이트', styles['Heading2']))
                for insight in insights[:3]:
                    story.append(Paragraph(
                        f"• {insight.get('title', '')}: {insight.get('description', '')}",
                        styles['Normal']
                    ))
                    story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            
            logger.info(f"PDF 리포트 생성: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"PDF 생성 오류: {e}", exc_info=True)
            return ""

