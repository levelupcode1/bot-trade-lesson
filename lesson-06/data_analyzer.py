#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from datetime import datetime, timedelta
import os
import glob
import json
from typing import List, Dict, Any, Optional
import logging

# 한글 폰트 설정
def setup_korean_font():
    """한글 폰트 설정"""
    try:
        # Windows에서 사용 가능한 한글 폰트 찾기
        font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        korean_fonts = []
        
        # 한글 폰트 우선순위
        preferred_fonts = ['Malgun Gothic', '맑은 고딕', 'Gulim', '굴림', 'Dotum', '돋움', 
                          'Batang', '바탕', 'Gungsuh', '궁서']
        
        # 시스템 폰트에서 한글 폰트 찾기
        for font_path in font_list:
            try:
                font_prop = fm.FontProperties(fname=font_path)
                font_name = font_prop.get_name()
                if any(keyword in font_name for keyword in preferred_fonts):
                    korean_fonts.append(font_name)
            except:
                continue
        
        # 우선순위에 따라 폰트 선택
        selected_font = None
        for preferred in preferred_fonts:
            if preferred in korean_fonts:
                selected_font = preferred
                break
        
        if selected_font:
            plt.rcParams['font.family'] = selected_font
            plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
            print(f"✅ 한글 폰트 설정 완료: {selected_font}")
        else:
            # 기본 폰트로 설정
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            print("⚠️  한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            
    except Exception as e:
        print(f"⚠️  폰트 설정 중 오류: {e}")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False

# 한글 폰트 설정 실행
setup_korean_font()

class RealtimeDataAnalyzer:
    """
    실시간 수집된 데이터 분석 클래스
    
    주요 기능:
    - CSV/JSON 데이터 로드
    - 기본 통계 분석
    - 가격 차트 생성
    - 변동성 분석
    - 상관관계 분석
    """
    
    def __init__(self, data_dir: str = "realtime_data"):
        """
        초기화
        
        Args:
            data_dir (str): 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.data = None
        self.setup_logging()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, file_pattern: str = "realtime_data_*.csv") -> pd.DataFrame:
        """
        데이터 파일 로드
        
        Args:
            file_pattern (str): 파일 패턴
            
        Returns:
            pd.DataFrame: 로드된 데이터
        """
        try:
            # 파일 경로 찾기
            file_paths = glob.glob(os.path.join(self.data_dir, file_pattern))
            
            if not file_paths:
                self.logger.warning(f"데이터 파일을 찾을 수 없습니다: {file_pattern}")
                return pd.DataFrame()
            
            # 데이터 로드
            dataframes = []
            for file_path in file_paths:
                try:
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    elif file_path.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        df = pd.DataFrame(data)
                    else:
                        continue
                    
                    dataframes.append(df)
                    self.logger.info(f"데이터 로드 완료: {file_path} ({len(df)}개 레코드)")
                    
                except Exception as e:
                    self.logger.error(f"파일 로드 오류 {file_path}: {e}")
                    continue
            
            if dataframes:
                # 데이터 병합
                self.data = pd.concat(dataframes, ignore_index=True)
                
                # 타임스탬프 변환
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
                self.data = self.data.sort_values('timestamp')
                
                self.logger.info(f"총 {len(self.data)}개 레코드 로드 완료")
                return self.data
            else:
                self.logger.error("로드할 수 있는 데이터가 없습니다.")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"데이터 로드 오류: {e}")
            return pd.DataFrame()
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """기본 통계 정보 반환"""
        if self.data is None or self.data.empty:
            return {}
        
        stats = {}
        
        # 마켓별 통계
        for market in self.data['market'].unique():
            market_data = self.data[self.data['market'] == market]
            
            stats[market] = {
                'count': len(market_data),
                'price_range': {
                    'min': market_data['trade_price'].min(),
                    'max': market_data['trade_price'].max(),
                    'mean': market_data['trade_price'].mean(),
                    'std': market_data['trade_price'].std()
                },
                'volume_range': {
                    'min': market_data['trade_volume'].min(),
                    'max': market_data['trade_volume'].max(),
                    'mean': market_data['trade_volume'].mean(),
                    'std': market_data['trade_volume'].std()
                },
                'change_rate_range': {
                    'min': market_data['signed_change_rate'].min(),
                    'max': market_data['signed_change_rate'].max(),
                    'mean': market_data['signed_change_rate'].mean(),
                    'std': market_data['signed_change_rate'].std()
                }
            }
        
        return stats
    
    def create_price_chart(self, market: str, save_path: str = None) -> None:
        """
        가격 차트 생성
        
        Args:
            market (str): 마켓 코드
            save_path (str): 저장 경로
        """
        if self.data is None or self.data.empty:
            self.logger.error("데이터가 없습니다.")
            return
        
        market_data = self.data[self.data['market'] == market].copy()
        
        if market_data.empty:
            self.logger.error(f"마켓 데이터가 없습니다: {market}")
            return
        
        # 한글 폰트 재설정
        setup_korean_font()
        
        # 차트 생성
        try:
            plt.figure(figsize=(15, 8))
            
            # 가격 차트
            plt.subplot(2, 1, 1)
            plt.plot(market_data['timestamp'], market_data['trade_price'], 
                    linewidth=1, alpha=0.8)
            plt.title(f'{market} 실시간 가격', fontsize=14, fontweight='bold')
            plt.ylabel('가격 (원)')
            plt.grid(True, alpha=0.3)
            
            # 거래량 차트
            plt.subplot(2, 1, 2)
            plt.bar(market_data['timestamp'], market_data['trade_volume'], 
                   alpha=0.7, width=0.001)
            plt.title(f'{market} 거래량', fontsize=14, fontweight='bold')
            plt.ylabel('거래량')
            plt.xlabel('시간')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"차트 저장: {save_path}")
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"차트 생성 오류: {e}")
            print(f"❌ 차트 생성 중 오류 발생: {e}")
        finally:
            plt.close('all')  # 메모리 정리
    
    def create_correlation_heatmap(self, save_path: str = None) -> None:
        """
        가격 상관관계 히트맵 생성
        
        Args:
            save_path (str): 저장 경로
        """
        if self.data is None or self.data.empty:
            self.logger.error("데이터가 없습니다.")
            return
        
        # 한글 폰트 재설정
        setup_korean_font()
        
        # 피벗 테이블 생성 (마켓별 가격)
        price_pivot = self.data.pivot_table(
            index='timestamp', 
            columns='market', 
            values='trade_price'
        )
        
        # 상관관계 계산
        correlation = price_pivot.corr()
        
        # 히트맵 생성
        try:
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0,
                       square=True, fmt='.3f')
            plt.title('암호화폐 가격 상관관계', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"상관관계 차트 저장: {save_path}")
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"히트맵 생성 오류: {e}")
            print(f"❌ 히트맵 생성 중 오류 발생: {e}")
        finally:
            plt.close('all')  # 메모리 정리
    
    def analyze_volatility(self, market: str) -> Dict[str, float]:
        """
        변동성 분석
        
        Args:
            market (str): 마켓 코드
            
        Returns:
            Dict[str, float]: 변동성 지표
        """
        if self.data is None or self.data.empty:
            return {}
        
        market_data = self.data[self.data['market'] == market].copy()
        
        if market_data.empty:
            return {}
        
        # 가격 변화율 계산
        market_data['price_change'] = market_data['trade_price'].pct_change()
        
        # 변동성 지표 계산
        volatility = {
            'daily_volatility': market_data['price_change'].std() * np.sqrt(24 * 60),  # 일일 변동성
            'max_change': market_data['signed_change_rate'].max(),
            'min_change': market_data['signed_change_rate'].min(),
            'avg_abs_change': abs(market_data['signed_change_rate']).mean(),
            'volatility_ratio': market_data['price_change'].std() / market_data['trade_price'].mean()
        }
        
        return volatility
    
    def get_market_summary(self) -> pd.DataFrame:
        """마켓별 요약 정보 반환"""
        if self.data is None or self.data.empty:
            return pd.DataFrame()
        
        summary = self.data.groupby('market').agg({
            'trade_price': ['count', 'min', 'max', 'mean', 'std'],
            'trade_volume': ['sum', 'mean'],
            'signed_change_rate': ['min', 'max', 'mean', 'std']
        }).round(2)
        
        # 컬럼명 정리
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        
        return summary
    
    def export_analysis_report(self, output_path: str = "analysis_report.html") -> None:
        """분석 보고서 HTML로 내보내기"""
        if self.data is None or self.data.empty:
            self.logger.error("데이터가 없습니다.")
            return
        
        try:
            # 기본 통계
            stats = self.get_basic_statistics()
            
            # 마켓별 요약
            summary = self.get_market_summary()
            
            # HTML 보고서 생성
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>실시간 데이터 분석 보고서</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .stats {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <h1>실시간 암호화폐 데이터 분석 보고서</h1>
                <p>생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>데이터 개요</h2>
                <div class="stats">
                    <p><strong>총 레코드 수:</strong> {len(self.data):,}개</p>
                    <p><strong>수집 기간:</strong> {self.data['timestamp'].min()} ~ {self.data['timestamp'].max()}</p>
                    <p><strong>분석 마켓:</strong> {', '.join(self.data['market'].unique())}</p>
                </div>
                
                <h2>마켓별 요약 통계</h2>
                {summary.to_html(classes='table', escape=False)}
                
                <h2>상세 통계</h2>
            """
            
            # 마켓별 상세 통계 추가
            for market, market_stats in stats.items():
                html_content += f"""
                <h3>{market}</h3>
                <div class="stats">
                    <p><strong>데이터 수:</strong> {market_stats['count']:,}개</p>
                    <p><strong>가격 범위:</strong> {market_stats['price_range']['min']:,.0f}원 ~ {market_stats['price_range']['max']:,.0f}원</p>
                    <p><strong>평균 가격:</strong> {market_stats['price_range']['mean']:,.0f}원</p>
                    <p><strong>가격 표준편차:</strong> {market_stats['price_range']['std']:,.0f}원</p>
                    <p><strong>변동률 범위:</strong> {market_stats['change_rate_range']['min']:.2%} ~ {market_stats['change_rate_range']['max']:.2%}</p>
                    <p><strong>평균 변동률:</strong> {market_stats['change_rate_range']['mean']:.2%}</p>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"분석 보고서 저장: {output_path}")
            
        except Exception as e:
            self.logger.error(f"보고서 생성 오류: {e}")

# 사용 예시
def main():
    """데이터 분석 예시"""
    try:
        print("📊 실시간 데이터 분석을 시작합니다...")
        
        # 분석기 생성
        analyzer = RealtimeDataAnalyzer("realtime_data")
        
        # 데이터 로드
        print("📁 데이터 로드 중...")
        data = analyzer.load_data()
        
        if data.empty:
            print("❌ 분석할 데이터가 없습니다.")
            print("먼저 realtime_price_collector.py를 실행하여 데이터를 수집하세요.")
            return
        
        print(f"✅ {len(data)}개 레코드 로드 완료")
        
        # 기본 통계 출력
        print("\n📈 기본 통계:")
        stats = analyzer.get_basic_statistics()
        for market, market_stats in stats.items():
            print(f"\n{market}:")
            print(f"  데이터 수: {market_stats['count']:,}개")
            print(f"  가격 범위: {market_stats['price_range']['min']:,.0f}원 ~ {market_stats['price_range']['max']:,.0f}원")
            print(f"  평균 가격: {market_stats['price_range']['mean']:,.0f}원")
            print(f"  변동률 범위: {market_stats['change_rate_range']['min']:.2%} ~ {market_stats['change_rate_range']['max']:.2%}")
        
        # 마켓별 요약 테이블
        print("\n📋 마켓별 요약:")
        summary = analyzer.get_market_summary()
        print(summary)
        
        # 변동성 분석
        print("\n📊 변동성 분석:")
        for market in data['market'].unique():
            volatility = analyzer.analyze_volatility(market)
            if volatility:
                print(f"\n{market}:")
                print(f"  일일 변동성: {volatility['daily_volatility']:.2%}")
                print(f"  최대 변동률: {volatility['max_change']:.2%}")
                print(f"  최소 변동률: {volatility['min_change']:.2%}")
                print(f"  평균 절대 변동률: {volatility['avg_abs_change']:.2%}")
        
        # 차트 생성 (첫 번째 마켓)
        first_market = data['market'].iloc[0]
        print(f"\n📈 {first_market} 가격 차트 생성 중...")
        analyzer.create_price_chart(first_market, f"price_chart_{first_market}.png")
        
        # 상관관계 히트맵
        print("🔗 가격 상관관계 히트맵 생성 중...")
        analyzer.create_correlation_heatmap("correlation_heatmap.png")
        
        # 분석 보고서 생성
        print("📄 분석 보고서 생성 중...")
        analyzer.export_analysis_report("analysis_report.html")
        
        print("\n✅ 모든 분석이 완료되었습니다!")
        print("생성된 파일:")
        print("- price_chart_*.png: 가격 차트")
        print("- correlation_heatmap.png: 상관관계 히트맵")
        print("- analysis_report.html: 분석 보고서")
        
    except Exception as e:
        print(f"❌ 분석 오류: {e}")

if __name__ == "__main__":
    main()
