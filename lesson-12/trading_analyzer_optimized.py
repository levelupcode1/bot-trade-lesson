#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 분석 시스템 메인 클래스 (최적화 버전)
통합된 최적화된 분석 파이프라인
"""

import pandas as pd
import numpy as np
import time
import gc
import psutil
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from pathlib import Path
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# 최적화된 모듈들 import
from data_processor_optimized import OptimizedDataProcessor, DataConfig
from performance_metrics_optimized import OptimizedPerformanceAnalyzer, PerformanceMetrics
from visualization_optimized import OptimizedTradingVisualizer, ChartConfig
from statistical_analysis_optimized import OptimizedStatisticalAnalyzer, StatisticalResults
from error_handler_optimized import OptimizedErrorHandler, ErrorSeverity, ErrorCategory
from cache_batch_optimizer import OptimizedCacheBatchSystem, CacheConfig, BatchConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizedAnalysisConfig:
    """최적화된 분석 설정 클래스"""
    # 데이터 설정
    data_config: DataConfig = field(default_factory=DataConfig)
    
    # 분석 옵션
    enable_performance_analysis: bool = True
    enable_statistical_analysis: bool = True
    enable_visualization: bool = True
    enable_report_generation: bool = True
    
    # 최적화 옵션
    enable_parallel_processing: bool = True
    enable_caching: bool = True
    enable_batch_processing: bool = True
    enable_error_recovery: bool = True
    
    # 성능 설정
    max_memory_usage_mb: int = 800
    max_processing_time_seconds: int = 300  # 5분
    chunk_size: int = 5000
    max_workers: int = None
    
    # 출력 설정
    report_formats: List[str] = field(default_factory=lambda: ["html", "json"])
    save_charts: bool = True
    chart_quality: str = "high"  # low, medium, high
    
    # 모니터링 설정
    enable_performance_monitoring: bool = True
    enable_memory_monitoring: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = min(mp.cpu_count(), 8)

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, config: OptimizedAnalysisConfig):
        self.config = config
        self.start_time = None
        self.end_time = None
        self.phase_times = {}
        self.memory_usage = []
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.start_time = time.time()
        self.monitoring = True
        
        if self.config.enable_memory_monitoring:
            self._start_memory_monitoring()
        
        logger.info("성능 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.end_time = time.time()
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        logger.info("성능 모니터링 중지")
    
    def _start_memory_monitoring(self):
        """메모리 모니터링 시작"""
        def monitor_memory():
            while self.monitoring:
                try:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    self.memory_usage.append({
                        'timestamp': time.time(),
                        'memory_mb': memory_mb
                    })
                    
                    # 메모리 사용량이 임계값을 초과하면 경고
                    if memory_mb > self.config.max_memory_usage_mb:
                        logger.warning(f"메모리 사용량 초과: {memory_mb:.1f}MB > {self.config.max_memory_usage_mb}MB")
                    
                    time.sleep(2.0)
                except Exception as e:
                    logger.error(f"메모리 모니터링 오류: {e}")
                    time.sleep(2.0)
        
        self.monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        self.monitor_thread.start()
    
    def record_phase_time(self, phase: str, duration: float):
        """단계별 시간 기록"""
        self.phase_times[phase] = duration
        logger.debug(f"단계 '{phase}' 완료: {duration:.3f}초")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 반환"""
        total_time = self.end_time - self.start_time if self.end_time else 0
        
        peak_memory = max([m['memory_mb'] for m in self.memory_usage]) if self.memory_usage else 0
        avg_memory = np.mean([m['memory_mb'] for m in self.memory_usage]) if self.memory_usage else 0
        
        return {
            'total_time_seconds': total_time,
            'peak_memory_mb': peak_memory,
            'average_memory_mb': avg_memory,
            'phase_times': self.phase_times.copy(),
            'memory_samples': len(self.memory_usage),
            'efficiency_score': self._calculate_efficiency_score()
        }
    
    def _calculate_efficiency_score(self) -> float:
        """효율성 점수 계산 (0-100)"""
        if not self.phase_times:
            return 0.0
        
        total_time = sum(self.phase_times.values())
        if total_time == 0:
            return 100.0
        
        # 각 단계별 가중치
        weights = {
            'data_processing': 0.3,
            'performance_analysis': 0.25,
            'statistical_analysis': 0.2,
            'visualization': 0.15,
            'report_generation': 0.1
        }
        
        # 예상 시간 대비 실제 시간으로 효율성 계산
        expected_ratios = {
            'data_processing': 0.3,
            'performance_analysis': 0.25,
            'statistical_analysis': 0.2,
            'visualization': 0.15,
            'report_generation': 0.1
        }
        
        efficiency_score = 100.0
        for phase, actual_time in self.phase_times.items():
            expected_ratio = expected_ratios.get(phase, 0.1)
            actual_ratio = actual_time / total_time
            ratio_diff = abs(actual_ratio - expected_ratio)
            efficiency_score -= ratio_diff * 200  # 패널티 계산
        
        return max(0.0, min(100.0, efficiency_score))

class OptimizedTradingAnalyzer:
    """최적화된 자동매매 분석 클래스"""
    
    def __init__(self, config: OptimizedAnalysisConfig = None):
        self.config = config or OptimizedAnalysisConfig()
        self.logger = logging.getLogger(__name__)
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # 성능 모니터링
        self.performance_monitor = PerformanceMonitor(self.config)
        
        # 분석 결과 저장
        self.analysis_results = {}
        self.insights = []
        
        self.logger.info("최적화된 자동매매 분석 시스템 초기화 완료")
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        try:
            # 오류 처리 시스템
            self.error_handler = OptimizedErrorHandler(
                log_file=f"logs/optimized_analysis_{datetime.now().strftime('%Y%m%d')}.log"
            )
            
            # 캐싱 및 배치 처리 시스템
            if self.config.enable_caching or self.config.enable_batch_processing:
                cache_config = CacheConfig(
                    max_memory_mb=self.config.max_memory_usage_mb // 2,
                    cache_dir="cache/optimized_analysis/"
                )
                batch_config = BatchConfig(
                    max_workers=self.config.max_workers,
                    memory_threshold_mb=self.config.max_memory_usage_mb
                )
                
                self.cache_batch_system = OptimizedCacheBatchSystem(cache_config, batch_config)
                self.cache_batch_system.start()
            else:
                self.cache_batch_system = None
            
            # 데이터 처리기
            self.data_processor = OptimizedDataProcessor(self.config.data_config)
            
            # 성과 분석기
            if self.config.enable_performance_analysis:
                self.performance_analyzer = OptimizedPerformanceAnalyzer(
                    enable_parallel=self.config.enable_parallel_processing
                )
            
            # 통계 분석기
            if self.config.enable_statistical_analysis:
                self.statistical_analyzer = OptimizedStatisticalAnalyzer(
                    enable_parallel=self.config.enable_parallel_processing
                )
            
            # 시각화 생성기
            if self.config.enable_visualization:
                chart_config = ChartConfig(
                    dpi=150 if self.config.chart_quality == "high" else 100,
                    save_path="optimized_charts/"
                )
                self.visualizer = OptimizedTradingVisualizer(chart_config)
            
            self.logger.info("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 오류: {e}")
            raise
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """최적화된 종합 분석 실행"""
        start_time = time.time()
        
        try:
            # 성능 모니터링 시작
            if self.config.enable_performance_monitoring:
                self.performance_monitor.start_monitoring()
            
            self.logger.info("최적화된 종합 분석 시작")
            
            # 1단계: 데이터 로드 및 전처리
            processed_data = self._run_optimized_data_processing()
            if not processed_data:
                return {'error': '데이터 처리 실패'}
            
            # 2단계: 성과 분석
            performance_results = self._run_optimized_performance_analysis(processed_data)
            
            # 3단계: 통계 분석
            statistical_results = self._run_optimized_statistical_analysis(processed_data)
            
            # 4단계: 시각화 생성
            visualization_results = self._run_optimized_visualization(processed_data)
            
            # 5단계: 인사이트 도출
            insights = self._generate_optimized_insights(
                performance_results, statistical_results, processed_data
            )
            
            # 6단계: 리포트 생성
            report_results = self._generate_optimized_reports(
                performance_results, statistical_results, visualization_results, insights
            )
            
            # 결과 통합
            self.analysis_results = {
                'data_summary': self._get_data_summary(processed_data),
                'performance_analysis': performance_results,
                'statistical_analysis': statistical_results,
                'visualization_results': visualization_results,
                'insights': insights,
                'reports': report_results,
                'performance_metrics': self.performance_monitor.get_performance_summary(),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            total_time = time.time() - start_time
            self.logger.info(f"최적화된 종합 분석 완료: {total_time:.3f}초")
            
            return self.analysis_results
            
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e,
                context={'analysis_type': 'comprehensive'},
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM
            )
            
            self.logger.error(f"종합 분석 오류: {e}")
            return {'error': str(e), 'error_info': error_info}
        
        finally:
            # 성능 모니터링 중지
            if self.config.enable_performance_monitoring:
                self.performance_monitor.stop_monitoring()
    
    def _run_optimized_data_processing(self) -> Optional[Dict[str, pd.DataFrame]]:
        """최적화된 데이터 처리 실행"""
        phase_start = time.time()
        
        try:
            self.logger.info("1단계: 최적화된 데이터 로드 및 전처리")
            
            # 데이터 로드 (캐싱 활용)
            if self.cache_batch_system:
                @self.cache_batch_system.cached_function(ttl=1800)
                def load_data():
                    trades = self.data_processor.load_trade_data_optimized()
                    account = self.data_processor.load_account_history_optimized()
                    return trades, account
                
                trades, account = load_data()
            else:
                trades = self.data_processor.load_trade_data_optimized()
                account = self.data_processor.load_account_history_optimized()
            
            if trades.empty and account.empty:
                self.logger.warning("분석할 데이터가 없습니다")
                return None
            
            # 데이터 전처리 (배치 처리 활용)
            if self.cache_batch_system:
                @self.cache_batch_system.batch_processed_function()
                def preprocess_trades(trade_items):
                    return [self.data_processor.preprocess_trade_data_optimized(item) 
                           for item in trade_items]
                
                processed_trades = self.data_processor.preprocess_trade_data_optimized(trades)
            else:
                processed_trades = self.data_processor.preprocess_trade_data_optimized(trades)
            
            processed_account = self.data_processor.preprocess_account_data_optimized(account)
            
            phase_time = time.time() - phase_start
            self.performance_monitor.record_phase_time('data_processing', phase_time)
            
            self.logger.info(f"데이터 처리 완료: {len(processed_trades)}건 거래, {len(processed_account)}건 계좌")
            
            return {
                'trades': processed_trades,
                'account': processed_account
            }
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'data_processing'},
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATA
            )
            return None
    
    def _run_optimized_performance_analysis(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """최적화된 성과 분석 실행"""
        if not self.config.enable_performance_analysis:
            return {}
        
        phase_start = time.time()
        
        try:
            self.logger.info("2단계: 최적화된 성과 분석")
            
            trades = processed_data['trades']
            account = processed_data['account']
            
            # 종합 성과 지표 계산
            overall_metrics = self.performance_analyzer.calculate_comprehensive_metrics(trades, account)
            
            # 세분화된 분석
            symbol_analysis = {}
            strategy_analysis = {}
            
            if not trades.empty:
                # 병렬 분석 실행
                if self.config.enable_parallel_processing:
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        # 코인별 분석
                        symbols = trades['symbol'].unique()
                        symbol_futures = {
                            executor.submit(
                                self.performance_analyzer.analyze_by_symbol_optimized,
                                trades[trades['symbol'] == symbol], account
                            ): symbol for symbol in symbols
                        }
                        
                        for future in symbol_futures:
                            try:
                                symbol, metrics = future.result(timeout=30)
                                symbol_analysis[symbol] = metrics
                            except Exception as e:
                                logger.error(f"심볼 분석 오류: {e}")
                        
                        # 전략별 분석
                        strategies = trades['strategy'].unique()
                        strategy_futures = {
                            executor.submit(
                                self.performance_analyzer.analyze_by_strategy_optimized,
                                trades[trades['strategy'] == strategy], account
                            ): strategy for strategy in strategies
                        }
                        
                        for future in strategy_futures:
                            try:
                                strategy, metrics = future.result(timeout=30)
                                strategy_analysis[strategy] = metrics
                            except Exception as e:
                                logger.error(f"전략 분석 오류: {e}")
                else:
                    symbol_analysis = self.performance_analyzer.analyze_by_symbol_optimized(trades, account)
                    strategy_analysis = self.performance_analyzer.analyze_by_strategy_optimized(trades, account)
            
            phase_time = time.time() - phase_start
            self.performance_monitor.record_phase_time('performance_analysis', phase_time)
            
            self.logger.info("성과 분석 완료")
            
            return {
                'overall_metrics': overall_metrics,
                'symbol_analysis': symbol_analysis,
                'strategy_analysis': strategy_analysis
            }
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'performance_analysis'},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.CALCULATION
            )
            return {}
    
    def _run_optimized_statistical_analysis(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """최적화된 통계 분석 실행"""
        if not self.config.enable_statistical_analysis:
            return {}
        
        phase_start = time.time()
        
        try:
            self.logger.info("3단계: 최적화된 통계 분석")
            
            trades = processed_data['trades']
            account = processed_data['account']
            
            # 종합 통계 분석
            statistical_results = self.statistical_analyzer.analyze_comprehensive_statistics(trades, account)
            
            phase_time = time.time() - phase_start
            self.performance_monitor.record_phase_time('statistical_analysis', phase_time)
            
            self.logger.info("통계 분석 완료")
            
            return statistical_results
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'statistical_analysis'},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.CALCULATION
            )
            return {}
    
    def _run_optimized_visualization(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """최적화된 시각화 실행"""
        if not self.config.enable_visualization:
            return {}
        
        phase_start = time.time()
        
        try:
            self.logger.info("4단계: 최적화된 시각화 생성")
            
            trades = processed_data['trades']
            account = processed_data['account']
            
            visualization_results = {}
            
            if not account.empty:
                # 자산 곡선
                fig = self.visualizer.create_equity_curve_optimized(
                    account, save_file="optimized_equity_curve"
                )
                if fig:
                    visualization_results['equity_curve'] = "optimized_equity_curve"
                
                # 낙폭 차트
                fig = self.visualizer.create_drawdown_chart_optimized(
                    account, save_file="optimized_drawdown"
                )
                if fig:
                    visualization_results['drawdown'] = "optimized_drawdown"
            
            if not trades.empty:
                # 거래 분포
                fig = self.visualizer.create_trade_distribution_optimized(
                    trades, save_file="optimized_trade_distribution"
                )
                if fig:
                    visualization_results['trade_distribution'] = "optimized_trade_distribution"
            
            # 종합 대시보드
            fig = self.visualizer.create_comprehensive_dashboard_optimized(
                trades, account, save_file="optimized_dashboard"
            )
            if fig:
                visualization_results['dashboard'] = "optimized_dashboard"
            
            phase_time = time.time() - phase_start
            self.performance_monitor.record_phase_time('visualization', phase_time)
            
            self.logger.info(f"시각화 생성 완료: {len(visualization_results)}개 차트")
            
            return visualization_results
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'visualization'},
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.VISUALIZATION
            )
            return {}
    
    def _generate_optimized_insights(self, performance_results: Dict[str, Any], 
                                   statistical_results: Dict[str, Any],
                                   processed_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """최적화된 인사이트 도출"""
        insights = []
        
        try:
            # 성과 기반 인사이트
            if 'overall_metrics' in performance_results:
                metrics = performance_results['overall_metrics']
                
                # 수익률 기반 인사이트
                if metrics.total_return < -10:
                    insights.append({
                        'type': 'warning',
                        'title': '큰 손실 발생',
                        'description': f'총 수익률이 {metrics.total_return:.2f}%로 큰 손실을 보입니다.',
                        'recommendation': '전략 재검토 및 리스크 관리 강화 필요',
                        'priority': 'high'
                    })
                
                # 승률 기반 인사이트
                if metrics.win_rate < 40:
                    insights.append({
                        'type': 'warning',
                        'title': '낮은 승률',
                        'description': f'승률이 {metrics.win_rate:.1f}%로 낮습니다.',
                        'recommendation': '진입/청산 조건 재검토 필요',
                        'priority': 'medium'
                    })
                
                # 최대 낙폭 기반 인사이트
                if metrics.max_drawdown > 20:
                    insights.append({
                        'type': 'warning',
                        'title': '높은 최대 낙폭 위험',
                        'description': f'최대 낙폭이 {metrics.max_drawdown:.2f}%로 리스크 관리가 필요합니다.',
                        'recommendation': '포지션 크기 조절 및 손절매 강화',
                        'priority': 'high'
                    })
            
            # 통계 기반 인사이트
            if 'DAILY_RETURNS' in statistical_results:
                daily_returns_stats = statistical_results['DAILY_RETURNS']
                
                if daily_returns_stats.skewness < -0.5:
                    insights.append({
                        'type': 'info',
                        'title': '음의 왜도 감지',
                        'description': f'일일 수익률의 왜도가 {daily_returns_stats.skewness:.3f}로 음의 값입니다.',
                        'recommendation': '큰 손실 가능성에 대한 대비책 필요',
                        'priority': 'medium'
                    })
            
            # 데이터 기반 인사이트
            if not processed_data['trades'].empty:
                trades = processed_data['trades']
                
                # 시간대별 거래 분석
                trades['hour'] = trades['created_at'].dt.hour
                hourly_volume = trades.groupby('hour').size()
                
                if len(hourly_volume) > 0:
                    peak_hour = hourly_volume.idxmax()
                    insights.append({
                        'type': 'info',
                        'title': '최적 거래 시간대',
                        'description': f'{peak_hour}시에 가장 많은 거래가 발생했습니다.',
                        'recommendation': '해당 시간대의 시장 특성 분석 권장',
                        'priority': 'low'
                    })
            
            self.logger.info(f"{len(insights)}개의 인사이트 도출")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'insights_generation'},
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.CALCULATION
            )
        
        return insights
    
    def _generate_optimized_reports(self, performance_results: Dict[str, Any],
                                  statistical_results: Dict[str, Any],
                                  visualization_results: Dict[str, str],
                                  insights: List[Dict[str, Any]]) -> Dict[str, str]:
        """최적화된 리포트 생성"""
        phase_start = time.time()
        
        try:
            self.logger.info("6단계: 최적화된 리포트 생성")
            
            reports = {}
            
            # JSON 리포트
            if "json" in self.config.report_formats:
                json_report = {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'performance_results': performance_results,
                    'statistical_results': statistical_results,
                    'visualization_files': visualization_results,
                    'insights': insights,
                    'performance_metrics': self.performance_monitor.get_performance_summary()
                }
                
                json_file = f"optimized_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
                
                reports['json'] = json_file
            
            # HTML 리포트 (간단한 버전)
            if "html" in self.config.report_formats:
                html_content = self._generate_html_report(
                    performance_results, statistical_results, insights
                )
                
                html_file = f"optimized_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                reports['html'] = html_file
            
            phase_time = time.time() - phase_start
            self.performance_monitor.record_phase_time('report_generation', phase_time)
            
            self.logger.info(f"리포트 생성 완료: {list(reports.keys())}")
            
            return reports
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context={'phase': 'report_generation'},
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.SYSTEM
            )
            return {}
    
    def _generate_html_report(self, performance_results: Dict[str, Any],
                            statistical_results: Dict[str, Any],
                            insights: List[Dict[str, Any]]) -> str:
        """HTML 리포트 생성"""
        html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>최적화된 자동매매 분석 리포트</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; }}
        .insight {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .insight.warning {{ background-color: #fdf2e9; border-left: 4px solid #e67e22; }}
        .insight.info {{ background-color: #e8f4fd; border-left: 4px solid #3498db; }}
        .performance-summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 최적화된 자동매매 분석 리포트</h1>
        <p><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 성과 요약</h2>
        <div class="performance-summary">
"""
        
        # 성과 지표 추가
        if 'overall_metrics' in performance_results:
            metrics = performance_results['overall_metrics']
            html_template += f"""
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics.total_return:.2f}%</div>
                    <div class="metric-label">총 수익률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.win_rate:.1f}%</div>
                    <div class="metric-label">승률</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.max_drawdown:.2f}%</div>
                    <div class="metric-label">최대 낙폭</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.sharpe_ratio:.2f}</div>
                    <div class="metric-label">샤프 비율</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.total_trades}</div>
                    <div class="metric-label">총 거래 수</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics.avg_holding_period:.0f}분</div>
                    <div class="metric-label">평균 보유 기간</div>
                </div>
            </div>
"""
        
        html_template += """
        </div>
        
        <h2>💡 주요 인사이트</h2>
"""
        
        # 인사이트 추가
        for insight in insights:
            priority_class = insight.get('priority', 'info')
            html_template += f"""
        <div class="insight {priority_class}">
            <h3>{insight.get('title', '인사이트')}</h3>
            <p><strong>설명:</strong> {insight.get('description', '')}</p>
            <p><strong>권장사항:</strong> {insight.get('recommendation', '')}</p>
            <p><strong>우선순위:</strong> {insight.get('priority', 'low')}</p>
        </div>
"""
        
        # 성능 정보 추가
        performance_metrics = self.performance_monitor.get_performance_summary()
        html_template += f"""
        <h2>⚡ 성능 정보</h2>
        <div class="performance-summary">
            <p><strong>총 분석 시간:</strong> {performance_metrics['total_time_seconds']:.3f}초</p>
            <p><strong>최대 메모리 사용량:</strong> {performance_metrics['peak_memory_mb']:.1f}MB</p>
            <p><strong>효율성 점수:</strong> {performance_metrics['efficiency_score']:.1f}/100</p>
        </div>
        
        <h2>📈 단계별 처리 시간</h2>
        <table>
            <tr><th>단계</th><th>처리 시간</th></tr>
"""
        
        for phase, duration in performance_metrics['phase_times'].items():
            html_template += f"<tr><td>{phase}</td><td>{duration:.3f}초</td></tr>"
        
        html_template += """
        </table>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; text-align: center;">
            <p>최적화된 자동매매 분석 시스템 v2.0</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html_template
    
    def _get_data_summary(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """데이터 요약 정보 반환"""
        trades = processed_data.get('trades', pd.DataFrame())
        account = processed_data.get('account', pd.DataFrame())
        
        summary = {
            'trades_count': len(trades),
            'account_records': len(account),
            'date_range': {
                'start': trades['created_at'].min().isoformat() if not trades.empty else None,
                'end': trades['created_at'].max().isoformat() if not trades.empty else None
            },
            'symbols': trades['symbol'].unique().tolist() if not trades.empty else [],
            'strategies': trades['strategy'].unique().tolist() if not trades.empty else []
        }
        
        return summary
    
    def get_analysis_summary(self) -> str:
        """분석 요약 반환"""
        if not self.analysis_results:
            return "분석이 실행되지 않았습니다."
        
        summary = f"""
=== 최적화된 자동매매 분석 요약 ===
분석 시간: {self.analysis_results.get('analysis_timestamp', 'N/A')}

📊 핵심 지표
"""
        
        if 'performance_analysis' in self.analysis_results:
            perf_results = self.analysis_results['performance_analysis']
            if 'overall_metrics' in perf_results:
                metrics = perf_results['overall_metrics']
                summary += f"- 총 수익률: {metrics.total_return:.2f}%\n"
                summary += f"- 승률: {metrics.win_rate:.1f}%\n"
                summary += f"- 최대 낙폭: {metrics.max_drawdown:.2f}%\n"
                summary += f"- 샤프 비율: {metrics.sharpe_ratio:.2f}\n"
                summary += f"- 총 거래 수: {metrics.total_trades}건\n"
        
        summary += f"\n📈 생성된 차트: {len(self.analysis_results.get('visualization_results', {}))}개\n"
        summary += f"💡 핵심 인사이트: {len(self.analysis_results.get('insights', []))}개\n"
        
        if 'reports' in self.analysis_results:
            reports = self.analysis_results['reports']
            summary += f"\n📄 생성된 리포트:\n"
            for format_type, filename in reports.items():
                summary += f"- {format_type.upper()}: {filename}\n"
        
        return summary
    
    def cleanup_resources(self):
        """리소스 정리"""
        try:
            if self.cache_batch_system:
                self.cache_batch_system.cleanup_resources()
            
            if hasattr(self, 'visualizer'):
                self.visualizer.cleanup_resources()
            
            self.error_handler.cleanup_resources()
            
            gc.collect()
            
            self.logger.info("최적화된 분석 시스템 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"리소스 정리 오류: {e}")

# 사용 예시
if __name__ == "__main__":
    import time
    
    # 최적화된 설정
    data_config = DataConfig(
        db_path="data/optimized_trading.db",
        data_period_days=90,
        chunk_size=5000
    )
    
    analysis_config = OptimizedAnalysisConfig(
        data_config=data_config,
        enable_performance_analysis=True,
        enable_statistical_analysis=True,
        enable_visualization=True,
        enable_report_generation=True,
        enable_parallel_processing=True,
        enable_caching=True,
        enable_batch_processing=True,
        max_memory_usage_mb=600,
        max_processing_time_seconds=300,
        report_formats=["html", "json"],
        chart_quality="high"
    )
    
    # 최적화된 분석기 생성
    analyzer = OptimizedTradingAnalyzer(analysis_config)
    
    try:
        # 종합 분석 실행
        start_time = time.time()
        results = analyzer.run_comprehensive_analysis()
        total_time = time.time() - start_time
        
        # 결과 출력
        print("=== 최적화된 자동매매 분석 결과 ===")
        print(f"총 처리 시간: {total_time:.3f}초")
        
        if 'error' not in results:
            summary = analyzer.get_analysis_summary()
            print(summary)
            
            # 성능 메트릭 출력
            if 'performance_metrics' in results:
                perf_metrics = results['performance_metrics']
                print(f"\n=== 성능 정보 ===")
                print(f"효율성 점수: {perf_metrics['efficiency_score']:.1f}/100")
                print(f"최대 메모리 사용량: {perf_metrics['peak_memory_mb']:.1f}MB")
                print(f"단계별 처리 시간:")
                for phase, duration in perf_metrics['phase_times'].items():
                    print(f"  - {phase}: {duration:.3f}초")
        else:
            print(f"분석 오류: {results['error']}")
    
    finally:
        # 리소스 정리
        analyzer.cleanup_resources()
        print("분석 완료!")









