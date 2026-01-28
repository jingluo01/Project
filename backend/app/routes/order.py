from flask import Blueprint, request, jsonify
from app.utils.auth_utils import token_required
from app.services.order_service import OrderService

order_bp = Blueprint('order', __name__)

@order_bp.route('/create', methods=['POST'])
@token_required
def create_order(current_user):
    """创建订单"""
    data = request.get_json()
    result, status_code = OrderService.create_order(
        current_user,
        data.get('spot_id'),
        data.get('plate_number')
    )
    return jsonify(result), status_code

@order_bp.route('/pay', methods=['POST'])
@token_required
def pay_order(current_user):
    """支付订单"""
    data = request.get_json()
    result, status_code = OrderService.pay_order(
        current_user,
        data.get('order_id'),
        data.get('pay_way', 0)
    )
    return jsonify(result), status_code

@order_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_order(current_user):
    """取消预约"""
    data = request.get_json()
    result, status_code = OrderService.cancel_order(current_user, data.get('order_id'))
    return jsonify(result), status_code

@order_bp.route('/list', methods=['GET'])
@token_required
def get_orders(current_user):
    """获取订单列表 (通过通用化的 OrderService 接口)"""
    status = request.args.get('status', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query_keyword = request.args.get('query')
    
    # 统一调用 search_orders，Service 层会根据 current_user 自动做权限隔离
    result, status_code = OrderService.search_orders(
        current_user, 
        status, 
        page, 
        per_page,
        start_date=start_date,
        end_date=end_date,
        query_keyword=query_keyword
    )
    return jsonify(result), status_code

@order_bp.route('/refund', methods=['POST'])
@token_required
def refund_order(current_user):
    """退款"""
    data = request.get_json()
    result, status_code = OrderService.refund_order(current_user, data.get('order_id'))
    return jsonify(result), status_code
