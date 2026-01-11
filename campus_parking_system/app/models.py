from . import db
from datetime import datetime

# ================= 用户模型 =================
class User(db.Model):
    __tablename__ = 'sys_user'
    
    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    credit_score = db.Column(db.Integer, default=100)
    
    # 建立与车辆的一对多关系，lazy='dynamic' 允许后续链式查询
    cars = db.relationship('Car', backref='owner', lazy='dynamic')

    def to_dict(self):
        """序列化方法，方便返回 JSON"""
        return {
            'id': self.user_id,
            'username': self.username,
            'role': self.role,
            'credit': self.credit_score
        }

# ================= 车辆模型 =================
class Car(db.Model):
    __tablename__ = 'car'
    
    car_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('sys_user.user_id'), nullable=False)
    plate_number = db.Column(db.String(20), nullable=False)
    # 其他字段如果需要

# ================= 车位模型 =================
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    
    spot_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    spot_no = db.Column(db.String(20), unique=True, nullable=False)
    area_code = db.Column(db.String(10), default='A')
    status = db.Column(db.Integer, default=0)  # 0-空闲, 1-占用, 2-预约
    is_vip = db.Column(db.Integer, default=0)
    version = db.Column(db.Integer, default=0) # 乐观锁版本号

# ================= 订单模型 =================
class Order(db.Model):
    __tablename__ = 'parking_order'
    
    order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(64), unique=True, nullable=False)
    
    # 外键关联
    user_id = db.Column(db.BigInteger, db.ForeignKey('sys_user.user_id'), nullable=False)
    spot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spot.spot_id'), nullable=False)
    
    plate_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.Integer, default=0) # 0-预约, 1-入场...
    
    reserve_start_time = db.Column(db.DateTime)
    reserve_end_time = db.Column(db.DateTime)
    actual_in_time = db.Column(db.DateTime)
    actual_out_time = db.Column(db.DateTime)
    total_fee = db.Column(db.Numeric(10, 2), default=0.00)