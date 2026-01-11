from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # <--- 新增导入
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # --- 新增 CORS 配置 ---
    # 允许所有路由(/api/*) 被跨域访问
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.parking import parking_bp
    app.register_blueprint(parking_bp, url_prefix='/api/parking')

    return app