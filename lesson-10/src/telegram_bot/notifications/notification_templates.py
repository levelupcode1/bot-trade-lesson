"""
알림 메시지 템플릿 시스템
각 알림 타입별로 최적화된 메시지 템플릿을 제공
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .notification_manager import NotificationType, NotificationPriority


class NotificationTemplates:
    """알림 메시지 템플릿 관리자"""
    
    # 거래 실행 템플릿
    TRADE_EXECUTION_TEMPLATES = {
        "buy": """
🟢 *매수 체결* #{trade_id}
📊 *{symbol}*: {amount} {currency}
💰 *가격*: {price:,}원
💵 *총액*: {total:,}원
⏰ *시간*: {timestamp}
📈 *전략*: {strategy}
🎯 *목표가*: {target_price:,}원
🛡️ *손절가*: {stop_loss:,}원
""",
        "sell": """
🔴 *매도 체결* #{trade_id}
📊 *{symbol}*: {amount} {currency}
💰 *가격*: {price:,}원
💵 *총액*: {total:,}원
⏰ *시간*: {timestamp}
📈 *전략*: {strategy}
📊 *수익률*: {profit_rate:+.2f}%
💰 *손익*: {profit_amount:+,}원
"""
    }
    
    # 수익률 달성 템플릿
    PROFIT_ACHIEVEMENT_TEMPLATES = {
        "daily_target": """
🎉 *일일 수익률 목표 달성!*
📊 *일일 수익률*: +{daily_return:.1f}%
💰 *실현 손익*: +{realized_pnl:,}원
📈 *누적 수익률*: +{total_return:.1f}%
🏆 *승률*: {win_rate:.1f}%
⏰ *달성 시간*: {timestamp}
📊 *금일 거래*: {daily_trades}회
""",
        "weekly_target": """
🏆 *주간 수익률 목표 달성!*
📊 *주간 수익률*: +{weekly_return:.1f}%
💰 *실현 손익*: +{realized_pnl:,}원
📈 *누적 수익률*: +{total_return:.1f}%
🎯 *목표 달성률*: {achievement_rate:.1f}%
⏰ *달성 시간*: {timestamp}
📊 *주간 거래*: {weekly_trades}회
""",
        "milestone": """
🎊 *수익률 마일스톤 달성!*
🎯 *달성 마일스톤*: +{milestone}%
📊 *현재 수익률*: +{current_return:.1f}%
💰 *총 손익*: +{total_pnl:,}원
📈 *투자 대비 수익률*: +{roi:.1f}%
⏰ *달성 시간*: {timestamp}
🏆 *현재 승률*: {win_rate:.1f}%
"""
    }
    
    # 손실 한계 템플릿
    LOSS_LIMIT_TEMPLATES = {
        "daily_loss": """
🚨 *일일 손실 한계 도달!*
⚠️ *일일 손실*: {daily_loss:.1f}%
💸 *손실 금액*: {loss_amount:,}원
🛑 *자동 중지*: 활성화됨
📞 *긴급 연락*: 권장
⏰ *발생 시간*: {timestamp}
📊 *금일 거래*: {daily_trades}회
🔔 *다음 거래*: 내일 오전 9시
""",
        "position_loss": """
⚠️ *포지션 손실 한계 도달!*
📊 *포지션 손실*: {position_loss:.1f}%
💸 *손실 금액*: {loss_amount:,}원
🛑 *포지션 정리*: 진행 중
📈 *현재 가격*: {current_price:,}원
⏰ *발생 시간*: {timestamp}
🎯 *손절가*: {stop_loss:,}원
""",
        "consecutive_loss": """
🔄 *연속 손실 거래 감지!*
📊 *연속 손실*: {consecutive_loss}회
💸 *총 손실*: {total_loss:,}원
🛑 *자동 일시정지*: 활성화됨
⏰ *일시정지 시간*: {pause_duration}분
⏰ *발생 시간*: {timestamp}
🔍 *원인 분석*: 진행 중
"""
    }
    
    # 시스템 오류 템플릿
    SYSTEM_ERROR_TEMPLATES = {
        "api_error": """
🔥 *API 연결 오류 발생*
❌ *오류 유형*: {error_type}
📊 *영향 범위*: {impact_scope}
🔄 *복구 시도*: {retry_count}/{max_retries}회
📞 *관리자 알림*: {admin_notified}
⏰ *발생 시간*: {timestamp}
🔧 *예상 복구*: {estimated_recovery}
""",
        "order_error": """
⚠️ *주문 실행 오류*
❌ *오류 유형*: {error_type}
📊 *영향 거래*: {affected_trades}
🔄 *재시도*: {retry_count}/{max_retries}회
💰 *영향 금액*: {affected_amount:,}원
⏰ *발생 시간*: {timestamp}
📞 *고객 지원*: {support_contacted}
""",
        "data_error": """
📊 *데이터 수신 오류*
❌ *오류 유형*: {error_type}
📈 *영향 데이터*: {affected_data}
🔄 *복구 시도*: {retry_count}/{max_retries}회
⏰ *발생 시간*: {timestamp}
🔧 *대체 소스*: {backup_source}
📞 *상태 업데이트*: {status_update}
"""
    }
    
    # 정기 상태 보고 템플릿
    STATUS_REPORT_TEMPLATES = {
        "daily": """
📊 *일일 거래 리포트*
📅 *{date}* ({day_of_week})
💰 *일일 수익률*: {daily_return:+.1f}%
📈 *거래 횟수*: {trade_count}회
🏆 *성공률*: {success_rate:.1f}%
⏰ *가동률*: {uptime:.1f}%
🔔 *알림*: {notification_count}건
📊 *활성 포지션*: {active_positions}개
""",
        "weekly": """
📈 *주간 성과 리포트*
📅 *{start_date} ~ {end_date}*
💰 *주간 수익률*: {weekly_return:+.1f}%
📊 *총 거래*: {total_trades}회
🏆 *평균 승률*: {avg_success_rate:.1f}%
📈 *최고 수익률*: +{max_return:.1f}%
📉 *최대 손실*: {max_loss:.1f}%
⏰ *평균 가동률*: {avg_uptime:.1f}%
🎯 *목표 달성률*: {goal_achievement:.1f}%
""",
        "monthly": """
📊 *월간 성과 리포트*
📅 *{month}월 {year}년*
💰 *월간 수익률*: {monthly_return:+.1f}%
📈 *총 거래*: {total_trades}회
🏆 *평균 승률*: {avg_success_rate:.1f}%
📊 *샤프 비율*: {sharpe_ratio:.2f}
📈 *최대 수익률*: +{max_return:.1f}%
📉 *최대 낙폭*: {max_drawdown:.1f}%
⏰ *평균 가동률*: {avg_uptime:.1f}%
🎯 *목표 달성률*: {goal_achievement:.1f}%
"""
    }
    
    # 설정 변경 템플릿
    CONFIG_CHANGE_TEMPLATES = {
        "risk_settings": """
⚙️ *리스크 설정 변경*
🛡️ *포지션 크기*: {old_value}% → {new_value}%
🛑 *손절률*: {old_stop_loss}% → {new_stop_loss}%
🎯 *익절률*: {old_take_profit}% → {new_take_profit}%
⚠️ *일일 손실 한도*: {old_daily_limit}% → {new_daily_limit}%
⏰ *변경 시간*: {timestamp}
👤 *변경자*: {changed_by}
""",
        "strategy_settings": """
📈 *전략 설정 변경*
🎯 *전략*: {old_strategy} → {new_strategy}
⚙️ *매개변수*: {parameters}
🔄 *백테스트 결과*: {backtest_result}
⏰ *변경 시간*: {timestamp}
👤 *변경자*: {changed_by}
""",
        "notification_settings": """
🔔 *알림 설정 변경*
📢 *변경된 설정*: {changed_settings}
🔕 *비활성화*: {disabled_types}
🔔 *활성화*: {enabled_types}
⏰ *변경 시간*: {timestamp}
👤 *변경자*: {changed_by}
"""
    }
    
    # 리스크 경고 템플릿
    RISK_WARNING_TEMPLATES = {
        "high_volatility": """
⚠️ *높은 변동성 감지*
📊 *현재 변동성*: {volatility:.1f}%
📈 *평균 대비*: {vs_average:+.1f}%
🛡️ *리스크 수준*: {risk_level}
💡 *권장사항*: {recommendation}
⏰ *감지 시간*: {timestamp}
📊 *영향 코인*: {affected_coins}
""",
        "low_liquidity": """
💧 *낮은 유동성 감지*
📊 *현재 유동성*: {liquidity_level}
💰 *영향 금액*: {affected_amount:,}원
⚠️ *리스크*: {risk_description}
💡 *권장사항*: {recommendation}
⏰ *감지 시간*: {timestamp}
📊 *영향 코인*: {affected_coins}
""",
        "market_anomaly": """
🔍 *시장 이상 감지*
📊 *이상 유형*: {anomaly_type}
📈 *정상 대비*: {vs_normal:.1f}%
⚠️ *리스크 수준*: {risk_level}
💡 *권장사항*: {recommendation}
⏰ *감지 시간*: {timestamp}
📊 *영향 범위*: {affected_scope}
"""
    }
    
    @classmethod
    def get_template(
        cls, 
        notification_type: NotificationType, 
        template_key: str, 
        data: Dict[str, Any]
    ) -> str:
        """템플릿 가져오기 및 데이터 바인딩"""
        
        # 템플릿 선택
        template_map = {
            NotificationType.TRADE_EXECUTION: cls.TRADE_EXECUTION_TEMPLATES,
            NotificationType.PROFIT_ACHIEVEMENT: cls.PROFIT_ACHIEVEMENT_TEMPLATES,
            NotificationType.LOSS_LIMIT: cls.LOSS_LIMIT_TEMPLATES,
            NotificationType.SYSTEM_ERROR: cls.SYSTEM_ERROR_TEMPLATES,
            NotificationType.STATUS_REPORT: cls.STATUS_REPORT_TEMPLATES,
            NotificationType.CONFIG_CHANGE: cls.CONFIG_CHANGE_TEMPLATES,
            NotificationType.RISK_WARNING: cls.RISK_WARNING_TEMPLATES,
        }
        
        templates = template_map.get(notification_type, {})
        template = templates.get(template_key)
        
        if not template:
            # 기본 템플릿 사용
            return cls._get_default_template(notification_type, data)
        
        # 데이터 바인딩
        try:
            # 누락된 키에 대해 기본값 제공
            formatted_data = {}
            for key in template.split('{'):
                if '}' in key:
                    var_name = key.split('}')[0]
                    if ':' in var_name:
                        var_name = var_name.split(':')[0]
                    if var_name not in data:
                        data[var_name] = 'N/A'
            
            return template.format(**data)
        except (KeyError, ValueError) as e:
            cls._log_template_error(notification_type, template_key, e, data)
            return cls._get_fallback_template(notification_type, data)
    
    @classmethod
    def _get_default_template(cls, notification_type: NotificationType, data: Dict[str, Any]) -> str:
        """기본 템플릿 반환"""
        title = data.get('title', '알림')
        message = data.get('message', '알림이 발생했습니다.')
        timestamp = data.get('timestamp', datetime.now().strftime('%H:%M:%S'))
        
        return f"📢 *{title}*\n\n{message}\n\n⏰ {timestamp}"
    
    @classmethod
    def _get_fallback_template(cls, notification_type: NotificationType, data: Dict[str, Any]) -> str:
        """폴백 템플릿 반환"""
        return cls._get_default_template(notification_type, data)
    
    @classmethod
    def _log_template_error(cls, notification_type: NotificationType, template_key: str, error: Exception, data: Dict[str, Any]):
        """템플릿 오류 로깅"""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"템플릿 오류 - {notification_type.value}.{template_key}: {error}")
        logger.debug(f"데이터: {data}")


class NotificationTemplateBuilder:
    """알림 템플릿 빌더 - 동적 템플릿 생성"""
    
    def __init__(self):
        self.templates = NotificationTemplates()
    
    def build_trade_execution_message(
        self, 
        action: str, 
        trade_data: Dict[str, Any]
    ) -> str:
        """거래 실행 메시지 빌드"""
        template_key = action.lower()  # 'buy' 또는 'sell'
        
        # 기본 데이터 설정
        data = {
            'trade_id': trade_data.get('id', 'N/A'),
            'symbol': trade_data.get('symbol', 'N/A'),
            'amount': trade_data.get('amount', 0),
            'currency': trade_data.get('currency', ''),
            'price': trade_data.get('price', 0),
            'total': trade_data.get('total', 0),
            'timestamp': trade_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'strategy': trade_data.get('strategy', 'N/A'),
            'target_price': trade_data.get('target_price', 0),
            'stop_loss': trade_data.get('stop_loss', 0),
            'profit_rate': trade_data.get('profit_rate', 0),
            'profit_amount': trade_data.get('profit_amount', 0),
        }
        
        return self.templates.get_template(
            NotificationType.TRADE_EXECUTION,
            template_key,
            data
        )
    
    def build_profit_achievement_message(
        self, 
        achievement_type: str, 
        profit_data: Dict[str, Any]
    ) -> str:
        """수익률 달성 메시지 빌드"""
        data = {
            'daily_return': profit_data.get('daily_return', 0),
            'weekly_return': profit_data.get('weekly_return', 0),
            'total_return': profit_data.get('total_return', 0),
            'realized_pnl': profit_data.get('realized_pnl', 0),
            'win_rate': profit_data.get('win_rate', 0),
            'timestamp': profit_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'daily_trades': profit_data.get('daily_trades', 0),
            'weekly_trades': profit_data.get('weekly_trades', 0),
            'milestone': profit_data.get('milestone', 0),
            'current_return': profit_data.get('current_return', 0),
            'total_pnl': profit_data.get('total_pnl', 0),
            'roi': profit_data.get('roi', 0),
            'achievement_rate': profit_data.get('achievement_rate', 0),
        }
        
        return self.templates.get_template(
            NotificationType.PROFIT_ACHIEVEMENT,
            achievement_type,
            data
        )
    
    def build_loss_limit_message(
        self, 
        loss_type: str, 
        loss_data: Dict[str, Any]
    ) -> str:
        """손실 한계 메시지 빌드"""
        data = {
            'daily_loss': loss_data.get('daily_loss', 0),
            'position_loss': loss_data.get('position_loss', 0),
            'loss_amount': loss_data.get('loss_amount', 0),
            'timestamp': loss_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'daily_trades': loss_data.get('daily_trades', 0),
            'current_price': loss_data.get('current_price', 0),
            'stop_loss': loss_data.get('stop_loss', 0),
            'consecutive_loss': loss_data.get('consecutive_loss', 0),
            'total_loss': loss_data.get('total_loss', 0),
            'pause_duration': loss_data.get('pause_duration', 0),
        }
        
        return self.templates.get_template(
            NotificationType.LOSS_LIMIT,
            loss_type,
            data
        )
    
    def build_system_error_message(
        self, 
        error_type: str, 
        error_data: Dict[str, Any]
    ) -> str:
        """시스템 오류 메시지 빌드"""
        data = {
            'error_type': error_data.get('error_type', 'Unknown'),
            'impact_scope': error_data.get('impact_scope', 'Unknown'),
            'retry_count': error_data.get('retry_count', 0),
            'max_retries': error_data.get('max_retries', 3),
            'admin_notified': error_data.get('admin_notified', 'No'),
            'timestamp': error_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'estimated_recovery': error_data.get('estimated_recovery', 'Unknown'),
            'affected_trades': error_data.get('affected_trades', 0),
            'affected_amount': error_data.get('affected_amount', 0),
            'support_contacted': error_data.get('support_contacted', 'No'),
            'affected_data': error_data.get('affected_data', 'Unknown'),
            'backup_source': error_data.get('backup_source', 'None'),
            'status_update': error_data.get('status_update', 'Pending'),
        }
        
        return self.templates.get_template(
            NotificationType.SYSTEM_ERROR,
            error_type,
            data
        )
    
    def build_status_report_message(
        self, 
        report_type: str, 
        status_data: Dict[str, Any]
    ) -> str:
        """상태 보고 메시지 빌드"""
        data = {
            'date': status_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'day_of_week': status_data.get('day_of_week', ''),
            'start_date': status_data.get('start_date', ''),
            'end_date': status_data.get('end_date', ''),
            'month': status_data.get('month', datetime.now().month),
            'year': status_data.get('year', datetime.now().year),
            'daily_return': status_data.get('daily_return', 0),
            'weekly_return': status_data.get('weekly_return', 0),
            'monthly_return': status_data.get('monthly_return', 0),
            'trade_count': status_data.get('trade_count', 0),
            'total_trades': status_data.get('total_trades', 0),
            'success_rate': status_data.get('success_rate', 0),
            'avg_success_rate': status_data.get('avg_success_rate', 0),
            'uptime': status_data.get('uptime', 0),
            'avg_uptime': status_data.get('avg_uptime', 0),
            'notification_count': status_data.get('notification_count', 0),
            'active_positions': status_data.get('active_positions', 0),
            'max_return': status_data.get('max_return', 0),
            'max_loss': status_data.get('max_loss', 0),
            'goal_achievement': status_data.get('goal_achievement', 0),
            'sharpe_ratio': status_data.get('sharpe_ratio', 0),
            'max_drawdown': status_data.get('max_drawdown', 0),
        }
        
        return self.templates.get_template(
            NotificationType.STATUS_REPORT,
            report_type,
            data
        )
    
    def build_config_change_message(
        self, 
        config_type: str, 
        config_data: Dict[str, Any]
    ) -> str:
        """설정 변경 메시지 빌드"""
        data = {
            'old_value': config_data.get('old_value', 'N/A'),
            'new_value': config_data.get('new_value', 'N/A'),
            'old_stop_loss': config_data.get('old_stop_loss', 'N/A'),
            'new_stop_loss': config_data.get('new_stop_loss', 'N/A'),
            'old_take_profit': config_data.get('old_take_profit', 'N/A'),
            'new_take_profit': config_data.get('new_take_profit', 'N/A'),
            'old_daily_limit': config_data.get('old_daily_limit', 'N/A'),
            'new_daily_limit': config_data.get('new_daily_limit', 'N/A'),
            'timestamp': config_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'changed_by': config_data.get('changed_by', 'System'),
            'old_strategy': config_data.get('old_strategy', 'N/A'),
            'new_strategy': config_data.get('new_strategy', 'N/A'),
            'parameters': config_data.get('parameters', 'N/A'),
            'backtest_result': config_data.get('backtest_result', 'N/A'),
            'changed_settings': config_data.get('changed_settings', 'N/A'),
            'disabled_types': config_data.get('disabled_types', 'None'),
            'enabled_types': config_data.get('enabled_types', 'None'),
        }
        
        return self.templates.get_template(
            NotificationType.CONFIG_CHANGE,
            config_type,
            data
        )
    
    def build_risk_warning_message(
        self, 
        warning_type: str, 
        warning_data: Dict[str, Any]
    ) -> str:
        """리스크 경고 메시지 빌드"""
        data = {
            'volatility': warning_data.get('volatility', 0),
            'vs_average': warning_data.get('vs_average', 0),
            'risk_level': warning_data.get('risk_level', 'Unknown'),
            'recommendation': warning_data.get('recommendation', 'None'),
            'timestamp': warning_data.get('timestamp', datetime.now().strftime('%H:%M:%S')),
            'affected_coins': warning_data.get('affected_coins', 'None'),
            'liquidity_level': warning_data.get('liquidity_level', 'Unknown'),
            'affected_amount': warning_data.get('affected_amount', 0),
            'risk_description': warning_data.get('risk_description', 'Unknown'),
            'anomaly_type': warning_data.get('anomaly_type', 'Unknown'),
            'vs_normal': warning_data.get('vs_normal', 0),
            'affected_scope': warning_data.get('affected_scope', 'Unknown'),
        }
        
        return self.templates.get_template(
            NotificationType.RISK_WARNING,
            warning_type,
            data
        )
