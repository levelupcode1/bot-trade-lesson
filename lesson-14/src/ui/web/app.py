"""
Flask 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from typing import Optional
import os
import logging

from ...user.profile.profile_manager import ProfileManager
from ...user.profile.user_profile import UserType
from ...user.auth.authorization import Authorization
from ...strategy.strategy_loader import StrategyLoader
from ...config.config_manager import ConfigManager


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Flask 앱 생성
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')


# 서비스 인스턴스
profile_manager = ProfileManager()
authorization = Authorization()
strategy_loader = StrategyLoader()
config_manager = ConfigManager()


@app.route('/')
def index():
    """메인 페이지"""
    # 세션에서 사용자 정보 가져오기
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    # 프로필 로드
    profile = profile_manager.load_profile(user_id)
    if not profile:
        return redirect(url_for('login'))
    
    # 프로필에 따라 다른 대시보드 렌더링
    template_map = {
        UserType.BEGINNER: 'beginner/dashboard.html',
        UserType.INTERMEDIATE: 'intermediate/dashboard.html',
        UserType.ADVANCED: 'advanced/dashboard.html',
    }
    
    template = template_map.get(profile.user_type, 'beginner/dashboard.html')
    
    return render_template(
        template,
        profile=profile,
        user_id=user_id
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_type = request.form.get('user_type', 'beginner')
        investment_amount = float(request.form.get('investment_amount', 1000000))
        
        # 프로필 로드 또는 생성
        profile = profile_manager.load_profile(user_id)
        
        if not profile:
            # 새 프로필 생성
            user_type_enum = UserType(user_type)
            profile = profile_manager.create_profile(
                user_id=user_id,
                user_type=user_type_enum,
                investment_amount=investment_amount
            )
            logger.info(f"새 프로필 생성: {user_id} ({user_type})")
        
        # 세션에 저장
        session['user_id'] = user_id
        session['user_type'] = profile.user_type.value
        
        return redirect(url_for('index'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    """프로필 설정 페이지"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    profile = profile_manager.load_profile(user_id)
    if not profile:
        return redirect(url_for('login'))
    
    return render_template(
        'profile.html',
        profile=profile
    )


@app.route('/api/strategies')
def api_strategies():
    """사용 가능한 전략 목록 API"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    profile = profile_manager.load_profile(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    # 사용 가능한 전략 목록
    strategies = strategy_loader.get_strategies_for_profile(profile)
    
    return jsonify({"strategies": strategies})


@app.route('/api/permissions')
def api_permissions():
    """사용자 권한 목록 API"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    profile = profile_manager.load_profile(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    # 권한 정보
    available_features = authorization.get_available_features(profile)
    restricted_features = authorization.get_restricted_features(profile)
    
    return jsonify({
        "available_features": available_features,
        "restricted_features": restricted_features
    })


@app.route('/api/validate_action', methods=['POST'])
def api_validate_action():
    """액션 검증 API"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    profile = profile_manager.load_profile(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    data = request.json
    action = data.get('action')
    context = data.get('context', {})
    
    # 액션 검증
    is_valid, error_msg = authorization.validate_action(profile, action, context)
    
    return jsonify({
        "valid": is_valid,
        "error": error_msg
    })


@app.route('/api/upgrade_profile', methods=['POST'])
def api_upgrade_profile():
    """프로필 업그레이드 API"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # 프로필 업그레이드
    new_profile = profile_manager.upgrade_profile(user_id)
    
    if new_profile:
        session['user_type'] = new_profile.user_type.value
        return jsonify({
            "success": True,
            "new_type": new_profile.user_type.value
        })
    else:
        return jsonify({
            "success": False,
            "error": "이미 최고 레벨입니다"
        })


def create_app(config=None):
    """애플리케이션 팩토리"""
    if config:
        app.config.update(config)
    
    # 전략 로드
    strategy_loader.load_all_strategies()
    logger.info("애플리케이션 초기화 완료")
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

