#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 발송 모듈
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramSender:
    """텔레그램 발송 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.token = config.get('token')
        self.chat_id = config.get('chat_id')
        self.enabled = bool(self.token and self.chat_id)
        
        if not self.enabled:
            logger.warning("텔레그램 설정이 없습니다. 텔레그램 발송을 건너뜁니다.")
    
    def send_report_notification(self, report_type: str, summary: str, 
                                file_path: str = None):
        """리포트 알림 발송"""
        if not self.enabled:
            logger.info("텔레그램 발송 비활성화됨")
            return
        
        try:
            import requests
            
            # 메시지 발송
            message = f"📊 *{report_type.upper()} 리포트*\n\n{summary}"
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"텔레그램 메시지 발송 성공: {report_type}")
            else:
                logger.error(f"텔레그램 발송 실패: {response.text}")
            
            # 파일 첨부 (선택사항)
            if file_path and Path(file_path).exists():
                self._send_document(file_path)
                
        except ImportError:
            logger.warning("requests 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            logger.error(f"텔레그램 발송 오류: {e}", exc_info=True)
    
    def _send_document(self, file_path: str):
        """파일 발송"""
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendDocument"
            
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.chat_id}
                
                response = requests.post(url, data=data, files=files, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"텔레그램 파일 발송 성공: {file_path}")
                else:
                    logger.error(f"텔레그램 파일 발송 실패: {response.text}")
                    
        except Exception as e:
            logger.error(f"텔레그램 파일 발송 오류: {e}")
    
    def send_message(self, message: str):
        """단순 메시지 발송"""
        if not self.enabled:
            return
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("텔레그램 메시지 발송 성공")
            else:
                logger.error(f"텔레그램 발송 실패: {response.text}")
                
        except Exception as e:
            logger.error(f"텔레그램 발송 오류: {e}")

