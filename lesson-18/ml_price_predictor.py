"""
ml_price_predictor.py - 통합 ML 가격 예측 시스템

LSTM과 앙상블 모델을 통합하여 가격을 예측합니다.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import logging
import os

from data_pipeline import DataPipeline
from feature_engineering import FeatureEngineer
from models.lstm_model import LSTMModel
from models.ensemble_model import EnsembleModel


class MLPricePredictor:
    """
    통합 ML 가격 예측 시스템
    
    기능:
    - 데이터 수집 및 전처리
    - 특징 생성
    - LSTM + 앙상블 모델 학습
    - 다중 모델 예측 통합
    - 신뢰도 기반 예측
    """
    
    def __init__(
        self,
        market: str = 'KRW-BTC',
        sequence_length: int = 60,
        forecast_horizon: int = 1,
        model_weights: Dict[str, float] = None
    ):
        """
        초기화
        
        Args:
            market: 마켓 코드
            sequence_length: LSTM 시퀀스 길이
            forecast_horizon: 예측 시점 (몇 시간 후)
            model_weights: 모델별 가중치
        """
        self.market = market
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        
        # 모델 가중치 (LSTM, RF, XGB)
        self.model_weights = model_weights or {
            'lstm': 0.6,
            'rf': 0.2,
            'xgb': 0.2
        }
        
        # 컴포넌트 초기화
        self.pipeline = DataPipeline()
        self.feature_engineer = FeatureEngineer()
        self.lstm_model = None
        self.ensemble_model = None
        
        # 스케일러
        self.price_scaler = None
        self.feature_scaler = None
        
        # 특징 이름
        self.feature_names = []
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def prepare_data(
        self,
        interval: str = '60',
        days: int = 180
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        데이터 준비
        
        Args:
            interval: 캔들 간격
            days: 수집 기간
        
        Returns:
            X_train_lstm, X_train_ml, X_val_lstm, X_val_ml, X_test_lstm, X_test_ml,
            y_train, y_val, y_test
        """
        self.logger.info("="*60)
        self.logger.info("데이터 준비 시작")
        self.logger.info("="*60)
        
        # 1. 데이터 수집
        self.logger.info(f"\n1. {self.market} 데이터 수집 ({days}일)")
        df = self.pipeline.collect_historical_data(
            market=self.market,
            interval=interval,
            days=days
        )
        
        # 2. 특징 생성
        self.logger.info("\n2. 특징 생성")
        df_features = self.feature_engineer.create_all_features(df)
        self.feature_names = self.feature_engineer.get_feature_importance_names()
        self.logger.info(f"생성된 특징 개수: {len(self.feature_names)}")
        
        # 3. 결측치 제거
        df_features = df_features.dropna()
        self.logger.info(f"최종 데이터 개수: {len(df_features)}")
        
        # 4. LSTM용 시퀀스 데이터 준비
        self.logger.info("\n3. LSTM용 데이터 준비")
        price_data = df_features[['close']].values
        X_lstm, y = self.pipeline.create_sequences(
            price_data,
            sequence_length=self.sequence_length,
            forecast_horizon=self.forecast_horizon
        )
        
        # 5. 머신러닝용 특징 데이터 준비
        self.logger.info("\n4. 머신러닝용 데이터 준비")
        feature_cols = [col for col in df_features.columns 
                       if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # 시퀀스와 맞추기 위해 앞부분 제거
        X_ml = df_features[feature_cols].values[self.sequence_length + self.forecast_horizon - 1:]
        
        # 길이 맞추기
        min_length = min(len(X_lstm), len(X_ml), len(y))
        X_lstm = X_lstm[:min_length]
        X_ml = X_ml[:min_length]
        y = y[:min_length]
        
        # 6. 데이터 분할
        self.logger.info("\n5. 데이터 분할")
        n = len(X_lstm)
        train_end = int(n * 0.7)
        val_end = int(n * 0.85)
        
        X_train_lstm = X_lstm[:train_end]
        X_val_lstm = X_lstm[train_end:val_end]
        X_test_lstm = X_lstm[val_end:]
        
        X_train_ml = X_ml[:train_end]
        X_val_ml = X_ml[train_end:val_end]
        X_test_ml = X_ml[val_end:]
        
        y_train = y[:train_end]
        y_val = y[train_end:val_end]
        y_test = y[val_end:]
        
        self.logger.info(f"  학습: {len(X_train_lstm)}")
        self.logger.info(f"  검증: {len(X_val_lstm)}")
        self.logger.info(f"  테스트: {len(X_test_lstm)}")
        
        # 7. 정규화
        self.logger.info("\n6. 데이터 정규화")
        X_train_lstm, X_val_lstm, X_test_lstm, self.price_scaler = \
            self.pipeline.normalize_data(X_train_lstm, X_val_lstm, X_test_lstm, 'minmax')
        
        X_train_ml, X_val_ml, X_test_ml, self.feature_scaler = \
            self.pipeline.normalize_data(X_train_ml, X_val_ml, X_test_ml, 'standard')
        
        # 타겟 정규화 (예측 시 역변환 필요)
        y_train_2d = y_train.reshape(-1, 1)
        y_val_2d = y_val.reshape(-1, 1)
        y_test_2d = y_test.reshape(-1, 1)
        
        from sklearn.preprocessing import MinMaxScaler
        y_scaler = MinMaxScaler()
        y_train = y_scaler.fit_transform(y_train_2d).flatten()
        y_val = y_scaler.transform(y_val_2d).flatten()
        y_test = y_scaler.transform(y_test_2d).flatten()
        
        self.y_scaler = y_scaler
        
        self.logger.info("데이터 준비 완료\n")
        
        return (X_train_lstm, X_train_ml, X_val_lstm, X_val_ml, 
                X_test_lstm, X_test_ml, y_train, y_val, y_test)
    
    def train_models(
        self,
        X_train_lstm: np.ndarray,
        X_train_ml: np.ndarray,
        X_val_lstm: np.ndarray,
        X_val_ml: np.ndarray,
        y_train: np.ndarray,
        y_val: np.ndarray,
        lstm_epochs: int = 50,
        lstm_batch_size: int = 32
    ):
        """
        모델 학습
        
        Args:
            X_train_lstm: LSTM 학습 데이터
            X_train_ml: ML 학습 데이터
            X_val_lstm: LSTM 검증 데이터
            X_val_ml: ML 검증 데이터
            y_train: 학습 타겟
            y_val: 검증 타겟
            lstm_epochs: LSTM 에폭 수
            lstm_batch_size: LSTM 배치 크기
        """
        self.logger.info("="*60)
        self.logger.info("모델 학습 시작")
        self.logger.info("="*60)
        
        # 1. LSTM 모델 학습
        self.logger.info("\n1. LSTM 모델 학습")
        n_features = X_train_lstm.shape[2]
        self.lstm_model = LSTMModel(
            sequence_length=self.sequence_length,
            n_features=n_features,
            lstm_units=[128, 64, 32],
            dropout_rate=0.2
        )
        
        self.lstm_model.train(
            X_train_lstm, y_train,
            X_val_lstm, y_val,
            epochs=lstm_epochs,
            batch_size=lstm_batch_size,
            verbose=1
        )
        
        # 2. 앙상블 모델 학습
        self.logger.info("\n2. 앙상블 모델 학습")
        self.ensemble_model = EnsembleModel(
            ensemble_weights=(0.5, 0.5)
        )
        
        self.ensemble_model.train(
            X_train_ml, y_train,
            X_val_ml, y_val
        )
        
        self.logger.info("\n모델 학습 완료\n")
    
    def predict(
        self,
        X_lstm: np.ndarray,
        X_ml: np.ndarray,
        return_confidence: bool = True
    ) -> Dict:
        """
        가격 예측
        
        Args:
            X_lstm: LSTM 입력 데이터
            X_ml: ML 입력 데이터
            return_confidence: 신뢰도 반환 여부
        
        Returns:
            예측 결과 딕셔너리
        """
        if self.lstm_model is None or self.ensemble_model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        # 각 모델 예측
        lstm_pred = self.lstm_model.predict(X_lstm)
        rf_pred = self.ensemble_model.predict(X_ml, use_ensemble=False)  # RF만
        xgb_pred = self.ensemble_model.xgb_model.predict(X_ml)  # XGB만
        
        # 가중 평균
        final_pred = (
            lstm_pred * self.model_weights['lstm'] +
            rf_pred * self.model_weights['rf'] +
            xgb_pred * self.model_weights['xgb']
        )
        
        # 역정규화
        final_pred_2d = final_pred.reshape(-1, 1)
        final_pred_original = self.y_scaler.inverse_transform(final_pred_2d).flatten()
        
        result = {
            'predictions': final_pred_original,
            'lstm_pred': self.y_scaler.inverse_transform(lstm_pred.reshape(-1, 1)).flatten(),
            'rf_pred': self.y_scaler.inverse_transform(rf_pred.reshape(-1, 1)).flatten(),
            'xgb_pred': self.y_scaler.inverse_transform(xgb_pred.reshape(-1, 1)).flatten()
        }
        
        if return_confidence:
            # 신뢰도 계산 (예측 일치도 기반)
            all_preds = np.array([
                result['lstm_pred'],
                result['rf_pred'],
                result['xgb_pred']
            ])
            
            # 표준편차가 작을수록 신뢰도 높음
            std = np.std(all_preds, axis=0)
            mean_pred = np.mean(all_preds, axis=0)
            cv = std / (np.abs(mean_pred) + 1e-10)  # 변동계수
            
            # 신뢰도 (0~1)
            confidence = 1.0 / (1.0 + cv)
            result['confidence'] = confidence
        
        return result
    
    def evaluate(
        self,
        X_test_lstm: np.ndarray,
        X_test_ml: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        모델 평가
        
        Args:
            X_test_lstm: LSTM 테스트 데이터
            X_test_ml: ML 테스트 데이터
            y_test: 테스트 타겟 (정규화된 값)
        
        Returns:
            평가 지표
        """
        self.logger.info("="*60)
        self.logger.info("모델 평가")
        self.logger.info("="*60)
        
        # 예측
        result = self.predict(X_test_lstm, X_test_ml)
        predictions = result['predictions']
        
        # 실제 값 역정규화
        y_test_2d = y_test.reshape(-1, 1)
        y_test_original = self.y_scaler.inverse_transform(y_test_2d).flatten()
        
        # 지표 계산
        mse = np.mean((y_test_original - predictions) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_test_original - predictions))
        mape = np.mean(np.abs((y_test_original - predictions) / y_test_original)) * 100
        
        # 방향 정확도
        direction_actual = np.sign(np.diff(y_test_original))
        direction_pred = np.sign(np.diff(predictions))
        direction_accuracy = np.mean(direction_actual == direction_pred) * 100
        
        metrics = {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'direction_accuracy': direction_accuracy
        }
        
        self.logger.info(f"\n최종 통합 모델 성능:")
        self.logger.info(f"  RMSE: {rmse:,.2f}")
        self.logger.info(f"  MAE: {mae:,.2f}")
        self.logger.info(f"  MAPE: {mape:.2f}%")
        self.logger.info(f"  방향 정확도: {direction_accuracy:.2f}%")
        
        return metrics
    
    def save_models(self, model_dir: str = './models'):
        """모델 저장"""
        os.makedirs(model_dir, exist_ok=True)
        
        if self.lstm_model:
            self.lstm_model.save_model(f'{model_dir}/lstm_model.h5')
        
        if self.ensemble_model:
            self.ensemble_model.save_models(
                rf_path=f'{model_dir}/rf_model.pkl',
                xgb_path=f'{model_dir}/xgb_model.pkl'
            )
        
        # 스케일러 저장
        self.pipeline.save_scaler(self.price_scaler, 'price_scaler.pkl')
        self.pipeline.save_scaler(self.feature_scaler, 'feature_scaler.pkl')
        self.pipeline.save_scaler(self.y_scaler, 'y_scaler.pkl')
        
        self.logger.info("모든 모델 저장 완료")
    
    def load_models(self, model_dir: str = './models'):
        """모델 로드"""
        if self.lstm_model:
            self.lstm_model.load_model(f'{model_dir}/lstm_model.h5')
        
        if self.ensemble_model:
            self.ensemble_model.load_models(
                rf_path=f'{model_dir}/rf_model.pkl',
                xgb_path=f'{model_dir}/xgb_model.pkl'
            )
        
        # 스케일러 로드
        self.price_scaler = self.pipeline.load_scaler('price_scaler.pkl')
        self.feature_scaler = self.pipeline.load_scaler('feature_scaler.pkl')
        self.y_scaler = self.pipeline.load_scaler('y_scaler.pkl')
        
        self.logger.info("모든 모델 로드 완료")


if __name__ == '__main__':
    # 사용 예시
    print("통합 ML 가격 예측 시스템 테스트\n")
    
    # 예측 시스템 초기화
    predictor = MLPricePredictor(
        market='KRW-BTC',
        sequence_length=60,
        forecast_horizon=1
    )
    
    # 데이터 준비
    (X_train_lstm, X_train_ml, X_val_lstm, X_val_ml,
     X_test_lstm, X_test_ml, y_train, y_val, y_test) = predictor.prepare_data(
        interval='60',
        days=180
    )
    
    # 모델 학습
    predictor.train_models(
        X_train_lstm, X_train_ml,
        X_val_lstm, X_val_ml,
        y_train, y_val,
        lstm_epochs=30,
        lstm_batch_size=32
    )
    
    # 평가
    metrics = predictor.evaluate(X_test_lstm, X_test_ml, y_test)
    
    # 예측 샘플
    print("\n예측 샘플:")
    result = predictor.predict(X_test_lstm[:5], X_test_ml[:5])
    print(f"예측값: {result['predictions']}")
    print(f"신뢰도: {result['confidence']}")
    
    # 모델 저장
    print("\n모델 저장...")
    predictor.save_models()

