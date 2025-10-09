"""
CryptoAutoTrader - 메인 실행 파일
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.core.trading_system import TradingSystem
from src.core.config_manager import ConfigManager


def main():
    """
    메인 함수
    """
    # 로거 설정
    logger = setup_logger("CryptoAutoTrader", "logs/trading.log")
    logger.info("=" * 60)
    logger.info("CryptoAutoTrader 시작")
    logger.info("=" * 60)
    
    try:
        # 설정 로드
        logger.info("설정 파일 로드 중...")
        config_manager = ConfigManager()
        # config = config_manager.load_config()
        
        # 트레이딩 시스템 초기화
        logger.info("트레이딩 시스템 초기화 중...")
        trading_system = TradingSystem()
        
        # 시스템 시작
        logger.info("트레이딩 시스템 시작")
        logger.info("종료하려면 Ctrl+C를 누르세요")
        # trading_system.start()
        
        # TODO: 실제 구현 완료 후 주석 해제
        logger.info("아직 구현되지 않았습니다. Phase 1부터 개발을 시작하세요.")
        
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 시스템 종료")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
    finally:
        logger.info("=" * 60)
        logger.info("CryptoAutoTrader 종료")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

