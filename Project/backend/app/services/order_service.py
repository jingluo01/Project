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
        
        # 1. 信用分检查 (动态读取数据库配置)
        from app.models.config import SysConfig
        min_score = int(SysConfig.get_value('MIN_CREDIT_SCORE', current_app.config.get('MIN_CREDIT_SCORE', 70)))
        
        if user.credit_score < min_score:
            return {'success': False, 'message': f'您的信用分({user.credit_score})低于及格线({min_score})，禁止预约'}, 403
        
        # 2. 违约检查 (全局检查：只要有违约记录未处理，无论哪辆车都不能预约)
        violation_order = ParkingOrder.query.filter(
            ParkingOrder.user_id == user.user_id,
            ParkingOrder.status == 6
        ).first()
        if violation_order:
            return {'success': False, 'message': '您有违约记录未处理，请联系管理员或处理欠费以恢复信用'}, 403
 
        # 3. 车辆状态检查 (针对当前车牌：预约中、停车中、待支付 状态下不能再次预约)
        active_car_order = ParkingOrder.query.filter(
            ParkingOrder.plate_number == plate_number,
            ParkingOrder.status.in_([0, 1, 2])
        ).first()
        if active_car_order:
            status_desc = {0: '预约中', 1: '停车中', 2: '待支付'}
            return {'success': False, 'message': f'该车辆({plate_number})当前处于{status_desc.get(active_car_order.status, "活跃")}状态，不能重复预约'}, 403
        
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
        """取消预约业务逻辑 (支持管理员强制操作)"""
        if not order_id:
            return {'success': False, 'message': '订单ID不能为空'}, 400
        
        # 管理员权限：可以查询跨用户的订单
        if user.role == 3:
            order = ParkingOrder.query.get(order_id)
        else:
            order = ParkingOrder.query.filter_by(order_id=order_id, user_id=user.user_id).first()
            
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
        if order.status != 0:
            return {'success': False, 'message': '该订单当前状态无法取消'}, 400
        
        order.status = 4
        spot = ParkingSpot.query.get(order.spot_id)
        db.session.commit()
        
        if spot:
            from app.services.parking_service import ParkingService
            ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, 0, None)
            
        return {'success': True, 'message': '取消成功', 'data': order.to_dict()}, 200

    @staticmethod
    def search_orders(user, status=None, page=1, per_page=20, start_date=None, end_date=None, query_keyword=None):
        """统一订单查询逻辑 (支持多维查询过滤)"""
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
        
        # 权限隔离
        if user.role != 3: 
            query = query.filter(ParkingOrder.user_id == user.user_id)
        
        # 状态过滤
        if status is not None:
            query = query.filter(ParkingOrder.status == status)
            
        # 日期范围过滤
        if start_date:
            query = query.filter(ParkingOrder.created_at >= start_date)
        if end_date:
            query = query.filter(ParkingOrder.created_at <= end_date)
            
        # 关键词搜索 (订单号、车牌、用户名、学号)
        if query_keyword:
            k = f"%{query_keyword}%"
            query = query.filter(db.or_(
                ParkingOrder.order_no.like(k),
                ParkingOrder.plate_number.like(k),
                SysUser.username.like(k),
                SysUser.user_no.like(k)
            ))
        
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
        elif order.pay_way == 2:
            from app.services.alipay_service import AlipayService
            # 调用支付宝原路退款接口
            result, code = AlipayService.refund_payment(order.order_no, order.total_fee)
            if not result.get('success'):
                return result, code
                
        order.status = 5
        db.session.commit()
        return {'success': True, 'message': '已按原支付方式退款成功', 'data': order.to_dict()}, 200
