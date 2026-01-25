#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24시간 연속 운영 오류 처리 서비스
Docker 컨테이너에서 실행되는 메인 서비스
"""

import os
import time
import signal
import sys
import logging
from error_handler import ErrorHandler, ErrorType, ErrorSeverity

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 전역 변수
error_handler = None
running = True


def signal_handler(signum, frame):
    """시그널 핸들러 (Graceful shutdown)"""
    global running
    logger.info(f"시그널 {signum} 수신. 서비스 종료 중...")
    running = False


def main():
    """메인 서비스 함수"""
    global error_handler, running
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 오류 처리자 초기화
        error_handler = ErrorHandler(
            log_file=os.getenv('LOG_FILE', 'logs/error_handler.log'),
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            email_config={
                'smtp_server': os.getenv('SMTP_SERVER'),
                'smtp_port': os.getenv('SMTP_PORT', '587'),
                'username': os.getenv('EMAIL_USERNAME'),
                'password': os.getenv('EMAIL_PASSWORD'),
                'to_email': os.getenv('EMAIL_TO')
            }
        )
        
        logger.info("오류 처리 서비스 시작")
        
        # 서비스 루프 (24시간 연속 운영)
        while running:
            try:
                # 실제 구현에서는 여기서 오류 모니터링 및 처리 로직 실행
                # 예: API 호출, 데이터 검증 등
                
                # 주기적으로 오류 요약 출력
                if int(time.time()) % 3600 == 0:  # 1시간마다
                    summary = error_handler.get_error_summary()
                    logger.info(f"오류 요약: {summary}")
                
                time.sleep(1)  # CPU 사용률 감소
                
            except KeyboardInterrupt:
                logger.info("키보드 인터럽트 수신")
                running = False
            except Exception as e:
                logger.error(f"서비스 루프 오류: {e}", exc_info=True)
                time.sleep(5)  # 오류 발생 시 잠시 대기
        
        logger.info("오류 처리 서비스 종료")
        
    except Exception as e:
        logger.critical(f"서비스 초기화 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
