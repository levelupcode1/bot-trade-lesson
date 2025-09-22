#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업비트 API 통합 클래스
시장 데이터 조회, 계좌 조회, 주문 실행 기능을 포함한 완전한 API 클라이언트
"""

import requests
import json
import time
import hmac
import hashlib
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class UpbitAPI:
    """
    업비트 API 통합 클래스
    
    주요 기능:
    - 시장 데이터 조회 (인증 불필요)
    - 계좌 조회 (인증 필요)
    - 주문 실행 (인증 필요)
    - JWT 토큰 기반 인증
    - 자동 재시도 및 오류 처리
    - 요청 제한 관리
    """
    
    def __init__(self, access_key: str = None, secret_key: str = None, 
                 base_url: str = "https://api.upbit.com", 
                 timeout: int = 30, max_retries: int = 3):
        """
        업비트 API 클라이언트 초기화
        
        Args:
            access_key (str): API Access Key (환경변수에서 자동 로드 가능)
            secret_key (str): API Secret Key (환경변수에서 자동 로드 가능)
            base_url (str): API 기본 URL
            timeout (int): 요청 타임아웃 (초)
            max_retries (int): 최대 재시도 횟수
        """
        # API 키 설정 (환경변수 우선)
        self.access_key = access_key or os.getenv('UPBIT_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('UPBIT_SECRET_KEY')
        
        # 기본 설정
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 요청 제한 관리
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 요청 간 최소 간격 (초)
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UpbitAPI/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # 로깅 설정
        self.setup_logging()
        
        # API 키 검증
        self._validate_api_keys()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('upbit_api.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _validate_api_keys(self):
        """API 키 유효성 검증"""
        if not self.access_key or not self.secret_key:
            self.logger.warning("API 키가 설정되지 않았습니다. 인증이 필요한 기능을 사용할 수 없습니다.")
            self.authenticated = False
        else:
            self.authenticated = True
            self.logger.info("API 키가 설정되었습니다.")
    
    def _rate_limit_control(self):
        """요청 제한 관리"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _create_jwt_token(self) -> str:
        """
        JWT 토큰 생성
        
        Returns:
            str: JWT 토큰
        """
        if not self.authenticated:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _create_signature(self, query_string: str) -> str:
        """
        요청 서명 생성
        
        Args:
            query_string (str): 쿼리 문자열
            
        Returns:
            str: HMAC-SHA512 서명
        """
        if not self.authenticated:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, require_auth: bool = False) -> Dict:
        """
        HTTP 요청 실행
        
        Args:
            method (str): HTTP 메서드 (GET, POST, DELETE)
            endpoint (str): API 엔드포인트
            params (Dict): URL 파라미터
            data (Dict): 요청 본문 데이터
            require_auth (bool): 인증 필요 여부
            
        Returns:
            Dict: API 응답 데이터
        """
        # 요청 제한 관리
        self._rate_limit_control()
        
        # URL 구성
        url = f"{self.base_url}{endpoint}"
        
        # 인증이 필요한 경우 JWT 토큰 추가
        headers = {}
        if require_auth:
            if not self.authenticated:
                raise ValueError("인증이 필요한 요청입니다. API 키를 설정해주세요.")
            
            jwt_token = self._create_jwt_token()
            headers['Authorization'] = f'Bearer {jwt_token}'
        
        # 쿼리 파라미터 처리
        if params:
            query_string = urlencode(params)
            if require_auth:
                signature = self._create_signature(query_string)
                params['signature'] = signature
            url += f"?{urlencode(params)}"
        
        # 재시도 로직
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"요청 시도 {attempt + 1}/{self.max_retries}: {method} {url}")
                
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, headers=headers, json=data, timeout=self.timeout)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, headers=headers, timeout=self.timeout)
                else:
                    raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
                
                # 응답 상태 코드 확인
                response.raise_for_status()
                
                # JSON 응답 파싱
                result = response.json()
                
                # 에러 응답 확인
                if isinstance(result, dict) and 'error' in result:
                    error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
                    raise Exception(f"API 오류: {error_msg}")
                
                self.logger.debug(f"요청 성공: {method} {endpoint}")
                return result
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"요청 타임아웃 (시도 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise Exception("요청 타임아웃: 서버 응답이 없습니다.")
                time.sleep(2 ** attempt)  # 지수 백오프
                
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise Exception("연결 오류: 서버에 연결할 수 없습니다.")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    self.logger.warning("요청 제한 초과. 대기 후 재시도합니다.")
                    time.sleep(5)
                    continue
                elif e.response.status_code in [401, 403]:
                    raise Exception(f"인증 오류: {e.response.text}")
                else:
                    raise Exception(f"HTTP 오류 {e.response.status_code}: {e.response.text}")
                    
            except Exception as e:
                self.logger.error(f"요청 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        raise Exception("최대 재시도 횟수를 초과했습니다.")
    
    # ==================== 시장 데이터 조회 API ====================
    
    def get_markets(self) -> List[Dict]:
        """
        전체 마켓 코드 조회
        
        Returns:
            List[Dict]: 마켓 정보 리스트
        """
        try:
            result = self._make_request('GET', '/v1/market/all')
            self.logger.info(f"마켓 코드 조회 완료: {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"마켓 코드 조회 실패: {e}")
            raise
    
    def get_ticker(self, markets: List[str] = None) -> List[Dict]:
        """
        현재가 정보 조회
        
        Args:
            markets (List[str]): 마켓 코드 리스트 (None이면 전체)
            
        Returns:
            List[Dict]: 현재가 정보 리스트
        """
        try:
            params = {}
            if markets:
                params['markets'] = ','.join(markets)
            
            result = self._make_request('GET', '/v1/ticker', params=params)
            self.logger.info(f"현재가 정보 조회 완료: {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"현재가 정보 조회 실패: {e}")
            raise
    
    def get_candles(self, market: str, count: int = 200, unit: str = 'days', 
                   to: str = None) -> List[Dict]:
        """
        캔들(차트) 데이터 조회
        
        Args:
            market (str): 마켓 코드
            count (int): 캔들 개수 (최대 200)
            unit (str): 캔들 단위 (minutes, days, weeks, months)
            to (str): 마지막 캔들 시각 (ISO 8601)
            
        Returns:
            List[Dict]: 캔들 데이터 리스트
        """
        try:
            params = {
                'market': market,
                'count': min(count, 200)
            }
            
            if to:
                params['to'] = to
            
            endpoint = f'/v1/candles/{unit}'
            result = self._make_request('GET', endpoint, params=params)
            self.logger.info(f"캔들 데이터 조회 완료: {market} {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"캔들 데이터 조회 실패: {e}")
            raise
    
    def get_orderbook(self, markets: List[str]) -> List[Dict]:
        """
        호가 정보 조회
        
        Args:
            markets (List[str]): 마켓 코드 리스트
            
        Returns:
            List[Dict]: 호가 정보 리스트
        """
        try:
            params = {'markets': ','.join(markets)}
            result = self._make_request('GET', '/v1/orderbook', params=params)
            self.logger.info(f"호가 정보 조회 완료: {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"호가 정보 조회 실패: {e}")
            raise
    
    def get_trades_ticks(self, market: str, count: int = 100, 
                        to: str = None, cursor: str = None) -> List[Dict]:
        """
        체결 내역 조회
        
        Args:
            market (str): 마켓 코드
            count (int): 체결 개수 (최대 500)
            to (str): 마지막 체결 시각 (ISO 8601)
            cursor (str): 페이지네이션 커서
            
        Returns:
            List[Dict]: 체결 내역 리스트
        """
        try:
            params = {
                'market': market,
                'count': min(count, 500)
            }
            
            if to:
                params['to'] = to
            if cursor:
                params['cursor'] = cursor
            
            result = self._make_request('GET', '/v1/trades/ticks', params=params)
            self.logger.info(f"체결 내역 조회 완료: {market} {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"체결 내역 조회 실패: {e}")
            raise
    
    # ==================== 계좌 조회 API ====================
    
    def get_accounts(self) -> List[Dict]:
        """
        전체 계좌 조회
        
        Returns:
            List[Dict]: 계좌 정보 리스트
        """
        try:
            result = self._make_request('GET', '/v1/accounts', require_auth=True)
            self.logger.info(f"계좌 조회 완료: {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"계좌 조회 실패: {e}")
            raise
    
    def get_orders(self, market: str = None, state: str = None, 
                  page: int = 1, limit: int = 100, order_by: str = 'desc') -> List[Dict]:
        """
        주문 리스트 조회
        
        Args:
            market (str): 마켓 코드
            state (str): 주문 상태 (wait, done, cancel)
            page (int): 페이지 번호
            limit (int): 페이지당 개수 (최대 100)
            order_by (str): 정렬 순서 (asc, desc)
            
        Returns:
            List[Dict]: 주문 리스트
        """
        try:
            params = {
                'page': page,
                'limit': min(limit, 100),
                'order_by': order_by
            }
            
            if market:
                params['market'] = market
            if state:
                params['state'] = state
            
            result = self._make_request('GET', '/v1/orders', params=params, require_auth=True)
            self.logger.info(f"주문 리스트 조회 완료: {len(result)}개")
            return result
        except Exception as e:
            self.logger.error(f"주문 리스트 조회 실패: {e}")
            raise
    
    def get_order_detail(self, uuid: str) -> Dict:
        """
        개별 주문 조회
        
        Args:
            uuid (str): 주문 UUID
            
        Returns:
            Dict: 주문 상세 정보
        """
        try:
            params = {'uuid': uuid}
            result = self._make_request('GET', '/v1/order', params=params, require_auth=True)
            self.logger.info(f"주문 상세 조회 완료: {uuid}")
            return result
        except Exception as e:
            self.logger.error(f"주문 상세 조회 실패: {e}")
            raise
    
    # ==================== 주문 실행 API ====================
    
    def create_order(self, market: str, side: str, volume: str = None, 
                    price: str = None, ord_type: str = 'limit', 
                    identifier: str = None) -> Dict:
        """
        주문 생성
        
        Args:
            market (str): 마켓 코드
            side (str): 주문 종류 (bid: 매수, ask: 매도)
            volume (str): 주문 수량
            price (str): 주문 가격
            ord_type (str): 주문 타입 (limit, price, market)
            identifier (str): 조회용 사용자 지정값
            
        Returns:
            Dict: 주문 결과
        """
        try:
            data = {
                'market': market,
                'side': side,
                'ord_type': ord_type
            }
            
            if volume:
                data['volume'] = volume
            if price:
                data['price'] = price
            if identifier:
                data['identifier'] = identifier
            
            result = self._make_request('POST', '/v1/orders', data=data, require_auth=True)
            self.logger.info(f"주문 생성 완료: {market} {side} {volume}@{price}")
            return result
        except Exception as e:
            self.logger.error(f"주문 생성 실패: {e}")
            raise
    
    def cancel_order(self, uuid: str) -> Dict:
        """
        주문 취소
        
        Args:
            uuid (str): 주문 UUID
            
        Returns:
            Dict: 취소 결과
        """
        try:
            params = {'uuid': uuid}
            result = self._make_request('DELETE', '/v1/order', params=params, require_auth=True)
            self.logger.info(f"주문 취소 완료: {uuid}")
            return result
        except Exception as e:
            self.logger.error(f"주문 취소 실패: {e}")
            raise
    
    # ==================== 유틸리티 메서드 ====================
    
    def get_balance(self, currency: str = None) -> Union[Dict, List[Dict]]:
        """
        잔고 조회 (편의 메서드)
        
        Args:
            currency (str): 통화 코드 (None이면 전체)
            
        Returns:
            Union[Dict, List[Dict]]: 잔고 정보
        """
        try:
            accounts = self.get_accounts()
            
            if currency:
                for account in accounts:
                    if account['currency'] == currency:
                        return account
                return {}
            else:
                return accounts
        except Exception as e:
            self.logger.error(f"잔고 조회 실패: {e}")
            raise
    
    def get_current_price(self, market: str) -> float:
        """
        현재가 조회 (편의 메서드)
        
        Args:
            market (str): 마켓 코드
            
        Returns:
            float: 현재가
        """
        try:
            ticker = self.get_ticker([market])
            if ticker:
                return float(ticker[0]['trade_price'])
            return 0.0
        except Exception as e:
            self.logger.error(f"현재가 조회 실패: {e}")
            raise
    
    def get_market_summary(self, markets: List[str] = None) -> Dict[str, Dict]:
        """
        마켓 요약 정보 조회 (편의 메서드)
        
        Args:
            markets (List[str]): 마켓 코드 리스트
            
        Returns:
            Dict[str, Dict]: 마켓별 요약 정보
        """
        try:
            tickers = self.get_ticker(markets)
            summary = {}
            
            for ticker in tickers:
                market = ticker['market']
                summary[market] = {
                    'price': ticker['trade_price'],
                    'change_rate': ticker['signed_change_rate'],
                    'change_price': ticker['signed_change_price'],
                    'volume': ticker['acc_trade_volume_24h'],
                    'high_price': ticker['high_price'],
                    'low_price': ticker['low_price']
                }
            
            return summary
        except Exception as e:
            self.logger.error(f"마켓 요약 조회 실패: {e}")
            raise
    
    def get_request_stats(self) -> Dict:
        """
        요청 통계 조회
        
        Returns:
            Dict: 요청 통계 정보
        """
        return {
            'total_requests': self.request_count,
            'last_request_time': self.last_request_time,
            'rate_limit_delay': self.rate_limit_delay,
            'authenticated': self.authenticated
        }
