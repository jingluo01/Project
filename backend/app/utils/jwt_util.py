import jwt
import datetime
from flask import current_app

class JwtUtil:
    @staticmethod
    def generate_token(user_id):
        """生成 JWT Token"""
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1), # 过期时间 1天
                'iat': datetime.datetime.utcnow(), # 签发时间
                'sub': user_id # 主体
            }
            # 使用配置中的 SECRET_KEY 进行签名
            return jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return str(e)

    @staticmethod
    def decode_token(token):
        """解析 Token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY'),
                algorithms=['HS256']
            )
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'EXPIRED'
        except jwt.InvalidTokenError:
            return 'INVALID'