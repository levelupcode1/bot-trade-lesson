"""
웹 API 라우트
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any

# 블루프린트 생성
api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/status', methods=['GET'])
def get_status():
    """
    시스템 상태 조회
    """
    # TODO: 구현 필요
    return jsonify({"status": "ok"})


@api.route('/trades', methods=['GET'])
def get_trades():
    """
    거래 내역 조회
    """
    # TODO: 구현 필요
    return jsonify({"trades": []})


@api.route('/strategies', methods=['GET'])
def get_strategies():
    """
    전략 목록 조회
    """
    # TODO: 구현 필요
    return jsonify({"strategies": []})


@api.route('/config', methods=['GET', 'POST'])
def manage_config():
    """
    설정 관리
    """
    if request.method == 'GET':
        # TODO: 설정 조회
        return jsonify({"config": {}})
    elif request.method == 'POST':
        # TODO: 설정 저장
        return jsonify({"message": "Configuration saved"})

