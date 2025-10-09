"""
맞춤형 추천 시스템
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random

from .user_preferences import UserPreferences, RiskTolerance, TradingStyle


class RecommendationType(Enum):
    """추천 유형"""
    STRATEGY = "strategy"
    COIN = "coin"
    SETTING = "setting"
    EDUCATION = "education"
    ACTION = "action"


@dataclass
class Recommendation:
    """추천 항목"""
    type: RecommendationType
    item_id: str
    title: str
    description: str
    confidence: float  # 0.0 ~ 1.0
    reason: str
    priority: int  # 1 (highest) ~ 5 (lowest)
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "reason": self.reason,
            "priority": self.priority,
            "metadata": self.metadata
        }


class RecommendationEngine:
    """추천 엔진"""
    
    def __init__(self):
        # 전략 데이터베이스 (실제로는 DB에서 로드)
        self.strategy_db = self._init_strategy_db()
        
        # 코인 데이터베이스
        self.coin_db = self._init_coin_db()
        
        # 교육 콘텐츠 데이터베이스
        self.education_db = self._init_education_db()
    
    def _init_strategy_db(self) -> Dict[str, Dict[str, Any]]:
        """전략 데이터베이스 초기화"""
        return {
            "volatility_breakout_conservative": {
                "name": "보수적 변동성 돌파",
                "risk_level": "low",
                "suitable_for": ["beginner"],
                "expected_return": 5.0,
                "volatility": 0.15,
                "description": "안정적인 수익을 추구하는 보수적 전략"
            },
            "volatility_breakout": {
                "name": "변동성 돌파",
                "risk_level": "moderate",
                "suitable_for": ["intermediate", "advanced"],
                "expected_return": 10.0,
                "volatility": 0.25,
                "description": "중간 리스크의 균형잡힌 전략"
            },
            "ma_crossover": {
                "name": "이동평균 교차",
                "risk_level": "moderate",
                "suitable_for": ["beginner", "intermediate"],
                "expected_return": 8.0,
                "volatility": 0.20,
                "description": "안정적인 추세 추종 전략"
            },
            "portfolio_strategy": {
                "name": "포트폴리오 전략",
                "risk_level": "moderate",
                "suitable_for": ["intermediate", "advanced"],
                "expected_return": 12.0,
                "volatility": 0.30,
                "description": "다중 코인 분산 투자 전략"
            },
            "aggressive_momentum": {
                "name": "공격적 모멘텀",
                "risk_level": "high",
                "suitable_for": ["advanced"],
                "expected_return": 20.0,
                "volatility": 0.45,
                "description": "고수익 추구 공격적 전략"
            }
        }
    
    def _init_coin_db(self) -> Dict[str, Dict[str, Any]]:
        """코인 데이터베이스 초기화"""
        return {
            "KRW-BTC": {
                "name": "비트코인",
                "risk_level": "moderate",
                "volatility": 0.30,
                "market_cap": "large",
                "liquidity": "very_high",
                "suitable_for": ["beginner", "intermediate", "advanced"]
            },
            "KRW-ETH": {
                "name": "이더리움",
                "risk_level": "moderate",
                "volatility": 0.35,
                "market_cap": "large",
                "liquidity": "very_high",
                "suitable_for": ["beginner", "intermediate", "advanced"]
            },
            "KRW-XRP": {
                "name": "리플",
                "risk_level": "moderate_high",
                "volatility": 0.40,
                "market_cap": "medium",
                "liquidity": "high",
                "suitable_for": ["intermediate", "advanced"]
            },
            "KRW-ADA": {
                "name": "카르다노",
                "risk_level": "moderate_high",
                "volatility": 0.42,
                "market_cap": "medium",
                "liquidity": "high",
                "suitable_for": ["intermediate", "advanced"]
            },
            "KRW-SOL": {
                "name": "솔라나",
                "risk_level": "high",
                "volatility": 0.50,
                "market_cap": "medium",
                "liquidity": "high",
                "suitable_for": ["advanced"]
            }
        }
    
    def _init_education_db(self) -> Dict[str, Dict[str, Any]]:
        """교육 콘텐츠 데이터베이스 초기화"""
        return {
            "crypto_basics": {
                "title": "암호화폐 기초",
                "level": "beginner",
                "duration": 30,
                "topics": ["blockchain", "cryptocurrency", "wallets"],
                "description": "암호화폐의 기본 개념 학습"
            },
            "technical_analysis": {
                "title": "기술적 분석 입문",
                "level": "beginner",
                "duration": 60,
                "topics": ["charts", "indicators", "patterns"],
                "description": "차트 분석의 기초"
            },
            "risk_management": {
                "title": "리스크 관리",
                "level": "intermediate",
                "duration": 45,
                "topics": ["position_sizing", "stop_loss", "diversification"],
                "description": "안전한 거래를 위한 리스크 관리"
            },
            "advanced_strategies": {
                "title": "고급 전략",
                "level": "advanced",
                "duration": 90,
                "topics": ["arbitrage", "hedging", "algorithmic_trading"],
                "description": "전문가 수준의 거래 전략"
            }
        }
    
    def get_recommendations(
        self,
        user_preferences: UserPreferences,
        recommendation_types: Optional[List[RecommendationType]] = None,
        limit: int = 10
    ) -> List[Recommendation]:
        """사용자에게 맞춤 추천 제공"""
        if recommendation_types is None:
            recommendation_types = list(RecommendationType)
        
        all_recommendations = []
        
        for rec_type in recommendation_types:
            if rec_type == RecommendationType.STRATEGY:
                all_recommendations.extend(
                    self._recommend_strategies(user_preferences)
                )
            elif rec_type == RecommendationType.COIN:
                all_recommendations.extend(
                    self._recommend_coins(user_preferences)
                )
            elif rec_type == RecommendationType.EDUCATION:
                all_recommendations.extend(
                    self._recommend_education(user_preferences)
                )
            elif rec_type == RecommendationType.SETTING:
                all_recommendations.extend(
                    self._recommend_settings(user_preferences)
                )
            elif rec_type == RecommendationType.ACTION:
                all_recommendations.extend(
                    self._recommend_actions(user_preferences)
                )
        
        # 우선순위와 신뢰도로 정렬
        all_recommendations.sort(
            key=lambda x: (x.priority, -x.confidence)
        )
        
        return all_recommendations[:limit]
    
    def _recommend_strategies(
        self,
        user_preferences: UserPreferences
    ) -> List[Recommendation]:
        """전략 추천"""
        recommendations = []
        
        risk_level = user_preferences.investment_profile.risk_tolerance
        trading_style = user_preferences.investment_profile.trading_style
        
        # 리스크 레벨에 맞는 전략 찾기
        for strategy_id, strategy_data in self.strategy_db.items():
            # 이미 선호 전략에 있으면 제외
            if strategy_id in user_preferences.trading_prefs.favorite_strategies:
                continue
            
            confidence = self._calculate_strategy_confidence(
                strategy_data,
                risk_level,
                trading_style
            )
            
            if confidence > 0.3:  # 임계값
                recommendations.append(Recommendation(
                    type=RecommendationType.STRATEGY,
                    item_id=strategy_id,
                    title=strategy_data["name"],
                    description=strategy_data["description"],
                    confidence=confidence,
                    reason=self._get_strategy_reason(
                        strategy_data, risk_level, trading_style
                    ),
                    priority=1 if confidence > 0.7 else 2,
                    metadata={
                        "expected_return": strategy_data["expected_return"],
                        "volatility": strategy_data["volatility"],
                        "risk_level": strategy_data["risk_level"]
                    }
                ))
        
        return recommendations
    
    def _recommend_coins(
        self,
        user_preferences: UserPreferences
    ) -> List[Recommendation]:
        """코인 추천"""
        recommendations = []
        
        risk_tolerance = user_preferences.investment_profile.risk_tolerance
        prefer_stable = user_preferences.trading_prefs.prefer_stable_coins
        
        for coin_id, coin_data in self.coin_db.items():
            # 이미 선호 코인에 있으면 제외
            if coin_id in user_preferences.trading_prefs.favorite_coins:
                continue
            
            # 블랙리스트에 있으면 제외
            if coin_id in user_preferences.trading_prefs.blacklist_coins:
                continue
            
            confidence = self._calculate_coin_confidence(
                coin_data,
                risk_tolerance,
                prefer_stable
            )
            
            if confidence > 0.3:
                recommendations.append(Recommendation(
                    type=RecommendationType.COIN,
                    item_id=coin_id,
                    title=coin_data["name"],
                    description=f"{coin_data['market_cap']} 마켓캡, {coin_data['liquidity']} 유동성",
                    confidence=confidence,
                    reason=self._get_coin_reason(coin_data, risk_tolerance),
                    priority=2,
                    metadata={
                        "volatility": coin_data["volatility"],
                        "risk_level": coin_data["risk_level"],
                        "liquidity": coin_data["liquidity"]
                    }
                ))
        
        return recommendations
    
    def _recommend_education(
        self,
        user_preferences: UserPreferences
    ) -> List[Recommendation]:
        """교육 콘텐츠 추천"""
        recommendations = []
        
        learning_level = user_preferences.learning_prefs.learning_level
        interested_topics = user_preferences.learning_prefs.interested_topics
        completed = user_preferences.learning_prefs.completed_courses
        
        for edu_id, edu_data in self.education_db.items():
            # 이미 완료한 코스는 제외
            if edu_id in completed:
                continue
            
            # 레벨 매칭
            if edu_data["level"] == learning_level:
                confidence = 0.8
            elif (learning_level == "beginner" and edu_data["level"] == "intermediate"):
                confidence = 0.5
            elif (learning_level == "intermediate" and edu_data["level"] == "advanced"):
                confidence = 0.5
            else:
                confidence = 0.3
            
            # 관심 주제와 매칭
            topic_match = any(
                topic in interested_topics 
                for topic in edu_data["topics"]
            )
            if topic_match:
                confidence += 0.2
            
            if confidence > 0.4:
                recommendations.append(Recommendation(
                    type=RecommendationType.EDUCATION,
                    item_id=edu_id,
                    title=edu_data["title"],
                    description=edu_data["description"],
                    confidence=min(confidence, 1.0),
                    reason=f"{edu_data['level']} 레벨 콘텐츠, {edu_data['duration']}분 소요",
                    priority=3,
                    metadata={
                        "level": edu_data["level"],
                        "duration": edu_data["duration"],
                        "topics": edu_data["topics"]
                    }
                ))
        
        return recommendations
    
    def _recommend_settings(
        self,
        user_preferences: UserPreferences
    ) -> List[Recommendation]:
        """설정 추천"""
        recommendations = []
        
        # 알림 설정 최적화 추천
        if not user_preferences.notification_prefs.daily_summary:
            recommendations.append(Recommendation(
                type=RecommendationType.SETTING,
                item_id="enable_daily_summary",
                title="일일 요약 알림 활성화",
                description="매일 거래 성과를 요약해서 받아보세요",
                confidence=0.7,
                reason="일일 성과 모니터링에 도움이 됩니다",
                priority=3,
                metadata={"setting": "notification_prefs.daily_summary", "value": True}
            ))
        
        # 자동 손절 추천
        if not user_preferences.trading_prefs.auto_stop_loss:
            recommendations.append(Recommendation(
                type=RecommendationType.SETTING,
                item_id="enable_auto_stop_loss",
                title="자동 손절 활성화",
                description="손실을 자동으로 제한하여 리스크를 관리하세요",
                confidence=0.9,
                reason="안전한 거래를 위해 필수적입니다",
                priority=1,
                metadata={"setting": "trading_prefs.auto_stop_loss", "value": True}
            ))
        
        return recommendations
    
    def _recommend_actions(
        self,
        user_preferences: UserPreferences
    ) -> List[Recommendation]:
        """액션 추천 (할 일)"""
        recommendations = []
        
        # 포트폴리오 다각화 추천
        if len(user_preferences.trading_prefs.favorite_coins) < 3:
            recommendations.append(Recommendation(
                type=RecommendationType.ACTION,
                item_id="diversify_portfolio",
                title="포트폴리오 다각화",
                description="리스크 분산을 위해 더 많은 코인에 투자하세요",
                confidence=0.6,
                reason=f"현재 {len(user_preferences.trading_prefs.favorite_coins)}개 코인만 거래 중",
                priority=2,
                metadata={"current_coins": len(user_preferences.trading_prefs.favorite_coins)}
            ))
        
        # 학습 진행 추천
        if len(user_preferences.learning_prefs.completed_courses) == 0:
            recommendations.append(Recommendation(
                type=RecommendationType.ACTION,
                item_id="start_learning",
                title="학습 시작",
                description="기초 교육 과정을 시작하세요",
                confidence=0.8,
                reason="거래 실력 향상을 위한 기초 학습",
                priority=2,
                metadata={}
            ))
        
        return recommendations
    
    def _calculate_strategy_confidence(
        self,
        strategy_data: Dict[str, Any],
        risk_tolerance: RiskTolerance,
        trading_style: TradingStyle
    ) -> float:
        """전략 신뢰도 계산"""
        confidence = 0.5
        
        # 리스크 레벨 매칭
        risk_map = {
            RiskTolerance.VERY_LOW: ["low"],
            RiskTolerance.LOW: ["low", "moderate"],
            RiskTolerance.MODERATE: ["moderate"],
            RiskTolerance.HIGH: ["moderate", "high"],
            RiskTolerance.VERY_HIGH: ["high"]
        }
        
        if strategy_data["risk_level"] in risk_map.get(risk_tolerance, []):
            confidence += 0.3
        
        # 거래 스타일 매칭
        if trading_style == TradingStyle.CONSERVATIVE and strategy_data["risk_level"] == "low":
            confidence += 0.2
        elif trading_style == TradingStyle.AGGRESSIVE and strategy_data["risk_level"] == "high":
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_coin_confidence(
        self,
        coin_data: Dict[str, Any],
        risk_tolerance: RiskTolerance,
        prefer_stable: bool
    ) -> float:
        """코인 신뢰도 계산"""
        confidence = 0.5
        
        # 안정성 선호도
        if prefer_stable:
            if coin_data["market_cap"] == "large":
                confidence += 0.2
            if coin_data["volatility"] < 0.35:
                confidence += 0.2
        else:
            if coin_data["volatility"] > 0.40:
                confidence += 0.1
        
        # 유동성
        if coin_data["liquidity"] in ["very_high", "high"]:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_strategy_reason(
        self,
        strategy_data: Dict[str, Any],
        risk_tolerance: RiskTolerance,
        trading_style: TradingStyle
    ) -> str:
        """전략 추천 이유"""
        reasons = []
        
        reasons.append(f"기대 수익률 {strategy_data['expected_return']}%")
        reasons.append(f"리스크 레벨: {strategy_data['risk_level']}")
        
        if risk_tolerance.value in ["low", "very_low"]:
            reasons.append("안전한 투자 성향에 적합")
        elif risk_tolerance.value == "high":
            reasons.append("공격적 투자 성향에 적합")
        
        return ", ".join(reasons)
    
    def _get_coin_reason(
        self,
        coin_data: Dict[str, Any],
        risk_tolerance: RiskTolerance
    ) -> str:
        """코인 추천 이유"""
        reasons = []
        
        reasons.append(f"{coin_data['market_cap']} 시가총액")
        reasons.append(f"{coin_data['liquidity']} 유동성")
        
        if coin_data["volatility"] < 0.35:
            reasons.append("상대적으로 안정적")
        else:
            reasons.append("높은 수익 가능성")
        
        return ", ".join(reasons)


