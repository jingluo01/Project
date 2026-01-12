"""
车位管理相关路由
"""
from flask import Blueprint, jsonify, request
from app.models import db, ParkingSpot, Order
from app.services.websocket_service import WebSocketEventService

spots_bp = Blueprint('spots', __name__)

# ================= 1. 获取车位列表 =================
@spots_bp.route('/spots', methods=['GET'])
def get_spots():
    """获取所有车位状态"""
    spots = ParkingSpot.query.all()
    data = []
    for spot in spots:
        spot_info = {
            'id': spot.spot_id, 
            'no': spot.spot_no, 
            'status': spot.status, 
            'area': spot.area_code,
            'current_plate': None, 
            'current_order': None
        }
        if spot.status != 0:
            active_order = Order.query.filter(
                Order.spot_id == spot.spot_id, 
                Order.status.in_([0, 1, 3])
            ).first()
            if active_order:
                spot_info['current_plate'] = active_order.plate_number
                spot_info['current_order'] = active_order.order_no
                if active_order.status == 3: 
                    spot_info['status'] = 3
        data.append(spot_info)
    return jsonify({'code': 200, 'data': data})

# ================= 2. 预约车位 =================
@spots_bp.route('/reserve', methods=['POST'])
def reserve_spot():
    """预约车位"""
    from app.models import User
    from datetime import datetime
    import random
    
    data = request.get_json()
    user_id, spot_id, plate = data.get('user_id'), data.get('spot_id'), data.get('plate_number')

    if not all([user_id, spot_id, plate]): 
        return jsonify({'code': 400}), 400
    
    # 信用分检查
    user = db.session.get(User, user_id)
    if not user or user.credit_score < 80: 
        return jsonify({'code': 403, 'msg': '信用分不足'}), 403
    
    # 一人一单
    if Order.query.filter(Order.user_id==user_id, Order.status.in_([0,1,3])).first():
        return jsonify({'code': 400, 'msg': '已有进行中订单'}), 400

    spot = db.session.get(ParkingSpot, spot_id)
    if not spot or spot.status != 0: 
        return jsonify({'code': 409, 'msg': '已被占用'}), 409

    # 乐观锁更新车位状态
    if ParkingSpot.query.filter_by(
        spot_id=spot_id, 
        version=spot.version, 
        status=0
    ).update({
        'status': 2, 
        'version': spot.version+1
    }) == 0:
        db.session.rollback()
        return jsonify({'code': 409, 'msg': '手慢了'}), 409
    
    # 生成订单号
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

    try:
        new_order = Order(
            order_no=order_no, 
            user_id=user_id, 
            spot_id=spot_id, 
            plate_number=plate, 
            status=0, 
            reserve_start_time=datetime.now()
        )
        db.session.add(new_order)
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({'code': 200, 'msg': '预约成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500