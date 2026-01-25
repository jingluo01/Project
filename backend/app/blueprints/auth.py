from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    result, status_code = AuthService.login(
        data.get('user_no'),
        data.get('password')
    )
    return jsonify(result), status_code

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    result, status_code = AuthService.register(
        data.get('user_no'),
        data.get('username'),
        data.get('password'),
        data.get('role', 1)
    )
    return jsonify(result), status_code

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """密码重置"""
    data = request.get_json()
    result, status_code = AuthService.reset_password(
        data.get('user_no'),
        data.get('new_password')
    )
    return jsonify(result), status_code
