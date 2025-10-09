#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 리포트 시스템 메인 실행 파일
"""

import sys
from pathlib import Path
import logging
import signal

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigManager
from core.scheduler import ReportScheduler
from core.report_manager import ReportManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_report.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """종료 시그널 핸들러"""
    logger.info("시스템 종료 요청 수신")
    sys.exit(0)

def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("자동 리포트 생성 시스템 시작")
    logger.info("=" * 60)
    
    # 설정 로드
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        logger.info("설정 파일이 없습니다. 기본 설정 파일을 생성합니다.")
        ConfigManager.save_default_config(str(config_path))
        logger.info(f"설정 파일 생성: {config_path}")
        logger.info("config.yaml 파일을 수정한 후 다시 실행하세요.")
        return
    
    config = ConfigManager.load_config(str(config_path))
    
    # 스케줄러 초기화
    scheduler = ReportScheduler(config)
    
    if not scheduler.scheduler:
        logger.error("스케줄러 초기화 실패. 수동 리포트 생성 모드로 전환합니다.")
        logger.info("일간 리포트를 수동으로 생성합니다...")
        
        manager = ReportManager(config)
        files = manager.generate_report('daily')
        
        if files:
            logger.info("리포트 생성 완료:")
            for format_type, path in files.items():
                logger.info(f"  - {format_type.upper()}: {path}")
        
        return
    
    # 스케줄 추가
    schedule_config = config.get('schedule', {})
    
    if schedule_config.get('daily', {}).get('enabled'):
        scheduler.add_daily_report(
            hour=schedule_config['daily'].get('hour', 23),
            minute=schedule_config['daily'].get('minute', 0)
        )
    
    if schedule_config.get('weekly', {}).get('enabled'):
        scheduler.add_weekly_report(
            day_of_week=schedule_config['weekly'].get('day_of_week', 6),
            hour=schedule_config['weekly'].get('hour', 23),
            minute=schedule_config['weekly'].get('minute', 30)
        )
    
    if schedule_config.get('monthly', {}).get('enabled'):
        scheduler.add_monthly_report(
            day=schedule_config['monthly'].get('day', 1),
            hour=schedule_config['monthly'].get('hour', 1),
            minute=schedule_config['monthly'].get('minute', 0)
        )
    
    if schedule_config.get('alert', {}).get('enabled'):
        scheduler.add_alert_monitor(
            interval_minutes=schedule_config['alert'].get('interval_minutes', 5)
        )
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 스케줄러 시작
    logger.info("스케줄러가 시작되었습니다. Ctrl+C로 종료할 수 있습니다.")
    scheduler.start()

if __name__ == "__main__":
    main()

