#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 5% 상승 시 알림을 보내는 봇 (v2)
Upbit API를 사용하여 실시간 가격을 모니터링하고 알림을 표시하며,
알림 메시지를 price_alerts.txt 파일에 저장합니다.
"""

import requests
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os

class BitcoinPriceAlertBotV2:
    def __init__(self):
        """봇 초기화"""
        self.base_price = None  # 기준 가격
        self.current_price = None  # 현재 가격
        self.alert_threshold = 5.0  # 알림 임계값 (5%)
        self.is_running = False
        
        # Upbit API 엔드포인트
        self.api_url = "https://api.upbit.com/v1/ticker"
        self.market = "KRW-BTC"  # 비트코인 마켓
        
        # 알림 로그 파일 설정
        self.alert_log_file = "price_alerts.txt"
        self.setup_alert_log_file()
        
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
        """사용자 인터페이스 설정"""
        self.root = tk.Tk()
        self.root.title("비트코인 가격 알림 봇 v2 (파일 저장 기능 포함)")
        self.root.geometry("500x400")
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = tk.Label(main_frame, text="비트코인 가격 알림 봇 v2", 
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
        self.base_price_label = tk.Label(self.base_frame, text="설정되지 않음", 
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
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 로그 파일 열기 버튼
        self.open_log_button = tk.Button(button_frame, text="로그 파일 열기", 
                                       command=self.open_log_file, 
                                       bg="blue", fg="white", font=("Arial", 12))
        self.open_log_button.pack(side=tk.LEFT)
        
        # 상태 표시
        self.status_label = tk.Label(main_frame, text="대기 중", 
                                   font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=10)
        
        # 최근 알림 표시 영역
        log_frame = tk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        tk.Label(log_frame, text="최근 알림:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.insert(tk.END, "알림이 발생하면 여기에 표시됩니다.\n")
        self.log_text.config(state=tk.DISABLED)
        
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
        # 화면 알림 표시
        messagebox.showwarning("비트코인 가격 알림", message)
        
        # 콘솔에 출력
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        
        # 파일에 저장
        self.log_alert_to_file(message)
        
        # GUI 로그 영역에 표시
        self.update_log_display(message)
    
    def update_log_display(self, message):
        """GUI 로그 영역 업데이트"""
        try:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] {message}\n"
            
            # 최근 10개 알림만 유지
            current_content = self.log_text.get("1.0", tk.END)
            lines = current_content.strip().split('\n')
            if len(lines) > 20:  # 20줄 이상이면 오래된 것 제거
                lines = lines[-20:]
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert(tk.END, '\n'.join(lines) + '\n')
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)  # 최신 내용으로 스크롤
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"로그 표시 업데이트 오류: {e}")
    
    def open_log_file(self):
        """로그 파일을 기본 텍스트 에디터로 열기"""
        try:
            if os.path.exists(self.alert_log_file):
                os.startfile(self.alert_log_file)  # Windows
                print(f"로그 파일이 열렸습니다: {self.alert_log_file}")
            else:
                messagebox.showinfo("알림", "아직 알림 로그 파일이 생성되지 않았습니다.")
        except Exception as e:
            print(f"로그 파일 열기 오류: {e}")
            messagebox.showerror("오류", f"로그 파일을 열 수 없습니다: {e}")
    
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
    print("비트코인 가격 알림 봇 v2를 시작합니다...")
    print("Upbit API를 사용하여 실시간 비트코인 가격을 모니터링합니다.")
    print("5% 이상 상승 시 알림이 표시되고 price_alerts.txt 파일에 저장됩니다.")
    print("-" * 60)
    
    bot = BitcoinPriceAlertBotV2()
    bot.run()

if __name__ == "__main__":
    main()
