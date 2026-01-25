#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백테스팅 성과 지표 계산 모듈
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_performance_metrics(
    trades: List[Dict[str, Any]],
    initial_capital: Optional[float] = None,
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """
    백테스팅 성과 지표를 계산합니다.
    
    계산 지표:
    1. 총 수익률: (최종 자산 - 초기 자산) / 초기 자산 * 100
    2. 승률: 수익 거래 수 / 전체 거래 수 * 100
    3. MDD (Maximum Drawdown): 누적 수익률의 최고점과 최저점 차이
    4. 샤프 비율: (평균 수익률 - 무위험 수익률) / 수익률 표준편차
    
    Args:
        trades (List[Dict[str, Any]]): 거래 내역 리스트
            각 거래는 다음 키를 포함해야 함:
            - 'date': 거래 날짜
            - 'buy_price': 매수가
            - 'sell_price': 매도가
            - 'quantity': 거래 수량
        initial_capital (Optional[float]): 초기 자산
            None인 경우 첫 거래의 매수 금액 합계를 초기 자산으로 사용
        risk_free_rate (float): 무위험 수익률 (기본값: 0.02 = 2%)
    
    Returns:
        Dict[str, float]: 성과 지표 딕셔너리
            - 'total_return': 총 수익률 (%)
            - 'win_rate': 승률 (%)
            - 'mdd': 최대 낙폭 (MDD, %)
            - 'sharpe_ratio': 샤프 비율
    
    Raises:
        ValueError: 입력 데이터가 유효하지 않을 경우
    
    Examples:
        >>> trades = [
        ...     {'date': '2024-01-01', 'buy_price': 100, 'sell_price': 110, 'quantity': 1},
        ...     {'date': '2024-01-02', 'buy_price': 105, 'sell_price': 100, 'quantity': 1}
        ... ]
        >>> metrics = calculate_performance_metrics(trades)
        >>> print(f"총 수익률: {metrics['total_return']:.2f}%")
    """
    # 입력 데이터 검증
    if not trades or len(trades) == 0:
        logger.warning("거래 내역이 없습니다. 기본값을 반환합니다.")
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'mdd': 0.0,
            'sharpe_ratio': 0.0
        }
    
    # 필수 키 검증
    required_keys = ['buy_price', 'sell_price', 'quantity']
    for i, trade in enumerate(trades):
        for key in required_keys:
            if key not in trade:
                raise ValueError(f"거래 {i+1}번째에 필수 키 '{key}'가 없습니다.")
        
        # 값 검증
        if trade['buy_price'] <= 0 or trade['sell_price'] <= 0 or trade['quantity'] <= 0:
            raise ValueError(f"거래 {i+1}번째의 가격 또는 수량이 0 이하입니다.")
    
    try:
        # 각 거래의 수익률 계산
        trade_returns = []
        trade_profits = []
        cumulative_returns = []
        cumulative_capital = 0.0
        
        # 초기 자산 계산
        if initial_capital is None:
            # 첫 거래의 매수 금액 합계를 초기 자산으로 사용
            initial_capital = sum(
                trade['buy_price'] * trade['quantity'] 
                for trade in trades
            )
            logger.info(f"초기 자산 자동 계산: {initial_capital:,.0f}원")
        else:
            if initial_capital <= 0:
                raise ValueError("초기 자산은 0보다 커야 합니다.")
            logger.info(f"초기 자산: {initial_capital:,.0f}원")
        
        # 각 거래 처리
        for i, trade in enumerate(trades):
            buy_price = float(trade['buy_price'])
            sell_price = float(trade['sell_price'])
            quantity = float(trade['quantity'])
            
            # 거래 금액
            buy_amount = buy_price * quantity
            sell_amount = sell_price * quantity
            
            # 거래 수익률 (각 거래별)
            trade_return = (sell_amount - buy_amount) / buy_amount
            trade_returns.append(trade_return)
            
            # 거래 손익
            profit = sell_amount - buy_amount
            trade_profits.append(profit)
            
            # 누적 자산 계산
            cumulative_capital += sell_amount
            
            # 누적 수익률 계산
            if i == 0:
                cumulative_return = trade_return
            else:
                # 이전 누적 수익률에 현재 거래 수익률을 곱함
                cumulative_return = (1 + cumulative_returns[-1]) * (1 + trade_return) - 1
            
            cumulative_returns.append(cumulative_return)
        
        # numpy 배열로 변환
        trade_returns_array = np.array(trade_returns)
        cumulative_returns_array = np.array(cumulative_returns)
        
        # 1. 총 수익률 계산: (최종 자산 - 초기 자산) / 초기 자산 * 100
        final_capital = cumulative_capital
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        
        logger.info(f"초기 자산: {initial_capital:,.0f}원")
        logger.info(f"최종 자산: {final_capital:,.0f}원")
        logger.info(f"총 수익률: {total_return:.2f}%")
        
        # 2. 승률 계산: 수익 거래 수 / 전체 거래 수 * 100
        winning_trades = sum(1 for profit in trade_profits if profit > 0)
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        logger.info(f"전체 거래: {total_trades}건, 수익 거래: {winning_trades}건")
        logger.info(f"승률: {win_rate:.2f}%")
        
        # 3. MDD (Maximum Drawdown) 계산: 누적 수익률의 최고점과 최저점 차이
        if len(cumulative_returns_array) > 0:
            # 누적 수익률의 최고점 추적
            running_max = np.maximum.accumulate(1 + cumulative_returns_array)
            
            # Drawdown 계산: (현재값 - 최고점) / 최고점
            drawdowns = (1 + cumulative_returns_array - running_max) / running_max
            
            # 최대 낙폭 (가장 큰 음수 값, 절댓값)
            mdd = abs(drawdowns.min()) * 100 if drawdowns.min() < 0 else 0.0
        else:
            mdd = 0.0
        
        logger.info(f"최대 낙폭 (MDD): {mdd:.2f}%")
        
        # 4. 샤프 비율 계산: (평균 수익률 - 무위험 수익률) / 수익률 표준편차
        if len(trade_returns_array) > 0:
            mean_return = np.mean(trade_returns_array)
            std_return = np.std(trade_returns_array)
            
            if std_return > 0:
                # 샤프 비율 = (평균 수익률 - 무위험 수익률) / 표준편차
                sharpe_ratio = (mean_return - risk_free_rate) / std_return
            else:
                # 표준편차가 0이면 샤프 비율 계산 불가
                sharpe_ratio = 0.0
                logger.warning("수익률 표준편차가 0이어서 샤프 비율을 계산할 수 없습니다.")
        else:
            sharpe_ratio = 0.0
        
        logger.info(f"평균 수익률: {mean_return*100:.2f}%")
        logger.info(f"수익률 표준편차: {std_return*100:.2f}%")
        logger.info(f"샤프 비율: {sharpe_ratio:.2f}")
        
        # 결과 반환
        result = {
            'total_return': float(total_return),
            'win_rate': float(win_rate),
            'mdd': float(mdd),
            'sharpe_ratio': float(sharpe_ratio)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"성과 지표 계산 중 오류 발생: {e}")
        raise ValueError(f"성과 지표 계산 실패: {e}")


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("백테스팅 성과 지표 계산 테스트")
    print("=" * 60)
    
    # 테스트 케이스 1: 정상 케이스
    print("\n[테스트 1] 정상 케이스")
    print("-" * 60)
    try:
        trades = [
            {'date': '2024-01-01', 'buy_price': 100.0, 'sell_price': 110.0, 'quantity': 1.0},
            {'date': '2024-01-02', 'buy_price': 105.0, 'sell_price': 115.0, 'quantity': 1.0},
            {'date': '2024-01-03', 'buy_price': 110.0, 'sell_price': 100.0, 'quantity': 1.0},
            {'date': '2024-01-04', 'buy_price': 95.0, 'sell_price': 105.0, 'quantity': 1.0},
        ]
        
        metrics = calculate_performance_metrics(trades)
        
        print("거래 내역:")
        for i, trade in enumerate(trades, 1):
            profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']
            print(f"  {i}. 매수: {trade['buy_price']:.0f}원, "
                  f"매도: {trade['sell_price']:.0f}원, "
                  f"손익: {profit:,.0f}원")
        
        print("\n성과 지표:")
        print(f"  총 수익률: {metrics['total_return']:.2f}%")
        print(f"  승률: {metrics['win_rate']:.2f}%")
        print(f"  MDD: {metrics['mdd']:.2f}%")
        print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 케이스 2: 초기 자산 지정
    print("\n[테스트 2] 초기 자산 지정")
    print("-" * 60)
    try:
        trades = [
            {'date': '2024-01-01', 'buy_price': 100.0, 'sell_price': 110.0, 'quantity': 10.0},
            {'date': '2024-01-02', 'buy_price': 105.0, 'sell_price': 115.0, 'quantity': 10.0},
        ]
        
        initial_capital = 10000.0
        metrics = calculate_performance_metrics(trades, initial_capital=initial_capital)
        
        print(f"초기 자산: {initial_capital:,.0f}원")
        print("\n성과 지표:")
        print(f"  총 수익률: {metrics['total_return']:.2f}%")
        print(f"  승률: {metrics['win_rate']:.2f}%")
        print(f"  MDD: {metrics['mdd']:.2f}%")
        print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 케이스 3: 빈 거래 리스트
    print("\n[테스트 3] 빈 거래 리스트")
    print("-" * 60)
    try:
        trades = []
        metrics = calculate_performance_metrics(trades)
        
        print("성과 지표 (기본값):")
        print(f"  총 수익률: {metrics['total_return']:.2f}%")
        print(f"  승률: {metrics['win_rate']:.2f}%")
        print(f"  MDD: {metrics['mdd']:.2f}%")
        print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 테스트 케이스 4: 실제 비트코인 거래 예시
    print("\n[테스트 4] 실제 비트코인 거래 예시")
    print("-" * 60)
    try:
        trades = [
            {'date': '2024-01-01', 'buy_price': 90000000.0, 'sell_price': 95000000.0, 'quantity': 0.1},
            {'date': '2024-01-02', 'buy_price': 94000000.0, 'sell_price': 98000000.0, 'quantity': 0.1},
            {'date': '2024-01-03', 'buy_price': 97000000.0, 'sell_price': 92000000.0, 'quantity': 0.1},
            {'date': '2024-01-04', 'buy_price': 91000000.0, 'sell_price': 96000000.0, 'quantity': 0.1},
            {'date': '2024-01-05', 'buy_price': 95000000.0, 'sell_price': 100000000.0, 'quantity': 0.1},
        ]
        
        metrics = calculate_performance_metrics(trades)
        
        print("거래 내역:")
        for i, trade in enumerate(trades, 1):
            profit = (trade['sell_price'] - trade['buy_price']) * trade['quantity']
            print(f"  {i}. 매수: {trade['buy_price']:,.0f}원, "
                  f"매도: {trade['sell_price']:,.0f}원, "
                  f"손익: {profit:,.0f}원")
        
        print("\n성과 지표:")
        print(f"  총 수익률: {metrics['total_return']:.2f}%")
        print(f"  승률: {metrics['win_rate']:.2f}%")
        print(f"  MDD: {metrics['mdd']:.2f}%")
        print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
