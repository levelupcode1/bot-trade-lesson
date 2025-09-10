#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import jwt
import uuid
import hashlib
import hmac
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class UpbitErrorHandler:
    """업비트 API 오류 처리 클래스"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_error_time = {}
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: str = "") -> dict:
        """오류 처리 및 복구 방안 제시"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # 오류 카운트 증가
        error_key = f"{error_type}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_error_time[error_key] = time.time()
        
        # 오류별 처리
        if isinstance(error, requests.exceptions.HTTPError):
            return self._handle_http_error(error, context)
        elif isinstance(error, requests.exceptions.ConnectionError):
            return self._handle_connection_error(error, context)
        elif isinstance(error, requests.exceptions.Timeout):
            return self._handle_timeout_error(error, context)
        elif isinstance(error, ValueError):
            return self._handle_value_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError, context: str) -> dict:
        """HTTP 오류 처리"""
        status_code = error.response.status_code
        
        if status_code == 400:
            return {
                'type': 'BAD_REQUEST',
                'message': '잘못된 요청입니다. 파라미터를 확인하세요.',
                'action': '요청 파라미터 검증',
                'retry': False
            }
        elif status_code == 401:
            return {
                'type': 'UNAUTHORIZED',
                'message': '인증에 실패했습니다. API 키를 확인하세요.',
                'action': 'API 키 재설정',
                'retry': False
            }
        elif status_code == 403:
            return {
                'type': 'FORBIDDEN',
                'message': '권한이 없습니다. API 키 권한을 확인하세요.',
                'action': 'API 키 권한 확인',
                'retry': False
            }
        elif status_code == 429:
            return {
                'type': 'RATE_LIMIT',
                'message': '요청 제한을 초과했습니다.',
                'action': '요청 간격 조정',
                'retry': True,
                'retry_after': 60
            }
        elif status_code >= 500:
            return {
                'type': 'SERVER_ERROR',
                'message': '서버 오류가 발생했습니다.',
                'action': '잠시 후 재시도',
                'retry': True,
                'retry_after': 30
            }
        else:
            return {
                'type': 'HTTP_ERROR',
                'message': f'HTTP 오류: {status_code}',
                'action': '오류 로그 확인',
                'retry': False
            }
    
    def _handle_connection_error(self, error: requests.exceptions.ConnectionError, context: str) -> dict:
        """연결 오류 처리"""
        return {
            'type': 'CONNECTION_ERROR',
            'message': '네트워크 연결에 실패했습니다.',
            'action': '네트워크 연결 확인',
            'retry': True,
            'retry_after': 10
        }
    
    def _handle_timeout_error(self, error: requests.exceptions.Timeout, context: str) -> dict:
        """타임아웃 오류 처리"""
        return {
            'type': 'TIMEOUT',
            'message': '요청 시간이 초과되었습니다.',
            'action': '타임아웃 설정 조정',
            'retry': True,
            'retry_after': 5
        }
    
    def _handle_value_error(self, error: ValueError, context: str) -> dict:
        """값 오류 처리"""
        return {
            'type': 'VALUE_ERROR',
            'message': f'값 오류: {error}',
            'action': '입력 값 검증',
            'retry': False
        }
    
    def _handle_generic_error(self, error: Exception, context: str) -> dict:
        """일반 오류 처리"""
        return {
            'type': 'GENERIC_ERROR',
            'message': f'알 수 없는 오류: {error}',
            'action': '오류 로그 확인',
            'retry': False
        }
    
    def should_retry(self, error: Exception, context: str) -> bool:
        """재시도 여부 판단"""
        error_info = self.handle_error(error, context)
        return error_info.get('retry', False)
    
    def get_retry_delay(self, error: Exception, context: str) -> int:
        """재시도 지연 시간 계산"""
        error_info = self.handle_error(error, context)
        return error_info.get('retry_after', 0)

class ErrorMonitor:
    """오류 모니터링 클래스"""
    
    def __init__(self):
        self.error_log = []
        self.alert_thresholds = {
            'RATE_LIMIT': 5,      # 5회 이상
            'SERVER_ERROR': 3,    # 3회 이상
            'CONNECTION_ERROR': 10  # 10회 이상
        }
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error: Exception, context: str):
        """오류 로그 기록"""
        error_entry = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        self.error_log.append(error_entry)
        
        # 최근 1시간 오류 수 확인
        recent_errors = self._get_recent_errors(hours=1)
        error_counts = self._count_errors_by_type(recent_errors)
        
        # 알림 임계값 확인
        self._check_alert_thresholds(error_counts)
    
    def _get_recent_errors(self, hours: int = 1) -> list:
        """최근 오류 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [e for e in self.error_log if e['timestamp'] > cutoff_time]
    
    def _count_errors_by_type(self, errors: list) -> dict:
        """오류 타입별 카운트"""
        counts = {}
        for error in errors:
            error_type = error['error_type']
            counts[error_type] = counts.get(error_type, 0) + 1
        return counts
    
    def _check_alert_thresholds(self, error_counts: dict):
        """알림 임계값 확인"""
        for error_type, count in error_counts.items():
            threshold = self.alert_thresholds.get(error_type, float('inf'))
            if count >= threshold:
                self._send_alert(error_type, count)
    
    def _send_alert(self, error_type: str, count: int):
        """알림 전송"""
        message = f"🚨 오류 알림: {error_type} 오류가 {count}회 발생했습니다."
        self.logger.warning(message)
        print(message)
        # 여기에 슬랙, 이메일 등 알림 로직 구현

class AdvancedRateLimiter:
    """고급 Rate Limiter"""
    
    def __init__(self, 
                 requests_per_second: int = 10,
                 requests_per_minute: int = 600,
                 requests_per_day: int = 10000):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        
        # 요청 기록 저장
        self.second_requests = []
        self.minute_requests = []
        self.day_requests = []
        
        # 스레드 안전을 위한 락
        self.lock = threading.Lock()
        
        # 백오프 설정
        self.backoff_factor = 1.5
        self.max_backoff = 60
    
    def wait_if_needed(self):
        """요청 제한에 걸리지 않도록 대기"""
        with self.lock:
            current_time = time.time()
            
            # 1초 이내 요청 정리
            self.second_requests = [t for t in self.second_requests if current_time - t < 1]
            
            # 1분 이내 요청 정리
            self.minute_requests = [t for t in self.minute_requests if current_time - t < 60]
            
            # 1일 이내 요청 정리
            self.day_requests = [t for t in self.day_requests if current_time - t < 86400]
            
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
            
            # 1일 제한 체크
            if len(self.day_requests) >= self.requests_per_day:
                sleep_time = 86400 - (current_time - self.day_requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            # 요청 기록 추가
            self.second_requests.append(current_time)
            self.minute_requests.append(current_time)
            self.day_requests.append(current_time)
    
    def handle_rate_limit_error(self, error_count: int = 0):
        """Rate Limit 오류 처리"""
        backoff_time = min(
            self.backoff_factor ** error_count,
            self.max_backoff
        )
        
        print(f"Rate Limit 오류 발생. {backoff_time}초 대기...")
        time.sleep(backoff_time)

def validate_market_code(market: str) -> bool:
    """마켓 코드 유효성 검사"""
    if not market:
        raise ValueError("마켓 코드가 비어있습니다.")
    
    # 업비트 마켓 코드 형식 검사
    if not market.startswith(('KRW-', 'BTC-', 'USDT-')):
        raise ValueError(f"잘못된 마켓 코드 형식: {market}")
    
    return True

def validate_order_params(market: str, side: str, volume: str = None, price: str = None):
    """주문 파라미터 유효성 검사"""
    errors = []
    
    # 마켓 코드 검사
    try:
        validate_market_code(market)
    except ValueError as e:
        errors.append(str(e))
    
    # 주문 방향 검사
    if side not in ['bid', 'ask']:
        errors.append(f"잘못된 주문 방향: {side}. 'bid' 또는 'ask'여야 합니다.")
    
    # 수량 검사
    if volume:
        try:
            vol = float(volume)
            if vol <= 0:
                errors.append("수량은 0보다 커야 합니다.")
        except ValueError:
            errors.append("수량은 숫자여야 합니다.")
    
    # 가격 검사
    if price:
        try:
            prc = float(price)
            if prc <= 0:
                errors.append("가격은 0보다 커야 합니다.")
        except ValueError:
            errors.append("가격은 숫자여야 합니다.")
    
    if errors:
        raise ValueError("; ".join(errors))

def create_secure_jwt_token(access_key: str, secret_key: str) -> str:
    """보안이 강화된 JWT 토큰 생성"""
    try:
        # API 키 유효성 검사
        if not access_key or not secret_key:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        if len(access_key) < 20 or len(secret_key) < 20:
            raise ValueError("API 키 길이가 너무 짧습니다.")
        
        # 현재 시간 기반 nonce 생성
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': int(time.time() * 1000)
        }
        
        # JWT 토큰 생성
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        # 토큰 유효성 검사
        try:
            decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
            if decoded['access_key'] != access_key:
                raise ValueError("토큰 검증 실패")
        except jwt.InvalidTokenError:
            raise ValueError("JWT 토큰 생성 실패")
        
        return token
        
    except Exception as e:
        raise ValueError(f"JWT 토큰 생성 오류: {e}")

def create_secure_signature(secret_key: str, query_string: str) -> str:
    """보안이 강화된 서명 생성"""
    try:
        if not secret_key or not query_string:
            raise ValueError("Secret Key 또는 쿼리 문자열이 비어있습니다.")
        
        # HMAC-SHA512 서명 생성
        signature = hmac.new(
            secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # 서명 길이 검사
        if len(signature) != 128:  # SHA512는 128자
            raise ValueError("서명 생성 실패")
        
        return signature
        
    except Exception as e:
        raise ValueError(f"서명 생성 오류: {e}")

def validate_market_status(market: str) -> dict:
    """마켓 상태 확인"""
    try:
        # 마켓 목록 조회
        markets = requests.get('https://api.upbit.com/v1/market/all').json()
        
        # 해당 마켓 찾기
        target_market = next((m for m in markets if m['market'] == market), None)
        
        if not target_market:
            return {
                'valid': False,
                'error': 'MARKET_NOT_FOUND',
                'message': f"마켓을 찾을 수 없습니다: {market}"
            }
        
        # 마켓 상태 확인
        if target_market.get('market_warning') == 'CAUTION':
            return {
                'valid': True,
                'warning': 'CAUTION',
                'message': '투자 주의 종목입니다.'
            }
        
        return {
            'valid': True,
            'market': target_market,
            'message': '정상적인 마켓입니다.'
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': 'VALIDATION_ERROR',
            'message': f"마켓 상태 확인 오류: {e}"
        }

def handle_server_error(max_retries: int = 3, base_delay: float = 1.0):
    """서버 오류 처리 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code >= 500:
                        last_exception = e
                        delay = base_delay * (2 ** attempt)  # 지수 백오프
                        print(f"서버 오류 발생. {delay}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise e
                except Exception as e:
                    raise e
            
            # 모든 재시도 실패
            raise last_exception
        
        return wrapper
    return decorator

# 사용 예시
def main():
    """오류 처리 예시"""
    try:
        # 오류 처리 클래스 생성
        error_handler = UpbitErrorHandler()
        error_monitor = ErrorMonitor()
        rate_limiter = AdvancedRateLimiter()
        
        print("🚀 업비트 API 오류 처리 테스트")
        print("=" * 50)
        
        # 1. 마켓 코드 검증 테스트
        print("\n📊 마켓 코드 검증 테스트...")
        test_markets = ['KRW-BTC', 'INVALID-MARKET', 'BTC-ETH', '']
        
        for market in test_markets:
            try:
                validate_market_code(market)
                print(f"✅ {market}: 유효한 마켓 코드")
            except ValueError as e:
                error_info = error_handler.handle_error(e, "validate_market_code")
                error_monitor.log_error(e, "validate_market_code")
                print(f"❌ {market}: {error_info['message']}")
                print(f"🔧 권장 조치: {error_info['action']}")
        
        # 2. 주문 파라미터 검증 테스트
        print("\n📝 주문 파라미터 검증 테스트...")
        test_orders = [
            ('KRW-BTC', 'bid', '0.001', '50000000'),
            ('KRW-BTC', 'invalid', '0.001', '50000000'),
            ('KRW-BTC', 'bid', '-0.001', '50000000'),
            ('KRW-BTC', 'bid', '0.001', '0'),
        ]
        
        for market, side, volume, price in test_orders:
            try:
                validate_order_params(market, side, volume, price)
                print(f"✅ 주문 파라미터 유효: {market}, {side}, {volume}, {price}")
            except ValueError as e:
                error_info = error_handler.handle_error(e, "validate_order_params")
                error_monitor.log_error(e, "validate_order_params")
                print(f"❌ 주문 파라미터 오류: {error_info['message']}")
                print(f"🔧 권장 조치: {error_info['action']}")
        
        # 3. Rate Limiter 테스트
        print("\n⏰ Rate Limiter 테스트...")
        for i in range(5):
            rate_limiter.wait_if_needed()
            print(f"요청 {i+1}: 허용됨")
        
        # 4. 마켓 상태 확인 테스트
        print("\n🔍 마켓 상태 확인 테스트...")
        test_markets = ['KRW-BTC', 'KRW-ETH', 'INVALID-MARKET']
        
        for market in test_markets:
            status = validate_market_status(market)
            if status['valid']:
                print(f"✅ {market}: {status['message']}")
                if 'warning' in status:
                    print(f"⚠️  주의: {status['warning']}")
            else:
                print(f"❌ {market}: {status['message']}")
        
        # 5. 오류 통계
        print("\n📈 오류 통계...")
        print(f"총 오류 수: {len(error_monitor.error_log)}")
        
        recent_errors = error_monitor._get_recent_errors(hours=1)
        error_counts = error_monitor._count_errors_by_type(recent_errors)
        
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count}회")
        
        print("\n✅ 오류 처리 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")

if __name__ == "__main__":
    main()
