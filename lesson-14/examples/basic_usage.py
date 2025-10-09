"""
기본 사용 예제
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user.profile.profile_manager import ProfileManager
from src.user.profile.user_profile import UserType
from src.user.auth.authorization import Authorization
from src.strategy.strategy_loader import StrategyLoader
from src.config.config_manager import ConfigManager


def main():
    """기본 사용 예제"""
    
    print("=" * 60)
    print("사용자 맞춤형 자동매매 시스템 - 기본 사용 예제")
    print("=" * 60)
    print()
    
    # 1. 프로필 관리자 생성
    print("1. 프로필 관리자 생성...")
    profile_manager = ProfileManager("data/user_profiles")
    
    # 2. 초보자 프로필 생성
    print("2. 초보자 프로필 생성...")
    beginner = profile_manager.create_profile(
        user_id="user001",
        user_type=UserType.BEGINNER,
        investment_amount=1000000
    )
    print(f"   [OK] 사용자: {beginner.user_id}")
    print(f"   [OK] 유형: {beginner.user_type.value}")
    print(f"   [OK] 투자금액: {beginner.investment_amount:,}원")
    print(f"   [OK] 최대 포지션: {beginner.trading_limits.max_position_size * 100}%")
    print(f"   [OK] 손절 라인: {beginner.trading_limits.stop_loss * 100}%")
    print()
    
    # 3. 중급자 프로필 생성
    print("3. 중급자 프로필 생성...")
    intermediate = profile_manager.create_profile(
        user_id="user002",
        user_type=UserType.INTERMEDIATE,
        investment_amount=5000000
    )
    print(f"   [OK] 사용자: {intermediate.user_id}")
    print(f"   [OK] 유형: {intermediate.user_type.value}")
    print(f"   [OK] 투자금액: {intermediate.investment_amount:,}원")
    print(f"   [OK] 최대 포지션: {intermediate.trading_limits.max_position_size * 100}%")
    print()
    
    # 4. 고급자 프로필 생성
    print("4. 고급자 프로필 생성...")
    advanced = profile_manager.create_profile(
        user_id="user003",
        user_type=UserType.ADVANCED,
        investment_amount=20000000
    )
    print(f"   [OK] 사용자: {advanced.user_id}")
    print(f"   [OK] 유형: {advanced.user_type.value}")
    print(f"   [OK] 투자금액: {advanced.investment_amount:,}원")
    print(f"   [OK] API 접근: {advanced.can_access_raw_api()}")
    print()
    
    # 5. 권한 확인
    print("5. 사용자별 권한 확인...")
    authorization = Authorization()
    
    for profile in [beginner, intermediate, advanced]:
        available_features = authorization.get_available_features(profile)
        print(f"\n   [{profile.user_type.value}] 사용 가능한 기능:")
        for feature in available_features[:5]:  # 처음 5개만 표시
            print(f"      [OK] {feature}")
        print(f"      ... 총 {len(available_features)}개 기능")
    print()
    
    # 6. 전략 로딩
    print("6. 전략 로딩...")
    strategy_loader = StrategyLoader()
    count = strategy_loader.load_all_strategies()
    print(f"   [OK] 로드된 전략: {count}개")
    print()
    
    # 7. 프로필별 전략 확인
    print("7. 프로필별 사용 가능한 전략...")
    for profile in [beginner, intermediate, advanced]:
        strategies = strategy_loader.get_strategies_for_profile(profile)
        print(f"\n   [{profile.user_type.value}]")
        if strategies:
            for strategy in strategies[:3]:  # 처음 3개만 표시
                print(f"      [OK] {strategy}")
            if len(strategies) > 3:
                print(f"      ... 총 {len(strategies)}개 전략")
        else:
            print("      (전략 없음)")
    print()
    
    # 8. 거래 검증
    print("8. 거래 유효성 검증...")
    
    # 초보자 - 허용된 거래
    trade_info_valid = {
        "coin": "KRW-BTC",
        "position_size": 0.10  # 10%
    }
    is_valid, error = beginner.validate_trade(trade_info_valid)
    print(f"\n   [초보자] BTC 10% 거래:")
    print(f"      [OK] 결과: {'성공' if is_valid else '실패'}")
    if error:
        print(f"      [ERROR] 오류: {error}")
    
    # 초보자 - 제한 초과 거래
    trade_info_invalid = {
        "coin": "KRW-BTC",
        "position_size": 0.30  # 30% (제한 초과)
    }
    is_valid, error = beginner.validate_trade(trade_info_invalid)
    print(f"\n   [초보자] BTC 30% 거래:")
    print(f"      [OK] 결과: {'성공' if is_valid else '실패'}")
    if error:
        print(f"      [ERROR] 오류: {error}")
    
    # 중급자 - 허용된 코인
    trade_info_intermediate = {
        "coin": "KRW-XRP",
        "position_size": 0.20
    }
    is_valid, error = intermediate.validate_trade(trade_info_intermediate)
    print(f"\n   [중급자] XRP 20% 거래:")
    print(f"      [OK] 결과: {'성공' if is_valid else '실패'}")
    if error:
        print(f"      [ERROR] 오류: {error}")
    print()
    
    # 9. 프로필 업그레이드
    print("9. 프로필 업그레이드...")
    print(f"   현재 레벨: {beginner.user_type.value}")
    
    upgraded = profile_manager.upgrade_profile("user001")
    if upgraded:
        print(f"   업그레이드 완료: {upgraded.user_type.value}")
        print(f"   새로운 일일 거래 한도: {upgraded.trading_limits.daily_trade_limit}회")
    print()
    
    # 10. 설정 관리
    print("10. 설정 관리...")
    config_manager = ConfigManager("config")
    
    # 프로필별 설정 로드
    beginner_config = config_manager.load_profile_config(UserType.BEGINNER)
    print(f"   [초보자 설정]")
    print(f"      [OK] UI 복잡도: {beginner_config.get('ui.complexity_level')}")
    print(f"      [OK] 툴팁 표시: {beginner_config.get('ui.show_tooltips')}")
    print(f"      [OK] 튜토리얼 모드: {beginner_config.get('ui.tutorial_mode')}")
    print()
    
    # 11. 요약
    print("=" * 60)
    print("예제 실행 완료!")
    print("=" * 60)
    print(f"\n[OK] 생성된 프로필: {len(profile_manager.list_profiles())}개")
    print(f"[OK] 로드된 전략: {count}개")
    print(f"[OK] 기능 플래그: {len(config_manager.load_feature_flags())}개")
    print("\n프로필은 'data/user_profiles/' 디렉토리에 저장되었습니다.")
    print("설정 파일은 'config/' 디렉토리에서 확인할 수 있습니다.")
    print()


if __name__ == "__main__":
    main()

