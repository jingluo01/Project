"""
管理员功能相关路由
"""
from flask import Blueprint, jsonify, request
from app.models import db, Order, User, FeeRule
from app.services.fee_service import FeeRuleManagementService
from app.services.websocket_service import WebSocketEventService

admin_bp = Blueprint('admin', __name__)

# ================= 1. 管理端全局订单 =================
@admin_bp.route('/admin/orders', methods=['GET'])
def get_all_orders():
    """获取所有订单（管理员）"""
    orders = Order.query.order_by(Order.order_id.desc()).all()
    data = []
    for o in orders:
        u = db.session.get(User, o.user_id)
        data.append({
            'order_no': o.order_no, 
            'username': u.real_name if u else "未知", 
            'plate': o.plate_number,
            'status': o.status, 
            'reserve_time': str(o.reserve_start_time) if o.reserve_start_time else '-',
            'in_time': str(o.actual_in_time) if o.actual_in_time else '-', 
            'out_time': str(o.actual_out_time) if o.actual_out_time else '-',
            'fee': str(o.total_fee)
        })
    return jsonify({'code': 200, 'data': data})

# ================= 2. 管理端退款功能 =================
@admin_bp.route('/admin/refund', methods=['POST'])
def admin_refund():
    """管理员退款功能"""
    try:
        data = request.get_json()
        order_no = data.get('order_no')
        
        order = Order.query.filter_by(order_no=order_no, status=2).first()
        if not order:
            return jsonify({'code': 400, 'msg': '订单不存在或状态不正确'}), 400
        
        # 退款到用户余额
        user = db.session.get(User, order.user_id)
        if user:
            user.balance += order.total_fee
        
        # 更新订单状态为已退款（可以新增一个状态码5）
        order.status = 4  # 暂时使用已取消状态
        
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({
            'code': 200, 
            'msg': f'退款成功，已退款¥{order.total_fee}到用户余额'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 3. 管理端删除订单功能 =================
@admin_bp.route('/admin/delete-order', methods=['POST'])
def admin_delete_order():
    """管理员删除订单功能"""
    try:
        data = request.get_json()
        order_no = data.get('order_no')
        
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 400, 'msg': '订单不存在'}), 400
        
        # 检查订单状态，只允许删除已完成或已取消的订单
        if order.status not in [2, 4]:  # 2-已完成, 4-已取消
            return jsonify({'code': 400, 'msg': '只能删除已完成或已取消的订单'}), 400
        
        # 如果是已完成的订单，需要先退款
        if order.status == 2 and order.total_fee > 0:
            user = db.session.get(User, order.user_id)
            if user:
                user.balance += order.total_fee
        
        # 删除订单
        db.session.delete(order)
        db.session.commit()
        
        # 触发实时更新
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()
        
        return jsonify({
            'code': 200, 
            'msg': f'订单删除成功' + (f'，已退款¥{order.total_fee}到用户余额' if order.status == 2 and order.total_fee > 0 else '')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 4. 费用规则管理 =================
@admin_bp.route('/admin/fee-rules', methods=['GET'])
def get_fee_rules():
    """获取费用规则列表"""
    try:
        user_role = request.args.get('user_role')
        rules = FeeRuleManagementService.get_rules_by_role(user_role)
        data = [rule.to_dict() for rule in rules]
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

@admin_bp.route('/admin/fee-rules', methods=['POST'])
def create_fee_rule():
    """创建费用规则"""
    try:
        rule_data = request.get_json()
        rule = FeeRuleManagementService.create_rule(rule_data)
        return jsonify({'code': 200, 'data': rule.to_dict(), 'msg': '规则创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

@admin_bp.route('/admin/fee-rules/<int:rule_id>', methods=['PUT'])
def update_fee_rule(rule_id):
    """更新费用规则"""
    try:
        rule_data = request.get_json()
        rule = FeeRuleManagementService.update_rule(rule_id, rule_data)
        return jsonify({'code': 200, 'data': rule.to_dict(), 'msg': '规则更新成功'})
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

@admin_bp.route('/admin/fee-rules/<int:rule_id>', methods=['DELETE'])
def delete_fee_rule(rule_id):
    """删除费用规则"""
    try:
        success = FeeRuleManagementService.delete_rule(rule_id)
        if success:
            return jsonify({'code': 200, 'msg': '规则删除成功'})
        else:
            return jsonify({'code': 404, 'msg': '规则不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 4. 初始化默认费用规则 =================
@admin_bp.route('/admin/init-fee-rules', methods=['POST'])
def init_default_fee_rules():
    """初始化默认费用规则"""
    try:
        FeeRuleManagementService.initialize_default_rules()
        return jsonify({'code': 200, 'msg': '默认费用规则初始化成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 5. 系统设置：费率管理（兼容旧版本） =================
# 全局配置 (内存存储，重启后重置)
PARKING_RATE = 1.0

@admin_bp.route('/admin/config', methods=['GET', 'POST'])
def handle_config():
    """系统配置管理（兼容旧版本）"""
    global PARKING_RATE
    if request.method == 'POST':
        rate = request.get_json().get('rate')
        if rate is not None:
            PARKING_RATE = float(rate)
        return jsonify({'code': 200, 'msg': '费率已更新'})
    else:
        return jsonify({'code': 200, 'data': {'rate': PARKING_RATE}})