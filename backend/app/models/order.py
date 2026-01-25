from datetime import datetime
from app.extensions import db
import uuid

class ParkingOrder(db.Model):
    """订单表 - 记录全生命周期"""
    __tablename__ = 'parking_order'
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='唯一业务单号')
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.spot_id'), nullable=False)
    plate_number = db.Column(db.String(20), nullable=False, comment='车牌号')
    
    # 状态机: 0-已预约, 1-进行中, 2-待支付, 3-已完成, 4-已取消, 5-已退款, 6-超时违约
    status = db.Column(db.Integer, default=0, comment='订单状态')
    
    # 时间轴
    reserve_time = db.Column(db.DateTime, default=datetime.utcnow, comment='预约时间')
    in_time = db.Column(db.DateTime, comment='入场时间')
    out_time = db.Column(db.DateTime, comment='出场时间')
    pay_time = db.Column(db.DateTime, comment='支付时间')
    
    # 费用
    total_fee = db.Column(db.Numeric(10, 2), default=0.00, comment='总费用')
    pay_way = db.Column(db.Integer, comment='0-余额, 1-微信, 2-支付宝')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def generate_order_no():
        """生成唯一订单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4().hex)[:6].upper()
        return f'ORD-{timestamp}{unique_id}'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'spot_id': self.spot_id,
            'plate_number': self.plate_number,
            'status': self.status,
            'reserve_time': self.reserve_time.isoformat() if self.reserve_time else None,
            'in_time': self.in_time.isoformat() if self.in_time else None,
            'out_time': self.out_time.isoformat() if self.out_time else None,
            'pay_time': self.pay_time.isoformat() if self.pay_time else None,
            'total_fee': float(self.total_fee),
            'pay_way': self.pay_way,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ParkingOrder {self.order_no}>'
