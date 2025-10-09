"""
data_pipeline.py - 머신러닝 학습용 데이터 파이프라인

업비트 API에서 데이터를 수집하고 ML 학습에 적합한 형태로 전처리합니다.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lesson-17'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Optional, List
import logging
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import pickle

try:
    from upbit_data_collector import UpbitDataCollector
except ImportError:
    print("경고: lesson-17/upbit_data_collector.py를 찾을 수 없습니다.")
    print("업비트 데이터 수집기를 사용할 수 없습니다.")


class DataPipeline:
    """
    ML 학습용 데이터 파이프라인
    
    기능:
    - 업비트 API 데이터 수집
    - 데이터 전처리 및 정규화
    - 학습/검증/테스트 데이터 분할
    - 시계열 시퀀스 생성
    """
    
    def __init__(self, data_dir: str = './data'):
        """
        초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 업비트 데이터 수집기
        try:
            self.collector = UpbitDataCollector()
        except:
            self.collector = None
            print("업비트 데이터 수집기 초기화 실패")
        
        # 스케일러
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = StandardScaler()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_historical_data(
        self,
        market: str = 'KRW-BTC',
        interval: str = '60',  # 60분봉
        days: int = 180  # 6개월
    ) -> pd.DataFrame:
        """
        과거 데이터 수집
        
        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            interval: 캔들 간격 ('1', '60', '240', 'day')
            days: 수집 기간 (일)
        
        Returns:
            OHLCV 데이터프레임
        """
        self.logger.info(f"{market} {days}일 데이터 수집 시작...")
        
        if self.collector is None:
            # 더미 데이터 생성 (테스트용)
            self.logger.warning("업비트 수집기 없음. 더미 데이터 생성")
            return self._generate_dummy_data(days, interval)
        
        try:
            # 업비트에서 데이터 수집
            if interval in ['1', '60', '240']:
                # 분봉 데이터
                df = self.collector.get_candles_minutes(
                    market=market,
                    interval=int(interval),
                    count=200  # 최대 200개씩
                )
                
                # 더 많은 데이터 수집 (반복)
                all_data = []
                required_candles = int((days * 24 * 60) / int(interval))
                
                for i in range(0, required_candles, 200):
                    batch = self.collector.get_candles_minutes(
                        market=market,
                        interval=int(interval),
                        count=min(200, required_candles - i)
                    )
                    if not batch.empty:
                        all_data.append(batch)
                    
                    if len(all_data) >= required_candles // 200:
                        break
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                    df = df.drop_duplicates(subset=['timestamp'])
                    df = df.sort_values('timestamp')
            
            elif interval == 'day':
                # 일봉 데이터
                df = self.collector.get_candles_daily(
                    market=market,
                    count=min(days, 200)
                )
            else:
                raise ValueError(f"지원하지 않는 간격: {interval}")
            
            self.logger.info(f"데이터 수집 완료: {len(df)}개 캔들")
            return df
        
        except Exception as e:
            self.logger.error(f"데이터 수집 오류: {e}")
            return self._generate_dummy_data(days, interval)
    
    def _generate_dummy_data(
        self, 
        days: int, 
        interval: str
    ) -> pd.DataFrame:
        """테스트용 더미 데이터 생성"""
        if interval == 'day':
            periods = days
            freq = 'D'
        elif interval == '240':
            periods = days * 6  # 4시간봉
            freq = '4H'
        elif interval == '60':
            periods = days * 24  # 1시간봉
            freq = '1H'
        else:
            periods = days * 24 * 60  # 1분봉
            freq = '1min'
        
        dates = pd.date_range(
            end=datetime.now(),
            periods=periods,
            freq=freq
        )
        
        # 랜덤 워크 기반 가격 생성
        np.random.seed(42)
        initial_price = 50000000  # 5천만원
        returns = np.random.normal(0.0001, 0.02, len(dates))
        prices = initial_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            'low': prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
            'close': prices,
            'volume': np.random.uniform(100, 1000, len(dates))
        })
        
        return df
    
    def preprocess_data(
        self,
        df: pd.DataFrame,
        target_col: str = 'close'
    ) -> pd.DataFrame:
        """
        데이터 전처리
        
        Args:
            df: 원본 데이터프레임
            target_col: 예측 대상 컬럼
        
        Returns:
            전처리된 데이터프레임
        """
        self.logger.info("데이터 전처리 시작...")
        
        df = df.copy()
        
        # 결측치 처리
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 중복 제거
        if 'timestamp' in df.columns:
            df = df.drop_duplicates(subset=['timestamp'])
        
        # 정렬
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 기본 특징 추가
        if target_col in df.columns:
            # 수익률 계산
            df['returns'] = df[target_col].pct_change()
            
            # 로그 수익률
            df['log_returns'] = np.log(df[target_col] / df[target_col].shift(1))
        
        # 결측치 다시 제거 (계산 과정에서 생성된 것)
        df = df.dropna()
        
        self.logger.info(f"전처리 완료: {len(df)}개 행")
        return df
    
    def create_sequences(
        self,
        data: np.ndarray,
        sequence_length: int = 60,
        forecast_horizon: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        시계열 시퀀스 생성
        
        Args:
            data: 입력 데이터 (n_samples, n_features)
            sequence_length: 시퀀스 길이 (과거 몇 개 사용)
            forecast_horizon: 예측 시점 (미래 몇 개 후)
        
        Returns:
            X: 입력 시퀀스 (n_samples, sequence_length, n_features)
            y: 타겟 값 (n_samples,)
        """
        X, y = [], []
        
        for i in range(len(data) - sequence_length - forecast_horizon + 1):
            # 입력: 과거 sequence_length 시점
            X.append(data[i:(i + sequence_length)])
            # 타겟: forecast_horizon 시점 후의 값
            y.append(data[i + sequence_length + forecast_horizon - 1, 0])
        
        return np.array(X), np.array(y)
    
    def split_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        시계열 데이터 분할 (순차 분할)
        
        Args:
            X: 입력 데이터
            y: 타겟 데이터
            train_ratio: 학습 데이터 비율
            val_ratio: 검증 데이터 비율
        
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        n_samples = len(X)
        
        train_end = int(n_samples * train_ratio)
        val_end = int(n_samples * (train_ratio + val_ratio))
        
        X_train = X[:train_end]
        y_train = y[:train_end]
        
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        self.logger.info(f"데이터 분할 완료:")
        self.logger.info(f"  학습: {len(X_train)} ({len(X_train)/n_samples*100:.1f}%)")
        self.logger.info(f"  검증: {len(X_val)} ({len(X_val)/n_samples*100:.1f}%)")
        self.logger.info(f"  테스트: {len(X_test)} ({len(X_test)/n_samples*100:.1f}%)")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def normalize_data(
        self,
        train_data: np.ndarray,
        val_data: Optional[np.ndarray] = None,
        test_data: Optional[np.ndarray] = None,
        scaler_type: str = 'minmax'
    ) -> Tuple:
        """
        데이터 정규화
        
        Args:
            train_data: 학습 데이터
            val_data: 검증 데이터
            test_data: 테스트 데이터
            scaler_type: 스케일러 타입 ('minmax' 또는 'standard')
        
        Returns:
            정규화된 데이터들
        """
        if scaler_type == 'minmax':
            scaler = MinMaxScaler()
        elif scaler_type == 'standard':
            scaler = StandardScaler()
        else:
            raise ValueError(f"지원하지 않는 스케일러: {scaler_type}")
        
        # 학습 데이터로 fit
        original_shape = train_data.shape
        if len(original_shape) == 3:
            # LSTM용 3D 데이터 (samples, timesteps, features)
            train_data_2d = train_data.reshape(-1, original_shape[-1])
            scaler.fit(train_data_2d)
            train_scaled = scaler.transform(train_data_2d).reshape(original_shape)
        else:
            scaler.fit(train_data)
            train_scaled = scaler.transform(train_data)
        
        result = [train_scaled]
        
        # 검증 데이터 변환
        if val_data is not None:
            if len(original_shape) == 3:
                val_shape = val_data.shape
                val_data_2d = val_data.reshape(-1, val_shape[-1])
                val_scaled = scaler.transform(val_data_2d).reshape(val_shape)
            else:
                val_scaled = scaler.transform(val_data)
            result.append(val_scaled)
        
        # 테스트 데이터 변환
        if test_data is not None:
            if len(original_shape) == 3:
                test_shape = test_data.shape
                test_data_2d = test_data.reshape(-1, test_shape[-1])
                test_scaled = scaler.transform(test_data_2d).reshape(test_shape)
            else:
                test_scaled = scaler.transform(test_data)
            result.append(test_scaled)
        
        # 스케일러 저장
        result.append(scaler)
        
        return tuple(result)
    
    def save_scaler(self, scaler, filename: str = 'scaler.pkl'):
        """스케일러 저장"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(scaler, f)
        self.logger.info(f"스케일러 저장: {filepath}")
    
    def load_scaler(self, filename: str = 'scaler.pkl'):
        """스케일러 로드"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'rb') as f:
            scaler = pickle.load(f)
        self.logger.info(f"스케일러 로드: {filepath}")
        return scaler
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """데이터 저장"""
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath, index=False)
        self.logger.info(f"데이터 저장: {filepath}")
    
    def load_data(self, filename: str) -> pd.DataFrame:
        """데이터 로드"""
        filepath = os.path.join(self.data_dir, filename)
        df = pd.read_csv(filepath)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        self.logger.info(f"데이터 로드: {filepath}")
        return df


if __name__ == '__main__':
    # 사용 예시
    pipeline = DataPipeline()
    
    # 1. 데이터 수집
    print("\n1. 데이터 수집")
    df = pipeline.collect_historical_data(
        market='KRW-BTC',
        interval='60',
        days=180
    )
    print(f"수집된 데이터: {len(df)}개")
    print(df.head())
    
    # 2. 전처리
    print("\n2. 데이터 전처리")
    df_processed = pipeline.preprocess_data(df)
    print(f"전처리된 데이터: {len(df_processed)}개")
    
    # 3. 시퀀스 생성
    print("\n3. 시퀀스 생성")
    data = df_processed[['close']].values
    X, y = pipeline.create_sequences(data, sequence_length=60, forecast_horizon=1)
    print(f"입력 shape: {X.shape}, 타겟 shape: {y.shape}")
    
    # 4. 데이터 분할
    print("\n4. 데이터 분할")
    X_train, X_val, X_test, y_train, y_val, y_test = pipeline.split_data(X, y)
    
    # 5. 정규화
    print("\n5. 데이터 정규화")
    X_train_scaled, X_val_scaled, X_test_scaled, scaler = pipeline.normalize_data(
        X_train, X_val, X_test
    )
    print("정규화 완료")
    
    # 6. 저장
    print("\n6. 데이터 저장")
    pipeline.save_data(df_processed, 'btc_processed.csv')
    pipeline.save_scaler(scaler, 'price_scaler.pkl')
    print("저장 완료")

