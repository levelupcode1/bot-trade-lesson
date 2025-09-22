#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 가격 알림 봇 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bitcoin_price_alert_simple import BitcoinPriceAlertBot

def test_api_connection():
    """API 연결 테스트"""
    print("🔍 Upbit API 연결 테스트 중...")
    
    bot = BitcoinPriceAlertBot()
    price = bot.get_bitcoin_price()
    
    if price:
        print(f"✅ API 연결 성공! 현재 비트코인 가격: {price:,.0f}원")
        return True
    else:
        print("❌ API 연결 실패!")
        return False

def test_price_calculation():
    """가격 변화율 계산 테스트"""
    print("\n🧮 가격 변화율 계산 테스트 중...")
    
    bot = BitcoinPriceAlertBot()
    
    # 테스트 데이터
    bot.base_price = 100000000  # 1억원
    bot.current_price = 100100000  # 1억 1만원 (0.1% 상승)
    
    change_percent = bot.calculate_price_change()
    expected_change = 0.1
    
    print(f"기준 가격: {bot.base_price:,.0f}원")
    print(f"현재 가격: {bot.current_price:,.0f}원")
    print(f"계산된 변화율: {change_percent:.2f}%")
    print(f"예상 변화율: {expected_change:.2f}%")
    
    if abs(change_percent - expected_change) < 0.01:
        print("✅ 가격 변화율 계산 정상!")
        return True
    else:
        print("❌ 가격 변화율 계산 오류!")
        return False

def test_alert_threshold():
    """알림 임계값 테스트"""
    print("\n🚨 알림 임계값 테스트 중...")
    
    bot = BitcoinPriceAlertBot()
    
    # 0.01% 미만 상승 테스트 (알림 발생 안함)
    bot.base_price = 100000000
    bot.current_price = 100010000  # 0.01% 상승
    change_percent = bot.calculate_price_change()
    
    print(f"0.01% 상승 테스트: {change_percent:.2f}% (임계값: {bot.alert_threshold}%)")
    if change_percent < bot.alert_threshold:
        print("✅ 0.01% 상승 시 알림 발생하지 않음 (정상)")
    else:
        print("❌ 0.01% 상승 시 알림 발생함 (오류)")
        return False
    
    # 0.02% 이상 상승 테스트 (알림 발생)
    bot.current_price = 100020000  # 0.02% 상승
    change_percent = bot.calculate_price_change()
    
    print(f"0.02% 상승 테스트: {change_percent:.2f}% (임계값: {bot.alert_threshold}%)")
    if change_percent >= bot.alert_threshold:
        print("✅ 0.02% 상승 시 알림 발생함 (정상)")
        return True
    else:
        print("❌ 0.02% 상승 시 알림 발생하지 않음 (오류)")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 비트코인 가격 알림 봇 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("API 연결 테스트", test_api_connection),
        ("가격 변화율 계산 테스트", test_price_calculation),
        ("알림 임계값 테스트", test_alert_threshold)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 실행 중 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 통과했습니다!")
        print("봇을 실행할 준비가 되었습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        print("문제를 해결한 후 다시 테스트해주세요.")
    
    print("\n실제 봇을 실행하려면 다음 명령어를 사용하세요:")
    print("python bitcoin_price_alert_simple.py")

if __name__ == "__main__":
    main()
