"""
autonomous_trading_bot.py - 완전 자동 24/7 자동매매 봇

사람 개입 없이 24시간 365일 자동으로 수익을 창출하는 시스템
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lesson-17'))

import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import traceback
import json

try:
    from upbit_data_collector import UpbitDataCollector
except ImportError:
    print("⚠️ 경고: lesson-17/upbit_data_collector.py를 찾을 수 없습니다.")
    UpbitDataCollector = None

from ml_price_predictor import MLPricePredictor
from ml_trading_system import MLTradingSystem
import pandas as pd
import numpy as np


class AutonomousTradingBot:
    """
    완전 자동 24/7 자동매매 봇
    
    기능:
    - 24시간 365일 자동 실행
    - 실시간 데이터 수집 및 분석
    - ML 기반 가격 예측
    - 자동 매매 실행
    - 오류 자동 복구
    - 성과 모니터링
    - 텔레그램 알림 (선택)
    - 자동 재학습
    """
    
    def __init__(
        self,
        market: str = 'KRW-BTC',
        initial_capital: float = 10_000_000,
        check_interval: int = 60,  # 60초마다 체크
        model_retrain_days: int = 7,  # 7일마다 재학습
        log_file: str = './logs/autonomous_bot.log'
    ):
        """
        초기화
        
        Args:
            market: 거래 마켓
            initial_capital: 초기 자본
            check_interval: 체크 간격 (초)
            model_retrain_days: 모델 재학습 주기 (일)
            log_file: 로그 파일 경로
        """
        self.market = market
        self.initial_capital = initial_capital
        self.check_interval = check_interval
        self.model_retrain_days = model_retrain_days
        
        # 로깅 설정
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 컴포넌트 초기화
        self.data_collector = UpbitDataCollector() if UpbitDataCollector else None
        self.predictor = None
        self.trading_system = None
        
        # 상태 관리
        self.is_running = False
        self.last_model_training = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        # 성과 추적
        self.daily_stats = {
            'date': datetime.now().date(),
            'trades': 0,
            'profit': 0,
            'win': 0,
            'loss': 0
        }
        
        self.logger.info("="*80)
        self.logger.info("🤖 Autonomous Trading Bot Initialized")
        self.logger.info("="*80)
        self.logger.info(f"Market: {market}")
        self.logger.info(f"Initial Capital: {initial_capital:,.0f} KRW")
        self.logger.info(f"Check Interval: {check_interval} seconds")
    
    def initialize_models(self, force_retrain: bool = False):
        """
        모델 초기화 및 학습
        
        Args:
            force_retrain: 강제 재학습 여부
        """
        try:
            self.logger.info("\n📊 Initializing ML Models...")
            
            # 예측 시스템 초기화
            self.predictor = MLPricePredictor(
                market=self.market,
                sequence_length=60,
                forecast_horizon=1
            )
            
            # 저장된 모델 로드 시도
            if not force_retrain:
                try:
                    self.predictor.load_models()
                    self.logger.info("✅ Loaded existing models")
                    self.last_model_training = datetime.now()
                    
                    # 거래 시스템 초기화
                    self.trading_system = MLTradingSystem(
                        predictor=self.predictor,
                        initial_capital=self.initial_capital,
                        signal_threshold=0.02,
                        confidence_threshold=0.7,
                        position_size=0.03,
                        stop_loss=-0.03,
                        take_profit=0.05,
                        max_positions=3
                    )
                    
                    return True
                except:
                    self.logger.warning("⚠️ No existing models found. Training new models...")
            
            # 새로운 모델 학습
            self.train_models()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Model initialization failed: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def train_models(self):
        """모델 학습"""
        try:
            self.logger.info("\n🎓 Training ML Models...")
            self.logger.info("This may take 10-30 minutes...")
            
            # 데이터 준비
            (X_train_lstm, X_train_ml, X_val_lstm, X_val_ml,
             X_test_lstm, X_test_ml, y_train, y_val, y_test) = self.predictor.prepare_data(
                interval='60',
                days=180
            )
            
            # 모델 학습
            self.predictor.train_models(
                X_train_lstm, X_train_ml,
                X_val_lstm, X_val_ml,
                y_train, y_val,
                lstm_epochs=30,
                lstm_batch_size=32
            )
            
            # 모델 저장
            self.predictor.save_models()
            
            # 거래 시스템 초기화
            self.trading_system = MLTradingSystem(
                predictor=self.predictor,
                initial_capital=self.initial_capital,
                signal_threshold=0.02,
                confidence_threshold=0.7,
                position_size=0.03,
                stop_loss=-0.03,
                take_profit=0.05,
                max_positions=3
            )
            
            self.last_model_training = datetime.now()
            self.logger.info("✅ Model training completed")
            
        except Exception as e:
            self.logger.error(f"❌ Model training failed: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def collect_latest_data(self) -> Optional[Dict]:
        """
        최신 데이터 수집 및 특징 생성
        
        Returns:
            데이터 딕셔너리 또는 None
        """
        try:
            if self.data_collector is None:
                self.logger.warning("⚠️ Data collector not available. Using dummy data.")
                return None
            
            # 최근 100개 캔들 수집 (60분봉)
            df = self.data_collector.get_candles_minutes(
                market=self.market,
                interval=60,
                count=100
            )
            
            if df.empty:
                self.logger.warning("⚠️ No data collected")
                return None
            
            # 특징 생성
            df_features = self.predictor.feature_engineer.create_all_features(df)
            df_features = df_features.dropna()
            
            if len(df_features) < self.predictor.sequence_length:
                self.logger.warning("⚠️ Insufficient data for prediction")
                return None
            
            # 시퀀스 데이터 준비
            price_data = df_features[['close']].values
            X_lstm, _ = self.predictor.pipeline.create_sequences(
                price_data,
                sequence_length=self.predictor.sequence_length,
                forecast_horizon=1
            )
            
            # ML 특징 준비
            feature_cols = [col for col in df_features.columns 
                           if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            X_ml = df_features[feature_cols].values[self.predictor.sequence_length:]
            
            # 정규화
            X_lstm_scaled = self.predictor.price_scaler.transform(
                X_lstm.reshape(-1, X_lstm.shape[-1])
            ).reshape(X_lstm.shape)
            X_ml_scaled = self.predictor.feature_scaler.transform(X_ml)
            
            current_price = price_data[-1][0]
            
            return {
                'X_lstm': X_lstm_scaled[-1:],
                'X_ml': X_ml_scaled[-1:],
                'current_price': current_price,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Data collection failed: {e}")
            return None
    
    def make_trading_decision(self, data: Dict) -> Optional[Dict]:
        """
        거래 결정
        
        Args:
            data: 최신 데이터
        
        Returns:
            거래 신호 딕셔너리
        """
        try:
            # 가격 예측
            result = self.predictor.predict(
                data['X_lstm'],
                data['X_ml'],
                return_confidence=True
            )
            
            predicted_price = result['predictions'][0]
            confidence = result['confidence'][0]
            current_price = data['current_price']
            
            # 신호 생성
            signal = self.trading_system.generate_signal(
                current_price,
                predicted_price,
                confidence
            )
            
            signal['current_price'] = current_price
            signal['predicted_price'] = predicted_price
            
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Trading decision failed: {e}")
            return None
    
    def execute_trade(self, signal: Dict):
        """
        거래 실행 (시뮬레이션)
        
        Args:
            signal: 거래 신호
        """
        try:
            current_price = signal['current_price']
            timestamp = datetime.now()
            
            # 매수 신호
            if signal['signal'] == 'BUY':
                if len(self.trading_system.positions) < self.trading_system.max_positions:
                    self.trading_system.open_position(signal, current_price, timestamp)
                    self.daily_stats['trades'] += 1
                    
                    self.logger.info(f"📈 BUY executed: {current_price:,.0f} KRW")
                    self.logger.info(f"   Confidence: {signal['confidence']:.2%}")
                    self.logger.info(f"   Reason: {signal['reason']}")
            
            # 기존 포지션 관리
            if len(self.trading_system.positions) > 0:
                # 리스크 관리 (손절/익절)
                self.trading_system.check_risk_management(current_price, timestamp)
                
                # 매도 신호
                if signal['signal'] == 'SELL':
                    for position in self.trading_system.positions[:]:
                        self.trading_system.close_position(
                            position,
                            current_price,
                            timestamp,
                            'SELL signal'
                        )
                        self.daily_stats['trades'] += 1
                        
                        profit = (current_price - position['entry_price']) * position['quantity']
                        self.daily_stats['profit'] += profit
                        
                        if profit > 0:
                            self.daily_stats['win'] += 1
                        else:
                            self.daily_stats['loss'] += 1
                        
                        self.logger.info(f"📉 SELL executed: {current_price:,.0f} KRW")
                        self.logger.info(f"   Profit: {profit:+,.0f} KRW")
            
        except Exception as e:
            self.logger.error(f"❌ Trade execution failed: {e}")
    
    def check_model_retrain(self):
        """모델 재학습 필요 여부 체크"""
        if self.last_model_training is None:
            return False
        
        days_since_training = (datetime.now() - self.last_model_training).days
        
        if days_since_training >= self.model_retrain_days:
            self.logger.info(f"\n🔄 Model retrain required ({days_since_training} days since last training)")
            return True
        
        return False
    
    def print_daily_summary(self):
        """일일 요약 출력"""
        current_date = datetime.now().date()
        
        if self.daily_stats['date'] != current_date:
            # 이전 날짜 요약
            self.logger.info("\n" + "="*80)
            self.logger.info(f"📊 Daily Summary - {self.daily_stats['date']}")
            self.logger.info("="*80)
            self.logger.info(f"Trades: {self.daily_stats['trades']}")
            self.logger.info(f"Profit: {self.daily_stats['profit']:+,.0f} KRW")
            self.logger.info(f"Win: {self.daily_stats['win']} | Loss: {self.daily_stats['loss']}")
            
            if self.daily_stats['trades'] > 0:
                win_rate = self.daily_stats['win'] / self.daily_stats['trades']
                self.logger.info(f"Win Rate: {win_rate:.1%}")
            
            self.logger.info("="*80 + "\n")
            
            # 초기화
            self.daily_stats = {
                'date': current_date,
                'trades': 0,
                'profit': 0,
                'win': 0,
                'loss': 0
            }
    
    def run_cycle(self):
        """한 사이클 실행"""
        try:
            self.logger.info(f"\n⚡ Running cycle - {datetime.now()}")
            
            # 1. 최신 데이터 수집
            data = self.collect_latest_data()
            if data is None:
                self.logger.warning("⚠️ Data collection failed. Skipping cycle.")
                return
            
            # 2. 거래 결정
            signal = self.make_trading_decision(data)
            if signal is None:
                self.logger.warning("⚠️ Trading decision failed. Skipping cycle.")
                return
            
            # 3. 거래 실행
            self.execute_trade(signal)
            
            # 4. 현재 상태 출력
            self.logger.info(f"💰 Current Capital: {self.trading_system.current_capital:,.0f} KRW")
            self.logger.info(f"📊 Open Positions: {len(self.trading_system.positions)}")
            self.logger.info(f"📈 Total Profit: {self.trading_system.total_profit:+,.0f} KRW")
            
            # 오류 카운터 리셋
            self.consecutive_errors = 0
            
        except Exception as e:
            self.consecutive_errors += 1
            self.logger.error(f"❌ Cycle error ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}")
            self.logger.error(traceback.format_exc())
            
            if self.consecutive_errors >= self.max_consecutive_errors:
                self.logger.error("🛑 Too many consecutive errors. Stopping bot.")
                self.stop()
    
    def start(self):
        """봇 시작"""
        try:
            self.logger.info("\n" + "="*80)
            self.logger.info("🚀 Starting Autonomous Trading Bot")
            self.logger.info("="*80)
            
            # 모델 초기화
            if not self.initialize_models():
                self.logger.error("❌ Failed to initialize models. Cannot start.")
                return
            
            self.is_running = True
            
            # 스케줄 설정
            schedule.every().day.at("00:00").do(self.print_daily_summary)
            
            if self.model_retrain_days > 0:
                schedule.every(self.model_retrain_days).days.do(self.train_models)
            
            self.logger.info("✅ Bot started successfully")
            self.logger.info(f"⏰ Running 24/7 - Check interval: {self.check_interval}s")
            self.logger.info("\n💡 Press Ctrl+C to stop\n")
            
            # 메인 루프
            while self.is_running:
                # 스케줄 실행
                schedule.run_pending()
                
                # 거래 사이클 실행
                self.run_cycle()
                
                # 대기
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n⚠️ Keyboard interrupt received")
            self.stop()
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}")
            self.logger.error(traceback.format_exc())
            self.stop()
    
    def stop(self):
        """봇 중지"""
        self.logger.info("\n" + "="*80)
        self.logger.info("🛑 Stopping Autonomous Trading Bot")
        self.logger.info("="*80)
        
        self.is_running = False
        
        # 열린 포지션 정리
        if self.trading_system and len(self.trading_system.positions) > 0:
            self.logger.info(f"Closing {len(self.trading_system.positions)} open positions...")
            # 실제로는 마지막 가격으로 청산
            # for position in self.trading_system.positions[:]:
            #     self.trading_system.close_position(...)
        
        # 최종 요약
        self.print_daily_summary()
        
        if self.trading_system:
            total_return = (
                (self.trading_system.current_capital - self.initial_capital) 
                / self.initial_capital
            )
            
            self.logger.info("\n📊 Final Summary:")
            self.logger.info(f"  Initial Capital: {self.initial_capital:,.0f} KRW")
            self.logger.info(f"  Final Capital: {self.trading_system.current_capital:,.0f} KRW")
            self.logger.info(f"  Total Profit: {self.trading_system.total_profit:+,.0f} KRW")
            self.logger.info(f"  Return: {total_return:+.2%}")
            self.logger.info(f"  Total Trades: {self.trading_system.total_trades}")
            
            if self.trading_system.total_trades > 0:
                win_rate = self.trading_system.winning_trades / self.trading_system.total_trades
                self.logger.info(f"  Win Rate: {win_rate:.1%}")
        
        self.logger.info("\n✅ Bot stopped\n")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous 24/7 Trading Bot')
    parser.add_argument('--market', default='KRW-BTC', help='Trading market (default: KRW-BTC)')
    parser.add_argument('--capital', type=float, default=10_000_000, help='Initial capital (default: 10,000,000)')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--retrain-days', type=int, default=7, help='Model retrain interval in days (default: 7)')
    parser.add_argument('--force-retrain', action='store_true', help='Force model retrain on start')
    
    args = parser.parse_args()
    
    # 봇 생성
    bot = AutonomousTradingBot(
        market=args.market,
        initial_capital=args.capital,
        check_interval=args.interval,
        model_retrain_days=args.retrain_days
    )
    
    # 강제 재학습
    if args.force_retrain:
        print("🔄 Force retraining models...")
        bot.initialize_models(force_retrain=True)
        return
    
    # 봇 시작
    bot.start()


if __name__ == '__main__':
    main()
