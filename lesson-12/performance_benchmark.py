#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 분석 시스템 성능 벤치마크 및 테스트
최적화 전후 성능 비교 및 대용량 데이터 처리 테스트
"""

import time
import psutil
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging
import json
import gc
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

# 원본 및 최적화된 모듈 import
from data_processor import DataProcessor, DataConfig as OriginalDataConfig
from performance_metrics import calculate_comprehensive_metrics
from visualization import ChartGenerator
from statistical_analysis import StatisticalAnalyzer
from trading_analyzer import TradingAnalyzer, AnalysisConfig as OriginalAnalysisConfig

from data_processor_optimized import OptimizedDataProcessor, DataConfig as OptimizedDataConfig
from performance_metrics_optimized import OptimizedPerformanceAnalyzer
from visualization_optimized import OptimizedTradingVisualizer, ChartConfig
from statistical_analysis_optimized import OptimizedStatisticalAnalyzer
from trading_analyzer_optimized import OptimizedTradingAnalyzer, OptimizedAnalysisConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkConfig:
    """벤치마크 설정"""
    test_data_sizes: List[int] = None  # 테스트할 데이터 크기들
    test_scenarios: List[str] = None   # 테스트 시나리오들
    iterations: int = 3                # 각 테스트 반복 횟수
    memory_limit_mb: int = 1000       # 메모리 제한
    timeout_seconds: int = 300         # 타임아웃
    
    def __post_init__(self):
        if self.test_data_sizes is None:
            self.test_data_sizes = [1000, 5000, 10000, 50000, 100000]
        if self.test_scenarios is None:
            self.test_scenarios = ["small", "medium", "large", "xlarge"]

@dataclass
class BenchmarkResult:
    """벤치마크 결과"""
    test_name: str
    version: str  # "original" or "optimized"
    data_size: int
    execution_time: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_usage_avg: float
    success: bool
    error_message: str = ""
    details: Dict[str, Any] = None

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.monitoring = True
        self.start_time = time.time()
        self.memory_samples = []
        self.cpu_samples = []
        
        # 백그라운드 모니터링 스레드
        import threading
        def monitor():
            while self.monitoring:
                try:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    cpu_percent = self.process.cpu_percent()
                    
                    self.memory_samples.append(memory_mb)
                    self.cpu_samples.append(cpu_percent)
                    
                    time.sleep(0.1)  # 100ms 간격
                except:
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Tuple[float, float, float]:
        """모니터링 중지 및 통계 반환"""
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        execution_time = time.time() - self.start_time if self.start_time else 0
        
        peak_memory = max(self.memory_samples) if self.memory_samples else 0
        avg_memory = np.mean(self.memory_samples) if self.memory_samples else 0
        avg_cpu = np.mean(self.cpu_samples) if self.cpu_samples else 0
        
        return execution_time, peak_memory, avg_memory, avg_cpu

class DataGenerator:
    """테스트 데이터 생성기"""
    
    @staticmethod
    def generate_test_data(size: int, scenario: str = "medium") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """테스트 데이터 생성"""
        np.random.seed(42)  # 재현 가능한 결과
        
        start_date = datetime.now() - timedelta(days=90)
        
        # 거래 데이터 생성
        trades_data = []
        for i in range(size):
            trade_date = start_date + timedelta(
                days=np.random.randint(0, 90),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            trades_data.append({
                'order_id': f'order_{i:06d}',
                'symbol': np.random.choice(['KRW-BTC', 'KRW-ETH', 'KRW-XRP']),
                'side': np.random.choice(['BUY', 'SELL']),
                'amount': np.random.uniform(0.001, 0.01),
                'price': np.random.uniform(30000000, 70000000),
                'status': 'filled',
                'strategy': np.random.choice(['volatility_breakout', 'ma_crossover', 'rsi_strategy']),
                'created_at': trade_date,
                'updated_at': trade_date
            })
        
        trades_df = pd.DataFrame(trades_data)
        
        # 계좌 데이터 생성
        account_data = []
        balance = 10000000
        for i in range(90):  # 90일간의 계좌 데이터
            date = start_date + timedelta(days=i)
            daily_return = np.random.uniform(-0.05, 0.05)
            balance = balance * (1 + daily_return)
            
            account_data.append({
                'balance': balance,
                'date': date.date()
            })
        
        account_df = pd.DataFrame(account_data)
        
        # 시나리오별 데이터 조정
        if scenario == "large":
            # 더 복잡한 데이터
            trades_df['pnl'] = np.random.uniform(-10000, 10000, len(trades_df))
            trades_df['holding_period'] = np.random.randint(1, 1440, len(trades_df))
        
        return trades_df, account_df

class PerformanceBenchmark:
    """성능 벤치마크 클래스"""
    
    def __init__(self, config: BenchmarkConfig = None):
        self.config = config or BenchmarkConfig()
        self.results = []
        self.logger = logging.getLogger(__name__)
        
        # 결과 저장 디렉토리
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """종합 벤치마크 실행"""
        self.logger.info("=== 종합 성능 벤치마크 시작 ===")
        
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config.__dict__,
            'results': []
        }
        
        # 1. 데이터 처리 벤치마크
        self.logger.info("1. 데이터 처리 벤치마크")
        data_processing_results = self._benchmark_data_processing()
        benchmark_results['results'].extend(data_processing_results)
        
        # 2. 성과 분석 벤치마크
        self.logger.info("2. 성과 분석 벤치마크")
        performance_analysis_results = self._benchmark_performance_analysis()
        benchmark_results['results'].extend(performance_analysis_results)
        
        # 3. 통계 분석 벤치마크
        self.logger.info("3. 통계 분석 벤치마크")
        statistical_analysis_results = self._benchmark_statistical_analysis()
        benchmark_results['results'].extend(statistical_analysis_results)
        
        # 4. 시각화 벤치마크
        self.logger.info("4. 시각화 벤치마크")
        visualization_results = self._benchmark_visualization()
        benchmark_results['results'].extend(visualization_results)
        
        # 5. 종합 분석 벤치마크
        self.logger.info("5. 종합 분석 벤치마크")
        comprehensive_results = self._benchmark_comprehensive_analysis()
        benchmark_results['results'].extend(comprehensive_results)
        
        # 결과 저장
        self._save_results(benchmark_results)
        
        # 성능 비교 리포트 생성
        self._generate_performance_report(benchmark_results)
        
        self.logger.info("=== 종합 성능 벤치마크 완료 ===")
        
        return benchmark_results
    
    def _benchmark_data_processing(self) -> List[BenchmarkResult]:
        """데이터 처리 벤치마크"""
        results = []
        
        for size in self.config.test_data_sizes:
            self.logger.info(f"데이터 처리 벤치마크: {size}건")
            
            # 테스트 데이터 생성
            trades_df, account_df = DataGenerator.generate_test_data(size)
            
            # 원본 버전 테스트
            result = self._test_data_processing_original(trades_df, account_df, size)
            results.append(result)
            
            # 최적화 버전 테스트
            result = self._test_data_processing_optimized(trades_df, account_df, size)
            results.append(result)
        
        return results
    
    def _test_data_processing_original(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """원본 데이터 처리 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 원본 데이터 처리기 생성 및 테스트
            config = OriginalDataConfig()
            processor = DataProcessor(config)
            
            # 데이터 전처리
            processed_trades = processor.preprocess_trade_data(trades_df)
            processed_account = processor.preprocess_account_data(account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="data_processing",
                version="original",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={
                    'processed_trades': len(processed_trades),
                    'processed_account': len(processed_account)
                }
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="data_processing",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _test_data_processing_optimized(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """최적화된 데이터 처리 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 최적화된 데이터 처리기 생성 및 테스트
            config = OptimizedDataConfig()
            processor = OptimizedDataProcessor(config)
            
            # 데이터 전처리
            processed_trades = processor.preprocess_trade_data_optimized(trades_df)
            processed_account = processor.preprocess_account_data_optimized(account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="data_processing",
                version="optimized",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={
                    'processed_trades': len(processed_trades),
                    'processed_account': len(processed_account)
                }
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="data_processing",
                version="optimized",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _benchmark_performance_analysis(self) -> List[BenchmarkResult]:
        """성과 분석 벤치마크"""
        results = []
        
        for size in self.config.test_data_sizes:
            self.logger.info(f"성과 분석 벤치마크: {size}건")
            
            # 테스트 데이터 생성
            trades_df, account_df = DataGenerator.generate_test_data(size)
            
            # 원본 버전 테스트
            result = self._test_performance_analysis_original(trades_df, account_df, size)
            results.append(result)
            
            # 최적화 버전 테스트
            result = self._test_performance_analysis_optimized(trades_df, account_df, size)
            results.append(result)
        
        return results
    
    def _test_performance_analysis_original(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """원본 성과 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 성과 지표 계산
            metrics = calculate_comprehensive_metrics(trades_df, account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="performance_analysis",
                version="original",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'metrics_calculated': len(metrics.__dict__)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="performance_analysis",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _test_performance_analysis_optimized(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """최적화된 성과 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 최적화된 성과 분석기
            analyzer = OptimizedPerformanceAnalyzer()
            metrics = analyzer.calculate_comprehensive_metrics(trades_df, account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="performance_analysis",
                version="optimized",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'metrics_calculated': len(metrics.__dict__)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="performance_analysis",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _benchmark_statistical_analysis(self) -> List[BenchmarkResult]:
        """통계 분석 벤치마크"""
        results = []
        
        for size in self.config.test_data_sizes:
            self.logger.info(f"통계 분석 벤치마크: {size}건")
            
            # 테스트 데이터 생성
            trades_df, account_df = DataGenerator.generate_test_data(size)
            
            # 원본 버전 테스트
            result = self._test_statistical_analysis_original(trades_df, account_df, size)
            results.append(result)
            
            # 최적화 버전 테스트
            result = self._test_statistical_analysis_optimized(trades_df, account_df, size)
            results.append(result)
        
        return results
    
    def _test_statistical_analysis_original(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """원본 통계 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 원본 통계 분석기
            analyzer = StatisticalAnalyzer()
            results = analyzer.analyze_comprehensive_statistics(trades_df, account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="statistical_analysis",
                version="original",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'statistical_tests': len(results)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="statistical_analysis",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _test_statistical_analysis_optimized(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """최적화된 통계 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 최적화된 통계 분석기
            analyzer = OptimizedStatisticalAnalyzer()
            results = analyzer.analyze_comprehensive_statistics(trades_df, account_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="statistical_analysis",
                version="optimized",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'statistical_tests': len(results)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="statistical_analysis",
                version="optimized",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _benchmark_visualization(self) -> List[BenchmarkResult]:
        """시각화 벤치마크"""
        results = []
        
        for size in self.config.test_data_sizes[:3]:  # 시각화는 작은 데이터만 테스트
            self.logger.info(f"시각화 벤치마크: {size}건")
            
            # 테스트 데이터 생성
            trades_df, account_df = DataGenerator.generate_test_data(size)
            
            # 원본 버전 테스트
            result = self._test_visualization_original(trades_df, account_df, size)
            results.append(result)
            
            # 최적화 버전 테스트
            result = self._test_visualization_optimized(trades_df, account_df, size)
            results.append(result)
        
        return results
    
    def _test_visualization_original(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """원본 시각화 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 원본 차트 생성기
            chart_generator = ChartGenerator()
            
            # 기본 차트 생성
            fig1 = chart_generator.create_equity_curve(account_df)
            fig2 = chart_generator.create_trade_distribution(trades_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="visualization",
                version="original",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'charts_created': 2}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="visualization",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _test_visualization_optimized(self, trades_df: pd.DataFrame, account_df: pd.DataFrame, size: int) -> BenchmarkResult:
        """최적화된 시각화 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 최적화된 시각화 생성기
            chart_config = ChartConfig()
            visualizer = OptimizedTradingVisualizer(chart_config)
            
            # 최적화된 차트 생성
            fig1 = visualizer.create_equity_curve_optimized(account_df)
            fig2 = visualizer.create_trade_distribution_optimized(trades_df)
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="visualization",
                version="optimized",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'charts_created': 2}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="visualization",
                version="optimized",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _benchmark_comprehensive_analysis(self) -> List[BenchmarkResult]:
        """종합 분석 벤치마크"""
        results = []
        
        for size in self.config.test_data_sizes[:3]:  # 종합 분석은 작은 데이터만 테스트
            self.logger.info(f"종합 분석 벤치마크: {size}건")
            
            # 원본 버전 테스트
            result = self._test_comprehensive_analysis_original(size)
            results.append(result)
            
            # 최적화 버전 테스트
            result = self._test_comprehensive_analysis_optimized(size)
            results.append(result)
        
        return results
    
    def _test_comprehensive_analysis_original(self, size: int) -> BenchmarkResult:
        """원본 종합 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 원본 분석기
            config = OriginalAnalysisConfig()
            analyzer = TradingAnalyzer(config)
            
            # 종합 분석 실행
            results = analyzer.run_comprehensive_analysis()
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="comprehensive_analysis",
                version="original",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'analysis_completed': bool(results)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="comprehensive_analysis",
                version="original",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _test_comprehensive_analysis_optimized(self, size: int) -> BenchmarkResult:
        """최적화된 종합 분석 테스트"""
        monitor = PerformanceMonitor()
        
        try:
            monitor.start_monitoring()
            
            # 최적화된 분석기
            config = OptimizedAnalysisConfig()
            analyzer = OptimizedTradingAnalyzer(config)
            
            # 종합 분석 실행
            results = analyzer.run_comprehensive_analysis()
            
            execution_time, peak_memory, avg_memory, avg_cpu = monitor.stop_monitoring()
            
            return BenchmarkResult(
                test_name="comprehensive_analysis",
                version="optimized",
                data_size=size,
                execution_time=execution_time,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                cpu_usage_avg=avg_cpu,
                success=True,
                details={'analysis_completed': bool(results)}
            )
            
        except Exception as e:
            monitor.stop_monitoring()
            return BenchmarkResult(
                test_name="comprehensive_analysis",
                version="optimized",
                data_size=size,
                execution_time=0,
                memory_peak_mb=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_avg=0,
                success=False,
                error_message=str(e)
            )
    
    def _save_results(self, benchmark_results: Dict[str, Any]):
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"benchmark_results_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"벤치마크 결과 저장: {filepath}")
    
    def _generate_performance_report(self, benchmark_results: Dict[str, Any]):
        """성능 비교 리포트 생성"""
        # 결과 분석
        df_results = pd.DataFrame([result.__dict__ for result in benchmark_results['results']])
        
        # 성공한 테스트만 필터링
        successful_results = df_results[df_results['success'] == True]
        
        if successful_results.empty:
            self.logger.warning("성공한 테스트가 없어 리포트를 생성할 수 없습니다.")
            return
        
        # 리포트 생성
        report = self._create_performance_report(successful_results)
        
        # 리포트 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.results_dir / f"performance_report_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"성능 리포트 생성: {report_file}")
    
    def _create_performance_report(self, df: pd.DataFrame) -> str:
        """성능 리포트 HTML 생성"""
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>자동매매 분석 시스템 성능 벤치마크 리포트</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background-color: #fff; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; }}
        .improvement {{ color: #27ae60; font-weight: bold; }}
        .regression {{ color: #e74c3c; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .original {{ background-color: #f8f9fa; }}
        .optimized {{ background-color: #e8f5e8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 자동매매 분석 시스템 성능 벤치마크 리포트</h1>
        <p><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 성능 요약</h2>
        <div class="summary">
"""
        
        # 성능 개선 통계 계산
        original_results = df[df['version'] == 'original']
        optimized_results = df[df['version'] == 'optimized']
        
        if not original_results.empty and not optimized_results.empty:
            # 평균 성능 비교
            avg_time_original = original_results['execution_time'].mean()
            avg_time_optimized = optimized_results['execution_time'].mean()
            time_improvement = ((avg_time_original - avg_time_optimized) / avg_time_original) * 100
            
            avg_memory_original = original_results['memory_peak_mb'].mean()
            avg_memory_optimized = optimized_results['memory_peak_mb'].mean()
            memory_improvement = ((avg_memory_original - avg_memory_optimized) / avg_memory_original) * 100
            
            html += f"""
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{time_improvement:+.1f}%</div>
                    <div class="metric-label">실행 시간 개선</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{memory_improvement:+.1f}%</div>
                    <div class="metric-label">메모리 사용량 개선</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(df[df['success']])}</div>
                    <div class="metric-label">성공한 테스트</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(df[df['success'] == False])}</div>
                    <div class="metric-label">실패한 테스트</div>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <h2>📈 상세 결과</h2>
        <table>
            <tr>
                <th>테스트</th>
                <th>버전</th>
                <th>데이터 크기</th>
                <th>실행 시간(초)</th>
                <th>최대 메모리(MB)</th>
                <th>평균 메모리(MB)</th>
                <th>CPU 사용률(%)</th>
                <th>성공</th>
            </tr>
"""
        
        # 결과 테이블 생성
        for _, row in df.iterrows():
            version_class = "original" if row['version'] == 'original' else "optimized"
            success_text = "✅" if row['success'] else "❌"
            
            html += f"""
            <tr class="{version_class}">
                <td>{row['test_name']}</td>
                <td>{row['version']}</td>
                <td>{row['data_size']:,}</td>
                <td>{row['execution_time']:.3f}</td>
                <td>{row['memory_peak_mb']:.1f}</td>
                <td>{row['memory_avg_mb']:.1f}</td>
                <td>{row['cpu_usage_avg']:.1f}</td>
                <td>{success_text}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>🎯 결론</h2>
        <div class="summary">
"""
        
        if time_improvement > 0:
            html += f"<p class='improvement'>✅ 최적화된 버전이 평균 {time_improvement:.1f}% 빠른 실행 시간을 보여줍니다.</p>"
        else:
            html += f"<p class='regression'>⚠️ 최적화된 버전이 평균 {abs(time_improvement):.1f}% 느린 실행 시간을 보여줍니다.</p>"
        
        if memory_improvement > 0:
            html += f"<p class='improvement'>✅ 최적화된 버전이 평균 {memory_improvement:.1f}% 적은 메모리를 사용합니다.</p>"
        else:
            html += f"<p class='regression'>⚠️ 최적화된 버전이 평균 {abs(memory_improvement):.1f}% 많은 메모리를 사용합니다.</p>"
        
        html += """
        </div>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; text-align: center;">
            <p>자동매매 분석 시스템 성능 벤치마크 v1.0</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html

# 사용 예시
if __name__ == "__main__":
    # 벤치마크 설정
    config = BenchmarkConfig(
        test_data_sizes=[1000, 5000, 10000],  # 작은 크기부터 시작
        iterations=1,  # 빠른 테스트를 위해 1회만
        memory_limit_mb=800,
        timeout_seconds=180
    )
    
    # 벤치마크 실행
    benchmark = PerformanceBenchmark(config)
    results = benchmark.run_comprehensive_benchmark()
    
    print("=== 성능 벤치마크 완료 ===")
    print(f"총 테스트 수: {len(results['results'])}")
    
    # 성공한 테스트 수
    successful_tests = [r for r in results['results'] if r.get('success', False)]
    print(f"성공한 테스트: {len(successful_tests)}")
    
    # 실패한 테스트 수
    failed_tests = [r for r in results['results'] if not r.get('success', False)]
    print(f"실패한 테스트: {len(failed_tests)}")
    
    if failed_tests:
        print("\n실패한 테스트:")
        for test in failed_tests:
            print(f"- {test['test_name']} ({test['version']}): {test.get('error_message', 'Unknown error')}")
    
    print(f"\n결과 저장 위치: {benchmark.results_dir}")
    print("벤치마크 완료!")














