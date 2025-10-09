#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 리포트 시스템 데모
수동으로 리포트를 생성하고 테스트하는 스크립트
"""

import sys
from pathlib import Path
import logging

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigManager
from core.report_manager import ReportManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def demo_daily_report():
    """일간 리포트 데모"""
    logger.info("=" * 60)
    logger.info("일간 리포트 생성 데모")
    logger.info("=" * 60)
    
    # 설정 로드
    config = ConfigManager.load_config()
    
    # 리포트 관리자 생성
    manager = ReportManager(config)
    
    # 일간 리포트 생성
    logger.info("일간 리포트 생성 중...")
    files = manager.generate_report('daily')
    
    if files:
        logger.info("\n✅ 리포트 생성 완료!")
        for format_type, path in files.items():
            logger.info(f"  📄 {format_type.upper()}: {path}")
    else:
        logger.warning("⚠️  리포트 생성 실패 또는 데이터 없음")

def demo_weekly_report():
    """주간 리포트 데모"""
    logger.info("=" * 60)
    logger.info("주간 리포트 생성 데모")
    logger.info("=" * 60)
    
    config = ConfigManager.load_config()
    manager = ReportManager(config)
    
    logger.info("주간 리포트 생성 중...")
    files = manager.generate_report('weekly')
    
    if files:
        logger.info("\n✅ 리포트 생성 완료!")
        for format_type, path in files.items():
            logger.info(f"  📄 {format_type.upper()}: {path}")
    else:
        logger.warning("⚠️  리포트 생성 실패 또는 데이터 없음")

def demo_monthly_report():
    """월간 리포트 데모"""
    logger.info("=" * 60)
    logger.info("월간 리포트 생성 데모")
    logger.info("=" * 60)
    
    config = ConfigManager.load_config()
    manager = ReportManager(config)
    
    logger.info("월간 리포트 생성 중...")
    files = manager.generate_report('monthly')
    
    if files:
        logger.info("\n✅ 리포트 생성 완료!")
        for format_type, path in files.items():
            logger.info(f"  📄 {format_type.upper()}: {path}")
    else:
        logger.warning("⚠️  리포트 생성 실패 또는 데이터 없음")

def demo_alert_check():
    """알림 체크 데모"""
    logger.info("=" * 60)
    logger.info("이상 상황 체크 데모")
    logger.info("=" * 60)
    
    from analyzers.alert_analyzer import AlertAnalyzer
    
    config = ConfigManager.load_config()
    analyzer = AlertAnalyzer(config)
    
    logger.info("이상 상황 체크 중...")
    alerts = analyzer.check_anomalies()
    
    if alerts:
        logger.info(f"\n⚠️  {len(alerts)}개의 알림이 감지되었습니다:")
        for i, alert in enumerate(alerts, 1):
            logger.info(f"\n{i}. {alert.get('title')}")
            logger.info(f"   설명: {alert.get('description')}")
            logger.info(f"   심각도: {alert.get('severity')}")
    else:
        logger.info("\n✅ 이상 상황 없음")

def main():
    """메인 함수"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       자동 리포트 시스템 데모                              ║
╚══════════════════════════════════════════════════════════╝

선택하세요:
1. 일간 리포트 생성
2. 주간 리포트 생성
3. 월간 리포트 생성
4. 이상 상황 체크
5. 모든 리포트 생성
0. 종료
""")
    
    # 설정 파일 확인
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        logger.warning("설정 파일이 없습니다. 기본 설정을 생성합니다...")
        ConfigManager.save_default_config(str(config_path))
        logger.info(f"설정 파일 생성: {config_path}")
    
    while True:
        try:
            choice = input("\n선택 (0-5): ").strip()
            
            if choice == '0':
                logger.info("프로그램을 종료합니다.")
                break
            elif choice == '1':
                demo_daily_report()
            elif choice == '2':
                demo_weekly_report()
            elif choice == '3':
                demo_monthly_report()
            elif choice == '4':
                demo_alert_check()
            elif choice == '5':
                demo_daily_report()
                print()
                demo_weekly_report()
                print()
                demo_monthly_report()
                print()
                demo_alert_check()
            else:
                print("잘못된 선택입니다. 0-5 사이의 숫자를 입력하세요.")
                
        except KeyboardInterrupt:
            logger.info("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            logger.error(f"오류 발생: {e}", exc_info=True)

if __name__ == "__main__":
    main()

