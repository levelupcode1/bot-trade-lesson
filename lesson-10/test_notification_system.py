"""
알림 시스템 테스트 스크립트
다양한 알림 시나리오를 테스트하고 시스템 동작을 확인
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.telegram_bot.notifications.notification_service import NotificationService
from src.telegram_bot.notifications.notification_manager import NotificationType, NotificationPriority
from src.telegram_bot.notifications.user_settings_manager import UserSettingsManager


class MockTelegramBot:
    """테스트용 모의 텔레그램 봇"""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_message(self, chat_id: str, text: str, parse_mode: str = None):
        """메시지 전송 모의 구현"""
        message = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "timestamp": datetime.now().isoformat()
        }
        self.sent_messages.append(message)
        print(f"📤 메시지 전송됨: {chat_id}")
        print(f"📝 내용: {text[:100]}...")
        print("-" * 50)
        return True


async def test_notification_system():
    """알림 시스템 종합 테스트"""
    
    print("🚀 알림 시스템 테스트 시작")
    print("=" * 60)
    
    # 모의 텔레그램 봇 생성
    mock_bot = MockTelegramBot()
    
    # 알림 서비스 초기화
    notification_service = NotificationService(
        telegram_bot=mock_bot,
        settings_dir="test_data/user_settings"
    )
    
    try:
        # 서비스 시작
        await notification_service.start()
        print("✅ 알림 서비스 시작 완료")
        
        # 테스트 사용자 ID
        test_user_id = "test_user_001"
        
        # 사용자 설정 테스트
        print("\n📋 사용자 설정 테스트")
        print("-" * 30)
        
        user_settings = notification_service.get_user_notification_settings(test_user_id)
        print(f"기본 설정: {len(user_settings.enabled_types)}개 알림 타입 활성화")
        
        # 설정 업데이트 테스트
        updates = {
            "enabled_types": ["trade_execution", "profit_achievement", "loss_limit"],
            "priority_threshold": 2,
            "batch_mode": True
        }
        
        success = notification_service.update_user_notification_settings(test_user_id, updates)
        print(f"설정 업데이트: {'성공' if success else '실패'}")
        
        # 각 알림 타입별 테스트
        print("\n🔔 알림 타입별 테스트")
        print("-" * 30)
        
        # 1. 거래 실행 알림 테스트
        print("1️⃣ 거래 실행 알림 테스트")
        trade_data = {
            "id": "TRD001",
            "symbol": "KRW-BTC",
            "amount": 0.001,
            "currency": "BTC",
            "price": 52000000,
            "total": 52000,
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "strategy": "Volatility Breakout",
            "target_price": 53000000,
            "stop_loss": 51000000
        }
        
        success = await notification_service.send_trade_execution_notification(
            test_user_id, "buy", trade_data
        )
        print(f"매수 알림: {'성공' if success else '실패'}")
        
        # 매도 알림 테스트
        trade_data["action"] = "sell"
        trade_data["profit_rate"] = 3.2
        trade_data["profit_amount"] = 1664
        
        success = await notification_service.send_trade_execution_notification(
            test_user_id, "sell", trade_data
        )
        print(f"매도 알림: {'성공' if success else '실패'}")
        
        # 2. 수익률 달성 알림 테스트
        print("\n2️⃣ 수익률 달성 알림 테스트")
        profit_data = {
            "daily_return": 8.5,
            "realized_pnl": 850000,
            "total_return": 15.2,
            "win_rate": 72.0,
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "daily_trades": 12
        }
        
        success = await notification_service.send_profit_achievement_notification(
            test_user_id, "daily_target", profit_data
        )
        print(f"일일 목표 달성: {'성공' if success else '실패'}")
        
        # 3. 손실 한계 알림 테스트
        print("\n3️⃣ 손실 한계 알림 테스트")
        loss_data = {
            "daily_loss": -3.2,
            "loss_amount": -320000,
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "daily_trades": 8
        }
        
        success = await notification_service.send_loss_limit_notification(
            test_user_id, "daily_loss", loss_data
        )
        print(f"일일 손실 한계: {'성공' if success else '실패'}")
        
        # 4. 시스템 오류 알림 테스트
        print("\n4️⃣ 시스템 오류 알림 테스트")
        error_data = {
            "error_type": "Connection Timeout",
            "impact_scope": "거래 중단",
            "retry_count": 2,
            "max_retries": 3,
            "admin_notified": "Yes",
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "estimated_recovery": "5분 내"
        }
        
        success = await notification_service.send_system_error_notification(
            test_user_id, "api_error", error_data
        )
        print(f"API 오류 알림: {'성공' if success else '실패'}")
        
        # 5. 상태 보고 알림 테스트
        print("\n5️⃣ 상태 보고 알림 테스트")
        status_data = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "day_of_week": "화",
            "daily_return": 2.1,
            "trade_count": 8,
            "success_rate": 75.0,
            "uptime": 99.8,
            "notification_count": 12,
            "active_positions": 2
        }
        
        success = await notification_service.send_status_report_notification(
            test_user_id, "daily", status_data
        )
        print(f"일일 리포트: {'성공' if success else '실패'}")
        
        # 6. 리스크 경고 알림 테스트
        print("\n6️⃣ 리스크 경고 알림 테스트")
        warning_data = {
            "volatility": 15.2,
            "vs_average": 8.5,
            "risk_level": "High",
            "recommendation": "포지션 크기 축소 권장",
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "affected_coins": ["KRW-BTC", "KRW-ETH"]
        }
        
        success = await notification_service.send_risk_warning_notification(
            test_user_id, "high_volatility", warning_data
        )
        print(f"변동성 경고: {'성공' if success else '실패'}")
        
        # 7. 중복 알림 방지 테스트
        print("\n7️⃣ 중복 알림 방지 테스트")
        print("동일한 알림을 3번 연속 전송 시도...")
        
        for i in range(3):
            success = await notification_service.send_trade_execution_notification(
                test_user_id, "buy", trade_data
            )
            print(f"  {i+1}번째 시도: {'성공' if success else '실패 (중복)'}")
            await asyncio.sleep(1)  # 1초 대기
        
        # 8. 알림 히스토리 테스트
        print("\n8️⃣ 알림 히스토리 테스트")
        history = notification_service.get_notification_history(test_user_id, limit=10)
        print(f"알림 히스토리: {len(history)}건 조회됨")
        
        for i, notification in enumerate(history[:3], 1):
            print(f"  {i}. {notification.type.value} - {notification.timestamp.strftime('%H:%M:%S')}")
        
        # 9. 서비스 상태 확인
        print("\n9️⃣ 서비스 상태 확인")
        status = notification_service.get_service_status()
        print(f"서비스 실행 중: {status['service_running']}")
        print(f"큐 상태: {status['queue_status']}")
        print(f"설정 요약: {status['settings_summary']}")
        
        # 10. 알림 시스템 테스트
        print("\n🔟 종합 알림 시스템 테스트")
        test_results = await notification_service.test_notification_system(test_user_id)
        
        print(f"테스트 결과:")
        for test_name, result in test_results.items():
            if test_name != "summary":
                print(f"  {test_name}: {result}")
        
        if "summary" in test_results:
            summary = test_results["summary"]
            print(f"\n📊 테스트 요약:")
            print(f"  총 테스트: {summary['total_tests']}개")
            print(f"  성공: {summary['successful_tests']}개")
            print(f"  성공률: {summary['success_rate']:.1f}%")
        
        # 전송된 메시지 통계
        print(f"\n📈 전송 통계:")
        print(f"  총 전송 메시지: {len(mock_bot.sent_messages)}건")
        
        # 메시지 타입별 통계
        message_types = {}
        for msg in mock_bot.sent_messages:
            msg_type = "기타"
            if "매수" in msg["text"] or "매도" in msg["text"]:
                msg_type = "거래 실행"
            elif "수익률" in msg["text"] or "달성" in msg["text"]:
                msg_type = "수익률 달성"
            elif "손실" in msg["text"] or "한계" in msg["text"]:
                msg_type = "손실 한계"
            elif "오류" in msg["text"] or "ERROR" in msg["text"]:
                msg_type = "시스템 오류"
            elif "리포트" in msg["text"] or "상태" in msg["text"]:
                msg_type = "상태 보고"
            elif "경고" in msg["text"] or "리스크" in msg["text"]:
                msg_type = "리스크 경고"
            
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}건")
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 서비스 중지
        await notification_service.stop()
        print("\n🛑 알림 서비스 중지 완료")


async def test_user_settings():
    """사용자 설정 관리 테스트"""
    
    print("\n🔧 사용자 설정 관리 테스트")
    print("=" * 40)
    
    settings_manager = UserSettingsManager("test_data/user_settings")
    
    test_user_id = "settings_test_user"
    
    try:
        # 1. 기본 설정 조회
        print("1️⃣ 기본 설정 조회")
        settings = settings_manager.get_user_settings(test_user_id)
        print(f"기본 활성화 타입: {len(settings.enabled_types)}개")
        print(f"우선순위 임계값: {settings.priority_threshold.name}")
        
        # 2. 설정 업데이트
        print("\n2️⃣ 설정 업데이트")
        updates = {
            "enabled_types": ["trade_execution", "profit_achievement"],
            "priority_threshold": 2,
            "batch_mode": True,
            "quiet_hours": {
                "enabled": True,
                "start_time": "22:00",
                "end_time": "08:00"
            }
        }
        
        success = settings_manager.update_user_settings(test_user_id, updates)
        print(f"설정 업데이트: {'성공' if success else '실패'}")
        
        # 3. 업데이트된 설정 확인
        print("\n3️⃣ 업데이트된 설정 확인")
        updated_settings = settings_manager.get_user_settings(test_user_id)
        print(f"활성화 타입: {[t.value for t in updated_settings.enabled_types]}")
        print(f"배치 모드: {updated_settings.batch_mode}")
        print(f"조용한 시간: {updated_settings.quiet_hours.enabled}")
        
        # 4. 설정 유효성 검증
        print("\n4️⃣ 설정 유효성 검증")
        errors = settings_manager.validate_settings(updated_settings)
        if errors:
            print(f"유효성 검증 오류: {errors}")
        else:
            print("유효성 검증: 통과")
        
        # 5. 설정 내보내기/가져오기
        print("\n5️⃣ 설정 내보내기/가져오기")
        export_path = "test_data/exported_settings.json"
        export_success = settings_manager.export_user_settings(test_user_id, export_path)
        print(f"설정 내보내기: {'성공' if export_success else '실패'}")
        
        # 6. 설정 요약
        print("\n6️⃣ 설정 요약")
        summary = settings_manager.get_settings_summary()
        print(f"총 사용자: {summary['total_users']}명")
        print(f"활성 사용자: {summary['active_users']}명")
        print(f"알림 타입 사용률: {summary['notification_types_usage']}")
        
    except Exception as e:
        print(f"❌ 사용자 설정 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수"""
    
    # 환경 변수 설정 (테스트용)
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_12345"
    
    try:
        # 알림 시스템 테스트
        await test_notification_system()
        
        # 사용자 설정 테스트
        await test_user_settings()
        
        print("\n🎉 모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 메인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 테스트 데이터 디렉토리 생성
    Path("test_data/user_settings").mkdir(parents=True, exist_ok=True)
    
    # 테스트 실행
    asyncio.run(main())













