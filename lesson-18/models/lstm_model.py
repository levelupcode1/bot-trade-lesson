"""
lstm_model.py - LSTM 딥러닝 모델

시계열 가격 데이터를 학습하여 미래 가격을 예측합니다.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import os
import logging

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, callbacks
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    TF_AVAILABLE = True
except ImportError:
    print("경고: TensorFlow가 설치되지 않았습니다.")
    print("pip install tensorflow 를 실행하세요.")
    tf = None
    keras = None
    Sequential = None
    load_model = None
    LSTM = None
    Dense = None
    Dropout = None
    BatchNormalization = None
    EarlyStopping = None
    ReduceLROnPlateau = None
    ModelCheckpoint = None
    TF_AVAILABLE = False


class LSTMModel:
    """
    LSTM 기반 가격 예측 모델
    
    기능:
    - 시계열 데이터 학습
    - 미래 가격 예측
    - 모델 저장/로드
    - 조기 종료 및 학습률 스케줄링
    """
    
    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 1,
        lstm_units: list = [128, 64, 32],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001
    ):
        """
        초기화
        
        Args:
            sequence_length: 입력 시퀀스 길이
            n_features: 특징 개수
            lstm_units: LSTM 레이어 유닛 수 리스트
            dropout_rate: 드롭아웃 비율
            learning_rate: 학습률
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow가 설치되지 않았습니다. pip install tensorflow 를 실행하세요.")
        
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.history = None
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def build_model(self):
        """
        LSTM 모델 구축
        
        Returns:
            컴파일된 Keras 모델
        """
        self.logger.info("LSTM 모델 구축 중...")
        
        model = Sequential(name='LSTM_PricePredictor')
        
        # 첫 번째 LSTM 레이어
        model.add(LSTM(
            units=self.lstm_units[0],
            return_sequences=True if len(self.lstm_units) > 1 else False,
            input_shape=(self.sequence_length, self.n_features),
            name='lstm_1'
        ))
        model.add(BatchNormalization(name='bn_1'))
        model.add(Dropout(self.dropout_rate, name='dropout_1'))
        
        # 추가 LSTM 레이어들
        for i, units in enumerate(self.lstm_units[1:], start=2):
            return_seq = i < len(self.lstm_units)
            model.add(LSTM(
                units=units,
                return_sequences=return_seq,
                name=f'lstm_{i}'
            ))
            model.add(BatchNormalization(name=f'bn_{i}'))
            model.add(Dropout(self.dropout_rate, name=f'dropout_{i}'))
        
        # Dense 레이어들
        model.add(Dense(32, activation='relu', name='dense_1'))
        model.add(Dropout(self.dropout_rate, name='dropout_final'))
        model.add(Dense(16, activation='relu', name='dense_2'))
        
        # 출력 레이어 (회귀)
        model.add(Dense(1, name='output'))
        
        # 컴파일
        optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        self.model = model
        
        self.logger.info("모델 구축 완료")
        self.logger.info(f"총 파라미터: {model.count_params():,}")
        
        return model
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 32,
        verbose: int = 1
    ) -> dict:
        """
        모델 학습
        
        Args:
            X_train: 학습 데이터 (samples, sequence_length, n_features)
            y_train: 학습 타겟 (samples,)
            X_val: 검증 데이터
            y_val: 검증 타겟
            epochs: 에폭 수
            batch_size: 배치 크기
            verbose: 출력 레벨
        
        Returns:
            학습 히스토리
        """
        if self.model is None:
            self.build_model()
        
        self.logger.info("모델 학습 시작...")
        self.logger.info(f"학습 데이터: {X_train.shape}, 타겟: {y_train.shape}")
        if X_val is not None:
            self.logger.info(f"검증 데이터: {X_val.shape}, 타겟: {y_val.shape}")
        
        # 콜백 설정
        callback_list = self._get_callbacks()
        
        # 검증 데이터 설정
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
        
        # 학습
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callback_list,
            verbose=verbose
        )
        
        self.history = history.history
        
        self.logger.info("학습 완료")
        if validation_data is not None:
            final_val_loss = history.history['val_loss'][-1]
            final_val_mae = history.history['val_mae'][-1]
            self.logger.info(f"최종 검증 손실: {final_val_loss:.6f}")
            self.logger.info(f"최종 검증 MAE: {final_val_mae:.6f}")
        
        return self.history
    
    def _get_callbacks(self) -> list:
        """학습 콜백 설정"""
        callback_list = []
        
        # 조기 종료
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )
        callback_list.append(early_stop)
        
        # 학습률 감소
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=7,
            min_lr=1e-7,
            verbose=1
        )
        callback_list.append(reduce_lr)
        
        # 모델 체크포인트
        checkpoint = ModelCheckpoint(
            filepath='./models/lstm_best.h5',
            monitor='val_loss',
            save_best_only=True,
            verbose=0
        )
        callback_list.append(checkpoint)
        
        return callback_list
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        가격 예측
        
        Args:
            X: 입력 데이터 (samples, sequence_length, n_features)
        
        Returns:
            예측값 (samples,)
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()
    
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> dict:
        """
        모델 평가
        
        Args:
            X_test: 테스트 데이터
            y_test: 테스트 타겟
        
        Returns:
            평가 지표 딕셔너리
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")
        
        self.logger.info("모델 평가 중...")
        
        # 예측
        y_pred = self.predict(X_test)
        
        # 지표 계산
        mse = np.mean((y_test - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_test - y_pred))
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        # 방향 정확도
        direction_actual = np.sign(np.diff(y_test))
        direction_pred = np.sign(np.diff(y_pred))
        direction_accuracy = np.mean(direction_actual == direction_pred) * 100
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'direction_accuracy': direction_accuracy
        }
        
        self.logger.info("평가 완료")
        self.logger.info(f"  RMSE: {rmse:.6f}")
        self.logger.info(f"  MAE: {mae:.6f}")
        self.logger.info(f"  MAPE: {mape:.2f}%")
        self.logger.info(f"  방향 정확도: {direction_accuracy:.2f}%")
        
        return metrics
    
    def save_model(self, filepath: str = './models/lstm_model.h5'):
        """
        모델 저장
        
        Args:
            filepath: 저장 경로
        """
        if self.model is None:
            raise ValueError("저장할 모델이 없습니다.")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        self.logger.info(f"모델 저장 완료: {filepath}")
    
    def load_model(self, filepath: str = './models/lstm_model.h5'):
        """
        모델 로드
        
        Args:
            filepath: 모델 파일 경로
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {filepath}")
        
        self.model = load_model(filepath)
        self.logger.info(f"모델 로드 완료: {filepath}")
    
    def get_model_summary(self):
        """모델 구조 출력"""
        if self.model is None:
            raise ValueError("모델이 구축되지 않았습니다.")
        
        return self.model.summary()


if __name__ == '__main__':
    # 사용 예시
    print("LSTM 모델 테스트")
    
    # 더미 데이터 생성
    n_samples = 1000
    sequence_length = 60
    n_features = 5
    
    X = np.random.randn(n_samples, sequence_length, n_features)
    y = np.random.randn(n_samples)
    
    # 데이터 분할
    split = int(n_samples * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # 모델 생성 및 학습
    model = LSTMModel(
        sequence_length=sequence_length,
        n_features=n_features,
        lstm_units=[64, 32],
        dropout_rate=0.2
    )
    
    # 모델 구조 출력
    model.build_model()
    model.get_model_summary()
    
    # 학습
    print("\n학습 시작...")
    history = model.train(
        X_train, y_train,
        X_val=X_test, y_val=y_test,
        epochs=10,
        batch_size=32,
        verbose=1
    )
    
    # 평가
    print("\n평가...")
    metrics = model.evaluate(X_test, y_test)
    
    # 예측
    print("\n예측...")
    predictions = model.predict(X_test[:10])
    print(f"예측값: {predictions[:5]}")
    print(f"실제값: {y_test[:5]}")
    
    # 저장
    print("\n모델 저장...")
    model.save_model()

