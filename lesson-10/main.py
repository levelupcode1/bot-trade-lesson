#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 봇 메인 실행 파일
자동매매 시스템 알림 봇의 진입점 (python-telegram-bot 20.x)
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

from src.telegram_bot.utils.encoding_utils import setup_windows_encoding, safe_print
from src.telegram_bot.core.bot_initializer import BotInitializer
from src.telegram_bot.utils.logger import get_logger

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

async def main():
    """메인 함수"""
    # 환경 변수 확인
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        safe_print("❌ TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        safe_print("환경 변수를 설정하고 다시 실행하세요.")
        sys.exit(1)

    bot_initializer = BotInitializer("config")
    try:
        await bot_initializer.initialize()
        logger.info("텔레그램 봇 시작")
        safe_print("✅ 텔레그램 봇이 성공적으로 시작되었습니다!")
        safe_print("봇을 종료하려면 Ctrl+C를 누르세요.")
        await bot_initializer.run()
    except Exception as e:
        logger.error(f"애플리케이션 실행 오류: {e}")
        safe_print(f"❌ 애플리케이션 실행 오류: {e}")
    finally:
        logger.info("텔레그램 봇 중지 중...")
        await bot_initializer.stop()
        logger.info("텔레그램 봇 중지 완료")
        safe_print("👋 봇을 종료합니다.")

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
    setup_windows_encoding()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\n👋 봇을 종료합니다.")
    except Exception as e:
        safe_print(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)