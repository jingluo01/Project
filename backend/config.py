import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost:3306/campus_parking'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Parking System Settings
    PAYMENT_TIMEOUT_HOURS = 24  # 24小时未支付视为违约
    CREDIT_PENALTY_TIMEOUT = 30  # 违约扣除信用分
    CREDIT_PENALTY_DELAY = 10  # 超时扣除信用分

    MIN_CREDIT_SCORE = 70  # 最低信用分要求
    PERFECT_CREDIT_SCORE = 100  # 完美信用分
    FEE_MULTIPLIER = 10.0  # 费用倍率因子（开发测试用）
    RESERVATION_TIMEOUT_MINUTES = 180 # 预约超时时间(分钟)，设为3小时
    VIOLATION_FEE = 5.00 # 预约违约金(元)
    
    # Role-based Discount
    ROLE_DISCOUNT = {
        0: 1.0,   # 外部用户，无折扣
        1: 0.9,   # 学生，9折
        2: 0.8,   # 教职工，8折
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False # 关闭 SQL 回显，显著提升控制台性能和 API 响应感受


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
