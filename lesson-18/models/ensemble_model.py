"""
ensemble_model.py - 앙상블 머신러닝 모델

Random Forest와 XGBoost를 결합한 앙상블 모델로 가격을 예측합니다.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict
import os
import logging
import joblib

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
except ImportError:
    print("경고: scikit-learn이 설치되지 않았습니다.")
    RandomForestRegressor = None

try:
    import xgboost as xgb
except ImportError:
    print("경고: xgboost가 설치되지 않았습니다.")
    xgb = None


class EnsembleModel:
    """
    앙상블 머신러닝 모델 (Random Forest + XGBoost)
    
    기능:
    - Random Forest 회귀
    - XGBoost 회귀
    - 두 모델의 앙상블 예측
    - 특징 중요도 분석
    """
    
    def __init__(
        self,
        rf_params: Optional[Dict] = None,
        xgb_params: Optional[Dict] = None,
        ensemble_weights: Tuple[float, float] = (0.5, 0.5)
    ):
        """
        초기화
        
        Args:
            rf_params: Random Forest 파라미터
            xgb_params: XGBoost 파라미터
            ensemble_weights: 앙상블 가중치 (RF, XGB)
        """
        # 기본 파라미터
        self.rf_params = rf_params or {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.xgb_params = xgb_params or {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.ensemble_weights = ensemble_weights
        
        # 모델 초기화
        self.rf_model = None
        self.xgb_model = None
        
        if RandomForestRegressor is not None:
            self.rf_model = RandomForestRegressor(**self.rf_params)
        
        if xgb is not None:
            self.xgb_model = xgb.XGBRegressor(**self.xgb_params)
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ):
        """
        모델 학습
        
        Args:
            X_train: 학습 데이터 (samples, features)
            y_train: 학습 타겟 (samples,)
            X_val: 검증 데이터 (선택)
            y_val: 검증 타겟 (선택)
        """
        self.logger.info("앙상블 모델 학습 시작...")
        self.logger.info(f"학습 데이터: {X_train.shape}, 타겟: {y_train.shape}")
        
        # Random Forest 학습
        if self.rf_model is not None:
            self.logger.info("Random Forest 학습 중...")
            self.rf_model.fit(X_train, y_train)
            self.logger.info("Random Forest 학습 완료")
            
            if X_val is not None and y_val is not None:
                rf_pred = self.rf_model.predict(X_val)
                rf_rmse = np.sqrt(mean_squared_error(y_val, rf_pred))
                rf_mae = mean_absolute_error(y_val, rf_pred)
                self.logger.info(f"  검증 RMSE: {rf_rmse:.6f}")
                self.logger.info(f"  검증 MAE: {rf_mae:.6f}")
        
        # XGBoost 학습
        if self.xgb_model is not None:
            self.logger.info("XGBoost 학습 중...")
            
            # 조기 종료를 위한 평가 세트
            eval_set = []
            if X_val is not None and y_val is not None:
                eval_set = [(X_val, y_val)]
            
            self.xgb_model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
            self.logger.info("XGBoost 학습 완료")
            
            if X_val is not None and y_val is not None:
                xgb_pred = self.xgb_model.predict(X_val)
                xgb_rmse = np.sqrt(mean_squared_error(y_val, xgb_pred))
                xgb_mae = mean_absolute_error(y_val, xgb_pred)
                self.logger.info(f"  검증 RMSE: {xgb_rmse:.6f}")
                self.logger.info(f"  검증 MAE: {xgb_mae:.6f}")
        
        self.logger.info("앙상블 모델 학습 완료")
    
    def predict(self, X: np.ndarray, use_ensemble: bool = True) -> np.ndarray:
        """
        가격 예측
        
        Args:
            X: 입력 데이터 (samples, features)
            use_ensemble: 앙상블 사용 여부
        
        Returns:
            예측값 (samples,)
        """
        predictions = []
        
        # Random Forest 예측
        if self.rf_model is not None:
            rf_pred = self.rf_model.predict(X)
            predictions.append(rf_pred)
        
        # XGBoost 예측
        if self.xgb_model is not None:
            xgb_pred = self.xgb_model.predict(X)
            predictions.append(xgb_pred)
        
        if not predictions:
            raise ValueError("학습된 모델이 없습니다.")
        
        if use_ensemble and len(predictions) > 1:
            # 가중 평균
            ensemble_pred = (
                predictions[0] * self.ensemble_weights[0] +
                predictions[1] * self.ensemble_weights[1]
            )
            return ensemble_pred
        else:
            # 단일 모델 또는 평균
            return np.mean(predictions, axis=0)
    
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        use_ensemble: bool = True
    ) -> Dict:
        """
        모델 평가
        
        Args:
            X_test: 테스트 데이터
            y_test: 테스트 타겟
            use_ensemble: 앙상블 사용 여부
        
        Returns:
            평가 지표 딕셔너리
        """
        self.logger.info("모델 평가 중...")
        
        # 예측
        y_pred = self.predict(X_test, use_ensemble=use_ensemble)
        
        # 지표 계산
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # MAPE 계산 (0으로 나누기 방지)
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100
        
        # 방향 정확도
        direction_actual = np.sign(np.diff(y_test))
        direction_pred = np.sign(np.diff(y_pred))
        direction_accuracy = np.mean(direction_actual == direction_pred) * 100
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2': r2,
            'direction_accuracy': direction_accuracy
        }
        
        self.logger.info("평가 완료")
        self.logger.info(f"  RMSE: {rmse:.6f}")
        self.logger.info(f"  MAE: {mae:.6f}")
        self.logger.info(f"  MAPE: {mape:.2f}%")
        self.logger.info(f"  R2 Score: {r2:.4f}")
        self.logger.info(f"  방향 정확도: {direction_accuracy:.2f}%")
        
        return metrics
    
    def get_feature_importance(
        self,
        feature_names: Optional[list] = None,
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        특징 중요도 분석
        
        Args:
            feature_names: 특징 이름 리스트
            top_n: 상위 몇 개를 반환할지
        
        Returns:
            특징 중요도 데이터프레임
        """
        importance_dict = {}
        
        # Random Forest 중요도
        if self.rf_model is not None:
            importance_dict['rf_importance'] = self.rf_model.feature_importances_
        
        # XGBoost 중요도
        if self.xgb_model is not None:
            importance_dict['xgb_importance'] = self.xgb_model.feature_importances_
        
        if not importance_dict:
            self.logger.warning("학습된 모델이 없습니다.")
            return pd.DataFrame()
        
        # 데이터프레임 생성
        df = pd.DataFrame(importance_dict)
        
        # 평균 중요도 계산
        df['avg_importance'] = df.mean(axis=1)
        
        # 특징 이름 추가
        if feature_names is not None:
            df['feature'] = feature_names
        else:
            df['feature'] = [f'feature_{i}' for i in range(len(df))]
        
        # 정렬
        df = df.sort_values('avg_importance', ascending=False)
        
        # 상위 N개만 반환
        if top_n is not None:
            df = df.head(top_n)
        
        return df[['feature', 'avg_importance', 'rf_importance', 'xgb_importance']]
    
    def save_models(self, rf_path: str = './models/rf_model.pkl',
                    xgb_path: str = './models/xgb_model.pkl'):
        """
        모델 저장
        
        Args:
            rf_path: Random Forest 모델 저장 경로
            xgb_path: XGBoost 모델 저장 경로
        """
        os.makedirs(os.path.dirname(rf_path), exist_ok=True)
        os.makedirs(os.path.dirname(xgb_path), exist_ok=True)
        
        if self.rf_model is not None:
            joblib.dump(self.rf_model, rf_path)
            self.logger.info(f"Random Forest 저장: {rf_path}")
        
        if self.xgb_model is not None:
            joblib.dump(self.xgb_model, xgb_path)
            self.logger.info(f"XGBoost 저장: {xgb_path}")
    
    def load_models(self, rf_path: str = './models/rf_model.pkl',
                    xgb_path: str = './models/xgb_model.pkl'):
        """
        모델 로드
        
        Args:
            rf_path: Random Forest 모델 경로
            xgb_path: XGBoost 모델 경로
        """
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)
            self.logger.info(f"Random Forest 로드: {rf_path}")
        else:
            self.logger.warning(f"RF 모델 파일 없음: {rf_path}")
        
        if os.path.exists(xgb_path):
            self.xgb_model = joblib.load(xgb_path)
            self.logger.info(f"XGBoost 로드: {xgb_path}")
        else:
            self.logger.warning(f"XGB 모델 파일 없음: {xgb_path}")


if __name__ == '__main__':
    # 사용 예시
    print("앙상블 모델 테스트")
    
    # 더미 데이터 생성
    n_samples = 1000
    n_features = 20
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randn(n_samples) * 100 + 50000000  # 가격 시뮬레이션
    
    # 데이터 분할
    split = int(n_samples * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # 모델 생성 및 학습
    model = EnsembleModel(
        ensemble_weights=(0.5, 0.5)
    )
    
    print("\n학습 시작...")
    model.train(X_train, y_train, X_test, y_test)
    
    # 평가
    print("\n평가...")
    metrics = model.evaluate(X_test, y_test)
    
    # 예측
    print("\n예측...")
    predictions = model.predict(X_test[:10])
    print(f"예측값: {predictions[:5]}")
    print(f"실제값: {y_test[:5]}")
    
    # 특징 중요도
    print("\n특징 중요도:")
    importance = model.get_feature_importance(top_n=10)
    print(importance)
    
    # 저장
    print("\n모델 저장...")
    model.save_models()

