#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오류 처리 시스템 테스트
"""

import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from error_handler import ErrorHandler, ErrorType, ErrorSeverity


class TestErrorHandler(unittest.TestCase):
    """오류 처리자 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.error_handler = ErrorHandler(
            log_file="logs/test_error_handler.log",
            telegram_bot_token=None,
            telegram_chat_id=None
        )
    
    def test_handle_auth_error(self):
        """인증 오류 처리 테스트"""
        error = Exception("인증 실패")
        context = {
            'api_key': 'test_key',
            'secret_key': 'test_secret'
        }
        
        # API 키가 없을 때
        with patch.dict(os.environ, {}, clear=True):
            result = self.error_handler.handle_auth_error(error, context)
            self.assertFalse(result)
    
    def test_handle_network_error(self):
        """네트워크 오류 처리 테스트"""
        error = Exception("네트워크 연결 실패")
        
        # 성공하는 재시도 함수
        success_func = Mock(return_value="success")
        context = {
            'retry_func': success_func,
            'args': [],
            'kwargs': {}
        }
        
        result = self.error_handler.handle_network_error(error, context, max_retries=3)
        self.assertTrue(result)
        self.assertTrue(success_func.called)
    
    def test_handle_data_error(self):
        """데이터 오류 처리 테스트"""
        error = Exception("데이터 검증 실패")
        
        # 검증 함수
        def validate_func(data):
            return isinstance(data, dict) and 'price' in data
        
        # 정상 데이터
        valid_data = {'price': 100.0, 'volume': 1000.0}
        context = {
            'data': valid_data,
            'validation_func': validate_func
        }
        
        result = self.error_handler.handle_data_error(error, context, data_key='test')
        self.assertIsNotNone(result)
        self.assertEqual(result, valid_data)
    
    def test_error_logging(self):
        """오류 로깅 테스트"""
        from error_handler import ErrorRecord
        
        error_record = ErrorRecord(
            error_type=ErrorType.NETWORK_ERROR,
            error_message="테스트 오류",
            timestamp=time.time(),
            retry_count=1,
            severity=ErrorSeverity.MEDIUM
        )
        
        initial_count = len(self.error_handler.error_history)
        self.error_handler._log_error(error_record)
        
        self.assertEqual(len(self.error_handler.error_history), initial_count + 1)
    
    def test_get_error_summary(self):
        """오류 요약 테스트"""
        summary = self.error_handler.get_error_summary()
        
        self.assertIn('total_errors', summary)
        self.assertIn('recovered_errors', summary)
        self.assertIn('recovery_rate', summary)
        self.assertIn('error_type_counts', summary)
        self.assertIn('retry_stats', summary)


if __name__ == "__main__":
    # 테스트 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    
    # 테스트 실행
    unittest.main()
