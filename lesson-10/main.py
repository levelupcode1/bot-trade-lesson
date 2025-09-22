#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 봇 메인 실행 파일
자동매매 시스템 알림 봇의 진입점
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# 인코딩 유틸리티 임포트 (Windows 환경에서 한글 출력을 위한 설정)
from src.telegram_bot.utils.encoding_utils import setup_windows_encoding, safe_print

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.telegram_bot.core.bot_initializer import BotInitializer
from src.telegram_bot.utils.logger import get_logger

class TelegramBotApp:
    """텔레그램 봇 애플리케이션 클래스"""
    
    def __init__(self):
        self.bot_initializer = None
        self.logger = get_logger(__name__)
        self.running = False
        
    def initialize(self) -> None:
        """애플리케이션 초기화"""
        try:
            # 봇 초기화자 생성
            self.bot_initializer = BotInitializer("config")
            
            # 봇 초기화
            self.bot_initializer.initialize()
            
            self.logger.info("애플리케이션 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"애플리케이션 초기화 오류: {e}")
            raise
    
    def start(self) -> None:
        """애플리케이션 시작"""
        try:
            if not self.bot_initializer:
                self.initialize()
            
            self.running = True
            self.logger.info("텔레그램 봇 시작")
            
            # 봇 실행
            self.bot_initializer.start_bot()
            
        except Exception as e:
            self.logger.error(f"애플리케이션 시작 오류: {e}")
            raise
    
    def stop(self) -> None:
        """애플리케이션 중지"""
        try:
            self.running = False
            self.logger.info("텔레그램 봇 중지 중...")
            
            if self.bot_initializer:
                self.bot_initializer.stop_bot()
            
            self.logger.info("텔레그램 봇 중지 완료")
            
        except Exception as e:
            self.logger.error(f"애플리케이션 중지 오류: {e}")
    
    def reload_config(self) -> None:
        """설정 재로드"""
        try:
            if self.bot_initializer:
                success = self.bot_initializer.reload_config()
                if success:
                    self.logger.info("설정 재로드 성공")
                else:
                    self.logger.warning("설정 재로드 실패")
            else:
                self.logger.warning("봇이 초기화되지 않았습니다")
                
        except Exception as e:
            self.logger.error(f"설정 재로드 오류: {e}")

def main():
    """메인 함수"""
    app = TelegramBotApp()
    
    # 시그널 핸들러 설정
    def signal_handler(signum, frame):
        """시그널 핸들러"""
        safe_print(f"\n시그널 {signum} 수신. 봇을 중지합니다...")
        app.stop()
    
    # SIGINT (Ctrl+C) 및 SIGTERM 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 환경 변수 확인
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            safe_print("❌ TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
            safe_print("환경 변수를 설정하고 다시 실행하세요.")
            sys.exit(1)
        
        # 애플리케이션 시작
        app.start()
        
    except KeyboardInterrupt:
        safe_print("\n키보드 인터럽트 감지. 봇을 중지합니다...")
        app.stop()
        
    except Exception as e:
        safe_print(f"❌ 애플리케이션 실행 오류: {e}")
        app.stop()
        sys.exit(1)

def check_requirements():
    """필수 요구사항 확인"""
    required_files = [
        "config/bot_config.yaml",
        "src/telegram_bot/__init__.py",
        "src/telegram_bot/core/__init__.py",
        "src/telegram_bot/handlers/__init__.py",
        "src/telegram_bot/templates/__init__.py",
        "src/telegram_bot/utils/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        safe_print("❌ 필수 파일이 누락되었습니다:")
        for file_path in missing_files:
            safe_print(f"  - {file_path}")
        return False
    
    return True

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "config",
        "logs",
        "src/telegram_bot",
        "src/telegram_bot/core",
        "src/telegram_bot/handlers",
        "src/telegram_bot/templates",
        "src/telegram_bot/config",
        "src/telegram_bot/utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    safe_print("🚀 텔레그램 봇 시작 중...")
    
    # 디렉토리 설정
    setup_directories()
    
    # 필수 요구사항 확인
    if not check_requirements():
        safe_print("❌ 필수 요구사항을 확인하고 다시 실행하세요.")
        sys.exit(1)
    
    # 환경 변수 안내
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        safe_print("\n📝 환경 변수 설정이 필요합니다:")
        safe_print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        safe_print("\n봇 토큰을 설정하고 다시 실행하세요.")
        sys.exit(1)
    
    # 메인 함수 실행
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n👋 봇을 종료합니다.")
    except Exception as e:
        safe_print(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)
