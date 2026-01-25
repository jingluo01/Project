from flask import Flask
from flask_cors import CORS
from config import config
from app.extensions import db, socketio, init_redis

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    init_redis(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*').split(','))
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.user import user_bp
    from app.blueprints.parking import parking_bp
    from app.blueprints.order import order_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(parking_bp, url_prefix='/api/parking')
    app.register_blueprint(order_bp, url_prefix='/api/order')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Register SocketIO events
    from app.blueprints.parking import register_socketio_events
    register_socketio_events(socketio)
    
    return app
