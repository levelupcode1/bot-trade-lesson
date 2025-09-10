#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import websocket
import json
import threading
import time
import pandas as pd
import logging
from datetime import datetime
import os
from typing import List, Dict, Any

class UpbitWebSocketCollector:
    """
    업비트 WebSocket을 사용한 실시간 데이터 수집기
    """
    
    def __init__(self, markets: List[str], data_dir: str = "data"):
        """
        초기화
        
        Args:
            markets (List[str]): 수집할 마켓 코드 리스트 (예: ['KRW-BTC', 'KRW-ETH'])
            data_dir (str): 데이터 저장 디렉토리
        """
        self.markets = markets
        self.data_dir = data_dir
        self.ws = None
        self.is_connected = False
        self.data_buffer = []
        self.buffer_lock = threading.Lock()
        
        # 데이터 저장 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 데이터 저장 설정
        self.save_interval = 60  # 60초마다 파일 저장
        self.last_save_time = time.time()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{self.data_dir}/websocket.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def on_message(self, ws, message):
        """WebSocket 메시지 수신 처리"""
        try:
            data = json.loads(message)
            
            # 티커 데이터 처리
            if 'type' in data and data['type'] == 'ticker':
                self.process_ticker_data(data)
            
            # 체결 데이터 처리
            elif 'type' in data and data['type'] == 'trade':
                self.process_trade_data(data)
            
            # 호가 데이터 처리
            elif 'type' in data and data['type'] == 'orderbook':
                self.process_orderbook_data(data)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 디코딩 오류: {e}")
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
    
    def process_ticker_data(self, data):
        """티커 데이터 처리"""
        try:
            ticker_data = {
                'timestamp': datetime.now().isoformat(),
                'market': data.get('code', ''),
                'trade_price': data.get('trade_price', 0),
                'trade_volume': data.get('trade_volume', 0),
                'trade_date': data.get('trade_date', ''),
                'trade_time': data.get('trade_time', ''),
                'trade_timestamp': data.get('trade_timestamp', 0),
                'opening_price': data.get('opening_price', 0),
                'high_price': data.get('high_price', 0),
                'low_price': data.get('low_price', 0),
                'prev_closing_price': data.get('prev_closing_price', 0),
                'change': data.get('change', ''),
                'change_price': data.get('change_price', 0),
                'change_rate': data.get('change_rate', 0),
                'signed_change_price': data.get('signed_change_price', 0),
                'signed_change_rate': data.get('signed_change_rate', 0),
                'trade_status': data.get('trade_status', ''),
                'acc_trade_volume_24h': data.get('acc_trade_volume_24h', 0),
                'acc_trade_price_24h': data.get('acc_trade_price_24h', 0),
                'acc_trade_volume_24h_change_24h': data.get('acc_trade_volume_24h_change_24h', 0),
                'acc_trade_price_24h_change_24h': data.get('acc_trade_price_24h_change_24h', 0),
                'highest_52_week_price': data.get('highest_52_week_price', 0),
                'highest_52_week_date': data.get('highest_52_week_date', ''),
                'lowest_52_week_price': data.get('lowest_52_week_price', 0),
                'lowest_52_week_date': data.get('lowest_52_week_date', ''),
                'market_state': data.get('market_state', ''),
                'is_trading_suspended': data.get('is_trading_suspended', False),
                'delisting_date': data.get('delisting_date', ''),
                'market_warning': data.get('market_warning', ''),
                'timestamp': data.get('timestamp', 0)
            }
            
            # 버퍼에 데이터 추가
            with self.buffer_lock:
                self.data_buffer.append(ticker_data)
            
            # 실시간 로그 출력
            self.logger.info(f"티커 수신 - {ticker_data['market']}: {ticker_data['trade_price']:,}원 "
                           f"(변화율: {ticker_data['change_rate']:.2%})")
            
            # 주기적 파일 저장
            self.check_and_save_data()
            
        except Exception as e:
            self.logger.error(f"티커 데이터 처리 오류: {e}")
    
    def process_trade_data(self, data):
        """체결 데이터 처리"""
        try:
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'market': data.get('code', ''),
                'trade_price': data.get('trade_price', 0),
                'trade_volume': data.get('trade_volume', 0),
                'trade_date': data.get('trade_date', ''),
                'trade_time': data.get('trade_time', ''),
                'trade_timestamp': data.get('trade_timestamp', 0),
                'trade_type': data.get('trade_type', ''),
                'ask_bid': data.get('ask_bid', ''),
                'prev_closing_price': data.get('prev_closing_price', 0),
                'change': data.get('change', ''),
                'change_price': data.get('change_price', 0),
                'sequential_id': data.get('sequential_id', 0),
                'stream_type': data.get('stream_type', '')
            }
            
            # 버퍼에 데이터 추가
            with self.buffer_lock:
                self.data_buffer.append(trade_data)
            
            self.logger.info(f"체결 수신 - {trade_data['market']}: {trade_data['trade_price']:,}원 "
                           f"({trade_data['trade_volume']}개)")
            
        except Exception as e:
            self.logger.error(f"체결 데이터 처리 오류: {e}")
    
    def process_orderbook_data(self, data):
        """호가 데이터 처리"""
        try:
            orderbook_data = {
                'timestamp': datetime.now().isoformat(),
                'market': data.get('code', ''),
                'orderbook_units': data.get('orderbook_units', []),
                'total_ask_size': data.get('total_ask_size', 0),
                'total_bid_size': data.get('total_bid_size', 0),
                'orderbook_state': data.get('orderbook_state', ''),
                'timestamp': data.get('timestamp', 0)
            }
            
            # 버퍼에 데이터 추가
            with self.buffer_lock:
                self.data_buffer.append(orderbook_data)
            
        except Exception as e:
            self.logger.error(f"호가 데이터 처리 오류: {e}")
    
    def check_and_save_data(self):
        """주기적 데이터 저장 확인"""
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            self.save_data_to_file()
            self.last_save_time = current_time
    
    def save_data_to_file(self):
        """버퍼의 데이터를 파일로 저장"""
        try:
            with self.buffer_lock:
                if not self.data_buffer:
                    return
                
                # 데이터를 DataFrame으로 변환
                df = pd.DataFrame(self.data_buffer)
                
                # 파일명 생성 (날짜별)
                today = datetime.now().strftime('%Y%m%d')
                filename = f"{self.data_dir}/upbit_realtime_{today}.csv"
                
                # 기존 파일이 있으면 추가, 없으면 새로 생성
                if os.path.exists(filename):
                    df.to_csv(filename, mode='a', header=False, index=False)
                else:
                    df.to_csv(filename, mode='w', header=True, index=False)
                
                self.logger.info(f"데이터 저장 완료: {filename} ({len(self.data_buffer)}개 레코드)")
                
                # 버퍼 초기화
                self.data_buffer.clear()
                
        except Exception as e:
            self.logger.error(f"데이터 저장 오류: {e}")
    
    def on_error(self, ws, error):
        """WebSocket 오류 처리"""
        self.logger.error(f"WebSocket 오류: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket 연결 종료 처리"""
        self.logger.info(f"WebSocket 연결 종료: {close_status_code} - {close_msg}")
        self.is_connected = False
        
        # 마지막 데이터 저장
        self.save_data_to_file()
    
    def on_open(self, ws):
        """WebSocket 연결 시작 처리"""
        self.logger.info("WebSocket 연결 시작")
        self.is_connected = True
        
        # 구독 메시지 전송
        subscribe_message = [
            {
                "ticket": f"realtime_data_{int(time.time())}",
                "type": "ticker",
                "codes": self.markets,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
        ]
        
        ws.send(json.dumps(subscribe_message))
        self.logger.info(f"구독 시작: {self.markets}")
    
    def connect(self):
        """WebSocket 연결 시작"""
        try:
            # WebSocket 연결
            self.ws = websocket.WebSocketApp(
                "wss://api.upbit.com/websocket/v1",
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            self.logger.info("WebSocket 연결 시도 중...")
            self.ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"WebSocket 연결 오류: {e}")
    
    def disconnect(self):
        """WebSocket 연결 종료"""
        if self.ws:
            self.ws.close()
            self.logger.info("WebSocket 연결 종료")

def main():
    """메인 함수"""
    # 수집할 마켓 설정
    markets = [
        'KRW-BTC',    # 비트코인
        'KRW-ETH',    # 이더리움
        'KRW-XRP',    # 리플
        'KRW-ADA',    # 카르다노
        'KRW-DOT'     # 폴카닷
    ]
    
    # 데이터 수집기 생성
    collector = UpbitWebSocketCollector(
        markets=markets,
        data_dir="realtime_data"
    )
    
    try:
        print("🚀 업비트 실시간 데이터 수집 시작")
        print(f"📊 수집 마켓: {', '.join(markets)}")
        print("📁 데이터 저장 위치: realtime_data/")
        print("⏹️  종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        # WebSocket 연결 시작
        collector.connect()
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단됨")
        collector.disconnect()
        print("✅ 데이터 수집 완료")

if __name__ == "__main__":
    main()
