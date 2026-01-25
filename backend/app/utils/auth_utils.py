from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from app.models.user import SysUser

def hash_password(password):
    """Hash password"""
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """Verify password"""
    return check_password_hash(password_hash, password)

def generate_token(user_id, role):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator for token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': 'Token格式错误'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': '缺少认证token'}), 401
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        # Get current user
        current_user = SysUser.query.get(payload['user_id'])
        if not current_user or not current_user.is_active:
            return jsonify({'success': False, 'message': '用户不存在或已被禁用'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator for admin authentication"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 3:  # 3 = admin
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated
