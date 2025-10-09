#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이메일 발송 모듈
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class EmailSender:
    """이메일 발송 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_address = config.get('from_address')
        
        self.enabled = bool(
            self.smtp_server and self.username and 
            self.password and self.from_address
        )
        
        if not self.enabled:
            logger.warning("이메일 설정이 없습니다. 이메일 발송을 건너뜁니다.")
    
    def send_report(self, report_type: str, recipients: List[str],
                   files: Dict[str, str], data: Dict[str, Any]):
        """리포트 이메일 발송"""
        if not self.enabled:
            logger.info("이메일 발송 비활성화됨")
            return
        
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            
            # 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[자동매매] {report_type.upper()} 리포트"
            
            # 본문
            analysis = data.get('analysis', {})
            body = f"""
자동매매 {report_type.upper()} 리포트입니다.

📊 핵심 지표
- 총 수익률: {analysis.get('total_return', 0):.2f}%
- 거래 수: {analysis.get('total_trades', 0)}건
- 승률: {analysis.get('win_rate', 0):.1f}%
- 최대 낙폭: {analysis.get('max_drawdown', 0):.2f}%

자세한 내용은 첨부 파일을 확인하세요.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # 파일 첨부
            for format_type, file_path in files.items():
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(file_path).name}'
                        )
                        msg.attach(part)
            
            # 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"이메일 발송 성공: {recipients}")
            
        except ImportError:
            logger.warning("이메일 발송에 필요한 라이브러리가 없습니다.")
        except Exception as e:
            logger.error(f"이메일 발송 오류: {e}", exc_info=True)

