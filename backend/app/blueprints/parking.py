from flask import Blueprint, request, jsonify
from app.utils.auth_utils import token_required
from app.services.parking_service import ParkingService

parking_bp = Blueprint('parking', __name__)

@parking_bp.route('/zones', methods=['GET'])
def get_zones():
    """获取所有停车区域"""
    result, status_code = ParkingService.get_zones()
    return jsonify(result), status_code

@parking_bp.route('/spots', methods=['GET'])
def get_spots():
    """获取车位实时状态"""
    zone_id = request.args.get('zone_id', type=int)
    result, status_code = ParkingService.get_spots(zone_id)
    return jsonify(result), status_code

@parking_bp.route('/enter', methods=['POST'])
def vehicle_enter():
    """车辆入场识别"""
    data = request.get_json()
    result, status_code = ParkingService.vehicle_enter(data.get('plate_number'))
    return jsonify(result), status_code

@parking_bp.route('/exit', methods=['POST'])
def vehicle_exit():
    """车辆出场识别与计费"""
    data = request.get_json()
    # auto_pay: True 表示物理设备自动识别，可以自动支付
    # auto_pay: False 表示用户手动操作，强制进入待支付状态
    auto_pay = data.get('auto_pay', True)  # 默认 True 保持向后兼容
    result, status_code = ParkingService.vehicle_exit(
        data.get('plate_number'), 
        auto_pay=auto_pay
    )
    return jsonify(result), status_code

def register_socketio_events(socketio_instance):
    """注册WebSocket事件"""
    @socketio_instance.on('connect')
    def handle_connect():
        print('Client connected')
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
