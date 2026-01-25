#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 필터링 함수 모듈

가짜 돌파를 줄이기 위한 필터링 기법:
1. 변동성 필터: 충분한 변동성이 있는 날만 거래
2. 시간대 필터: 유동성이 높은 시간대에만 거래
3. 확인 캔들 필터: 돌파 후 다음 캔들에서도 돌파선 위 유지 확인
"""

import logging
from typing import Tuple

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def volatility_filter(
    current_volatility: float,
    avg_volatility: float
) -> bool:
    """
    변동성 필터 함수
    
    전일 변동폭이 최근 N일 평균 변동폭보다 큰지 확인합니다.
    충분한 변동성이 있는 날에만 거래하여 가짜 돌파를 줄입니다.
    
    Args:
        current_volatility (float): 전일 변동폭 (고가 - 저가)
        avg_volatility (float): 최근 N일 평균 변동폭
    
    Returns:
        bool: 필터 통과 여부
            - True: 전일 변동폭이 평균보다 큼 (거래 가능)
            - False: 전일 변동폭이 평균보다 작거나 같음 (거래 불가)
    
    Raises:
        ValueError: 입력값이 유효하지 않을 경우
    
    Examples:
        >>> # 전일 변동폭이 평균보다 큰 경우
        >>> result = volatility_filter(1000.0, 800.0)
        >>> print(result)  # True
        
        >>> # 전일 변동폭이 평균보다 작은 경우
        >>> result = volatility_filter(600.0, 800.0)
        >>> print(result)  # False
    """
    # 입력값 검증
    if current_volatility < 0:
        error_msg = f"전일 변동폭({current_volatility})은 0 이상이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if avg_volatility < 0:
        error_msg = f"평균 변동폭({avg_volatility})은 0 이상이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if avg_volatility == 0:
        logger.warning("평균 변동폭이 0입니다. 필터를 통과하지 않습니다.")
        return False
    
    # 변동성 필터: 전일 변동폭 > 평균 변동폭
    filter_passed = current_volatility > avg_volatility
    
    if filter_passed:
        logger.debug(
            f"변동성 필터 통과: 전일 변동폭({current_volatility:.2f}) > "
            f"평균 변동폭({avg_volatility:.2f})"
        )
    else:
        logger.debug(
            f"변동성 필터 실패: 전일 변동폭({current_volatility:.2f}) <= "
            f"평균 변동폭({avg_volatility:.2f})"
        )
    
    return filter_passed


def time_filter(
    current_hour: int,
    start_hour: int = 9,
    end_hour: int = 18
) -> bool:
    """
    시간대 필터 함수
    
    현재 시간이 지정된 시간대(기본값: 9시~18시) 내인지 확인합니다.
    유동성이 높은 시간대에만 거래하여 거래 품질을 향상시킵니다.
    
    Args:
        current_hour (int): 현재 시간 (0~23)
        start_hour (int): 거래 시작 시간 (기본값: 9)
        end_hour (int): 거래 종료 시간 (기본값: 18)
    
    Returns:
        bool: 필터 통과 여부
            - True: 현재 시간이 지정된 시간대 내 (거래 가능)
            - False: 현재 시간이 지정된 시간대 밖 (거래 불가)
    
    Raises:
        ValueError: 입력값이 유효하지 않을 경우
    
    Examples:
        >>> # 거래 가능 시간대 (9시~18시)
        >>> result = time_filter(12, 9, 18)
        >>> print(result)  # True
        
        >>> # 거래 불가 시간대 (밤)
        >>> result = time_filter(22, 9, 18)
        >>> print(result)  # False
    """
    # 입력값 검증
    if not (0 <= current_hour <= 23):
        error_msg = f"현재 시간({current_hour})은 0~23 사이의 값이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not (0 <= start_hour <= 23):
        error_msg = f"시작 시간({start_hour})은 0~23 사이의 값이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not (0 <= end_hour <= 23):
        error_msg = f"종료 시간({end_hour})은 0~23 사이의 값이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if start_hour > end_hour:
        error_msg = f"시작 시간({start_hour})은 종료 시간({end_hour})보다 작거나 같아야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 시간대 필터: start_hour <= current_hour < end_hour
    filter_passed = start_hour <= current_hour < end_hour
    
    if filter_passed:
        logger.debug(
            f"시간대 필터 통과: 현재 시간({current_hour}시)이 "
            f"거래 시간대({start_hour}시~{end_hour}시) 내"
        )
    else:
        logger.debug(
            f"시간대 필터 실패: 현재 시간({current_hour}시)이 "
            f"거래 시간대({start_hour}시~{end_hour}시) 밖"
        )
    
    return filter_passed


def confirmation_candle_filter(
    current_price: float,
    breakout_price: float,
    prev_price: float
) -> bool:
    """
    확인 캔들 필터 함수
    
    돌파 후 다음 캔들에서도 돌파선 위에 유지되는지 확인합니다.
    가짜 돌파를 걸러내고 진짜 돌파만 거래합니다.
    
    필터 조건:
    1. 현재가가 돌파선 위에 있어야 함 (current_price > breakout_price)
    2. 이전 캔들도 돌파선 위에 있었어야 함 (prev_price > breakout_price)
    
    Args:
        current_price (float): 현재 캔들의 가격 (종가)
        breakout_price (float): 돌파선 가격
        prev_price (float): 이전 캔들의 가격 (종가)
    
    Returns:
        bool: 필터 통과 여부
            - True: 현재가와 이전가 모두 돌파선 위 (거래 가능)
            - False: 현재가 또는 이전가가 돌파선 아래 (거래 불가)
    
    Raises:
        ValueError: 입력값이 유효하지 않을 경우
    
    Examples:
        >>> # 확인 캔들 필터 통과 (연속 2개 캔들이 돌파선 위)
        >>> result = confirmation_candle_filter(105.0, 100.0, 102.0)
        >>> print(result)  # True
        
        >>> # 확인 캔들 필터 실패 (이전 캔들이 돌파선 아래)
        >>> result = confirmation_candle_filter(105.0, 100.0, 98.0)
        >>> print(result)  # False
    """
    # 입력값 검증
    if current_price <= 0:
        error_msg = f"현재가({current_price})는 0보다 커야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if breakout_price <= 0:
        error_msg = f"돌파선 가격({breakout_price})은 0보다 커야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if prev_price <= 0:
        error_msg = f"이전 가격({prev_price})은 0보다 커야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 확인 캔들 필터 조건
    # 1. 현재가가 돌파선 위에 있어야 함
    current_above_breakout = current_price > breakout_price
    
    # 2. 이전 캔들도 돌파선 위에 있었어야 함
    prev_above_breakout = prev_price > breakout_price
    
    # 두 조건 모두 만족해야 필터 통과
    filter_passed = current_above_breakout and prev_above_breakout
    
    if filter_passed:
        logger.debug(
            f"확인 캔들 필터 통과: 현재가({current_price:.2f}) > 돌파선({breakout_price:.2f}) "
            f"AND 이전가({prev_price:.2f}) > 돌파선({breakout_price:.2f})"
        )
    else:
        if not current_above_breakout:
            logger.debug(
                f"확인 캔들 필터 실패: 현재가({current_price:.2f}) <= 돌파선({breakout_price:.2f})"
            )
        if not prev_above_breakout:
            logger.debug(
                f"확인 캔들 필터 실패: 이전가({prev_price:.2f}) <= 돌파선({breakout_price:.2f})"
            )
    
    return filter_passed


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("변동성 돌파 전략 필터링 함수 테스트")
    print("=" * 60)
    
    # 테스트 1: 변동성 필터
    print("\n[테스트 1] 변동성 필터")
    print("-" * 60)
    try:
        # 케이스 1: 필터 통과 (전일 변동폭이 평균보다 큼)
        result1 = volatility_filter(current_volatility=1000.0, avg_volatility=800.0)
        print(f"케이스 1 - 전일 변동폭(1000) > 평균 변동폭(800): {result1}")
        
        # 케이스 2: 필터 실패 (전일 변동폭이 평균보다 작음)
        result2 = volatility_filter(current_volatility=600.0, avg_volatility=800.0)
        print(f"케이스 2 - 전일 변동폭(600) < 평균 변동폭(800): {result2}")
        
        # 케이스 3: 필터 실패 (전일 변동폭이 평균과 같음)
        result3 = volatility_filter(current_volatility=800.0, avg_volatility=800.0)
        print(f"케이스 3 - 전일 변동폭(800) == 평균 변동폭(800): {result3}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 2: 시간대 필터
    print("\n[테스트 2] 시간대 필터")
    print("-" * 60)
    try:
        # 케이스 1: 필터 통과 (거래 시간대 내)
        result1 = time_filter(current_hour=12, start_hour=9, end_hour=18)
        print(f"케이스 1 - 현재 시간(12시)이 거래 시간대(9시~18시) 내: {result1}")
        
        # 케이스 2: 필터 실패 (거래 시간대 밖)
        result2 = time_filter(current_hour=22, start_hour=9, end_hour=18)
        print(f"케이스 2 - 현재 시간(22시)이 거래 시간대(9시~18시) 밖: {result2}")
        
        # 케이스 3: 필터 실패 (거래 시작 시간 이전)
        result3 = time_filter(current_hour=8, start_hour=9, end_hour=18)
        print(f"케이스 3 - 현재 시간(8시)이 거래 시작 시간(9시) 이전: {result3}")
        
        # 케이스 4: 필터 실패 (거래 종료 시간 이후)
        result4 = time_filter(current_hour=18, start_hour=9, end_hour=18)
        print(f"케이스 4 - 현재 시간(18시)이 거래 종료 시간(18시) 이후: {result4}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 3: 확인 캔들 필터
    print("\n[테스트 3] 확인 캔들 필터")
    print("-" * 60)
    try:
        # 케이스 1: 필터 통과 (연속 2개 캔들이 돌파선 위)
        result1 = confirmation_candle_filter(
            current_price=105.0,
            breakout_price=100.0,
            prev_price=102.0
        )
        print(f"케이스 1 - 현재가(105) > 돌파선(100) AND 이전가(102) > 돌파선(100): {result1}")
        
        # 케이스 2: 필터 실패 (이전 캔들이 돌파선 아래)
        result2 = confirmation_candle_filter(
            current_price=105.0,
            breakout_price=100.0,
            prev_price=98.0
        )
        print(f"케이스 2 - 현재가(105) > 돌파선(100) BUT 이전가(98) <= 돌파선(100): {result2}")
        
        # 케이스 3: 필터 실패 (현재 캔들이 돌파선 아래)
        result3 = confirmation_candle_filter(
            current_price=95.0,
            breakout_price=100.0,
            prev_price=102.0
        )
        print(f"케이스 3 - 현재가(95) <= 돌파선(100) BUT 이전가(102) > 돌파선(100): {result3}")
        
        # 케이스 4: 필터 실패 (두 캔들 모두 돌파선 아래)
        result4 = confirmation_candle_filter(
            current_price=95.0,
            breakout_price=100.0,
            prev_price=98.0
        )
        print(f"케이스 4 - 현재가(95) <= 돌파선(100) AND 이전가(98) <= 돌파선(100): {result4}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 4: 통합 테스트 (실제 사용 시나리오)
    print("\n[테스트 4] 통합 테스트 - 실제 사용 시나리오")
    print("-" * 60)
    try:
        # 시나리오: 변동성 돌파 전략에서 필터 적용
        current_volatility = 1000.0
        avg_volatility = 800.0
        current_hour = 14
        current_price = 105.0
        breakout_price = 100.0
        prev_price = 102.0
        
        # 각 필터 적용
        vol_filter = volatility_filter(current_volatility, avg_volatility)
        time_filter_result = time_filter(current_hour, 9, 18)
        confirm_filter = confirmation_candle_filter(current_price, breakout_price, prev_price)
        
        # 모든 필터 통과 여부
        all_filters_passed = vol_filter and time_filter_result and confirm_filter
        
        print("입력값:")
        print(f"  전일 변동폭: {current_volatility:.0f}")
        print(f"  평균 변동폭: {avg_volatility:.0f}")
        print(f"  현재 시간: {current_hour}시")
        print(f"  현재가: {current_price:.0f}")
        print(f"  돌파선: {breakout_price:.0f}")
        print(f"  이전가: {prev_price:.0f}")
        
        print("\n필터 결과:")
        print(f"  변동성 필터: {'통과' if vol_filter else '실패'}")
        print(f"  시간대 필터: {'통과' if time_filter_result else '실패'}")
        print(f"  확인 캔들 필터: {'통과' if confirm_filter else '실패'}")
        print(f"\n  최종 결과: {'모든 필터 통과 - 거래 가능' if all_filters_passed else '필터 실패 - 거래 불가'}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
