#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import jwt
import uuid
import hashlib
import hmac
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

class RateLimiter:
    """API 요청 제한 관리"""
    
    def __init__(self, requests_per_second=10, requests_per_minute=600):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        
        # 요청 기록 저장
        self.second_requests = []
        self.minute_requests = []
        
        # 스레드 안전을 위한 락
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """요청 제한에 걸리지 않도록 대기"""
        with self.lock:
            current_time = time.time()
            
            # 1초 이내 요청 정리
            self.second_requests = [t for t in self.second_requests if current_time - t < 1]
            
            # 1분 이내 요청 정리
            self.minute_requests = [t for t in self.minute_requests if current_time - t < 60]
            
            # 1초 제한 체크
            if len(self.second_requests) >= self.requests_per_second:
                sleep_time = 1 - (current_time - self.second_requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            # 1분 제한 체크
            if len(self.minute_requests) >= self.requests_per_minute:
                sleep_time = 60 - (current_time - self.minute_requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            # 요청 기록 추가
            self.second_requests.append(current_time)
            self.minute_requests.append(current_time)

class CacheManager:
    """API 응답 캐싱 관리자"""
    
    def __init__(self, default_ttl: int = 60):
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.default_ttl:
                    return data
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, data: Any, ttl: int = None):
        """캐시에 데이터 저장"""
        with self.lock:
            self.cache[key] = (data, time.time())
    
    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()

class OptimizedUpbitAPI:
    """효율성이 최적화된 업비트 API 클라이언트"""
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.upbit.com"
        
        # 캐싱 시스템
        self.cache = CacheManager()
        
        # 로깅 설정
        self.setup_logging()
        
        # 세션 풀 설정
        self.session_pool = self._create_session_pool()
        
        # 요청 제한 관리
        self.rate_limiter = RateLimiter()
        
        # 병렬 처리용 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _create_session_pool(self):
        """세션 풀 생성"""
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        
        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        session.headers.update({
            'User-Agent': 'OptimizedUpbitAPI/2.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('optimized_upbit_api.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @lru_cache(maxsize=128)
    def create_jwt_token(self) -> str:
        """JWT 토큰 생성 (캐싱 적용)"""
        if not self.access_key or not self.secret_key:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def create_signature(self, query_string: str) -> str:
        """요청 서명 생성 (주문 API용)"""
        if not self.secret_key:
            raise ValueError("Secret Key가 설정되지 않았습니다.")
        
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, 
                     data: dict = None, require_auth: bool = False, 
                     use_cache: bool = True, cache_ttl: int = 60) -> dict:
        """최적화된 API 요청 실행"""
        
        # 캐시 키 생성
        cache_key = f"{method}:{endpoint}:{str(params)}:{str(data)}"
        
        # 캐시에서 조회
        if use_cache and method == 'GET':
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"캐시에서 데이터 조회: {endpoint}")
                return cached_data
        
        # Rate Limit 체크
        self.rate_limiter.wait_if_needed()
        
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
            
            # 요청 실행 (타임아웃 단축)
            response = self.session_pool.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                headers=headers,
                timeout=10  # 30초 → 10초로 단축
            )
            
            # 응답 상태 코드 확인
            if response.status_code == 200:
                result = response.json()
                
                # GET 요청인 경우 캐시에 저장
                if use_cache and method == 'GET':
                    self.cache.set(cache_key, result, cache_ttl)
                
                return result
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
    
    # ==================== 최적화된 시장 데이터 조회 API ====================
    
    def get_markets(self, use_cache: bool = True) -> List[dict]:
        """마켓 목록 조회 (캐싱 적용)"""
        try:
            self.logger.info("마켓 목록 조회 중...")
            markets = self._make_request('GET', '/v1/market/all', use_cache=use_cache, cache_ttl=3600)  # 1시간 캐싱
            self.logger.info(f"마켓 목록 조회 완료: {len(markets)}개")
            return markets
        except Exception as e:
            self.logger.error(f"마켓 목록 조회 실패: {e}")
            raise
    
    def get_ticker(self, markets: List[str] = None, use_cache: bool = True) -> List[dict]:
        """현재가 조회 (캐싱 적용)"""
        try:
            params = {}
            if markets:
                params['markets'] = ','.join(markets)
            
            self.logger.info(f"현재가 조회 중... (마켓: {markets or '전체'})")
            tickers = self._make_request('GET', '/v1/ticker', params=params, use_cache=use_cache, cache_ttl=30)  # 30초 캐싱
            self.logger.info(f"현재가 조회 완료: {len(tickers)}개")
            return tickers
        except Exception as e:
            self.logger.error(f"현재가 조회 실패: {e}")
            raise
    
    def get_multiple_tickers_parallel(self, market_lists: List[List[str]]) -> List[List[dict]]:
        """여러 마켓 그룹의 현재가를 병렬로 조회"""
        try:
            self.logger.info(f"병렬 현재가 조회 시작: {len(market_lists)}개 그룹")
            
            # 병렬 처리로 여러 요청 동시 실행
            futures = []
            for markets in market_lists:
                future = self.executor.submit(self.get_ticker, markets)
                futures.append(future)
            
            # 결과 수집
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=15)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"병렬 조회 실패: {e}")
                    results.append([])
            
            self.logger.info(f"병렬 현재가 조회 완료: {len(results)}개 그룹")
            return results
            
        except Exception as e:
            self.logger.error(f"병렬 현재가 조회 실패: {e}")
            raise
    
    def get_candles(self, market: str, count: int = 200, 
                   unit: str = 'days', use_cache: bool = True) -> List[dict]:
        """캔들 데이터 조회 (캐싱 적용)"""
        try:
            params = {
                'market': market,
                'count': count
            }
            
            # 캐싱 TTL 설정 (단위별로 다르게)
            cache_ttl = {
                'minutes': 60,    # 1분 캐싱
                'days': 3600,     # 1시간 캐싱
                'weeks': 7200,    # 2시간 캐싱
                'months': 14400   # 4시간 캐싱
            }.get(unit, 3600)
            
            self.logger.info(f"캔들 데이터 조회 중... (마켓: {market}, 단위: {unit})")
            candles = self._make_request('GET', f'/v1/candles/{unit}', params=params, 
                                       use_cache=use_cache, cache_ttl=cache_ttl)
            self.logger.info(f"캔들 데이터 조회 완료: {len(candles)}개")
            return candles
        except Exception as e:
            self.logger.error(f"캔들 데이터 조회 실패: {e}")
            raise
    
    # ==================== 최적화된 편의 메서드 ====================
    
    def get_current_price(self, market: str) -> float:
        """특정 마켓 현재가 조회 (캐싱 적용)"""
        try:
            # 단일 마켓 조회로 최적화
            tickers = self.get_ticker([market])
            if tickers:
                return float(tickers[0]['trade_price'])
            return 0.0
        except Exception as e:
            self.logger.error(f"현재가 조회 실패: {e}")
            return 0.0
    
    def get_multiple_current_prices(self, markets: List[str]) -> Dict[str, float]:
        """여러 마켓의 현재가를 한 번에 조회"""
        try:
            tickers = self.get_ticker(markets)
            prices = {}
            for ticker in tickers:
                prices[ticker['market']] = float(ticker['trade_price'])
            return prices
        except Exception as e:
            self.logger.error(f"다중 현재가 조회 실패: {e}")
            return {}
    
    def get_market_info(self, market: str) -> dict:
        """마켓 정보 조회 (캐싱 적용)"""
        try:
            tickers = self.get_ticker([market])
            if tickers:
                return tickers[0]
            return {}
        except Exception as e:
            self.logger.error(f"마켓 정보 조회 실패: {e}")
            return {}
    
    def batch_get_market_info(self, markets: List[str]) -> Dict[str, dict]:
        """여러 마켓의 정보를 한 번에 조회"""
        try:
            tickers = self.get_ticker(markets)
            market_info = {}
            for ticker in tickers:
                market_info[ticker['market']] = ticker
            return market_info
        except Exception as e:
            self.logger.error(f"배치 마켓 정보 조회 실패: {e}")
            return {}
    
    # ==================== 메모리 최적화 메서드 ====================
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        self.logger.info("캐시가 초기화되었습니다.")
    
    def get_cache_stats(self) -> dict:
        """캐시 통계 조회"""
        with self.cache.lock:
            return {
                'cache_size': len(self.cache.cache),
                'cache_keys': list(self.cache.cache.keys())
            }
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        self.session_pool.close()
        self.cache.clear()
        self.logger.info("리소스가 정리되었습니다.")

# 사용 예시
def main():
    """최적화된 API 사용 예시"""
    try:
        # API 클라이언트 생성
        api = OptimizedUpbitAPI()
        
        print("🚀 최적화된 업비트 API 클라이언트 테스트")
        print("=" * 50)
        
        # 1. 캐싱 테스트
        print("\n📊 캐싱 테스트...")
        start_time = time.time()
        markets1 = api.get_markets()
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        markets2 = api.get_markets()  # 캐시에서 조회
        second_call_time = time.time() - start_time
        
        print(f"첫 번째 호출: {first_call_time:.3f}초")
        print(f"두 번째 호출 (캐시): {second_call_time:.3f}초")
        print(f"성능 향상: {first_call_time/second_call_time:.1f}배")
        
        # 2. 병렬 처리 테스트
        print("\n⚡ 병렬 처리 테스트...")
        market_groups = [
            ['KRW-BTC', 'KRW-ETH'],
            ['KRW-XRP', 'KRW-ADA'],
            ['KRW-DOT', 'KRW-LINK']
        ]
        
        start_time = time.time()
        results = api.get_multiple_tickers_parallel(market_groups)
        parallel_time = time.time() - start_time
        
        print(f"병렬 처리 시간: {parallel_time:.3f}초")
        print(f"조회된 그룹 수: {len(results)}")
        
        # 3. 배치 조회 테스트
        print("\n📦 배치 조회 테스트...")
        markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        
        start_time = time.time()
        prices = api.get_multiple_current_prices(markets)
        batch_time = time.time() - start_time
        
        print(f"배치 조회 시간: {batch_time:.3f}초")
        for market, price in prices.items():
            print(f"  {market}: {price:,}원")
        
        # 4. 캐시 통계
        print("\n📈 캐시 통계...")
        stats = api.get_cache_stats()
        print(f"캐시 크기: {stats['cache_size']}개")
        
        # 5. 리소스 정리
        api.cleanup()
        
        print("\n✅ 모든 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
