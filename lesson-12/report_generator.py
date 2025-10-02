#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 리포트 생성 모듈
HTML, PDF, Excel 형태의 종합 분석 리포트 생성
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
from dataclasses import dataclass
import json
import base64
from io import BytesIO

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """리포트 설정 클래스"""
    output_dir: str = "reports/"
    template_dir: str = "templates/"
    chart_dir: str = "charts/"
    include_charts: bool = True
    include_raw_data: bool = False
    format_types: List[str] = None
    
    def __post_init__(self):
        if self.format_types is None:
            self.format_types = ["html", "json"]

class HTMLReportGenerator:
    """HTML 리포트 생성 클래스"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_html_report(self, analysis_data: Dict[str, Any], 
                           charts_info: Dict[str, str] = None) -> str:
        """HTML 리포트 생성"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>자동매매 분석 리포트</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 1.2em;
            margin-top: 10px;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #007bff;
            background-color: #f8f9fa;
        }}
        .section h2 {{
            color: #333;
            margin-top: 0;
            font-size: 1.8em;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .positive {{
            color: #28a745 !important;
        }}
        .negative {{
            color: #dc3545 !important;
        }}
        .neutral {{
            color: #6c757d !important;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .insight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .insight-box h3 {{
            margin-top: 0;
            font-size: 1.3em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            background-color: #007bff;
            color: white;
            border-radius: 4px;
            font-size: 0.8em;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(analysis_data)}
        {self._generate_summary_section(analysis_data)}
        {self._generate_performance_section(analysis_data)}
        {self._generate_risk_section(analysis_data)}
        {self._generate_trading_section(analysis_data)}
        {self._generate_charts_section(charts_info)}
        {self._generate_insights_section(analysis_data)}
        {self._generate_footer()}
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _generate_header(self, analysis_data: Dict[str, Any]) -> str:
        """헤더 섹션 생성"""
        timestamp = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
        
        return f"""
        <div class="header">
            <h1>🚀 자동매매 분석 리포트</h1>
            <div class="subtitle">생성 시간: {timestamp}</div>
        </div>
        """
    
    def _generate_summary_section(self, analysis_data: Dict[str, Any]) -> str:
        """요약 섹션 생성"""
        data_summary = analysis_data.get('data_summary', {})
        performance_metrics = analysis_data.get('performance_metrics', {})
        
        return f"""
        <div class="section">
            <h2>📊 분석 요약</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{data_summary.get('total_observations', 0):,}</div>
                    <div class="metric-label">총 관측일수</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if performance_metrics.get('total_return', 0) >= 0 else 'negative'}">
                        {performance_metrics.get('total_return', 0):.2f}%
                    </div>
                    <div class="metric-label">총 수익률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{performance_metrics.get('win_rate', 0):.1f}%</div>
                    <div class="metric-label">승률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value negative">{performance_metrics.get('max_drawdown', 0):.2f}%</div>
                    <div class="metric-label">최대 낙폭</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_performance_section(self, analysis_data: Dict[str, Any]) -> str:
        """성과 섹션 생성"""
        metrics = analysis_data.get('performance_metrics', {})
        
        return f"""
        <div class="section">
            <h2>📈 성과 지표</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value {'positive' if metrics.get('total_return', 0) >= 0 else 'negative'}">
                        {metrics.get('total_return', 0):.2f}%
                    </div>
                    <div class="metric-label">총 수익률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if metrics.get('annualized_return', 0) >= 0 else 'negative'}">
                        {metrics.get('annualized_return', 0):.2f}%
                    </div>
                    <div class="metric-label">연환산 수익률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('sharpe_ratio', 0):.2f}</div>
                    <div class="metric-label">샤프 비율</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('sortino_ratio', 0):.2f}</div>
                    <div class="metric-label">소르티노 비율</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_risk_section(self, analysis_data: Dict[str, Any]) -> str:
        """리스크 섹션 생성"""
        metrics = analysis_data.get('performance_metrics', {})
        
        return f"""
        <div class="section">
            <h2>⚠️ 리스크 지표</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value negative">{metrics.get('max_drawdown', 0):.2f}%</div>
                    <div class="metric-label">최대 낙폭 (MDD)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('var_95', 0):.2f}</div>
                    <div class="metric-label">VaR (95%)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('cvar_95', 0):.2f}</div>
                    <div class="metric-label">CVaR (95%)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('calmar_ratio', 0):.2f}</div>
                    <div class="metric-label">칼마 비율</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_trading_section(self, analysis_data: Dict[str, Any]) -> str:
        """거래 섹션 생성"""
        metrics = analysis_data.get('performance_metrics', {})
        symbol_analysis = analysis_data.get('symbol_analysis', {})
        
        symbol_table = ""
        if symbol_analysis:
            symbol_table = "<h3>코인별 성과</h3><div class='table-container'><table><tr><th>코인</th><th>수익률</th><th>승률</th><th>거래수</th></tr>"
            for symbol, data in symbol_analysis.items():
                symbol_table += f"""
                <tr>
                    <td><span class="badge">{symbol}</span></td>
                    <td class="{'positive' if data.get('total_return', 0) >= 0 else 'negative'}">
                        {data.get('total_return', 0):.2f}%
                    </td>
                    <td>{data.get('win_rate', 0):.1f}%</td>
                    <td>{data.get('total_trades', 0)}</td>
                </tr>
                """
            symbol_table += "</table></div>"
        
        return f"""
        <div class="section">
            <h2>💰 거래 분석</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('total_trades', 0)}</div>
                    <div class="metric-label">총 거래 수</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('winning_trades', 0)}</div>
                    <div class="metric-label">수익 거래</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('profit_factor', 0):.2f}</div>
                    <div class="metric-label">프로핏 팩터</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.get('avg_holding_period', 0):.0f}분</div>
                    <div class="metric-label">평균 보유기간</div>
                </div>
            </div>
            {symbol_table}
        </div>
        """
    
    def _generate_charts_section(self, charts_info: Dict[str, str] = None) -> str:
        """차트 섹션 생성"""
        if not charts_info:
            return ""
        
        charts_html = "<div class='section'><h2>📊 시각화</h2>"
        
        for chart_name, chart_path in charts_info.items():
            charts_html += f"""
            <div class="chart-container">
                <h3>{chart_name}</h3>
                <img src="{chart_path}" alt="{chart_name}">
            </div>
            """
        
        charts_html += "</div>"
        return charts_html
    
    def _generate_insights_section(self, analysis_data: Dict[str, Any]) -> str:
        """인사이트 섹션 생성"""
        insights = analysis_data.get('insights', [])
        
        if not insights:
            return ""
        
        insights_html = "<div class='section'><h2>💡 핵심 인사이트</h2>"
        
        for insight in insights:
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
        
        insights_html += "</div>"
        return insights_html
    
    def _generate_footer(self) -> str:
        """푸터 생성"""
        return f"""
        <div class="footer">
            <p>본 리포트는 자동매매 시스템에 의해 생성되었습니다.</p>
            <p>투자에 참고하시되, 투자 결정은 신중히 하시기 바랍니다.</p>
        </div>
        """

class ReportGenerator:
    """종합 리포트 생성 클래스"""
    
    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()
        self.logger = logging.getLogger(__name__)
        
        # 출력 디렉토리 생성
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(self, analysis_data: Dict[str, Any],
                                    charts_info: Dict[str, str] = None) -> Dict[str, str]:
        """종합 리포트 생성"""
        results = {}
        
        try:
            # HTML 리포트 생성
            if "html" in self.config.format_types:
                html_generator = HTMLReportGenerator(self.config)
                html_content = html_generator.generate_html_report(analysis_data, charts_info)
                
                html_path = Path(self.config.output_dir) / f"trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                results['html'] = str(html_path)
                self.logger.info(f"HTML 리포트 생성: {html_path}")
            
            # JSON 리포트 생성
            if "json" in self.config.format_types:
                json_path = Path(self.config.output_dir) / f"trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
                
                results['json'] = str(json_path)
                self.logger.info(f"JSON 리포트 생성: {json_path}")
            
            # CSV 리포트 생성 (선택사항)
            if "csv" in self.config.format_types and self.config.include_raw_data:
                csv_path = Path(self.config.output_dir) / f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                # 거래 데이터를 CSV로 저장
                if 'trades_data' in analysis_data:
                    trades_df = pd.DataFrame(analysis_data['trades_data'])
                    trades_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    results['csv'] = str(csv_path)
            
            self.logger.info("종합 리포트 생성 완료")
            
        except Exception as e:
            self.logger.error(f"리포트 생성 오류: {e}")
            results['error'] = str(e)
        
        return results
    
    def generate_summary_report(self, analysis_data: Dict[str, Any]) -> str:
        """요약 리포트 생성 (텍스트 형태)"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            performance = analysis_data.get('performance_metrics', {})
            data_summary = analysis_data.get('data_summary', {})
            
            summary = f"""
=== 자동매매 분석 요약 리포트 ===
생성 시간: {timestamp}

📊 핵심 지표
- 총 수익률: {performance.get('total_return', 0):.2f}%
- 승률: {performance.get('win_rate', 0):.1f}%
- 최대 낙폭: {performance.get('max_drawdown', 0):.2f}%
- 샤프 비율: {performance.get('sharpe_ratio', 0):.2f}
- 총 거래 수: {performance.get('total_trades', 0)}건

⚠️ 리스크 지표
- VaR (95%): {performance.get('var_95', 0):.4f}
- CVaR (95%): {performance.get('cvar_95', 0):.4f}
- 평균 일일 수익률: {data_summary.get('mean', 0):.4f}%
- 일일 수익률 변동성: {data_summary.get('std', 0):.4f}%

📈 거래 분석
- 수익 거래: {performance.get('winning_trades', 0)}건
- 손실 거래: {performance.get('losing_trades', 0)}건
- 프로핏 팩터: {performance.get('profit_factor', 0):.2f}
- 평균 보유 기간: {performance.get('avg_holding_period', 0):.0f}분

💡 주요 인사이트
"""
            
            insights = analysis_data.get('insights', [])
            for i, insight in enumerate(insights[:3], 1):  # 상위 3개만
                summary += f"{i}. {insight.get('title', '인사이트')}: {insight.get('description', '')}\n"
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"요약 리포트 생성 오류: {e}")
            return f"리포트 생성 중 오류 발생: {e}"

# 사용 예시
if __name__ == "__main__":
    from data_processor import TradingDataProcessor, DataConfig
    from performance_metrics import PerformanceAnalyzer
    from statistical_analysis import StatisticalAnalyzer
    
    # 설정 및 데이터 로드
    config = DataConfig()
    processor = TradingDataProcessor(config)
    
    trades = processor.load_trade_data()
    account = processor.load_account_history()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data(trades)
        processed_account = processor.preprocess_account_data(account)
        
        # 분석 수행
        perf_analyzer = PerformanceAnalyzer()
        stats_analyzer = StatisticalAnalyzer()
        
        performance_metrics = perf_analyzer.calculate_comprehensive_metrics(processed_trades, processed_account)
        stats_results = stats_analyzer.comprehensive_analysis(processed_trades, processed_account)
        
        # 분석 데이터 통합
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': performance_metrics.__dict__,
            'data_summary': stats_results.get('data_summary', {}),
            'symbol_analysis': perf_analyzer.analyze_by_symbol(processed_trades, processed_account),
            'insights': [
                {
                    'title': '수익률 분석',
                    'description': f"총 수익률이 {performance_metrics.total_return:.2f}%로 {'양호' if performance_metrics.total_return > 0 else '부진'}한 성과를 보입니다.",
                    'recommendation': '전략 최적화를 통해 수익률 개선이 필요합니다.' if performance_metrics.total_return <= 0 else '현재 전략을 유지하되 리스크 관리를 강화하세요.',
                    'impact': 'high' if abs(performance_metrics.total_return) > 10 else 'medium'
                }
            ]
        }
        
        # 리포트 생성
        report_config = ReportConfig(
            output_dir="reports/",
            format_types=["html", "json"]
        )
        
        report_generator = ReportGenerator(report_config)
        results = report_generator.generate_comprehensive_report(analysis_data)
        
        # 요약 리포트 생성
        summary = report_generator.generate_summary_report(analysis_data)
        print(summary)
        
        print(f"\n리포트가 생성되었습니다:")
        for format_type, path in results.items():
            print(f"- {format_type.upper()}: {path}")
    else:
        print("리포트 생성할 데이터가 없습니다.")

