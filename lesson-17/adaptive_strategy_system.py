"""
adaptive_strategy_system.py - 적응형 전략 자동 전환 시스템

시장 상황을 실시간으로 감지하고 최적의 전략으로 자동 전환합니다.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import logging

from market_condition_detector import MarketConditionDetector, MarketCondition
from market_strategies import (
    BaseStrategy,
    TrendFollowingStrategy,
    RangeTradingStrategy,
    VolatilityBreakoutStrategy,
    DefensiveStrategy,
    MomentumScalpingStrategy
)


class AdaptiveStrategySystem:
    """
    적응형 전략 시스템
    
    기능:
    - 시장 상황 자동 감지
    - 최적 전략 자동 선택
    - 실시간 전략 전환
    - 성과 추적 및 최적화
    """
    
    def __init__(self, account_balance: float, min_confidence: float = 0.6):
        """
        초기화
        
        Args:
            account_balance: 계좌 잔고
            min_confidence: 전략 전환 최소 신뢰도
        """
        self.account_balance = account_balance
        self.initial_balance = account_balance
        self.min_confidence = min_confidence
        
        # 시장 감지기
        self.market_detector = MarketConditionDetector()
        
        # 전략 풀
        self.strategies: Dict[str, Optional[BaseStrategy]] = {
            'trend_following': TrendFollowingStrategy(),
            'range_trading': RangeTradingStrategy(),
            'volatility_breakout': VolatilityBreakoutStrategy(),
            'momentum_scalping': MomentumScalpingStrategy(),
            'defensive': DefensiveStrategy(),
            'wait': None  # 현금 보유
        }
        
        # 현재 활성 전략
        self.active_strategy: Optional[BaseStrategy] = None
        self.active_strategy_name: Optional[str] = None
        
        # 전략 전환 히스토리
        self.strategy_history: List[Dict] = []
        
        # 전략별 성과 추적
        self.strategy_performance = {
            strategy_name: {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'win_rate': 0.0
            }
            for strategy_name in self.strategies.keys()
        }
        
        # 현재 포지션
        self.current_position: Optional[Dict] = None
        
        # 거래 히스토리
        self.trade_history: List[Dict] = []
        
        # 로깅
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def analyze_and_select_strategy(self, 
                                    price_data: pd.DataFrame) -> Tuple[str, MarketCondition]:
        """
        시장 분석 및 최적 전략 선택
        
        Args:
            price_data: OHLCV 데이터
        
        Returns:
            (선택된 전략명, 시장 상황)
        """
        # 시장 상황 감지
        market_condition = self.market_detector.detect_market_condition(price_data)
        
        # 추천 전략
        recommended_strategy = market_condition.get_recommended_strategy()
        
        # 신뢰도가 낮으면 현재 전략 유지
        if market_condition.confidence < self.min_confidence and self.active_strategy_name:
            self.logger.info(
                f"신뢰도 낮음 ({market_condition.confidence:.2f}) - "
                f"현재 전략 유지: {self.active_strategy_name}"
            )
            return self.active_strategy_name, market_condition
        
        return recommended_strategy, market_condition
    
    def execute_strategy(self, price_data: pd.DataFrame) -> Dict:
        """
        전략 실행
        
        Args:
            price_data: OHLCV 데이터
        
        Returns:
            실행 결과
        """
        # 1. 전략 선택
        selected_strategy, market_condition = self.analyze_and_select_strategy(price_data)
        
        # 2. 전략 전환 필요 시
        if selected_strategy != self.active_strategy_name:
            self._switch_strategy(selected_strategy, market_condition)
        
        # 3. 전략 실행 ('wait'는 제외)
        if selected_strategy == 'wait':
            return {
                'action': 'HOLD',
                'reason': '시장 상황 부적합 - 현금 보유',
                'market_condition': market_condition,
                'strategy': 'wait'
            }
        
        # 4. 신호 생성
        strategy = self.strategies[selected_strategy]
        signal = strategy.generate_signal(price_data)
        
        # 5. 포지션 크기 계산
        if signal['action'] == 'BUY':
            risk_percent = 0.02  # 기본 2%
            position_size = strategy.calculate_position_size(
                self.account_balance, risk_percent
            )
            signal['position_size'] = position_size
        
        # 6. 시장 상황 정보 추가
        signal['market_condition'] = market_condition
        signal['strategy'] = selected_strategy
        
        return signal
    
    def _switch_strategy(self, new_strategy: str, market_condition: MarketCondition):
        """
        전략 전환
        
        Args:
            new_strategy: 새 전략명
            market_condition: 현재 시장 상황
        """
        old_strategy = self.active_strategy_name
        
        self.active_strategy_name = new_strategy
        self.active_strategy = self.strategies.get(new_strategy)
        
        # 히스토리 기록
        self.strategy_history.append({
            'timestamp': datetime.now(),
            'from_strategy': old_strategy,
            'to_strategy': new_strategy,
            'market_trend': market_condition.trend.value,
            'market_volatility': market_condition.volatility.value,
            'confidence': market_condition.confidence
        })
        
        self.logger.info(
            f"\n{'='*60}\n"
            f"🔄 전략 전환\n"
            f"{'='*60}\n"
            f"이전 전략: {old_strategy}\n"
            f"새 전략: {new_strategy}\n"
            f"시장 상황: {market_condition.trend.value}\n"
            f"변동성: {market_condition.volatility.value}\n"
            f"신뢰도: {market_condition.confidence:.2f}\n"
            f"{'='*60}"
        )
    
    def open_position(self, signal: Dict) -> bool:
        """
        포지션 개설
        
        Args:
            signal: 매매 신호
        
        Returns:
            성공 여부
        """
        if signal['action'] != 'BUY':
            return False
        
        if self.current_position is not None:
            self.logger.warning("이미 포지션이 열려있습니다.")
            return False
        
        self.current_position = {
            'strategy': signal['strategy'],
            'entry_price': signal['entry_price'],
            'position_size': signal['position_size'],
            'stop_loss': signal.get('stop_loss'),
            'take_profit': signal.get('take_profit'),
            'entry_time': datetime.now(),
            'reason': signal['reason']
        }
        
        self.logger.info(
            f"\n✅ 포지션 개설\n"
            f"전략: {signal['strategy']}\n"
            f"진입가: {signal['entry_price']:,.0f}원\n"
            f"투자금: {signal['position_size']:,.0f}원\n"
            f"손절가: {signal.get('stop_loss', 0):,.0f}원\n"
            f"익절가: {signal.get('take_profit', 0):,.0f}원\n"
            f"사유: {signal['reason']}"
        )
        
        return True
    
    def close_position(self, exit_price: float, reason: str) -> Optional[Dict]:
        """
        포지션 청산
        
        Args:
            exit_price: 청산 가격
            reason: 청산 사유
        
        Returns:
            거래 결과
        """
        if self.current_position is None:
            return None
        
        # 손익 계산
        entry_price = self.current_position['entry_price']
        position_size = self.current_position['position_size']
        
        quantity = position_size / entry_price
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = (exit_price - entry_price) / entry_price
        
        # 거래 기록
        trade_result = {
            'strategy': self.current_position['strategy'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'entry_time': self.current_position['entry_time'],
            'exit_time': datetime.now(),
            'reason': reason
        }
        
        self.trade_history.append(trade_result)
        
        # 계좌 업데이트
        self.account_balance += pnl
        
        # 전략 성과 업데이트
        self.record_trade_result(self.current_position['strategy'], pnl)
        
        # 로깅
        profit_emoji = '✅' if pnl > 0 else '❌'
        self.logger.info(
            f"\n{profit_emoji} 포지션 청산\n"
            f"전략: {self.current_position['strategy']}\n"
            f"진입가: {entry_price:,.0f}원\n"
            f"청산가: {exit_price:,.0f}원\n"
            f"손익: {pnl:+,.0f}원 ({pnl_percent*100:+.2f}%)\n"
            f"사유: {reason}\n"
            f"잔고: {self.account_balance:,.0f}원"
        )
        
        # 포지션 초기화
        self.current_position = None
        
        return trade_result
    
    def record_trade_result(self, strategy_name: str, pnl: float):
        """
        거래 결과 기록
        
        Args:
            strategy_name: 전략명
            pnl: 손익
        """
        perf = self.strategy_performance[strategy_name]
        
        perf['total_trades'] += 1
        perf['total_pnl'] += pnl
        
        if pnl > 0:
            perf['wins'] += 1
        else:
            perf['losses'] += 1
        
        perf['avg_pnl'] = perf['total_pnl'] / perf['total_trades']
        perf['win_rate'] = perf['wins'] / perf['total_trades'] if perf['total_trades'] > 0 else 0
    
    def get_performance_report(self) -> Dict:
        """
        성과 리포트 생성
        
        Returns:
            성과 리포트
        """
        total_return = (self.account_balance - self.initial_balance) / self.initial_balance
        total_trades = len(self.trade_history)
        
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        losses = sum(1 for t in self.trade_history if t['pnl'] < 0)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        return {
            'timestamp': datetime.now(),
            'account_balance': self.account_balance,
            'initial_balance': self.initial_balance,
            'total_return': total_return,
            'total_return_percent': total_return * 100,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'active_strategy': self.active_strategy_name,
            'strategy_switches': len(self.strategy_history),
            'strategy_performance': self.strategy_performance
        }
    
    def print_performance_report(self):
        """성과 리포트 출력"""
        report = self.get_performance_report()
        
        print("\n" + "="*60)
        print("📊 성과 리포트")
        print("="*60)
        print(f"초기 잔고: {report['initial_balance']:,.0f}원")
        print(f"현재 잔고: {report['account_balance']:,.0f}원")
        print(f"수익률: {report['total_return_percent']:+.2f}%")
        print(f"\n총 거래: {report['total_trades']}회")
        print(f"승: {report['wins']}회 | 패: {report['losses']}회")
        print(f"승률: {report['win_rate']*100:.1f}%")
        print(f"\n전략 전환: {report['strategy_switches']}회")
        print(f"현재 전략: {report['active_strategy']}")
        
        print("\n" + "-"*60)
        print("전략별 성과:")
        print("-"*60)
        
        for strategy_name, perf in report['strategy_performance'].items():
            if perf['total_trades'] > 0:
                print(f"\n{strategy_name}:")
                print(f"  거래 횟수: {perf['total_trades']}회")
                print(f"  승률: {perf['win_rate']*100:.1f}%")
                print(f"  평균 손익: {perf['avg_pnl']:+,.0f}원")
                print(f"  총 손익: {perf['total_pnl']:+,.0f}원")
        
        print("="*60)

