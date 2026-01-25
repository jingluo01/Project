from flask import Blueprint, request, jsonify
from app.utils.auth_utils import token_required
from app.services.user_service import UserService
from app.services.car_service import CarService

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取个人信息 (含车辆信息)"""
    result, status_code = UserService.get_profile(current_user)
    return jsonify(result), status_code

@user_bp.route('/car/bind', methods=['POST'])
@token_required
def bind_car(current_user):
    """绑定车辆 (资产逻辑归口至 CarService)"""
    data = request.get_json()
    result, status_code = CarService.bind_car(
        current_user,
        data.get('plate_number'),
        data.get('nickname')
    )
    return jsonify(result), status_code

@user_bp.route('/car/remove/<int:car_id>', methods=['DELETE'])
@token_required
def remove_car(current_user, car_id):
    """解绑车辆 (资产逻辑归口至 CarService)"""
    result, status_code = CarService.remove_car(current_user, car_id)
    return jsonify(result), status_code

@user_bp.route('/recharge', methods=['POST'])
@token_required
def recharge(current_user):
    """钱包充值"""
    data = request.get_json()
    result, status_code = UserService.recharge(current_user, data.get('amount'))
    return jsonify(result), status_code
