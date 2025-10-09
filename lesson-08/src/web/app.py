"""
Flask 웹 애플리케이션
"""

from flask import Flask
from pathlib import Path


def create_app():
    """
    Flask 앱 생성 및 설정
    
    Returns:
        Flask 앱 인스턴스
    """
    app = Flask(__name__)
    
    # 설정 로드
    # TODO: 구현 필요
    
    # 라우트 등록
    # TODO: 구현 필요
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

