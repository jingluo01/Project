from datetime import datetime
from app.extensions import db

class ParkingZone(db.Model):
    """停车场区域表"""
    __tablename__ = 'parking_zone'
    
    zone_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_name = db.Column(db.String(100), nullable=False, comment='区域名称，如A区-教学楼')
    map_file_path = db.Column(db.String(255), comment='地图资源路径')
    fee_rate = db.Column(db.Numeric(10, 2), default=5.00, comment='每小时费率')
    free_time = db.Column(db.Integer, default=15, comment='免费时长(分钟)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    spots = db.relationship('ParkingSpot', backref='zone', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'zone_id': self.zone_id,
            'zone_name': self.zone_name,
            'map_file_path': self.map_file_path,
            'fee_rate': float(self.fee_rate),
            'free_time': self.free_time,
            'total_spots': self.spots.count(),
            'available_spots': self.spots.filter_by(status=0).count()
        }
    
    def __repr__(self):
        return f'<ParkingZone {self.zone_name}>'


class ParkingSpot(db.Model):
    """车位表"""
    __tablename__ = 'parking_spot'
    
    spot_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_no = db.Column(db.String(20), nullable=False, comment='车位编号，如A-001')
    zone_id = db.Column(db.Integer, db.ForeignKey('parking_zone.zone_id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Integer, default=0, comment='0-空闲, 1-占用, 2-维修')
    current_plate = db.Column(db.String(20), comment='当前停放车牌')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('ParkingOrder', backref='spot', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'spot_id': self.spot_id,
            'spot_no': self.spot_no,
            'zone_id': self.zone_id,
            'status': self.status,
            'current_plate': self.current_plate,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_no}>'
