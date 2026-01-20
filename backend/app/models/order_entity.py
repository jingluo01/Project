from datetime import datetime
from app.extensions import db

class ParkingOrder(db.Model):
    """订单表"""
    __tablename__ = 'parking_order'

    order_id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False, index=True, comment='业务单号')
    
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.spot_id'), nullable=False)
    plate_number = db.Column(db.String(20), nullable=False, comment='实际入场车牌')
    
    # 状态机: 0-已预约, 1-进行中(已入场), 2-待支付, 3-已完成, 4-已取消, 5-退款中, 6-违约
    status = db.Column(db.Integer, default=0, index=True, comment='订单状态')
    
    # 时间轴
    create_time = db.Column(db.DateTime, default=datetime.now, comment='预约时间')
    in_time = db.Column(db.DateTime, nullable=True, comment='入场时间')
    out_time = db.Column(db.DateTime, nullable=True, comment='出场时间')
    pay_time = db.Column(db.DateTime, nullable=True, comment='支付时间')
    
    # 费用
    total_fee = db.Column(db.Numeric(10, 2), default=0.00, comment='总费用')
    real_fee = db.Column(db.Numeric(10, 2), default=0.00, comment='实收费用')

    # 关联关系
    user = db.relationship('SysUser', backref='orders')
    spot = db.relationship('ParkingSpot', backref='orders')