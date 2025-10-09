"""
example_ml_trading.py - ML 자동매매 시스템 실행 예제

전체 플로우: 데이터 수집 → 학습 → 예측 → 백테스팅 → 실전 거래
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 영어 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

from ml_price_predictor import MLPricePredictor
from ml_trading_system import MLTradingSystem


def example_full_pipeline():
    """전체 파이프라인 실행 예제"""
    
    print("="*80)
    print("💡 ML 기반 자동매매 시스템 - 전체 플로우 예제")
    print("="*80)
    print()
    
    # ==================== 1. 시스템 초기화 ====================
    print("\n" + "="*80)
    print("STEP 1: 시스템 초기화")
    print("="*80)
    
    predictor = MLPricePredictor(
        market='KRW-BTC',
        sequence_length=60,
        forecast_horizon=1,
        model_weights={
            'lstm': 0.6,
            'rf': 0.2,
            'xgb': 0.2
        }
    )
    
    print(f"✅ 마켓: {predictor.market}")
    print(f"✅ 시퀀스 길이: {predictor.sequence_length}")
    print(f"✅ 예측 시점: {predictor.forecast_horizon} 시간 후")
    
    # ==================== 2. 데이터 준비 ====================
    print("\n" + "="*80)
    print("STEP 2: 데이터 수집 및 전처리")
    print("="*80)
    
    (X_train_lstm, X_train_ml, X_val_lstm, X_val_ml,
     X_test_lstm, X_test_ml, y_train, y_val, y_test) = predictor.prepare_data(
        interval='60',  # 1시간봉
        days=180  # 6개월 데이터
    )
    
    print(f"\n✅ 데이터 준비 완료")
    print(f"   - LSTM 입력 shape: {X_train_lstm.shape}")
    print(f"   - ML 입력 shape: {X_train_ml.shape}")
    print(f"   - 특징 개수: {X_train_ml.shape[1]}")
    
    # ==================== 3. 모델 학습 ====================
    print("\n" + "="*80)
    print("STEP 3: ML/DL 모델 학습")
    print("="*80)
    
    predictor.train_models(
        X_train_lstm, X_train_ml,
        X_val_lstm, X_val_ml,
        y_train, y_val,
        lstm_epochs=30,
        lstm_batch_size=32
    )
    
    print("\n✅ 모델 학습 완료")
    
    # ==================== 4. 모델 평가 ====================
    print("\n" + "="*80)
    print("STEP 4: 모델 성능 평가")
    print("="*80)
    
    metrics = predictor.evaluate(X_test_lstm, X_test_ml, y_test)
    
    # ==================== 5. 예측 예시 ====================
    print("\n" + "="*80)
    print("STEP 5: 가격 예측 예시")
    print("="*80)
    
    # 최근 5개 데이터로 예측
    n_samples = min(5, len(X_test_lstm))
    result = predictor.predict(
        X_test_lstm[:n_samples],
        X_test_ml[:n_samples],
        return_confidence=True
    )
    
    print(f"\n예측 결과 ({n_samples}개 샘플):")
    for i in range(n_samples):
        print(f"\n{i+1}. 예측:")
        print(f"   - 통합 예측: {result['predictions'][i]:,.0f}원")
        print(f"   - LSTM: {result['lstm_pred'][i]:,.0f}원")
        print(f"   - RF: {result['rf_pred'][i]:,.0f}원")
        print(f"   - XGB: {result['xgb_pred'][i]:,.0f}원")
        print(f"   - 신뢰도: {result['confidence'][i]:.2%}")
    
    # ==================== 6. 백테스팅 ====================
    print("\n" + "="*80)
    print("STEP 6: 백테스팅 실행")
    print("="*80)
    
    trading_system = MLTradingSystem(
        predictor=predictor,
        initial_capital=10_000_000,  # 1천만원
        signal_threshold=0.02,  # 2% 변동
        confidence_threshold=0.7,  # 70% 신뢰도
        position_size=0.03,  # 3% 투자
        stop_loss=-0.03,  # -3% 손절
        take_profit=0.05,  # +5% 익절
        max_positions=3
    )
    
    # 실제 가격 데이터 준비
    y_test_2d = y_test.reshape(-1, 1)
    prices = predictor.y_scaler.inverse_transform(y_test_2d).flatten()
    timestamps = [datetime.now()] * len(prices)
    
    # 백테스팅 실행
    backtest_results = trading_system.backtest(
        X_test_lstm,
        X_test_ml,
        prices,
        timestamps
    )
    
    # ==================== 7. 결과 시각화 ====================
    print("\n" + "="*80)
    print("STEP 7: 결과 시각화")
    print("="*80)
    
    visualize_results(
        predictor,
        trading_system,
        X_test_lstm,
        X_test_ml,
        y_test,
        prices,
        backtest_results
    )
    
    # ==================== 8. 모델 저장 ====================
    print("\n" + "="*80)
    print("STEP 8: 모델 저장")
    print("="*80)
    
    predictor.save_models()
    print("\n✅ 모델 저장 완료")
    
    # ==================== 9. 요약 ====================
    print("\n" + "="*80)
    print("📊 최종 요약")
    print("="*80)
    
    print(f"\n🎯 모델 성능:")
    print(f"   - RMSE: {metrics['rmse']:,.0f}원")
    print(f"   - MAPE: {metrics['mape']:.2f}%")
    print(f"   - 방향 정확도: {metrics['direction_accuracy']:.2f}%")
    
    print(f"\n💰 백테스팅 결과:")
    print(f"   - 총 수익률: {backtest_results['total_return']:+.2%}")
    print(f"   - 승률: {backtest_results['win_rate']:.2%}")
    print(f"   - 샤프 비율: {backtest_results['sharpe_ratio']:.2f}")
    print(f"   - 최대 낙폭: {backtest_results['max_drawdown']:.2%}")
    
    print("\n" + "="*80)
    print("✅ 전체 플로우 완료!")
    print("="*80)
    
    return predictor, trading_system, backtest_results


def visualize_results(
    predictor,
    trading_system,
    X_test_lstm,
    X_test_ml,
    y_test,
    prices,
    backtest_results
):
    """결과 시각화"""
    
    # Graph style settings
    sns.set_style("whitegrid")
    
    # 1. Prediction vs Actual Price
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('ML Trading System Backtest Results', fontsize=16, fontweight='bold')
    
    # Predictions
    result = predictor.predict(X_test_lstm, X_test_ml)
    predictions = result['predictions']
    
    # Graph 1: Price Prediction
    ax1 = axes[0, 0]
    indices = range(len(prices))
    ax1.plot(indices, prices, label='Actual Price', alpha=0.7, linewidth=2)
    ax1.plot(indices, predictions, label='Predicted Price', alpha=0.7, linewidth=2)
    ax1.set_title('Price Prediction vs Actual Price')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price (KRW)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Graph 2: Prediction Error
    ax2 = axes[0, 1]
    errors = predictions - prices
    ax2.hist(errors, bins=50, alpha=0.7, edgecolor='black')
    ax2.axvline(x=0, color='r', linestyle='--', linewidth=2)
    ax2.set_title(f'Prediction Error Distribution (Avg: {np.mean(errors):,.0f} KRW)')
    ax2.set_xlabel('Error (KRW)')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, alpha=0.3)
    
    # Graph 3: Cumulative Profit
    ax3 = axes[1, 0]
    trade_history_df = trading_system.get_trade_history_df()
    
    if not trade_history_df.empty:
        cumulative_returns = trade_history_df['profit'].cumsum()
        ax3.plot(cumulative_returns.values, linewidth=2)
        ax3.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        ax3.set_title(f'Cumulative Profit: {backtest_results["total_profit"]:+,.0f} KRW')
        ax3.set_xlabel('Number of Trades')
        ax3.set_ylabel('Cumulative Profit (KRW)')
        ax3.grid(True, alpha=0.3)
    
    # Graph 4: Trade Statistics
    ax4 = axes[1, 1]
    stats = [
        backtest_results['winning_trades'],
        backtest_results['losing_trades']
    ]
    colors = ['green', 'red']
    labels = [f'Win\n{backtest_results["winning_trades"]} trades',
              f'Loss\n{backtest_results["losing_trades"]} trades']
    
    wedges, texts, autotexts = ax4.pie(
        stats,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )
    ax4.set_title(f'Trade Statistics (Win Rate: {backtest_results["win_rate"]:.1%})')
    
    plt.tight_layout()
    
    # Save
    os.makedirs('./results', exist_ok=True)
    plt.savefig('./results/backtest_results.png', dpi=300, bbox_inches='tight')
    print("\n✅ Graph saved: ./results/backtest_results.png")
    
    # 화면에 표시
    plt.show()


def example_realtime_prediction():
    """실시간 예측 예제 (실제 거래는 하지 않음)"""
    
    print("\n" + "="*80)
    print("💡 실시간 예측 예제 (시뮬레이션)")
    print("="*80)
    
    # 모델 로드
    predictor = MLPricePredictor(market='KRW-BTC')
    
    try:
        predictor.load_models()
        print("✅ 저장된 모델 로드 완료")
    except:
        print("⚠️ 저장된 모델이 없습니다. 먼저 학습을 실행하세요.")
        return
    
    # 최신 데이터 수집 및 예측
    print("\n최신 데이터 수집 중...")
    df = predictor.pipeline.collect_historical_data(
        market='KRW-BTC',
        interval='60',
        days=30
    )
    
    # 특징 생성
    df_features = predictor.feature_engineer.create_all_features(df)
    df_features = df_features.dropna()
    
    # 최근 데이터로 예측
    price_data = df_features[['close']].values
    X_lstm, _ = predictor.pipeline.create_sequences(
        price_data,
        sequence_length=predictor.sequence_length,
        forecast_horizon=1
    )
    
    feature_cols = [col for col in df_features.columns 
                   if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    X_ml = df_features[feature_cols].values[predictor.sequence_length:]
    
    # 정규화
    X_lstm_scaled = predictor.price_scaler.transform(
        X_lstm.reshape(-1, X_lstm.shape[-1])
    ).reshape(X_lstm.shape)
    X_ml_scaled = predictor.feature_scaler.transform(X_ml)
    
    # 예측
    result = predictor.predict(
        X_lstm_scaled[-1:],
        X_ml_scaled[-1:],
        return_confidence=True
    )
    
    current_price = price_data[-1][0]
    predicted_price = result['predictions'][0]
    confidence = result['confidence'][0]
    expected_change = (predicted_price - current_price) / current_price
    
    print(f"\n📊 예측 결과:")
    print(f"   - 현재 가격: {current_price:,.0f}원")
    print(f"   - 예측 가격: {predicted_price:,.0f}원")
    print(f"   - 예상 변화: {expected_change:+.2%}")
    print(f"   - 신뢰도: {confidence:.2%}")
    
    # 신호 생성
    if expected_change > 0.02 and confidence > 0.7:
        print(f"\n✅ 매수 신호 (상승 예측)")
    elif expected_change < -0.02 and confidence > 0.7:
        print(f"\n⚠️ 매도 신호 (하락 예측)")
    else:
        print(f"\n⏸️ 대기 신호 (변화율 작음 또는 낮은 신뢰도)")


if __name__ == '__main__':
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == 'realtime':
            # 실시간 예측 모드
            example_realtime_prediction()
        elif sys.argv[1] == 'full':
            # 전체 파이프라인
            example_full_pipeline()
        else:
            print("사용법:")
            print("  python example_ml_trading.py full      # 전체 플로우 실행")
            print("  python example_ml_trading.py realtime  # 실시간 예측")
    else:
        # 기본: 전체 파이프라인
        example_full_pipeline()

