import os

class Config:
    # 替换为你自己的 MySQL 密码和数据库名
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/campus_parking_db?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'dev-secret-key'  # 用于 session 加密