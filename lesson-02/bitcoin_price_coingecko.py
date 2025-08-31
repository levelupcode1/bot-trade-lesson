#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinGecko API를 사용한 비트코인 현재가 조회
requests 라이브러리를 사용하고 종합적인 오류 처리를 포함합니다.
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

class CoinGeckoBitcoinPrice:
    def __init__(self):
        """CoinGecko API 클라이언트 초기화"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # User-Agent 설정 (API 호환성을 위해)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 요청 제한 관리를 위한 설정
        self.max_retries = 3
        self.retry_delay = 1  # 초
        
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        API 요청을 수행하고 응답을 반환합니다.
        
        Args:
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            
        Returns:
            API 응답 데이터 또는 None (오류 시)
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                print(f"API 요청 시도 {attempt + 1}/{self.max_retries}: {url}")
                
                response = self.session.get(url, params=params, timeout=10)
                
                # HTTP 상태 코드 확인
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit 초과
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay * 2))
                    print(f"Rate limit 초과. {retry_after}초 후 재시도합니다...")
                    time.sleep(retry_after)
                elif response.status_code == 404:
                    print(f"요청한 리소스를 찾을 수 없습니다: {endpoint}")
                    return None
                elif response.status_code >= 500:
                    print(f"서버 오류 (HTTP {response.status_code}). 재시도합니다...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"HTTP 오류 {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"요청 시간 초과 (시도 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.ConnectionError:
                print(f"연결 오류 (시도 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.RequestException as e:
                print(f"요청 오류: {e}")
                return None
                
            except json.JSONDecodeError:
                print("응답을 JSON으로 파싱할 수 없습니다.")
                return None
                
            except Exception as e:
                print(f"예상치 못한 오류: {e}")
                return None
        
        print(f"최대 재시도 횟수({self.max_retries})를 초과했습니다.")
        return None
    
    def get_bitcoin_price(self, currency: str = "krw") -> Optional[Dict[str, Any]]:
        """
        비트코인의 현재 가격 정보를 조회합니다.
        
        Args:
            currency: 가격 표시 통화 (기본값: "krw")
            
        Returns:
            비트코인 가격 정보 또는 None (오류 시)
        """
        try:
            endpoint = "/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            print(f"비트코인 가격 조회 중... (통화: {currency.upper()})")
            
            data = self._make_request(endpoint, params)
            
            if data and "bitcoin" in data:
                return data["bitcoin"]
            else:
                print("비트코인 가격 데이터를 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"비트코인 가격 조회 중 오류 발생: {e}")
            return None
    
    def get_bitcoin_detailed_info(self) -> Optional[Dict[str, Any]]:
        """
        비트코인의 상세 정보를 조회합니다.
        
        Returns:
            비트코인 상세 정보 또는 None (오류 시)
        """
        try:
            endpoint = "/coins/bitcoin"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            
            print("비트코인 상세 정보 조회 중...")
            
            return self._make_request(endpoint, params)
            
        except Exception as e:
            print(f"비트코인 상세 정보 조회 중 오류 발생: {e}")
            return None
    
    def format_price(self, price: float, currency: str = "krw") -> str:
        """
        가격을 사용자 친화적인 형식으로 포맷팅합니다.
        
        Args:
            price: 가격
            currency: 통화
            
        Returns:
            포맷팅된 가격 문자열
        """
        if currency.lower() == "krw":
            return f"{price:,.0f}원"
        elif currency.lower() == "usd":
            return f"${price:,.2f}"
        elif currency.lower() == "eur":
            return f"€{price:,.2f}"
        else:
            return f"{price:,.2f} {currency.upper()}"
    
    def display_price_info(self, price_data: Dict[str, Any], currency: str = "krw"):
        """
        가격 정보를 사용자 친화적으로 표시합니다.
        
        Args:
            price_data: 가격 데이터
            currency: 통화
        """
        if not price_data:
            print("표시할 가격 데이터가 없습니다.")
            return
        
        print("\n" + "="*60)
        print("비트코인 현재가 정보")
        print("="*60)
        
        # 현재 가격
        if currency in price_data:
            price = price_data[currency]
            formatted_price = self.format_price(price, currency)
            print(f"현재 가격: {formatted_price}")
        
        # 시가총액
        if f"{currency}_market_cap" in price_data:
            market_cap = price_data[f"{currency}_market_cap"]
            formatted_market_cap = self.format_price(market_cap, currency)
            print(f"시가총액: {formatted_market_cap}")
        
        # 24시간 거래량
        if f"{currency}_24h_vol" in price_data:
            volume = price_data[f"{currency}_24h_vol"]
            formatted_volume = self.format_price(volume, currency)
            print(f"24시간 거래량: {formatted_volume}")
        
        # 24시간 가격 변화
        if f"{currency}_24h_change" in price_data:
            change = price_data[f"{currency}_24h_change"]
            change_symbol = "📈" if change >= 0 else "📉"
            print(f"24시간 변화: {change_symbol} {change:+.2f}%")
        
        # 마지막 업데이트 시간
        if "last_updated_at" in price_data:
            timestamp = price_data["last_updated_at"]
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                print(f"마지막 업데이트: {formatted_time}")
        
        print("="*60)
    
    def display_detailed_info(self, detailed_data: Dict[str, Any]):
        """
        상세 정보를 표시합니다.
        
        Args:
            detailed_data: 상세 데이터
        """
        if not detailed_data:
            print("표시할 상세 데이터가 없습니다.")
            return
        
        print("\n" + "="*60)
        print("비트코인 상세 정보")
        print("="*60)
        
        # 기본 정보
        if "name" in detailed_data:
            print(f"이름: {detailed_data['name']}")
        
        if "symbol" in detailed_data:
            print(f"심볼: {detailed_data['symbol'].upper()}")
        
        if "genesis_date" in detailed_data:
            print(f"생성일: {detailed_data['genesis_date']}")
        
        # 시장 데이터
        if "market_data" in detailed_data:
            market_data = detailed_data["market_data"]
            
            if "current_price" in market_data:
                print("\n현재 가격:")
                for currency, price in market_data["current_price"].items():
                    if price:
                        formatted_price = self.format_price(price, currency)
                        print(f"  {currency.upper()}: {formatted_price}")
            
            if "market_cap" in market_data:
                print("\n시가총액:")
                for currency, cap in market_data["market_cap"].items():
                    if cap:
                        formatted_cap = self.format_price(cap, currency)
                        print(f"  {currency.upper()}: {formatted_cap}")
        
        print("="*60)

def main():
    """메인 함수"""
    print("CoinGecko API를 사용한 비트코인 가격 조회 프로그램")
    print("-" * 60)
    
    # CoinGecko 클라이언트 생성
    client = CoinGeckoBitcoinPrice()
    
    try:
        # 1. 간단한 가격 정보 조회 (KRW)
        print("\n1. 한국 원화 기준 비트코인 가격 조회")
        price_data_krw = client.get_bitcoin_price("krw")
        if price_data_krw:
            client.display_price_info(price_data_krw, "krw")
        
        # 2. 간단한 가격 정보 조회 (USD)
        print("\n2. 미국 달러 기준 비트코인 가격 조회")
        price_data_usd = client.get_bitcoin_price("usd")
        if price_data_usd:
            client.display_price_info(price_data_usd, "usd")
        
        # 3. 상세 정보 조회
        print("\n3. 비트코인 상세 정보 조회")
        detailed_data = client.get_bitcoin_detailed_info()
        if detailed_data:
            client.display_detailed_info(detailed_data)
        
        print("\n프로그램이 성공적으로 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n프로그램 실행 중 예상치 못한 오류가 발생했습니다: {e}")
    finally:
        print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
