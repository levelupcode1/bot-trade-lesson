#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 자동 업데이트 비트코인 가격 차트
1시간마다 자동으로 가격을 업데이트하고 그래프가 자동으로 바뀝니다.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation
import numpy as np
import os
import csv

class LiveBitcoinPriceChart:
    def __init__(self):
        """실시간 비트코인 가격 차트 생성기 초기화"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 데이터 저장소
        self.price_history = []  # (시간, 가격) 튜플의 리스트
        self.currency = "krw"
        self.update_interval = 3600  # 1시간 (초 단위)
        self.is_running = False
        self.data_lock = threading.Lock()
        
        # matplotlib 한글 폰트 설정
        self.setup_korean_font()
        
        # 차트 스타일 설정
        plt.style.use('seaborn-v0_8')
        
        # 데이터 파일 설정
        self.data_file = f"bitcoin_live_data_{datetime.now().strftime('%Y%m%d')}.csv"
        self.setup_data_file()
        
        # 초기 데이터 로드
        self.load_initial_data()
        
    def setup_data_file(self):
        """데이터 저장 파일 초기 설정"""
        try:
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'datetime', 'price', 'currency'])
                print(f"데이터 파일이 생성되었습니다: {self.data_file}")
        except Exception as e:
            print(f"데이터 파일 생성 오류: {e}")
    
    def save_price_data(self, timestamp: datetime, price: float):
        """가격 데이터를 CSV 파일에 저장"""
        try:
            with open(self.data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp.timestamp(),
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    price,
                    self.currency
                ])
        except Exception as e:
            print(f"데이터 저장 오류: {e}")
    
    def load_initial_data(self):
        """초기 데이터 로드 (최근 24시간)"""
        try:
            print("초기 데이터 로딩 중...")
            initial_data = self.get_bitcoin_price_history(1, self.currency)  # 1일
            if initial_data:
                with self.data_lock:
                    self.price_history = initial_data
                    # 데이터 저장
                    for timestamp, price in initial_data:
                        self.save_price_data(timestamp, price)
                print(f"초기 {len(initial_data)}개 데이터 로드 완료")
            else:
                # 초기 데이터가 없으면 현재 가격으로 시작
                current_price = self.get_current_bitcoin_price(self.currency)
                if current_price:
                    now = datetime.now()
                    with self.data_lock:
                        self.price_history = [(now, current_price)]
                        self.save_price_data(now, current_price)
                    print("현재 가격으로 초기화 완료")
        except Exception as e:
            print(f"초기 데이터 로드 오류: {e}")
    
    def setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            font_path = 'C:/Windows/Fonts/malgun.ttf'
            if not font_manager.findfont(font_manager.FontProperties(fname=font_path)):
                plt.rcParams['font.family'] = 'DejaVu Sans'
            else:
                font_prop = font_manager.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
            print("한글 폰트가 설정되었습니다.")
        except Exception as e:
            print(f"한글 폰트 설정 중 오류: {e}")
            plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def get_bitcoin_price_history(self, days: int = 1, currency: str = "krw") -> Optional[List[Tuple[datetime, float]]]:
        """비트코인의 과거 가격 데이터를 조회합니다."""
        try:
            endpoint = "/coins/bitcoin/market_chart"
            params = {
                "vs_currency": currency,
                "days": days,
                "interval": "hourly"
            }
            
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "prices" in data and data["prices"]:
                    price_data = []
                    for timestamp_ms, price in data["prices"]:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        price_data.append((dt, price))
                    
                    return price_data
            return None
                
        except Exception as e:
            print(f"가격 데이터 조회 오류: {e}")
            return None
    
    def get_current_bitcoin_price(self, currency: str = "krw") -> Optional[float]:
        """비트코인의 현재 가격을 조회합니다."""
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
    
    def update_price_data(self):
        """가격 데이터를 업데이트합니다."""
        try:
            current_price = self.get_current_bitcoin_price(self.currency)
            if current_price:
                now = datetime.now()
                
                with self.data_lock:
                    # 중복 데이터 방지 (1분 이내)
                    if (not self.price_history or 
                        (now - self.price_history[-1][0]).total_seconds() > 60):
                        
                        self.price_history.append((now, current_price))
                        self.save_price_data(now, current_price)
                        
                        # 최근 24시간 데이터만 유지
                        cutoff_time = now - timedelta(hours=24)
                        self.price_history = [
                            (t, p) for t, p in self.price_history 
                            if t > cutoff_time
                        ]
                        
                        print(f"[{now.strftime('%H:%M:%S')}] 가격 업데이트: {self.format_price(current_price, self.currency)}")
                    else:
                        print(f"[{now.strftime('%H:%M:%S')}] 업데이트 스킵 (최근 데이터 존재)")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 가격 조회 실패")
                
        except Exception as e:
            print(f"데이터 업데이트 오류: {e}")
    
    def format_price(self, price: float, currency: str = "krw") -> str:
        """가격을 사용자 친화적인 형식으로 포맷팅합니다."""
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
    
    def data_collection_worker(self):
        """백그라운드 데이터 수집 작업자"""
        while self.is_running:
            try:
                self.update_price_data()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"데이터 수집 작업자 오류: {e}")
                time.sleep(60)  # 오류 시 1분 후 재시도
    
    def start_data_collection(self):
        """데이터 수집을 시작합니다."""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self.data_collection_worker, daemon=True)
            self.collection_thread.start()
            print("자동 데이터 수집이 시작되었습니다.")
    
    def stop_data_collection(self):
        """데이터 수집을 중지합니다."""
        self.is_running = False
        print("자동 데이터 수집이 중지되었습니다.")
    
    def create_live_chart(self):
        """실시간 업데이트 차트를 생성합니다."""
        # 차트 초기화
        self.fig, self.ax = plt.subplots(figsize=(16, 10))
        self.fig.suptitle('실시간 비트코인 가격 차트 (1시간마다 자동 업데이트)', 
                         fontsize=16, fontweight='bold')
        
        # 애니메이션 함수
        def animate(frame):
            try:
                with self.data_lock:
                    if self.price_history:
                        # 데이터 분리
                        dates = [item[0] for item in self.price_history]
                        prices = [item[1] for item in self.price_history]
                        
                        # 차트 클리어
                        self.ax.clear()
                        
                        # 선 그래프 그리기
                        self.ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                                   marker='o', markersize=4, markerfacecolor='white', 
                                   markeredgecolor='#f7931a', markeredgewidth=1.5)
                        
                        # 현재 가격 강조 표시
                        if prices:
                            current_price = prices[-1]
                            self.ax.axhline(y=current_price, color='red', linestyle='--', 
                                          alpha=0.7, linewidth=1.5, 
                                          label=f'현재 가격: {self.format_price(current_price, self.currency)}')
                        
                        # 최고가/최저가 표시
                        if len(prices) > 1:
                            max_price = max(prices)
                            min_price = min(prices)
                            max_date = dates[prices.index(max_price)]
                            min_date = dates[prices.index(min_price)]
                            
                            # 최고가 포인트
                            self.ax.scatter(max_date, max_price, color='red', s=100, zorder=5,
                                          label=f'최고가: {self.format_price(max_price, self.currency)}')
                            
                            # 최저가 포인트
                            self.ax.scatter(min_date, min_price, color='blue', s=100, zorder=5,
                                          label=f'최저가: {self.format_price(min_price, self.currency)}')
                        
                        # 차트 스타일링
                        self.ax.set_title(f'비트코인 실시간 가격 변동 (통화: {self.currency.upper()})', 
                                        fontsize=14, fontweight='bold', pad=20)
                        
                        # x축 설정
                        self.ax.set_xlabel('시간', fontsize=12, fontweight='bold')
                        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                        
                        # y축 설정
                        self.ax.set_ylabel(f'가격 ({self.currency.upper()})', fontsize=12, fontweight='bold')
                        
                        # 그리드 설정
                        self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                        self.ax.set_axisbelow(True)
                        
                        # 범례 설정
                        self.ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
                        
                        # 통계 정보 추가
                        if len(prices) > 1:
                            price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
                            change_symbol = "📈" if price_change >= 0 else "📉"
                            
                            stats_text = f"""
                            📊 실시간 통계
                            • 시작 가격: {self.format_price(prices[0], self.currency)}
                            • 현재 가격: {self.format_price(prices[-1], self.currency)}
                            • 변화율: {change_symbol} {price_change:+.2f}%
                            • 데이터 포인트: {len(prices)}개
                            • 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}
                            """
                            
                            self.ax.text(0.98, 0.02, stats_text, transform=self.ax.transAxes,
                                       fontsize=10, verticalalignment='bottom', 
                                       horizontalalignment='right',
                                       bbox=dict(boxstyle='round,pad=0.5', 
                                               facecolor='lightgray', alpha=0.8),
                                       fontfamily='monospace')
                        
                        # 배경색 설정
                        self.ax.set_facecolor('#f8f9fa')
                        self.fig.patch.set_facecolor('white')
                        
                        # 레이아웃 조정
                        self.fig.tight_layout()
                        
            except Exception as e:
                print(f"차트 업데이트 오류: {e}")
        
        # 애니메이션 시작
        self.ani = FuncAnimation(self.fig, animate, interval=5000, blit=False)  # 5초마다 업데이트
        
        # 차트 표시
        plt.show()
        
        return self.fig
    
    def create_manual_chart(self):
        """수동으로 차트를 생성합니다."""
        with self.data_lock:
            if not self.price_history:
                print("표시할 데이터가 없습니다.")
                return None
            
            # 데이터 분리
            dates = [item[0] for item in self.price_history]
            prices = [item[1] for item in self.price_history]
            
            # 차트 생성
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # 선 그래프 그리기
            ax.plot(dates, prices, linewidth=2.5, color='#f7931a', 
                   marker='o', markersize=4, markerfacecolor='white', 
                   markeredgecolor='#f7931a', markeredgewidth=1.5)
            
            # 차트 스타일링
            ax.set_title(f'비트코인 가격 변동 (수동 생성)', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('시간', fontsize=12, fontweight='bold')
            ax.set_ylabel(f'가격 ({self.currency.upper()})', fontsize=12, fontweight='bold')
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
            return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("실시간 자동 업데이트 비트코인 가격 차트 프로그램")
    print("=" * 80)
    
    # 실시간 차트 생성기 초기화
    live_chart = LiveBitcoinPriceChart()
    
    try:
        print("\n📊 차트 옵션을 선택하세요:")
        print("1. 실시간 자동 업데이트 차트 (1시간마다 자동 갱신)")
        print("2. 수동 차트 생성 (현재 데이터로)")
        print("3. 데이터 수집만 시작 (백그라운드)")
        print("4. 설정 변경")
        
        choice = input("\n선택 (1-4, 기본값: 1): ").strip() or "1"
        
        if choice == "1":
            # 실시간 자동 업데이트 차트
            print("\n🔄 실시간 자동 업데이트 차트를 시작합니다...")
            print("💡 차트는 5초마다 자동으로 갱신됩니다.")
            print("💡 가격 데이터는 1시간마다 자동으로 수집됩니다.")
            print("💡 차트를 닫으면 프로그램이 종료됩니다.")
            
            # 데이터 수집 시작
            live_chart.start_data_collection()
            
            # 실시간 차트 생성
            live_chart.create_live_chart()
            
        elif choice == "2":
            # 수동 차트 생성
            print("\n🔄 수동 차트를 생성합니다...")
            live_chart.create_manual_chart()
            
        elif choice == "3":
            # 데이터 수집만 시작
            print("\n🔄 백그라운드 데이터 수집을 시작합니다...")
            print("💡 데이터는 1시간마다 자동으로 수집됩니다.")
            print("💡 프로그램을 종료하려면 Ctrl+C를 누르세요.")
            
            live_chart.start_data_collection()
            
            try:
                while True:
                    time.sleep(60)  # 1분마다 상태 출력
                    with live_chart.data_lock:
                        if live_chart.price_history:
                            latest = live_chart.price_history[-1]
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                                  f"최신 데이터: {latest[0].strftime('%H:%M:%S')} - "
                                  f"{live_chart.format_price(latest[1], live_chart.currency)}")
            except KeyboardInterrupt:
                print("\n⏹️ 사용자에 의해 중단되었습니다.")
                live_chart.stop_data_collection()
                
        elif choice == "4":
            # 설정 변경
            print("\n⚙️ 설정 변경")
            
            # 통화 변경
            new_currency = input(f"통화 (현재: {live_chart.currency}, krw/usd/eur): ").strip().lower()
            if new_currency in ['krw', 'usd', 'eur']:
                live_chart.currency = new_currency
                print(f"통화가 {new_currency.upper()}로 변경되었습니다.")
            
            # 업데이트 간격 변경
            try:
                new_interval = int(input(f"업데이트 간격 (현재: {live_chart.update_interval//60}분, 분 단위): ").strip())
                if new_interval > 0:
                    live_chart.update_interval = new_interval * 60
                    print(f"업데이트 간격이 {new_interval}분으로 변경되었습니다.")
            except ValueError:
                print("잘못된 입력입니다. 기존 설정을 유지합니다.")
        
        else:
            print("❌ 잘못된 선택입니다. 기본 옵션을 실행합니다.")
            live_chart.start_data_collection()
            live_chart.create_live_chart()
        
        print("\n✅ 프로그램이 성공적으로 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 프로그램이 중단되었습니다.")
        live_chart.stop_data_collection()
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류가 발생했습니다: {e}")
        live_chart.stop_data_collection()
    finally:
        print("\n👋 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
