#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import jwt
import uuid
import hashlib
import hmac
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

class UpbitAPI:
    """
    업비트 API 연동 클래스
    
    주요 기능:
    - 시장 데이터 조회 (인증 불필요)
    - 계좌 조회 (인증 필요)
    - 주문 실행 (인증 필요)
    - API 키 인증 및 오류 처리
    """
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        """
        초기화
        
        Args:
            access_key (str): 업비트 Access Key (선택사항)
            secret_key (str): 업비트 Secret Key (선택사항)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.upbit.com"
        
        # 로깅 설정
        self.setup_logging()
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UpbitAPI/1.0',
            'Accept': 'application/json'
        })
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('upbit_api.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_jwt_token(self) -> str:
        """
        JWT 토큰 생성 (인증이 필요한 API용)
        
        Returns:
            str: JWT 토큰
        """
        if not self.access_key or not self.secret_key:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def create_signature(self, query_string: str) -> str:
        """
        요청 서명 생성 (주문 API용)
        
        Args:
            query_string (str): 쿼리 스트링
            
        Returns:
            str: 서명된 해시값
        """
        if not self.secret_key:
            raise ValueError("Secret Key가 설정되지 않았습니다.")
        
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, 
                     data: dict = None, require_auth: bool = False) -> dict:
        """
        API 요청 실행
        
        Args:
            method (str): HTTP 메서드 (GET, POST, DELETE)
            endpoint (str): API 엔드포인트
            params (dict): URL 파라미터
            data (dict): 요청 데이터
            require_auth (bool): 인증 필요 여부
            
        Returns:
            dict: API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        try:
            # 인증이 필요한 경우 JWT 토큰 추가
            if require_auth:
                jwt_token = self.create_jwt_token()
                headers['Authorization'] = f'Bearer {jwt_token}'
            
            # 주문 API의 경우 서명 추가
            if data and 'market' in data:
                query_string = urlencode(data, doseq=True)
                signature = self.create_signature(query_string)
                data['signature'] = signature
            
            # 요청 실행
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                headers=headers,
                timeout=30
            )
            
            # 응답 상태 코드 확인
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise ValueError("인증 실패: API 키를 확인하세요.")
            elif response.status_code == 429:
                raise ValueError("요청 제한 초과: 잠시 후 다시 시도하세요.")
            else:
                error_msg = f"API 오류: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error']['message']}"
                except:
                    pass
                raise ValueError(error_msg)
                
        except requests.exceptions.Timeout:
            raise ValueError("요청 시간 초과")
        except requests.exceptions.ConnectionError:
            raise ValueError("네트워크 연결 오류")
        except Exception as e:
            self.logger.error(f"API 요청 오류: {e}")
            raise
    
    # ==================== 시장 데이터 조회 API ====================
    
    def get_markets(self) -> List[dict]:
        """
        마켓 목록 조회
        
        Returns:
            List[dict]: 마켓 목록
        """
        try:
            self.logger.info("마켓 목록 조회 중...")
            markets = self._make_request('GET', '/v1/market/all')
            self.logger.info(f"마켓 목록 조회 완료: {len(markets)}개")
            return markets
        except Exception as e:
            self.logger.error(f"마켓 목록 조회 실패: {e}")
            raise
    
    def get_ticker(self, markets: List[str] = None) -> List[dict]:
        """
        현재가 조회
        
        Args:
            markets (List[str]): 조회할 마켓 코드 리스트 (None이면 전체)
            
        Returns:
            List[dict]: 현재가 정보
        """
        try:
            params = {}
            if markets:
                params['markets'] = ','.join(markets)
            
            self.logger.info(f"현재가 조회 중... (마켓: {markets or '전체'})")
            tickers = self._make_request('GET', '/v1/ticker', params=params)
            self.logger.info(f"현재가 조회 완료: {len(tickers)}개")
            return tickers
        except Exception as e:
            self.logger.error(f"현재가 조회 실패: {e}")
            raise
    
    def get_candles(self, market: str, count: int = 200, 
                   unit: str = 'days') -> List[dict]:
        """
        캔들 데이터 조회
        
        Args:
            market (str): 마켓 코드
            count (int): 조회할 캔들 개수
            unit (str): 캔들 단위 (minutes, days, weeks, months)
            
        Returns:
            List[dict]: 캔들 데이터
        """
        try:
            params = {
                'market': market,
                'count': count
            }
            
            self.logger.info(f"캔들 데이터 조회 중... (마켓: {market}, 단위: {unit})")
            candles = self._make_request('GET', f'/v1/candles/{unit}', params=params)
            self.logger.info(f"캔들 데이터 조회 완료: {len(candles)}개")
            return candles
        except Exception as e:
            self.logger.error(f"캔들 데이터 조회 실패: {e}")
            raise
    
    def get_orderbook(self, markets: List[str]) -> List[dict]:
        """
        호가 정보 조회
        
        Args:
            markets (List[str]): 조회할 마켓 코드 리스트
            
        Returns:
            List[dict]: 호가 정보
        """
        try:
            params = {'markets': ','.join(markets)}
            
            self.logger.info(f"호가 정보 조회 중... (마켓: {markets})")
            orderbook = self._make_request('GET', '/v1/orderbook', params=params)
            self.logger.info(f"호가 정보 조회 완료: {len(orderbook)}개")
            return orderbook
        except Exception as e:
            self.logger.error(f"호가 정보 조회 실패: {e}")
            raise
    
    def get_trades_ticks(self, market: str, count: int = 100) -> List[dict]:
        """
        체결 이력 조회
        
        Args:
            market (str): 마켓 코드
            count (int): 조회할 체결 개수
            
        Returns:
            List[dict]: 체결 이력
        """
        try:
            params = {
                'market': market,
                'count': count
            }
            
            self.logger.info(f"체결 이력 조회 중... (마켓: {market})")
            trades = self._make_request('GET', '/v1/trades/ticks', params=params)
            self.logger.info(f"체결 이력 조회 완료: {len(trades)}개")
            return trades
        except Exception as e:
            self.logger.error(f"체결 이력 조회 실패: {e}")
            raise
    
    # ==================== 계좌 조회 API ====================
    
    def get_accounts(self) -> List[dict]:
        """
        계정 잔고 조회
        
        Returns:
            List[dict]: 계정 잔고 정보
        """
        try:
            self.logger.info("계정 잔고 조회 중...")
            accounts = self._make_request('GET', '/v1/accounts', require_auth=True)
            self.logger.info(f"계정 잔고 조회 완료: {len(accounts)}개 자산")
            return accounts
        except Exception as e:
            self.logger.error(f"계정 잔고 조회 실패: {e}")
            raise
    
    def get_orders(self, market: str = None, state: str = None, 
                  page: int = 1, limit: int = 100) -> List[dict]:
        """
        주문 내역 조회
        
        Args:
            market (str): 마켓 코드 (선택사항)
            state (str): 주문 상태 (wait, done, cancel)
            page (int): 페이지 번호
            limit (int): 조회 개수
            
        Returns:
            List[dict]: 주문 내역
        """
        try:
            params = {
                'page': page,
                'limit': limit
            }
            if market:
                params['market'] = market
            if state:
                params['state'] = state
            
            self.logger.info(f"주문 내역 조회 중... (마켓: {market}, 상태: {state})")
            orders = self._make_request('GET', '/v1/orders', params=params, require_auth=True)
            self.logger.info(f"주문 내역 조회 완료: {len(orders)}개")
            return orders
        except Exception as e:
            self.logger.error(f"주문 내역 조회 실패: {e}")
            raise
    
    # ==================== 주문 실행 API ====================
    
    def create_order(self, market: str, side: str, volume: str = None, 
                    price: str = None, ord_type: str = 'limit') -> dict:
        """
        주문 생성
        
        Args:
            market (str): 마켓 코드
            side (str): 주문 종류 (bid: 매수, ask: 매도)
            volume (str): 주문 수량
            price (str): 주문 가격 (지정가 주문 시)
            ord_type (str): 주문 타입 (limit: 지정가, price: 시장가 매수, market: 시장가 매도)
            
        Returns:
            dict: 주문 결과
        """
        try:
            data = {
                'market': market,
                'side': side,
                'ord_type': ord_type
            }
            
            if ord_type == 'limit':
                if not volume or not price:
                    raise ValueError("지정가 주문은 수량과 가격이 필요합니다.")
                data['volume'] = volume
                data['price'] = price
            elif ord_type == 'price':
                if not price:
                    raise ValueError("시장가 매수는 가격이 필요합니다.")
                data['price'] = price
            elif ord_type == 'market':
                if not volume:
                    raise ValueError("시장가 매도는 수량이 필요합니다.")
                data['volume'] = volume
            
            self.logger.info(f"주문 생성 중... (마켓: {market}, 종류: {side}, 타입: {ord_type})")
            result = self._make_request('POST', '/v1/orders', data=data, require_auth=True)
            self.logger.info(f"주문 생성 완료: {result.get('uuid', 'N/A')}")
            return result
        except Exception as e:
            self.logger.error(f"주문 생성 실패: {e}")
            raise
    
    def cancel_order(self, uuid: str) -> dict:
        """
        주문 취소
        
        Args:
            uuid (str): 주문 UUID
            
        Returns:
            dict: 취소 결과
        """
        try:
            data = {'uuid': uuid}
            
            self.logger.info(f"주문 취소 중... (UUID: {uuid})")
            result = self._make_request('DELETE', f'/v1/order', data=data, require_auth=True)
            self.logger.info(f"주문 취소 완료: {uuid}")
            return result
        except Exception as e:
            self.logger.error(f"주문 취소 실패: {e}")
            raise
    
    # ==================== 편의 메서드 ====================
    
    def get_balance(self, currency: str = 'KRW') -> float:
        """
        특정 통화 잔고 조회
        
        Args:
            currency (str): 통화 코드
            
        Returns:
            float: 잔고
        """
        try:
            accounts = self.get_accounts()
            for account in accounts:
                if account['currency'] == currency:
                    return float(account['balance'])
            return 0.0
        except Exception as e:
            self.logger.error(f"잔고 조회 실패: {e}")
            return 0.0
    
    def get_current_price(self, market: str) -> float:
        """
        특정 마켓 현재가 조회
        
        Args:
            market (str): 마켓 코드
            
        Returns:
            float: 현재가
        """
        try:
            tickers = self.get_ticker([market])
            if tickers:
                return float(tickers[0]['trade_price'])
            return 0.0
        except Exception as e:
            self.logger.error(f"현재가 조회 실패: {e}")
            return 0.0
    
    def get_market_info(self, market: str) -> dict:
        """
        마켓 정보 조회 (현재가, 24시간 통계 등)
        
        Args:
            market (str): 마켓 코드
            
        Returns:
            dict: 마켓 정보
        """
        try:
            tickers = self.get_ticker([market])
            if tickers:
                return tickers[0]
            return {}
        except Exception as e:
            self.logger.error(f"마켓 정보 조회 실패: {e}")
            return {}

# 사용 예시
def main():
    """사용 예시"""
    try:
        # API 클라이언트 생성 (API 키 없이도 시장 데이터 조회 가능)
        api = UpbitAPI()
        
        print("🚀 업비트 API 클라이언트 테스트")
        print("=" * 50)
        
        # 1. 마켓 목록 조회
        print("\n📊 마켓 목록 조회...")
        markets = api.get_markets()
        krw_markets = [m for m in markets if m['market'].startswith('KRW-')]
        print(f"✅ KRW 마켓: {len(krw_markets)}개")
        
        # 2. 주요 마켓 현재가 조회
        print("\n💰 주요 마켓 현재가 조회...")
        major_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        tickers = api.get_ticker(major_markets)
        
        for ticker in tickers:
            print(f"  {ticker['market']}: {ticker['trade_price']:,}원 "
                  f"({ticker['signed_change_rate']:.2%})")
        
        # 3. 비트코인 캔들 데이터 조회
        print("\n📈 비트코인 일봉 데이터 조회...")
        candles = api.get_candles('KRW-BTC', count=5, unit='days')
        for candle in candles:
            print(f"  {candle['candle_date_time_kst']}: "
                  f"시가 {candle['opening_price']:,}원, "
                  f"고가 {candle['high_price']:,}원, "
                  f"저가 {candle['low_price']:,}원, "
                  f"종가 {candle['trade_price']:,}원")
        
        # 4. API 키가 있는 경우 계좌 조회
        print("\n💳 계좌 조회 (API 키 필요)...")
        try:
            # 실제 사용 시에는 API 키를 설정하세요
            # api_with_key = UpbitAPI(access_key="your_key", secret_key="your_secret")
            # accounts = api_with_key.get_accounts()
            print("  ⚠️  API 키가 설정되지 않아 계좌 조회를 건너뜁니다.")
        except Exception as e:
            print(f"  ❌ 계좌 조회 실패: {e}")
        
        print("\n✅ 모든 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
