#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 종합 분석 시스템
모든 분석 모듈을 통합한 메인 분석 클래스
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
from dataclasses import dataclass
import json

# 내부 모듈 import
from data_processor import TradingDataProcessor, DataConfig
from performance_metrics import PerformanceAnalyzer, PerformanceMetrics
from visualization import TradingVisualizer, ChartConfig
from statistical_analysis import StatisticalAnalyzer
from report_generator import ReportGenerator, ReportConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """분석 설정 클래스"""
    # 데이터 설정
    data_config: DataConfig = None
    
    # 차트 설정
    chart_config: ChartConfig = None
    
    # 리포트 설정
    report_config: ReportConfig = None
    
    # 분석 옵션
    enable_visualization: bool = True
    enable_statistical_analysis: bool = True
    enable_performance_analysis: bool = True
    enable_report_generation: bool = True
    
    # 출력 옵션
    save_charts: bool = True
    generate_html_report: bool = True
    generate_json_report: bool = True
    
    def __post_init__(self):
        if self.data_config is None:
            self.data_config = DataConfig()
        if self.chart_config is None:
            self.chart_config = ChartConfig()
        if self.report_config is None:
            self.report_config = ReportConfig()

class TradingAnalyzer:
    """자동매매 종합 분석 클래스"""
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.logger = logging.getLogger(__name__)
        
        # 분석 모듈 초기화
        self.data_processor = TradingDataProcessor(self.config.data_config)
        self.performance_analyzer = PerformanceAnalyzer()
        self.visualizer = TradingVisualizer(self.config.chart_config)
        self.statistical_analyzer = StatisticalAnalyzer()
        self.report_generator = ReportGenerator(self.config.report_config)
        
        # 분석 결과 저장
        self.analysis_results = {}
        self.charts_generated = {}
        
        self.logger.info("자동매매 분석 시스템 초기화 완료")
    
    def run_comprehensive_analysis(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """종합 분석 실행"""
        try:
            self.logger.info("종합 분석 시작")
            
            # 1. 데이터 로드 및 전처리
            self.logger.info("1단계: 데이터 로드 및 전처리")
            raw_trades, raw_account = self._load_and_preprocess_data(start_date, end_date)
            
            if raw_trades.empty or raw_account.empty:
                self.logger.warning("분석할 데이터가 없습니다")
                return {"error": "분석할 데이터가 없습니다"}
            
            # 2. 성과 분석
            if self.config.enable_performance_analysis:
                self.logger.info("2단계: 성과 분석")
                performance_results = self._run_performance_analysis(raw_trades, raw_account)
                self.analysis_results.update(performance_results)
            
            # 3. 통계 분석
            if self.config.enable_statistical_analysis:
                self.logger.info("3단계: 통계 분석")
                statistical_results = self._run_statistical_analysis(raw_trades, raw_account)
                self.analysis_results.update(statistical_results)
            
            # 4. 시각화 생성
            if self.config.enable_visualization:
                self.logger.info("4단계: 시각화 생성")
                visualization_results = self._run_visualization(raw_trades, raw_account)
                self.analysis_results.update(visualization_results)
            
            # 5. 인사이트 도출
            self.logger.info("5단계: 인사이트 도출")
            insights = self._generate_insights()
            self.analysis_results['insights'] = insights
            
            # 6. 리포트 생성
            if self.config.enable_report_generation:
                self.logger.info("6단계: 리포트 생성")
                report_results = self._generate_reports()
                self.analysis_results['reports'] = report_results
            
            self.logger.info("종합 분석 완료")
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"종합 분석 오류: {e}")
            return {"error": str(e)}
    
    def _load_and_preprocess_data(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """데이터 로드 및 전처리"""
        try:
            # 데이터 로드
            trades = self.data_processor.load_trade_data(start_date, end_date)
            account = self.data_processor.load_account_history(start_date, end_date)
            
            if trades.empty or account.empty:
                return trades, account
            
            # 데이터 전처리
            processed_trades = self.data_processor.preprocess_trade_data(trades)
            processed_account = self.data_processor.preprocess_account_data(account)
            
            # 분석 결과에 저장
            self.analysis_results['trades_data'] = processed_trades.to_dict('records')
            self.analysis_results['account_data'] = processed_account.to_dict('records')
            
            return processed_trades, processed_account
            
        except Exception as e:
            self.logger.error(f"데이터 로드 및 전처리 오류: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _run_performance_analysis(self, trades: pd.DataFrame, account: pd.DataFrame) -> Dict[str, Any]:
        """성과 분석 실행"""
        try:
            # 전체 성과 분석
            overall_metrics = self.performance_analyzer.calculate_comprehensive_metrics(trades, account)
            
            # 심볼별 분석
            symbol_analysis = self.performance_analyzer.analyze_by_symbol(trades, account)
            
            # 전략별 분석
            strategy_analysis = self.performance_analyzer.analyze_by_strategy(trades, account)
            
            # 시간대별 분석
            time_analysis = self.performance_analyzer.analyze_by_time_period(trades, account)
            
            return {
                'performance_metrics': overall_metrics.__dict__,
                'symbol_analysis': {k: v.__dict__ for k, v in symbol_analysis.items()},
                'strategy_analysis': {k: v.__dict__ for k, v in strategy_analysis.items()},
                'time_analysis': {k: v.__dict__ for k, v in time_analysis.items()},
                'performance_summary': self.performance_analyzer.generate_performance_report(overall_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"성과 분석 오류: {e}")
            return {}
    
    def _run_statistical_analysis(self, trades: pd.DataFrame, account: pd.DataFrame) -> Dict[str, Any]:
        """통계 분석 실행"""
        try:
            # 종합 통계 분석
            statistical_results = self.statistical_analyzer.comprehensive_analysis(trades, account)
            
            # 통계 리포트 생성
            statistical_report = self.statistical_analyzer.generate_statistical_report(statistical_results)
            
            return {
                'statistical_analysis': statistical_results,
                'statistical_report': statistical_report
            }
            
        except Exception as e:
            self.logger.error(f"통계 분석 오류: {e}")
            return {}
    
    def _run_visualization(self, trades: pd.DataFrame, account: pd.DataFrame) -> Dict[str, Any]:
        """시각화 실행"""
        try:
            charts_info = {}
            
            # 기본 차트들 생성
            if self.config.save_charts:
                # 자산 곡선
                equity_fig = self.visualizer.create_equity_curve(
                    account, save_file="equity_curve"
                )
                if equity_fig:
                    charts_info['equity_curve'] = "charts/equity_curve.png"
                
                # 낙폭 차트
                drawdown_fig = self.visualizer.create_drawdown_chart(
                    account, save_file="drawdown"
                )
                if drawdown_fig:
                    charts_info['drawdown'] = "charts/drawdown.png"
                
                # 거래 분포
                distribution_fig = self.visualizer.create_trade_distribution(
                    trades, save_file="trade_distribution"
                )
                if distribution_fig:
                    charts_info['trade_distribution'] = "charts/trade_distribution.png"
                
                # 일일 수익률 히스토그램
                returns_fig = self.visualizer.create_daily_returns_histogram(
                    account, save_file="daily_returns"
                )
                if returns_fig:
                    charts_info['daily_returns'] = "charts/daily_returns.png"
                
                # 종합 대시보드
                dashboard_fig = self.visualizer.create_comprehensive_dashboard(
                    trades, account, save_file="dashboard"
                )
                if dashboard_fig:
                    charts_info['dashboard'] = "charts/dashboard.png"
                
                # 심볼별 분석 차트
                if 'symbol_analysis' in self.analysis_results:
                    symbol_metrics = {}
                    for symbol, metrics_dict in self.analysis_results['symbol_analysis'].items():
                        symbol_metrics[symbol] = PerformanceMetrics(**metrics_dict)
                    
                    risk_return_fig = self.visualizer.create_risk_return_scatter(
                        symbol_metrics, save_file="risk_return_scatter"
                    )
                    if risk_return_fig:
                        charts_info['risk_return_scatter'] = "charts/risk_return_scatter.png"
                
                # 전략별 비교 차트
                if 'strategy_analysis' in self.analysis_results:
                    strategy_metrics = {}
                    for strategy, metrics_dict in self.analysis_results['strategy_analysis'].items():
                        strategy_metrics[strategy] = PerformanceMetrics(**metrics_dict)
                    
                    strategy_fig = self.visualizer.create_strategy_comparison(
                        strategy_metrics, save_file="strategy_comparison"
                    )
                    if strategy_fig:
                        charts_info['strategy_comparison'] = "charts/strategy_comparison.png"
            
            self.charts_generated = charts_info
            
            return {
                'charts_generated': charts_info,
                'visualization_summary': f"총 {len(charts_info)}개의 차트가 생성되었습니다."
            }
            
        except Exception as e:
            self.logger.error(f"시각화 오류: {e}")
            return {}
    
    def _generate_insights(self) -> List[Dict[str, Any]]:
        """인사이트 도출"""
        insights = []
        
        try:
            # 성과 기반 인사이트
            if 'performance_metrics' in self.analysis_results:
                metrics = self.analysis_results['performance_metrics']
                
                # 수익률 인사이트
                total_return = metrics.get('total_return', 0)
                if total_return > 20:
                    insights.append({
                        'title': '우수한 수익률 달성',
                        'description': f'총 수익률이 {total_return:.2f}%로 매우 우수한 성과를 보입니다.',
                        'recommendation': '현재 전략을 유지하되, 리스크 관리를 통해 안정성을 높이세요.',
                        'impact': 'high'
                    })
                elif total_return < -10:
                    insights.append({
                        'title': '손실 발생 - 전략 재검토 필요',
                        'description': f'총 수익률이 {total_return:.2f}%로 큰 손실을 보입니다.',
                        'recommendation': '전략을 재검토하고 매개변수를 조정하거나 새로운 전략을 고려하세요.',
                        'impact': 'high'
                    })
                
                # 승률 인사이트
                win_rate = metrics.get('win_rate', 0)
                if win_rate < 40:
                    insights.append({
                        'title': '낮은 승률 개선 필요',
                        'description': f'승률이 {win_rate:.1f}%로 개선이 필요합니다.',
                        'recommendation': '진입 신호의 정확도를 높이기 위해 추가 필터 조건을 검토하세요.',
                        'impact': 'medium'
                    })
                
                # 리스크 인사이트
                max_drawdown = metrics.get('max_drawdown', 0)
                if max_drawdown > 15:
                    insights.append({
                        'title': '높은 최대 낙폭 위험',
                        'description': f'최대 낙폭이 {max_drawdown:.2f}%로 리스크 관리가 필요합니다.',
                        'recommendation': '포지션 크기를 줄이고 손절 규칙을 강화하세요.',
                        'impact': 'high'
                    })
            
            # 심볼별 인사이트
            if 'symbol_analysis' in self.analysis_results:
                symbol_analysis = self.analysis_results['symbol_analysis']
                
                # 최고/최악 성과 심볼
                best_symbol = max(symbol_analysis.keys(), 
                                key=lambda x: symbol_analysis[x].get('total_return', 0))
                worst_symbol = min(symbol_analysis.keys(),
                                 key=lambda x: symbol_analysis[x].get('total_return', 0))
                
                best_return = symbol_analysis[best_symbol].get('total_return', 0)
                worst_return = symbol_analysis[worst_symbol].get('total_return', 0)
                
                if best_return > 10:
                    insights.append({
                        'title': '우수 성과 코인 발견',
                        'description': f'{best_symbol}이 {best_return:.2f}%의 우수한 성과를 보입니다.',
                        'recommendation': '해당 코인의 거래 비중을 늘리고 유사한 특성을 가진 코인을 찾아보세요.',
                        'impact': 'medium'
                    })
                
                if worst_return < -10:
                    insights.append({
                        'title': '저성과 코인 감지',
                        'description': f'{worst_symbol}이 {worst_return:.2f}%의 손실을 보입니다.',
                        'recommendation': '해당 코인의 거래를 중단하고 전략을 재검토하세요.',
                        'impact': 'high'
                    })
            
            # 통계 분석 인사이트
            if 'statistical_analysis' in self.analysis_results:
                stats_data = self.analysis_results['statistical_analysis']
                
                # 정규성 검정 결과
                normality_tests = stats_data.get('normality_tests', {})
                daily_returns_normality = normality_tests.get('daily_returns', [])
                
                if daily_returns_normality:
                    # 모든 검정에서 정규분포가 아닌 경우
                    non_normal_count = sum(1 for test in daily_returns_normality 
                                         if test.get('p_value', 1) < 0.05)
                    
                    if non_normal_count >= 2:
                        insights.append({
                            'title': '수익률 분포의 비정규성',
                            'description': '일일 수익률이 정규분포를 따르지 않아 리스크 측정에 주의가 필요합니다.',
                            'recommendation': '히스토리컬 VaR 대신 파라메트릭 VaR을 사용하거나 더 보수적인 리스크 관리가 필요합니다.',
                            'impact': 'medium'
                        })
            
            # 인사이트가 없는 경우
            if not insights:
                insights.append({
                    'title': '분석 완료',
                    'description': '현재 데이터를 기반으로 특별한 개선점이 발견되지 않았습니다.',
                    'recommendation': '정기적인 모니터링을 통해 지속적인 성과 관리를 하세요.',
                    'impact': 'low'
                })
            
            self.logger.info(f"{len(insights)}개의 인사이트가 도출되었습니다")
            
        except Exception as e:
            self.logger.error(f"인사이트 도출 오류: {e}")
            insights = [{
                'title': '인사이트 생성 오류',
                'description': f'인사이트 생성 중 오류가 발생했습니다: {e}',
                'recommendation': '데이터를 확인하고 다시 분석을 실행해주세요.',
                'impact': 'medium'
            }]
        
        return insights
    
    def _generate_reports(self) -> Dict[str, str]:
        """리포트 생성"""
        try:
            # 분석 데이터 준비
            report_data = {
                **self.analysis_results,
                'charts_info': self.charts_generated
            }
            
            # 리포트 생성
            report_results = self.report_generator.generate_comprehensive_report(
                report_data, self.charts_generated
            )
            
            # 요약 리포트 생성
            summary_report = self.report_generator.generate_summary_report(report_data)
            
            return {
                **report_results,
                'summary': summary_report
            }
            
        except Exception as e:
            self.logger.error(f"리포트 생성 오류: {e}")
            return {"error": str(e)}
    
    def get_analysis_summary(self) -> str:
        """분석 요약 반환"""
        if not self.analysis_results:
            return "아직 분석이 실행되지 않았습니다. run_comprehensive_analysis()를 먼저 실행하세요."
        
        try:
            # 기본 정보
            timestamp = self.analysis_results.get('timestamp', datetime.now().isoformat())
            performance = self.analysis_results.get('performance_metrics', {})
            
            summary = f"""
=== 자동매매 분석 요약 ===
분석 시간: {timestamp}

📊 핵심 지표
- 총 수익률: {performance.get('total_return', 0):.2f}%
- 승률: {performance.get('win_rate', 0):.1f}%
- 최대 낙폭: {performance.get('max_drawdown', 0):.2f}%
- 샤프 비율: {performance.get('sharpe_ratio', 0):.2f}
- 총 거래 수: {performance.get('total_trades', 0)}건

📈 생성된 차트: {len(self.charts_generated)}개
💡 핵심 인사이트: {len(self.analysis_results.get('insights', []))}개

📄 생성된 리포트:
"""
            
            reports = self.analysis_results.get('reports', {})
            for report_type, path in reports.items():
                if report_type != 'error':
                    summary += f"- {report_type.upper()}: {path}\n"
            
            return summary.strip()
            
        except Exception as e:
            return f"요약 생성 중 오류 발생: {e}"
    
    def export_analysis_data(self, output_path: str) -> bool:
        """분석 데이터 내보내기"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"분석 데이터 내보내기 완료: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"분석 데이터 내보내기 오류: {e}")
            return False

# 사용 예시
if __name__ == "__main__":
    # 분석 설정
    analysis_config = AnalysisConfig(
        enable_visualization=True,
        enable_statistical_analysis=True,
        enable_performance_analysis=True,
        enable_report_generation=True,
        save_charts=True,
        generate_html_report=True,
        generate_json_report=True
    )
    
    # 분석 시스템 초기화
    analyzer = TradingAnalyzer(analysis_config)
    
    # 종합 분석 실행
    print("자동매매 종합 분석을 시작합니다...")
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        # 분석 요약 출력
        summary = analyzer.get_analysis_summary()
        print(summary)
        
        # 분석 데이터 내보내기
        analyzer.export_analysis_data("analysis_results.json")
        print("\n분석이 완료되었습니다!")
    else:
        print(f"분석 중 오류 발생: {results['error']}")



