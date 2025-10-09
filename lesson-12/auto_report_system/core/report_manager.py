#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
리포트 관리자
리포트 생성, 포맷 변환, 발송 관리
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import logging
import sys

# 상위 모듈 임포트
sys.path.append(str(Path(__file__).parent.parent))

from generators.html_generator import HTMLReportGenerator
from generators.pdf_generator import PDFReportGenerator
from generators.excel_generator import ExcelReportGenerator
from notifications.telegram_sender import TelegramSender
from notifications.email_sender import EmailSender
from utils.data_collector import DataCollector
from utils.insight_engine import InsightEngine

logger = logging.getLogger(__name__)

class ReportManager:
    """리포트 관리 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.report_config = config.get('report', {})
        
        # 생성기 초기화
        self.generators = {}
        
        output_formats = self.report_config.get('output_formats', ['html'])
        
        if 'html' in output_formats:
            self.generators['html'] = HTMLReportGenerator(self.report_config)
        if 'pdf' in output_formats:
            self.generators['pdf'] = PDFReportGenerator(self.report_config)
        if 'excel' in output_formats:
            self.generators['excel'] = ExcelReportGenerator(self.report_config)
        
        # 발송 클라이언트
        self.telegram_sender = None
        self.email_sender = None
        
        if self.report_config.get('send_telegram'):
            self.telegram_sender = TelegramSender(config.get('telegram', {}))
        
        if self.report_config.get('send_email'):
            self.email_sender = EmailSender(config.get('email', {}))
        
        logger.info("리포트 관리자 초기화 완료")
    
    def generate_report(self, report_type: str, data: Dict[str, Any] = None) -> Dict[str, str]:
        """리포트 생성"""
        try:
            # 데이터 수집
            if data is None:
                data = self._collect_data(report_type)
            
            # 분석 수행
            analysis = self._analyze_data(report_type, data)
            
            # 인사이트 생성
            insights = self._generate_insights(report_type, analysis)
            
            # 리포트 데이터 구성
            report_data = {
                'type': report_type,
                'timestamp': datetime.now(),
                'data': data,
                'analysis': analysis,
                'insights': insights
            }
            
            # 포맷별 생성
            generated_files = {}
            for format_type, generator in self.generators.items():
                file_path = generator.generate(report_type, report_data)
                if file_path:
                    generated_files[format_type] = file_path
                    logger.info(f"{format_type.upper()} 리포트 생성: {file_path}")
            
            # 발송
            if generated_files:
                self._send_reports(report_type, generated_files, report_data)
            
            return generated_files
            
        except Exception as e:
            logger.error(f"리포트 생성 오류: {e}", exc_info=True)
            return {}
    
    def generate_alert_report(self, alerts: List[Dict[str, Any]]) -> Dict[str, str]:
        """긴급 알림 리포트 생성"""
        try:
            from utils.insight_engine import InsightEngine
            
            engine = InsightEngine()
            insights = engine.generate_alert_insights(alerts)
            
            report_data = {
                'type': 'alert',
                'timestamp': datetime.now(),
                'alerts': alerts,
                'analysis': {},
                'insights': insights
            }
            
            # HTML만 빠르게 생성
            generated_files = {}
            if 'html' in self.generators:
                html_path = self.generators['html'].generate('alert', report_data)
                if html_path:
                    generated_files['html'] = html_path
            
            # 즉시 발송
            if self.telegram_sender:
                self._send_telegram_alert(alerts)
            
            return generated_files
            
        except Exception as e:
            logger.error(f"알림 리포트 생성 오류: {e}", exc_info=True)
            return {}
    
    def _collect_data(self, report_type: str) -> Dict[str, Any]:
        """데이터 수집"""
        collector = DataCollector()
        
        if report_type == 'daily':
            return collector.collect_daily()
        elif report_type == 'weekly':
            return collector.collect_weekly()
        elif report_type == 'monthly':
            return collector.collect_monthly()
        else:
            return collector.collect_daily()
    
    def _analyze_data(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 분석"""
        analyzer_map = {
            'daily': 'analyzers.daily_analyzer.DailyAnalyzer',
            'weekly': 'analyzers.weekly_analyzer.WeeklyAnalyzer',
            'monthly': 'analyzers.monthly_analyzer.MonthlyAnalyzer'
        }
        
        if report_type in analyzer_map:
            module_path = analyzer_map[report_type]
            module_name, class_name = module_path.rsplit('.', 1)
            
            import importlib
            module = importlib.import_module(module_name)
            analyzer_class = getattr(module, class_name)
            
            analyzer = analyzer_class()
            return analyzer.analyze(data)
        
        return {}
    
    def _generate_insights(self, report_type: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """인사이트 생성"""
        engine = InsightEngine()
        return engine.generate_insights(report_type, analysis)
    
    def _send_reports(self, report_type: str, files: Dict[str, str], data: Dict[str, Any]):
        """리포트 발송"""
        try:
            # 텔레그램 발송
            if self.telegram_sender:
                summary = self._create_summary(report_type, data)
                self.telegram_sender.send_report_notification(
                    report_type, summary, files.get('html')
                )
            
            # 이메일 발송
            if self.email_sender:
                recipients = self.report_config.get('recipients', [])
                if recipients:
                    self.email_sender.send_report(
                        report_type, recipients, files, data
                    )
                    
        except Exception as e:
            logger.error(f"리포트 발송 오류: {e}", exc_info=True)
    
    def _send_telegram_alert(self, alerts: List[Dict[str, Any]]):
        """텔레그램 긴급 알림"""
        message = "🚨 *긴급 알림*\n\n"
        for alert in alerts[:3]:  # 최대 3개
            message += f"⚠️ {alert.get('title', '알림')}\n"
            message += f"   {alert.get('description', '')}\n\n"
        
        self.telegram_sender.send_message(message)
    
    def _create_summary(self, report_type: str, data: Dict[str, Any]) -> str:
        """요약 생성"""
        analysis = data.get('analysis', {})
        
        if report_type == 'daily':
            return f"""
📊 일간 리포트
- 수익률: {analysis.get('total_return', 0):.2f}%
- 거래 수: {analysis.get('total_trades', 0)}건
- 승률: {analysis.get('win_rate', 0):.1f}%
"""
        elif report_type == 'weekly':
            return f"""
📈 주간 리포트
- 주간 수익률: {analysis.get('total_return', 0):.2f}%
- 총 거래: {analysis.get('total_trades', 0)}건
- 샤프 비율: {analysis.get('sharpe_ratio', 0):.2f}
"""
        elif report_type == 'monthly':
            return f"""
📅 월간 리포트
- 월간 수익률: {analysis.get('total_return', 0):.2f}%
- 연환산 수익률: {analysis.get('annualized_return', 0):.2f}%
- MDD: {analysis.get('max_drawdown', 0):.2f}%
"""
        
        return "리포트가 생성되었습니다."

