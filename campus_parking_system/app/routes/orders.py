"""
订单管理相关路由
"""
from flask import Blueprint, jsonify, request
from app.models import db, Order, User, ParkingSpot
from app.services.fee_service import FeeCalculationService
from app.services.websocket_service import WebSocketEventService
from datetime import datetime, timedelta
import math

orders_bp = Blueprint('orders', __name__)

# ================= 1. 入场 =================
@orders_bp.route('/enter', methods=['POST'])
def enter_garage():
    """车辆入场"""
    order = Order.query.filter_by(
        order_no=request.get_json().get('order_no'), 
        status=0
    ).first()
    if not order: 
        return jsonify({'code': 404}), 404
        
    try:
        order.status = 1
        order.actual_in_time = datetime.now()
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 1
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({'code': 200, 'msg': '入场成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 2. 出场 (使用新的费用计算服务) =================
@orders_bp.route('/exit', methods=['POST'])
def exit_garage():
    """车辆出场"""
    order = Order.query.filter_by(
        order_no=request.get_json().get('order_no'), 
        status=1
    ).first()
    if not order: 
        return jsonify({'code': 404}), 404
        
    try:
        now = datetime.now()
        duration_min = (now - order.actual_in_time).total_seconds() / 60
        
        # 使用新的费用计算服务
        try:
            fee_info = FeeCalculationService.calculate_parking_fee(
                user_id=order.user_id,
                spot_id=order.spot_id,
                duration_minutes=int(math.ceil(duration_min)),
                parking_time=order.actual_in_time
            )
            fee = fee_info['total_fee']
        except Exception as fee_error:
            print(f"费用计算错误，使用默认费率: {fee_error}")
            # 如果费用计算失败，使用默认费率
            fee = round(max(0, math.ceil(duration_min) * 1.0), 2)

        order.actual_out_time = now
        order.total_fee = fee
        order.status = 3
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({
            'code': 200, 
            'data': {
                'fee': fee, 
                'duration': f"{int(duration_min)}分钟"
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 3. 支付 =================
@orders_bp.route('/pay', methods=['POST'])
def pay_order():
    """订单支付"""
    data = request.get_json()
    order = Order.query.filter_by(
        order_no=data.get('order_no'), 
        status=3
    ).first()
    if not order: 
        return jsonify({'code': 400}), 400
        
    try:
        if data.get('payment_method') == 'balance':
            user = db.session.get(User, order.user_id)
            if user.balance < order.total_fee: 
                return jsonify({'code': 402, 'msg': '余额不足'}), 402
            user.balance -= order.total_fee
        
        order.status = 2
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 0
        spot.version += 1
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({
            'code': 200, 
            'new_balance': user.balance if data.get('payment_method')=='balance' else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 4. 取消订单 =================
@orders_bp.route('/cancel', methods=['POST'])
def cancel_order():
    """取消订单"""
    order = Order.query.filter_by(
        order_no=request.get_json().get('order_no'), 
        status=0
    ).first()
    if not order: 
        return jsonify({'code': 400}), 400
        
    try:
        order.status = 4
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 0
        spot.version += 1
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({'code': 200})
    except: 
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 5. 我的订单 =================
@orders_bp.route('/orders', methods=['GET'])
def get_my_orders():
    """获取用户订单列表"""
    orders = Order.query.filter_by(
        user_id=request.args.get('user_id')
    ).order_by(Order.order_id.desc()).all()
    
    data = []
    for o in orders:
        data.append({
            'order_no': o.order_no, 
            'plate': o.plate_number, 
            'status': o.status, 
            'in_time': o.actual_in_time.strftime('%H:%M') if o.actual_in_time else '-', 
            'fee': str(o.total_fee)
        })
    return jsonify({'code': 200, 'data': data})

# ================= 6. 检查超时订单 =================
@orders_bp.route('/check_overdue', methods=['GET', 'POST'])
def check_overdue():
    """检查超时订单 - 预约超过30分钟未入场的订单自动取消"""
    try:
        # 查找超过30分钟未入场的预约订单
        overdue_time = datetime.now() - timedelta(minutes=30)
        overdue_orders = Order.query.filter(
            Order.status == 0,  # 已预约状态
            Order.reserve_start_time < overdue_time
        ).all()
        
        cancelled_count = 0
        for order in overdue_orders:
            # 取消订单
            order.status = 4  # 已取消
            # 释放车位
            spot = db.session.get(ParkingSpot, order.spot_id)
            if spot:
                spot.status = 0  # 空闲
                spot.version += 1
            cancelled_count += 1
        
        if cancelled_count > 0:
            db.session.commit()
            # 触发实时更新
            WebSocketEventService.emit_spot_update()
            WebSocketEventService.emit_order_update()
            WebSocketEventService.emit_stats_update()
        
        return jsonify({
            'code': 200, 
            'data': {
                'cancelled_count': cancelled_count,
                'message': f'已自动取消{cancelled_count}个超时订单'
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500