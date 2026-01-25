from datetime import datetime
from app.extensions import db

class SysUser(db.Model):
    """用户表 - 存储账户信息"""
    __tablename__ = 'sys_user'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_no = db.Column(db.String(50), unique=True, nullable=False, comment='学号/工号')
    username = db.Column(db.String(100), nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码hash')
    role = db.Column(db.Integer, default=1, comment='0-外部用户, 1-学生, 2-教职工, 3-管理员')
    balance = db.Column(db.Numeric(10, 2), default=0.00, comment='余额')
    credit_score = db.Column(db.Integer, default=100, comment='信用分')
    is_active = db.Column(db.Boolean, default=True, comment='账号状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cars = db.relationship('Car', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('ParkingOrder', backref='user', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'user_no': self.user_no,
            'username': self.username,
            'role': self.role,
            'balance': float(self.balance),
            'credit_score': self.credit_score,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<SysUser {self.username}>'
