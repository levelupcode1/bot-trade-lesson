#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 관련 핸들러
거래 내역, 수익률, 시스템 제어 등
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# 모의 데이터 생성 함수들
class MockTradingData:
    """모의 거래 데이터 생성 클래스"""
    
    @staticmethod
    def get_recent_trades(limit: int = 5) -> List[Dict[str, Any]]:
        """최근 거래 내역 생성 (모의 데이터)"""
        trades = []
        base_price = 50000000  # 5천만원
        
        for i in range(limit):
            is_buy = random.choice([True, False])
            price = base_price + random.randint(-1000000, 1000000)
            amount = round(random.uniform(0.001, 0.01), 4)
            
            trade = {
                'id': f'T{1000 + i}',
                'type': 'BUY' if is_buy else 'SELL',
                'symbol': 'KRW-BTC',
                'price': price,
                'amount': amount,
                'total': price * amount,
                'timestamp': datetime.now() - timedelta(hours=i*2),
                'status': 'completed'
            }
            trades.append(trade)
        
        return trades
    
    @staticmethod
    def get_profit_data() -> Dict[str, Any]:
        """수익률 데이터 생성 (모의 데이터)"""
        return {
            'total_invested': 10000000,  # 1천만원
            'current_value': 10850000,   # 1085만원
            'realized_profit': 850000,    # 85만원
            'unrealized_profit': 250000,  # 25만원
            'total_profit': 1100000,      # 110만원
            'profit_rate': 11.0,          # 11%
            'win_rate': 65.5,             # 승률 65.5%
            'total_trades': 42,
            'winning_trades': 27,
            'losing_trades': 15,
            'period': '30일'
        }
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """시스템 상태 데이터 생성"""
        return {
            'trading_active': random.choice([True, False]),
            'strategy': 'Volatility Breakout v2',
            'running_time': '2일 14시간 32분',
            'api_status': 'connected',
            'last_update': datetime.now(),
            'active_positions': 3,
            'pending_orders': 1,
            'daily_trades': 8,
            'error_count': 0
        }
    
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """현재 설정 데이터"""
        return {
            'auto_trading': True,
            'max_position_size': 0.1,  # 10%
            'stop_loss': -0.02,        # -2%
            'take_profit': 0.05,       # 5%
            'daily_loss_limit': -0.05, # -5%
            'notification_enabled': True,
            'trade_alerts': True,
            'profit_alerts': True,
            'risk_alerts': True
        }


async def trades_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """거래 내역 조회 명령어 핸들러"""
    
    # 모의 거래 데이터 가져오기
    trades = MockTradingData.get_recent_trades(5)
    
    # 메시지 구성
    message = "📊 *최근 거래 내역*\n"
    message += "=" * 30 + "\n\n"
    
    for trade in trades:
        emoji = "🟢" if trade['type'] == 'BUY' else "🔴"
        message += f"{emoji} *{trade['type']}* #{trade['id']}\n"
        message += f"   💰 가격: {trade['price']:,}원\n"
        message += f"   📦 수량: {trade['amount']} BTC\n"
        message += f"   💵 총액: {int(trade['total']):,}원\n"
        message += f"   ⏰ 시간: {trade['timestamp'].strftime('%m-%d %H:%M')}\n"
        message += f"   ✅ 상태: {trade['status']}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📈 총 {len(trades)}개 거래 표시"
    
    # 인라인 키보드
    keyboard = [
        [
            InlineKeyboardButton("🔄 새로고침", callback_data="refresh_trades"),
            InlineKeyboardButton("📊 더보기", callback_data="more_trades")
        ],
        [
            InlineKeyboardButton("💰 수익률", callback_data="show_profit"),
            InlineKeyboardButton("🏠 메인", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """수익률 확인 명령어 핸들러"""
    
    # 수익률 데이터 가져오기
    profit_data = MockTradingData.get_profit_data()
    
    # 수익률에 따른 이모지
    profit_emoji = "📈" if profit_data['profit_rate'] > 0 else "📉"
    profit_color = "🟢" if profit_data['profit_rate'] > 0 else "🔴"
    
    message = f"{profit_emoji} *수익률 분석 ({profit_data['period']})*\n"
    message += "=" * 30 + "\n\n"
    
    message += f"💼 *투자 현황*\n"
    message += f"   • 투자금: {profit_data['total_invested']:,}원\n"
    message += f"   • 평가액: {profit_data['current_value']:,}원\n"
    message += f"   • 실현손익: {profit_data['realized_profit']:,}원\n"
    message += f"   • 미실현손익: {profit_data['unrealized_profit']:,}원\n\n"
    
    message += f"{profit_color} *총 수익*\n"
    message += f"   • 금액: {profit_data['total_profit']:,}원\n"
    message += f"   • 수익률: {profit_data['profit_rate']:+.1f}%\n\n"
    
    message += f"📊 *거래 통계*\n"
    message += f"   • 총 거래: {profit_data['total_trades']}회\n"
    message += f"   • 성공: {profit_data['winning_trades']}회 ✅\n"
    message += f"   • 실패: {profit_data['losing_trades']}회 ❌\n"
    message += f"   • 승률: {profit_data['win_rate']:.1f}%\n\n"
    
    # 수익률 그래프 (텍스트 기반)
    bars = int(profit_data['profit_rate'] / 2)
    if bars > 0:
        message += f"📊 {profit_color * bars}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 *Tip:* 안정적인 수익을 위해 리스크 관리가 중요합니다!"
    
    # 인라인 키보드
    keyboard = [
        [
            InlineKeyboardButton("📊 거래내역", callback_data="show_trades"),
            InlineKeyboardButton("📈 상세분석", callback_data="detailed_analysis")
        ],
        [
            InlineKeyboardButton("⚙️ 설정", callback_data="show_settings"),
            InlineKeyboardButton("🏠 메인", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """시스템 상태 확인 명령어 핸들러"""
    
    # 시스템 상태 데이터
    status = MockTradingData.get_system_status()
    
    # 상태에 따른 이모지
    trading_status = "🟢 활성" if status['trading_active'] else "🔴 정지"
    api_status = "🟢 연결됨" if status['api_status'] == 'connected' else "🔴 끊김"
    
    message = "🖥️ *시스템 상태*\n"
    message += "=" * 30 + "\n\n"
    
    message += f"⚡ *거래 시스템*\n"
    message += f"   • 상태: {trading_status}\n"
    message += f"   • 전략: {status['strategy']}\n"
    message += f"   • 가동시간: {status['running_time']}\n\n"
    
    message += f"🔌 *연결 상태*\n"
    message += f"   • API: {api_status}\n"
    message += f"   • 마지막 업데이트: {status['last_update'].strftime('%H:%M:%S')}\n\n"
    
    message += f"📊 *현재 활동*\n"
    message += f"   • 활성 포지션: {status['active_positions']}개\n"
    message += f"   • 대기 주문: {status['pending_orders']}개\n"
    message += f"   • 금일 거래: {status['daily_trades']}회\n"
    message += f"   • 오류 횟수: {status['error_count']}회\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if status['trading_active']:
        message += "✅ 시스템이 정상적으로 작동 중입니다."
    else:
        message += "⚠️ 거래가 중지되어 있습니다. /start_trading 으로 시작하세요."
    
    # 인라인 키보드
    keyboard = []
    if status['trading_active']:
        keyboard.append([
            InlineKeyboardButton("⏸️ 거래중지", callback_data="stop_trading"),
            InlineKeyboardButton("🔄 새로고침", callback_data="refresh_status")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("▶️ 거래시작", callback_data="start_trading"),
            InlineKeyboardButton("🔄 새로고침", callback_data="refresh_status")
        ])
    
    keyboard.append([
        InlineKeyboardButton("⚙️ 설정", callback_data="show_settings"),
        InlineKeyboardButton("🏠 메인", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """설정 변경 명령어 핸들러"""
    
    settings = MockTradingData.get_settings()
    
    message = "⚙️ *시스템 설정*\n"
    message += "=" * 30 + "\n\n"
    
    message += f"🤖 *자동매매*\n"
    auto_status = "✅ 활성화" if settings['auto_trading'] else "❌ 비활성화"
    message += f"   • 상태: {auto_status}\n\n"
    
    message += f"💰 *리스크 관리*\n"
    message += f"   • 최대 포지션: {settings['max_position_size']*100:.0f}%\n"
    message += f"   • 손절: {settings['stop_loss']*100:+.0f}%\n"
    message += f"   • 익절: {settings['take_profit']*100:+.0f}%\n"
    message += f"   • 일일손실한도: {settings['daily_loss_limit']*100:+.0f}%\n\n"
    
    message += f"🔔 *알림 설정*\n"
    noti_status = "✅" if settings['notification_enabled'] else "❌"
    trade_status = "✅" if settings['trade_alerts'] else "❌"
    profit_status = "✅" if settings['profit_alerts'] else "❌"
    risk_status = "✅" if settings['risk_alerts'] else "❌"
    
    message += f"   • 전체 알림: {noti_status}\n"
    message += f"   • 거래 알림: {trade_status}\n"
    message += f"   • 수익 알림: {profit_status}\n"
    message += f"   • 리스크 경고: {risk_status}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 설정을 변경하려면 아래 버튼을 사용하세요."
    
    # 인라인 키보드
    keyboard = [
        [
            InlineKeyboardButton("🎯 전략설정", callback_data="config_strategy"),
            InlineKeyboardButton("⚠️ 리스크", callback_data="config_risk")
        ],
        [
            InlineKeyboardButton("🔔 알림", callback_data="config_notifications"),
            InlineKeyboardButton("🔐 보안", callback_data="config_security")
        ],
        [
            InlineKeyboardButton("💾 저장", callback_data="save_settings"),
            InlineKeyboardButton("🏠 메인", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def stop_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """거래 중지 명령어 핸들러"""
    
    message = "⏸️ *거래 중지*\n"
    message += "=" * 30 + "\n\n"
    message += "거래를 중지하시겠습니까?\n\n"
    message += "⚠️ *주의사항:*\n"
    message += "• 진행 중인 주문은 완료됩니다\n"
    message += "• 새로운 거래는 실행되지 않습니다\n"
    message += "• 활성 포지션은 유지됩니다\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 확인 버튼을 눌러 거래를 중지하세요."
    
    keyboard = [
        [
            InlineKeyboardButton("✅ 확인 - 중지", callback_data="confirm_stop_trading"),
            InlineKeyboardButton("❌ 취소", callback_data="cancel_action")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def start_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """거래 시작 명령어 핸들러"""
    
    message = "▶️ *거래 시작*\n"
    message += "=" * 30 + "\n\n"
    message += "자동매매를 시작하시겠습니까?\n\n"
    message += "📋 *시작 전 확인사항:*\n"
    message += "• API 연결 상태 확인 ✅\n"
    message += "• 계좌 잔액 충분 ✅\n"
    message += "• 전략 설정 완료 ✅\n"
    message += "• 리스크 관리 설정 완료 ✅\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 확인 버튼을 눌러 거래를 시작하세요."
    
    keyboard = [
        [
            InlineKeyboardButton("✅ 확인 - 시작", callback_data="confirm_start_trading"),
            InlineKeyboardButton("❌ 취소", callback_data="cancel_action")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_trading_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """거래 관련 콜백 쿼리 핸들러"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "refresh_trades":
        # 거래 내역 새로고침
        trades = MockTradingData.get_recent_trades(5)
        message = "🔄 *거래 내역 새로고침*\n\n"
        message += f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        for trade in trades[:3]:
            emoji = "🟢" if trade['type'] == 'BUY' else "🔴"
            message += f"{emoji} {trade['type']} {trade['amount']} BTC @ {trade['price']:,}원\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif callback_data == "confirm_stop_trading":
        # 거래 중지 확인
        message = "⏸️ *거래 중지 완료*\n\n"
        message += "✅ 자동매매가 중지되었습니다.\n\n"
        message += f"중지 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "💡 /start_trading 명령어로 다시 시작할 수 있습니다."
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif callback_data == "confirm_start_trading":
        # 거래 시작 확인
        message = "▶️ *거래 시작 완료*\n\n"
        message += "✅ 자동매매가 시작되었습니다.\n\n"
        message += f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"전략: Volatility Breakout v2\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "💡 /status 명령어로 상태를 확인할 수 있습니다."
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif callback_data == "cancel_action":
        await query.edit_message_text("❌ 작업이 취소되었습니다.")
    
    elif callback_data == "main_menu":
        # 메인 메뉴로 이동
        keyboard = [
            [
                InlineKeyboardButton("📊 거래내역", callback_data="show_trades"),
                InlineKeyboardButton("💰 수익률", callback_data="show_profit")
            ],
            [
                InlineKeyboardButton("🖥️ 상태", callback_data="show_status"),
                InlineKeyboardButton("⚙️ 설정", callback_data="show_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 *메인 메뉴*\n\n원하는 기능을 선택하세요:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    else:
        await query.edit_message_text(f"⚠️ 이 기능은 준비 중입니다: {callback_data}")
