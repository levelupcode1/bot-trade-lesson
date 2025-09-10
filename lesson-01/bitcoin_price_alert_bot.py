#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 5% 상승 시 알림을 보내는 봇
Upbit API를 사용하여 실시간 가격을 모니터링하고 matplotlib으로 그래프를 표시합니다.
"""

import requests
import time
import json
from datetime import datetime
import matplotlib
matplotlib.use('Qt5Agg')  # Qt5 백엔드 사용 (tkinter 대신)
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import threading

# 한글 폰트 설정
import matplotlib.font_manager as fm
import platform

def setup_korean_font():
    """한글 폰트를 설정합니다."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # macOS에서 사용 가능한 한글 폰트들
        korean_fonts = ['AppleGothic', 'Malgun Gothic', 'NanumGothic', 'Arial Unicode MS']
    elif system == "Windows":
        # Windows에서 사용 가능한 한글 폰트들
        korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Dotum', 'Batang']
    else:  # Linux
        # Linux에서 사용 가능한 한글 폰트들
        korean_fonts = ['NanumGothic', 'DejaVu Sans', 'Liberation Sans']
    
    # 사용 가능한 폰트 찾기
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    for font in korean_fonts:
        if font in available_fonts:
            plt.rcParams['font.family'] = font
            print(f"한글 폰트 설정: {font}")
            return font
    
    # 한글 폰트를 찾지 못한 경우 기본 설정
    plt.rcParams['font.family'] = 'DejaVu Sans'
    print("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
    return None

# 한글 폰트 설정
setup_korean_font()
plt.rcParams['axes.unicode_minus'] = False

class BitcoinPriceAlertBot:
    def __init__(self):
        """봇 초기화"""
        self.base_price = None  # 기준 가격
        self.current_price = None  # 현재 가격
        self.alert_threshold = 5.0  # 알림 임계값 (5%)
        self.is_running = False
        
        # 가격 데이터 저장용
        self.price_history = []  # 가격 이력
        self.time_history = []   # 시간 이력
        self.max_points = 100    # 최대 표시 포인트 수
        
        # Upbit API 엔드포인트
        self.api_url = "https://api.upbit.com/v1/ticker"
        self.market = "KRW-BTC"  # 비트코인 마켓
        
        # GUI 초기화
        self.setup_gui()
        
    def setup_gui(self):
        """그래프 설정"""
        # matplotlib 그래프 설정
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        
        # 한글 폰트로 제목과 라벨 설정
        current_font = plt.rcParams['font.family']
        self.ax.set_title("비트코인 실시간 가격 변화", fontsize=16, fontweight='bold', fontfamily=current_font)
        self.ax.set_xlabel("시간", fontsize=12, fontfamily=current_font)
        self.ax.set_ylabel("가격 (원)", fontsize=12, fontfamily=current_font)
        self.ax.grid(True, alpha=0.3)
        
        # 그래프 창 설정
        self.fig.canvas.manager.set_window_title("비트코인 가격 알림 봇 - 실시간 그래프")
        
        # 키보드 이벤트 바인딩
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 상태 정보를 그래프에 텍스트로 표시
        self.info_text = self.ax.text(0.02, 0.98, "대기 중...", transform=self.ax.transAxes, 
                                    verticalalignment='top', fontsize=10, fontfamily=current_font,
                                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
    def get_bitcoin_price(self):
        """Upbit API에서 비트코인 현재가 조회"""
        try:
            params = {'markets': self.market}
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return float(data[0]['trade_price'])
            return None
        except Exception as e:
            print(f"가격 조회 오류: {e}")
            return None
    
    def calculate_price_change(self):
        """가격 변화율 계산"""
        if self.base_price and self.current_price:
            change_percent = ((self.current_price - self.base_price) / self.base_price) * 100
            return change_percent
        return 0.0
    
    def show_alert(self, message):
        """알림 메시지 표시"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        print("=" * 50)
        print("🚨 비트코인 가격 알림 🚨")
        print(message)
        print("=" * 50)
    
    def on_key_press(self, event):
        """키보드 이벤트 처리"""
        if event.key == ' ' and not self.is_running:  # 스페이스바로 시작
            self.start_monitoring()
        elif event.key == 'q' and self.is_running:  # q로 중지
            self.stop_monitoring()
        elif event.key == 'escape':  # ESC로 종료
            self.stop_monitoring()
            plt.close('all')
    
    def update_gui(self):
        """GUI 업데이트"""
        # 상태 정보 텍스트 업데이트
        status_text = f"상태: {'모니터링 중...' if self.is_running else '대기 중'}\n"
        if self.current_price:
            status_text += f"현재 가격: {self.current_price:,.0f}원\n"
        if self.base_price:
            status_text += f"기준 가격: {self.base_price:,.0f}원\n"
        
        change_percent = self.calculate_price_change()
        status_text += f"상승률: {change_percent:.2f}%\n"
        status_text += "\n키보드 단축키:\n"
        status_text += "스페이스바: 시작\n"
        status_text += "Q: 중지\n"
        status_text += "ESC: 종료"
        
        # 한글 폰트 적용
        current_font = plt.rcParams['font.family']
        self.info_text.set_text(status_text)
        self.info_text.set_fontfamily(current_font)
    
    def update_graph(self):
        """그래프 업데이트"""
        if len(self.price_history) > 0:
            # 그래프 클리어
            self.ax.clear()
            
            # 가격 데이터 플롯
            self.ax.plot(self.time_history, self.price_history, 'b-', linewidth=2, label='비트코인 가격')
            
            # 기준 가격선 표시
            if self.base_price:
                self.ax.axhline(y=self.base_price, color='gray', linestyle='--', alpha=0.7, label=f'기준가: {self.base_price:,.0f}원')
                
                # 5% 상승선 표시
                alert_price = self.base_price * (1 + self.alert_threshold / 100)
                self.ax.axhline(y=alert_price, color='red', linestyle='--', alpha=0.7, label=f'알림선: {alert_price:,.0f}원')
            
            # 현재 가격 포인트 강조
            if self.current_price:
                self.ax.scatter(self.time_history[-1], self.price_history[-1], 
                              color='red', s=100, zorder=5, label=f'현재가: {self.current_price:,.0f}원')
            
            # 그래프 설정
            current_font = plt.rcParams['font.family']
            self.ax.set_title("비트코인 실시간 가격 변화", fontsize=14, fontweight='bold', fontfamily=current_font)
            self.ax.set_xlabel("시간", fontfamily=current_font)
            self.ax.set_ylabel("가격 (원)", fontfamily=current_font)
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left', prop={'family': current_font})
            
            # Y축 포맷팅 (천 단위 구분)
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            # X축 시간 포맷팅
            if len(self.time_history) > 0:
                self.ax.set_xticks(self.time_history[::max(1, len(self.time_history)//10)])
                self.ax.set_xticklabels([t.strftime('%H:%M:%S') for t in self.time_history[::max(1, len(self.time_history)//10)]], 
                                      rotation=45)
            
            # 그래프 새로고침
            self.fig.canvas.draw()
    
    def monitoring_loop(self):
        """가격 모니터링 루프"""
        while self.is_running:
            try:
                # 현재 가격 조회
                new_price = self.get_bitcoin_price()
                if new_price:
                    self.current_price = new_price
                    current_time = datetime.now()
                    
                    # 가격 이력에 추가
                    self.price_history.append(new_price)
                    self.time_history.append(current_time)
                    
                    # 최대 포인트 수 제한
                    if len(self.price_history) > self.max_points:
                        self.price_history.pop(0)
                        self.time_history.pop(0)
                    
                    # 기준 가격이 설정되지 않은 경우 현재 가격을 기준으로 설정
                    if self.base_price is None:
                        self.base_price = new_price
                        print(f"기준 가격 설정: {self.base_price:,.0f}원")
                    
                    # 가격 변화율 계산
                    change_percent = self.calculate_price_change()
                    
                    # GUI 업데이트
                    self.update_gui()
                    self.update_graph()
                    
                    # 5% 이상 상승 시 알림
                    if change_percent >= self.alert_threshold:
                        alert_message = f"비트코인 가격이 {change_percent:.2f}% 상승했습니다!\n"
                        alert_message += f"기준 가격: {self.base_price:,.0f}원\n"
                        alert_message += f"현재 가격: {self.current_price:,.0f}원"
                        
                        self.show_alert(alert_message)
                    
                    print(f"[{current_time.strftime('%H:%M:%S')}] "
                          f"현재가: {self.current_price:,.0f}원, "
                          f"변화율: {change_percent:.2f}%")
                
                # 10초 대기
                time.sleep(10)
                
            except Exception as e:
                print(f"모니터링 오류: {e}")
                time.sleep(10)
    
    def start_monitoring(self):
        """모니터링 시작"""
        if not self.is_running:
            self.is_running = True
            
            # 기준 가격 초기화
            self.base_price = None
            
            # 모니터링 스레드 시작
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            print("모니터링이 시작되었습니다.")
            self.update_gui()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        print("모니터링이 중지되었습니다.")
        self.update_gui()
    
    def run(self):
        """봇 실행"""
        try:
            print("\n비트코인 가격 알림 봇이 시작되었습니다!")
            print("키보드 단축키:")
            print("  스페이스바: 모니터링 시작")
            print("  Q: 모니터링 중지")
            print("  ESC: 프로그램 종료")
            print("-" * 50)
            
            # 초기 GUI 업데이트
            self.update_gui()
            
            # matplotlib 이벤트 루프 시작
            plt.show()
        except KeyboardInterrupt:
            print("\n봇이 종료되었습니다.")
            plt.close('all')

def main():
    """메인 함수"""
    print("비트코인 가격 알림 봇을 시작합니다...")
    print("Upbit API를 사용하여 실시간 비트코인 가격을 모니터링합니다.")
    print("5% 이상 상승 시 알림이 표시됩니다.")
    print("-" * 50)
    
    bot = BitcoinPriceAlertBot()
    bot.run()

if __name__ == "__main__":
    main()
