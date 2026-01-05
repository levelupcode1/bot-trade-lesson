#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 분석 시스템 사용 예제
다양한 분석 시나리오를 보여주는 예제 코드
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_analyzer import TradingAnalyzer, AnalysisConfig
from data_processor import DataConfig
from visualization import ChartConfig
from report_generator import ReportConfig

def example_basic_analysis():
    """기본 분석 예제"""
    print("=== 기본 분석 예제 ===")
    
    # 기본 설정으로 분석 시스템 초기화
    analyzer = TradingAnalyzer()
    
    # 종합 분석 실행
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        # 분석 요약 출력
        summary = analyzer.get_analysis_summary()
        print(summary)
        
        # 분석 데이터 내보내기
        analyzer.export_analysis_data("basic_analysis_results.json")
        print("기본 분석 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_custom_config_analysis():
    """커스텀 설정 분석 예제"""
    print("\n=== 커스텀 설정 분석 예제 ===")
    
    # 커스텀 설정
    data_config = DataConfig(
        db_path="data/custom_trading.db",
        data_period_days=60,  # 60일 데이터 분석
        symbols=["KRW-BTC", "KRW-ETH", "KRW-ADA"],
        strategies=["volatility_breakout", "ma_crossover", "rsi_strategy"]
    )
    
    chart_config = ChartConfig(
        figure_size=(15, 10),
        dpi=150,
        save_path="custom_charts/",
        style="seaborn-v0_8"
    )
    
    report_config = ReportConfig(
        output_dir="custom_reports/",
        format_types=["html", "json", "csv"],
        include_raw_data=True
    )
    
    analysis_config = AnalysisConfig(
        data_config=data_config,
        chart_config=chart_config,
        report_config=report_config,
        enable_visualization=True,
        enable_statistical_analysis=True,
        enable_performance_analysis=True,
        enable_report_generation=True,
        save_charts=True,
        generate_html_report=True,
        generate_json_report=True
    )
    
    # 커스텀 설정으로 분석 시스템 초기화
    analyzer = TradingAnalyzer(analysis_config)
    
    # 특정 기간 분석 (최근 30일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    results = analyzer.run_comprehensive_analysis(start_date, end_date)
    
    if 'error' not in results:
        summary = analyzer.get_analysis_summary()
        print(summary)
        print("커스텀 설정 분석 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_performance_focus_analysis():
    """성과 중심 분석 예제"""
    print("\n=== 성과 중심 분석 예제 ===")
    
    # 성과 분석에만 집중하는 설정
    analysis_config = AnalysisConfig(
        enable_visualization=False,  # 시각화 비활성화
        enable_statistical_analysis=False,  # 통계 분석 비활성화
        enable_performance_analysis=True,  # 성과 분석만 활성화
        enable_report_generation=False,  # 리포트 생성 비활성화
        save_charts=False
    )
    
    analyzer = TradingAnalyzer(analysis_config)
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        # 성과 분석 결과만 출력
        performance_metrics = results.get('performance_metrics', {})
        
        print("📊 성과 분석 결과:")
        print(f"- 총 수익률: {performance_metrics.get('total_return', 0):.2f}%")
        print(f"- 승률: {performance_metrics.get('win_rate', 0):.1f}%")
        print(f"- 샤프 비율: {performance_metrics.get('sharpe_ratio', 0):.2f}")
        print(f"- 최대 낙폭: {performance_metrics.get('max_drawdown', 0):.2f}%")
        print(f"- 총 거래 수: {performance_metrics.get('total_trades', 0)}건")
        
        # 심볼별 성과
        symbol_analysis = results.get('symbol_analysis', {})
        if symbol_analysis:
            print("\n📈 심볼별 성과:")
            for symbol, metrics in symbol_analysis.items():
                print(f"- {symbol}: 수익률 {metrics.get('total_return', 0):.2f}%, "
                      f"승률 {metrics.get('win_rate', 0):.1f}%")
        
        print("성과 중심 분석 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_visualization_only():
    """시각화만 생성하는 예제"""
    print("\n=== 시각화 생성 예제 ===")
    
    # 시각화에만 집중하는 설정
    chart_config = ChartConfig(
        figure_size=(16, 12),
        dpi=200,
        save_path="visualization_charts/",
        style="seaborn-v0_8"
    )
    
    analysis_config = AnalysisConfig(
        chart_config=chart_config,
        enable_visualization=True,
        enable_statistical_analysis=False,
        enable_performance_analysis=False,
        enable_report_generation=False,
        save_charts=True
    )
    
    analyzer = TradingAnalyzer(analysis_config)
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        charts_info = results.get('charts_generated', {})
        
        print("📊 생성된 차트:")
        for chart_name, chart_path in charts_info.items():
            print(f"- {chart_name}: {chart_path}")
        
        print("시각화 생성 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_statistical_analysis():
    """통계 분석만 수행하는 예제"""
    print("\n=== 통계 분석 예제 ===")
    
    # 통계 분석에만 집중하는 설정
    analysis_config = AnalysisConfig(
        enable_visualization=False,
        enable_statistical_analysis=True,
        enable_performance_analysis=False,
        enable_report_generation=False
    )
    
    analyzer = TradingAnalyzer(analysis_config)
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        statistical_report = results.get('statistical_report', '')
        print("📈 통계 분석 리포트:")
        print(statistical_report)
        
        print("통계 분석 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_report_generation():
    """리포트 생성만 수행하는 예제"""
    print("\n=== 리포트 생성 예제 ===")
    
    # 리포트 생성에만 집중하는 설정
    report_config = ReportConfig(
        output_dir="example_reports/",
        format_types=["html", "json"],
        include_raw_data=True
    )
    
    analysis_config = AnalysisConfig(
        report_config=report_config,
        enable_visualization=False,
        enable_statistical_analysis=False,
        enable_performance_analysis=True,  # 리포트 생성을 위해 성과 분석 필요
        enable_report_generation=True
    )
    
    analyzer = TradingAnalyzer(analysis_config)
    results = analyzer.run_comprehensive_analysis()
    
    if 'error' not in results:
        reports = results.get('reports', {})
        
        print("📄 생성된 리포트:")
        for report_type, report_path in reports.items():
            if report_type != 'error':
                print(f"- {report_type.upper()}: {report_path}")
        
        # 요약 리포트 출력
        if 'summary' in reports:
            print("\n📋 요약 리포트:")
            print(reports['summary'])
        
        print("리포트 생성 완료!")
    else:
        print(f"분석 오류: {results['error']}")

def example_batch_analysis():
    """배치 분석 예제 (여러 기간 분석)"""
    print("\n=== 배치 분석 예제 ===")
    
    # 여러 기간에 대해 분석 수행
    periods = [
        ("최근 7일", 7),
        ("최근 30일", 30),
        ("최근 90일", 90)
    ]
    
    analyzer = TradingAnalyzer()
    
    for period_name, days in periods:
        print(f"\n📅 {period_name} 분석 중...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = analyzer.run_comprehensive_analysis(start_date, end_date)
        
        if 'error' not in results:
            performance = results.get('performance_metrics', {})
            print(f"  - 수익률: {performance.get('total_return', 0):.2f}%")
            print(f"  - 승률: {performance.get('win_rate', 0):.1f}%")
            print(f"  - 거래 수: {performance.get('total_trades', 0)}건")
            
            # 기간별 결과 저장
            analyzer.export_analysis_data(f"batch_analysis_{days}days.json")
        else:
            print(f"  - 분석 오류: {results['error']}")
    
    print("배치 분석 완료!")

def main():
    """메인 함수 - 모든 예제 실행"""
    print("🚀 자동매매 데이터 분석 시스템 예제")
    print("=" * 50)
    
    try:
        # 기본 분석
        example_basic_analysis()
        
        # 커스텀 설정 분석
        example_custom_config_analysis()
        
        # 성과 중심 분석
        example_performance_focus_analysis()
        
        # 시각화만 생성
        example_visualization_only()
        
        # 통계 분석만 수행
        example_statistical_analysis()
        
        # 리포트 생성만 수행
        example_report_generation()
        
        # 배치 분석
        example_batch_analysis()
        
        print("\n" + "=" * 50)
        print("✅ 모든 예제 실행 완료!")
        print("\n📁 생성된 파일들:")
        print("- charts/: 차트 이미지 파일들")
        print("- reports/: HTML/JSON 리포트 파일들")
        print("- *.json: 분석 결과 데이터 파일들")
        
    except Exception as e:
        print(f"❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()














