"""
example_adaptive_trading.py - 적응형 전략 시스템 실행 예제

시장 상황에 따라 자동으로 전략이 전환되는 모습을 시뮬레이션합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from adaptive_strategy_system import AdaptiveStrategySystem


def generate_sample_data(scenario: str, days: int = 100) -> pd.DataFrame:
    """
    시나리오별 샘플 데이터 생성
    
    Args:
        scenario: 'bull' (상승장), 'bear' (하락장), 'sideways' (횡보장), 'mixed' (혼합)
        days: 생성할 일수
    
    Returns:
        OHLCV 데이터
    """
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    base_price = 50_000_000  # 5천만원
    
    if scenario == 'bull':
        # 상승장: 꾸준한 상승 + 낮은 변동성
        trend = np.linspace(0, 0.3, days)  # 30% 상승
        noise = np.random.randn(days) * 0.01  # 1% 변동
        returns = trend + noise
        
    elif scenario == 'bear':
        # 하락장: 꾸준한 하락 + 중간 변동성
        trend = np.linspace(0, -0.25, days)  # 25% 하락
        noise = np.random.randn(days) * 0.02  # 2% 변동
        returns = trend + noise
        
    elif scenario == 'sideways':
        # 횡보장: 방향성 없음 + 작은 변동
        returns = np.random.randn(days) * 0.015  # 1.5% 변동
        
    else:  # mixed
        # 혼합: 상승 → 횡보 → 하락 → 반등
        bull_period = days // 4
        sideways_period = days // 4
        bear_period = days // 4
        recovery_period = days - (bull_period + sideways_period + bear_period)
        
        bull_returns = np.linspace(0, 0.2, bull_period) + np.random.randn(bull_period) * 0.01
        sideways_returns = np.random.randn(sideways_period) * 0.015
        bear_returns = np.linspace(0, -0.15, bear_period) + np.random.randn(bear_period) * 0.025
        recovery_returns = np.linspace(0, 0.1, recovery_period) + np.random.randn(recovery_period) * 0.02
        
        returns = np.concatenate([bull_returns, sideways_returns, bear_returns, recovery_returns])
    
    # 가격 계산 (누적 수익률)
    prices = base_price * (1 + returns)
    
    # OHLCV 생성
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + abs(np.random.randn(days)) * 0.01),
        'low': prices * (1 - abs(np.random.randn(days)) * 0.01),
        'close': prices,
        'volume': np.random.randint(100, 1000, days) * 1_000_000
    })
    
    # high는 open, close보다 높아야 함
    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    # low는 open, close보다 낮아야 함
    data['low'] = data[['open', 'close', 'low']].min(axis=1)
    
    return data


def run_simulation(scenario: str, initial_balance: float = 10_000_000):
    """
    시뮬레이션 실행
    
    Args:
        scenario: 시장 시나리오
        initial_balance: 초기 자금
    """
    print("\n" + "="*80)
    print(f"🚀 적응형 전략 시스템 시뮬레이션 - {scenario.upper()} 시나리오")
    print("="*80)
    
    # 데이터 생성
    price_data = generate_sample_data(scenario, days=100)
    
    # 시스템 초기화
    system = AdaptiveStrategySystem(account_balance=initial_balance)
    
    # 시뮬레이션 실행
    lookback_window = 50  # 분석 기간
    
    for i in range(lookback_window, len(price_data)):
        # 분석용 데이터 (최근 N일)
        analysis_data = price_data.iloc[i-lookback_window:i].copy()
        current_price = price_data.iloc[i]['close']
        
        # 전략 실행
        signal = system.execute_strategy(analysis_data)
        
        # 포지션 관리
        if system.current_position is None:
            # 매수 신호
            if signal['action'] == 'BUY' and signal['confidence'] > 0.7:
                system.open_position(signal)
        
        else:
            # 포지션이 있을 때
            entry_price = system.current_position['entry_price']
            stop_loss = system.current_position.get('stop_loss')
            take_profit = system.current_position.get('take_profit')
            
            # 손절 확인
            if stop_loss and current_price <= stop_loss:
                system.close_position(current_price, "손절")
            
            # 익절 확인
            elif take_profit and current_price >= take_profit:
                system.close_position(current_price, "익절")
            
            # 매도 신호
            elif signal['action'] == 'SELL' and signal['confidence'] > 0.6:
                system.close_position(current_price, signal['reason'])
    
    # 마지막 포지션 정리
    if system.current_position:
        last_price = price_data.iloc[-1]['close']
        system.close_position(last_price, "시뮬레이션 종료")
    
    # 성과 리포트
    system.print_performance_report()
    
    # 전략 전환 히스토리
    if system.strategy_history:
        print("\n" + "="*80)
        print("📈 전략 전환 히스토리")
        print("="*80)
        for i, switch in enumerate(system.strategy_history[:10], 1):  # 최근 10개만
            print(f"\n{i}. {switch['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   {switch['from_strategy']} → {switch['to_strategy']}")
            print(f"   시장: {switch['market_trend']} ({switch['market_volatility']})")
            print(f"   신뢰도: {switch['confidence']:.2f}")


def main():
    """메인 함수"""
    
    print("\n" + "="*80)
    print("💡 적응형 전략 자동 전환 시스템")
    print("="*80)
    print("\n이 시스템은 시장 상황을 자동으로 감지하고,")
    print("상승장, 하락장, 횡보장에 따라 최적의 전략으로 자동 전환합니다.")
    print("\n전략 종류:")
    print("  1. 추세 추종 전략 (상승장)")
    print("  2. 레인지 트레이딩 전략 (횡보장)")
    print("  3. 변동성 돌파 전략 (횡보장 → 추세 전환)")
    print("  4. 모멘텀 스캘핑 전략 (고변동성 상승장)")
    print("  5. 방어 전략 (하락장)")
    
    # 시나리오별 시뮬레이션
    scenarios = ['bull', 'bear', 'sideways', 'mixed']
    
    for scenario in scenarios:
        run_simulation(scenario)
        input("\n계속하려면 Enter를 누르세요...")
    
    print("\n" + "="*80)
    print("✅ 모든 시뮬레이션 완료!")
    print("="*80)


if __name__ == "__main__":
    main()

