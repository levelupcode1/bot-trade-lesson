#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 시스템 리스크 관리 모듈

사용자 유형별 맞춤형 리스크 관리:
- 초보자: 보수적인 설정 (낮은 손실 한도, 작은 포지션 크기)
- 중급자: 균형잡힌 설정
- 고급자: 공격적인 설정 (높은 손실 한도, 큰 포지션 크기)
"""

import logging
from datetime import datetime, date
from typing import Tuple, Optional, Dict, Any
from enum import Enum

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UserLevel(Enum):
    """사용자 유형"""
    BEGINNER = "초보자"
    INTERMEDIATE = "중급자"
    ADVANCED = "고급자"


class RiskManager:
    """
    자동매매 시스템 리스크 관리 클래스
    
    주요 기능:
    - 일일 손실 한도 관리
    - 포지션 크기 제한
    - 손절/익절 관리
    - 거래 중단 플래그 관리
    - 사용자 유형별 맞춤형 설정
    """
    
    # 사용자 유형별 기본 설정
    DEFAULT_SETTINGS = {
        UserLevel.BEGINNER: {
            'daily_loss_limit': 0.02,      # 2% (보수적)
            'max_position_size_ratio': 0.1,  # 10% (작은 포지션)
            'stop_loss_ratio': -0.01,        # -1% (빠른 손절)
            'take_profit_ratio': 0.03,      # 3% (빠른 익절)
        },
        UserLevel.INTERMEDIATE: {
            'daily_loss_limit': 0.05,       # 5% (균형)
            'max_position_size_ratio': 0.2,  # 20% (중간 포지션)
            'stop_loss_ratio': -0.02,        # -2% (표준 손절)
            'take_profit_ratio': 0.05,      # 5% (표준 익절)
        },
        UserLevel.ADVANCED: {
            'daily_loss_limit': 0.10,       # 10% (공격적)
            'max_position_size_ratio': 0.3,  # 30% (큰 포지션)
            'stop_loss_ratio': -0.03,        # -3% (느린 손절)
            'take_profit_ratio': 0.10,      # 10% (높은 익절)
        }
    }
    
    def __init__(
        self,
        daily_loss_limit: Optional[float] = None,
        max_position_size_ratio: Optional[float] = None,
        stop_loss_ratio: Optional[float] = None,
        take_profit_ratio: Optional[float] = None,
        user_level: UserLevel = UserLevel.INTERMEDIATE,
        initial_capital: float = 10000000.0
    ):
        """
        리스크 관리자 초기화
        
        Args:
            daily_loss_limit (Optional[float]): 일일 손실 한도 (비율, 예: 0.05 = 5%)
                None인 경우 사용자 유형별 기본값 사용
            max_position_size_ratio (Optional[float]): 최대 포지션 크기 비율 (예: 0.2 = 20%)
                None인 경우 사용자 유형별 기본값 사용
            stop_loss_ratio (Optional[float]): 손절 비율 (음수, 예: -0.02 = -2%)
                None인 경우 사용자 유형별 기본값 사용
            take_profit_ratio (Optional[float]): 익절 비율 (양수, 예: 0.05 = 5%)
                None인 경우 사용자 유형별 기본값 사용
            user_level (UserLevel): 사용자 유형 (기본값: 중급자)
            initial_capital (float): 초기 자본 (기본값: 10,000,000원)
        """
        self.user_level = user_level
        self.initial_capital = initial_capital
        
        # 사용자 유형별 기본 설정 가져오기
        default_settings = self.DEFAULT_SETTINGS[user_level]
        
        # 설정값 적용 (사용자 지정값이 있으면 우선 사용)
        self.daily_loss_limit = daily_loss_limit or default_settings['daily_loss_limit']
        self.max_position_size_ratio = max_position_size_ratio or default_settings['max_position_size_ratio']
        self.stop_loss_ratio = stop_loss_ratio or default_settings['stop_loss_ratio']
        self.take_profit_ratio = take_profit_ratio or default_settings['take_profit_ratio']
        
        # 상태 관리
        self.is_trading_allowed = True
        self.accumulated_loss = 0.0
        self.last_reset_date = date.today()
        
        # 알림 기록
        self.notifications = []
        
        # 입력값 검증
        self._validate_settings()
        
        logger.info(f"리스크 관리자 초기화 완료 ({user_level.value})")
        logger.info(f"  일일 손실 한도: {self.daily_loss_limit*100:.1f}%")
        logger.info(f"  최대 포지션 크기: {self.max_position_size_ratio*100:.1f}%")
        logger.info(f"  손절 비율: {self.stop_loss_ratio*100:.1f}%")
        logger.info(f"  익절 비율: {self.take_profit_ratio*100:.1f}%")
    
    def _validate_settings(self) -> None:
        """설정값 검증"""
        if not (0 < self.daily_loss_limit <= 1):
            raise ValueError(f"일일 손실 한도({self.daily_loss_limit})는 0과 1 사이여야 합니다.")
        
        if not (0 < self.max_position_size_ratio <= 1):
            raise ValueError(f"최대 포지션 크기 비율({self.max_position_size_ratio})은 0과 1 사이여야 합니다.")
        
        if not (-1 <= self.stop_loss_ratio < 0):
            raise ValueError(f"손절 비율({self.stop_loss_ratio})은 -1과 0 사이여야 합니다.")
        
        if not (0 < self.take_profit_ratio <= 1):
            raise ValueError(f"익절 비율({self.take_profit_ratio})은 0과 1 사이여야 합니다.")
        
        if self.initial_capital <= 0:
            raise ValueError(f"초기 자본({self.initial_capital})은 0보다 커야 합니다.")
    
    def _reset_daily_loss(self) -> None:
        """일일 손실 초기화 (날짜 변경 시)"""
        today = date.today()
        if today != self.last_reset_date:
            old_loss = self.accumulated_loss
            self.accumulated_loss = 0.0
            self.last_reset_date = today
            logger.info(f"일일 손실 초기화: {old_loss:,.0f}원 -> 0원")
    
    def check_daily_loss(self, accumulated_loss: float) -> bool:
        """
        일일 누적 손실 확인
        
        Args:
            accumulated_loss (float): 누적 손실 금액
        
        Returns:
            bool: 거래 허용 여부
                - True: 일일 손실 한도 내 (거래 가능)
                - False: 일일 손실 한도 초과 (거래 불가)
        """
        # 날짜 변경 확인 및 초기화
        self._reset_daily_loss()
        
        # 누적 손실 업데이트
        self.accumulated_loss = accumulated_loss
        
        # 일일 손실 한도 계산
        max_daily_loss = self.initial_capital * self.daily_loss_limit
        
        # 손실 한도 확인
        if accumulated_loss >= max_daily_loss:
            self.is_trading_allowed = False
            message = (
                f"⚠️ 일일 손실 한도 초과! "
                f"누적 손실: {accumulated_loss:,.0f}원, "
                f"한도: {max_daily_loss:,.0f}원 ({self.daily_loss_limit*100:.1f}%)"
            )
            logger.warning(message)
            self._add_notification("일일 손실 한도 초과", message)
            return False
        
        # 손실 한도 근접 경고 (80% 이상)
        warning_threshold = max_daily_loss * 0.8
        if accumulated_loss >= warning_threshold:
            message = (
                f"⚠️ 일일 손실 한도 근접! "
                f"누적 손실: {accumulated_loss:,.0f}원, "
                f"한도: {max_daily_loss:,.0f}원"
            )
            logger.warning(message)
            self._add_notification("일일 손실 한도 근접", message)
        
        logger.debug(
            f"일일 손실 확인: {accumulated_loss:,.0f}원 / "
            f"{max_daily_loss:,.0f}원 ({self.daily_loss_limit*100:.1f}%)"
        )
        
        return True
    
    def check_position_size(
        self,
        position_size: float,
        total_asset: float
    ) -> bool:
        """
        포지션 크기 확인
        
        Args:
            position_size (float): 신규 포지션 크기 (금액)
            total_asset (float): 총 자산
        
        Returns:
            bool: 거래 허용 여부
                - True: 포지션 크기 한도 내 (거래 가능)
                - False: 포지션 크기 한도 초과 (거래 불가)
        """
        if position_size <= 0:
            logger.warning(f"포지션 크기가 0 이하입니다: {position_size}")
            return False
        
        if total_asset <= 0:
            logger.warning(f"총 자산이 0 이하입니다: {total_asset}")
            return False
        
        # 최대 포지션 크기 계산
        max_position_size = total_asset * self.max_position_size_ratio
        
        # 포지션 크기 확인
        if position_size > max_position_size:
            self.is_trading_allowed = False
            message = (
                f"⚠️ 포지션 크기 한도 초과! "
                f"신규 포지션: {position_size:,.0f}원, "
                f"한도: {max_position_size:,.0f}원 ({self.max_position_size_ratio*100:.1f}%)"
            )
            logger.warning(message)
            self._add_notification("포지션 크기 한도 초과", message)
            return False
        
        logger.debug(
            f"포지션 크기 확인: {position_size:,.0f}원 / "
            f"{max_position_size:,.0f}원 ({self.max_position_size_ratio*100:.1f}%)"
        )
        
        return True
    
    def check_stop_loss_take_profit(
        self,
        entry_price: float,
        current_price: float
    ) -> Tuple[bool, str]:
        """
        손절/익절 확인
        
        Args:
            entry_price (float): 진입 가격
            current_price (float): 현재 가격
        
        Returns:
            Tuple[bool, str]: (조건 달성 여부, 조건 타입)
                - (True, 'stop_loss'): 손절 조건 달성
                - (True, 'take_profit'): 익절 조건 달성
                - (False, ''): 조건 미달성
        """
        if entry_price <= 0:
            logger.error(f"진입 가격이 0 이하입니다: {entry_price}")
            return (False, '')
        
        if current_price <= 0:
            logger.error(f"현재 가격이 0 이하입니다: {current_price}")
            return (False, '')
        
        # 수익률 계산
        return_rate = (current_price - entry_price) / entry_price
        
        # 손절 확인
        if return_rate <= self.stop_loss_ratio:
            message = (
                f"🛑 손절 조건 달성! "
                f"진입가: {entry_price:,.0f}원, "
                f"현재가: {current_price:,.0f}원, "
                f"수익률: {return_rate*100:.2f}% (손절: {self.stop_loss_ratio*100:.1f}%)"
            )
            logger.warning(message)
            self._add_notification("손절 조건 달성", message)
            return (True, 'stop_loss')
        
        # 익절 확인
        if return_rate >= self.take_profit_ratio:
            message = (
                f"✅ 익절 조건 달성! "
                f"진입가: {entry_price:,.0f}원, "
                f"현재가: {current_price:,.0f}원, "
                f"수익률: {return_rate*100:.2f}% (익절: {self.take_profit_ratio*100:.1f}%)"
            )
            logger.info(message)
            self._add_notification("익절 조건 달성", message)
            return (True, 'take_profit')
        
        logger.debug(
            f"손절/익절 확인: 수익률 {return_rate*100:.2f}% "
            f"(손절: {self.stop_loss_ratio*100:.1f}%, 익절: {self.take_profit_ratio*100:.1f}%)"
        )
        
        return (False, '')
    
    def _add_notification(self, title: str, message: str) -> None:
        """알림 추가"""
        notification = {
            'timestamp': datetime.now(),
            'title': title,
            'message': message
        }
        self.notifications.append(notification)
        
        # 알림 개수 제한 (최근 100개만 유지)
        if len(self.notifications) > 100:
            self.notifications = self.notifications[-100:]
    
    def get_notifications(self, limit: int = 10) -> list:
        """
        최근 알림 조회
        
        Args:
            limit (int): 조회할 알림 개수 (기본값: 10)
        
        Returns:
            list: 알림 리스트
        """
        return self.notifications[-limit:]
    
    def reset_trading_flag(self) -> None:
        """거래 중단 플래그 초기화 (수동 재개)"""
        if not self.is_trading_allowed:
            logger.info("거래 중단 플래그 초기화 - 거래 재개")
            self.is_trading_allowed = True
            self._add_notification("거래 재개", "거래가 재개되었습니다.")
    
    def emergency_stop(self) -> None:
        """긴급 정지"""
        self.is_trading_allowed = False
        message = "🚨 긴급 정지! 모든 거래가 중단되었습니다."
        logger.critical(message)
        self._add_notification("긴급 정지", message)
    
    def get_status(self) -> Dict[str, Any]:
        """
        현재 상태 조회
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        max_daily_loss = self.initial_capital * self.daily_loss_limit
        
        return {
            'user_level': self.user_level.value,
            'is_trading_allowed': self.is_trading_allowed,
            'accumulated_loss': self.accumulated_loss,
            'max_daily_loss': max_daily_loss,
            'daily_loss_ratio': (self.accumulated_loss / max_daily_loss * 100) if max_daily_loss > 0 else 0,
            'settings': {
                'daily_loss_limit': self.daily_loss_limit,
                'max_position_size_ratio': self.max_position_size_ratio,
                'stop_loss_ratio': self.stop_loss_ratio,
                'take_profit_ratio': self.take_profit_ratio,
            },
            'notification_count': len(self.notifications)
        }


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("자동매매 시스템 리스크 관리 클래스 테스트")
    print("=" * 60)
    
    # 테스트 1: 초보자 설정
    print("\n[테스트 1] 초보자 설정")
    print("-" * 60)
    try:
        risk_manager = RiskManager(
            user_level=UserLevel.BEGINNER,
            initial_capital=10000000.0
        )
        
        status = risk_manager.get_status()
        print(f"사용자 유형: {status['user_level']}")
        print(f"일일 손실 한도: {status['settings']['daily_loss_limit']*100:.1f}%")
        print(f"최대 포지션 크기: {status['settings']['max_position_size_ratio']*100:.1f}%")
        print(f"손절 비율: {status['settings']['stop_loss_ratio']*100:.1f}%")
        print(f"익절 비율: {status['settings']['take_profit_ratio']*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 2: 일일 손실 확인
    print("\n[테스트 2] 일일 손실 확인")
    print("-" * 60)
    try:
        risk_manager = RiskManager(
            user_level=UserLevel.INTERMEDIATE,
            initial_capital=10000000.0
        )
        
        # 정상 케이스
        result1 = risk_manager.check_daily_loss(accumulated_loss=100000.0)
        print(f"누적 손실 10만원: {'통과' if result1 else '실패'}")
        
        # 한도 초과 케이스
        result2 = risk_manager.check_daily_loss(accumulated_loss=600000.0)
        print(f"누적 손실 60만원 (한도 초과): {'통과' if result2 else '실패'}")
        print(f"거래 허용 여부: {risk_manager.is_trading_allowed}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 3: 포지션 크기 확인
    print("\n[테스트 3] 포지션 크기 확인")
    print("-" * 60)
    try:
        risk_manager = RiskManager(
            user_level=UserLevel.INTERMEDIATE,
            initial_capital=10000000.0
        )
        
        total_asset = 10000000.0
        
        # 정상 케이스
        result1 = risk_manager.check_position_size(
            position_size=1500000.0,
            total_asset=total_asset
        )
        print(f"포지션 크기 150만원 (한도 내): {'통과' if result1 else '실패'}")
        
        # 한도 초과 케이스
        result2 = risk_manager.check_position_size(
            position_size=2500000.0,
            total_asset=total_asset
        )
        print(f"포지션 크기 250만원 (한도 초과): {'통과' if result2 else '실패'}")
        print(f"거래 허용 여부: {risk_manager.is_trading_allowed}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 4: 손절/익절 확인
    print("\n[테스트 4] 손절/익절 확인")
    print("-" * 60)
    try:
        risk_manager = RiskManager(
            user_level=UserLevel.INTERMEDIATE,
            initial_capital=10000000.0
        )
        
        entry_price = 1000000.0
        
        # 손절 케이스
        result1, condition1 = risk_manager.check_stop_loss_take_profit(
            entry_price=entry_price,
            current_price=980000.0  # -2%
        )
        print(f"손절 조건: {'달성' if result1 else '미달성'} ({condition1})")
        
        # 익절 케이스
        result2, condition2 = risk_manager.check_stop_loss_take_profit(
            entry_price=entry_price,
            current_price=1050000.0  # +5%
        )
        print(f"익절 조건: {'달성' if result2 else '미달성'} ({condition2})")
        
        # 조건 미달성 케이스
        result3, condition3 = risk_manager.check_stop_loss_take_profit(
            entry_price=entry_price,
            current_price=1020000.0  # +2%
        )
        print(f"조건 미달성: {'달성' if result3 else '미달성'} ({condition3})")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 5: 사용자 유형별 설정 비교
    print("\n[테스트 5] 사용자 유형별 설정 비교")
    print("-" * 60)
    for level in UserLevel:
        risk_manager = RiskManager(
            user_level=level,
            initial_capital=10000000.0
        )
        status = risk_manager.get_status()
        print(f"\n{level.value}:")
        print(f"  일일 손실 한도: {status['settings']['daily_loss_limit']*100:.1f}%")
        print(f"  최대 포지션 크기: {status['settings']['max_position_size_ratio']*100:.1f}%")
        print(f"  손절 비율: {status['settings']['stop_loss_ratio']*100:.1f}%")
        print(f"  익절 비율: {status['settings']['take_profit_ratio']*100:.1f}%")
    
    # 테스트 6: 알림 기능
    print("\n[테스트 6] 알림 기능")
    print("-" * 60)
    try:
        risk_manager = RiskManager(
            user_level=UserLevel.INTERMEDIATE,
            initial_capital=10000000.0
        )
        
        # 여러 알림 발생
        risk_manager.check_daily_loss(600000.0)  # 한도 초과
        risk_manager.check_position_size(2500000.0, 10000000.0)  # 포지션 크기 초과
        
        # 알림 조회
        notifications = risk_manager.get_notifications(limit=5)
        print(f"최근 알림 {len(notifications)}개:")
        for notif in notifications:
            print(f"  [{notif['timestamp'].strftime('%H:%M:%S')}] {notif['title']}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
