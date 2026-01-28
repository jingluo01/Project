from flask import Flask
from flask_cors import CORS
from config import config
from app.extensions import db, socketio, init_redis, jwt

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    jwt.init_app(app)
    
    # JWT Error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {"success": False, "message": "Signature verification failed", "error": "invalid_token"}, 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {"success": False, "message": "Request does not contain an access token", "error": "authorization_header_missing"}, 401
    init_redis(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*').split(','))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.parking import parking_bp
    from app.routes.order import order_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payment_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(parking_bp, url_prefix='/api/parking')
    app.register_blueprint(order_bp, url_prefix='/api/order')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(payment_bp)  # payment_bp已经在定义时指定了url_prefix
    
    # Register SocketIO events
    from app.routes.parking import register_socketio_events
    register_socketio_events(socketio)
    
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        from app.models import user, parking, order, car, config as sys_config, school
        db.create_all()
    
    return app
