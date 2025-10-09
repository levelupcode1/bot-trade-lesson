"""
ml_trading_system.py - ML 기반 자동매매 시스템

ML 가격 예측을 실제 거래 시스템에 통합합니다.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
import logging

from ml_price_predictor import MLPricePredictor


class MLTradingSystem:
    """
    ML 기반 자동매매 시스템
    
    기능:
    - ML 예측 기반 매매 신호 생성
    - 신뢰도 기반 포지션 사이징
    - 리스크 관리 (손절/익절)
    - 백테스팅
    - 성과 추적
    """
    
    def __init__(
        self,
        predictor: MLPricePredictor,
        initial_capital: float = 10_000_000,
        signal_threshold: float = 0.02,  # 2% 이상 변동 시 신호
        confidence_threshold: float = 0.7,  # 70% 이상 신뢰도
        position_size: float = 0.03,  # 계좌의 3%
        stop_loss: float = -0.03,  # -3% 손절
        take_profit: float = 0.05,  # +5% 익절
        max_positions: int = 3  # 최대 보유 수
    ):
        """
        초기화
        
        Args:
            predictor: ML 예측 시스템
            initial_capital: 초기 자본
            signal_threshold: 신호 임계값
            confidence_threshold: 신뢰도 임계값
            position_size: 포지션 크기 비율
            stop_loss: 손절 비율
            take_profit: 익절 비율
            max_positions: 최대 보유 포지션 수
        """
        self.predictor = predictor
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 거래 파라미터
        self.signal_threshold = signal_threshold
        self.confidence_threshold = confidence_threshold
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_positions = max_positions
        
        # 포지션 관리
        self.positions = []  # 현재 보유 포지션
        self.trade_history = []  # 거래 히스토리
        
        # 성과 추적
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.max_drawdown = 0
        self.peak_capital = initial_capital
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_signal(
        self,
        current_price: float,
        predicted_price: float,
        confidence: float
    ) -> Dict:
        """
        매매 신호 생성
        
        Args:
            current_price: 현재 가격
            predicted_price: 예측 가격
            confidence: 신뢰도
        
        Returns:
            신호 딕셔너리
        """
        # 예상 변화율
        expected_change = (predicted_price - current_price) / current_price
        
        # 신호 생성
        signal = 'HOLD'
        reason = ''
        
        # 신뢰도 체크
        if confidence < self.confidence_threshold:
            reason = f'낮은 신뢰도 ({confidence:.2%})'
            return {
                'signal': signal,
                'expected_change': expected_change,
                'confidence': confidence,
                'reason': reason
            }
        
        # 매수 신호
        if expected_change > self.signal_threshold:
            signal = 'BUY'
            reason = f'상승 예측 ({expected_change:+.2%})'
        
        # 매도 신호
        elif expected_change < -self.signal_threshold:
            signal = 'SELL'
            reason = f'하락 예측 ({expected_change:+.2%})'
        
        else:
            reason = f'변화율 작음 ({expected_change:+.2%})'
        
        return {
            'signal': signal,
            'expected_change': expected_change,
            'confidence': confidence,
            'reason': reason
        }
    
    def calculate_position_size(
        self,
        confidence: float
    ) -> float:
        """
        신뢰도 기반 포지션 크기 계산
        
        Args:
            confidence: 신뢰도 (0~1)
        
        Returns:
            투자 금액
        """
        # 기본 포지션 크기
        base_size = self.current_capital * self.position_size
        
        # 신뢰도에 따라 조정
        # 신뢰도 0.7 = 50%, 0.8 = 75%, 0.9 = 100%, 1.0 = 125%
        confidence_multiplier = (confidence - 0.5) * 2
        confidence_multiplier = max(0.5, min(1.25, confidence_multiplier))
        
        adjusted_size = base_size * confidence_multiplier
        
        # 사용 가능한 자본 확인
        available_capital = self.current_capital * 0.8  # 최대 80%까지 사용
        adjusted_size = min(adjusted_size, available_capital)
        
        return adjusted_size
    
    def open_position(
        self,
        signal: Dict,
        current_price: float,
        timestamp: datetime
    ):
        """
        포지션 오픈
        
        Args:
            signal: 매매 신호
            current_price: 현재 가격
            timestamp: 시간
        """
        # 최대 포지션 수 체크
        if len(self.positions) >= self.max_positions:
            self.logger.warning(f"최대 포지션 수 도달 ({self.max_positions})")
            return
        
        # 포지션 크기 계산
        position_value = self.calculate_position_size(signal['confidence'])
        
        # 포지션 생성
        position = {
            'entry_price': current_price,
            'entry_time': timestamp,
            'position_value': position_value,
            'quantity': position_value / current_price,
            'signal': signal,
            'stop_loss_price': current_price * (1 + self.stop_loss),
            'take_profit_price': current_price * (1 + self.take_profit)
        }
        
        self.positions.append(position)
        self.current_capital -= position_value
        
        self.logger.info(f"📈 매수: {current_price:,.0f}원 "
                        f"({position_value:,.0f}원, {signal['confidence']:.2%} 신뢰도)")
    
    def close_position(
        self,
        position: Dict,
        current_price: float,
        timestamp: datetime,
        reason: str
    ):
        """
        포지션 청산
        
        Args:
            position: 포지션 정보
            current_price: 현재 가격
            timestamp: 시간
            reason: 청산 이유
        """
        # 수익 계산
        entry_value = position['position_value']
        exit_value = position['quantity'] * current_price
        profit = exit_value - entry_value
        profit_rate = profit / entry_value
        
        # 자본 업데이트
        self.current_capital += exit_value
        self.total_profit += profit
        
        # 통계 업데이트
        self.total_trades += 1
        if profit > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # 최대 낙폭 계산
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 거래 히스토리 저장
        trade = {
            'entry_price': position['entry_price'],
            'entry_time': position['entry_time'],
            'exit_price': current_price,
            'exit_time': timestamp,
            'profit': profit,
            'profit_rate': profit_rate,
            'reason': reason
        }
        self.trade_history.append(trade)
        
        # 포지션 제거
        self.positions.remove(position)
        
        profit_emoji = "💰" if profit > 0 else "📉"
        self.logger.info(f"{profit_emoji} 매도: {current_price:,.0f}원 "
                        f"({profit:+,.0f}원, {profit_rate:+.2%}) - {reason}")
    
    def check_risk_management(
        self,
        current_price: float,
        timestamp: datetime
    ):
        """
        리스크 관리 (손절/익절 체크)
        
        Args:
            current_price: 현재 가격
            timestamp: 시간
        """
        positions_to_close = []
        
        for position in self.positions:
            # 손절 체크
            if current_price <= position['stop_loss_price']:
                positions_to_close.append((position, '손절'))
            
            # 익절 체크
            elif current_price >= position['take_profit_price']:
                positions_to_close.append((position, '익절'))
        
        # 청산 실행
        for position, reason in positions_to_close:
            self.close_position(position, current_price, timestamp, reason)
    
    def backtest(
        self,
        X_test_lstm: np.ndarray,
        X_test_ml: np.ndarray,
        prices: np.ndarray,
        timestamps: List[datetime]
    ) -> Dict:
        """
        백테스팅
        
        Args:
            X_test_lstm: LSTM 테스트 데이터
            X_test_ml: ML 테스트 데이터
            prices: 실제 가격 데이터
            timestamps: 시간 데이터
        
        Returns:
            백테스팅 결과
        """
        self.logger.info("="*60)
        self.logger.info("백테스팅 시작")
        self.logger.info("="*60)
        
        # 초기화
        self.current_capital = self.initial_capital
        self.positions = []
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.max_drawdown = 0
        self.peak_capital = self.initial_capital
        
        # 가격 예측
        self.logger.info("가격 예측 중...")
        predictions = self.predictor.predict(X_test_lstm, X_test_ml)
        
        # 매매 시뮬레이션
        self.logger.info("매매 시뮬레이션 시작...\n")
        
        for i in range(len(prices) - 1):
            current_price = prices[i]
            predicted_price = predictions['predictions'][i]
            confidence = predictions['confidence'][i]
            timestamp = timestamps[i] if i < len(timestamps) else datetime.now()
            
            # 신호 생성
            signal = self.generate_signal(
                current_price,
                predicted_price,
                confidence
            )
            
            # 매수 신호
            if signal['signal'] == 'BUY' and len(self.positions) < self.max_positions:
                self.open_position(signal, current_price, timestamp)
            
            # 매도 신호 또는 리스크 관리
            if len(self.positions) > 0:
                # 리스크 관리 체크
                self.check_risk_management(current_price, timestamp)
                
                # 매도 신호 시 모든 포지션 청산
                if signal['signal'] == 'SELL':
                    for position in self.positions[:]:
                        self.close_position(
                            position,
                            current_price,
                            timestamp,
                            '매도 신호'
                        )
        
        # 남은 포지션 청산
        final_price = prices[-1]
        final_timestamp = timestamps[-1] if timestamps else datetime.now()
        for position in self.positions[:]:
            self.close_position(
                position,
                final_price,
                final_timestamp,
                '백테스트 종료'
            )
        
        # 결과 계산
        results = self._calculate_results()
        
        # 결과 출력
        self._print_results(results)
        
        return results
    
    def _calculate_results(self) -> Dict:
        """백테스팅 결과 계산"""
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        # 평균 수익/손실
        if self.trade_history:
            profits = [t['profit'] for t in self.trade_history]
            winning_profits = [p for p in profits if p > 0]
            losing_profits = [p for p in profits if p < 0]
            
            avg_profit = np.mean(winning_profits) if winning_profits else 0
            avg_loss = np.mean(losing_profits) if losing_profits else 0
            profit_factor = abs(sum(winning_profits) / sum(losing_profits)) if losing_profits else 0
        else:
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        
        # 샤프 비율 (간단한 계산)
        if self.trade_history:
            returns = [t['profit_rate'] for t in self.trade_history]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_profit': self.total_profit,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
    
    def _print_results(self, results: Dict):
        """결과 출력"""
        self.logger.info("\n" + "="*60)
        self.logger.info("백테스팅 결과")
        self.logger.info("="*60)
        
        self.logger.info(f"\n💰 수익 지표:")
        self.logger.info(f"  초기 자본: {results['initial_capital']:,.0f}원")
        self.logger.info(f"  최종 자본: {results['final_capital']:,.0f}원")
        self.logger.info(f"  총 수익: {results['total_profit']:+,.0f}원 "
                        f"({results['total_return']:+.2%})")
        
        self.logger.info(f"\n📊 거래 통계:")
        self.logger.info(f"  총 거래 수: {results['total_trades']}회")
        self.logger.info(f"  승리: {results['winning_trades']}회")
        self.logger.info(f"  손실: {results['losing_trades']}회")
        self.logger.info(f"  승률: {results['win_rate']:.2%}")
        
        self.logger.info(f"\n📈 성과 지표:")
        self.logger.info(f"  평균 수익: {results['avg_profit']:+,.0f}원")
        self.logger.info(f"  평균 손실: {results['avg_loss']:+,.0f}원")
        self.logger.info(f"  손익비: {results['profit_factor']:.2f}")
        self.logger.info(f"  최대 낙폭: {results['max_drawdown']:.2%}")
        self.logger.info(f"  샤프 비율: {results['sharpe_ratio']:.2f}")
        
        self.logger.info("\n" + "="*60)
    
    def get_trade_history_df(self) -> pd.DataFrame:
        """거래 히스토리를 데이터프레임으로 반환"""
        if not self.trade_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.trade_history)


if __name__ == '__main__':
    print("ML 거래 시스템 테스트\n")
    
    # 예측 시스템 초기화
    predictor = MLPricePredictor(
        market='KRW-BTC',
        sequence_length=60
    )
    
    # 데이터 준비 및 학습 (실제로는 먼저 실행)
    print("데이터 준비 및 모델 학습...")
    (X_train_lstm, X_train_ml, X_val_lstm, X_val_ml,
     X_test_lstm, X_test_ml, y_train, y_val, y_test) = predictor.prepare_data(
        interval='60',
        days=180
    )
    
    predictor.train_models(
        X_train_lstm, X_train_ml,
        X_val_lstm, X_val_ml,
        y_train, y_val,
        lstm_epochs=10,  # 테스트용 짧게
        lstm_batch_size=32
    )
    
    # 거래 시스템 초기화
    trading_system = MLTradingSystem(
        predictor=predictor,
        initial_capital=10_000_000,
        signal_threshold=0.02,
        confidence_threshold=0.7
    )
    
    # 백테스팅
    # 실제 가격 데이터 (역정규화)
    y_test_2d = y_test.reshape(-1, 1)
    prices = predictor.y_scaler.inverse_transform(y_test_2d).flatten()
    timestamps = [datetime.now()] * len(prices)
    
    results = trading_system.backtest(
        X_test_lstm,
        X_test_ml,
        prices,
        timestamps
    )

