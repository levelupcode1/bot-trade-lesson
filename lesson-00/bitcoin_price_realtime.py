#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 실시간 표시 프로그램
0차시 맛보기 강의용 예제 코드
"""

import requests
import json
import time
from datetime import datetime

def get_bitcoin_price():
    """
    CoinGecko API를 사용하여 비트코인 현재 가격을 가져옵니다.
    
    Returns:
        dict: 가격 정보가 담긴 딕셔너리 또는 None (에러 시)
    """
    try:
        # CoinGecko API 엔드포인트 (API 키 불필요)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        # API 요청
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # HTTP 에러가 있으면 예외 발생
        
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

def format_price(price):
    """
    가격을 보기 좋게 포맷팅합니다.
    
    Args:
        price (float): 가격
        
    Returns:
        str: 포맷팅된 가격 문자열
    """
    return f"${price:,.2f}"

def format_change(change):
    """
    24시간 변동률을 보기 좋게 포맷팅합니다.
    
    Args:
        change (float): 변동률
        
    Returns:
        str: 포맷팅된 변동률 문자열
    """
    if change > 0:
        return f"+{change:.2f}%"
    else:
        return f"{change:.2f}%"

def display_price_info(price_data):
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
    
    # 콘솔 화면 지우기 (Windows/Unix 호환)
    print("\033[2J\033[H", end="")
    
    print("=" * 50)
    print("🚀 비트코인 실시간 가격 모니터")
    print("=" * 50)
    print(f"⏰ 업데이트 시간: {current_time}")
    print(f"💰 현재 가격: {format_price(price)}")
    print(f"📈 24시간 변동: {format_change(change)}")
    print("=" * 50)
    print("💡 종료하려면 Ctrl+C를 누르세요")
    print()

def main():
    """
    메인 실행 함수
    """
    print("🚀 비트코인 가격 실시간 모니터를 시작합니다...")
    print("📡 API에서 데이터를 가져오는 중...")
    
    update_interval = 30  # 30초마다 업데이트
    
    try:
        while True:
            # 가격 정보 가져오기
            price_data = get_bitcoin_price()
            
            if price_data:
                display_price_info(price_data)
            else:
                print("❌ 가격 정보를 가져올 수 없습니다. 10초 후 다시 시도합니다...")
                time.sleep(10)
                continue
            
            # 다음 업데이트까지 대기
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다. 감사합니다!")
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
