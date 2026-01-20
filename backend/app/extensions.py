from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_redis import FlaskRedis

# 初始化插件对象，但在 app_factory 中才真正绑定 app
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*") # 允许跨域
redis_client = FlaskRedis()