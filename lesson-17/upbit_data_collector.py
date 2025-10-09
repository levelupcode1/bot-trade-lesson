"""
upbit_data_collector.py - 업비트 실시간 데이터 수집기

업비트 API를 통해 실시간 가격 데이터를 수집합니다.
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging


class UpbitDataCollector:
    """
    업비트 데이터 수집기
    
    기능:
    - 실시간 가격 조회
    - 캔들 데이터 조회 (일/분/주/월)
    - 호가 정보 조회
    - 체결 내역 조회
    """
    
    def __init__(self):
        """초기화"""
        self.base_url = "https://api.upbit.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UpbitDataCollector/1.0',
            'Accept': 'application/json'
        })
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def get_current_price(self, markets: List[str]) -> Dict:
        """
        현재가 조회
        
        Args:
            markets: 마켓 코드 리스트 (예: ['KRW-BTC', 'KRW-ETH'])
        
        Returns:
            코인별 현재가 정보
        """
        try:
            url = f"{self.base_url}/ticker"
            params = {'markets': ','.join(markets)}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            result = {}
            for item in data:
                result[item['market']] = {
                    'price': item['trade_price'],
                    'change': item['change'],
                    'change_rate': item['change_rate'],
                    'change_price': item['change_price'],
                    'high_price': item['high_price'],
                    'low_price': item['low_price'],
                    'volume': item['acc_trade_volume_24h'],
                    'timestamp': datetime.fromtimestamp(item['timestamp'] / 1000)
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"현재가 조회 오류: {e}")
            return {}
    
    def get_candles_daily(self, market: str, count: int = 100) -> pd.DataFrame:
        """
        일봉 데이터 조회
        
        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (최대 200)
        
        Returns:
            OHLCV 데이터프레임
        """
        try:
            url = f"{self.base_url}/candles/days"
            params = {
                'market': market,
                'count': min(count, 200)
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # 데이터프레임 생성
            df = pd.DataFrame(data)
            
            # 컬럼명 변경
            df = df.rename(columns={
                'candle_date_time_kst': 'datetime',
                'opening_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'trade_price': 'close',
                'candle_acc_trade_volume': 'volume'
            })
            
            # 필요한 컬럼만 선택
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            
            # 시간 순서대로 정렬 (오래된 것부터)
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # datetime을 인덱스로 설정
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"일봉 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_candles_minutes(self, market: str, unit: int = 1, 
                           count: int = 100) -> pd.DataFrame:
        """
        분봉 데이터 조회
        
        Args:
            market: 마켓 코드
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            count: 조회할 캔들 개수
        
        Returns:
            OHLCV 데이터프레임
        """
        try:
            valid_units = [1, 3, 5, 10, 15, 30, 60, 240]
            if unit not in valid_units:
                raise ValueError(f"unit은 {valid_units} 중 하나여야 합니다.")
            
            url = f"{self.base_url}/candles/minutes/{unit}"
            params = {
                'market': market,
                'count': min(count, 200)
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'candle_date_time_kst': 'datetime',
                'opening_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'trade_price': 'close',
                'candle_acc_trade_volume': 'volume'
            })
            
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('datetime').reset_index(drop=True)
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"분봉 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_market_list(self, is_details: bool = False) -> List[Dict]:
        """
        마켓 코드 조회
        
        Args:
            is_details: 상세 정보 포함 여부
        
        Returns:
            마켓 리스트
        """
        try:
            url = f"{self.base_url}/market/all"
            params = {'isDetails': 'true' if is_details else 'false'}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"마켓 리스트 조회 오류: {e}")
            return []
    
    def get_krw_markets(self) -> List[str]:
        """
        원화 마켓 코드 조회
        
        Returns:
            원화 마켓 코드 리스트
        """
        markets = self.get_market_list()
        krw_markets = [m['market'] for m in markets if m['market'].startswith('KRW-')]
        return krw_markets
    
    def get_orderbook(self, markets: List[str]) -> Dict:
        """
        호가 정보 조회
        
        Args:
            markets: 마켓 코드 리스트
        
        Returns:
            호가 정보
        """
        try:
            url = f"{self.base_url}/orderbook"
            params = {'markets': ','.join(markets)}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"호가 조회 오류: {e}")
            return {}
    
    def collect_historical_data(self, market: str, days: int = 100) -> pd.DataFrame:
        """
        과거 데이터 수집 (여러 번 요청하여 많은 데이터 수집)
        
        Args:
            market: 마켓 코드
            days: 수집할 일수
        
        Returns:
            OHLCV 데이터프레임
        """
        all_data = []
        remaining_days = days
        
        while remaining_days > 0:
            count = min(remaining_days, 200)
            
            df = self.get_candles_daily(market, count)
            
            if df.empty:
                break
            
            all_data.append(df)
            remaining_days -= count
            
            # API 호출 제한 방지 (초당 10회)
            time.sleep(0.1)
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.drop_duplicates(subset=['datetime']).sort_values('datetime')
            result = result.reset_index(drop=True)
            return result
        
        return pd.DataFrame()


class RealtimeDataMonitor:
    """
    실시간 데이터 모니터
    
    지정된 간격으로 데이터를 수집하고 콜백 함수를 실행합니다.
    """
    
    def __init__(self, collector: UpbitDataCollector, 
                 market: str, interval: int = 60):
        """
        초기화
        
        Args:
            collector: 데이터 수집기
            market: 모니터링할 마켓
            interval: 수집 간격 (초)
        """
        self.collector = collector
        self.market = market
        self.interval = interval
        self.is_running = False
        
        self.logger = logging.getLogger(__name__)
    
    def start(self, callback=None):
        """
        모니터링 시작
        
        Args:
            callback: 데이터 수집 시 호출할 함수
        """
        self.is_running = True
        self.logger.info(f"실시간 모니터링 시작: {self.market}")
        
        try:
            while self.is_running:
                # 현재가 조회
                current_data = self.collector.get_current_price([self.market])
                
                # 최근 데이터 조회 (분석용)
                historical_data = self.collector.get_candles_daily(
                    self.market, count=100
                )
                
                # 콜백 실행
                if callback and not historical_data.empty:
                    callback(current_data, historical_data)
                
                # 대기
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("모니터링 중지 (사용자 중단)")
            self.is_running = False
        except Exception as e:
            self.logger.error(f"모니터링 오류: {e}")
            self.is_running = False
    
    def stop(self):
        """모니터링 중지"""
        self.is_running = False
        self.logger.info("모니터링 중지")

