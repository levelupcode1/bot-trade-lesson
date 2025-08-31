#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 암호화폐 데이터 수집 및 통합 시스템
여러 거래소의 데이터를 실시간으로 합치고 기술적 지표를 계산합니다.
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics
import numpy as np
from dataclasses import dataclass
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_data.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class CryptoPrice:
    """암호화폐 가격 데이터 구조"""
    exchange: str
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'exchange': self.exchange,
            'symbol': self.symbol,
            'price': self.price,
            'volume_24h': self.volume_24h,
            'change_24h': self.change_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'timestamp': self.timestamp.isoformat()
        }

class ExchangeDataCollector:
    """거래소별 데이터 수집기"""
    
    def __init__(self, exchange_name: str):
        """초기화"""
        self.exchange_name = exchange_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def collect_bitcoin_data(self) -> Optional[CryptoPrice]:
        """비트코인 데이터 수집 (거래소별 구현)"""
        if self.exchange_name == 'upbit':
            return self._collect_upbit_data()
        elif self.exchange_name == 'bithumb':
            return self._collect_bithumb_data()
        elif self.exchange_name == 'coinone':
            return self._collect_coinone_data()
        else:
            logging.warning(f"지원하지 않는 거래소: {self.exchange_name}")
            return None
    
    def _collect_upbit_data(self) -> Optional[CryptoPrice]:
        """Upbit 데이터 수집"""
        try:
            url = "https://api.upbit.com/v1/ticker"
            params = {"markets": "KRW-BTC"}
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    ticker = data[0]
                    return CryptoPrice(
                        exchange="Upbit",
                        symbol="BTC/KRW",
                        price=float(ticker['trade_price']),
                        volume_24h=float(ticker['acc_trade_volume_24h']),
                        change_24h=float(ticker['signed_change_rate']) * 100,
                        high_24h=float(ticker['high_price']),
                        low_24h=float(ticker['low_price']),
                        timestamp=datetime.now()
                    )
            else:
                logging.error(f"Upbit API 오류: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Upbit 데이터 수집 실패: {e}")
            
        return None
    
    def _collect_bithumb_data(self) -> Optional[CryptoPrice]:
        """Bithumb 데이터 수집"""
        try:
            url = "https://api.bithumb.com/public/ticker/BTC_KRW"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '0000':
                    ticker = data['data']
                    return CryptoPrice(
                        exchange="Bithumb",
                        symbol="BTC/KRW",
                        price=float(ticker['closing_price']),
                        volume_24h=float(ticker['acc_trade_value_24h']),
                        change_24h=float(ticker['fluctate_24h']),
                        high_24h=float(ticker['max_price']),
                        low_24h=float(ticker['min_price']),
                        timestamp=datetime.now()
                    )
            else:
                logging.error(f"Bithumb API 오류: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Bithumb 데이터 수집 실패: {e}")
            
        return None
    
    def _collect_coinone_data(self) -> Optional[CryptoPrice]:
        """Coinone 데이터 수집"""
        try:
            url = "https://api.coinone.co.kr/public/v2/markets_status"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['result'] == 'success':
                    # Coinone은 현재 가격만 제공
                    return CryptoPrice(
                        exchange="Coinone",
                        symbol="BTC/KRW",
                        price=0.0,  # Coinone API로는 실시간 가격을 가져올 수 없음
                        volume_24h=0.0,
                        change_24h=0.0,
                        high_24h=0.0,
                        low_24h=0.0,
                        timestamp=datetime.now()
                    )
            else:
                logging.error(f"Coinone API 오류: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Coinone 데이터 수집 실패: {e}")
            
        return None

class DataAggregator:
    """데이터 통합 및 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.price_history: List[CryptoPrice] = []
        self.aggregated_data: Dict[str, Any] = {}
        
    def add_price_data(self, price_data: CryptoPrice):
        """가격 데이터 추가"""
        self.price_history.append(price_data)
        
        # 최근 100개 데이터만 유지
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
    
    def aggregate_current_data(self, current_data: List[CryptoPrice]) -> Dict[str, Any]:
        """현재 데이터 통합"""
        if not current_data:
            return {}
        
        # 가격 데이터 추출
        prices = [data.price for data in current_data if data.price > 0]
        volumes = [data.volume_24h for data in current_data if data.volume_24h > 0]
        changes = [data.change_24h for data in current_data if data.change_24h != 0]
        
        if not prices:
            return {}
        
        # 통합 통계 계산
        aggregated = {
            'timestamp': datetime.now().isoformat(),
            'total_exchanges': len(current_data),
            'valid_exchanges': len(prices),
            'price_stats': {
                'current_prices': {data.exchange: data.price for data in current_data if data.price > 0},
                'weighted_average': self._calculate_weighted_average(prices, volumes) if volumes else statistics.mean(prices),
                'simple_average': statistics.mean(prices),
                'median': statistics.median(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'price_spread': max(prices) - min(prices),
                'price_spread_percent': ((max(prices) - min(prices)) / min(prices)) * 100
            },
            'volume_stats': {
                'total_volume': sum(volumes) if volumes else 0,
                'average_volume': statistics.mean(volumes) if volumes else 0,
                'volume_distribution': {data.exchange: data.volume_24h for data in current_data if data.volume_24h > 0}
            },
            'change_stats': {
                'average_change': statistics.mean(changes) if changes else 0,
                'change_distribution': {data.exchange: data.change_24h for data in current_data if data.change_24h != 0}
            },
            'market_analysis': self._analyze_market_conditions(prices, changes)
        }
        
        self.aggregated_data = aggregated
        return aggregated
    
    def _calculate_weighted_average(self, prices: List[float], volumes: List[float]) -> float:
        """거래량 가중 평균 계산"""
        if len(prices) != len(volumes) or not volumes:
            return statistics.mean(prices)
        
        total_volume = sum(volumes)
        if total_volume == 0:
            return statistics.mean(prices)
        
        weighted_sum = sum(p * v for p, v in zip(prices, volumes))
        return weighted_sum / total_volume
    
    def _analyze_market_conditions(self, prices: List[float], changes: List[float]) -> Dict[str, Any]:
        """시장 상황 분석"""
        if not prices:
            return {}
        
        # 가격 변동성 계산
        price_volatility = statistics.stdev(prices) if len(prices) > 1 else 0
        price_volatility_percent = (price_volatility / statistics.mean(prices)) * 100 if prices else 0
        
        # 시장 방향성 분석
        if changes:
            positive_changes = len([c for c in changes if c > 0])
            negative_changes = len([c for c in changes if c < 0])
            market_sentiment = "상승" if positive_changes > negative_changes else "하락" if negative_changes > positive_changes else "중립"
        else:
            market_sentiment = "중립"
        
        return {
            'volatility': {
                'absolute': price_volatility,
                'percentage': price_volatility_percent,
                'level': self._classify_volatility(price_volatility_percent)
            },
            'sentiment': market_sentiment,
            'price_trend': self._analyze_price_trend(prices),
            'market_health': self._assess_market_health(prices, changes)
        }
    
    def _classify_volatility(self, volatility_percent: float) -> str:
        """변동성 수준 분류"""
        if volatility_percent < 1:
            return "낮음"
        elif volatility_percent < 5:
            return "보통"
        elif volatility_percent < 10:
            return "높음"
        else:
            return "매우 높음"
    
    def _analyze_price_trend(self, prices: List[float]) -> str:
        """가격 추세 분석"""
        if len(prices) < 2:
            return "데이터 부족"
        
        # 최근 5개 데이터로 단기 추세 분석
        recent_prices = prices[-5:] if len(prices) >= 5 else prices
        
        if len(recent_prices) >= 2:
            trend = recent_prices[-1] - recent_prices[0]
            if trend > 0:
                return "상승"
            elif trend < 0:
                return "하락"
            else:
                return "횡보"
        
        return "분석 불가"
    
    def _assess_market_health(self, prices: List[float], changes: List[float]) -> str:
        """시장 건강도 평가"""
        if not prices or not changes:
            return "평가 불가"
        
        # 가격 안정성과 변동성 기반 평가
        price_stability = 1 - (statistics.stdev(prices) / statistics.mean(prices)) if prices else 0
        change_consistency = 1 - (statistics.stdev(changes) / abs(statistics.mean(changes))) if changes and statistics.mean(changes) != 0 else 0
        
        overall_health = (price_stability + change_consistency) / 2
        
        if overall_health > 0.7:
            return "건강"
        elif overall_health > 0.4:
            return "보통"
        else:
            return "불안정"

class TechnicalIndicatorCalculator:
    """기술적 지표 계산 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """단순이동평균 (Simple Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i-period+1:i+1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """지수가동평균 (Exponential Moving Average) 계산"""
        if len(prices) < period:
            return []
        
        ema_values = []
        multiplier = 2 / (period + 1)
        
        # 첫 번째 EMA는 SMA로 계산
        first_ema = sum(prices[:period]) / period
        ema_values.append(first_ema)
        
        # 나머지 EMA 계산
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """RSI (Relative Strength Index) 계산"""
        if len(prices) < period + 1:
            return []
        
        # 가격 변화 계산
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]
        
        rsi_values = []
        
        # 첫 번째 RSI 계산
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # 나머지 RSI 계산
        for i in range(period, len(changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """볼린저 밴드 계산"""
        if len(prices) < period:
            return [], [], []
        
        sma_values = self.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i, sma in enumerate(sma_values):
            start_idx = i
            end_idx = start_idx + period
            if end_idx > len(prices):
                break
            
            period_prices = prices[start_idx:end_idx]
            std = statistics.stdev(period_prices) if len(period_prices) > 1 else 0
            
            upper = sma + (std_dev * std)
            lower = sma - (std_dev * std)
            
            upper_band.append(upper)
            lower_band.append(lower)
        
        return sma_values, upper_band, lower_band

class CryptoDataSystem:
    """암호화폐 데이터 시스템 메인 클래스"""
    
    def __init__(self):
        """초기화"""
        self.exchanges = ['upbit', 'bithumb', 'coinone']
        self.collectors = {name: ExchangeDataCollector(name) for name in self.exchanges}
        self.aggregator = DataAggregator()
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.is_running = False
        self.collection_thread = None
        
    def start_data_collection(self, interval: int = 60):
        """데이터 수집 시작"""
        if self.is_running:
            logging.info("데이터 수집이 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._data_collection_worker, args=(interval,), daemon=True)
        self.collection_thread.start()
        logging.info(f"데이터 수집이 시작되었습니다. (간격: {interval}초)")
    
    def stop_data_collection(self):
        """데이터 수집 중지"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logging.info("데이터 수집이 중지되었습니다.")
    
    def _data_collection_worker(self, interval: int):
        """데이터 수집 작업자"""
        while self.is_running:
            try:
                # 모든 거래소에서 데이터 수집
                current_data = []
                for name, collector in self.collectors.items():
                    try:
                        price_data = collector.collect_bitcoin_data()
                        if price_data:
                            current_data.append(price_data)
                            self.aggregator.add_price_data(price_data)
                    except Exception as e:
                        logging.error(f"{name} 데이터 수집 오류: {e}")
                
                # 데이터 통합 및 분석
                if current_data:
                    aggregated = self.aggregator.aggregate_current_data(current_data)
                    self._display_aggregated_data(aggregated)
                    
                    # 기술적 지표 계산 및 표시
                    self._calculate_and_display_indicators()
                
                # 대기
                time.sleep(interval)
                
            except Exception as e:
                logging.error(f"데이터 수집 작업자 오류: {e}")
                time.sleep(10)  # 오류 시 10초 후 재시도
    
    def _display_aggregated_data(self, aggregated: Dict[str, Any]):
        """통합된 데이터 표시"""
        if not aggregated:
            return
        
        print("\n" + "=" * 80)
        print(f"📊 실시간 암호화폐 데이터 통합 결과 ({aggregated['timestamp']})")
        print("=" * 80)
        
        # 거래소별 현재 가격
        print("🏪 거래소별 현재 가격:")
        for exchange, price in aggregated['price_stats']['current_prices'].items():
            print(f"  • {exchange}: {price:,.0f}원")
        
        # 통합 통계
        print(f"\n📈 통합 통계:")
        print(f"  • 가중 평균 가격: {aggregated['price_stats']['weighted_average']:,.0f}원")
        print(f"  • 단순 평균 가격: {aggregated['price_stats']['simple_average']:,.0f}원")
        print(f"  • 최고가: {aggregated['price_stats']['max_price']:,.0f}원")
        print(f"  • 최저가: {aggregated['price_stats']['min_price']:,.0f}원")
        print(f"  • 가격 스프레드: {aggregated['price_stats']['price_spread']:,.0f}원 ({aggregated['price_stats']['price_spread_percent']:.2f}%)")
        
        # 시장 분석
        market = aggregated['market_analysis']
        print(f"\n🎯 시장 분석:")
        print(f"  • 변동성: {market['volatility']['level']} ({market['volatility']['percentage']:.2f}%)")
        print(f"  • 시장 심리: {market['sentiment']}")
        print(f"  • 가격 추세: {market['price_trend']}")
        print(f"  • 시장 건강도: {market['market_health']}")
    
    def _calculate_and_display_indicators(self):
        """기술적 지표 계산 및 표시"""
        if len(self.aggregator.price_history) < 20:
            return
        
        # 최근 가격 데이터 추출
        recent_prices = [data.price for data in self.aggregator.price_history[-50:]]
        
        print(f"\n📊 기술적 지표 (최근 {len(recent_prices)}개 데이터):")
        
        # 이동평균
        sma_20 = self.technical_calculator.calculate_sma(recent_prices, 20)
        if sma_20:
            print(f"  • 20일 단순이동평균: {sma_20[-1]:,.0f}원")
        
        ema_20 = self.technical_calculator.calculate_ema(recent_prices, 20)
        if ema_20:
            print(f"  • 20일 지수가동평균: {ema_20[-1]:,.0f}원")
        
        # RSI
        rsi = self.technical_calculator.calculate_rsi(recent_prices, 14)
        if rsi:
            current_rsi = rsi[-1]
            rsi_status = "과매수" if current_rsi > 70 else "과매도" if current_rsi < 30 else "보통"
            print(f"  • RSI(14): {current_rsi:.2f} ({rsi_status})")
        
        # 볼린저 밴드
        sma, upper, lower = self.technical_calculator.calculate_bollinger_bands(recent_prices, 20)
        if sma and upper and lower:
            current_price = recent_prices[-1]
            current_sma = sma[-1]
            current_upper = upper[-1]
            current_lower = lower[-1]
            
            print(f"  • 볼린저 밴드:")
            print(f"    - 중간선 (20일 SMA): {current_sma:,.0f}원")
            print(f"    - 상단 밴드: {current_upper:,.0f}원")
            print(f"    - 하단 밴드: {current_lower:,.0f}원")
            
            # 현재 가격 위치
            if current_price > current_upper:
                print(f"    - 현재 가격: 상단 밴드 위 (과매수 구간)")
            elif current_price < current_lower:
                print(f"    - 현재 가격: 하단 밴드 아래 (과매도 구간)")
            else:
                print(f"    - 현재 가격: 밴드 내부 (정상 구간)")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'is_running': self.is_running,
            'total_data_points': len(self.aggregator.price_history),
            'last_update': self.aggregator.aggregated_data.get('timestamp', 'N/A'),
            'active_exchanges': len([c for c in self.collectors.values() if c]),
            'system_health': '정상' if self.is_running else '중지'
        }

def main():
    """메인 함수"""
    print("🚀 실시간 암호화폐 데이터 수집 및 통합 시스템")
    print("=" * 80)
    
    # 시스템 초기화
    crypto_system = CryptoDataSystem()
    
    try:
        print("\n📋 시스템 옵션:")
        print("1. 실시간 데이터 수집 시작 (1분 간격)")
        print("2. 실시간 데이터 수집 시작 (5분 간격)")
        print("3. 시스템 상태 조회")
        print("4. 종료")
        
        while True:
            choice = input("\n선택 (1-4): ").strip()
            
            if choice == "1":
                print("\n🔄 1분 간격으로 데이터 수집을 시작합니다...")
                crypto_system.start_data_collection(60)
                
            elif choice == "2":
                print("\n🔄 5분 간격으로 데이터 수집을 시작합니다...")
                crypto_system.start_data_collection(300)
                
            elif choice == "3":
                status = crypto_system.get_system_status()
                print(f"\n📊 시스템 상태:")
                print(f"  • 실행 상태: {status['is_running']}")
                print(f"  • 총 데이터 포인트: {status['total_data_points']}")
                print(f"  • 마지막 업데이트: {status['last_update']}")
                print(f"  • 활성 거래소: {status['active_exchanges']}")
                print(f"  • 시스템 건강도: {status['system_health']}")
                
            elif choice == "4":
                print("\n⏹️ 시스템을 종료합니다...")
                crypto_system.stop_data_collection()
                break
                
            else:
                print("❌ 잘못된 선택입니다. 1-4 중에서 선택하세요.")
                
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단되었습니다.")
        crypto_system.stop_data_collection()
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 오류가 발생했습니다: {e}")
        crypto_system.stop_data_collection()
    finally:
        print("\n👋 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
