from datetime import datetime
from decimal import Decimal
from app.extensions import db, socketio
from app.models.parking import ParkingZone, ParkingSpot
from app.models.order import ParkingOrder
from app.models.user import SysUser
from app.utils.fee_calculator import calculate_parking_fee
from app.utils.service_utils import handle_service_exception
from flask import current_app

class ParkingService:
    @staticmethod
    def _broadcast_spot_update(spot_id, zone_id, status, current_plate=None):
        """统一 WebSocket 广播逻辑"""
        socketio.emit('spot_status_update', {
            'spot_id': spot_id,
            'zone_id': zone_id,
            'status': status,
            'current_plate': current_plate
        })

    @staticmethod
    def get_zones():
        """获取所有停车区域逻辑"""
        zones = ParkingZone.query.all()
        return {'success': True, 'data': [zone.to_dict() for zone in zones]}, 200

    @staticmethod
    def get_spots(zone_id=None):
        """获取车位实时状态业务逻辑"""
        if zone_id:
            spots = ParkingSpot.query.filter_by(zone_id=zone_id).all()
        else:
            spots = ParkingSpot.query.all()

        # 优化：仅查询本批次车位的预约状态，避免全表扫描
        spot_ids = [s.spot_id for s in spots]
        reserved_orders = ParkingOrder.query.filter(
            ParkingOrder.spot_id.in_(spot_ids),
            ParkingOrder.status == 0
        ).all()
        reserved_spot_map = {order.spot_id: order.plate_number for order in reserved_orders}
        
        spots_data = []
        for spot in spots:
            spot_dict = spot.to_dict()
            if spot.status == 0 and spot.spot_id in reserved_spot_map:
                spot_dict['status'] = 3
                spot_dict['current_plate'] = reserved_spot_map[spot.spot_id]
            spots_data.append(spot_dict)
            
        return {'success': True, 'data': spots_data}, 200

    @staticmethod
    @handle_service_exception(message_prefix="入场失败")
    def vehicle_enter(plate_number):
        """车辆入场业务逻辑"""
        if not plate_number:
            return {'success': False, 'message': '车牌号不能为空'}, 400
        
        order = ParkingOrder.query.filter_by(plate_number=plate_number, status=0).first()
        if not order:
            return {'success': False, 'message': '未找到有效预约订单'}, 404
        
        order.status = 1
        order.in_time = datetime.utcnow()
        
        spot = ParkingSpot.query.get(order.spot_id)
        spot.status = 1
        spot.current_plate = plate_number
        
        db.session.commit()
        ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, spot.status, plate_number)
        
        return {'success': True, 'message': '入场成功', 'data': order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="出场失败")
    def vehicle_exit(plate_number, auto_pay=True):
        """
        车辆出场识别与计费业务逻辑
        
        Args:
            plate_number: 车牌号
            auto_pay: 是否允许自动支付
                     True - 物理设备识别，满足条件可自动支付
                     False - 用户手动操作，强制进入待支付状态
        """
        if not plate_number:
            return {'success': False, 'message': '车牌号不能为空'}, 400
        
        order = ParkingOrder.query.filter_by(plate_number=plate_number, status=1).first()
        if not order:
            return {'success': False, 'message': '未找到进行中的订单'}, 404
        
        order.out_time = datetime.utcnow()
        spot = ParkingSpot.query.get(order.spot_id)
        zone = ParkingZone.query.get(spot.zone_id)
        user = SysUser.query.get(order.user_id)
        
        total_fee = calculate_parking_fee(
            order.in_time,
            order.out_time,
            zone.fee_rate,
            zone.free_time,
            user.role,
            current_app.config['ROLE_DISCOUNT']
        )
        order.total_fee = total_fee
        
        # 只有在 auto_pay=True 且满足条件时才自动支付
        if auto_pay:
            has_violation = ParkingOrder.query.filter_by(user_id=user.user_id, status=6).first()
            if user.credit_score == current_app.config['PERFECT_CREDIT_SCORE'] and not has_violation:
                if user.balance >= total_fee:
                    user.balance -= total_fee
                    order.status = 3
                    order.pay_time = datetime.utcnow()
                    order.pay_way = 0
                else:
                    order.status = 2
            else:
                order.status = 2
        else:
            # 用户手动操作，强制进入待支付状态
            order.status = 2
        
        spot.status = 0
        spot.current_plate = None
        db.session.commit()
        ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, spot.status, None)
        
        return {'success': True, 'message': '出场成功', 'data': order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="场地维护失败")
    def update_parking_or_zone(data):
        """更新车位或区域信息逻辑"""
        if 'spot_id' in data:
            spot = ParkingSpot.query.get(data['spot_id'])
            if not spot: return {'success': False, 'message': '车位不存在'}, 404
            
            if 'status' in data: 
                spot.status = data['status']
                ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, spot.status, spot.current_plate)
            
            db.session.commit()
            return {'success': True, 'message': '车位状态更新成功'}, 200
        
        if 'zone_id' in data:
            zone = ParkingZone.query.get(data['zone_id'])
            if not zone: return {'success': False, 'message': '区域不存在'}, 404
            
            if 'fee_rate' in data: zone.fee_rate = Decimal(str(data['fee_rate']))
            if 'free_time' in data: zone.free_time = data['free_time']
            
            db.session.commit()
            return {'success': True, 'message': '区域费率更新成功'}, 200
        
        return {'success': False, 'message': '缺少必要参数'}, 400
