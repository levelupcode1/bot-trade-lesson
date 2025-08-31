#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 5% 상승 시 알림을 보내는 봇
Upbit API를 사용하여 실시간 가격을 모니터링하고 알림을 표시합니다.
"""

import requests
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import threading

class BitcoinPriceAlertBot:
    def __init__(self):
        """봇 초기화"""
        self.base_price = None  # 기준 가격
        self.current_price = None  # 현재 가격
        self.alert_threshold = 5.0  # 알림 임계값 (5%)
        self.is_running = False
        
        # Upbit API 엔드포인트
        self.api_url = "https://api.upbit.com/v1/ticker"
        self.market = "KRW-BTC"  # 비트코인 마켓
        
        # GUI 초기화
        self.setup_gui()
        
    def setup_gui(self):
        """사용자 인터페이스 설정"""
        self.root = tk.Tk()
        self.root.title("비트코인 가격 알림 봇")
        self.root.geometry("400x300")
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = tk.Label(main_frame, text="비트코인 가격 알림 봇", 
                             font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 현재 가격 표시
        self.price_frame = tk.Frame(main_frame)
        self.price_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.price_frame, text="현재 가격:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.current_price_label = tk.Label(self.price_frame, text="로딩 중...", 
                                          font=("Arial", 12, "bold"), fg="blue")
        self.current_price_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 기준 가격 표시
        self.base_frame = tk.Frame(main_frame)
        self.base_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.base_frame, text="기준 가격:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.base_price_label = tk.Label(self.price_frame, text="설정되지 않음", 
                                       font=("Arial", 12), fg="gray")
        self.base_price_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 상승률 표시
        self.change_frame = tk.Frame(main_frame)
        self.change_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.change_frame, text="상승률:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.change_label = tk.Label(self.change_frame, text="0.00%", 
                                   font=("Arial", 12))
        self.change_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 버튼들
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.start_button = tk.Button(button_frame, text="모니터링 시작", 
                                    command=self.start_monitoring, 
                                    bg="green", fg="white", font=("Arial", 12))
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = tk.Button(button_frame, text="모니터링 중지", 
                                   command=self.stop_monitoring, 
                                   bg="red", fg="white", font=("Arial", 12), 
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # 상태 표시
        self.status_label = tk.Label(main_frame, text="대기 중", 
                                   font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=10)
        
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
        messagebox.showwarning("비트코인 가격 알림", message)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
    def update_gui(self):
        """GUI 업데이트"""
        if self.current_price:
            self.current_price_label.config(text=f"{self.current_price:,.0f}원")
        
        if self.base_price:
            self.base_price_label.config(text=f"{self.base_price:,.0f}원")
        
        change_percent = self.calculate_price_change()
        self.change_label.config(text=f"{change_percent:.2f}%")
        
        # 상승률에 따른 색상 변경
        if change_percent >= self.alert_threshold:
            self.change_label.config(fg="red", font=("Arial", 12, "bold"))
        elif change_percent > 0:
            self.change_label.config(fg="green")
        else:
            self.change_label.config(fg="black")
    
    def monitoring_loop(self):
        """가격 모니터링 루프"""
        while self.is_running:
            try:
                # 현재 가격 조회
                new_price = self.get_bitcoin_price()
                if new_price:
                    self.current_price = new_price
                    
                    # 기준 가격이 설정되지 않은 경우 현재 가격을 기준으로 설정
                    if self.base_price is None:
                        self.base_price = new_price
                        print(f"기준 가격 설정: {self.base_price:,.0f}원")
                    
                    # 가격 변화율 계산
                    change_percent = self.calculate_price_change()
                    
                    # GUI 업데이트
                    self.root.after(0, self.update_gui)
                    
                    # 5% 이상 상승 시 알림
                    if change_percent >= self.alert_threshold:
                        alert_message = f"비트코인 가격이 {change_percent:.2f}% 상승했습니다!\n"
                        alert_message += f"기준 가격: {self.base_price:,.0f}원\n"
                        alert_message += f"현재 가격: {self.current_price:,.0f}원"
                        
                        self.root.after(0, lambda: self.show_alert(alert_message))
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
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
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="모니터링 중...", fg="green")
            
            # 기준 가격 초기화
            self.base_price = None
            
            # 모니터링 스레드 시작
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            print("모니터링이 시작되었습니다.")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="대기 중", fg="gray")
        print("모니터링이 중지되었습니다.")
    
    def run(self):
        """봇 실행"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n봇이 종료되었습니다.")

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
