from flask import Flask
from config import config
from app.extensions import db, migrate, socketio, redis_client

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 1. 加载配置
    app.config.from_object(config[config_name])
    
    # 2. 初始化扩展
    register_extensions(app)
    
    # 3. 导入模型 (必须在 db.init_app 之后)
    from app.models import SysUser, Car, ParkingZone, ParkingSpot, ParkingOrder
    
    # 4. 注册蓝图 (Controller)
    register_blueprints(app)
    
    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "Smart Parking System is running..."}

    return app

def register_extensions(app):
    """绑定插件与 App"""
    db.init_app(app)
    migrate.init_app(app, db)
    redis_client.init_app(app)
    socketio.init_app(app)

def register_blueprints(app):
    """注册所有蓝图"""
    # 认证相关接口
    from app.routes.auth_controller import auth_bp
    app.register_blueprint(auth_bp)
    
    # 用户相关接口
    from app.routes.user_controller import user_bp
    app.register_blueprint(user_bp)
    
    print("✅ 已注册蓝图:")
    print(f"   - auth_bp: {auth_bp.url_prefix}")
    print(f"   - user_bp: {user_bp.url_prefix}")
    
    # 未来可以在这里添加更多蓝图
    # from app.routes.parking_controller import parking_bp
    # app.register_blueprint(parking_bp)