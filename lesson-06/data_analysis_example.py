#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def analyze_realtime_data(data_file: str):
    """
    실시간 수집된 데이터 분석
    
    Args:
        data_file (str): 분석할 CSV 파일 경로
    """
    try:
        # 데이터 로드
        df = pd.read_csv(data_file)
        print(f"📊 데이터 로드 완료: {len(df)}개 레코드")
        
        # 기본 정보 출력
        print("\n=== 데이터 기본 정보 ===")
        print(f"수집 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        print(f"수집 마켓: {df['market'].unique()}")
        print(f"데이터 컬럼: {list(df.columns)}")
        
        # 마켓별 데이터 분석
        print("\n=== 마켓별 데이터 분석 ===")
        for market in df['market'].unique():
            market_data = df[df['market'] == market]
            print(f"\n{market}:")
            print(f"  - 데이터 수: {len(market_data)}개")
            print(f"  - 최고가: {market_data['high_price'].max():,.0f}원")
            print(f"  - 최저가: {market_data['low_price'].min():,.0f}원")
            print(f"  - 평균가: {market_data['trade_price'].mean():,.0f}원")
            print(f"  - 최대 변동률: {market_data['change_rate'].max():.2%}")
            print(f"  - 최소 변동률: {market_data['change_rate'].min():.2%}")
        
        return df
        
    except Exception as e:
        print(f"❌ 데이터 분석 오류: {e}")
        return None

def create_price_chart(df: pd.DataFrame, market: str, save_path: str = None):
    """
    가격 차트 생성
    
    Args:
        df (pd.DataFrame): 데이터프레임
        market (str): 차트를 그릴 마켓
        save_path (str): 차트 저장 경로 (선택사항)
    """
    try:
        # 특정 마켓 데이터 필터링
        market_data = df[df['market'] == market].copy()
        if market_data.empty:
            print(f"❌ {market} 데이터가 없습니다.")
            return
        
        # 시간 컬럼 변환
        market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
        market_data = market_data.sort_values('timestamp')
        
        # 차트 생성
        plt.figure(figsize=(15, 8))
        
        # 서브플롯 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 가격 차트
        ax1.plot(market_data['timestamp'], market_data['trade_price'], 
                linewidth=2, label='현재가', color='blue')
        ax1.plot(market_data['timestamp'], market_data['high_price'], 
                linewidth=1, label='고가', color='red', alpha=0.7)
        ax1.plot(market_data['timestamp'], market_data['low_price'], 
                linewidth=1, label='저가', color='green', alpha=0.7)
        
        ax1.set_title(f'{market} 실시간 가격 차트', fontsize=16, fontweight='bold')
        ax1.set_ylabel('가격 (원)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 변동률 차트
        ax2.plot(market_data['timestamp'], market_data['change_rate'] * 100, 
                linewidth=2, label='변동률', color='purple')
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title(f'{market} 변동률 차트', fontsize=16, fontweight='bold')
        ax2.set_xlabel('시간', fontsize=12)
        ax2.set_ylabel('변동률 (%)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # x축 레이블 회전
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 차트 저장
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 차트 저장 완료: {save_path}")
        
        plt.show()
        
    except Exception as e:
        print(f"❌ 차트 생성 오류: {e}")

def create_volume_analysis(df: pd.DataFrame, market: str):
    """
    거래량 분석
    
    Args:
        df (pd.DataFrame): 데이터프레임
        market (str): 분석할 마켓
    """
    try:
        market_data = df[df['market'] == market].copy()
        if market_data.empty:
            print(f"❌ {market} 데이터가 없습니다.")
            return
        
        # 시간 컬럼 변환
        market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
        market_data = market_data.sort_values('timestamp')
        
        # 거래량 차트
        plt.figure(figsize=(15, 6))
        plt.plot(market_data['timestamp'], market_data['trade_volume'], 
                linewidth=2, label='거래량', color='orange')
        
        plt.title(f'{market} 거래량 분석', fontsize=16, fontweight='bold')
        plt.xlabel('시간', fontsize=12)
        plt.ylabel('거래량', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        # 거래량 통계
        print(f"\n=== {market} 거래량 통계 ===")
        print(f"평균 거래량: {market_data['trade_volume'].mean():,.2f}")
        print(f"최대 거래량: {market_data['trade_volume'].max():,.2f}")
        print(f"최소 거래량: {market_data['trade_volume'].min():,.2f}")
        print(f"거래량 표준편차: {market_data['trade_volume'].std():,.2f}")
        
    except Exception as e:
        print(f"❌ 거래량 분석 오류: {e}")

def create_correlation_analysis(df: pd.DataFrame):
    """
    마켓 간 상관관계 분석
    
    Args:
        df (pd.DataFrame): 데이터프레임
    """
    try:
        # 마켓별 가격 데이터 피벗
        price_pivot = df.pivot_table(
            index='timestamp', 
            columns='market', 
            values='trade_price'
        )
        
        # 상관관계 계산
        correlation_matrix = price_pivot.corr()
        
        # 상관관계 히트맵
        plt.figure(figsize=(10, 8))
        plt.imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
        plt.colorbar()
        plt.title('마켓 간 가격 상관관계', fontsize=16, fontweight='bold')
        plt.xlabel('마켓', fontsize=12)
        plt.ylabel('마켓', fontsize=12)
        
        # 축 레이블 설정
        markets = correlation_matrix.columns
        plt.xticks(range(len(markets)), markets, rotation=45)
        plt.yticks(range(len(markets)), markets)
        
        # 상관계수 값 표시
        for i in range(len(markets)):
            for j in range(len(markets)):
                plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}', 
                        ha='center', va='center', fontsize=10)
        
        plt.tight_layout()
        plt.show()
        
        print("\n=== 마켓 간 상관관계 ===")
        print(correlation_matrix)
        
    except Exception as e:
        print(f"❌ 상관관계 분석 오류: {e}")

def export_summary_report(df: pd.DataFrame, output_file: str = "analysis_report.txt"):
    """
    분석 결과 요약 보고서 생성
    
    Args:
        df (pd.DataFrame): 데이터프레임
        output_file (str): 출력 파일명
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== 업비트 실시간 데이터 분석 보고서 ===\n\n")
            f.write(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"총 데이터 수: {len(df)}개\n")
            f.write(f"수집 마켓: {', '.join(df['market'].unique())}\n")
            f.write(f"수집 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}\n\n")
            
            f.write("=== 마켓별 요약 ===\n")
            for market in df['market'].unique():
                market_data = df[df['market'] == market]
                f.write(f"\n{market}:\n")
                f.write(f"  - 데이터 수: {len(market_data)}개\n")
                f.write(f"  - 최고가: {market_data['high_price'].max():,.0f}원\n")
                f.write(f"  - 최저가: {market_data['low_price'].min():,.0f}원\n")
                f.write(f"  - 평균가: {market_data['trade_price'].mean():,.0f}원\n")
                f.write(f"  - 최대 변동률: {market_data['change_rate'].max():.2%}\n")
                f.write(f"  - 최소 변동률: {market_data['change_rate'].min():.2%}\n")
                f.write(f"  - 평균 거래량: {market_data['trade_volume'].mean():,.2f}\n")
        
        print(f"📄 분석 보고서 생성 완료: {output_file}")
        
    except Exception as e:
        print(f"❌ 보고서 생성 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 업비트 실시간 데이터 분석 도구")
    print("=" * 50)
    
    # 데이터 파일 경로 설정
    data_dir = "realtime_data"
    today = datetime.now().strftime('%Y%m%d')
    data_file = f"{data_dir}/upbit_realtime_{today}.csv"
    
    # 데이터 파일 존재 확인
    if not os.path.exists(data_file):
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {data_file}")
        print("먼저 upbit_websocket_collector.py를 실행하여 데이터를 수집하세요.")
        return
    
    # 데이터 분석 실행
    df = analyze_realtime_data(data_file)
    if df is None:
        return
    
    # 비트코인 가격 차트 생성
    print("\n📊 비트코인 가격 차트 생성 중...")
    create_price_chart(df, 'KRW-BTC', f"{data_dir}/btc_price_chart_{today}.png")
    
    # 비트코인 거래량 분석
    print("\n📊 비트코인 거래량 분석 중...")
    create_volume_analysis(df, 'KRW-BTC')
    
    # 마켓 간 상관관계 분석
    print("\n📊 마켓 간 상관관계 분석 중...")
    create_correlation_analysis(df)
    
    # 분석 보고서 생성
    print("\n📄 분석 보고서 생성 중...")
    export_summary_report(df, f"{data_dir}/analysis_report_{today}.txt")
    
    print("\n✅ 모든 분석이 완료되었습니다!")

if __name__ == "__main__":
    main()
