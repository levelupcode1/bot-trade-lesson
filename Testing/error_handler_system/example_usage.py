#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오류 처리 시스템 사용 예시
"""

import os
import time
from error_handler import ErrorHandler, ErrorType, ErrorSeverity


def example_auth_error():
    """인증 오류 처리 예시"""
    print("=" * 60)
    print("인증 오류 처리 예시")
    print("=" * 60)
    
    error_handler = ErrorHandler(
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID')
    )
    
    # 인증 오류 시뮬레이션
    try:
        # API 호출 시뮬레이션
        raise Exception("401 Unauthorized")
    except Exception as e:
        context = {
            'api_key': os.getenv('UPBIT_ACCESS_KEY', 'test_key'),
            'secret_key': os.getenv('UPBIT_SECRET_KEY', 'test_secret')
        }
        recovered = error_handler.handle_auth_error(e, context)
        print(f"복구 성공: {recovered}")


def example_network_error():
    """네트워크 오류 처리 예시"""
    print("\n" + "=" * 60)
    print("네트워크 오류 처리 예시")
    print("=" * 60)
    
    error_handler = ErrorHandler()
    
    # 재시도 함수 정의
    attempt_count = 0
    
    def api_call():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Connection timeout")
        return {"status": "success", "data": "test"}
    
    # 네트워크 오류 시뮬레이션
    try:
        result = api_call()
    except Exception as e:
        context = {
            'retry_func': api_call,
            'args': [],
            'kwargs': {}
        }
        recovered = error_handler.handle_network_error(e, context, max_retries=3)
        print(f"복구 성공: {recovered}")
        if recovered:
            print(f"결과: {result}")


def example_data_error():
    """데이터 오류 처리 예시"""
    print("\n" + "=" * 60)
    print("데이터 오류 처리 예시")
    print("=" * 60)
    
    error_handler = ErrorHandler()
    
    # 데이터 검증 함수
    def validate_price_data(data):
        if not isinstance(data, dict):
            return False
        if 'price' not in data or 'volume' not in data:
            return False
        if data['price'] <= 0 or data['volume'] < 0:
            return False
        return True
    
    # 잘못된 데이터
    invalid_data = {'price': -100, 'volume': 1000}
    
    # 정상 데이터 (이전 데이터)
    valid_data = {'price': 100.0, 'volume': 1000.0}
    error_handler.last_valid_data['price_data'] = valid_data
    
    # 데이터 오류 시뮬레이션
    try:
        if not validate_price_data(invalid_data):
            raise ValueError("데이터 검증 실패")
    except Exception as e:
        context = {
            'data': invalid_data,
            'validation_func': validate_price_data
        }
        recovered_data = error_handler.handle_data_error(e, context, data_key='price_data')
        print(f"복구된 데이터: {recovered_data}")


def example_error_summary():
    """오류 요약 예시"""
    print("\n" + "=" * 60)
    print("오류 요약 예시")
    print("=" * 60)
    
    error_handler = ErrorHandler()
    
    # 여러 오류 시뮬레이션
    for i in range(5):
        from error_handler import ErrorRecord
        error_record = ErrorRecord(
            error_type=ErrorType.NETWORK_ERROR,
            error_message=f"테스트 오류 {i+1}",
            timestamp=time.time(),
            retry_count=i % 3,
            severity=ErrorSeverity.MEDIUM,
            recovered=(i % 2 == 0)
        )
        error_handler._log_error(error_record)
    
    # 요약 조회
    summary = error_handler.get_error_summary()
    print(f"총 오류: {summary['total_errors']}")
    print(f"복구 성공: {summary['recovered_errors']}")
    print(f"복구율: {summary['recovery_rate']:.2f}%")
    print(f"오류 유형별 통계: {summary['error_type_counts']}")
    print(f"재시도 통계: {summary['retry_stats']}")


if __name__ == "__main__":
    # 로그 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    
    # 예시 실행
    example_auth_error()
    example_network_error()
    example_data_error()
    example_error_summary()
    
    print("\n" + "=" * 60)
    print("예시 실행 완료")
    print("=" * 60)
