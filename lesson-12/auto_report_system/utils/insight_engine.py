#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인사이트 생성 엔진
분석 결과를 바탕으로 자동으로 인사이트 도출
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class InsightEngine:
    """인사이트 생성 엔진"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_insights(self, report_type: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        분석 결과로부터 인사이트 생성
        
        Args:
            report_type: 리포트 유형 (daily, weekly, monthly)
            analysis: 분석 결과
            
        Returns:
            인사이트 리스트
        """
        insights = []
        
        # 수익률 인사이트
        insights.extend(self._generate_return_insights(analysis))
        
        # 리스크 인사이트
        insights.extend(self._generate_risk_insights(analysis))
        
        # 거래 패턴 인사이트
        insights.extend(self._generate_trading_insights(analysis))
        
        # 전략 인사이트
        if 'strategy_analysis' in analysis:
            insights.extend(self._generate_strategy_insights(analysis))
        
        # 리포트 유형별 추가 인사이트
        if report_type == 'weekly':
            insights.extend(self._generate_weekly_insights(analysis))
        elif report_type == 'monthly':
            insights.extend(self._generate_monthly_insights(analysis))
        
        # 중요도 순으로 정렬
        insights.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['impact'], 2))
        
        return insights
    
    def _generate_return_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """수익률 인사이트"""
        insights = []
        total_return = analysis.get('total_return', 0)
        
        if total_return > 10:
            insights.append({
                'title': '🎉 우수한 수익률 달성',
                'description': f'총 수익률 {total_return:.2f}%로 매우 양호한 성과를 기록했습니다.',
                'recommendation': '현재 전략을 유지하되, 일부 수익을 실현하고 리스크 관리를 강화하세요.',
                'impact': 'high',
                'category': 'performance'
            })
        elif total_return > 5:
            insights.append({
                'title': '✅ 양호한 수익률',
                'description': f'총 수익률 {total_return:.2f}%로 안정적인 성과를 보이고 있습니다.',
                'recommendation': '현재 전략을 지속하되, 포지션 크기 최적화를 고려하세요.',
                'impact': 'medium',
                'category': 'performance'
            })
        elif total_return < -5:
            insights.append({
                'title': '⚠️ 손실 발생',
                'description': f'총 수익률 {total_return:.2f}%로 손실이 발생했습니다.',
                'recommendation': '전략 재검토 및 리스크 관리 강화가 필요합니다. 필요시 거래를 일시 중단하세요.',
                'impact': 'high',
                'category': 'risk'
            })
        
        return insights
    
    def _generate_risk_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """리스크 인사이트"""
        insights = []
        
        mdd = abs(analysis.get('max_drawdown', 0))
        sharpe = analysis.get('sharpe_ratio', 0)
        
        if mdd > 15:
            insights.append({
                'title': '🚨 높은 낙폭 경고',
                'description': f'최대 낙폭이 {mdd:.2f}%로 위험 수준입니다.',
                'recommendation': '포지션 크기를 축소하고 손절 기준을 강화하세요.',
                'impact': 'high',
                'category': 'risk'
            })
        elif mdd > 10:
            insights.append({
                'title': '⚠️ 낙폭 주의',
                'description': f'최대 낙폭이 {mdd:.2f}%로 관리가 필요합니다.',
                'recommendation': '리스크 관리 전략을 점검하고 적절한 조치를 취하세요.',
                'impact': 'medium',
                'category': 'risk'
            })
        
        if sharpe < 1.0:
            insights.append({
                'title': '📉 낮은 샤프 비율',
                'description': f'샤프 비율 {sharpe:.2f}로 리스크 대비 수익이 낮습니다.',
                'recommendation': '변동성을 줄이거나 수익성을 개선할 전략 조정이 필요합니다.',
                'impact': 'medium',
                'category': 'risk'
            })
        elif sharpe > 2.0:
            insights.append({
                'title': '⭐ 우수한 샤프 비율',
                'description': f'샤프 비율 {sharpe:.2f}로 리스크 대비 수익이 매우 우수합니다.',
                'recommendation': '현재 전략의 핵심 요소를 분석하고 다른 전략에도 적용하세요.',
                'impact': 'high',
                'category': 'performance'
            })
        
        return insights
    
    def _generate_trading_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """거래 패턴 인사이트"""
        insights = []
        
        win_rate = analysis.get('win_rate', 0)
        total_trades = analysis.get('total_trades', 0)
        profit_factor = analysis.get('profit_factor', 0)
        
        if win_rate < 40:
            insights.append({
                'title': '⚠️ 낮은 승률',
                'description': f'승률이 {win_rate:.1f}%로 낮습니다.',
                'recommendation': '진입 조건을 강화하거나 손절 기준을 재검토하세요.',
                'impact': 'high',
                'category': 'trading'
            })
        elif win_rate > 70:
            insights.append({
                'title': '✨ 높은 승률',
                'description': f'승률이 {win_rate:.1f}%로 매우 우수합니다.',
                'recommendation': '현재 진입 조건을 유지하되, 수익 실현 전략을 최적화하세요.',
                'impact': 'medium',
                'category': 'trading'
            })
        
        if total_trades > 100:
            insights.append({
                'title': '📊 과도한 거래',
                'description': f'총 {total_trades}건의 거래가 발생했습니다.',
                'recommendation': '과도한 거래는 수수료 부담을 증가시킵니다. 진입 기준을 강화하세요.',
                'impact': 'medium',
                'category': 'trading'
            })
        elif total_trades < 5:
            insights.append({
                'title': '⏸️ 적은 거래',
                'description': f'거래가 {total_trades}건으로 매우 적습니다.',
                'recommendation': '기회를 놓치고 있을 수 있습니다. 진입 조건을 재검토하세요.',
                'impact': 'low',
                'category': 'trading'
            })
        
        if profit_factor > 2.0:
            insights.append({
                'title': '💰 우수한 프로핏 팩터',
                'description': f'프로핏 팩터 {profit_factor:.2f}로 수익 대비 손실이 양호합니다.',
                'recommendation': '현재 손익 관리 전략을 지속하세요.',
                'impact': 'medium',
                'category': 'performance'
            })
        
        return insights
    
    def _generate_strategy_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """전략 인사이트"""
        insights = []
        
        strategy_analysis = analysis.get('strategy_analysis', {})
        
        if strategy_analysis:
            # 최고 성과 전략
            best_strategy = max(
                strategy_analysis.items(),
                key=lambda x: x[1].get('total_return', 0)
            )
            
            insights.append({
                'title': f'🏆 최고 전략: {best_strategy[0]}',
                'description': f'{best_strategy[0]} 전략이 {best_strategy[1].get("total_return", 0):.2f}%의 최고 수익률을 기록했습니다.',
                'recommendation': '성과가 좋은 전략의 비중을 늘리는 것을 고려하세요.',
                'impact': 'high',
                'category': 'strategy'
            })
        
        return insights
    
    def _generate_weekly_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """주간 인사이트"""
        insights = []
        
        # 주간 특화 분석
        insights.append({
            'title': '📅 주간 리뷰',
            'description': '지난 주의 거래 패턴과 시장 상황을 분석했습니다.',
            'recommendation': '주말 동안 다음 주 전략을 재검토하세요.',
            'impact': 'low',
            'category': 'review'
        })
        
        return insights
    
    def _generate_monthly_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월간 인사이트"""
        insights = []
        
        # 월간 특화 분석
        insights.append({
            'title': '📆 월간 종합 분석',
            'description': '한 달간의 종합적인 성과를 평가했습니다.',
            'recommendation': '월간 성과를 바탕으로 전략 조정 및 목표를 재설정하세요.',
            'impact': 'medium',
            'category': 'review'
        })
        
        return insights
    
    def generate_alert_insights(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """긴급 알림 인사이트"""
        insights = []
        
        for alert in alerts:
            severity = alert.get('severity', 'low')
            
            insights.append({
                'title': f'🚨 {alert.get("title", "긴급 알림")}',
                'description': alert.get('description', '이상 상황이 감지되었습니다.'),
                'recommendation': alert.get('recommendation', '즉시 확인이 필요합니다.'),
                'impact': severity,
                'category': 'alert'
            })
        
        return insights

