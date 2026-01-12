from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # CORS 配置
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # SocketIO 配置 - 使用threading模式，稳定配置
    socketio.init_app(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        logger=False,
        engineio_logger=False,
        ping_timeout=120,
        ping_interval=60,
        transports=['websocket', 'polling']
    )

    # 注册蓝图
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # 注册 WebSocket 事件处理器
    from app.services.websocket_service import register_websocket_handlers
    register_websocket_handlers()

    return app