#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략의 돌파선 계산 모듈
"""

import logging
from typing import Tuple

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_breakout_price(
    high: float,
    low: float,
    k: float,
    current_price: float
) -> Tuple[float, bool]:
    """
    변동성 돌파 전략의 돌파선을 계산하고 매수 신호를 판단합니다.
    
    돌파선 계산 공식:
        target_price = high + (high - low) * k
    
    매수 신호 판단:
        current_price > target_price일 때 매수 신호(True) 반환
    
    Args:
        high (float): 전일 고가
        low (float): 전일 저가
        k (float): 변동성 계수 (0 < k < 1)
        current_price (float): 현재가
    
    Returns:
        Tuple[float, bool]: (target_price, buy_signal) 튜플
            - target_price: 계산된 돌파선 가격
            - buy_signal: 매수 신호 (True: 매수, False: 매수 아님)
    
    Raises:
        ValueError: 입력값이 유효하지 않을 경우
            - high <= low: 고가가 저가보다 크지 않음
            - k <= 0 또는 k >= 1: K값이 범위를 벗어남
    
    Examples:
        >>> target, signal = calculate_breakout_price(100, 90, 0.5, 105)
        >>> print(f"돌파선: {target}, 매수신호: {signal}")
        돌파선: 105.0, 매수신호: True
    """
    # 입력값 검증: high > low
    if high <= low:
        error_msg = f"고가({high})는 저가({low})보다 커야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 입력값 검증: 0 < k < 1
    if k <= 0 or k >= 1:
        error_msg = f"K값({k})은 0과 1 사이의 값이어야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 입력값 검증: 가격이 양수인지 확인
    if high <= 0 or low <= 0 or current_price <= 0:
        error_msg = "가격 값은 0보다 커야 합니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # 돌파선 계산: target_price = high + (high - low) * k
        price_range = high - low  # 전일 변동폭
        target_price = high + (price_range * k)
        
        logger.debug(
            f"돌파선 계산: 고가={high}, 저가={low}, K={k}, "
            f"변동폭={price_range}, 돌파선={target_price}"
        )
        
        # 매수 신호 판단: current_price > target_price
        buy_signal = current_price > target_price
        
        if buy_signal:
            logger.info(
                f"매수 신호 발생: 현재가({current_price}) > 돌파선({target_price:.2f})"
            )
        else:
            logger.debug(
                f"매수 신호 없음: 현재가({current_price}) <= 돌파선({target_price:.2f})"
            )
        
        return (target_price, buy_signal)
        
    except Exception as e:
        logger.error(f"돌파선 계산 중 오류 발생: {e}")
        raise ValueError(f"돌파선 계산 실패: {e}")


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("변동성 돌파 전략 돌파선 계산 테스트")
    print("=" * 60)
    
    # 테스트 케이스 1: 정상 케이스 - 매수 신호 발생
    print("\n[테스트 1] 매수 신호 발생 케이스")
    print("-" * 60)
    try:
        high = 100.0
        low = 90.0
        k = 0.5
        current_price = 105.0
        
        target_price, buy_signal = calculate_breakout_price(high, low, k, current_price)
        
        print(f"입력값:")
        print(f"  고가: {high}")
        print(f"  저가: {low}")
        print(f"  K값: {k}")
        print(f"  현재가: {current_price}")
        print(f"\n결과:")
        print(f"  돌파선: {target_price:.2f}")
        print(f"  매수 신호: {buy_signal}")
        print(f"  설명: 현재가({current_price})가 돌파선({target_price:.2f})을 상향 돌파")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 케이스 2: 정상 케이스 - 매수 신호 없음
    print("\n[테스트 2] 매수 신호 없음 케이스")
    print("-" * 60)
    try:
        high = 100.0
        low = 90.0
        k = 0.5
        current_price = 100.0
        
        target_price, buy_signal = calculate_breakout_price(high, low, k, current_price)
        
        print(f"입력값:")
        print(f"  고가: {high}")
        print(f"  저가: {low}")
        print(f"  K값: {k}")
        print(f"  현재가: {current_price}")
        print(f"\n결과:")
        print(f"  돌파선: {target_price:.2f}")
        print(f"  매수 신호: {buy_signal}")
        print(f"  설명: 현재가({current_price})가 돌파선({target_price:.2f})을 돌파하지 않음")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 케이스 3: 입력값 검증 - high <= low
    print("\n[테스트 3] 입력값 검증 - high <= low")
    print("-" * 60)
    try:
        high = 90.0
        low = 100.0
        k = 0.5
        current_price = 105.0
        
        target_price, buy_signal = calculate_breakout_price(high, low, k, current_price)
        print(f"❌ 검증 실패: 예외가 발생해야 합니다.")
    except ValueError as e:
        print(f"✅ 검증 성공: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    
    # 테스트 케이스 4: 입력값 검증 - k 범위 초과
    print("\n[테스트 4] 입력값 검증 - k 범위 초과")
    print("-" * 60)
    try:
        high = 100.0
        low = 90.0
        k = 1.5  # 범위 초과
        current_price = 105.0
        
        target_price, buy_signal = calculate_breakout_price(high, low, k, current_price)
        print(f"❌ 검증 실패: 예외가 발생해야 합니다.")
    except ValueError as e:
        print(f"✅ 검증 성공: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    
    # 테스트 케이스 5: 실제 비트코인 가격 예시
    print("\n[테스트 5] 실제 비트코인 가격 예시")
    print("-" * 60)
    try:
        # 전일 고가: 95,000,000원, 전일 저가: 90,000,000원
        high = 95000000.0
        low = 90000000.0
        k = 0.5
        current_price = 98000000.0
        
        target_price, buy_signal = calculate_breakout_price(high, low, k, current_price)
        
        print(f"입력값:")
        print(f"  전일 고가: {high:,.0f}원")
        print(f"  전일 저가: {low:,.0f}원")
        print(f"  K값: {k}")
        print(f"  현재가: {current_price:,.0f}원")
        print(f"\n결과:")
        print(f"  돌파선: {target_price:,.0f}원")
        print(f"  매수 신호: {buy_signal}")
        
        if buy_signal:
            print(f"\n✅ 매수 신호 발생!")
            print(f"   현재가가 돌파선을 {current_price - target_price:,.0f}원 상향 돌파")
        else:
            print(f"\n⏸️  매수 신호 없음")
            print(f"   돌파선까지 {target_price - current_price:,.0f}원 남음")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
