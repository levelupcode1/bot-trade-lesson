"""
feature_engineering.py - 기술적 지표 기반 특징 엔지니어링

가격 데이터에서 다양한 기술적 지표와 특징을 생성합니다.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import pandas_ta as ta
except ImportError:
    print("경고: pandas_ta가 설치되지 않았습니다. 일부 지표를 사용할 수 없습니다.")
    ta = None


class FeatureEngineer:
    """
    기술적 지표 기반 특징 생성기
    
    기능:
    - 30-40개 기술적 지표 계산
    - 가격 기반 특징
    - 거래량 기반 특징
    - 시간 기반 특징
    """
    
    def __init__(self):
        """초기화"""
        self.feature_names = []
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 특징 생성
        
        Args:
            df: OHLCV 데이터프레임
        
        Returns:
            특징이 추가된 데이터프레임
        """
        df = df.copy()
        
        # 1. 가격 기반 특징
        df = self.create_price_features(df)
        
        # 2. 기술적 지표
        df = self.create_technical_indicators(df)
        
        # 3. 거래량 특징
        df = self.create_volume_features(df)
        
        # 4. 시간 특징
        if 'timestamp' in df.columns:
            df = self.create_time_features(df)
        
        # 5. 상호작용 특징
        df = self.create_interaction_features(df)
        
        # 결측치 처리
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 특징 이름 저장
        self.feature_names = [col for col in df.columns if col not in 
                             ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    def create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """가격 기반 특징 생성"""
        # 수익률
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 가격 변화
        df['price_change'] = df['close'] - df['close'].shift(1)
        df['price_change_pct'] = df['price_change'] / df['close'].shift(1) * 100
        
        # 고가/저가 비율
        df['high_low_ratio'] = df['high'] / df['low']
        df['high_close_ratio'] = df['high'] / df['close']
        df['low_close_ratio'] = df['low'] / df['close']
        
        # 시가/종가 비율
        df['open_close_ratio'] = df['open'] / df['close']
        
        # 변동성 (고가-저가)
        df['hl_volatility'] = (df['high'] - df['low']) / df['close']
        
        # 갭 (전일 종가 대비 시가)
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        
        # 이동평균
        for period in [5, 10, 20, 50]:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}']
        
        # 지수 이동평균
        for period in [12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        return df
    
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 생성"""
        
        # RSI (Relative Strength Index)
        df['rsi_14'] = self.calculate_rsi(df['close'], period=14)
        df['rsi_7'] = self.calculate_rsi(df['close'], period=7)
        
        # MACD
        macd, signal, hist = self.calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        # Bollinger Bands
        bb_middle, bb_upper, bb_lower = self.calculate_bollinger_bands(df['close'])
        df['bb_middle'] = bb_middle
        df['bb_upper'] = bb_upper
        df['bb_lower'] = bb_lower
        df['bb_width'] = (bb_upper - bb_lower) / bb_middle
        df['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # ATR (Average True Range)
        df['atr_14'] = self.calculate_atr(df, period=14)
        
        # Stochastic Oscillator
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(df)
        
        # CCI (Commodity Channel Index)
        df['cci_20'] = self.calculate_cci(df, period=20)
        
        # Williams %R
        df['williams_r'] = self.calculate_williams_r(df, period=14)
        
        # ROC (Rate of Change)
        df['roc_10'] = self.calculate_roc(df['close'], period=10)
        
        # Momentum
        df['momentum_10'] = df['close'] - df['close'].shift(10)
        
        return df
    
    def create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """거래량 기반 특징 생성"""
        if 'volume' not in df.columns:
            return df
        
        # 거래량 변화율
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # OBV (On-Balance Volume)
        df['obv'] = self.calculate_obv(df)
        df['obv_ma'] = df['obv'].rolling(window=20).mean()
        
        # 거래량 가중 가격
        df['vwap'] = (df['close'] * df['volume']).rolling(window=20).sum() / \
                     df['volume'].rolling(window=20).sum()
        
        # 금액 (가격 * 거래량)
        df['money_flow'] = df['close'] * df['volume']
        df['money_flow_ratio'] = df['money_flow'] / df['money_flow'].rolling(window=20).mean()
        
        return df
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """시간 기반 특징 생성"""
        if 'timestamp' in df.columns:
            # 요일 (0=월요일, 6=일요일)
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            # 시간
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            
            # 주기성 인코딩 (사인/코사인)
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        return df
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """상호작용 특징 생성"""
        # RSI와 볼린저 밴드 위치의 상호작용
        if 'rsi_14' in df.columns and 'bb_position' in df.columns:
            df['rsi_bb_interaction'] = df['rsi_14'] * df['bb_position']
        
        # MACD와 RSI의 상호작용
        if 'macd' in df.columns and 'rsi_14' in df.columns:
            df['macd_rsi_interaction'] = df['macd'] * df['rsi_14']
        
        # 거래량과 가격 변화의 상호작용
        if 'volume_ratio' in df.columns and 'returns' in df.columns:
            df['volume_return_interaction'] = df['volume_ratio'] * df['returns']
        
        return df
    
    # ===== 지표 계산 메서드 =====
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> tuple:
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std: float = 2.0
    ) -> tuple:
        """볼린저 밴드 계산"""
        middle = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return middle, upper, lower
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """ATR 계산"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def calculate_stochastic(
        self,
        df: pd.DataFrame,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> tuple:
        """Stochastic Oscillator 계산"""
        lowest_low = df['low'].rolling(window=period).min()
        highest_high = df['high'].rolling(window=period).max()
        
        stoch = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
        stoch_k = stoch.rolling(window=smooth_k).mean()
        stoch_d = stoch_k.rolling(window=smooth_d).mean()
        
        return stoch_k, stoch_d
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """CCI 계산"""
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - sma) / (0.015 * mad)
        return cci
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R 계산"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return williams_r
    
    def calculate_roc(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """ROC 계산"""
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """OBV 계산"""
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return obv
    
    def get_feature_importance_names(self) -> List[str]:
        """특징 이름 리스트 반환"""
        return self.feature_names


if __name__ == '__main__':
    # 사용 예시
    from data_pipeline import DataPipeline
    
    # 1. 데이터 수집
    print("1. 데이터 수집")
    pipeline = DataPipeline()
    df = pipeline.collect_historical_data(
        market='KRW-BTC',
        interval='60',
        days=180
    )
    
    # 2. 특징 생성
    print("\n2. 특징 생성")
    fe = FeatureEngineer()
    df_features = fe.create_all_features(df)
    
    print(f"\n생성된 특징 개수: {len(fe.feature_names)}")
    print("\n특징 목록:")
    for i, name in enumerate(fe.feature_names, 1):
        print(f"{i:2d}. {name}")
    
    # 3. 데이터 확인
    print(f"\n데이터 shape: {df_features.shape}")
    print("\n데이터 샘플:")
    print(df_features.head())
    
    # 4. 결측치 확인
    missing = df_features.isnull().sum()
    if missing.sum() > 0:
        print("\n결측치:")
        print(missing[missing > 0])
    else:
        print("\n결측치 없음")

