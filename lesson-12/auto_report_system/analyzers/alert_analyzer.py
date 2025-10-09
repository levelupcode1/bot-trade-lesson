#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이상 탐지 분석기
긴급 알림이 필요한 상황 감지
"""

import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertAnalyzer:
    """알림 분석 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.thresholds = config.get('alerts', {}) if config else {}
        
        # 기본 임계값
        self.max_drawdown_threshold = self.thresholds.get('max_drawdown', 10.0)
        self.daily_loss_threshold = self.thresholds.get('daily_loss', 5.0)
        self.win_rate_threshold = self.thresholds.get('win_rate_drop', 40.0)
    
    def check_anomalies(self) -> List[Dict[str, Any]]:
        """이상 상황 체크"""
        alerts = []
        
        try:
            from ..utils.data_collector import DataCollector
            
            collector = DataCollector()
            
            # 최신 메트릭 조회
            metrics = collector.get_latest_metrics()
            
            # 오늘 데이터 수집
            data = collector.collect_daily()
            trades = data.get('trades', pd.DataFrame())
            account = data.get('account_history', pd.DataFrame())
            
            # 낙폭 체크
            alerts.extend(self._check_drawdown(account))
            
            # 일일 손실 체크
            alerts.extend(self._check_daily_loss(account))
            
            # 승률 체크
            alerts.extend(self._check_win_rate(trades))
            
            # 거래 중단 체크
            alerts.extend(self._check_trading_halt(trades))
            
            # 시스템 오류 체크
            alerts.extend(self._check_system_errors(trades))
            
        except Exception as e:
            logger.error(f"이상 탐지 오류: {e}", exc_info=True)
            alerts.append({
                'title': '시스템 오류',
                'description': f'이상 탐지 중 오류 발생: {str(e)}',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _check_drawdown(self, account: pd.DataFrame) -> List[Dict[str, Any]]:
        """낙폭 체크"""
        alerts = []
        
        if account.empty or 'total_value' not in account.columns:
            return alerts
        
        # 최근 낙폭 계산
        cummax = account['total_value'].cummax()
        drawdown = (account['total_value'] - cummax) / cummax * 100
        current_dd = abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0
        
        if current_dd > self.max_drawdown_threshold:
            alerts.append({
                'title': '높은 낙폭 경고',
                'description': f'현재 낙폭이 {current_dd:.2f}%로 임계값 {self.max_drawdown_threshold}%를 초과했습니다.',
                'recommendation': '포지션 축소 또는 거래 일시 중단을 고려하세요.',
                'severity': 'high' if current_dd > 15 else 'medium',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _check_daily_loss(self, account: pd.DataFrame) -> List[Dict[str, Any]]:
        """일일 손실 체크"""
        alerts = []
        
        if account.empty or len(account) < 2:
            return alerts
        
        start_value = account.iloc[0]['total_value']
        end_value = account.iloc[-1]['total_value']
        daily_return = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
        
        if daily_return < -self.daily_loss_threshold:
            alerts.append({
                'title': '일일 손실 한도 초과',
                'description': f'오늘 {abs(daily_return):.2f}%의 손실이 발생했습니다.',
                'recommendation': '즉시 거래를 중단하고 원인을 분석하세요.',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _check_win_rate(self, trades: pd.DataFrame) -> List[Dict[str, Any]]:
        """승률 체크"""
        alerts = []
        
        if trades.empty or len(trades) < 10:  # 최소 10건 이상
            return alerts
        
        # 최근 거래의 승률 계산
        if 'profit_loss' in trades.columns:
            recent_trades = trades.tail(20)  # 최근 20건
            wins = len(recent_trades[recent_trades['profit_loss'] > 0])
            win_rate = (wins / len(recent_trades) * 100) if len(recent_trades) > 0 else 0
            
            if win_rate < self.win_rate_threshold:
                alerts.append({
                    'title': '낮은 승률 경고',
                    'description': f'최근 승률이 {win_rate:.1f}%로 임계값 {self.win_rate_threshold}% 이하입니다.',
                    'recommendation': '전략을 재검토하고 필요시 거래를 일시 중단하세요.',
                    'severity': 'medium',
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def _check_trading_halt(self, trades: pd.DataFrame) -> List[Dict[str, Any]]:
        """거래 중단 체크"""
        alerts = []
        
        if trades.empty:
            # 최근 1시간 동안 거래 없음
            alerts.append({
                'title': '거래 중단 감지',
                'description': '최근 거래 활동이 감지되지 않았습니다.',
                'recommendation': '시스템 상태를 확인하세요.',
                'severity': 'low',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def _check_system_errors(self, trades: pd.DataFrame) -> List[Dict[str, Any]]:
        """시스템 오류 체크"""
        alerts = []
        
        # 실패한 거래 체크
        if not trades.empty and 'status' in trades.columns:
            failed_trades = trades[trades['status'] == 'failed']
            
            if len(failed_trades) > 0:
                alerts.append({
                    'title': '거래 실패 감지',
                    'description': f'{len(failed_trades)}건의 거래가 실패했습니다.',
                    'recommendation': 'API 연결 및 주문 설정을 확인하세요.',
                    'severity': 'medium',
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts

