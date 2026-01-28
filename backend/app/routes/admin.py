from flask import Blueprint, request, jsonify
from app.utils.auth_utils import token_required, admin_required
from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.parking_service import ParkingService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_stats(current_user):
    """获取仪表盘统计数据"""
    result, status_code = AdminService.get_stats()
    return jsonify(result), status_code

@admin_bp.route('/config', methods=['GET'])
@token_required
def get_system_config(current_user):
    """获取系统业务配置 (数据库优先)"""
    result, status_code = AdminService.get_system_config()
    return jsonify(result), status_code

@admin_bp.route('/config/update', methods=['POST'])
@token_required
@admin_required
def update_system_config(current_user):
    """更新系统业务配置"""
    data = request.get_json()
    result, status_code = AdminService.update_system_config(data)
    return jsonify(result), status_code

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result, status_code = UserService.get_users_list(page, per_page)
    return jsonify(result), status_code

@admin_bp.route('/user/update', methods=['POST'])
@token_required
@admin_required
def update_user(current_user):
    """修改用户信息"""
    data = request.get_json()
    result, status_code = UserService.update_user(data.get('user_id'), data)
    return jsonify(result), status_code

@admin_bp.route('/parking/update', methods=['POST'])
@token_required
@admin_required
def update_parking(current_user):
    """管理车位状态及停车场费率 (场地逻辑归口至 ParkingService)"""
    data = request.get_json()
    result, status_code = ParkingService.update_parking_or_zone(data)
    return jsonify(result), status_code

@admin_bp.route('/order/force-exit', methods=['POST'])
@token_required
@admin_required
def force_exit_order(current_user):
    """管理员强制结束停车订单并计费"""
    data = request.get_json()
    plate_number = data.get('plate_number')
    result, status_code = ParkingService.vehicle_exit(plate_number, auto_pay=False)
    return jsonify(result), status_code

@admin_bp.route('/orders', methods=['GET'])
@token_required
@admin_required
def get_all_orders(current_user):
    """获取所有订单"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query_keyword = request.args.get('query')
    
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
