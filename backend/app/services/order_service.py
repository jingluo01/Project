from datetime import datetime
from decimal import Decimal
from flask import current_app
from app.extensions import db, socketio
from app.models.order import ParkingOrder
from app.models.parking import ParkingSpot, ParkingZone
from app.models.user import SysUser
from app.models.car import Car
from app.utils.service_utils import handle_service_exception

class OrderService:
    @staticmethod
    @handle_service_exception(message_prefix="预约失败")
    def create_order(user, spot_id, plate_number):
        """创建订单业务逻辑"""
        if not spot_id or not plate_number:
            return {'success': False, 'message': '车位ID和车牌号不能为空'}, 400
        
        # 1. 信用分检查
        if user.credit_score < current_app.config['MIN_CREDIT_SCORE']:
            return {'success': False, 'message': f'信用分不足{current_app.config["MIN_CREDIT_SCORE"]}，无法预约'}, 403
        
        # 2. 欠费/违约检查
        unpaid_or_violated = ParkingOrder.query.filter_by(user_id=user.user_id).filter(
            ParkingOrder.status.in_([2, 6])
        ).first()
        if unpaid_or_violated:
            msg = '您有待支付订单，先支付' if unpaid_or_violated.status == 2 else '您有违约记录，请先处理'
            return {'success': False, 'message': msg}, 403

        # 3. 车辆重复检查
        active_car_order = ParkingOrder.query.filter_by(plate_number=plate_number).filter(
            ParkingOrder.status.in_([0, 1])
        ).first()
        if active_car_order:
            status_msg = {0: '该车辆已有预约中的订单', 1: '该车辆当前正在停车中'}
            return {'success': False, 'message': status_msg.get(active_car_order.status, '该车辆已有进行中的订单')}, 403
        
        # 4. 车辆绑定验证
        car = Car.query.filter_by(plate_number=plate_number, user_id=user.user_id).first()
        if not car:
            return {'success': False, 'message': '该车辆未绑定到您的账户'}, 403
        
        # 5. 车位预约冲突检查
        is_spot_reserved = ParkingOrder.query.filter_by(spot_id=spot_id, status=0).first()
        if is_spot_reserved:
            return {'success': False, 'message': '手慢了，该车位已被他人锁定'}, 409

        # 悲观锁锁定车位
        spot = db.session.query(ParkingSpot).with_for_update().filter_by(spot_id=spot_id).first()
        if not spot:
            return {'success': False, 'message': '车位不存在'}, 404
        if spot.status != 0:
            status_msg = {1: '车位已被车辆占用', 2: '车位正在维护中'}
            return {'success': False, 'message': status_msg.get(spot.status, '车位不可用')}, 409
        
        new_order = ParkingOrder(
            order_no=ParkingOrder.generate_order_no(),
            user_id=user.user_id,
            spot_id=spot_id,
            plate_number=plate_number,
            status=0,
            reserve_time=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.commit()
        
        # 发送 WebSocket 通知
        from app.services.parking_service import ParkingService
        ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, 3, plate_number)
        
        return {'success': True, 'message': '预约成功', 'data': new_order.to_dict()}, 201

    @staticmethod
    @handle_service_exception(message_prefix="支付失败")
    def pay_order(user, order_id, pay_way=0):
        """支付订单业务逻辑"""
        if not order_id:
            return {'success': False, 'message': '订单ID不能为空'}, 400
        
        order = ParkingOrder.query.filter_by(order_id=order_id, user_id=user.user_id).first()
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
        if order.status not in [2, 6]:
            return {'success': False, 'message': '订单状态不正确'}, 400
        
        if pay_way == 0:
            if user.balance < order.total_fee:
                return {'success': False, 'message': '余额不足'}, 400
            user.balance -= order.total_fee
        else:
            return {'success': False, 'message': '暂不支持该支付方式'}, 400
        
        order.status = 3
        order.pay_time = datetime.utcnow()
        order.pay_way = pay_way
        db.session.commit()
        
        return {'success': True, 'message': '支付成功', 'data': order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="取消失败")
    def cancel_order(user, order_id):
        """取消预约业务逻辑"""
        if not order_id:
            return {'success': False, 'message': '订单ID不能为空'}, 400
        
        order = ParkingOrder.query.filter_by(order_id=order_id, user_id=user.user_id).first()
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
        if order.status != 0:
            return {'success': False, 'message': '该订单无法取消'}, 400
        
        order.status = 4
        spot = ParkingSpot.query.get(order.spot_id)
        db.session.commit()
        
        if spot:
            from app.services.parking_service import ParkingService
            ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, 0, None)
            
        return {'success': True, 'message': '取消成功', 'data': order.to_dict()}, 200

    @staticmethod
    def search_orders(user, status=None, page=1, per_page=20):
        """统一订单查询逻辑 (优化后的列查询)"""
        # 仅选择必要的列，显著减少数据传输量
        query = db.session.query(
            ParkingOrder, 
            SysUser.username, 
            SysUser.user_no, 
            SysUser.role,
            ParkingSpot.spot_no, 
            ParkingZone.zone_name,
            ParkingZone.zone_id,
            ParkingZone.fee_rate,
            ParkingZone.free_time
        ).join(
            SysUser, ParkingOrder.user_id == SysUser.user_id
        ).join(
            ParkingSpot, ParkingOrder.spot_id == ParkingSpot.spot_id
        ).join(
            ParkingZone, ParkingSpot.zone_id == ParkingZone.zone_id
        )
        
        if user.role != 3: 
            query = query.filter(ParkingOrder.user_id == user.user_id)
        
        if status is not None:
            query = query.filter(ParkingOrder.status == status)
        
        # 权重排序：预约(0)/进行中(1)最优先，待支付(2)/违约(6)其次，已完成等历史最后
        from sqlalchemy import case
        sort_weight = case(
            {0: 0, 1: 0, 2: 1, 6: 1}, 
            value=ParkingOrder.status, 
            else_=2
        )
        
        pagination = query.order_by(sort_weight, ParkingOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders_data = []
        for order, username, user_no, role, spot_no, zone_name, zone_id, fee_rate, free_time in pagination.items:
            o_dict = order.to_dict()
            o_dict.update({
                'username': username,
                'user_no': user_no,
                'user_role': role,
                'spot_no': spot_no,
                'zone_name': zone_name,
                'zone_id': zone_id,
                'fee_rate': float(fee_rate),
                'free_time': free_time
            })
            orders_data.append(o_dict)
            
        return {
            'success': True,
            'data': {
                'orders': orders_data,
                'total': pagination.total,
                'page': page,
                'per_page': per_page
            }
        }, 200

    @staticmethod
    @handle_service_exception(message_prefix="违约处理失败")
    def process_order_violation(order_id, violation_type='payment'):
        """
        统一违约处理业务逻辑 (Phase 4)
        violation_type: 'payment' (支付超时), 'reservation' (预约未入场超时)
        """
        order = ParkingOrder.query.get(order_id)
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
            
        user = SysUser.query.get(order.user_id)
        if not user:
            return {'success': False, 'message': '相关用户不存在'}, 404

        # 1. 更新订单状态为超时违约
        order.status = 6
        
        # 2. 根据类型执行差异化逻辑
        if violation_type == 'reservation':
            # 预约超时：记录违约时间、产生违约金、扣分较多
            order.out_time = datetime.utcnow()
            order.total_fee = Decimal(str(current_app.config.get('VIOLATION_FEE', 5.00)))
            penalty = current_app.config.get('CREDIT_PENALTY_DELAY', 10)
            
            # 释放车位
            spot = ParkingSpot.query.get(order.spot_id)
            if spot:
                from app.services.parking_service import ParkingService
                ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, 0, None)
        else:
            # 支付超时：扣分常态
            penalty = current_app.config.get('CREDIT_PENALTY_TIMEOUT', 5)

        # 3. 扣除信用分
        user.credit_score = max(0, user.credit_score - penalty)
        
        db.session.commit()
        
        msg = f"订单 {order.order_no} ({violation_type}) 违约处理成功，扣除信用分 {penalty}"
        return {'success': True, 'message': msg, 'data': order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="退款失败")
    def refund_order(user, order_id):
        """退款业务逻辑 (支持管理员操作)"""
        if not order_id:
            return {'success': False, 'message': '订单ID不能为空'}, 400
        
        # 管理员可以退款任何人的订单
        if user.role == 3:
            order = ParkingOrder.query.get(order_id)
        else:
            order = ParkingOrder.query.filter_by(order_id=order_id, user_id=user.user_id).first()
            
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
        if order.status != 3:
            return {'success': False, 'message': '该订单无法退款'}, 400
        
        # 退款逻辑：将金额返还给订单的【拥有者】而非操作者
        if order.pay_way == 0:
            owner = SysUser.query.get(order.user_id)
            if owner:
                owner.balance += order.total_fee
                
        order.status = 5
        db.session.commit()
        return {'success': True, 'message': '退款成功', 'data': order.to_dict()}, 200
