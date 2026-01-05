"""
피드백 수집 시스템
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path


class FeedbackType(Enum):
    """피드백 유형"""
    RATING = "rating"                    # 평점
    FEATURE_FEEDBACK = "feature_feedback"  # 기능 피드백
    RECOMMENDATION_FEEDBACK = "recommendation_feedback"  # 추천 피드백
    IMPROVEMENT = "improvement"          # 개선 제안
    BUG_REPORT = "bug_report"           # 버그 리포트
    SATISFACTION = "satisfaction"        # 만족도 조사


@dataclass
class Feedback:
    """피드백 데이터 구조"""
    user_id: str
    feedback_type: FeedbackType
    timestamp: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "feedback_type": self.feedback_type.value,
            "timestamp": self.timestamp,
            "content": self.content,
            "metadata": self.metadata or {}
        }


class FeedbackCollector:
    """피드백 수집 및 관리 시스템"""
    
    def __init__(self, feedback_dir: str = "data/user_feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # 피드백 캐시
        self.feedback_cache: Dict[str, List[Feedback]] = {}
    
    def collect_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """피드백 수집"""
        feedback = Feedback(
            user_id=user_id,
            feedback_type=feedback_type,
            timestamp=datetime.now().isoformat(),
            content=content,
            metadata=metadata or {}
        )
        
        # 캐시에 추가
        if user_id not in self.feedback_cache:
            self.feedback_cache[user_id] = []
        self.feedback_cache[user_id].append(feedback)
        
        # 파일에 저장
        self._save_feedback(feedback)
        
        return feedback
    
    def collect_rating(
        self,
        user_id: str,
        item_type: str,  # "strategy", "coin", "feature", etc.
        item_id: str,
        rating: int,  # 1-5
        comment: Optional[str] = None
    ) -> Feedback:
        """평점 피드백 수집"""
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.RATING,
            content={
                "item_type": item_type,
                "item_id": item_id,
                "rating": rating,
                "comment": comment
            },
            metadata={"source": "user_rating"}
        )
    
    def collect_feature_feedback(
        self,
        user_id: str,
        feature: str,
        rating: int,  # 1-5
        usefulness: Optional[int] = None,  # 1-5
        ease_of_use: Optional[int] = None,  # 1-5
        comment: Optional[str] = None
    ) -> Feedback:
        """기능 피드백 수집"""
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.FEATURE_FEEDBACK,
            content={
                "feature": feature,
                "rating": rating,
                "usefulness": usefulness,
                "ease_of_use": ease_of_use,
                "comment": comment
            },
            metadata={"source": "feature_feedback"}
        )
    
    def collect_recommendation_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        accepted: bool,
        reason: Optional[str] = None,
        actual_rating: Optional[int] = None  # 실제 사용 후 평점
    ) -> Feedback:
        """추천 피드백 수집"""
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.RECOMMENDATION_FEEDBACK,
            content={
                "recommendation_id": recommendation_id,
                "accepted": accepted,
                "reason": reason,
                "actual_rating": actual_rating
            },
            metadata={"source": "recommendation_feedback"}
        )
    
    def collect_improvement_suggestion(
        self,
        user_id: str,
        area: str,  # "dashboard", "trading", "notifications", etc.
        suggestion: str,
        priority: Optional[str] = None  # "low", "medium", "high"
    ) -> Feedback:
        """개선 제안 수집"""
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.IMPROVEMENT,
            content={
                "area": area,
                "suggestion": suggestion,
                "priority": priority or "medium"
            },
            metadata={"source": "improvement_suggestion"}
        )
    
    def collect_satisfaction_survey(
        self,
        user_id: str,
        overall_satisfaction: int,  # 1-5
        ease_of_use: int,  # 1-5
        usefulness: int,  # 1-5
        would_recommend: bool,
        comments: Optional[str] = None
    ) -> Feedback:
        """만족도 조사 수집"""
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.SATISFACTION,
            content={
                "overall_satisfaction": overall_satisfaction,
                "ease_of_use": ease_of_use,
                "usefulness": usefulness,
                "would_recommend": would_recommend,
                "comments": comments
            },
            metadata={"source": "satisfaction_survey"}
        )
    
    def collect_implicit_feedback(
        self,
        user_id: str,
        action: str,
        context: Dict[str, Any]
    ) -> Feedback:
        """암묵적 피드백 수집 (사용자 행동 기반)"""
        # 예: 추천을 클릭했는지, 얼마나 오래 봤는지 등
        return self.collect_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.RECOMMENDATION_FEEDBACK,
            content={
                "action": action,
                "context": context
            },
            metadata={"source": "implicit", "action": action}
        )
    
    def get_user_feedback(
        self,
        user_id: str,
        feedback_type: Optional[FeedbackType] = None,
        limit: Optional[int] = None
    ) -> List[Feedback]:
        """사용자 피드백 조회"""
        # 캐시 확인
        if user_id in self.feedback_cache:
            feedbacks = self.feedback_cache[user_id]
        else:
            # 파일에서 로드
            feedbacks = self._load_user_feedback(user_id)
            self.feedback_cache[user_id] = feedbacks
        
        # 타입 필터링
        if feedback_type:
            feedbacks = [
                f for f in feedbacks
                if f.feedback_type == feedback_type
            ]
        
        # 정렬 (최신순)
        feedbacks.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 제한
        if limit:
            feedbacks = feedbacks[:limit]
        
        return feedbacks
    
    def get_feedback_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """피드백 요약 통계"""
        feedbacks = self.get_user_feedback(user_id)
        
        if not feedbacks:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "satisfaction_score": 0.0,
                "feedback_by_type": {},
                "recent_feedback_count": 0
            }
        
        # 타입별 개수
        feedback_by_type = {}
        for feedback in feedbacks:
            ftype = feedback.feedback_type.value
            feedback_by_type[ftype] = feedback_by_type.get(ftype, 0) + 1
        
        # 평균 평점
        ratings = []
        satisfaction_scores = []
        
        for feedback in feedbacks:
            content = feedback.content
            if "rating" in content:
                ratings.append(content["rating"])
            if feedback.feedback_type == FeedbackType.SATISFACTION:
                if "overall_satisfaction" in content:
                    satisfaction_scores.append(content["overall_satisfaction"])
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores
            else 0.0
        )
        
        # 최근 피드백 (7일)
        from datetime import timedelta
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_feedback = [
            f for f in feedbacks
            if datetime.fromisoformat(f.timestamp) > recent_cutoff
        ]
        
        return {
            "total_feedback": len(feedbacks),
            "average_rating": round(avg_rating, 2),
            "satisfaction_score": round(avg_satisfaction, 2),
            "feedback_by_type": feedback_by_type,
            "recent_feedback_count": len(recent_feedback),
            "feedback_trend": self._calculate_feedback_trend(feedbacks)
        }
    
    def _calculate_feedback_trend(
        self,
        feedbacks: List[Feedback]
    ) -> str:
        """피드백 트렌드 계산"""
        if len(feedbacks) < 2:
            return "stable"
        
        # 최근 10개와 그 이전 10개 비교
        recent = feedbacks[:10]
        older = feedbacks[10:20] if len(feedbacks) > 10 else []
        
        if not older:
            return "stable"
        
        # 평점 비교
        recent_ratings = [
            f.content.get("rating", 0)
            for f in recent
            if "rating" in f.content
        ]
        older_ratings = [
            f.content.get("rating", 0)
            for f in older
            if "rating" in f.content
        ]
        
        if not recent_ratings or not older_ratings:
            return "stable"
        
        recent_avg = sum(recent_ratings) / len(recent_ratings)
        older_avg = sum(older_ratings) / len(older_ratings)
        
        diff = recent_avg - older_avg
        
        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"
    
    def get_aggregated_feedback(
        self,
        item_type: Optional[str] = None,
        item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """집계된 피드백 (모든 사용자)"""
        # 모든 피드백 파일 스캔
        all_feedbacks = []
        
        for feedback_file in self.feedback_dir.glob("*.json"):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_feedbacks.extend(data)
                    else:
                        all_feedbacks.append(data)
            except:
                continue
        
        # 필터링
        if item_type and item_id:
            filtered = [
                f for f in all_feedbacks
                if f.get("content", {}).get("item_type") == item_type
                and f.get("content", {}).get("item_id") == item_id
            ]
        else:
            filtered = all_feedbacks
        
        # 통계 계산
        ratings = [
            f.get("content", {}).get("rating", 0)
            for f in filtered
            if "rating" in f.get("content", {})
        ]
        
        return {
            "total_feedback": len(filtered),
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
            "rating_distribution": self._calculate_rating_distribution(ratings),
            "feedback_count": len(filtered)
        }
    
    def _calculate_rating_distribution(
        self,
        ratings: List[int]
    ) -> Dict[int, int]:
        """평점 분포 계산"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            if 1 <= rating <= 5:
                distribution[rating] = distribution.get(rating, 0) + 1
        return distribution
    
    def _save_feedback(self, feedback: Feedback) -> None:
        """피드백 저장"""
        feedback_file = self.feedback_dir / f"{feedback.user_id}_feedback.json"
        
        # 기존 피드백 로드
        existing_feedbacks = []
        if feedback_file.exists():
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    existing_feedbacks = json.load(f)
            except:
                existing_feedbacks = []
        
        # 새 피드백 추가
        existing_feedbacks.append(feedback.to_dict())
        
        # 최근 1000개만 유지
        if len(existing_feedbacks) > 1000:
            existing_feedbacks = existing_feedbacks[-1000:]
        
        # 저장
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(existing_feedbacks, f, ensure_ascii=False, indent=2)
    
    def _load_user_feedback(self, user_id: str) -> List[Feedback]:
        """사용자 피드백 로드"""
        feedback_file = self.feedback_dir / f"{user_id}_feedback.json"
        
        if not feedback_file.exists():
            return []
        
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            feedbacks = []
            for item in data:
                feedback = Feedback(
                    user_id=item["user_id"],
                    feedback_type=FeedbackType(item["feedback_type"]),
                    timestamp=item["timestamp"],
                    content=item["content"],
                    metadata=item.get("metadata", {})
                )
                feedbacks.append(feedback)
            
            return feedbacks
        except:
            return []





