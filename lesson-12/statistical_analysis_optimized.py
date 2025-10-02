#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 통계 분석 모듈 (최적화 버전)
벡터화 연산과 병렬 처리를 위한 최적화된 통계 분석
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy import signal
from numba import jit, prange
import gc
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller
import warnings

# 경고 메시지 필터링
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StatisticalResults:
    """통계 분석 결과 데이터 클래스"""
    # 기본 통계
    count: int = 0
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # 정규성 검정
    shapiro_wilk: Dict[str, float] = None
    jarque_bera: Dict[str, float] = None
    kolmogorov_smirnov: Dict[str, float] = None
    
    # VaR/CVaR
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    
    # 상관관계
    pearson_corr: Dict[str, float] = None
    spearman_corr: Dict[str, float] = None
    
    # 시계열 분석
    adf_test: Dict[str, float] = None
    ljung_box: Dict[str, float] = None
    
    # 가설 검정
    t_test: Dict[str, float] = None

# Numba를 사용한 고성능 통계 계산 함수들
@jit(nopython=True, cache=True)
def calculate_skewness_kurtosis_numba(data: np.ndarray) -> Tuple[float, float]:
    """Numba를 사용한 왜도와 첨도 계산"""
    n = len(data)
    if n < 3:
        return 0.0, 0.0
    
    mean_val = np.mean(data)
    std_val = np.std(data)
    
    if std_val == 0:
        return 0.0, 0.0
    
    # 표준화된 데이터
    standardized = (data - mean_val) / std_val
    
    # 왜도 계산
    skewness = np.mean(standardized ** 3)
    
    # 첨도 계산 (정규분포 대비)
    kurtosis = np.mean(standardized ** 4) - 3
    
    return skewness, kurtosis

@jit(nopython=True, parallel=True, cache=True)
def calculate_rolling_statistics_numba(data: np.ndarray, window: int) -> Tuple[np.ndarray, np.ndarray]:
    """Numba를 사용한 롤링 통계 계산"""
    n = len(data)
    if n < window:
        return np.zeros(n), np.zeros(n)
    
    rolling_mean = np.zeros(n)
    rolling_std = np.zeros(n)
    
    for i in prange(window - 1, n):
        start_idx = i - window + 1
        window_data = data[start_idx:i+1]
        
        rolling_mean[i] = np.mean(window_data)
        rolling_std[i] = np.std(window_data)
    
    return rolling_mean, rolling_std

@jit(nopython=True, cache=True)
def calculate_var_cvar_historical_numba(data: np.ndarray, confidence: float) -> Tuple[float, float]:
    """Numba를 사용한 히스토리컬 VaR/CVaR 계산"""
    if len(data) == 0:
        return 0.0, 0.0
    
    sorted_data = np.sort(data)
    var_index = int((1 - confidence) * len(sorted_data))
    var_value = sorted_data[var_index]
    
    # CVaR 계산
    cvar_data = sorted_data[:var_index+1]
    cvar_value = np.mean(cvar_data) if len(cvar_data) > 0 else 0.0
    
    return var_value, cvar_value

@jit(nopython=True, cache=True)
def calculate_autocorrelation_numba(data: np.ndarray, max_lag: int) -> np.ndarray:
    """Numba를 사용한 자기상관 계산"""
    n = len(data)
    if n < 2:
        return np.array([])
    
    max_lag = min(max_lag, n - 1)
    autocorr = np.zeros(max_lag + 1)
    
    # 평균 제거
    mean_val = np.mean(data)
    centered_data = data - mean_val
    
    # 분산 계산
    variance = np.sum(centered_data ** 2)
    
    if variance == 0:
        return np.zeros(max_lag + 1)
    
    # 자기상관 계산
    for lag in range(max_lag + 1):
        if lag == 0:
            autocorr[lag] = 1.0
        else:
            numerator = np.sum(centered_data[lag:] * centered_data[:n-lag])
            autocorr[lag] = numerator / variance
    
    return autocorr

class OptimizedBasicStatistics:
    """최적화된 기본 통계 계산 클래스"""
    
    @staticmethod
    def calculate_descriptive_stats_vectorized(data: np.ndarray) -> Dict[str, float]:
        """벡터화된 기술통계 계산"""
        if len(data) == 0:
            return {
                'count': 0, 'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0,
                'skewness': 0.0, 'kurtosis': 0.0
            }
        
        # 기본 통계 (벡터화)
        count = len(data)
        mean_val = np.mean(data)
        std_val = np.std(data, ddof=1) if count > 1 else 0.0
        min_val = np.min(data)
        max_val = np.max(data)
        
        # 왜도와 첨도 (Numba 최적화)
        skewness, kurtosis = calculate_skewness_kurtosis_numba(data)
        
        return {
            'count': count,
            'mean': mean_val,
            'std': std_val,
            'min': min_val,
            'max': max_val,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    @staticmethod
    def calculate_rolling_stats_optimized(data: pd.Series, window: int = 20) -> pd.DataFrame:
        """최적화된 롤링 통계 계산"""
        if len(data) < window:
            return pd.DataFrame()
        
        # Numba 최적화 사용
        data_array = data.values.astype(np.float64)
        rolling_mean, rolling_std = calculate_rolling_statistics_numba(data_array, window)
        
        result = pd.DataFrame({
            'rolling_mean': rolling_mean,
            'rolling_std': rolling_std
        }, index=data.index)
        
        return result

class OptimizedNormalityTests:
    """최적화된 정규성 검정 클래스"""
    
    @staticmethod
    def perform_normality_tests_optimized(data: np.ndarray, sample_size: int = 5000) -> Dict[str, Dict[str, float]]:
        """최적화된 정규성 검정 수행"""
        if len(data) == 0:
            return {
                'shapiro_wilk': {'statistic': 0.0, 'p_value': 1.0},
                'jarque_bera': {'statistic': 0.0, 'p_value': 1.0},
                'kolmogorov_smirnov': {'statistic': 0.0, 'p_value': 1.0}
            }
        
        # 대용량 데이터 샘플링
        if len(data) > sample_size:
            np.random.seed(42)
            sample_indices = np.random.choice(len(data), sample_size, replace=False)
            sample_data = data[sample_indices]
            logger.info(f"정규성 검정을 위해 데이터 샘플링: {len(data)} -> {len(sample_data)}")
        else:
            sample_data = data
        
        results = {}
        
        try:
            # Shapiro-Wilk 검정 (최대 5000개)
            if len(sample_data) <= 5000:
                shapiro_stat, shapiro_p = stats.shapiro(sample_data)
                results['shapiro_wilk'] = {'statistic': shapiro_stat, 'p_value': shapiro_p}
            else:
                results['shapiro_wilk'] = {'statistic': 0.0, 'p_value': 1.0}
            
            # Jarque-Bera 검정
            jb_stat, jb_p = stats.jarque_bera(sample_data)
            results['jarque_bera'] = {'statistic': jb_stat, 'p_value': jb_p}
            
            # Kolmogorov-Smirnov 검정
            ks_stat, ks_p = stats.kstest(sample_data, 'norm', args=(np.mean(sample_data), np.std(sample_data)))
            results['kolmogorov_smirnov'] = {'statistic': ks_stat, 'p_value': ks_p}
            
        except Exception as e:
            logger.error(f"정규성 검정 오류: {e}")
            results = {
                'shapiro_wilk': {'statistic': 0.0, 'p_value': 1.0},
                'jarque_bera': {'statistic': 0.0, 'p_value': 1.0},
                'kolmogorov_smirnov': {'statistic': 0.0, 'p_value': 1.0}
            }
        
        return results

class OptimizedRiskAnalysis:
    """최적화된 리스크 분석 클래스"""
    
    @staticmethod
    def calculate_var_cvar_optimized(returns: np.ndarray, confidence_levels: List[float] = None) -> Dict[str, Tuple[float, float]]:
        """최적화된 VaR/CVaR 계산"""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]
        
        results = {}
        
        for confidence in confidence_levels:
            var, cvar = calculate_var_cvar_historical_numba(returns.astype(np.float64), confidence)
            results[f'var_{int(confidence*100)}'] = (var, cvar)
        
        return results
    
    @staticmethod
    def calculate_expected_shortfall_optimized(returns: np.ndarray, confidence: float = 0.95) -> float:
        """최적화된 예상 부족액 계산"""
        if len(returns) == 0:
            return 0.0
        
        var, cvar = calculate_var_cvar_historical_numba(returns.astype(np.float64), confidence)
        return abs(cvar)

class OptimizedCorrelationAnalysis:
    """최적화된 상관관계 분석 클래스"""
    
    @staticmethod
    def calculate_correlations_optimized(data_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """최적화된 상관관계 계산"""
        if len(data_dict) < 2:
            return {}
        
        # 데이터 정렬 및 길이 맞추기
        min_length = min(len(data) for data in data_dict.values())
        if min_length == 0:
            return {}
        
        aligned_data = {}
        for key, data in data_dict.items():
            if len(data) > min_length:
                aligned_data[key] = data[-min_length:]
            else:
                aligned_data[key] = data
        
        # DataFrame 생성
        df = pd.DataFrame(aligned_data)
        
        # NaN 제거
        df_clean = df.dropna()
        
        if len(df_clean) < 2:
            return {}
        
        results = {}
        
        try:
            # Pearson 상관계수
            pearson_corr = df_clean.corr(method='pearson')
            results['pearson'] = pearson_corr.to_dict()
            
            # Spearman 상관계수
            spearman_corr = df_clean.corr(method='spearman')
            results['spearman'] = spearman_corr.to_dict()
            
        except Exception as e:
            logger.error(f"상관관계 계산 오류: {e}")
            results = {}
        
        return results

class OptimizedTimeSeriesAnalysis:
    """최적화된 시계열 분석 클래스"""
    
    @staticmethod
    def perform_stationarity_test_optimized(data: pd.Series, max_lag: int = None) -> Dict[str, float]:
        """최적화된 정상성 검정"""
        if len(data) < 10:
            return {'adf_statistic': 0.0, 'adf_p_value': 1.0, 'critical_values': {}}
        
        # 대용량 데이터 샘플링
        if len(data) > 10000:
            sample_indices = np.linspace(0, len(data)-1, 10000, dtype=int)
            sample_data = data.iloc[sample_indices]
            logger.info(f"정상성 검정을 위해 데이터 샘플링: {len(data)} -> {len(sample_data)}")
        else:
            sample_data = data
        
        try:
            # ADF 검정
            adf_result = adfuller(sample_data.dropna(), maxlag=max_lag)
            
            return {
                'adf_statistic': adf_result[0],
                'adf_p_value': adf_result[1],
                'critical_values': {
                    '1%': adf_result[4]['1%'],
                    '5%': adf_result[4]['5%'],
                    '10%': adf_result[4]['10%']
                }
            }
            
        except Exception as e:
            logger.error(f"정상성 검정 오류: {e}")
            return {'adf_statistic': 0.0, 'adf_p_value': 1.0, 'critical_values': {}}
    
    @staticmethod
    def perform_autocorrelation_test_optimized(data: pd.Series, lags: int = 10) -> Dict[str, float]:
        """최적화된 자기상관 검정"""
        if len(data) < lags + 10:
            return {'ljung_box_stat': 0.0, 'ljung_box_p_value': 1.0}
        
        # 대용량 데이터 샘플링
        if len(data) > 10000:
            sample_indices = np.linspace(0, len(data)-1, 10000, dtype=int)
            sample_data = data.iloc[sample_indices]
        else:
            sample_data = data
        
        try:
            # Ljung-Box 검정
            ljung_box_result = acorr_ljungbox(sample_data.dropna(), lags=lags, return_df=True)
            
            # 최종 lag의 결과 사용
            final_lag_result = ljung_box_result.iloc[-1]
            
            return {
                'ljung_box_stat': final_lag_result['lb_stat'],
                'ljung_box_p_value': final_lag_result['lb_pvalue']
            }
            
        except Exception as e:
            logger.error(f"자기상관 검정 오류: {e}")
            return {'ljung_box_stat': 0.0, 'ljung_box_p_value': 1.0}

class ParallelStatisticalAnalyzer:
    """병렬 통계 분석 클래스"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.logger = logging.getLogger(__name__)
    
    def analyze_multiple_series_parallel(self, data_dict: Dict[str, pd.Series]) -> Dict[str, StatisticalResults]:
        """여러 시계열 병렬 분석"""
        def analyze_single_series(name_data_tuple):
            name, data = name_data_tuple
            analyzer = OptimizedStatisticalAnalyzer()
            results = analyzer.analyze_single_series(data)
            return name, results
        
        results = {}
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_name = {
                    executor.submit(analyze_single_series, item): item[0] 
                    for item in data_dict.items()
                }
                
                for future in future_to_name:
                    try:
                        name, result = future.result(timeout=30)
                        results[name] = result
                    except Exception as e:
                        self.logger.error(f"시계열 {future_to_name[future]} 분석 오류: {e}")
                        
        except Exception as e:
            self.logger.error(f"병렬 분석 오류: {e}")
        
        return results

class OptimizedStatisticalAnalyzer:
    """최적화된 종합 통계 분석 클래스"""
    
    def __init__(self, enable_parallel: bool = True):
        self.enable_parallel = enable_parallel
        self.logger = logging.getLogger(__name__)
        
        if enable_parallel:
            self.parallel_analyzer = ParallelStatisticalAnalyzer()
        else:
            self.parallel_analyzer = None
    
    def analyze_single_series(self, data: pd.Series) -> StatisticalResults:
        """단일 시계열 통계 분석"""
        try:
            # 기본 검증
            if data.empty:
                return StatisticalResults()
            
            # NaN 제거
            clean_data = data.dropna()
            if len(clean_data) == 0:
                return StatisticalResults()
            
            data_array = clean_data.values.astype(np.float64)
            
            # 기본 통계
            basic_stats = OptimizedBasicStatistics.calculate_descriptive_stats_vectorized(data_array)
            
            # 정규성 검정
            normality_tests = OptimizedNormalityTests.perform_normality_tests_optimized(data_array)
            
            # VaR/CVaR 계산
            var_cvar_results = OptimizedRiskAnalysis.calculate_var_cvar_optimized(data_array)
            
            # 시계열 분석
            stationarity_test = OptimizedTimeSeriesAnalysis.perform_stationarity_test_optimized(clean_data)
            autocorr_test = OptimizedTimeSeriesAnalysis.perform_autocorrelation_test_optimized(clean_data)
            
            # 결과 구성
            results = StatisticalResults(
                # 기본 통계
                count=basic_stats['count'],
                mean=basic_stats['mean'],
                std=basic_stats['std'],
                min_val=basic_stats['min'],
                max_val=basic_stats['max'],
                skewness=basic_stats['skewness'],
                kurtosis=basic_stats['kurtosis'],
                
                # 정규성 검정
                shapiro_wilk=normality_tests['shapiro_wilk'],
                jarque_bera=normality_tests['jarque_bera'],
                kolmogorov_smirnov=normality_tests['kolmogorov_smirnov'],
                
                # VaR/CVaR
                var_95=var_cvar_results.get('var_95', (0.0, 0.0))[0],
                var_99=var_cvar_results.get('var_99', (0.0, 0.0))[0],
                cvar_95=var_cvar_results.get('var_95', (0.0, 0.0))[1],
                cvar_99=var_cvar_results.get('var_99', (0.0, 0.0))[1],
                
                # 시계열 분석
                adf_test=stationarity_test,
                ljung_box=autocorr_test
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"통계 분석 오류: {e}")
            return StatisticalResults()
    
    def analyze_comprehensive_statistics(self, trades_df: pd.DataFrame, 
                                       account_df: pd.DataFrame) -> Dict[str, StatisticalResults]:
        """최적화된 종합 통계 분석"""
        try:
            results = {}
            
            # 메모리 사용량 확인
            if len(trades_df) > 100000:
                gc.collect()
            
            # 1. 계좌 데이터 분석
            if not account_df.empty:
                # 일일 수익률 분석
                if 'daily_return_pct' in account_df.columns:
                    daily_returns = account_df['daily_return_pct'].dropna()
                    if len(daily_returns) > 0:
                        results['DAILY_RETURNS'] = self.analyze_single_series(daily_returns)
                
                # 잔고 분석
                if 'balance' in account_df.columns:
                    balance = account_df['balance'].dropna()
                    if len(balance) > 0:
                        results['BALANCE'] = self.analyze_single_series(balance)
                
                # 낙폭 분석
                if 'drawdown_pct' in account_df.columns:
                    drawdown = account_df['drawdown_pct'].dropna()
                    if len(drawdown) > 0:
                        results['DRAWDOWN'] = self.analyze_single_series(drawdown)
            
            # 2. 거래 데이터 분석
            if not trades_df.empty:
                # P&L 분석
                sell_trades = trades_df[trades_df['side'] == 'SELL']
                if not sell_trades.empty and 'pnl' in sell_trades.columns:
                    pnl = sell_trades['pnl'].dropna()
                    if len(pnl) > 0:
                        results['PNL'] = self.analyze_single_series(pnl)
                
                # 보유 기간 분석
                if 'holding_period' in sell_trades.columns:
                    holding_period = sell_trades['holding_period'].dropna()
                    if len(holding_period) > 0:
                        results['HOLDING_PERIOD'] = self.analyze_single_series(holding_period)
            
            # 3. 상관관계 분석
            correlation_data = {}
            if 'DAILY_RETURNS' in results and 'PNL' in results:
                # 일일 수익률과 P&L의 상관관계
                daily_returns = account_df['daily_return_pct'].dropna()
                pnl_data = sell_trades['pnl'].dropna()
                
                # 길이 맞추기
                min_length = min(len(daily_returns), len(pnl_data))
                if min_length > 10:
                    correlation_data['daily_returns'] = daily_returns.values[-min_length:]
                    correlation_data['pnl'] = pnl_data.values[-min_length:]
            
            if correlation_data:
                corr_results = OptimizedCorrelationAnalysis.calculate_correlations_optimized(correlation_data)
                # 상관관계 결과를 StatisticalResults에 추가하는 로직
                for key in results:
                    if key in ['DAILY_RETURNS', 'PNL']:
                        results[key].pearson_corr = corr_results.get('pearson', {})
                        results[key].spearman_corr = corr_results.get('spearman', {})
            
            self.logger.info("최적화된 종합 통계 분석 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"종합 통계 분석 오류: {e}")
            return {}
    
    def generate_statistical_report_optimized(self, results: Dict[str, StatisticalResults]) -> str:
        """최적화된 통계 분석 리포트 생성"""
        if not results:
            return "분석할 데이터가 없습니다."
        
        report = "=== 최적화된 자동매매 통계 분석 리포트 ===\n\n"
        
        for series_name, stats in results.items():
            report += f"📊 {series_name} 분석\n"
            report += f"- 관측치 수: {stats.count:,}개\n"
            report += f"- 평균: {stats.mean:.4f}\n"
            report += f"- 표준편차: {stats.std:.4f}\n"
            report += f"- 최소값: {stats.min_val:.4f}\n"
            report += f"- 최대값: {stats.max_val:.4f}\n"
            report += f"- 왜도: {stats.skewness:.4f}\n"
            report += f"- 첨도: {stats.kurtosis:.4f}\n\n"
            
            # 정규성 검정 결과
            if stats.shapiro_wilk:
                report += "🔍 정규성 검정 결과\n"
                report += f"Shapiro-Wilk: {'정규분포' if stats.shapiro_wilk['p_value'] > 0.05 else '정규분포 아님'} "
                report += f"(p-value: {stats.shapiro_wilk['p_value']:.4f})\n"
                
                report += f"Jarque-Bera: {'정규분포' if stats.jarque_bera['p_value'] > 0.05 else '정규분포 아님'} "
                report += f"(p-value: {stats.jarque_bera['p_value']:.4f})\n"
                
                report += f"Kolmogorov-Smirnov: {'정규분포' if stats.kolmogorov_smirnov['p_value'] > 0.05 else '정규분포 아님'} "
                report += f"(p-value: {stats.kolmogorov_smirnov['p_value']:.4f})\n\n"
            
            # VaR/CVaR
            report += "⚠️ 리스크 통계\n"
            report += f"VaR (95%): {stats.var_95:.4f}\n"
            report += f"VaR (99%): {stats.var_99:.4f}\n"
            report += f"CVaR (95%): {stats.cvar_95:.4f}\n"
            report += f"CVaR (99%): {stats.cvar_99:.4f}\n\n"
            
            # 시계열 분석
            if stats.adf_test:
                report += "📈 시계열 분석\n"
                stationarity = "정상성" if stats.adf_test['adf_p_value'] < 0.05 else "비정상성"
                report += f"ADF 검정: {stationarity} (p-value: {stats.adf_test['adf_p_value']:.4f})\n"
            
            if stats.ljung_box:
                autocorr = "자기상관 있음" if stats.ljung_box['ljung_box_p_value'] < 0.05 else "자기상관 없음"
                report += f"Ljung-Box 검정: {autocorr} (p-value: {stats.ljung_box['ljung_box_p_value']:.4f})\n"
            
            report += "\n" + "="*50 + "\n\n"
        
        return report.strip()

# 사용 예시
if __name__ == "__main__":
    from data_processor_optimized import OptimizedDataProcessor, DataConfig
    import time
    
    # 최적화된 설정
    config = DataConfig(
        db_path="data/optimized_trading.db",
        data_period_days=90
    )
    
    # 데이터 로드
    processor = OptimizedDataProcessor(config)
    trades = processor.load_trade_data_optimized()
    account = processor.load_account_history_optimized()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data_optimized(trades)
        processed_account = processor.preprocess_account_data_optimized(account)
        
        # 최적화된 통계 분석
        start_time = time.time()
        
        analyzer = OptimizedStatisticalAnalyzer(enable_parallel=True)
        results = analyzer.analyze_comprehensive_statistics(processed_trades, processed_account)
        
        analysis_time = time.time() - start_time
        
        # 리포트 출력
        report = analyzer.generate_statistical_report_optimized(results)
        print(report)
        
        print(f"\n=== 성능 정보 ===")
        print(f"통계 분석 시간: {analysis_time:.3f}초")
        print(f"분석된 시계열 수: {len(results)}")
        print(f"거래 데이터 크기: {len(processed_trades):,}건")
        print(f"계좌 데이터 크기: {len(processed_account):,}건")
        
        # 상세 결과 출력
        for name, stats in results.items():
            print(f"\n{name}:")
            print(f"  - 평균: {stats.mean:.4f}")
            print(f"  - 표준편차: {stats.std:.4f}")
            print(f"  - 왜도: {stats.skewness:.4f}")
            print(f"  - 첨도: {stats.kurtosis:.4f}")
    else:
        print("통계 분석할 데이터가 없습니다.")



