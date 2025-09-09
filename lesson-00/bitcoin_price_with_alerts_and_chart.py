#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 실시간 표시 프로그램 (알림 및 그래프 기능 포함)
맛보기 강의용 개선된 예제 코드
"""

import requests
import json
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
from collections import deque
from plyer import notification
import threading

class BitcoinPriceMonitor:
    def __init__(self, max_data_points=50):
        """
        비트코인 가격 모니터 초기화
        
        Args:
            max_data_points (int): 그래프에 표시할 최대 데이터 포인트 수
        """
        self.max_data_points = max_data_points
        self.price_history = deque(maxlen=max_data_points)
        self.time_history = deque(maxlen=max_data_points)
        self.last_price = None
        self.price_increase_threshold = 0.5  # 0.5% 이상 상승 시 알림
        
        # 그래프 설정
        plt.ion()  # 인터랙티브 모드 활성화
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.ax.set_title('🚀 비트코인 실시간 가격 차트', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('시간', fontsize=12)
        self.ax.set_ylabel('가격 (USD)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        
        # 한글 폰트 설정 (Windows)
        try:
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'

    def get_bitcoin_price(self):
        """
        CoinGecko API를 사용하여 비트코인 현재 가격을 가져옵니다.
        
        Returns:
            dict: 가격 정보가 담긴 딕셔너리 또는 None (에러 시)
        """
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'bitcoin' in data:
                bitcoin_data = data['bitcoin']
                return {
                    'price': bitcoin_data.get('usd', 0),
                    'change_24h': bitcoin_data.get('usd_24h_change', 0)
                }
            else:
                print("❌ 비트코인 데이터를 찾을 수 없습니다.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 중 오류 발생: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return None

    def check_price_increase(self, current_price):
        """
        가격 상승을 확인하고 알림을 보냅니다.
        
        Args:
            current_price (float): 현재 가격
        """
        if self.last_price is not None:
            price_change = ((current_price - self.last_price) / self.last_price) * 100
            
            if price_change >= self.price_increase_threshold:
                self.send_notification(current_price, price_change)
        
        self.last_price = current_price

    def send_notification(self, price, change_percent):
        """
        가격 상승 알림을 보냅니다.
        
        Args:
            price (float): 현재 가격
            change_percent (float): 변동률
        """
        try:
            notification.notify(
                title="🚀 비트코인 가격 상승!",
                message=f"현재 가격: ${price:,.2f}\n상승률: +{change_percent:.2f}%",
                timeout=10
            )
            print(f"🔔 알림 발송: 가격이 {change_percent:.2f}% 상승했습니다!")
        except Exception as e:
            print(f"❌ 알림 발송 실패: {e}")

    def update_chart(self, price_data):
        """
        실시간 차트를 업데이트합니다.
        
        Args:
            price_data (dict): 가격 정보
        """
        if not price_data:
            return
        
        current_time = datetime.now()
        current_price = price_data['price']
        
        # 데이터 히스토리에 추가
        self.price_history.append(current_price)
        self.time_history.append(current_time)
        
        # 차트 업데이트
        self.ax.clear()
        self.ax.set_title('🚀 비트코인 실시간 가격 차트', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('시간', fontsize=12)
        self.ax.set_ylabel('가격 (USD)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        
        if len(self.price_history) > 1:
            # 가격 라인 그리기
            self.ax.plot(self.time_history, self.price_history, 
                        color='#f7931a', linewidth=2, marker='o', markersize=4)
            
            # 현재 가격 표시
            self.ax.axhline(y=current_price, color='red', linestyle='--', alpha=0.7)
            self.ax.text(0.02, 0.98, f'현재: ${current_price:,.2f}', 
                        transform=self.ax.transAxes, fontsize=12, 
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Y축 포맷팅
        self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # X축 시간 포맷팅
        if len(self.time_history) > 0:
            self.ax.set_xlim(self.time_history[0], self.time_history[-1])
        
        plt.tight_layout()
        plt.pause(0.1)  # 차트 업데이트

    def display_price_info(self, price_data):
        """
        가격 정보를 콘솔에 표시합니다.
        
        Args:
            price_data (dict): 가격 정보 딕셔너리
        """
        if not price_data:
            return
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price = price_data['price']
        change = price_data['change_24h']
        
        # 콘솔 화면 지우기
        print("\033[2J\033[H", end="")
        
        print("=" * 60)
        print("🚀 비트코인 실시간 가격 모니터 (알림 & 차트 포함)")
        print("=" * 60)
        print(f"⏰ 업데이트 시간: {current_time}")
        print(f"💰 현재 가격: ${price:,.2f}")
        print(f"📈 24시간 변동: {change:+.2f}%")
        print(f"🔔 알림 임계값: {self.price_increase_threshold}% 상승 시")
        print("=" * 60)
        print("💡 종료하려면 Ctrl+C를 누르세요")
        print("📊 차트 창을 확인하세요!")
        print()

    def run(self):
        """
        메인 실행 함수
        """
        print("🚀 비트코인 가격 실시간 모니터를 시작합니다...")
        print("📡 API에서 데이터를 가져오는 중...")
        print("📊 차트 창이 열립니다...")
        
        update_interval = 30  # 30초마다 업데이트
        
        try:
            while True:
                # 가격 정보 가져오기
                price_data = self.get_bitcoin_price()
                
                if price_data:
                    # 가격 상승 확인 및 알림
                    self.check_price_increase(price_data['price'])
                    
                    # 콘솔 정보 표시
                    self.display_price_info(price_data)
                    
                    # 차트 업데이트
                    self.update_chart(price_data)
                else:
                    print("❌ 가격 정보를 가져올 수 없습니다. 10초 후 다시 시도합니다...")
                    time.sleep(10)
                    continue
                
                # 다음 업데이트까지 대기
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다. 감사합니다!")
            plt.close('all')
        except Exception as e:
            print(f"\n❌ 프로그램 실행 중 오류 발생: {e}")
            plt.close('all')

def main():
    """
    메인 함수
    """
    monitor = BitcoinPriceMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
