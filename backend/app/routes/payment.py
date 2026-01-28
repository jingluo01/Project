"""
支付相关路由
"""
from flask import Blueprint, request, jsonify
from app.utils.auth_utils import token_required
from app.services.alipay_service import AlipayService
from app.models.user import SysUser

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

@payment_bp.route('/alipay/qrcode', methods=['POST'])
@token_required
def create_alipay_qrcode(current_user):
    """生成支付宝支付二维码"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'message': '订单ID不能为空'}), 400
        
        # 创建二维码
        result, status_code = AlipayService.create_qrcode_payment(order_id)
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@payment_bp.route('/alipay/query', methods=['GET'])
@token_required
def query_alipay_status(current_user):
    """查询支付宝支付状态"""
    try:
        out_trade_no = request.args.get('out_trade_no')
        
        if not out_trade_no:
            return jsonify({'success': False, 'message': '订单号不能为空'}), 400
        
        # 查询支付状态
        result, status_code = AlipayService.query_payment_status(out_trade_no)
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
