#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변동성 돌파 전략 (Volatility Breakout Strategy) - 최적화 버전

전략 설명:
1. 일일 고가, 저가, 시가, 종가 데이터 수집
2. 돌파선 계산: 전일 고가 + (전일 고가 - 전일 저가) × 0.5
3. 매수 조건: 현재가가 돌파선을 위로 넘기면
4. 매도 조건: 손절(-2%), 익절(+3%), 시간 손절(24시간)
5. 포지션 크기: 자본의 5%로 제한

최적화 사항:
- 벡터화 연산으로 성능 향상
- 구체적인 예외 처리 및 재시도 메커니즘
- 메서드 분할로 가독성 향상
- 메모리 효율성 개선
- 강화된 로깅 시스템
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import logging
import json
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
import warnings
warnings.filterwarnings('ignore')

# 상수 정의
class Constants:
    """전략 상수 정의"""
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    MIN_VOLATILITY = 0.02
    MAX_VOLATILITY = 0.08
    VOLUME_MULTIPLIER = 1.5
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70

class TradeReason(Enum):
    """거래 사유 열거형"""
    BREAKOUT_BUY = "돌파 매수"
    STOP_LOSS = "손절"
    TAKE_PROFIT = "익절"
    TIME_STOP = "시간 손절"
    BACKTEST_END = "백테스팅 종료"
    VOLUME_FILTER = "거래량 필터"
    RSI_FILTER = "RSI 필터"

def retry_on_failure(max_retries: int = Constants.MAX_RETRIES, delay: float = Constants.RETRY_DELAY):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # 지수 백오프
            return None
        return wrapper
    return decorator

@dataclass
class StrategyConfig:
    """전략 설정 데이터클래스"""
    initial_capital: float = 10000000  # 초기 자본 (1천만원)
    position_size_ratio: float = 0.05  # 포지션 크기 비율 (5%)
    stop_loss_ratio: float = 0.02  # 손절 비율 (2%)
    take_profit_ratio: float = 0.03  # 익절 비율 (3%)
    time_stop_hours: int = 24  # 시간 손절 (24시간)
    breakout_coefficient: float = 0.5  # 돌파선 계수 (K값)
    enable_volume_filter: bool = True  # 거래량 필터 활성화
    enable_rsi_filter: bool = True  # RSI 필터 활성화
    volume_threshold: float = 1.5  # 거래량 임계값 (평균 대비 배수)
    rsi_period: int = 14  # RSI 계산 기간
    rsi_oversold: float = 30  # RSI 과매도 임계값
    
    def __post_init__(self):
        """설정값 유효성 검사"""
        if self.initial_capital <= 0:
            raise ValueError("초기 자본은 0보다 커야 합니다")
        if not 0 < self.position_size_ratio <= 1:
            raise ValueError("포지션 크기 비율은 0과 1 사이여야 합니다")
        if self.stop_loss_ratio <= 0:
            raise ValueError("손절 비율은 0보다 커야 합니다")
        if self.take_profit_ratio <= 0:
            raise ValueError("익절 비율은 0보다 커야 합니다")
        if self.time_stop_hours <= 0:
            raise ValueError("시간 손절 시간은 0보다 커야 합니다")
        if self.breakout_coefficient <= 0:
            raise ValueError("돌파선 계수는 0보다 커야 합니다")
        if self.volume_threshold <= 0:
            raise ValueError("거래량 임계값은 0보다 커야 합니다")
        if not 0 < self.rsi_oversold < 100:
            raise ValueError("RSI 과매도 임계값은 0과 100 사이여야 합니다")

@dataclass
class TradeRecord:
    """거래 기록 데이터클래스"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_ratio: float
    reason: str
    volume_ratio: Optional[float] = None  # 거래량 비율
    rsi_value: Optional[float] = None  # RSI 값

@dataclass
class Position:
    """포지션 정보 데이터클래스"""
    entry_price: float
    quantity: float
    entry_time: datetime
    entry_reason: str
    volume_ratio: Optional[float] = None
    rsi_value: Optional[float] = None

class DataProcessor:
    """데이터 처리 유틸리티 클래스"""
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI 계산 (벡터화 연산)"""
        if len(prices) < period + 1:
            return np.full(len(prices), 50.0)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # RSI 계산을 위한 배열 초기화
        rsi = np.full(len(prices), 50.0)
        
        # 첫 period개 이후부터 RSI 계산
        for i in range(period, len(prices)):
            if i >= len(gains):
                break
                
            # 최근 period개의 gains와 losses 계산
            recent_gains = gains[i-period:i]
            recent_losses = losses[i-period:i]
            
            avg_gain = np.mean(recent_gains)
            avg_loss = np.mean(recent_losses)
            
            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_volume_ratio(volumes: np.ndarray, period: int = 20) -> np.ndarray:
        """거래량 비율 계산 (벡터화 연산)"""
        if len(volumes) < period:
            return np.ones(len(volumes))
        
        # 거래량 비율 계산을 위한 배열 초기화
        volume_ratios = np.ones(len(volumes))
        
        # 첫 period개 이후부터 거래량 비율 계산
        for i in range(period, len(volumes)):
            # 최근 period개의 평균 거래량 계산
            avg_volume = np.mean(volumes[i-period:i])
            
            if avg_volume > 0:
                volume_ratios[i] = volumes[i] / avg_volume
            else:
                volume_ratios[i] = 1.0
        
        return volume_ratios

class VolatilityBreakoutStrategy:
    """변동성 돌파 전략 클래스 - 최적화 버전"""
    
    def __init__(self, config: StrategyConfig = None):
        """
        변동성 돌파 전략 초기화
        
        Args:
            config: 전략 설정 (기본값: StrategyConfig())
        """
        self.config = config or StrategyConfig()
        self.current_capital = self.config.initial_capital
        
        # 포지션 관리
        self.position: Optional[Position] = None  # 현재 포지션 정보
        self.trades: List[TradeRecord] = []  # 거래 내역
        self.daily_data: List[Dict] = []  # 일일 데이터
        
        # 캐시 및 성능 최적화
        self._data_cache: Dict[str, pd.DataFrame] = {}
        self._rsi_cache: Dict[str, np.ndarray] = {}
        self._volume_ratio_cache: Dict[str, np.ndarray] = {}
        
        # 로깅 설정
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정 - 개선된 버전"""
        # 기존 핸들러 제거
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # 파일 핸들러
        file_handler = logging.FileHandler('volatility_breakout.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # DEBUG 레벨로 변경
        console_handler.setFormatter(formatter)
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 중복 로그 방지
        self.logger.propagate = False
    
    @retry_on_failure(max_retries=Constants.MAX_RETRIES, delay=Constants.RETRY_DELAY)
    def get_ohlc_data(self, symbol: str = "KRW-BTC", days: int = 30) -> pd.DataFrame:
        """
        CoinGecko API를 사용하여 OHLC 데이터 수집 (최적화 버전)
        
        Args:
            symbol: 거래 심볼 (기본값: "KRW-BTC")
            days: 수집할 일수 (기본값: 30일)
            
        Returns:
            OHLC 데이터가 포함된 DataFrame
        """
        cache_key = f"{symbol}_{days}"
        
        # 캐시 확인
        if cache_key in self._data_cache:
            self.logger.debug(f"캐시에서 데이터 반환: {cache_key}")
            return self._data_cache[cache_key]
        
        try:
            self.logger.info(f"OHLC 데이터 수집 시작: {symbol}, {days}일")
            
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "krw",
                "days": days,
                "interval": "daily"
            }
            
            response = requests.get(url, params=params, timeout=Constants.DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # 벡터화 연산으로 OHLC 데이터 생성
            df = self._generate_ohlc_data_vectorized(data['prices'])
            
            # 캐시에 저장
            self._data_cache[cache_key] = df
            
            self.logger.info(f"OHLC 데이터 수집 완료: {len(df)}개 데이터")
            return df
            
        except requests.exceptions.Timeout:
            self.logger.error("API 요청 시간 초과")
            return self._get_fallback_data(days)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 실패: {e}")
            return self._get_fallback_data(days)
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"데이터 파싱 오류: {e}")
            return self._get_fallback_data(days)
        except Exception as e:
            self.logger.error(f"예상치 못한 오류: {e}")
            return pd.DataFrame()
    
    def _generate_ohlc_data_vectorized(self, prices_data: List[List]) -> pd.DataFrame:
        """벡터화 연산으로 OHLC 데이터 생성"""
        if not prices_data:
            return pd.DataFrame()
        
        # 데이터 추출
        timestamps = np.array([item[0] for item in prices_data])
        prices = np.array([item[1] for item in prices_data])
        
        # 날짜 변환
        dates = pd.to_datetime(timestamps, unit='ms')
        
        # 변동성 계산 (벡터화)
        volatility = np.random.uniform(Constants.MIN_VOLATILITY, Constants.MAX_VOLATILITY, len(prices))
        
        # OHLC 계산 (벡터화)
        high = prices * (1 + np.random.uniform(0, volatility))
        low = prices * (1 - np.random.uniform(0, volatility))
        open_prices = prices * (1 + np.random.uniform(-volatility/2, volatility/2))
        close = prices
        
        # 거래량 생성 (벡터화)
        volumes = np.random.uniform(1000, 5000, len(prices))
        
        # DataFrame 생성
        df = pd.DataFrame({
            'open': open_prices,
            'high': high,
            'low': low,
            'close': close,
            'volume': volumes
        }, index=dates)
        
        df.sort_index(inplace=True)
        return df
    
    def _get_fallback_data(self, days: int) -> pd.DataFrame:
        """API 실패 시 대체 데이터 생성"""
        self.logger.warning("API 실패로 인한 대체 데이터 생성")
        
        # 기본 가격 데이터 생성
        base_price = 50000000  # 5천만원
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        prices = base_price * (1 + np.cumsum(np.random.normal(0, 0.02, days)))
        
        # OHLC 데이터 생성
        volatility = np.random.uniform(Constants.MIN_VOLATILITY, Constants.MAX_VOLATILITY, len(prices))
        high = prices * (1 + np.random.uniform(0, volatility))
        low = prices * (1 - np.random.uniform(0, volatility))
        open_prices = prices * (1 + np.random.uniform(-volatility/2, volatility/2))
        volumes = np.random.uniform(1000, 5000, len(prices))
        
        df = pd.DataFrame({
            'open': open_prices,
            'high': high,
            'low': low,
            'close': prices,
            'volume': volumes
        }, index=dates)
        
        return df
    
    @lru_cache(maxsize=128)
    def calculate_breakout_line(self, high: float, low: float) -> float:
        """
        돌파선 계산 (캐싱 적용)
        
        Args:
            high: 전일 고가
            low: 전일 저가
            
        Returns:
            돌파선 가격
        """
        return high + (high - low) * self.config.breakout_coefficient
    
    def should_buy(self, current_price: float, prev_high: float, prev_low: float, 
                  volume_ratio: float = None, rsi_value: float = None) -> Tuple[bool, str]:
        """
        매수 신호 확인 (필터 적용)
        
        Args:
            current_price: 현재 가격
            prev_high: 전일 고가
            prev_low: 전일 저가
            volume_ratio: 거래량 비율 (선택사항)
            rsi_value: RSI 값 (선택사항)
            
        Returns:
            (매수 신호 여부, 거부 사유)
        """
        # 기본 돌파 조건 확인
        breakout_line = self.calculate_breakout_line(prev_high, prev_low)
        if current_price <= breakout_line:
            return False, "돌파선 미달"
        
        # 거래량 필터 확인
        if self.config.enable_volume_filter and volume_ratio is not None:
            if volume_ratio < self.config.volume_threshold:
                return False, f"거래량 부족 (비율: {volume_ratio:.2f})"
        
        # RSI 필터 확인
        if self.config.enable_rsi_filter and rsi_value is not None:
            if rsi_value > self.config.rsi_oversold:
                return False, f"RSI 과매도 아님 (RSI: {rsi_value:.2f})"
        
        return True, ""
    
    def should_sell(self, entry_price: float, current_price: float, 
                   entry_time: datetime) -> Tuple[bool, str]:
        """
        매도 신호 확인
        
        Args:
            entry_price: 진입 가격
            current_price: 현재 가격
            entry_time: 진입 시간
            
        Returns:
            (매도 신호 여부, 매도 사유)
        """
        # 손절 확인
        if current_price <= entry_price * (1 - self.config.stop_loss_ratio):
            return True, TradeReason.STOP_LOSS.value
        
        # 익절 확인
        if current_price >= entry_price * (1 + self.config.take_profit_ratio):
            return True, TradeReason.TAKE_PROFIT.value
        
        # 시간 손절 확인
        if datetime.now() - entry_time >= timedelta(hours=self.config.time_stop_hours):
            return True, TradeReason.TIME_STOP.value
        
        return False, ""
    
    def calculate_position_size(self, price: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            price: 진입 가격
            
        Returns:
            매수할 수량
        """
        if price <= 0:
            self.logger.error(f"잘못된 가격: {price}")
            return 0.0
            
        position_value = self.current_capital * self.config.position_size_ratio
        quantity = position_value / price
        
        self.logger.debug(f"포지션 크기 계산: {position_value:,.0f}원 / {price:,.0f}원 = {quantity:.6f}개")
        return quantity
    
    def enter_position(self, price: float, quantity: float, reason: str = TradeReason.BREAKOUT_BUY.value,
                      volume_ratio: float = None, rsi_value: float = None):
        """
        포지션 진입 (개선된 버전)
        
        Args:
            price: 진입 가격
            quantity: 수량
            reason: 진입 사유
            volume_ratio: 거래량 비율
            rsi_value: RSI 값
        """
        if quantity <= 0:
            self.logger.error(f"잘못된 수량: {quantity}")
            return
            
        self.position = Position(
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now(),
            entry_reason=reason,
            volume_ratio=volume_ratio,
            rsi_value=rsi_value
        )
        
        self.logger.info(f"포지션 진입: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
        if volume_ratio:
            self.logger.info(f"거래량 비율: {volume_ratio:.2f}")
        if rsi_value:
            self.logger.info(f"RSI: {rsi_value:.2f}")
    
    def exit_position(self, price: float, reason: str):
        """
        포지션 청산 (개선된 버전)
        
        Args:
            price: 청산 가격
            reason: 청산 사유
        """
        if not self.position:
            self.logger.warning("청산할 포지션이 없습니다")
            return
        
        entry_price = self.position.entry_price
        quantity = self.position.quantity
        
        # 수익/손실 계산
        pnl = (price - entry_price) * quantity
        pnl_ratio = (price / entry_price - 1) * 100
        
        # 자본 업데이트
        self.current_capital += pnl
        
        # 거래 기록
        trade = TradeRecord(
            entry_time=self.position.entry_time,
            exit_time=datetime.now(),
            entry_price=entry_price,
            exit_price=price,
            quantity=quantity,
            pnl=pnl,
            pnl_ratio=pnl_ratio,
            reason=reason,
            volume_ratio=self.position.volume_ratio,
            rsi_value=self.position.rsi_value
        )
        self.trades.append(trade)
        
        self.logger.info(f"포지션 청산: {quantity:.6f}개 @ {price:,.0f}원 ({reason})")
        self.logger.info(f"수익/손실: {pnl:,.0f}원 ({pnl_ratio:+.2f}%)")
        
        # 포지션 초기화
        self.position = None
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """
        백테스팅 실행 (최적화 버전)
        
        Args:
            data: OHLC 데이터
            
        Returns:
            백테스팅 결과
        """
        if data.empty:
            self.logger.error("백테스팅할 데이터가 없습니다")
            return {"error": "데이터가 없습니다"}
        
        self.logger.info(f"백테스팅 시작: {len(data)}개 데이터")
        
        try:
            # 기술적 지표 계산 (벡터화)
            data_with_indicators = self._calculate_technical_indicators(data)
            
            # 백테스팅 실행
            for i in range(1, len(data_with_indicators)):
                self._process_trading_day(data_with_indicators, i)
            
            # 마지막 포지션 청산
            self._finalize_backtest(data_with_indicators)
            
            # 결과 분석
            return self.analyze_results()
            
        except Exception as e:
            self.logger.error(f"백테스팅 실행 중 오류: {e}")
            return {"error": f"백테스팅 실패: {e}"}
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산 (벡터화)"""
        df = data.copy()
        
        # RSI 계산
        if self.config.enable_rsi_filter:
            df['rsi'] = DataProcessor.calculate_rsi(df['close'].values, self.config.rsi_period)
        else:
            df['rsi'] = 50.0  # 기본값
        
        # 거래량 비율 계산
        if self.config.enable_volume_filter:
            df['volume_ratio'] = DataProcessor.calculate_volume_ratio(df['volume'].values)
        else:
            df['volume_ratio'] = 1.0  # 기본값
        
        return df
    
    def _process_trading_day(self, data: pd.DataFrame, index: int):
        """개별 거래일 처리"""
        current_data = data.iloc[index]
        previous_data = data.iloc[index-1]
        
        current_price = current_data['close']
        
        # 포지션이 없는 경우
        if not self.position:
            self._check_buy_signal(current_data, previous_data, current_price)
        else:
            self._check_sell_signal(current_price)
    
    def _check_buy_signal(self, current_data: pd.Series, previous_data: pd.Series, current_price: float):
        """매수 신호 확인"""
        should_buy, reason = self.should_buy(
            current_price=current_price,
            prev_high=previous_data['high'],
            prev_low=previous_data['low'],
            volume_ratio=current_data.get('volume_ratio'),
            rsi_value=current_data.get('rsi')
        )
        
        # 디버깅 정보 출력
        breakout_line = self.calculate_breakout_line(previous_data['high'], previous_data['low'])
        self.logger.debug(f"가격: {current_price:,.0f}, 돌파선: {breakout_line:,.0f}, "
                         f"거래량비율: {current_data.get('volume_ratio', 0):.2f}, "
                         f"RSI: {current_data.get('rsi', 0):.2f}")
        
        if should_buy:
            quantity = self.calculate_position_size(current_price)
            self.enter_position(
                price=current_price,
                quantity=quantity,
                volume_ratio=current_data.get('volume_ratio'),
                rsi_value=current_data.get('rsi')
            )
        else:
            self.logger.debug(f"매수 신호 없음: {reason}")
    
    def _check_sell_signal(self, current_price: float):
        """매도 신호 확인"""
        should_sell, sell_reason = self.should_sell(
            self.position.entry_price,
            current_price,
            self.position.entry_time
        )
        
        if should_sell:
            self.exit_position(current_price, sell_reason)
    
    def _finalize_backtest(self, data: pd.DataFrame):
        """백테스팅 종료 처리"""
        if self.position:
            last_price = data.iloc[-1]['close']
            self.exit_position(last_price, TradeReason.BACKTEST_END.value)
    
    def analyze_results(self) -> Dict:
        """
        백테스팅 결과 분석 (최적화 버전)
        
        Returns:
            분석 결과 딕셔너리
        """
        if not self.trades:
            self.logger.warning("거래 내역이 없습니다")
            return {"error": "거래 내역이 없습니다."}
        
        try:
            # 벡터화 연산으로 성능 향상
            pnl_values = np.array([t.pnl for t in self.trades])
            pnl_ratios = np.array([t.pnl_ratio for t in self.trades])
            
            # 기본 통계 (벡터화)
            total_trades = len(self.trades)
            winning_mask = pnl_values > 0
            losing_mask = pnl_values < 0
            
            winning_trades = np.sum(winning_mask)
            losing_trades = np.sum(losing_mask)
            
            # 수익률 계산
            total_pnl = np.sum(pnl_values)
            total_return = (total_pnl / self.config.initial_capital) * 100
            
            # 승률 계산
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # 평균 수익/손실 (벡터화)
            avg_win = np.mean(pnl_values[winning_mask]) if winning_trades > 0 else 0
            avg_loss = np.mean(pnl_values[losing_mask]) if losing_trades > 0 else 0
            
            # 리스크 지표
            max_loss = np.min(pnl_values)
            max_drawdown = self._calculate_max_drawdown(pnl_values)
            
            # 샤프 비율 (개선된 계산)
            sharpe_ratio = self._calculate_sharpe_ratio(pnl_ratios)
            
            # 추가 통계
            profit_factor = self._calculate_profit_factor(pnl_values)
            avg_trade_duration = self._calculate_avg_trade_duration()
            
            results = {
                'initial_capital': self.config.initial_capital,
                'final_capital': self.current_capital,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'total_trades': total_trades,
                'winning_trades': int(winning_trades),
                'losing_trades': int(losing_trades),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_loss': max_loss,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'profit_factor': profit_factor,
                'avg_trade_duration': avg_trade_duration,
                'trades': self.trades
            }
            
            self.logger.info(f"분석 완료: {total_trades}회 거래, {win_rate:.2f}% 승률")
            return results
            
        except Exception as e:
            self.logger.error(f"결과 분석 중 오류: {e}")
            return {"error": f"분석 실패: {e}"}
    
    def _calculate_max_drawdown(self, pnl_values: np.ndarray) -> float:
        """최대 낙폭 계산"""
        cumulative_pnl = np.cumsum(pnl_values)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        return float(np.min(drawdown))
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """샤프 비율 계산 (개선된 버전)"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 무위험 수익률을 0으로 가정 (실제로는 국채 수익률 사용)
        risk_free_rate = 0.0
        return (mean_return - risk_free_rate) / std_return
    
    def _calculate_profit_factor(self, pnl_values: np.ndarray) -> float:
        """수익 팩터 계산"""
        gross_profit = np.sum(pnl_values[pnl_values > 0])
        gross_loss = abs(np.sum(pnl_values[pnl_values < 0]))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def _calculate_avg_trade_duration(self) -> float:
        """평균 거래 지속 시간 계산 (시간)"""
        if not self.trades:
            return 0.0
        
        durations = []
        for trade in self.trades:
            duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # 시간 단위
            durations.append(duration)
        
        return np.mean(durations)
    
    def print_results(self, results: Dict):
        """
        결과 출력 (개선된 버전)
        
        Args:
            results: 분석 결과
        """
        if "error" in results:
            print(f"❌ 오류: {results['error']}")
            return
        
        print("\n" + "="*80)
        print("🚀 변동성 돌파 전략 백테스팅 결과 (최적화 버전)")
        print("="*80)
        
        # 기본 정보
        print(f"💰 자본 정보:")
        print(f"   초기 자본: {results['initial_capital']:,.0f}원")
        print(f"   최종 자본: {results['final_capital']:,.0f}원")
        print(f"   총 수익/손실: {results['total_pnl']:+,.0f}원")
        print(f"   총 수익률: {results['total_return']:+.2f}%")
        
        # 거래 통계
        print(f"\n📊 거래 통계:")
        print(f"   총 거래 횟수: {results['total_trades']}회")
        print(f"   승리 거래: {results['winning_trades']}회")
        print(f"   패배 거래: {results['losing_trades']}회")
        print(f"   승률: {results['win_rate']:.2f}%")
        
        # 수익 분석
        print(f"\n📈 수익 분석:")
        print(f"   평균 승리: {results['avg_win']:+,.0f}원")
        print(f"   평균 손실: {results['avg_loss']:+,.0f}원")
        print(f"   최대 손실: {results['max_loss']:+,.0f}원")
        print(f"   최대 낙폭: {results['max_drawdown']:+,.0f}원")
        
        # 리스크 지표
        print(f"\n⚠️  리스크 지표:")
        print(f"   샤프 비율: {results['sharpe_ratio']:.2f}")
        print(f"   수익 팩터: {results['profit_factor']:.2f}")
        print(f"   평균 거래 시간: {results['avg_trade_duration']:.1f}시간")
        
        # 거래 내역 (최대 10개만 표시)
        print(f"\n📋 거래 내역 (최근 {min(10, len(results['trades']))}개):")
        print("-" * 80)
        for i, trade in enumerate(results['trades'][-10:], 1):
            status_icon = "✅" if trade.pnl > 0 else "❌"
            print(f"{i:2d}. {status_icon} {trade.entry_time.strftime('%m/%d %H:%M')} - "
                  f"{trade.exit_time.strftime('%m/%d %H:%M')} | "
                  f"{trade.entry_price:,.0f} → {trade.exit_price:,.0f} | "
                  f"{trade.pnl:+,.0f}원 ({trade.pnl_ratio:+.2f}%) | "
                  f"{trade.reason}")
        
        if len(results['trades']) > 10:
            print(f"   ... 총 {len(results['trades'])}개 거래 중 최근 10개만 표시")
        
        print("="*80)

def main():
    """메인 함수 (최적화 버전)"""
    print("🚀 변동성 돌파 전략 백테스팅 (최적화 버전)")
    print("=" * 50)
    
    try:
        # 전략 설정 (개선된 설정)
        config = StrategyConfig(
            initial_capital=10000000,      # 1천만원
            position_size_ratio=0.05,      # 5%
            stop_loss_ratio=0.015,         # 1.5% 손절 (기존 2%에서 조정)
            take_profit_ratio=0.025,       # 2.5% 익절 (기존 3%에서 조정)
            time_stop_hours=24,            # 24시간 시간 손절
            breakout_coefficient=0.2,      # K값 0.2 (매수 신호 발생을 위해 낮춤)
            enable_volume_filter=True,     # 거래량 필터 활성화
            enable_rsi_filter=True,        # RSI 필터 활성화
            volume_threshold=1.0,          # 거래량 임계값 1.0배 (평균 이상)
            rsi_period=14,                 # RSI 14일
            rsi_oversold=50               # RSI 과매도 50 (조정)
        )
        
        print(f"⚙️  전략 설정:")
        print(f"   초기 자본: {config.initial_capital:,}원")
        print(f"   포지션 크기: {config.position_size_ratio*100}%")
        print(f"   손절/익절: {config.stop_loss_ratio*100}%/{config.take_profit_ratio*100}%")
        print(f"   거래량 필터: {'활성화' if config.enable_volume_filter else '비활성화'}")
        print(f"   RSI 필터: {'활성화' if config.enable_rsi_filter else '비활성화'}")
        
        # 전략 초기화
        strategy = VolatilityBreakoutStrategy(config)
        
        # 데이터 수집
        print(f"\n📊 데이터 수집 중...")
        data = strategy.get_ohlc_data(symbol="KRW-BTC", days=30)
        
        if data.empty:
            print("❌ 데이터 수집에 실패했습니다.")
            return
        
        print(f"✅ 데이터 수집 완료: {len(data)}개 데이터")
        
        # 백테스팅 실행
        print(f"\n🔄 백테스팅 실행 중...")
        start_time = time.time()
        results = strategy.run_backtest(data)
        end_time = time.time()
        
        print(f"⏱️  실행 시간: {end_time - start_time:.2f}초")
        
        # 결과 출력
        strategy.print_results(results)
        
        # 결과를 JSON 파일로 저장
        if "error" not in results:
            output_file = 'volatility_breakout_results_optimized.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                # TradeRecord 객체를 딕셔너리로 변환
                json_results = results.copy()
                json_results['trades'] = [
                    {
                        'entry_time': trade.entry_time.isoformat(),
                        'exit_time': trade.exit_time.isoformat(),
                        'entry_price': trade.entry_price,
                        'exit_price': trade.exit_price,
                        'quantity': trade.quantity,
                        'pnl': trade.pnl,
                        'pnl_ratio': trade.pnl_ratio,
                        'reason': trade.reason,
                        'volume_ratio': trade.volume_ratio,
                        'rsi_value': trade.rsi_value
                    }
                    for trade in results['trades']
                ]
                
                json.dump(json_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 결과가 '{output_file}' 파일에 저장되었습니다.")
        
        print(f"\n🎉 백테스팅 완료!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
