from datetime import datetime
from app.extensions import db

class SysUser(db.Model):
    """用户表"""
    __tablename__ = 'sys_user'

    user_id = db.Column(db.Integer, primary_key=True, comment='用户ID')
    username = db.Column(db.String(64), unique=True, nullable=False, comment='用户名')
    user_no = db.Column(db.String(32), unique=True, nullable=True, comment='学号/工号')
    password_hash = db.Column(db.String(128), nullable=False, comment='加密密码')
    
    # 角色: 0-校外人员, 1-学生, 2-教职工 (影响计费费率)
    role = db.Column(db.Integer, default=1, comment='角色')
    
    balance = db.Column(db.Numeric(10, 2), default=0.00, comment='余额')
    credit_score = db.Column(db.Integer, default=100, comment='信用分')
    is_active = db.Column(db.Boolean, default=True, comment='是否冻结')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='注册时间')

    # 关系: 一个用户有多辆车
    cars = db.relationship('Car', backref='owner', lazy='dynamic')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'user_no': self.user_no,
            'role': self.role,
            'credit_score': self.credit_score,
            'balance': float(self.balance)
        }

class Car(db.Model):
    """车辆表"""
    __tablename__ = 'car'

    car_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id'), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False, index=True, comment='车牌号')
    create_time = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'car_id': self.car_id,
            'plate_number': self.plate_number
        }