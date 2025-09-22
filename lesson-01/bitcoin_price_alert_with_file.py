#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 5% 상승 알림 봇 (파일 저장 강화 버전)
Upbit API를 사용하여 실시간 가격을 모니터링하고,
기준 가격 대비 5% 이상 상승 시 화면에 알림을 표시하고
price_alerts.txt 파일에 상세한 알림 메시지를 저장합니다.
"""

import requests
import time
import json
from datetime import datetime
import os
import platform
import threading

# Windows에서 알림을 위한 라이브러리
try:
    import plyer
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("plyer 라이브러리가 설치되지 않았습니다. 기본 알림만 사용합니다.")

class BitcoinPriceAlertBotWithFile:
    def __init__(self):
        """봇 초기화"""
        self.base_price = None  # 기준 가격
        self.current_price = None  # 현재 가격
        self.alert_threshold = 0.02  # 알림 임계값 (0.02%)
        
        self.is_running = False
        
        # Upbit API 설정
        self.api_url = "https://api.upbit.com/v1/ticker"
        self.market = "KRW-BTC"  # 비트코인 마켓
        
        # 알림 로그 파일 설정
        self.alert_log_file = "price_alerts.txt"
        self.setup_alert_log_file()
        
        # 알림 통계
        self.alert_count = 0
        self.total_price_change = 0.0
        
        print("비트코인 가격 알림 봇이 초기화되었습니다.")
        print(f"알림 임계값: {self.alert_threshold}%")
        print(f"알림 로그 파일: {self.alert_log_file}")
        print("-" * 50)
    
    def setup_alert_log_file(self):
        """알림 로그 파일 초기 설정"""
        try:
            # 파일이 존재하지 않으면 헤더와 함께 생성
            if not os.path.exists(self.alert_log_file):
                with open(self.alert_log_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("비트코인 가격 알림 로그\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"알림 임계값: {self.alert_threshold}%\n")
                    f.write("=" * 80 + "\n\n")
                print(f"✅ 알림 로그 파일이 생성되었습니다: {self.alert_log_file}")
            else:
                print(f"✅ 기존 알림 로그 파일을 사용합니다: {self.alert_log_file}")
                
                # 기존 파일에 새 세션 시작 표시
                with open(self.alert_log_file, 'a', encoding='utf-8') as f:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"새 세션 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    
        except Exception as e:
            print(f"❌ 알림 로그 파일 생성 오류: {e}")
    
    def get_bitcoin_price(self):
        """Upbit API에서 비트코인 현재가 조회"""
        try:
            params = {'markets': self.market}
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                price_data = data[0]
                return {
                    'price': float(price_data['trade_price']),
                    'volume': float(price_data['acc_trade_volume_24h']),
                    'change_rate': float(price_data['signed_change_rate']),
                    'change_price': float(price_data['signed_change_price'])
                }
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 가격 조회 오류: {e}")
            return None
    
    def calculate_price_change(self):
        """가격 변화율 계산"""
        if self.base_price and self.current_price:
            change_percent = ((self.current_price - self.base_price) / self.base_price) * 100
            return change_percent
        return 0.0
    
    def log_alert_to_file(self, message, price_data=None):
        """알림 메시지를 파일에 상세하게 저장"""
        try:
            timestamp = datetime.now()
            alert_id = self.alert_count + 1
            
            # 상세한 로그 엔트리 생성
            log_entry = f"🚨 알림 #{alert_id} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_entry += "-" * 60 + "\n"
            log_entry += f"📊 알림 내용:\n{message}\n\n"
            
            # 추가 정보 추가
            if price_data:
                log_entry += f"📈 추가 정보:\n"
                log_entry += f"   - 24시간 거래량: {price_data.get('volume', 0):,.2f} BTC\n"
                log_entry += f"   - 24시간 변화율: {price_data.get('change_rate', 0)*100:.2f}%\n"
                log_entry += f"   - 24시간 변화금액: {price_data.get('change_price', 0):,.0f}원\n"
                log_entry += "\n"
            
            # 통계 정보
            log_entry += f"📊 세션 통계:\n"
            log_entry += f"   - 총 알림 횟수: {alert_id}회\n"
            log_entry += f"   - 누적 상승률: {self.total_price_change:.2f}%\n"
            log_entry += f"   - 평균 상승률: {(self.total_price_change/max(1, alert_id)):.2f}%\n"
            log_entry += "=" * 80 + "\n\n"
            
            # 파일에 저장
            with open(self.alert_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            print(f"✅ 알림이 파일에 저장되었습니다: {self.alert_log_file}")
            print(f"   알림 ID: #{alert_id}")
            
        except Exception as e:
            print(f"❌ 알림 파일 저장 오류: {e}")
    
    def show_desktop_notification(self, message):
        """데스크톱 알림 표시"""
        if PLYER_AVAILABLE:
            try:
                plyer.notification.notify(
                    title="비트코인 가격 알림",
                    message=message,
                    app_name="Bitcoin Alert Bot",
                    timeout=10
                )
                print("🔔 데스크톱 알림이 표시되었습니다.")
            except Exception as e:
                print(f"❌ 데스크톱 알림 오류: {e}")
                self.show_console_alert(message)
        else:
            self.show_console_alert(message)
    
    def show_console_alert(self, message):
        """콘솔 알림 표시"""
        print("\n" + "=" * 80)
        print("🚨 비트코인 가격 알림 🚨")
        print("=" * 80)
        print(message)
        print("=" * 80)
        print("🔔 알림음이 울렸습니다! (시스템 사운드)")
        
        # Windows에서 시스템 사운드 재생
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as e:
            print(f"❌ 사운드 재생 오류: {e}")
    
    def show_alert(self, message, price_data=None):
        """종합 알림 표시"""
        # 알림 카운트 증가
        self.alert_count += 1
        
        # 콘솔 알림
        self.show_console_alert(message)
        
        # 데스크톱 알림
        self.show_desktop_notification(message)
        
        # 파일에 상세 저장
        self.log_alert_to_file(message, price_data)
    
    def monitoring_loop(self):
        """가격 모니터링 루프"""
        print("🔍 모니터링이 시작되었습니다...")
        print("📊 기준 가격을 설정하기 위해 첫 번째 가격을 조회합니다.")
        
        while self.is_running:
            try:
                # 현재 가격 조회
                price_data = self.get_bitcoin_price()
                if price_data:
                    self.current_price = price_data['price']
                    current_time = datetime.now()
                    
                    # 기준 가격이 설정되지 않은 경우 현재 가격을 기준으로 설정
                    if self.base_price is None:
                        self.base_price = self.current_price
                        print(f"✅ 기준 가격이 설정되었습니다: {self.base_price:,.0f}원")
                        print("이제 0.02% 이상 상승 시 알림이 발생합니다.")
                        print("-" * 50)
                    
                    # 가격 변화율 계산
                    change_percent = self.calculate_price_change()
                    
                    # 현재 상태 출력
                    print(f"[{current_time.strftime('%H:%M:%S')}] "
                          f"현재가: {self.current_price:,.0f}원, "
                          f"기준가: {self.base_price:,.0f}원, "
                          f"상승률: {change_percent:.2f}%")
                    
                    # 0.02% 이상 상승 또는 하락 시 알림
                    if abs(change_percent) >= self.alert_threshold:
                        # 상세한 알림 메시지 생성
                        alert_message = f"🎯 비트코인 가격이 {change_percent:.2f}% 상승했습니다!\n"
                        alert_message += f"📈 기준 가격: {self.base_price:,.0f}원\n"
                        alert_message += f"📈 현재 가격: {self.current_price:,.0f}원\n"
                        alert_message += f"💰 상승 금액: {self.current_price - self.base_price:,.0f}원\n"
                        alert_message += f"⏰ 알림 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        self.show_alert(alert_message, price_data)
                        
                        # 통계 업데이트
                        self.total_price_change += change_percent
                        
                        # 기준 가격을 현재 가격으로 업데이트 (중복 알림 방지)
                        old_base = self.base_price
                        self.base_price = self.current_price
                        print(f"📊 기준 가격이 업데이트되었습니다: {old_base:,.0f}원 → {self.base_price:,.0f}원")
                        print("-" * 50)
                
                # 10초 대기
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n⏹️ 사용자에 의해 모니터링이 중단되었습니다.")
                break
            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
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
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if self.is_running:
            self.is_running = False
            print("\n⏹️ 모니터링이 중지되었습니다.")
            
            # 세션 종료 로그 저장
            try:
                with open(self.alert_log_file, 'a', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"세션 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"총 알림 횟수: {self.alert_count}회\n")
                    f.write(f"누적 상승률: {self.total_price_change:.2f}%\n")
                    f.write("=" * 80 + "\n\n")
                print(f"📝 세션 종료 로그가 저장되었습니다.")
            except Exception as e:
                print(f"❌ 세션 종료 로그 저장 오류: {e}")
    
    def show_file_info(self):
        """파일 정보 표시"""
        try:
            if os.path.exists(self.alert_log_file):
                file_size = os.path.getsize(self.alert_log_file)
                file_time = datetime.fromtimestamp(os.path.getmtime(self.alert_log_file))
                
                print(f"\n📁 파일 정보:")
                print(f"   파일명: {self.alert_log_file}")
                print(f"   파일 크기: {file_size:,} bytes")
                print(f"   마지막 수정: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 파일 내용 미리보기
                with open(self.alert_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"   총 라인 수: {len(lines)}")
                    
                    # 최근 알림 찾기
                    recent_alerts = [line for line in lines if '🚨 알림 #' in line]
                    if recent_alerts:
                        print(f"   최근 알림: {recent_alerts[-1].strip()}")
                    else:
                        print("   저장된 알림이 없습니다.")
            else:
                print(f"\n❌ 파일이 존재하지 않습니다: {self.alert_log_file}")
        except Exception as e:
            print(f"❌ 파일 정보 조회 오류: {e}")
    
    def run(self):
        """봇 실행"""
        try:
            print("\n🚀 비트코인 가격 알림 봇이 시작되었습니다!")
            print("Upbit API를 사용하여 실시간 비트코인 가격을 모니터링합니다.")
            print(f"기준 가격 대비 {self.alert_threshold}% 이상 상승 시 알림이 발생합니다.")
            print(f"모든 알림은 '{self.alert_log_file}' 파일에 상세하게 저장됩니다.")
            print("-" * 80)
            
            # 모니터링 시작
            self.start_monitoring()
            
            # 메인 스레드에서 사용자 입력 대기
            while self.is_running:
                try:
                    user_input = input("\n명령어를 입력하세요 (s: 상태, f: 파일정보, q: 종료): ").strip().lower()
                    
                    if user_input == 'q' or user_input == 'quit':
                        self.stop_monitoring()
                        break
                    elif user_input == 's' or user_input == 'status':
                        if self.current_price and self.base_price:
                            change_percent = self.calculate_price_change()
                            print(f"\n📊 현재 상태:")
                            print(f"   현재 가격: {self.current_price:,.0f}원")
                            print(f"   기준 가격: {self.base_price:,.0f}원")
                            print(f"   상승률: {change_percent:.2f}%")
                            print(f"   알림 임계값: {self.alert_threshold}%")
                            print(f"   총 알림 횟수: {self.alert_count}회")
                            print(f"   누적 상승률: {self.total_price_change:.2f}%")
                        else:
                            print("\n📊 현재 상태: 가격 데이터를 수집 중입니다...")
                    elif user_input == 'f' or user_input == 'file':
                        self.show_file_info()
                    elif user_input == 'h' or user_input == 'help':
                        print("\n📖 사용 가능한 명령어:")
                        print("   s, status: 현재 상태 확인")
                        print("   f, file: 파일 정보 확인")
                        print("   q, quit: 프로그램 종료")
                        print("   h, help: 도움말 표시")
                    else:
                        print("❌ 알 수 없는 명령어입니다. 'h'를 입력하여 도움말을 확인하세요.")
                        
                except EOFError:
                    # Ctrl+D 입력 시 종료
                    self.stop_monitoring()
                    break
                except KeyboardInterrupt:
                    # Ctrl+C 입력 시 종료
                    self.stop_monitoring()
                    break
                    
        except Exception as e:
            print(f"❌ 봇 실행 오류: {e}")
        finally:
            print("\n👋 비트코인 가격 알림 봇이 종료되었습니다.")
            print(f"📝 알림 로그는 '{self.alert_log_file}' 파일에서 확인할 수 있습니다.")

def main():
    """메인 함수"""
    print("비트코인 가격 알림 봇을 시작합니다...")
    print("Upbit API를 사용하여 실시간 비트코인 가격을 모니터링합니다.")
    print("0.02% 이상 상승 시 알림이 표시되고 price_alerts.txt 파일에 상세하게 저장됩니다.")
    print("-" * 80)
    
    bot = BitcoinPriceAlertBotWithFile()
    bot.run()

if __name__ == "__main__":
    main()
