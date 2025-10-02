#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 통계 분석 모듈
scipy를 활용한 고급 통계 분석 및 검정
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import normaltest, shapiro, jarque_bera, kstest
from scipy.stats import ttest_1samp, ttest_ind, mannwhitneyu, wilcoxon
from scipy.stats import chi2_contingency, pearsonr, spearmanr, kendalltau
from scipy.stats import norm, t, chi2
from scipy.optimize import minimize
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StatisticalTestResult:
    """통계 검정 결과 클래스"""
    test_name: str
    statistic: float
    p_value: float
    critical_value: Optional[float] = None
    conclusion: str = ""
    interpretation: str = ""

class NormalityTester:
    """정규성 검정 클래스"""
    
    @staticmethod
    def test_normality(data: pd.Series, alpha: float = 0.05) -> List[StatisticalTestResult]:
        """정규성 검정 수행"""
        results = []
        
        if data.empty:
            logger.warning("정규성 검정을 위한 데이터가 없습니다")
            return results
        
        # 1. Shapiro-Wilk 검정 (샘플 크기 <= 5000)
        if len(data) <= 5000:
            try:
                statistic, p_value = shapiro(data)
                result = StatisticalTestResult(
                    test_name="Shapiro-Wilk",
                    statistic=statistic,
                    p_value=p_value,
                    conclusion="정규분포" if p_value > alpha else "정규분포 아님",
                    interpretation=f"p-value: {p_value:.4f}, α: {alpha}"
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Shapiro-Wilk 검정 오류: {e}")
        
        # 2. Jarque-Bera 검정
        try:
            statistic, p_value = jarque_bera(data)
            result = StatisticalTestResult(
                test_name="Jarque-Bera",
                statistic=statistic,
                p_value=p_value,
                conclusion="정규분포" if p_value > alpha else "정규분포 아님",
                interpretation=f"p-value: {p_value:.4f}, α: {alpha}"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Jarque-Bera 검정 오류: {e}")
        
        # 3. Kolmogorov-Smirnov 검정
        try:
            statistic, p_value = kstest(data, 'norm', args=(data.mean(), data.std()))
            result = StatisticalTestResult(
                test_name="Kolmogorov-Smirnov",
                statistic=statistic,
                p_value=p_value,
                conclusion="정규분포" if p_value > alpha else "정규분포 아님",
                interpretation=f"p-value: {p_value:.4f}, α: {alpha}"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Kolmogorov-Smirnov 검정 오류: {e}")
        
        return results

class CorrelationAnalyzer:
    """상관관계 분석 클래스"""
    
    @staticmethod
    def calculate_correlations(data1: pd.Series, data2: pd.Series) -> Dict[str, Any]:
        """다양한 상관관계 계수 계산"""
        results = {}
        
        if data1.empty or data2.empty:
            logger.warning("상관관계 분석을 위한 데이터가 없습니다")
            return results
        
        # 공통 인덱스만 사용
        common_index = data1.index.intersection(data2.index)
        if len(common_index) == 0:
            logger.warning("공통 인덱스가 없습니다")
            return results
        
        x = data1.loc[common_index]
        y = data2.loc[common_index]
        
        # 1. 피어슨 상관계수
        try:
            pearson_corr, pearson_p = pearsonr(x, y)
            results['pearson'] = {
                'correlation': pearson_corr,
                'p_value': pearson_p,
                'strength': CorrelationAnalyzer._interpret_correlation(pearson_corr)
            }
        except Exception as e:
            logger.error(f"피어슨 상관계수 계산 오류: {e}")
        
        # 2. 스피어만 상관계수
        try:
            spearman_corr, spearman_p = spearmanr(x, y)
            results['spearman'] = {
                'correlation': spearman_corr,
                'p_value': spearman_p,
                'strength': CorrelationAnalyzer._interpret_correlation(spearman_corr)
            }
        except Exception as e:
            logger.error(f"스피어만 상관계수 계산 오류: {e}")
        
        # 3. 켄달 타우
        try:
            kendall_corr, kendall_p = kendalltau(x, y)
            results['kendall'] = {
                'correlation': kendall_corr,
                'p_value': kendall_p,
                'strength': CorrelationAnalyzer._interpret_correlation(kendall_corr)
            }
        except Exception as e:
            logger.error(f"켄달 타우 계산 오류: {e}")
        
        return results
    
    @staticmethod
    def _interpret_correlation(corr: float) -> str:
        """상관계수 강도 해석"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return "매우 강함"
        elif abs_corr >= 0.7:
            return "강함"
        elif abs_corr >= 0.5:
            return "중간"
        elif abs_corr >= 0.3:
            return "약함"
        else:
            return "매우 약함"

class HypothesisTester:
    """가설 검정 클래스"""
    
    @staticmethod
    def test_mean_difference(data1: pd.Series, data2: pd.Series, 
                           alpha: float = 0.05) -> List[StatisticalTestResult]:
        """평균 차이 검정"""
        results = []
        
        if data1.empty or data2.empty:
            logger.warning("평균 차이 검정을 위한 데이터가 없습니다")
            return results
        
        # 공통 인덱스만 사용
        common_index = data1.index.intersection(data2.index)
        if len(common_index) == 0:
            logger.warning("공통 인덱스가 없습니다")
            return results
        
        x = data1.loc[common_index]
        y = data2.loc[common_index]
        
        # 1. 정규성 검정
        norm_tests_x = NormalityTester.test_normality(x, alpha)
        norm_tests_y = NormalityTester.test_normality(y, alpha)
        
        # 2. 독립 표본 t-검정 (정규분포인 경우)
        try:
            if any(test.p_value > alpha for test in norm_tests_x) and \
               any(test.p_value > alpha for test in norm_tests_y):
                
                t_stat, p_value = ttest_ind(x, y)
                result = StatisticalTestResult(
                    test_name="Independent t-test",
                    statistic=t_stat,
                    p_value=p_value,
                    conclusion="평균이 다름" if p_value < alpha else "평균이 같음",
                    interpretation=f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}"
                )
                results.append(result)
        except Exception as e:
            logger.error(f"독립 표본 t-검정 오류: {e}")
        
        # 3. Mann-Whitney U 검정 (비모수 검정)
        try:
            u_stat, p_value = mannwhitneyu(x, y, alternative='two-sided')
            result = StatisticalTestResult(
                test_name="Mann-Whitney U test",
                statistic=u_stat,
                p_value=p_value,
                conclusion="분포가 다름" if p_value < alpha else "분포가 같음",
                interpretation=f"U-statistic: {u_stat:.4f}, p-value: {p_value:.4f}"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Mann-Whitney U 검정 오류: {e}")
        
        return results
    
    @staticmethod
    def test_single_mean(data: pd.Series, expected_mean: float, 
                        alpha: float = 0.05) -> StatisticalTestResult:
        """단일 평균 검정"""
        if data.empty:
            logger.warning("단일 평균 검정을 위한 데이터가 없습니다")
            return StatisticalTestResult("", 0, 1, conclusion="데이터 없음")
        
        try:
            t_stat, p_value = ttest_1samp(data, expected_mean)
            result = StatisticalTestResult(
                test_name="One-sample t-test",
                statistic=t_stat,
                p_value=p_value,
                conclusion="기댓값과 다름" if p_value < alpha else "기댓값과 같음",
                interpretation=f"expected mean: {expected_mean:.4f}, "
                             f"sample mean: {data.mean():.4f}, "
                             f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}"
            )
            return result
        except Exception as e:
            logger.error(f"단일 평균 검정 오류: {e}")
            return StatisticalTestResult("", 0, 1, conclusion="오류 발생")

class RiskStatisticsCalculator:
    """리스크 통계 계산 클래스"""
    
    @staticmethod
    def calculate_var_cvar(returns: pd.Series, confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Dict]:
        """VaR 및 CVaR 계산"""
        results = {}
        
        if returns.empty:
            logger.warning("VaR/CVaR 계산을 위한 데이터가 없습니다")
            return results
        
        for confidence in confidence_levels:
            alpha = 1 - confidence
            
            # 1. 히스토리컬 VaR/CVaR
            var_hist = np.percentile(returns, alpha * 100)
            cvar_hist = returns[returns <= var_hist].mean()
            
            # 2. 파라메트릭 VaR/CVaR (정규분포 가정)
            mean_return = returns.mean()
            std_return = returns.std()
            var_param = norm.ppf(alpha, mean_return, std_return)
            cvar_param = mean_return - std_return * norm.pdf(norm.ppf(alpha)) / alpha
            
            # 3. 모멘트 VaR/CVaR (왜도, 첨도 고려)
            skewness = stats.skew(returns)
            kurtosis = stats.kurtosis(returns)
            
            # Cornish-Fisher 확장
            z_alpha = norm.ppf(alpha)
            z_cf = z_alpha + (z_alpha**2 - 1) * skewness / 6 + \
                   (z_alpha**3 - 3*z_alpha) * kurtosis / 24 - \
                   (2*z_alpha**3 - 5*z_alpha) * skewness**2 / 36
            
            var_cf = mean_return + std_return * z_cf
            cvar_cf = mean_return - std_return * (norm.pdf(z_cf) / alpha)
            
            results[f"{confidence*100:.0f}%"] = {
                'historical': {
                    'var': var_hist,
                    'cvar': cvar_hist
                },
                'parametric': {
                    'var': var_param,
                    'cvar': cvar_param
                },
                'cornish_fisher': {
                    'var': var_cf,
                    'cvar': cvar_cf
                },
                'statistics': {
                    'mean': mean_return,
                    'std': std_return,
                    'skewness': skewness,
                    'kurtosis': kurtosis
                }
            }
        
        return results
    
    @staticmethod
    def calculate_risk_metrics(returns: pd.Series) -> Dict[str, float]:
        """리스크 지표 계산"""
        if returns.empty:
            logger.warning("리스크 지표 계산을 위한 데이터가 없습니다")
            return {}
        
        # 기본 통계
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 고차 모멘트
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # VaR 및 CVaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        var_99 = np.percentile(returns, 1)
        cvar_99 = returns[returns <= var_99].mean()
        
        # 최대 낙폭
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 샤프 비율 (무위험 수익률 2% 가정)
        risk_free_rate = 0.02 / 252  # 일일 무위험 수익률
        sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
        
        # 소르티노 비율
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = (mean_return - risk_free_rate) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        # 칼마 비율
        calmar_ratio = (mean_return * 252) / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'mean_return': mean_return,
            'std_return': std_return,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'var_99': var_99,
            'cvar_99': cvar_99,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio
        }

class TimeSeriesAnalyzer:
    """시계열 분석 클래스"""
    
    @staticmethod
    def test_stationarity(data: pd.Series, alpha: float = 0.05) -> StatisticalTestResult:
        """정상성 검정 (ADF 테스트)"""
        if data.empty:
            logger.warning("정상성 검정을 위한 데이터가 없습니다")
            return StatisticalTestResult("", 0, 1, conclusion="데이터 없음")
        
        try:
            from statsmodels.tsa.stattools import adfuller
            
            result = adfuller(data.dropna())
            adf_statistic = result[0]
            p_value = result[1]
            critical_values = result[4]
            
            conclusion = "정상성" if p_value < alpha else "비정상성"
            
            return StatisticalTestResult(
                test_name="Augmented Dickey-Fuller",
                statistic=adf_statistic,
                p_value=p_value,
                critical_value=critical_values['5%'],
                conclusion=conclusion,
                interpretation=f"ADF statistic: {adf_statistic:.4f}, p-value: {p_value:.4f}"
            )
        except ImportError:
            logger.warning("statsmodels가 설치되지 않아 ADF 테스트를 수행할 수 없습니다")
            return StatisticalTestResult("", 0, 1, conclusion="라이브러리 없음")
        except Exception as e:
            logger.error(f"정상성 검정 오류: {e}")
            return StatisticalTestResult("", 0, 1, conclusion="오류 발생")
    
    @staticmethod
    def detect_autocorrelation(data: pd.Series, lags: int = 10) -> Dict[str, float]:
        """자기상관 검정"""
        if data.empty:
            logger.warning("자기상관 검정을 위한 데이터가 없습니다")
            return {}
        
        try:
            from statsmodels.tsa.stattools import acf, pacf
            
            # 자기상관함수 (ACF)
            acf_values = acf(data.dropna(), nlags=lags, fft=False)
            
            # 부분자기상관함수 (PACF)
            pacf_values = pacf(data.dropna(), nlags=lags)
            
            results = {}
            for i in range(1, lags + 1):
                results[f'acf_lag_{i}'] = acf_values[i]
                results[f'pacf_lag_{i}'] = pacf_values[i]
            
            return results
        except ImportError:
            logger.warning("statsmodels가 설치되지 않아 자기상관 분석을 수행할 수 없습니다")
            return {}
        except Exception as e:
            logger.error(f"자기상관 검정 오류: {e}")
            return {}

class StatisticalAnalyzer:
    """종합 통계 분석 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def comprehensive_analysis(self, trades_df: pd.DataFrame, 
                             account_df: pd.DataFrame) -> Dict[str, Any]:
        """종합 통계 분석 수행"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {},
            'normality_tests': {},
            'correlation_analysis': {},
            'risk_statistics': {},
            'time_series_analysis': {},
            'hypothesis_tests': {}
        }
        
        try:
            # 데이터 요약
            if not account_df.empty and 'daily_return_pct' in account_df.columns:
                daily_returns = account_df['daily_return_pct'].dropna()
                
                results['data_summary'] = {
                    'total_observations': len(daily_returns),
                    'mean': daily_returns.mean(),
                    'std': daily_returns.std(),
                    'min': daily_returns.min(),
                    'max': daily_returns.max(),
                    'skewness': stats.skew(daily_returns),
                    'kurtosis': stats.kurtosis(daily_returns)
                }
                
                # 정규성 검정
                normality_results = NormalityTester.test_normality(daily_returns)
                results['normality_tests']['daily_returns'] = [
                    {
                        'test_name': test.test_name,
                        'statistic': test.statistic,
                        'p_value': test.p_value,
                        'conclusion': test.conclusion
                    }
                    for test in normality_results
                ]
                
                # 리스크 통계
                results['risk_statistics'] = RiskStatisticsCalculator.calculate_risk_metrics(daily_returns)
                
                # VaR/CVaR 분석
                results['var_cvar_analysis'] = RiskStatisticsCalculator.calculate_var_cvar(daily_returns)
                
                # 시계열 분석
                stationarity_result = TimeSeriesAnalyzer.test_stationarity(daily_returns)
                results['time_series_analysis']['stationarity'] = {
                    'test_name': stationarity_result.test_name,
                    'statistic': stationarity_result.statistic,
                    'p_value': stationarity_result.p_value,
                    'conclusion': stationarity_result.conclusion
                }
                
                # 자기상관 분석
                autocorr_results = TimeSeriesAnalyzer.detect_autocorrelation(daily_returns)
                results['time_series_analysis']['autocorrelation'] = autocorr_results
            
            # 거래 데이터 분석
            if not trades_df.empty:
                sell_trades = trades_df[trades_df['side'] == 'SELL']
                if not sell_trades.empty:
                    pnl_data = sell_trades['pnl'].dropna()
                    
                    # P&L 정규성 검정
                    pnl_normality = NormalityTester.test_normality(pnl_data)
                    results['normality_tests']['pnl'] = [
                        {
                            'test_name': test.test_name,
                            'statistic': test.statistic,
                            'p_value': test.p_value,
                            'conclusion': test.conclusion
                        }
                        for test in pnl_normality
                    ]
                    
                    # P&L 평균이 0과 다른지 검정
                    pnl_mean_test = HypothesisTester.test_single_mean(pnl_data, 0)
                    results['hypothesis_tests']['pnl_mean'] = {
                        'test_name': pnl_mean_test.test_name,
                        'statistic': pnl_mean_test.statistic,
                        'p_value': pnl_mean_test.p_value,
                        'conclusion': pnl_mean_test.conclusion
                    }
            
            # 심볼별 상관관계 분석
            if not trades_df.empty:
                symbol_analysis = {}
                symbols = trades_df['symbol'].unique()
                
                for symbol in symbols:
                    symbol_trades = trades_df[trades_df['symbol'] == symbol]
                    if len(symbol_trades) > 10:  # 충분한 데이터가 있는 경우만
                        symbol_returns = symbol_trades['pnl'].dropna()
                        if len(symbol_returns) > 5:
                            symbol_analysis[symbol] = {
                                'count': len(symbol_returns),
                                'mean': symbol_returns.mean(),
                                'std': symbol_returns.std(),
                                'normality': [
                                    {
                                        'test_name': test.test_name,
                                        'p_value': test.p_value,
                                        'conclusion': test.conclusion
                                    }
                                    for test in NormalityTester.test_normality(symbol_returns)
                                ]
                            }
                
                results['symbol_analysis'] = symbol_analysis
            
            self.logger.info("종합 통계 분석 완료")
            
        except Exception as e:
            self.logger.error(f"통계 분석 오류: {e}")
            results['error'] = str(e)
        
        return results
    
    def generate_statistical_report(self, analysis_results: Dict[str, Any]) -> str:
        """통계 분석 리포트 생성"""
        report = f"""
=== 자동매매 통계 분석 리포트 ===
생성 시간: {analysis_results.get('timestamp', 'N/A')}

📊 데이터 요약
"""
        
        data_summary = analysis_results.get('data_summary', {})
        if data_summary:
            report += f"""
- 관측치 수: {data_summary.get('total_observations', 0):,}개
- 평균: {data_summary.get('mean', 0):.4f}%
- 표준편차: {data_summary.get('std', 0):.4f}%
- 최소값: {data_summary.get('min', 0):.4f}%
- 최대값: {data_summary.get('max', 0):.4f}%
- 왜도: {data_summary.get('skewness', 0):.4f}
- 첨도: {data_summary.get('kurtosis', 0):.4f}
"""
        
        # 정규성 검정 결과
        normality_tests = analysis_results.get('normality_tests', {})
        if normality_tests:
            report += "\n🔍 정규성 검정 결과\n"
            for data_type, tests in normality_tests.items():
                report += f"\n{data_type.upper()}:\n"
                for test in tests:
                    report += f"- {test['test_name']}: {test['conclusion']} (p-value: {test['p_value']:.4f})\n"
        
        # 리스크 통계
        risk_stats = analysis_results.get('risk_statistics', {})
        if risk_stats:
            report += "\n⚠️ 리스크 통계\n"
            report += f"- 샤프 비율: {risk_stats.get('sharpe_ratio', 0):.4f}\n"
            report += f"- 소르티노 비율: {risk_stats.get('sortino_ratio', 0):.4f}\n"
            report += f"- 칼마 비율: {risk_stats.get('calmar_ratio', 0):.4f}\n"
            report += f"- 최대 낙폭: {risk_stats.get('max_drawdown', 0):.4f}\n"
            report += f"- VaR (95%): {risk_stats.get('var_95', 0):.4f}\n"
            report += f"- CVaR (95%): {risk_stats.get('cvar_95', 0):.4f}\n"
        
        # 시계열 분석
        ts_analysis = analysis_results.get('time_series_analysis', {})
        if ts_analysis:
            report += "\n📈 시계열 분석\n"
            stationarity = ts_analysis.get('stationarity', {})
            if stationarity:
                report += f"- 정상성: {stationarity.get('conclusion', 'N/A')} (ADF p-value: {stationarity.get('p_value', 0):.4f})\n"
        
        # 가설 검정
        hypothesis_tests = analysis_results.get('hypothesis_tests', {})
        if hypothesis_tests:
            report += "\n🧪 가설 검정\n"
            for test_name, test_result in hypothesis_tests.items():
                report += f"- {test_result.get('test_name', test_name)}: {test_result.get('conclusion', 'N/A')} (p-value: {test_result.get('p_value', 0):.4f})\n"
        
        return report.strip()

# 사용 예시
if __name__ == "__main__":
    from data_processor import TradingDataProcessor, DataConfig
    
    # 설정 및 데이터 로드
    config = DataConfig()
    processor = TradingDataProcessor(config)
    
    trades = processor.load_trade_data()
    account = processor.load_account_history()
    
    if not trades.empty and not account.empty:
        # 데이터 전처리
        processed_trades = processor.preprocess_trade_data(trades)
        processed_account = processor.preprocess_account_data(account)
        
        # 통계 분석
        analyzer = StatisticalAnalyzer()
        analysis_results = analyzer.comprehensive_analysis(processed_trades, processed_account)
        
        # 리포트 생성
        report = analyzer.generate_statistical_report(analysis_results)
        print(report)
        
        # 상세 결과 출력
        print("\n=== 상세 분석 결과 ===")
        for key, value in analysis_results.items():
            if key != 'timestamp':
                print(f"\n{key}:")
                print(value)
    else:
        print("분석할 데이터가 없습니다.")

