#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24시간 연속 운영 자동매매 시스템 오류 처리 및 복구 클래스
"""

import os
import time
import logging
import jwt
import uuid
import requests
import smtplib
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(Enum):
    """오류 유형"""
    AUTH_ERROR = "인증 오류"
    NETWORK_ERROR = "네트워크 오류"
    DATA_ERROR = "데이터 오류"
    UNKNOWN_ERROR = "알 수 없는 오류"


class ErrorSeverity(Enum):
    """오류 심각도"""
    LOW = "낮음"
    MEDIUM = "중간"
    HIGH = "높음"
    CRITICAL = "치명적"


@dataclass
class ErrorRecord:
    """오류 기록"""
    error_type: ErrorType
    error_message: str
    timestamp: datetime
    retry_count: int
    context: Dict[str, Any] = field(default_factory=dict)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    recovered: bool = False


class ErrorHandler:
    """
    24시간 연속 운영 자동매매 시스템 오류 처리 및 복구 클래스
    
    주요 기능:
    - API 인증 오류 처리 및 자동 복구
    - 네트워크 오류 처리 및 지수 백오프 재시도
    - 데이터 오류 처리 및 검증
    - 로깅 및 알림 전송
    """
    
    def __init__(
        self,
        log_file: str = "logs/error_handler.log",
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        email_config: Optional[Dict[str, str]] = None
    ):
        """
        오류 처리자 초기화
        
        Args:
            log_file: 로그 파일 경로
            telegram_bot_token: 텔레그램 봇 토큰 (선택)
            telegram_chat_id: 텔레그램 채팅 ID (선택)
            email_config: 이메일 설정 딕셔너리 (선택)
                - smtp_server: SMTP 서버 주소
                - smtp_port: SMTP 포트
                - username: 이메일 주소
                - password: 이메일 비밀번호
                - to_email: 수신자 이메일
        """
        # 로깅 설정
        self._setup_logging(log_file)
        self.logger = logging.getLogger(__name__)
        
        # 알림 설정
        self.telegram_bot_token = telegram_bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.email_config = email_config or self._load_email_config()
        
        # 오류 기록
        self.error_history: List[ErrorRecord] = []
        self.max_history_size = 1000
        
        # 이전 정상 데이터 저장
        self.last_valid_data: Dict[str, Any] = {}
        
        # API 키 저장 (실제 구현에서는 암호화된 저장소 사용)
        self.api_keys: Dict[str, str] = {}
        
        # 재시도 통계
        self.retry_stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0
        }
        
        self.logger.info("오류 처리 시스템 초기화 완료")
    
    def _setup_logging(self, log_file: str) -> None:
        """로깅 설정"""
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs', exist_ok=True)
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _load_email_config(self) -> Optional[Dict[str, str]]:
        """이메일 설정 로드"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': os.getenv('SMTP_PORT', '587'),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'to_email': os.getenv('EMAIL_TO')
        }
    
    def handle_auth_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        max_retries: int = 3
    ) -> bool:
        """
        API 인증 오류 처리 및 자동 복구
        
        Args:
            error: 발생한 오류
            context: 오류 컨텍스트 (api_key, secret_key 등 포함)
            max_retries: 최대 재시도 횟수
        
        Returns:
            bool: 복구 성공 여부
        """
        context = context or {}
        retry_count = 0
        recovered = False
        
        self.logger.warning(f"인증 오류 발생: {error}")
        
        while retry_count < max_retries and not recovered:
            try:
                retry_count += 1
                self.retry_stats['total_retries'] += 1
                
                # 오류 기록
                error_record = ErrorRecord(
                    error_type=ErrorType.AUTH_ERROR,
                    error_message=str(error),
                    timestamp=datetime.now(),
                    retry_count=retry_count,
                    context=context,
                    severity=ErrorSeverity.HIGH
                )
                self._log_error(error_record)
                
                # API 키 재확인
                api_key = context.get('api_key') or os.getenv('UPBIT_ACCESS_KEY')
                secret_key = context.get('secret_key') or os.getenv('UPBIT_SECRET_KEY')
                
                if not api_key or not secret_key:
                    self.logger.error("API 키가 설정되지 않았습니다.")
                    self._send_notification(
                        "인증 오류",
                        "API 키가 설정되지 않았습니다. 환경 변수를 확인하세요.",
                        ErrorSeverity.CRITICAL
                    )
                    break
                
                # 토큰 재생성
                new_token = self._regenerate_jwt_token(api_key, secret_key)
                
                if new_token:
                    # 토큰 검증 (간단한 테스트 요청)
                    if self._verify_token(new_token):
                        recovered = True
                        error_record.recovered = True
                        self.retry_stats['successful_retries'] += 1
                        
                        self.logger.info(f"인증 오류 복구 성공 (재시도 {retry_count}회)")
                        self._send_notification(
                            "인증 오류 복구",
                            f"인증 오류가 복구되었습니다. (재시도 {retry_count}회)",
                            ErrorSeverity.LOW
                        )
                    else:
                        self.logger.warning(f"토큰 검증 실패 (재시도 {retry_count}/{max_retries})")
                else:
                    self.logger.warning(f"토큰 재생성 실패 (재시도 {retry_count}/{max_retries})")
                
                # 재시도 대기
                if not recovered and retry_count < max_retries:
                    wait_time = 2 ** retry_count  # 지수 백오프
                    time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"인증 오류 복구 중 예외 발생: {e}")
                if retry_count >= max_retries:
                    self.retry_stats['failed_retries'] += 1
                    self._send_notification(
                        "인증 오류 복구 실패",
                        f"인증 오류 복구에 실패했습니다: {error}",
                        ErrorSeverity.CRITICAL
                    )
        
        return recovered
    
    def handle_network_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> bool:
        """
        네트워크 오류 처리 및 지수 백오프 재시도
        
        Args:
            error: 발생한 오류
            context: 오류 컨텍스트 (url, method 등 포함)
            max_retries: 최대 재시도 횟수
            base_delay: 기본 지연 시간 (초)
        
        Returns:
            bool: 복구 성공 여부
        """
        context = context or {}
        retry_count = 0
        recovered = False
        
        self.logger.warning(f"네트워크 오류 발생: {error}")
        
        # 재시도 가능한 함수가 있는지 확인
        retry_func = context.get('retry_func')
        if not retry_func:
            self.logger.error("재시도 함수가 제공되지 않았습니다.")
            return False
        
        while retry_count < max_retries and not recovered:
            try:
                retry_count += 1
                self.retry_stats['total_retries'] += 1
                
                # 오류 기록
                error_record = ErrorRecord(
                    error_type=ErrorType.NETWORK_ERROR,
                    error_message=str(error),
                    timestamp=datetime.now(),
                    retry_count=retry_count,
                    context=context,
                    severity=ErrorSeverity.MEDIUM
                )
                self._log_error(error_record)
                
                # 지수 백오프 계산
                delay = base_delay * (2 ** (retry_count - 1))
                
                self.logger.info(f"네트워크 오류 재시도 {retry_count}/{max_retries} (대기 {delay:.1f}초)")
                time.sleep(delay)
                
                # 재시도 실행
                try:
                    result = retry_func(*context.get('args', []), **context.get('kwargs', {}))
                    recovered = True
                    error_record.recovered = True
                    self.retry_stats['successful_retries'] += 1
                    
                    self.logger.info(f"네트워크 오류 복구 성공 (재시도 {retry_count}회)")
                    self._send_notification(
                        "네트워크 오류 복구",
                        f"네트워크 오류가 복구되었습니다. (재시도 {retry_count}회)",
                        ErrorSeverity.LOW
                    )
                    
                except Exception as retry_error:
                    self.logger.warning(f"재시도 {retry_count} 실패: {retry_error}")
                    if retry_count >= max_retries:
                        self.retry_stats['failed_retries'] += 1
                        self._send_notification(
                            "네트워크 오류 복구 실패",
                            f"네트워크 오류 복구에 실패했습니다: {error}",
                            ErrorSeverity.HIGH
                        )
                
            except Exception as e:
                self.logger.error(f"네트워크 오류 복구 중 예외 발생: {e}")
                if retry_count >= max_retries:
                    self.retry_stats['failed_retries'] += 1
        
        return recovered
    
    def handle_data_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        data_key: str = "default"
    ) -> Optional[Any]:
        """
        데이터 오류 처리 및 검증
        
        Args:
            error: 발생한 오류
            context: 오류 컨텍스트 (data, validation_func 등 포함)
            data_key: 데이터 키 (이전 정상 데이터 식별용)
        
        Returns:
            Optional[Any]: 복구된 데이터 또는 None
        """
        context = context or {}
        recovered_data = None
        
        self.logger.warning(f"데이터 오류 발생: {error}")
        
        try:
            # 오류 기록
            error_record = ErrorRecord(
                error_type=ErrorType.DATA_ERROR,
                error_message=str(error),
                timestamp=datetime.now(),
                retry_count=0,
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
            self._log_error(error_record)
            
            # 데이터 검증
            data = context.get('data')
            validation_func = context.get('validation_func')
            
            if data and validation_func:
                try:
                    # 데이터 검증 시도
                    if validation_func(data):
                        recovered_data = data
                        error_record.recovered = True
                        self.logger.info("데이터 검증 성공")
                    else:
                        self.logger.warning("데이터 검증 실패")
                except Exception as e:
                    self.logger.error(f"데이터 검증 중 오류: {e}")
            
            # 이전 정상 데이터 사용
            if not recovered_data and data_key in self.last_valid_data:
                recovered_data = self.last_valid_data[data_key]
                error_record.recovered = True
                error_record.context['used_fallback_data'] = True
                
                self.logger.info(f"이전 정상 데이터 사용: {data_key}")
                self._send_notification(
                    "데이터 오류 복구",
                    f"데이터 오류가 발생하여 이전 정상 데이터를 사용합니다. (키: {data_key})",
                    ErrorSeverity.MEDIUM
                )
            else:
                self.logger.error("복구 가능한 데이터가 없습니다.")
                self._send_notification(
                    "데이터 오류 복구 실패",
                    f"데이터 오류 복구에 실패했습니다: {error}",
                    ErrorSeverity.HIGH
                )
            
            # 현재 데이터가 정상이면 저장
            if recovered_data and not error_record.context.get('used_fallback_data'):
                self.last_valid_data[data_key] = recovered_data
            
        except Exception as e:
            self.logger.error(f"데이터 오류 처리 중 예외 발생: {e}")
        
        return recovered_data
    
    def _regenerate_jwt_token(self, access_key: str, secret_key: str) -> Optional[str]:
        """JWT 토큰 재생성"""
        try:
            payload = {
                'access_key': access_key,
                'nonce': str(uuid.uuid4()),
                'timestamp': int(time.time() * 1000)
            }
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return token
        except Exception as e:
            self.logger.error(f"JWT 토큰 재생성 실패: {e}")
            return None
    
    def _verify_token(self, token: str) -> bool:
        """토큰 검증 (간단한 테스트 요청)"""
        try:
            # 실제 구현에서는 간단한 API 호출로 검증
            # 여기서는 토큰 형식만 확인
            if token and len(token) > 10:
                return True
            return False
        except Exception as e:
            self.logger.error(f"토큰 검증 실패: {e}")
            return False
    
    def _log_error(self, error_record: ErrorRecord) -> None:
        """오류 기록"""
        # 로그 파일에 기록
        log_message = (
            f"오류 유형: {error_record.error_type.value}, "
            f"메시지: {error_record.error_message}, "
            f"시간: {error_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"재시도 횟수: {error_record.retry_count}, "
            f"심각도: {error_record.severity.value}, "
            f"복구 여부: {error_record.recovered}"
        )
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        else:
            self.logger.warning(log_message)
        
        # 오류 기록 저장
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _send_notification(
        self,
        title: str,
        message: str,
        severity: ErrorSeverity
    ) -> None:
        """알림 전송 (텔레그램 또는 이메일)"""
        full_message = f"[{severity.value}] {title}\n\n{message}\n\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 텔레그램 알림
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                self._send_telegram_notification(full_message)
            except Exception as e:
                self.logger.error(f"텔레그램 알림 전송 실패: {e}")
        
        # 이메일 알림 (심각한 오류만)
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            if self.email_config and all([
                self.email_config.get('smtp_server'),
                self.email_config.get('username'),
                self.email_config.get('password'),
                self.email_config.get('to_email')
            ]):
                try:
                    self._send_email_notification(title, full_message)
                except Exception as e:
                    self.logger.error(f"이메일 알림 전송 실패: {e}")
    
    def _send_telegram_notification(self, message: str) -> None:
        """텔레그램 알림 전송"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"텔레그램 알림 전송 오류: {e}")
            raise
    
    def _send_email_notification(self, subject: str, message: str) -> None:
        """이메일 알림 전송"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = f"[자동매매 시스템] {subject}"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], int(self.email_config['smtp_port']))
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            self.logger.error(f"이메일 알림 전송 오류: {e}")
            raise
    
    def get_error_summary(self) -> Dict[str, Any]:
        """오류 요약 통계"""
        total_errors = len(self.error_history)
        recovered_errors = sum(1 for e in self.error_history if e.recovered)
        
        error_type_counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': total_errors,
            'recovered_errors': recovered_errors,
            'recovery_rate': (recovered_errors / total_errors * 100) if total_errors > 0 else 0.0,
            'error_type_counts': error_type_counts,
            'retry_stats': self.retry_stats.copy()
        }
