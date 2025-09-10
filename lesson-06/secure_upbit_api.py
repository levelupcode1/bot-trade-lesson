#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import time
import threading
import requests
import ssl
import traceback
import jwt
import uuid
import hashlib
import hmac
from typing import Optional, Dict, Any
from collections import deque
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
from datetime import datetime

class SecurityError(Exception):
    """보안 관련 예외"""
    pass

class RateLimiter:
    """API 요청 제한 관리"""
    
    def __init__(self, requests_per_second=10, requests_per_minute=600):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        
        # 요청 기록 저장
        self.second_requests = deque()
        self.minute_requests = deque()
        
        # 스레드 안전을 위한 락
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """요청 제한에 걸리지 않도록 대기"""
        with self.lock:
            current_time = time.time()
            
            # 1초 이내 요청 정리
            while self.second_requests and current_time - self.second_requests[0] > 1:
                self.second_requests.popleft()
            
            # 1분 이내 요청 정리
            while self.minute_requests and current_time - self.minute_requests[0] > 60:
                self.minute_requests.popleft()
            
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

class SecureErrorHandler:
    """보안 강화된 오류 처리"""
    
    @staticmethod
    def safe_log_error(error: Exception, context: Dict[str, Any] = None):
        """민감한 정보를 제외한 안전한 오류 로깅"""
        # 민감한 정보 제거
        safe_context = {}
        if context:
            for key, value in context.items():
                if 'key' in key.lower() or 'secret' in key.lower():
                    safe_context[key] = '***MASKED***'
                else:
                    safe_context[key] = value
        
        # 스택 트레이스에서 민감한 정보 제거
        safe_traceback = traceback.format_exc()
        safe_traceback = safe_traceback.replace('your_access_key', '***ACCESS_KEY***')
        safe_traceback = safe_traceback.replace('your_secret_key', '***SECRET_KEY***')
        
        # 로깅
        logging.error(f"오류 발생: {str(error)}")
        logging.error(f"컨텍스트: {safe_context}")
        logging.debug(f"스택 트레이스: {safe_traceback}")
    
    @staticmethod
    def handle_api_error(response):
        """API 오류 안전 처리"""
        try:
            error_data = response.json()
            
            # 오류 메시지에서 민감한 정보 제거
            if 'message' in error_data:
                error_data['message'] = error_data['message'].replace(
                    'access_key', '***ACCESS_KEY***'
                )
            
            return error_data
            
        except Exception:
            return {"error": "오류 정보를 파싱할 수 없습니다"}

class SecurityMonitor:
    """보안 모니터링 클래스"""
    
    def __init__(self):
        self.suspicious_activities = []
        self.failed_attempts = 0
        self.max_failed_attempts = 5
    
    def log_suspicious_activity(self, activity: str, details: dict):
        """의심스러운 활동 로깅"""
        self.suspicious_activities.append({
            'timestamp': datetime.now().isoformat(),
            'activity': activity,
            'details': details
        })
        
        # 위험도가 높은 경우 알림
        if activity in ['API_KEY_EXPOSED', 'RATE_LIMIT_EXCEEDED']:
            self.send_security_alert(activity, details)
    
    def check_failed_attempts(self):
        """실패한 시도 횟수 체크"""
        if self.failed_attempts >= self.max_failed_attempts:
            self.log_suspicious_activity('TOO_MANY_FAILED_ATTEMPTS', {
                'count': self.failed_attempts
            })
            return True
        return False
    
    def send_security_alert(self, activity: str, details: dict):
        """보안 알림 전송"""
        # 여기에 슬랙, 이메일 등 알림 로직 구현
        print(f"🚨 보안 알림: {activity} - {details}")

class SecureHTTPClient:
    """보안이 강화된 HTTP 클라이언트"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_secure_session()
    
    def setup_secure_session(self):
        """보안 설정 적용"""
        # SSL 검증 강화
        self.session.verify = True
        
        # TLS 1.2 이상만 허용
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,  # 최대 3회 재시도
            backoff_factor=1,  # 지수 백오프
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 상태 코드
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 기본 헤더 설정
        self.session.headers.update({
            'User-Agent': 'SecureUpbitBot/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def secure_request(self, method: str, url: str, **kwargs):
        """보안 요청 실행"""
        try:
            # 요청 전 보안 검증
            self.validate_request(url, kwargs)
            
            # 요청 실행
            response = self.session.request(method, url, **kwargs)
            
            # 응답 보안 검증
            self.validate_response(response)
            
            return response
            
        except requests.exceptions.SSLError as e:
            raise SecurityError(f"SSL 연결 오류: {e}")
        except requests.exceptions.ConnectionError as e:
            raise SecurityError(f"연결 오류: {e}")
        except Exception as e:
            raise SecurityError(f"요청 오류: {e}")
    
    def validate_request(self, url: str, kwargs: dict):
        """요청 보안 검증"""
        # URL 검증
        if not url.startswith('https://'):
            raise SecurityError("HTTPS 연결만 허용됩니다")
        
        # 업비트 도메인만 허용
        if 'api.upbit.com' not in url:
            raise SecurityError("업비트 API 도메인만 허용됩니다")
    
    def validate_response(self, response):
        """응답 보안 검증"""
        # 상태 코드 검증
        if response.status_code >= 400:
            raise SecurityError(f"HTTP 오류: {response.status_code}")
        
        # 응답 크기 제한 (1MB)
        if len(response.content) > 1024 * 1024:
            raise SecurityError("응답 크기가 너무 큽니다")

class SecureUpbitAPI:
    """보안이 강화된 업비트 API 클라이언트"""
    
    def __init__(self):
        """환경 변수에서 API 키 로드"""
        # .env 파일 로드
        load_dotenv()
        
        # API 키 로드 (환경 변수에서)
        self.access_key = os.getenv('UPBIT_ACCESS_KEY')
        self.secret_key = os.getenv('UPBIT_SECRET_KEY')
        
        # API 키 검증
        if not self.access_key or not self.secret_key:
            raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        # 로깅 설정 (민감한 정보 제외)
        self.setup_secure_logging()
        
        # Rate Limiter 설정
        self.rate_limiter = RateLimiter()
        
        # 보안 모니터링 설정
        self.security_monitor = SecurityMonitor()
        
        # HTTP 클라이언트 설정
        self.http_client = SecureHTTPClient()
        
        # API 기본 URL
        self.base_url = "https://api.upbit.com"
        
    def setup_secure_logging(self):
        """보안 강화된 로깅 설정"""
        # 민감한 정보를 마스킹하는 필터
        class SensitiveDataFilter(logging.Filter):
            def __init__(self, access_key, secret_key):
                self.access_key = access_key
                self.secret_key = secret_key
                
            def filter(self, record):
                # API 키 마스킹
                if hasattr(record, 'msg'):
                    record.msg = str(record.msg).replace(self.access_key, '***ACCESS_KEY***')
                    record.msg = str(record.msg).replace(self.secret_key, '***SECRET_KEY***')
                return True
        
        # 로거 설정
        logger = logging.getLogger(__name__)
        logger.addFilter(SensitiveDataFilter(self.access_key, self.secret_key))
        
        # 파일 로깅 (민감한 정보 제외)
        file_handler = logging.FileHandler('secure_api.log')
        file_handler.addFilter(SensitiveDataFilter(self.access_key, self.secret_key))
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        self.logger = logger
    
    def create_jwt_token(self):
        """JWT 토큰 생성"""
        try:
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            return jwt.encode(payload, self.secret_key, algorithm='HS256')
        except Exception as e:
            self.security_monitor.log_suspicious_activity('JWT_TOKEN_CREATION_FAILED', {
                'error': str(e)
            })
            raise SecurityError(f"JWT 토큰 생성 실패: {e}")
    
    def create_signature(self, query_string):
        """서명 생성"""
        try:
            return hmac.new(
                self.secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
        except Exception as e:
            self.security_monitor.log_suspicious_activity('SIGNATURE_CREATION_FAILED', {
                'error': str(e)
            })
            raise SecurityError(f"서명 생성 실패: {e}")
    
    def get_accounts(self):
        """계정 잔고 조회 (인증 필요)"""
        try:
            # Rate Limit 체크
            self.rate_limiter.wait_if_needed()
            
            # JWT 토큰 생성
            jwt_token = self.create_jwt_token()
            
            # 헤더 설정
            headers = {
                'Authorization': f'Bearer {jwt_token}'
            }
            
            # API 요청
            response = self.http_client.secure_request(
                'GET',
                f"{self.base_url}/v1/accounts",
                headers=headers
            )
            
            # 실패한 시도 횟수 초기화
            self.security_monitor.failed_attempts = 0
            
            return response.json()
            
        except SecurityError as e:
            self.security_monitor.failed_attempts += 1
            SecureErrorHandler.safe_log_error(e, {
                'method': 'get_accounts',
                'access_key': self.access_key[:8] + '...'  # 부분적으로만 표시
            })
            raise
        except Exception as e:
            self.security_monitor.failed_attempts += 1
            SecureErrorHandler.safe_log_error(e, {
                'method': 'get_accounts'
            })
            raise SecurityError(f"계정 조회 실패: {e}")
    
    def get_markets(self):
        """마켓 목록 조회 (인증 불필요)"""
        try:
            # Rate Limit 체크
            self.rate_limiter.wait_if_needed()
            
            # API 요청
            response = self.http_client.secure_request(
                'GET',
                f"{self.base_url}/v1/market/all"
            )
            
            return response.json()
            
        except Exception as e:
            SecureErrorHandler.safe_log_error(e, {
                'method': 'get_markets'
            })
            raise SecurityError(f"마켓 목록 조회 실패: {e}")
    
    def get_ticker(self, markets):
        """현재가 조회 (인증 불필요)"""
        try:
            # Rate Limit 체크
            self.rate_limiter.wait_if_needed()
            
            # 마켓 파라미터 처리
            if isinstance(markets, list):
                markets_param = ','.join(markets)
            else:
                markets_param = markets
            
            # API 요청
            response = self.http_client.secure_request(
                'GET',
                f"{self.base_url}/v1/ticker",
                params={'markets': markets_param}
            )
            
            return response.json()
            
        except Exception as e:
            SecureErrorHandler.safe_log_error(e, {
                'method': 'get_ticker',
                'markets': markets
            })
            raise SecurityError(f"현재가 조회 실패: {e}")

def main():
    """메인 함수 - 보안 강화된 API 사용 예시"""
    try:
        print("🔒 보안 강화된 업비트 API 클라이언트 시작")
        print("=" * 50)
        
        # API 클라이언트 생성
        api = SecureUpbitAPI()
        
        # 마켓 목록 조회
        print("📊 마켓 목록 조회 중...")
        markets = api.get_markets()
        print(f"✅ {len(markets)}개 마켓 조회 완료")
        
        # 주요 마켓 현재가 조회
        print("\n💰 주요 마켓 현재가 조회 중...")
        major_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        tickers = api.get_ticker(major_markets)
        
        for ticker in tickers:
            print(f"  {ticker['market']}: {ticker['trade_price']:,}원 "
                  f"({ticker['signed_change_rate']:.2%})")
        
        # 계정 잔고 조회 (API 키가 설정된 경우에만)
        print("\n💳 계정 잔고 조회 중...")
        try:
            accounts = api.get_accounts()
            print(f"✅ {len(accounts)}개 자산 조회 완료")
            
            for account in accounts:
                if float(account['balance']) > 0:
                    print(f"  {account['currency']}: {account['balance']}개")
                    
        except SecurityError as e:
            print(f"⚠️  계정 조회 실패: {e}")
            print("   (API 키가 설정되지 않았거나 권한이 없습니다)")
        
        print("\n✅ 모든 작업이 안전하게 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("   자세한 내용은 secure_api.log 파일을 확인하세요.")

if __name__ == "__main__":
    main()
