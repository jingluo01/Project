from datetime import datetime
from app.extensions import db

class Car(db.Model):
    """车辆表 - 实现人车解耦"""
    __tablename__ = 'car'
    
    car_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id', ondelete='CASCADE'), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False, comment='车牌号')
    nickname = db.Column(db.String(20), nullable=True, comment='车辆备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'car_id': self.car_id,
            'user_id': self.user_id,
            'plate_number': self.plate_number,
            'nickname': self.nickname,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Car {self.plate_number}>'
