from functools import wraps
from app.extensions import db

def handle_service_exception(message_prefix="操作失败"):
    """
    Service 层通用异常处理装饰器 (实现 DRY)
    自动处理 rollback 并返回标准错误格式
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'message': f'{message_prefix}: {str(e)}'}, 500
        return decorated_function
    return decorator
