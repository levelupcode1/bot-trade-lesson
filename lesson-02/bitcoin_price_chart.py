#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matplotlib을 사용한 비트코인 가격 차트 생성
CoinGecko API에서 가격 데이터를 수집하고 시간-가격 선 그래프를 생성합니다.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import numpy as np

class BitcoinPriceChart:
    def __init__(self):
        """비트코인 가격 차트 생성기 초기화"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # matplotlib 한글 폰트 설정
        self.setup_korean_font()
        
        # 차트 스타일 설정
        plt.style.use('seaborn-v0_8')
        
    def setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            # Windows 기본 한글 폰트 설정
            font_path = 'C:/Windows/Fonts/malgun.ttf'  # 맑은 고딕
            if not font_manager.findfont(font_manager.FontProperties(fname=font_path)):
                # 맑은 고딕이 없으면 기본 폰트 사용
                plt.rcParams['font.family'] = 'DejaVu Sans'
            else:
                font_prop = font_manager.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                
            print("한글 폰트가 설정되었습니다.")
        except Exception as e:
            print(f"한글 폰트 설정 중 오류: {e}")
            print("기본 폰트를 사용합니다.")
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def get_bitcoin_price_history(self, days: int = 30, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """
        비트코인의 과거 가격 데이터를 조회합니다.
        
        Args:
            days: 조회할 일수 (기본값: 30일)
            currency: 통화 (기본값: "krw")
            
        Returns:
            (시간, 가격) 튜플의 리스트 또는 None (오류 시)
        """
        try:
            endpoint = "/coins/bitcoin/market_chart"
            params = {
                "vs_currency": currency,
                "days": days,
                "interval": "daily"
            }
            
            print(f"비트코인 {days}일 가격 데이터 조회 중... (통화: {currency.upper()})")
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "prices" in data and data["prices"]:
                    # 가격 데이터 파싱
                    price_data = []
                    for timestamp_ms, price in data["prices"]:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        price_data.append((dt, price))
                    
                    print(f"총 {len(price_data)}개의 가격 데이터를 수집했습니다.")
                    return price_data
                else:
                    print("가격 데이터를 찾을 수 없습니다.")
                    return None
            else:
                print(f"API 요청 실패: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("요청 시간 초과")
            return None
        except requests.exceptions.RequestException as e:
            print(f"요청 오류: {e}")
            return None
        except Exception as e:
            print(f"데이터 조회 중 오류 발생: {e}")
            return None
    
    def get_current_bitcoin_price(self, currency: str = "krw") -> Optional[float]:
        """
        비트코인의 현재 가격을 조회합니다.
        
        Args:
            currency: 통화 (기본값: "krw")
            
        Returns:
            현재 가격 또는 None (오류 시)
        """
        try:
            endpoint = "/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": currency
            }
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "bitcoin" in data and currency in data["bitcoin"]:
                    return data["bitcoin"][currency]
            
            return None
            
        except Exception as e:
            print(f"현재 가격 조회 오류: {e}")
            return None
    
    def format_price(self, price: float, currency: str = "krw") -> str:
        """
        가격을 사용자 친화적인 형식으로 포맷팅합니다.
        
        Args:
            price: 가격
            currency: 통화
            
        Returns:
            포맷팅된 가격 문자열
        """
        if currency.lower() == "krw":
            if price >= 1000000:
                return f"{price/1000000:.1f}백만원"
            elif price >= 1000:
                return f"{price/1000:.1f}천원"
            else:
                return f"{price:,.0f}원"
        elif currency.lower() == "usd":
            if price >= 1000000:
                return f"${price/1000000:.1f}M"
            elif price >= 1000:
                return f"${price/1000:.1f}K"
            else:
                return f"${price:,.2f}"
        else:
            return f"{price:,.2f} {currency.upper()}"
    
    def create_price_chart(self, price_data: List[Tuple[datetime, float]], 
                          currency: str = "krw", days: int = 30):
        """
        비트코인 가격 차트를 생성합니다.
        
        Args:
            price_data: (시간, 가격) 튜플의 리스트
            currency: 통화
            days: 조회한 일수
        """
        if not price_data:
            print("차트를 그릴 데이터가 없습니다.")
            return
        
        # 데이터 분리
        dates = [item[0] for item in price_data]
        prices = [item[1] for item in price_data]
        
        # 현재 가격 조회
        current_price = self.get_current_bitcoin_price(currency)
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 선 그래프 그리기
        line = ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                      marker='o', markersize=4, markerfacecolor='white', 
                      markeredgecolor='#f7931a', markeredgewidth=1.5)
        
        # 현재 가격 강조 표시
        if current_price:
            ax.axhline(y=current_price, color='red', linestyle='--', alpha=0.7, 
                      linewidth=1.5, label=f'현재 가격: {self.format_price(current_price, currency)}')
        
        # 최고가/최저가 표시
        max_price = max(prices)
        min_price = min(prices)
        max_date = dates[prices.index(max_price)]
        min_date = dates[prices.index(min_price)]
        
        # 최고가 포인트
        ax.scatter(max_date, max_price, color='red', s=100, zorder=5, 
                  label=f'최고가: {self.format_price(max_price, currency)}')
        ax.annotate(f'최고가\n{self.format_price(max_price, currency)}', 
                   xy=(max_date, max_price), xytext=(10, 10),
                   textcoords='offset points', ha='left', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                   fontsize=10, color='white', weight='bold')
        
        # 최저가 포인트
        ax.scatter(min_date, min_price, color='blue', s=100, zorder=5,
                  label=f'최저가: {self.format_price(min_price, currency)}')
        ax.annotate(f'최저가\n{self.format_price(min_price, currency)}', 
                   xy=(min_date, min_price), xytext=(10, -10),
                   textcoords='offset points', ha='left', va='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   fontsize=10, color='white', weight='bold')
        
        # 차트 스타일링
        ax.set_title(f'비트코인 가격 변동 추이 ({days}일)', 
                    fontsize=20, fontweight='bold', pad=20, color='#2c3e50')
        
        # x축 설정
        ax.set_xlabel('날짜', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # y축 설정
        ax.set_ylabel(f'가격 ({currency.upper()})', fontsize=14, fontweight='bold', color='#2c3e50')
        
        # 그리드 설정
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # 범례 설정
        ax.legend(loc='upper left', fontsize=12, framealpha=0.9)
        
        # 통계 정보 추가
        price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
        change_symbol = "📈" if price_change >= 0 else "📉"
        change_color = 'green' if price_change >= 0 else 'red'
        
        stats_text = f"""
        📊 통계 정보
        • 시작 가격: {self.format_price(prices[0], currency)}
        • 현재 가격: {self.format_price(prices[-1], currency)}
        • {days}일 변화율: {change_symbol} {price_change:+.2f}%
        • 최고가: {self.format_price(max_price, currency)}
        • 최저가: {self.format_price(min_price, currency)}
        • 평균 가격: {self.format_price(np.mean(prices), currency)}
        """
        
        # 통계 정보를 차트 우측에 표시
        ax.text(0.98, 0.02, stats_text, transform=ax.transAxes, 
               fontsize=11, verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8),
               fontfamily='monospace')
        
        # 배경색 설정
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
        
        # 레이아웃 조정
        plt.tight_layout()
        
        # 차트 표시
        plt.show()
        
        # 차트 저장
        filename = f"bitcoin_price_chart_{currency}_{days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"차트가 '{filename}' 파일로 저장되었습니다.")
        
        return fig
    
    def create_multiple_currency_chart(self, currencies: List[str] = ["krw", "usd"], days: int = 30):
        """
        여러 통화의 비트코인 가격을 비교하는 차트를 생성합니다.
        
        Args:
            currencies: 비교할 통화 리스트
            days: 조회할 일수
        """
        fig, ax = plt.subplots(figsize=(16, 10))
        
        colors = ['#f7931a', '#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
        
        for i, currency in enumerate(currencies):
            price_data = self.get_bitcoin_price_history(days, currency)
            if price_data:
                dates = [item[0] for item in price_data]
                prices = [item[1] for item in price_data]
                
                # 가격을 첫 번째 가격 대비 상대적 변화율로 정규화
                normalized_prices = [(price / prices[0]) * 100 for price in prices]
                
                ax.plot(dates, normalized_prices, linewidth=2.5, 
                       color=colors[i % len(colors)], marker='o', markersize=3,
                       label=f'{currency.upper()} (기준: 100%)')
        
        ax.set_title(f'비트코인 가격 변화율 비교 ({days}일)', 
                    fontsize=20, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_xlabel('날짜', fontsize=14, fontweight='bold')
        ax.set_ylabel('상대적 변화율 (%)', fontsize=14, fontweight='bold')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=12)
        
        plt.tight_layout()
        plt.show()

def main():
    """메인 함수"""
    print("=" * 70)
    print("matplotlib을 사용한 비트코인 가격 차트 생성 프로그램")
    print("=" * 70)
    
    # 차트 생성기 초기화
    chart_generator = BitcoinPriceChart()
    
    try:
        # 사용자 입력 받기
        print("\n📊 차트 옵션을 선택하세요:")
        print("1. 단일 통화 가격 차트 (기본: KRW, 30일)")
        print("2. 다중 통화 비교 차트")
        print("3. 사용자 정의 설정")
        
        choice = input("\n선택 (1-3, 기본값: 1): ").strip() or "1"
        
        if choice == "1":
            # 기본 차트 생성
            print("\n🔄 기본 차트 생성 중...")
            price_data = chart_generator.get_bitcoin_price_history(30, "krw")
            if price_data:
                chart_generator.create_price_chart(price_data, "krw", 30)
            else:
                print("❌ 데이터를 가져올 수 없습니다.")
                
        elif choice == "2":
            # 다중 통화 비교 차트
            print("\n🔄 다중 통화 비교 차트 생성 중...")
            chart_generator.create_multiple_currency_chart(["krw", "usd"], 30)
            
        elif choice == "3":
            # 사용자 정의 설정
            print("\n⚙️ 사용자 정의 설정")
            
            # 통화 선택
            currency = input("통화 (krw/usd/eur, 기본값: krw): ").strip().lower() or "krw"
            
            # 일수 선택
            try:
                days = int(input("조회할 일수 (1-365, 기본값: 30): ").strip() or "30")
                days = max(1, min(365, days))
            except ValueError:
                days = 30
                print(f"잘못된 입력으로 기본값 {days}일을 사용합니다.")
            
            print(f"\n🔄 {currency.upper()} 기준 {days}일 차트 생성 중...")
            price_data = chart_generator.get_bitcoin_price_history(days, currency)
            if price_data:
                chart_generator.create_price_chart(price_data, currency, days)
            else:
                print("❌ 데이터를 가져올 수 없습니다.")
        
        else:
            print("❌ 잘못된 선택입니다. 기본 차트를 생성합니다.")
            price_data = chart_generator.get_bitcoin_price_history(30, "krw")
            if price_data:
                chart_generator.create_price_chart(price_data, "krw", 30)
        
        print("\n✅ 프로그램이 성공적으로 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류가 발생했습니다: {e}")
    finally:
        print("\n👋 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
