"""
停车服务模块，提供停车区域和车位查询、车辆入场/出场管理及场地维护等功能。
"""

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
    """停车服务类"""

    @staticmethod
    def _broadcast_spot_update(spot_id, zone_id, status, current_plate=None):
        """
        通过 WebSocket 向前端广播车位状态变更并清理相关缓存。

        Args:
            spot_id (int): 车位 ID
            zone_id (int): 区域 ID
            status (int): 新的状态标识
            current_plate (str, optional): 停靠车辆的车牌号. Defaults to None.
        """
        socketio.emit('spot_status_update', {
            'spot_id': spot_id,
            'zone_id': zone_id,
            'status': status,
            'current_plate': current_plate
        })
        ParkingService._clear_spots_cache(zone_id)

    @staticmethod
    def _clear_spots_cache(zone_id=None):
        """
        清理 Redis 中的车位及区域缓存列表。

        Args:
            zone_id (int, optional): 指定需清理的区域 ID。若无则清理全部车位及区域缓存。Defaults to None.
        """
        from app.extensions import redis_client
        if not redis_client: return
        try:
            if zone_id:
                redis_client.delete(f'parking:spots:{zone_id}')
            else:
                keys = redis_client.keys('parking:spots:*')
                if keys: redis_client.delete(*keys)
            redis_client.delete('parking:zones:all')
        except:
            pass

    @staticmethod
    def get_zones():
        """
        获取所有停车区域信息，优先使用 Redis 缓存读取。

        Returns:
            tuple: 包含停车区域列表数据 (dict) 和 HTTP 状态码 (int) 的元组
        """
        from app.extensions import redis_client
        import json
        
        cache_key = 'parking:zones:all'
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return {'success': True, 'data': json.loads(cached_data)}, 200
            except:
                pass

        zones = ParkingZone.query.all()
        data = [zone.to_dict() for zone in zones]
        
        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(data))
            except:
                pass
                
        return {'success': True, 'data': data}, 200

    @staticmethod
    def get_spots(zone_id=None):
        """
        获取车位实时状态业务逻辑，含高并发条件下的短时缓存保护，避免雪崩效应。

        Args:
            zone_id (int, optional): 指定区域 ID 以筛选车位. Defaults to None.

        Returns:
            tuple: 包含车位数据列表 (dict) 和 HTTP 状态码 (int) 的元组
        """
        from app.extensions import redis_client
        import json
        
        cache_key = f'parking:spots:{zone_id if zone_id else "all"}'
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return {'success': True, 'data': json.loads(cached_data)}, 200
            except:
                pass

        if zone_id:
            spots = ParkingSpot.query.filter_by(zone_id=zone_id).all()
        else:
            spots = ParkingSpot.query.all()

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
            
        if redis_client:
            try:
                redis_client.setex(cache_key, 3, json.dumps(spots_data))
            except:
                pass
            
        return {'success': True, 'data': spots_data}, 200

    @staticmethod
    @handle_service_exception(message_prefix="入场失败")
    def vehicle_enter(plate_number):
        """
        处理车辆入场业务逻辑。验证预约订单并更新车位状态，通知 WebSocket。

        Args:
            plate_number (str): 入场车辆车牌号

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
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
        处理车辆出场识别及计费逻辑。
        
        Args:
            plate_number (str): 车牌号
            auto_pay (bool, optional): 是否允许自动支付. True - 物理设备识别，满足条件可自动支付；False - 用户手动操作，强制待支付状态. Defaults to True.

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
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
            order.status = 2
        
        spot.status = 0
        spot.current_plate = None
        db.session.commit()
        ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, spot.status, None)
        
        return {'success': True, 'message': '出场成功', 'data': order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="场地维护失败")
    def update_parking_or_zone(data):
        """
        处理修改车位状态或区域配置信息逻辑。

        Args:
            data (dict): 包含 `spot_id` 或 `zone_id` 及其更新内容的字典

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
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
            
            from app.extensions import redis_client
            if redis_client:
                try:
                    redis_client.delete('parking:zones:all')
                except:
                    pass
                    
            return {'success': True, 'message': '区域费率更新成功'}, 200
        
        return {'success': False, 'message': '缺少必要参数'}, 400
