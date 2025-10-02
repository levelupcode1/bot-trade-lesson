"""
통합 알림 서비스
알림 관리자, 템플릿, 사용자 설정을 통합하여 제공하는 서비스
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .notification_manager import (
    NotificationManager, NotificationType, NotificationPriority,
    NotificationMessage, UserNotificationSettings
)
from .notification_templates import NotificationTemplateBuilder
from .user_settings_manager import UserSettingsManager, UserNotificationPreferences


class NotificationService:
    """통합 알림 서비스"""
    
    def __init__(self, telegram_bot=None, settings_dir: str = "data/user_settings"):
        self.logger = logging.getLogger(__name__)
        
        # 핵심 컴포넌트 초기화
        self.notification_manager = NotificationManager(telegram_bot)
        self.template_builder = NotificationTemplateBuilder()
        self.settings_manager = UserSettingsManager(settings_dir)
        
        # 서비스 상태
        self._running = False
        self._startup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """알림 서비스 시작"""
        if self._running:
            self.logger.warning("알림 서비스가 이미 실행 중입니다")
            return
        
        self._running = True
        
        try:
            # 알림 관리자 시작
            await self.notification_manager.start()
            
            # 설정 동기화 작업 시작
            self._startup_task = asyncio.create_task(self._sync_user_settings())
            
            self.logger.info("알림 서비스 시작 완료")
            
        except Exception as e:
            self.logger.error(f"알림 서비스 시작 실패: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """알림 서비스 중지"""
        self._running = False
        
        try:
            # 시작 작업 취소
            if self._startup_task:
                self._startup_task.cancel()
                try:
                    await self._startup_task
                except asyncio.CancelledError:
                    pass
            
            # 알림 관리자 중지
            await self.notification_manager.stop()
            
            self.logger.info("알림 서비스 중지 완료")
            
        except Exception as e:
            self.logger.error(f"알림 서비스 중지 중 오류: {e}")
    
    async def send_trade_execution_notification(
        self,
        user_id: str,
        action: str,
        trade_data: Dict[str, Any]
    ) -> bool:
        """거래 실행 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_trade_execution_message(action, trade_data)
            
            # 제목 생성
            action_emoji = "🟢" if action.lower() == "buy" else "🔴"
            action_text = "매수" if action.lower() == "buy" else "매도"
            title = f"{action_emoji} {action_text} 체결"
            
            # 메타데이터 설정
            metadata = {
                "trade_id": trade_data.get("id"),
                "symbol": trade_data.get("symbol"),
                "amount": trade_data.get("amount"),
                "price": trade_data.get("price"),
                "strategy": trade_data.get("strategy", "Unknown")
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.TRADE_EXECUTION,
                user_id,
                title,
                message,
                NotificationPriority.HIGH,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"거래 실행 알림 전송 실패: {e}")
            return False
    
    async def send_profit_achievement_notification(
        self,
        user_id: str,
        achievement_type: str,
        profit_data: Dict[str, Any]
    ) -> bool:
        """수익률 달성 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_profit_achievement_message(achievement_type, profit_data)
            
            # 제목 생성
            title_map = {
                "daily_target": "🎉 일일 수익률 목표 달성!",
                "weekly_target": "🏆 주간 수익률 목표 달성!",
                "milestone": "🎊 수익률 마일스톤 달성!"
            }
            title = title_map.get(achievement_type, "🎉 수익률 목표 달성!")
            
            # 메타데이터 설정
            metadata = {
                "achievement_type": achievement_type,
                "return_percent": profit_data.get("daily_return", profit_data.get("weekly_return", 0)),
                "pnl_amount": profit_data.get("realized_pnl", 0),
                "win_rate": profit_data.get("win_rate", 0)
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.PROFIT_ACHIEVEMENT,
                user_id,
                title,
                message,
                NotificationPriority.MEDIUM,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"수익률 달성 알림 전송 실패: {e}")
            return False
    
    async def send_loss_limit_notification(
        self,
        user_id: str,
        loss_type: str,
        loss_data: Dict[str, Any]
    ) -> bool:
        """손실 한계 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_loss_limit_message(loss_type, loss_data)
            
            # 제목 생성
            title_map = {
                "daily_loss": "🚨 일일 손실 한계 도달!",
                "position_loss": "⚠️ 포지션 손실 한계 도달!",
                "consecutive_loss": "🔄 연속 손실 거래 감지!"
            }
            title = title_map.get(loss_type, "🚨 손실 한계 도달!")
            
            # 메타데이터 설정
            metadata = {
                "loss_type": loss_type,
                "loss_percent": loss_data.get("daily_loss", loss_data.get("position_loss", 0)),
                "loss_amount": loss_data.get("loss_amount", 0),
                "auto_stop": True
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.LOSS_LIMIT,
                user_id,
                title,
                message,
                NotificationPriority.CRITICAL,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"손실 한계 알림 전송 실패: {e}")
            return False
    
    async def send_system_error_notification(
        self,
        user_id: str,
        error_type: str,
        error_data: Dict[str, Any]
    ) -> bool:
        """시스템 오류 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_system_error_message(error_type, error_data)
            
            # 제목 생성
            title_map = {
                "api_error": "🔥 API 연결 오류",
                "order_error": "⚠️ 주문 실행 오류",
                "data_error": "📊 데이터 수신 오류"
            }
            title = title_map.get(error_type, "🔥 시스템 오류 발생")
            
            # 메타데이터 설정
            metadata = {
                "error_type": error_type,
                "error_code": error_data.get("error_code", "Unknown"),
                "retry_count": error_data.get("retry_count", 0),
                "impact_level": error_data.get("impact_level", "Medium")
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.SYSTEM_ERROR,
                user_id,
                title,
                message,
                NotificationPriority.CRITICAL,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"시스템 오류 알림 전송 실패: {e}")
            return False
    
    async def send_status_report_notification(
        self,
        user_id: str,
        report_type: str,
        status_data: Dict[str, Any]
    ) -> bool:
        """상태 보고 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_status_report_message(report_type, status_data)
            
            # 제목 생성
            title_map = {
                "daily": "📊 일일 거래 리포트",
                "weekly": "📈 주간 성과 리포트",
                "monthly": "📊 월간 성과 리포트"
            }
            title = title_map.get(report_type, "📊 상태 보고")
            
            # 메타데이터 설정
            metadata = {
                "report_type": report_type,
                "return_percent": status_data.get("daily_return", status_data.get("weekly_return", 0)),
                "trade_count": status_data.get("trade_count", status_data.get("total_trades", 0)),
                "success_rate": status_data.get("success_rate", 0)
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.STATUS_REPORT,
                user_id,
                title,
                message,
                NotificationPriority.LOW,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"상태 보고 알림 전송 실패: {e}")
            return False
    
    async def send_config_change_notification(
        self,
        user_id: str,
        config_type: str,
        config_data: Dict[str, Any]
    ) -> bool:
        """설정 변경 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_config_change_message(config_type, config_data)
            
            # 제목 생성
            title_map = {
                "risk_settings": "⚙️ 리스크 설정 변경",
                "strategy_settings": "📈 전략 설정 변경",
                "notification_settings": "🔔 알림 설정 변경"
            }
            title = title_map.get(config_type, "⚙️ 설정 변경")
            
            # 메타데이터 설정
            metadata = {
                "config_type": config_type,
                "changed_by": config_data.get("changed_by", "System"),
                "change_summary": config_data.get("change_summary", "설정이 변경되었습니다")
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.CONFIG_CHANGE,
                user_id,
                title,
                message,
                NotificationPriority.MEDIUM,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"설정 변경 알림 전송 실패: {e}")
            return False
    
    async def send_risk_warning_notification(
        self,
        user_id: str,
        warning_type: str,
        warning_data: Dict[str, Any]
    ) -> bool:
        """리스크 경고 알림 전송"""
        try:
            # 메시지 생성
            message = self.template_builder.build_risk_warning_message(warning_type, warning_data)
            
            # 제목 생성
            title_map = {
                "high_volatility": "⚠️ 높은 변동성 감지",
                "low_liquidity": "💧 낮은 유동성 감지",
                "market_anomaly": "🔍 시장 이상 감지"
            }
            title = title_map.get(warning_type, "⚠️ 리스크 경고")
            
            # 메타데이터 설정
            metadata = {
                "warning_type": warning_type,
                "risk_level": warning_data.get("risk_level", "Medium"),
                "affected_coins": warning_data.get("affected_coins", []),
                "recommendation": warning_data.get("recommendation", "None")
            }
            
            return await self.notification_manager.send_notification(
                NotificationType.RISK_WARNING,
                user_id,
                title,
                message,
                NotificationPriority.HIGH,
                metadata
            )
            
        except Exception as e:
            self.logger.error(f"리스크 경고 알림 전송 실패: {e}")
            return False
    
    def get_user_notification_settings(self, user_id: str) -> UserNotificationPreferences:
        """사용자 알림 설정 조회"""
        return self.settings_manager.get_user_settings(user_id)
    
    def update_user_notification_settings(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """사용자 알림 설정 업데이트"""
        success = self.settings_manager.update_user_settings(user_id, updates)
        
        if success:
            # 알림 관리자의 사용자 설정도 업데이트
            self._sync_user_settings_to_manager(user_id)
        
        return success
    
    def get_notification_history(self, user_id: str, limit: int = 50) -> List[NotificationMessage]:
        """사용자 알림 히스토리 조회"""
        return self.notification_manager.history.get_user_history(user_id, limit)
    
    def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 정보"""
        queue_status = self.notification_manager.get_queue_status()
        settings_summary = self.settings_manager.get_settings_summary()
        
        return {
            "service_running": self._running,
            "queue_status": queue_status,
            "settings_summary": settings_summary,
            "uptime": "N/A",  # 실제로는 시작 시간부터 계산
            "last_activity": datetime.now().isoformat()
        }
    
    async def _sync_user_settings(self):
        """사용자 설정 동기화 (백그라운드 작업)"""
        while self._running:
            try:
                # 모든 사용자 설정을 알림 관리자와 동기화
                user_ids = self.settings_manager.list_all_users()
                
                for user_id in user_ids:
                    try:
                        self._sync_user_settings_to_manager(user_id)
                    except Exception as e:
                        self.logger.warning(f"사용자 {user_id} 설정 동기화 실패: {e}")
                
                # 5분마다 동기화
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"사용자 설정 동기화 중 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기
    
    def _sync_user_settings_to_manager(self, user_id: str):
        """개별 사용자 설정을 알림 관리자와 동기화"""
        try:
            preferences = self.settings_manager.get_user_settings(user_id)
            
            # UserNotificationSettings 객체로 변환
            user_settings = UserNotificationSettings(
                user_id=user_id,
                enabled_types=preferences.enabled_types,
                priority_threshold=preferences.priority_threshold,
                cooldown_settings=preferences.cooldown_settings.__dict__,
                quiet_hours=preferences.quiet_hours.__dict__,
                batch_mode=preferences.batch_mode,
                summary_mode=preferences.summary_mode
            )
            
            # 알림 관리자에 설정 적용
            self.notification_manager.set_user_settings(user_id, user_settings)
            
        except Exception as e:
            self.logger.error(f"사용자 {user_id} 설정 동기화 실패: {e}")
    
    async def broadcast_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """모든 사용자에게 알림 브로드캐스트"""
        try:
            user_ids = self.settings_manager.list_all_users()
            results = {}
            
            for user_id in user_ids:
                try:
                    success = await self.notification_manager.send_notification(
                        notification_type,
                        user_id,
                        title,
                        message,
                        priority,
                        metadata
                    )
                    results[user_id] = success
                except Exception as e:
                    self.logger.error(f"사용자 {user_id} 브로드캐스트 실패: {e}")
                    results[user_id] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"브로드캐스트 알림 실패: {e}")
            return {}
    
    async def test_notification_system(self, user_id: str) -> Dict[str, Any]:
        """알림 시스템 테스트"""
        test_results = {}
        
        try:
            # 각 알림 타입별 테스트 데이터
            test_data = {
                "trade_execution": {
                    "action": "buy",
                    "trade_data": {
                        "id": "TEST001",
                        "symbol": "KRW-BTC",
                        "amount": 0.001,
                        "currency": "BTC",
                        "price": 52000000,
                        "total": 52000,
                        "timestamp": datetime.now().strftime('%H:%M:%S'),
                        "strategy": "Volatility Breakout"
                    }
                },
                "profit_achievement": {
                    "achievement_type": "daily_target",
                    "profit_data": {
                        "daily_return": 8.5,
                        "realized_pnl": 850000,
                        "total_return": 15.2,
                        "win_rate": 72.0,
                        "timestamp": datetime.now().strftime('%H:%M:%S'),
                        "daily_trades": 12
                    }
                },
                "system_error": {
                    "error_type": "api_error",
                    "error_data": {
                        "error_type": "Connection Timeout",
                        "impact_scope": "거래 중단",
                        "retry_count": 2,
                        "max_retries": 3,
                        "admin_notified": "Yes",
                        "timestamp": datetime.now().strftime('%H:%M:%S'),
                        "estimated_recovery": "5분 내"
                    }
                }
            }
            
            # 테스트 실행
            for test_name, test_info in test_data.items():
                try:
                    if test_name == "trade_execution":
                        success = await self.send_trade_execution_notification(
                            user_id, test_info["action"], test_info["trade_data"]
                        )
                    elif test_name == "profit_achievement":
                        success = await self.send_profit_achievement_notification(
                            user_id, test_info["achievement_type"], test_info["profit_data"]
                        )
                    elif test_name == "system_error":
                        success = await self.send_system_error_notification(
                            user_id, test_info["error_type"], test_info["error_data"]
                        )
                    else:
                        success = False
                    
                    test_results[test_name] = {
                        "success": success,
                        "message": "테스트 성공" if success else "테스트 실패"
                    }
                    
                except Exception as e:
                    test_results[test_name] = {
                        "success": False,
                        "message": f"테스트 오류: {e}"
                    }
            
            # 전체 테스트 결과
            total_tests = len(test_results)
            successful_tests = sum(1 for result in test_results.values() if result["success"])
            
            test_results["summary"] = {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "test_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            test_results["error"] = str(e)
        
        return test_results


