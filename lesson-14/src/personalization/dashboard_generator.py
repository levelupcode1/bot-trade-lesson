"""
개인화된 대시보드 생성 시스템
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .user_preferences import UserPreferences, DashboardPreferences


class WidgetType(Enum):
    """위젯 유형"""
    PORTFOLIO_VALUE = "portfolio_value"
    PROFIT_LOSS = "profit_loss"
    RECENT_TRADES = "recent_trades"
    MARKET_OVERVIEW = "market_overview"
    PRICE_CHART = "price_chart"
    PERFORMANCE_CHART = "performance_chart"
    RECOMMENDATIONS = "recommendations"
    ALERTS = "alerts"
    NEWS = "news"
    STATISTICS = "statistics"
    RISK_METRICS = "risk_metrics"
    LEARNING_PROGRESS = "learning_progress"


@dataclass
class Widget:
    """대시보드 위젯"""
    widget_id: str
    widget_type: WidgetType
    title: str
    size: str  # "small", "medium", "large", "full"
    position: Dict[str, int]  # {"row": 0, "col": 0}
    config: Dict[str, Any]
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "widget_type": self.widget_type.value,
            "title": self.title,
            "size": self.size,
            "position": self.position,
            "config": self.config,
            "enabled": self.enabled
        }


class DashboardGenerator:
    """개인화된 대시보드 생성기"""
    
    def __init__(self):
        # 기본 위젯 템플릿
        self.widget_templates = self._init_widget_templates()
    
    def _init_widget_templates(self) -> Dict[WidgetType, Dict[str, Any]]:
        """위젯 템플릿 초기화"""
        return {
            WidgetType.PORTFOLIO_VALUE: {
                "title": "포트폴리오 가치",
                "default_size": "medium",
                "required": True,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.PROFIT_LOSS: {
                "title": "손익 현황",
                "default_size": "medium",
                "required": True,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.RECENT_TRADES: {
                "title": "최근 거래",
                "default_size": "large",
                "required": True,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.MARKET_OVERVIEW: {
                "title": "시장 개요",
                "default_size": "medium",
                "required": False,
                "user_levels": ["intermediate", "advanced"]
            },
            WidgetType.PRICE_CHART: {
                "title": "가격 차트",
                "default_size": "large",
                "required": False,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.PERFORMANCE_CHART: {
                "title": "성과 차트",
                "default_size": "large",
                "required": False,
                "user_levels": ["intermediate", "advanced"]
            },
            WidgetType.RECOMMENDATIONS: {
                "title": "추천",
                "default_size": "medium",
                "required": False,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.ALERTS: {
                "title": "알림",
                "default_size": "small",
                "required": False,
                "user_levels": ["beginner", "intermediate", "advanced"]
            },
            WidgetType.NEWS: {
                "title": "뉴스",
                "default_size": "medium",
                "required": False,
                "user_levels": ["intermediate", "advanced"]
            },
            WidgetType.STATISTICS: {
                "title": "통계",
                "default_size": "medium",
                "required": False,
                "user_levels": ["advanced"]
            },
            WidgetType.RISK_METRICS: {
                "title": "리스크 지표",
                "default_size": "medium",
                "required": False,
                "user_levels": ["intermediate", "advanced"]
            },
            WidgetType.LEARNING_PROGRESS: {
                "title": "학습 진행도",
                "default_size": "small",
                "required": False,
                "user_levels": ["beginner", "intermediate"]
            }
        }
    
    def generate_dashboard(
        self,
        user_preferences: UserPreferences,
        behavior_insights: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """사용자 맞춤 대시보드 생성"""
        
        # 사용자 레벨 결정
        user_level = user_preferences.learning_prefs.learning_level
        
        # 위젯 목록 생성
        widgets = self._generate_widgets(
            user_preferences,
            user_level,
            behavior_insights
        )
        
        # 레이아웃 생성
        layout = self._generate_layout(
            user_preferences.dashboard_prefs.layout,
            widgets
        )
        
        # 대시보드 구성
        dashboard = {
            "user_id": user_preferences.user_id,
            "layout": layout,
            "theme": user_preferences.dashboard_prefs.theme,
            "language": user_preferences.dashboard_prefs.language,
            "widgets": [w.to_dict() for w in widgets],
            "config": {
                "chart_type": user_preferences.dashboard_prefs.default_chart_type,
                "chart_timeframe": user_preferences.dashboard_prefs.chart_timeframe,
                "chart_indicators": user_preferences.dashboard_prefs.chart_indicators,
                "show_portfolio_value": user_preferences.dashboard_prefs.show_portfolio_value,
                "show_profit_loss": user_preferences.dashboard_prefs.show_profit_loss,
                "show_recent_trades": user_preferences.dashboard_prefs.show_recent_trades,
                "show_market_news": user_preferences.dashboard_prefs.show_market_news
            }
        }
        
        return dashboard
    
    def _generate_widgets(
        self,
        user_preferences: UserPreferences,
        user_level: str,
        behavior_insights: Optional[Dict[str, Any]]
    ) -> List[Widget]:
        """위젯 목록 생성"""
        widgets = []
        
        # 사용자 레벨에 맞는 위젯 필터링
        available_widgets = [
            widget_type for widget_type, template in self.widget_templates.items()
            if user_level in template["user_levels"]
        ]
        
        # 사용자가 이미 설정한 위젯 확인
        user_enabled = user_preferences.dashboard_prefs.enabled_widgets
        user_widget_order = user_preferences.dashboard_prefs.widget_order
        user_widget_sizes = user_preferences.dashboard_prefs.widget_sizes
        
        # 필수 위젯 추가
        required_widgets = [
            wt for wt in available_widgets
            if self.widget_templates[wt]["required"]
        ]
        
        # 사용자 선호도 기반 위젯 추가
        if user_enabled:
            for widget_id in user_enabled:
                try:
                    widget_type = WidgetType(widget_id)
                    if widget_type in available_widgets:
                        widgets.append(self._create_widget(
                            widget_type,
                            user_preferences,
                            user_widget_sizes.get(widget_id, "medium")
                        ))
                except ValueError:
                    continue
        
        # 필수 위젯 추가 (아직 추가되지 않은 경우)
        for widget_type in required_widgets:
            if not any(w.widget_type == widget_type for w in widgets):
                widgets.append(self._create_widget(
                    widget_type,
                    user_preferences,
                    self.widget_templates[widget_type]["default_size"]
                ))
        
        # 행동 인사이트 기반 추천 위젯 추가
        if behavior_insights:
            recommended_widgets = self._recommend_widgets_from_behavior(
                behavior_insights,
                available_widgets,
                [w.widget_type for w in widgets]
            )
            for widget_type in recommended_widgets:
                widgets.append(self._create_widget(
                    widget_type,
                    user_preferences,
                    self.widget_templates[widget_type]["default_size"]
                ))
        
        # 사용자 순서 적용
        if user_widget_order:
            widget_dict = {w.widget_id: w for w in widgets}
            ordered_widgets = []
            for widget_id in user_widget_order:
                if widget_id in widget_dict:
                    ordered_widgets.append(widget_dict[widget_id])
            # 순서에 없는 위젯은 뒤에 추가
            for widget in widgets:
                if widget.widget_id not in user_widget_order:
                    ordered_widgets.append(widget)
            widgets = ordered_widgets
        
        return widgets
    
    def _create_widget(
        self,
        widget_type: WidgetType,
        user_preferences: UserPreferences,
        size: str
    ) -> Widget:
        """위젯 생성"""
        template = self.widget_templates[widget_type]
        
        # 위젯 설정
        config = self._get_widget_config(widget_type, user_preferences)
        
        widget = Widget(
            widget_id=widget_type.value,
            widget_type=widget_type,
            title=template["title"],
            size=size,
            position={"row": 0, "col": 0},  # 레이아웃에서 조정
            config=config,
            enabled=True
        )
        
        return widget
    
    def _get_widget_config(
        self,
        widget_type: WidgetType,
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """위젯별 설정 생성"""
        config = {}
        
        if widget_type == WidgetType.PRICE_CHART:
            config = {
                "chart_type": user_preferences.dashboard_prefs.default_chart_type,
                "timeframe": user_preferences.dashboard_prefs.chart_timeframe,
                "indicators": user_preferences.dashboard_prefs.chart_indicators,
                "coins": user_preferences.trading_prefs.favorite_coins[:3]  # 상위 3개
            }
        elif widget_type == WidgetType.RECOMMENDATIONS:
            config = {
                "max_items": 5,
                "types": ["strategy", "coin", "action"]
            }
        elif widget_type == WidgetType.MARKET_OVERVIEW:
            config = {
                "coins": user_preferences.trading_prefs.favorite_coins,
                "show_trend": True
            }
        elif widget_type == WidgetType.ALERTS:
            config = {
                "max_items": 10,
                "priority": "high"
            }
        elif widget_type == WidgetType.STATISTICS:
            config = {
                "metrics": ["win_rate", "sharpe_ratio", "max_drawdown"],
                "period": "30d"
            }
        elif widget_type == WidgetType.RISK_METRICS:
            config = {
                "show_position_size": True,
                "show_diversification": True,
                "show_correlation": False
            }
        elif widget_type == WidgetType.LEARNING_PROGRESS:
            config = {
                "show_completed": True,
                "show_recommended": True
            }
        
        return config
    
    def _recommend_widgets_from_behavior(
        self,
        behavior_insights: Dict[str, Any],
        available_widgets: List[WidgetType],
        existing_widgets: List[WidgetType]
    ) -> List[WidgetType]:
        """행동 인사이트 기반 위젯 추천"""
        recommended = []
        
        # 거래 패턴 분석
        trading_patterns = behavior_insights.get("trading_patterns", {})
        if trading_patterns.get("total_trades", 0) > 10:
            if WidgetType.PERFORMANCE_CHART not in existing_widgets:
                recommended.append(WidgetType.PERFORMANCE_CHART)
            if WidgetType.STATISTICS not in existing_widgets:
                recommended.append(WidgetType.STATISTICS)
        
        # 학습 진행도
        engagement = behavior_insights.get("engagement_metrics", {})
        if engagement.get("learning_progress", 0) > 0:
            if WidgetType.LEARNING_PROGRESS not in existing_widgets:
                recommended.append(WidgetType.LEARNING_PROGRESS)
        
        # 리스크 관심도
        if trading_patterns.get("win_rate", 0) < 50:
            if WidgetType.RISK_METRICS not in existing_widgets:
                recommended.append(WidgetType.RISK_METRICS)
        
        # 사용 가능한 위젯만 반환
        return [w for w in recommended if w in available_widgets]
    
    def _generate_layout(
        self,
        layout_type: str,
        widgets: List[Widget]
    ) -> Dict[str, Any]:
        """레이아웃 생성"""
        if layout_type == "grid":
            return self._generate_grid_layout(widgets)
        elif layout_type == "list":
            return self._generate_list_layout(widgets)
        else:  # custom
            return self._generate_custom_layout(widgets)
    
    def _generate_grid_layout(self, widgets: List[Widget]) -> Dict[str, Any]:
        """그리드 레이아웃 생성"""
        # 그리드 크기 계산
        cols = 3  # 기본 3열
        row = 0
        col = 0
        
        for i, widget in enumerate(widgets):
            # 위젯 크기에 따라 위치 조정
            size_cols = {
                "small": 1,
                "medium": 2,
                "large": 3,
                "full": 3
            }
            
            widget_cols = size_cols.get(widget.size, 2)
            
            # 다음 행으로 넘어가야 하는지 확인
            if col + widget_cols > cols:
                row += 1
                col = 0
            
            widget.position = {"row": row, "col": col}
            col += widget_cols
        
        return {
            "type": "grid",
            "columns": cols,
            "rows": row + 1,
            "gap": 16
        }
    
    def _generate_list_layout(self, widgets: List[Widget]) -> Dict[str, Any]:
        """리스트 레이아웃 생성"""
        for i, widget in enumerate(widgets):
            widget.position = {"row": i, "col": 0}
            widget.size = "full"  # 리스트 레이아웃은 전체 너비
        
        return {
            "type": "list",
            "columns": 1,
            "rows": len(widgets),
            "gap": 12
        }
    
    def _generate_custom_layout(self, widgets: List[Widget]) -> Dict[str, Any]:
        """커스텀 레이아웃 생성 (사용자 정의 위치 유지)"""
        # 기존 위치 정보 유지
        return {
            "type": "custom",
            "columns": 4,
            "rows": 10,
            "gap": 16
        }
    
    def update_dashboard(
        self,
        dashboard: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """대시보드 업데이트"""
        # 위젯 추가/제거
        if "add_widget" in updates:
            widget_type = WidgetType(updates["add_widget"])
            # 위젯 추가 로직
            pass
        
        if "remove_widget" in updates:
            widget_id = updates["remove_widget"]
            dashboard["widgets"] = [
                w for w in dashboard["widgets"]
                if w["widget_id"] != widget_id
            ]
        
        # 레이아웃 변경
        if "layout" in updates:
            dashboard["layout"] = updates["layout"]
        
        # 테마 변경
        if "theme" in updates:
            dashboard["theme"] = updates["theme"]
        
        return dashboard





