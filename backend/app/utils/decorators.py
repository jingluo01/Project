from functools import wraps
from flask import request, g
from app.utils.jwt_util import JwtUtil
from app.common.response import Result

def login_required(f):
    """
    JWT 鉴权装饰器
    放在 Controller 方法上，解析 Header 中的 Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 获取 Header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Result.error(code=401, msg='未提供认证令牌')
        
        # 2. 提取 Token (格式通常为 "Bearer <token>")
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return Result.error(code=401, msg='令牌格式错误')

        # 3. 解析 Token
        user_id = JwtUtil.decode_token(token)
        if isinstance(user_id, str): # 解析出错返回的是错误字符串
            return Result.error(code=401, msg='令牌无效或已过期')

        # 4. 存入 g 变量，后续流程可直接用 g.user_id 获取当前用户
        g.user_id = user_id
        
        return f(*args, **kwargs)
    return decorated_function