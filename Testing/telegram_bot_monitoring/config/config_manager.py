#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 모듈
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """설정 관리자"""
    
    def __init__(self):
        """설정 초기화"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.trading_system_status = False  # 거래 시스템 상태
        self.initial_capital = float(os.getenv('INITIAL_CAPITAL', '10000000.0'))
        self.current_capital = self.initial_capital
        self.total_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # 설정 검증
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
    
    def get_bot_token(self) -> Optional[str]:
        """봇 토큰 조회"""
        return self.bot_token
    
    def is_trading_active(self) -> bool:
        """거래 시스템 활성화 여부"""
        return self.trading_system_status
    
    def start_trading(self) -> bool:
        """거래 시스템 시작"""
        if self.trading_system_status:
            logger.warning("거래 시스템이 이미 실행 중입니다.")
            return False
        
        self.trading_system_status = True
        logger.info("거래 시스템이 시작되었습니다.")
        return True
    
    def stop_trading(self) -> bool:
        """거래 시스템 중지"""
        if not self.trading_system_status:
            logger.warning("거래 시스템이 이미 중지되어 있습니다.")
            return False
        
        self.trading_system_status = False
        logger.info("거래 시스템이 중지되었습니다.")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'trading_status': 'running' if self.trading_system_status else 'stopped',
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_profit': self.total_profit,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        }
    
    def get_profit_info(self) -> Dict[str, Any]:
        """수익 정보 조회"""
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0.0
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_profit': self.total_profit,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.total_trades - self.winning_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        }
