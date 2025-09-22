#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인코딩 유틸리티 모듈
Windows 환경에서 한글 출력을 위한 인코딩 설정
"""

import sys
import os
import codecs
from typing import Optional

def setup_windows_encoding() -> None:
    """Windows 환경에서 UTF-8 인코딩 설정"""
    if sys.platform.startswith('win'):
        try:
            # 환경 변수 설정
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # 표준 출력/에러 스트림을 UTF-8로 설정
            if hasattr(sys.stdout, 'detach'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            if hasattr(sys.stderr, 'detach'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            
            # 콘솔 코드페이지 설정은 배치 파일에서 처리
            # 여기서는 Python 스트림만 설정
                
        except Exception as e:
            print(f"인코딩 설정 중 오류 발생: {e}")

def safe_print(text: str, file: Optional = None) -> None:
    """안전한 한글 출력 함수"""
    try:
        if file is None:
            file = sys.stdout
        
        # Windows 환경에서 인코딩 설정
        if sys.platform.startswith('win'):
            if hasattr(file, 'write'):
                file.write(text + '\n')
                file.flush()
        else:
            print(text, file=file)
            
    except UnicodeEncodeError:
        # 인코딩 오류 시 ASCII로 대체
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text, file=file)
    except Exception as e:
        print(f"출력 오류: {e}", file=file)

def get_console_encoding() -> str:
    """현재 콘솔 인코딩 반환"""
    if sys.platform.startswith('win'):
        try:
            import locale
            return locale.getpreferredencoding()
        except Exception:
            return 'cp949'  # Windows 기본 인코딩
    else:
        return 'utf-8'

def ensure_utf8_string(text: str) -> str:
    """문자열이 UTF-8로 인코딩되도록 보장"""
    if isinstance(text, bytes):
        try:
            return text.decode('utf-8')
        except UnicodeDecodeError:
            return text.decode('utf-8', 'replace')
    return text

def setup_logging_encoding() -> None:
    """로깅 시스템을 위한 인코딩 설정"""
    if sys.platform.startswith('win'):
        # 로깅 핸들러의 인코딩 설정
        import logging
        
        # 루트 로거의 모든 핸들러에 UTF-8 인코딩 설정
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if hasattr(handler, 'stream') and hasattr(handler.stream, 'reconfigure'):
                try:
                    handler.stream.reconfigure(encoding='utf-8')
                except Exception:
                    pass

# 모듈 로드 시 자동으로 인코딩 설정
setup_windows_encoding()
