"""
realtime_adaptive_bot.py - 실시간 적응형 자동매매 봇

업비트 API와 연동하여 실시간으로 시장 상황을 분석하고
최적의 전략으로 자동 전환하며 거래를 실행합니다.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from upbit_data_collector import UpbitDataCollector, RealtimeDataMonitor
from adaptive_strategy_system import AdaptiveStrategySystem
from market_condition_detector import MarketCondition


class RealtimeAdaptiveBot:
    """
    실시간 적응형 자동매매 봇
    
    기능:
    - 실시간 시장 데이터 수집
    - 시장 상황 자동 감지
    - 전략 자동 전환
    - 자동 매매 실행 (시뮬레이션)
    """
    
    def __init__(self, 
                 market: str,
                 initial_balance: float,
                 update_interval: int = 300,  # 5분
                 dry_run: bool = True):
        """
        초기화
        
        Args:
            market: 거래할 마켓 코드 (예: 'KRW-BTC')
            initial_balance: 초기 자금
            update_interval: 업데이트 간격 (초)
            dry_run: 테스트 모드 (실제 주문 X)
        """
        self.market = market
        self.initial_balance = initial_balance
        self.update_interval = update_interval
        self.dry_run = dry_run
        
        # 데이터 수집기
        self.collector = UpbitDataCollector()
        
        # 적응형 전략 시스템
        self.strategy_system = AdaptiveStrategySystem(account_balance=initial_balance)
        
        # 실행 상태
        self.is_running = False
        self.last_update_time = None
        self.update_count = 0
        
        # 로깅
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'realtime_bot_{market}.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger.info(f"봇 초기화 완료: {market}")
        self.logger.info(f"초기 자금: {initial_balance:,.0f}원")
        self.logger.info(f"업데이트 간격: {update_interval}초")
        self.logger.info(f"모드: {'테스트(DRY RUN)' if dry_run else '실전'}")
    
    def start(self):
        """봇 시작"""
        self.is_running = True
        self.logger.info("\n" + "="*80)
        self.logger.info("🚀 실시간 적응형 자동매매 봇 시작!")
        self.logger.info("="*80 + "\n")
        
        try:
            while self.is_running:
                self.run_cycle()
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n봇 중지 (사용자 중단)")
            self.stop()
        except Exception as e:
            self.logger.error(f"봇 실행 오류: {e}")
            self.stop()
    
    def run_cycle(self):
        """한 사이클 실행"""
        self.update_count += 1
        self.last_update_time = datetime.now()
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"📊 업데이트 #{self.update_count} - {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'='*80}")
        
        try:
            # 1. 데이터 수집
            self.logger.info("\n1️⃣ 데이터 수집 중...")
            current_data = self.collector.get_current_price([self.market])
            historical_data = self.collector.get_candles_daily(self.market, count=100)
            
            if not current_data or historical_data.empty:
                self.logger.warning("데이터 수집 실패")
                return
            
            market_info = current_data[self.market]
            current_price = market_info['price']
            
            self.logger.info(f"현재가: {current_price:,.0f}원")
            self.logger.info(f"24시간 변동: {market_info['change_rate']*100:+.2f}%")
            self.logger.info(f"거래량: {market_info['volume']:,.2f}")
            
            # 2. 전략 실행
            self.logger.info("\n2️⃣ 전략 분석 및 실행...")
            signal = self.strategy_system.execute_strategy(historical_data)
            
            # 3. 시장 상황 출력
            self._print_market_condition(signal['market_condition'])
            
            # 4. 신호 처리
            self._process_signal(signal, current_price)
            
            # 5. 상태 확인
            self._print_status()
            
        except Exception as e:
            self.logger.error(f"사이클 실행 오류: {e}")
    
    def _print_market_condition(self, market_condition: MarketCondition):
        """시장 상황 출력"""
        self.logger.info("\n📈 시장 상황 분석:")
        self.logger.info(f"  추세: {market_condition.trend.value}")
        self.logger.info(f"  추세 강도: {market_condition.trend_strength:.2f}")
        self.logger.info(f"  변동성: {market_condition.volatility.value}")
        self.logger.info(f"  모멘텀: {market_condition.momentum:+.2f}")
        self.logger.info(f"  거래량: {market_condition.volume_profile}")
        self.logger.info(f"  신뢰도: {market_condition.confidence:.2f}")
        self.logger.info(f"  → 추천 전략: {market_condition.get_recommended_strategy()}")
    
    def _process_signal(self, signal: Dict, current_price: float):
        """신호 처리"""
        self.logger.info(f"\n🎯 신호 분석:")
        self.logger.info(f"  현재 전략: {signal['strategy']}")
        self.logger.info(f"  신호: {signal['action']}")
        self.logger.info(f"  신뢰도: {signal['confidence']:.2f}")
        self.logger.info(f"  사유: {signal['reason']}")
        
        # 포지션 없을 때 - 매수 신호 처리
        if self.strategy_system.current_position is None:
            if signal['action'] == 'BUY' and signal['confidence'] > 0.7:
                self.logger.info("\n✅ 매수 신호 감지!")
                
                if self.dry_run:
                    # 테스트 모드
                    self.logger.info("  [DRY RUN] 실제 주문은 실행하지 않습니다.")
                    self.strategy_system.open_position(signal)
                else:
                    # 실전 모드 (TODO: 실제 주문 API 연동)
                    self.logger.warning("  [실전 모드는 아직 구현되지 않았습니다]")
        
        # 포지션 있을 때 - 청산 조건 확인
        else:
            position = self.strategy_system.current_position
            entry_price = position['entry_price']
            stop_loss = position.get('stop_loss')
            take_profit = position.get('take_profit')
            
            pnl_percent = (current_price - entry_price) / entry_price
            
            self.logger.info(f"\n💼 현재 포지션:")
            self.logger.info(f"  진입가: {entry_price:,.0f}원")
            self.logger.info(f"  현재가: {current_price:,.0f}원")
            self.logger.info(f"  손익: {pnl_percent*100:+.2f}%")
            
            should_close = False
            close_reason = ""
            
            # 손절 확인
            if stop_loss and current_price <= stop_loss:
                should_close = True
                close_reason = "손절"
                self.logger.warning(f"  ⚠️ 손절가 도달: {stop_loss:,.0f}원")
            
            # 익절 확인
            elif take_profit and current_price >= take_profit:
                should_close = True
                close_reason = "익절"
                self.logger.info(f"  🎉 익절가 도달: {take_profit:,.0f}원")
            
            # 매도 신호 확인
            elif signal['action'] == 'SELL' and signal['confidence'] > 0.6:
                should_close = True
                close_reason = f"전략 매도 ({signal['reason']})"
                self.logger.info(f"  📤 매도 신호: {signal['reason']}")
            
            # 포지션 청산
            if should_close:
                if self.dry_run:
                    self.logger.info(f"\n✅ 포지션 청산: {close_reason}")
                    self.logger.info("  [DRY RUN] 실제 주문은 실행하지 않습니다.")
                    self.strategy_system.close_position(current_price, close_reason)
                else:
                    self.logger.warning("  [실전 모드는 아직 구현되지 않았습니다]")
    
    def _print_status(self):
        """상태 출력"""
        report = self.strategy_system.get_performance_report()
        
        self.logger.info(f"\n💰 계좌 상태:")
        self.logger.info(f"  현재 잔고: {report['account_balance']:,.0f}원")
        self.logger.info(f"  수익률: {report['total_return_percent']:+.2f}%")
        self.logger.info(f"  총 거래: {report['total_trades']}회")
        
        if report['total_trades'] > 0:
            self.logger.info(f"  승률: {report['win_rate']*100:.1f}%")
            self.logger.info(f"  승: {report['wins']}회 | 패: {report['losses']}회")
        
        self.logger.info(f"  전략 전환: {report['strategy_switches']}회")
        self.logger.info(f"  현재 전략: {report['active_strategy']}")
    
    def stop(self):
        """봇 중지"""
        self.is_running = False
        
        self.logger.info("\n" + "="*80)
        self.logger.info("🛑 봇 중지")
        self.logger.info("="*80)
        
        # 최종 리포트
        self.strategy_system.print_performance_report()
        
        self.logger.info("\n봇이 안전하게 종료되었습니다.")
    
    def get_status(self) -> Dict:
        """현재 상태 조회"""
        return {
            'market': self.market,
            'is_running': self.is_running,
            'update_count': self.update_count,
            'last_update': self.last_update_time,
            'performance': self.strategy_system.get_performance_report()
        }


def main():
    """메인 함수"""
    
    print("\n" + "="*80)
    print("🤖 실시간 적응형 자동매매 봇")
    print("="*80)
    print("\n이 봇은 업비트 API와 연동하여:")
    print("  1. 실시간으로 시장 상황을 분석하고")
    print("  2. 상승장/하락장/횡보장을 자동 감지하여")
    print("  3. 최적의 전략으로 자동 전환하며")
    print("  4. 자동으로 매매를 실행합니다.")
    print("\n⚠️  현재는 테스트 모드(DRY RUN)로 실행됩니다.")
    print("    실제 주문은 실행되지 않습니다.")
    
    # 설정
    print("\n" + "-"*80)
    print("⚙️  설정")
    print("-"*80)
    
    # 마켓 선택
    print("\n거래할 코인을 선택하세요:")
    print("  1. KRW-BTC (비트코인)")
    print("  2. KRW-ETH (이더리움)")
    print("  3. KRW-XRP (리플)")
    print("  4. 직접 입력")
    
    choice = input("\n선택 (1-4): ").strip()
    
    markets = {
        '1': 'KRW-BTC',
        '2': 'KRW-ETH',
        '3': 'KRW-XRP'
    }
    
    if choice in markets:
        market = markets[choice]
    elif choice == '4':
        market = input("마켓 코드 입력 (예: KRW-BTC): ").strip().upper()
    else:
        print("잘못된 선택입니다. KRW-BTC로 설정합니다.")
        market = 'KRW-BTC'
    
    # 초기 자금
    try:
        balance_input = input("\n초기 자금 입력 (원, 기본값: 1000000): ").strip()
        initial_balance = float(balance_input) if balance_input else 1_000_000
    except:
        initial_balance = 1_000_000
    
    # 업데이트 간격
    try:
        interval_input = input("업데이트 간격 입력 (초, 기본값: 300): ").strip()
        update_interval = int(interval_input) if interval_input else 300
    except:
        update_interval = 300
    
    print("\n" + "-"*80)
    print("📋 설정 완료")
    print("-"*80)
    print(f"  마켓: {market}")
    print(f"  초기 자금: {initial_balance:,.0f}원")
    print(f"  업데이트 간격: {update_interval}초 ({update_interval/60:.1f}분)")
    print(f"  모드: 테스트 (DRY RUN)")
    
    input("\n시작하려면 Enter를 누르세요...")
    
    # 봇 생성 및 실행
    bot = RealtimeAdaptiveBot(
        market=market,
        initial_balance=initial_balance,
        update_interval=update_interval,
        dry_run=True
    )
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    finally:
        bot.stop()


if __name__ == "__main__":
    main()

