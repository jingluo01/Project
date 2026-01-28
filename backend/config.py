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
    # 方案一：多数据库绑定 - 用于交叉验证学校师生数据库
    SQLALCHEMY_BINDS = {
        'school_db': os.getenv(
            'SCHOOL_DATABASE_URL',
            'mysql+pymysql://root:password@localhost:3306/school_official'
        )
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_COOKIE_CSRF_PROTECT = False
    
    # SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Parking System Settings
    PAYMENT_TIMEOUT_HOURS = 24  # 24小时未支付视为违约
    CREDIT_PENALTY_TIMEOUT = 30  # 违约扣除信用分
    CREDIT_PENALTY_DELAY = 10  # 超时扣除信用分

    MIN_CREDIT_SCORE = 70  # 最低信用分要求 (及格线)
    GOOD_CREDIT_SCORE = 85 # 良好信用分要求
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
    
    # Alipay Configuration
    ALIPAY_APPID = os.getenv('ALIPAY_APPID', '')
    ALIPAY_PRIVATE_KEY = os.getenv('ALIPAY_PRIVATE_KEY', '')
    ALIPAY_PUBLIC_KEY = os.getenv('ALIPAY_PUBLIC_KEY', '')
    ALIPAY_GATEWAY = os.getenv('ALIPAY_GATEWAY', 'https://openapi-sandbox.dl.alipaydev.com/gateway.do')
    ALIPAY_RETURN_URL = os.getenv('ALIPAY_RETURN_URL', 'http://localhost:5173/payment/return')


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
