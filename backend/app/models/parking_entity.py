from app.extensions import db

class ParkingZone(db.Model):
    """停车区域 (如: A区, B区)"""
    __tablename__ = 'parking_zone'

    zone_id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(50), nullable=False, unique=True, comment='区域名称')
    fee_rate = db.Column(db.Numeric(5, 2), default=5.00, comment='每小时费率')
    free_time = db.Column(db.Integer, default=15, comment='免费时长(分钟)')
    total_spots = db.Column(db.Integer, default=0, comment='总车位数')
    
    # 关系: 一个区域有多个车位
    spots = db.relationship('ParkingSpot', backref='zone', lazy='dynamic')

class ParkingSpot(db.Model):
    """具体车位"""
    __tablename__ = 'parking_spot'

    spot_id = db.Column(db.Integer, primary_key=True)
    spot_no = db.Column(db.String(20), nullable=False, comment='车位编号(如A-001)')
    zone_id = db.Column(db.Integer, db.ForeignKey('parking_zone.zone_id'))
    
    # 状态: 0-空闲, 1-占用(有车), 2-已预约(锁定)
    status = db.Column(db.Integer, default=0, index=True, comment='车位状态')
    
    # 当前停放的车牌 (冗余字段，方便快速查询，不需要连表)
    current_plate = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            'spot_id': self.spot_id,
            'spot_no': self.spot_no,
            'status': self.status,
            'zone_name': self.zone.zone_name if self.zone else ''
        }