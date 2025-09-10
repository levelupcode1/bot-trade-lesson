#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 5% 상승 시 알림을 보내는 봇 (v2)
Upbit API를 사용하여 실시간 가격을 모니터링하고 matplotlib으로 그래프를 표시하며,
알림 메시지를 price_alerts.txt 파일에 저장합니다.
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
import os
import platform

# 한글 폰트 설정
import matplotlib.font_manager as fm

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

class BitcoinPriceAlertBotV2:
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
        
        # 알림 로그 파일 설정
        self.alert_log_file = "price_alerts.txt"
        self.setup_alert_log_file()
        
        # 최근 알림 저장용
        self.recent_alerts = []
        self.max_recent_alerts = 10
        
        # GUI 초기화
        self.setup_gui()
        
    def setup_alert_log_file(self):
        """알림 로그 파일 초기 설정"""
        try:
            # 파일이 존재하지 않으면 헤더와 함께 생성
            if not os.path.exists(self.alert_log_file):
                with open(self.alert_log_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("비트코인 가격 알림 로그\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                print(f"알림 로그 파일이 생성되었습니다: {self.alert_log_file}")
        except Exception as e:
            print(f"알림 로그 파일 생성 오류: {e}")
    
    def log_alert_to_file(self, message):
        """알림 메시지를 파일에 저장"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(self.alert_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                f.write("-" * 60 + "\n")
            
            print(f"알림이 파일에 저장되었습니다: {self.alert_log_file}")
        except Exception as e:
            print(f"알림 파일 저장 오류: {e}")
    
    def setup_gui(self):
        """그래프 설정"""
        # matplotlib 그래프 설정
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 상단 그래프 (가격 차트)
        current_font = plt.rcParams['font.family']
        self.ax1.set_title("비트코인 실시간 가격 변화 (v2 - 파일 저장 기능 포함)", 
                          fontsize=16, fontweight='bold', fontfamily=current_font)
        self.ax1.set_xlabel("시간", fontsize=12, fontfamily=current_font)
        self.ax1.set_ylabel("가격 (원)", fontsize=12, fontfamily=current_font)
        self.ax1.grid(True, alpha=0.3)
        
        # 하단 그래프 (알림 로그)
        self.ax2.set_title("최근 알림 로그", fontsize=14, fontweight='bold', fontfamily=current_font)
        self.ax2.set_xlim(0, 1)
        self.ax2.set_ylim(0, 1)
        self.ax2.axis('off')
        
        # 그래프 창 설정
        self.fig.canvas.manager.set_window_title("비트코인 가격 알림 봇 v2 - 실시간 그래프")
        
        # 키보드 이벤트 바인딩
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 상태 정보를 그래프에 텍스트로 표시
        self.info_text = self.ax1.text(0.02, 0.98, "대기 중...", transform=self.ax1.transAxes, 
                                     verticalalignment='top', fontsize=10, fontfamily=current_font,
                                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 알림 로그 텍스트
        self.alert_text = self.ax2.text(0.02, 0.98, "알림이 발생하면 여기에 표시됩니다.", 
                                      transform=self.ax2.transAxes, verticalalignment='top', 
                                      fontsize=9, fontfamily=current_font,
                                      bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def on_key_press(self, event):
        """키보드 이벤트 처리"""
        if event.key == ' ' and not self.is_running:  # 스페이스바로 시작
            self.start_monitoring()
        elif event.key == 'q' and self.is_running:  # q로 중지
            self.stop_monitoring()
        elif event.key == 'escape':  # ESC로 종료
            self.stop_monitoring()
            plt.close('all')
        elif event.key == 'l':  # L로 로그 파일 열기
            self.open_log_file()
        
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
        """알림 메시지 표시 및 파일 저장"""
        # 콘솔에 출력
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        print("=" * 50)
        print("🚨 비트코인 가격 알림 🚨")
        print(message)
        print("=" * 50)
        
        # 파일에 저장
        self.log_alert_to_file(message)
        
        # GUI 로그 영역에 표시
        self.update_log_display(message)
    
    def update_log_display(self, message):
        """GUI 로그 영역 업데이트"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] {message}"
            
            # 최근 알림에 추가
            self.recent_alerts.append(log_entry)
            
            # 최대 개수 제한
            if len(self.recent_alerts) > self.max_recent_alerts:
                self.recent_alerts.pop(0)
            
            # 알림 텍스트 업데이트
            alert_text = "최근 알림:\n" + "\n".join(self.recent_alerts[-5:])  # 최근 5개만 표시
            self.alert_text.set_text(alert_text)
            
            # 그래프 새로고침
            self.fig.canvas.draw()
        except Exception as e:
            print(f"로그 표시 업데이트 오류: {e}")
    
    def open_log_file(self):
        """로그 파일을 기본 텍스트 에디터로 열기"""
        try:
            if os.path.exists(self.alert_log_file):
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["open", self.alert_log_file])
                elif system == "Windows":
                    os.startfile(self.alert_log_file)
                else:  # Linux
                    subprocess.run(["xdg-open", self.alert_log_file])
                
                print(f"로그 파일이 열렸습니다: {self.alert_log_file}")
            else:
                print("아직 알림 로그 파일이 생성되지 않았습니다.")
        except Exception as e:
            print(f"로그 파일 열기 오류: {e}")
    
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
        status_text += "L: 로그 파일 열기\n"
        status_text += "ESC: 종료"
        
        # 한글 폰트 적용
        current_font = plt.rcParams['font.family']
        self.info_text.set_text(status_text)
        self.info_text.set_fontfamily(current_font)
    
    def update_graph(self):
        """그래프 업데이트"""
        if len(self.price_history) > 0:
            # 그래프 클리어
            self.ax1.clear()
            
            # 가격 데이터 플롯
            self.ax1.plot(self.time_history, self.price_history, 'b-', linewidth=2, label='비트코인 가격')
            
            # 기준 가격선 표시
            if self.base_price:
                self.ax1.axhline(y=self.base_price, color='gray', linestyle='--', alpha=0.7, label=f'기준가: {self.base_price:,.0f}원')
                
                # 5% 상승선 표시
                alert_price = self.base_price * (1 + self.alert_threshold / 100)
                self.ax1.axhline(y=alert_price, color='red', linestyle='--', alpha=0.7, label=f'알림선: {alert_price:,.0f}원')
            
            # 현재 가격 포인트 강조
            if self.current_price:
                self.ax1.scatter(self.time_history[-1], self.price_history[-1], 
                              color='red', s=100, zorder=5, label=f'현재가: {self.current_price:,.0f}원')
            
            # 그래프 설정
            current_font = plt.rcParams['font.family']
            self.ax1.set_title("비트코인 실시간 가격 변화 (v2 - 파일 저장 기능 포함)", 
                              fontsize=14, fontweight='bold', fontfamily=current_font)
            self.ax1.set_xlabel("시간", fontfamily=current_font)
            self.ax1.set_ylabel("가격 (원)", fontfamily=current_font)
            self.ax1.grid(True, alpha=0.3)
            self.ax1.legend(loc='upper left', prop={'family': current_font})
            
            # Y축 포맷팅 (천 단위 구분)
            self.ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            # X축 시간 포맷팅
            if len(self.time_history) > 0:
                self.ax1.set_xticks(self.time_history[::max(1, len(self.time_history)//10)])
                self.ax1.set_xticklabels([t.strftime('%H:%M:%S') for t in self.time_history[::max(1, len(self.time_history)//10)]], 
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
            print("\n비트코인 가격 알림 봇 v2가 시작되었습니다!")
            print("키보드 단축키:")
            print("  스페이스바: 모니터링 시작")
            print("  Q: 모니터링 중지")
            print("  L: 로그 파일 열기")
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
    print("비트코인 가격 알림 봇 v2를 시작합니다...")
    print("Upbit API를 사용하여 실시간 비트코인 가격을 모니터링합니다.")
    print("5% 이상 상승 시 알림이 표시되고 price_alerts.txt 파일에 저장됩니다.")
    print("-" * 60)
    
    bot = BitcoinPriceAlertBotV2()
    bot.run()

if __name__ == "__main__":
    main()
