from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
import redis

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
jwt = JWTManager()
redis_client = None

def init_redis(app):
    """Initialize Redis client"""
    global redis_client
    redis_url = app.config['REDIS_URL']
    redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client
