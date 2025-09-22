#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import websocket
import json
import threading
import time
import logging
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import signal
import sys

class UpbitWebSocketCollector:
    """
    업비트 WebSocket을 사용한 실시간 가격 데이터 수집기
    
    주요 기능:
    - 실시간 가격 데이터 수집
    - 자동 재연결
    - 데이터 파일 저장 (CSV, JSON)
    - 오류 처리 및 로깅
    - 사용자 정의 콜백 함수 지원
    """
    
    def __init__(self, markets: List[str] = None, 
                 data_dir: str = "data", 
                 save_format: str = "csv"):
        """
        초기화
        
        Args:
            markets (List[str]): 수집할 마켓 코드 리스트
            data_dir (str): 데이터 저장 디렉토리
            save_format (str): 저장 형식 (csv, json)
        """
        self.markets = markets or ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        self.data_dir = data_dir
        self.save_format = save_format
        self.ws = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # 초
        
        # 데이터 저장용
        self.data_buffer = []
        self.buffer_size = 100  # 버퍼 크기
        self.save_interval = 30  # 저장 간격 (초)
        
        # 콜백 함수
        self.on_ticker_callback = None
        self.on_error_callback = None
        self.on_connect_callback = None
        
        # 로깅 설정
        self.setup_logging()
        
        # 데이터 디렉토리 생성
        self.create_data_directory()
        
        # 시그널 핸들러 설정
        self.setup_signal_handlers()
        
        # 자동 저장 스레드 시작
        self.start_auto_save_thread()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('realtime_collector.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_data_directory(self):
        """데이터 저장 디렉토리 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            self.logger.info(f"데이터 디렉토리 생성: {self.data_dir}")
    
    def setup_signal_handlers(self):
        """시그널 핸들러 설정 (Ctrl+C 처리)"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.logger.info("종료 신호를 받았습니다. 데이터를 저장하고 종료합니다...")
        self.stop()
        sys.exit(0)
    
    def set_callbacks(self, on_ticker: Callable = None, 
                     on_error: Callable = None, 
                     on_connect: Callable = None):
        """
        콜백 함수 설정
        
        Args:
            on_ticker: 티커 데이터 수신 시 호출되는 함수
            on_error: 오류 발생 시 호출되는 함수
            on_connect: 연결 성공 시 호출되는 함수
        """
        self.on_ticker_callback = on_ticker
        self.on_error_callback = on_error
        self.on_connect_callback = on_connect
    
    def on_message(self, ws, message):
        """WebSocket 메시지 수신 처리"""
        try:
            data = json.loads(message)
            
            # 티커 데이터 처리 (업비트 WebSocket 형식)
            if isinstance(data, dict) and data.get('ty') == 'ticker':
                self.process_ticker_data(data)
            else:
                # 디버깅용 로그 (너무 많은 로그를 방지하기 위해 주석 처리)
                # self.logger.debug(f"수신된 메시지: {data}")
                pass
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 오류: {e}")
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
    
    def process_ticker_data(self, data: Dict[str, Any]):
        """티커 데이터 처리"""
        try:
            # 업비트 WebSocket 데이터 형식에 맞게 매핑
            ticker_data = {
                'timestamp': datetime.now().isoformat(),
                'market': data.get('cd', ''),  # 업비트는 'cd' 필드 사용
                'trade_price': data.get('tp', 0),  # 업비트는 'tp' 필드 사용
                'trade_volume': data.get('tv', 0),  # 업비트는 'tv' 필드 사용
                'signed_change_rate': data.get('scr', 0),  # 업비트는 'scr' 필드 사용
                'signed_change_price': data.get('scp', 0),  # 업비트는 'scp' 필드 사용
                'high_price': data.get('hp', 0),  # 업비트는 'hp' 필드 사용
                'low_price': data.get('lp', 0),  # 업비트는 'lp' 필드 사용
                'opening_price': data.get('op', 0),  # 업비트는 'op' 필드 사용
                'prev_closing_price': data.get('pcp', 0),  # 업비트는 'pcp' 필드 사용
                'acc_trade_volume_24h': data.get('atv24h', 0),  # 업비트는 'atv24h' 필드 사용
                'acc_trade_price_24h': data.get('atp24h', 0),  # 업비트는 'atp24h' 필드 사용
                'highest_52_week_price': data.get('h52wp', 0),  # 업비트는 'h52wp' 필드 사용
                'lowest_52_week_price': data.get('l52wp', 0),  # 업비트는 'l52wp' 필드 사용
                'trade_date': data.get('tdt', ''),  # 업비트는 'tdt' 필드 사용
                'trade_time': data.get('ttm', ''),  # 업비트는 'ttm' 필드 사용
                'trade_timestamp': data.get('ttms', 0)  # 업비트는 'ttms' 필드 사용
            }
            
            # 버퍼에 추가
            self.data_buffer.append(ticker_data)
            
            # 로그 출력
            self.logger.info(
                f"{ticker_data['market']}: {ticker_data['trade_price']:,}원 "
                f"({ticker_data['signed_change_rate']:.2%})"
            )
            
            # 사용자 콜백 호출
            if self.on_ticker_callback:
                self.on_ticker_callback(ticker_data)
            
            # 버퍼가 가득 찼으면 저장
            if len(self.data_buffer) >= self.buffer_size:
                self.save_data()
                
        except Exception as e:
            self.logger.error(f"티커 데이터 처리 오류: {e}")
    
    def on_error(self, ws, error):
        """WebSocket 오류 처리"""
        self.logger.error(f"WebSocket 오류: {error}")
        
        if self.on_error_callback:
            self.on_error_callback(error)
        
        # 자동 재연결 시도
        if self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
            time.sleep(self.reconnect_delay)
            self.connect()
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket 연결 종료 처리"""
        self.logger.info("WebSocket 연결이 종료되었습니다.")
        
        # 자동 재연결 시도
        if self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
            time.sleep(self.reconnect_delay)
            self.connect()
    
    def on_open(self, ws):
        """WebSocket 연결 성공 처리"""
        self.logger.info("WebSocket 연결이 성공했습니다.")
        self.reconnect_attempts = 0  # 재연결 시도 횟수 초기화
        
        # 구독 메시지 전송
        subscribe_data = [
            {"ticket": "realtime_collector"},
            {"type": "ticker", "codes": self.markets},
            {"format": "SIMPLE"}
        ]
        
        try:
            ws.send(json.dumps(subscribe_data))
            self.logger.info(f"구독 메시지 전송: {subscribe_data}")
        except Exception as e:
            self.logger.error(f"구독 메시지 전송 실패: {e}")
        
        if self.on_connect_callback:
            self.on_connect_callback()
    
    def connect(self):
        """WebSocket 연결"""
        try:
            # WebSocket URL
            ws_url = "wss://api.upbit.com/websocket/v1"
            
            # WebSocket 연결
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # 연결 시작
            self.ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"WebSocket 연결 오류: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def start(self):
        """데이터 수집 시작"""
        self.logger.info("실시간 가격 데이터 수집을 시작합니다...")
        self.logger.info(f"수집 마켓: {', '.join(self.markets)}")
        self.logger.info(f"데이터 저장 형식: {self.save_format}")
        self.logger.info(f"데이터 저장 디렉토리: {self.data_dir}")
        
        self.is_running = True
        self.connect()
    
    def stop(self):
        """데이터 수집 중지"""
        self.logger.info("데이터 수집을 중지합니다...")
        self.is_running = False
        
        if self.ws:
            self.ws.close()
        
        # 남은 데이터 저장
        if self.data_buffer:
            self.save_data()
        
        self.logger.info("데이터 수집이 중지되었습니다.")
    
    def save_data(self):
        """데이터 저장"""
        if not self.data_buffer:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.save_format == "csv":
                self.save_csv(timestamp)
            elif self.save_format == "json":
                self.save_json(timestamp)
            
            # 버퍼 초기화
            self.data_buffer.clear()
            self.logger.info(f"데이터 저장 완료: {len(self.data_buffer)}개 레코드")
            
        except Exception as e:
            self.logger.error(f"데이터 저장 오류: {e}")
    
    def save_csv(self, timestamp: str):
        """CSV 형식으로 데이터 저장"""
        filename = f"{self.data_dir}/realtime_data_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if self.data_buffer:
                fieldnames = self.data_buffer[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data_buffer)
        
        self.logger.info(f"CSV 파일 저장: {filename}")
    
    def save_json(self, timestamp: str):
        """JSON 형식으로 데이터 저장"""
        filename = f"{self.data_dir}/realtime_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.data_buffer, jsonfile, ensure_ascii=False, indent=2)
        
        self.logger.info(f"JSON 파일 저장: {filename}")
    
    def start_auto_save_thread(self):
        """자동 저장 스레드 시작"""
        def auto_save():
            while self.is_running:
                time.sleep(self.save_interval)
                if self.data_buffer:
                    self.save_data()
        
        thread = threading.Thread(target=auto_save, daemon=True)
        thread.start()
    
    def get_statistics(self) -> Dict[str, Any]:
        """수집 통계 정보 반환"""
        return {
            'is_running': self.is_running,
            'markets': self.markets,
            'buffer_size': len(self.data_buffer),
            'reconnect_attempts': self.reconnect_attempts,
            'data_dir': self.data_dir,
            'save_format': self.save_format
        }

# 사용 예시 및 테스트 함수
def main():
    """메인 함수 - 실시간 데이터 수집 예시"""
    
    # 수집할 마켓 설정
    markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT']
    
    # 데이터 수집기 생성
    collector = UpbitWebSocketCollector(
        markets=markets,
        data_dir="realtime_data",
        save_format="csv"
    )
    
    # 콜백 함수 설정
    def on_ticker(data):
        """티커 데이터 수신 시 호출"""
        print(f"📊 {data['market']}: {data['trade_price']:,}원 "
              f"({data['signed_change_rate']:.2%})")
    
    def on_error(error):
        """오류 발생 시 호출"""
        print(f"❌ 오류 발생: {error}")
    
    def on_connect():
        """연결 성공 시 호출"""
        print("✅ WebSocket 연결 성공!")
    
    # 콜백 함수 등록
    collector.set_callbacks(
        on_ticker=on_ticker,
        on_error=on_error,
        on_connect=on_connect
    )
    
    try:
        print("🚀 실시간 가격 데이터 수집을 시작합니다...")
        print("종료하려면 Ctrl+C를 누르세요.")
        print("=" * 50)
        
        # 데이터 수집 시작
        collector.start()
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지되었습니다.")
        collector.stop()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        collector.stop()

if __name__ == "__main__":
    main()
