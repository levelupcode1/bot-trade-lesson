#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import websocket
import json
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_message(ws, message):
    """메시지 수신 처리"""
    try:
        data = json.loads(message)
        logger.info(f"수신된 데이터: {data}")
        
        # 파일에 저장
        with open("test_data.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
            
    except Exception as e:
        logger.error(f"메시지 처리 오류: {e}")

def on_error(ws, error):
    """오류 처리"""
    logger.error(f"WebSocket 오류: {error}")

def on_close(ws, close_status_code, close_msg):
    """연결 종료 처리"""
    logger.info("WebSocket 연결이 종료되었습니다.")

def on_open(ws):
    """연결 성공 처리"""
    logger.info("WebSocket 연결 성공!")
    
    # 구독 메시지 전송
    subscribe_data = [
        {"ticket": "test_collector"},
        {"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]},
        {"format": "SIMPLE"}
    ]
    
    try:
        ws.send(json.dumps(subscribe_data))
        logger.info(f"구독 메시지 전송: {subscribe_data}")
    except Exception as e:
        logger.error(f"구독 메시지 전송 실패: {e}")

def main():
    """메인 함수"""
    logger.info("업비트 WebSocket 테스트 시작")
    
    # WebSocket 연결
    ws = websocket.WebSocketApp(
        "wss://api.upbit.com/websocket/v1",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    
    try:
        # 연결 시작
        ws.run_forever()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중지됨")
        ws.close()

if __name__ == "__main__":
    main()
