from flask import Blueprint, jsonify, request
from app.models import db, ParkingSpot, Order, User
from sqlalchemy import func
from datetime import datetime, timedelta
import math
import random

parking_bp = Blueprint('parking', __name__)

# === 全局配置 (内存存储，重启后重置) ===
# 默认费率：1.0 元/分钟
PARKING_RATE = 1.0 

# ================= 1. 获取车位列表 =================
@parking_bp.route('/spots', methods=['GET'])
def get_spots():
    spots = ParkingSpot.query.all()
    data = []
    for spot in spots:
        spot_info = {
            'id': spot.spot_id, 'no': spot.spot_no, 'status': spot.status, 'area': spot.area_code,
            'current_plate': None, 'current_order': None
        }
        if spot.status != 0:
            active_order = Order.query.filter(Order.spot_id == spot.spot_id, Order.status.in_([0, 1, 3])).first()
            if active_order:
                spot_info['current_plate'] = active_order.plate_number
                spot_info['current_order'] = active_order.order_no
                if active_order.status == 3: spot_info['status'] = 3
        data.append(spot_info)
    return jsonify({'code': 200, 'data': data})

# ================= 2. 预约车位 =================
@parking_bp.route('/reserve', methods=['POST'])
def reserve_spot():
    data = request.get_json()
    user_id, spot_id, plate = data.get('user_id'), data.get('spot_id'), data.get('plate_number')

    if not all([user_id, spot_id, plate]): return jsonify({'code': 400}), 400
    
    # 信用分检查
    user = db.session.get(User, user_id)
    if not user or user.credit_score < 80: return jsonify({'code': 403, 'msg': '信用分不足'}), 403
    
    # 一人一单
    if Order.query.filter(Order.user_id==user_id, Order.status.in_([0,1,3])).first():
        return jsonify({'code': 400, 'msg': '已有进行中订单'}), 400

    spot = db.session.get(ParkingSpot, spot_id)
    if not spot or spot.status != 0: return jsonify({'code': 409, 'msg': '已被占用'}), 409

    if ParkingSpot.query.filter_by(spot_id=spot_id, version=spot.version, status=0).update({'status': 2, 'version': spot.version+1}) == 0:
        db.session.rollback()
        return jsonify({'code': 409, 'msg': '手慢了'}), 409
    # 2. 生成高并发安全的订单号 (时间戳精确到毫秒 + 3位随机数)
    # 格式示例: ORD20260112103055999
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

    try:
        new_order = Order(order_no=order_no, user_id=user_id, spot_id=spot_id, plate_number=plate, status=0, reserve_start_time=datetime.now())
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '预约成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 3. 入场 =================
@parking_bp.route('/enter', methods=['POST'])
def enter_garage():
    order = Order.query.filter_by(order_no=request.get_json().get('order_no'), status=0).first()
    if not order: return jsonify({'code': 404}), 404
    try:
        order.status = 1
        order.actual_in_time = datetime.now()
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 1
        db.session.commit()
        return jsonify({'code': 200, 'msg': '入场成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 4. 出场 (动态计费升级版) =================
@parking_bp.route('/exit', methods=['POST'])
def exit_garage():
    order = Order.query.filter_by(order_no=request.get_json().get('order_no'), status=1).first()
    if not order: return jsonify({'code': 404}), 404
    try:
        now = datetime.now()
        duration_min = (now - order.actual_in_time).total_seconds() / 60
        
        # === 核心修改：使用全局费率 PARKING_RATE ===
        fee = round(max(0, math.ceil(duration_min) * PARKING_RATE), 2) 
        # ========================================

        order.actual_out_time = now
        order.total_fee = fee
        order.status = 3
        db.session.commit()
        return jsonify({'code': 200, 'data': {'fee': fee, 'duration': f"{int(duration_min)}分钟"}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 5. 支付 =================
@parking_bp.route('/pay', methods=['POST'])
def pay_order():
    data = request.get_json()
    order = Order.query.filter_by(order_no=data.get('order_no'), status=3).first()
    if not order: return jsonify({'code': 400}), 400
    try:
        if data.get('payment_method') == 'balance':
            user = db.session.get(User, order.user_id)
            if user.balance < order.total_fee: return jsonify({'code': 402, 'msg': '余额不足'}), 402
            user.balance -= order.total_fee
        
        order.status = 2
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 0
        spot.version += 1
        db.session.commit()
        return jsonify({'code': 200, 'new_balance': user.balance if data.get('payment_method')=='balance' else None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500}), 500

# ================= 6. 取消 =================
@parking_bp.route('/cancel', methods=['POST'])
def cancel_order():
    order = Order.query.filter_by(order_no=request.get_json().get('order_no'), status=0).first()
    if not order: return jsonify({'code': 400}), 400
    try:
        order.status = 4
        spot = db.session.get(ParkingSpot, order.spot_id)
        spot.status = 0
        spot.version += 1
        db.session.commit()
        return jsonify({'code': 200})
    except: return jsonify({'code': 500}), 500

# ================= 7. 我的订单 =================
@parking_bp.route('/orders', methods=['GET'])
def get_my_orders():
    orders = Order.query.filter_by(user_id=request.args.get('user_id')).order_by(Order.order_id.desc()).all()
    data = [{'order_no': o.order_no, 'plate': o.plate_number, 'status': o.status, 'in_time': o.actual_in_time.strftime('%H:%M') if o.actual_in_time else '-', 'fee': str(o.total_fee)} for o in orders]
    return jsonify({'code': 200, 'data': data})

# ================= 8. 管理端统计 =================
@parking_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    # 简单模拟数据，仅供大屏展示
    dates = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(6, -1, -1)]
    return jsonify({'code': 200, 'data': {
        'pie_data': [{'value': ParkingSpot.query.filter_by(status=0).count(), 'name': '空闲'}, {'value': ParkingSpot.query.filter_by(status=1).count(), 'name': '占用'}],
        'line_data': {'categories': dates, 'values': [random.randint(100,500) for _ in range(7)]},
        'summary': {'total_income': 8888, 'utilization': 45.2}
    }})

# ================= 9. 管理端全局订单 =================
@parking_bp.route('/admin/orders', methods=['GET'])
def get_all_orders():
    orders = Order.query.order_by(Order.order_id.desc()).all()
    data = []
    for o in orders:
        u = db.session.get(User, o.user_id)
        data.append({
            'order_no': o.order_no, 'username': u.real_name if u else "未知", 'plate': o.plate_number,
            'status': o.status, 'in_time': str(o.actual_in_time) if o.actual_in_time else '-', 'fee': str(o.total_fee)
        })
    return jsonify({'code': 200, 'data': data})

# ================= 10. (新增) 系统设置：费率管理 =================
@parking_bp.route('/admin/config', methods=['GET', 'POST'])
def handle_config():
    global PARKING_RATE
    if request.method == 'POST':
        rate = request.get_json().get('rate')
        if rate is not None:
            PARKING_RATE = float(rate)
        return jsonify({'code': 200, 'msg': '费率已更新'})
    else:
        return jsonify({'code': 200, 'data': {'rate': PARKING_RATE}})