"""
커스텀 전략 템플릿 (고급자용)
"""

from ..strategy_registry import BaseStrategy


class CustomStrategyTemplate(BaseStrategy):
    """
    커스텀 전략 템플릿
    
    고급 사용자는 이 템플릿을 복사하여 자신만의 전략을 만들 수 있습니다.
    """
    
    def __init__(self, **params):
        """전략 파라미터 초기화"""
        self.params = params
    
    def execute(self, *args, **kwargs):
        """
        전략 실행 로직
        
        여기에 사용자의 전략 로직을 구현합니다.
        """
        # 사용자 전략 로직
        pass
    
    def backtest(self, historical_data):
        """백테스트 로직 (선택사항)"""
        pass
    
    def optimize(self, data):
        """파라미터 최적화 로직 (선택사항)"""
        pass

