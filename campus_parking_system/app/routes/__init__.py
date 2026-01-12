"""
路由模块初始化
"""
from .auth import auth_bp
from .spots import spots_bp
from .orders import orders_bp
from .admin import admin_bp
from .stats import stats_bp

def register_blueprints(app):
    """注册所有蓝图"""
    # 认证路由
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 停车相关路由
    app.register_blueprint(spots_bp, url_prefix='/api/parking')
    app.register_blueprint(orders_bp, url_prefix='/api/parking')
    app.register_blueprint(admin_bp, url_prefix='/api/parking')
    app.register_blueprint(stats_bp, url_prefix='/api/parking')