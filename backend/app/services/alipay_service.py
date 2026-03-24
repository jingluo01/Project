"""
支付宝支付服务模块，提供支付宝扫码支付、支付状态查询及退款等核心功能。
"""

from alipay import AliPay
from flask import current_app
from datetime import datetime
from app.models.order import ParkingOrder
from app.extensions import db
from app.utils.service_utils import handle_service_exception

class AlipayService:
    """支付宝支付服务类"""
    
    _alipay_instance = None
    
    @staticmethod
    def _format_key(key, key_type):
        """
        格式化 RSA 密钥。
        如果密钥是一行字符串，将其转换为 PEM 格式（带头尾和换行）。

        Args:
            key (str): 待格式化的密钥字符
            key_type (str): 密钥类型，可选 'PRIVATE' 或 'PUBLIC'

        Returns:
            str: 格式化后的 PEM 字符串
        """
        if not key or key.startswith('-----'):
            return key
            
        key = key.replace(' ', '')
        pem_key = '\n'.join([key[i:i+64] for i in range(0, len(key), 64)])
        
        if key_type == 'PRIVATE':
            return f"-----BEGIN RSA PRIVATE KEY-----\n{pem_key}\n-----END RSA PRIVATE KEY-----"
        else:
            return f"-----BEGIN PUBLIC KEY-----\n{pem_key}\n-----END PUBLIC KEY-----"

    @classmethod
    def get_alipay(cls):
        """
        获取正式的支付宝实例（单例模式）。

        Returns:
            AliPay: 官方 AliPay 客户端实例
        """
        if not cls._alipay_instance:
            try:
                appid = current_app.config.get('ALIPAY_APPID')
                p_key = current_app.config.get('ALIPAY_PRIVATE_KEY')
                pub_key = current_app.config.get('ALIPAY_PUBLIC_KEY')
                
                if not appid or not p_key or not pub_key:
                    raise Exception("Missing Alipay Configuration in Environment Variables")

                p_key_fmt = cls._format_key(p_key, 'PRIVATE')
                pub_key_fmt = cls._format_key(pub_key, 'PUBLIC')
                
                cls._alipay_instance = AliPay(
                    appid=appid,
                    app_notify_url=None,
                    app_private_key_string=p_key_fmt,
                    alipay_public_key_string=pub_key_fmt,
                    sign_type="RSA2",
                    debug=True # 沙箱环境默认设为True，生产环境请改为False
                )
            except Exception as e:
                current_app.logger.error(f"支付宝实例初始化失败: {str(e)}")
                raise e
        return cls._alipay_instance
    
    @classmethod
    @handle_service_exception(message_prefix="创建支付二维码失败")
    def create_qrcode_payment(cls, order_id):
        """
        创建真实扫码支付订单。
        
        Args:
            order_id (int): 订单 ID
            
        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组。
        """
        if not order_id:
            return {'success': False, 'message': '订单ID不能为空'}, 400
        
        order = ParkingOrder.query.get(order_id)
        if not order:
            return {'success': False, 'message': '订单不存在'}, 404
        
        if order.status not in [2, 6]:
            return {'success': False, 'message': '当前订单状态不允许发起支付'}, 400
        
        alipay = cls.get_alipay()
        
        # 为了兼容沙箱金额校验，强制将0或无金额替换为0.01进行支付测试
        amount = float(order.total_fee)
        if amount <= 0:
            amount = 0.01
        
        result = alipay.api_alipay_trade_precreate(
            subject=f"停车费支付-{order.plate_number}",
            out_trade_no=order.order_no,
            total_amount=str(amount),
            timeout_express="5m"
        )
        
        if result.get('code') == '10000':
            return {
                'success': True,
                'data': {
                    'qr_code': result.get('qr_code'),
                    'out_trade_no': order.order_no,
                    'expire_time': 300
                },
                'message': '支付二维码生成成功'
            }, 200
        else:
            return {
                'success': False,
                'message': f"生成二维码失败: {result.get('msg', '发生未知错误')}"
            }, 500
    
    @classmethod
    @handle_service_exception(message_prefix="查询支付状态失败")
    def query_payment_status(cls, out_trade_no):
        """
        查询订单真实支付状态，并执行相应的数据库订单状态更新。
        
        Args:
            out_trade_no (str): 商户订单号
            
        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not out_trade_no:
            return {'success': False, 'message': '订单号不能为空'}, 400
        
        alipay = cls.get_alipay()
        result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
        
        if result.get('code') == '10000':
            trade_status = result.get('trade_status')
            
            if trade_status == 'TRADE_SUCCESS':
                order = ParkingOrder.query.filter_by(order_no=out_trade_no).first()
                if order and order.status in [2, 6]:
                    order.status = 3
                    order.pay_time = datetime.utcnow()
                    order.pay_way = 2
                    order.trade_no = result.get('trade_no')
                    db.session.commit()
                    
                    current_app.logger.info(f"订单 {out_trade_no} 支付宝支付核销完成")
            
            return {
                'success': True,
                'data': {
                    'trade_status': trade_status,
                    'trade_no': result.get('trade_no', ''),
                    'total_amount': result.get('total_amount', '0')
                },
                'message': '查询成功'
            }, 200
        else:
            return {
                'success': True,
                'data': {
                    'trade_status': 'NOT_EXIST',
                    'trade_no': '',
                    'total_amount': '0'
                },
                'message': result.get('sub_msg', '该交易不存在或还未扫码')
            }, 200

    @classmethod
    @handle_service_exception(message_prefix="退款失败")
    def refund_payment(cls, out_trade_no, refund_amount, reason="用户申请退款"):
        """
        执行支付宝真实原路退款功能。
        
        Args:
            out_trade_no (str): 商户订单号
            refund_amount (str | float): 需退款金额
            reason (str, optional): 退款原因. Defaults to "用户申请退款".
            
        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        alipay = cls.get_alipay()
        
        order = ParkingOrder.query.filter_by(order_no=out_trade_no).first()
        trade_no = order.trade_no if order else None
        
        refund_params = {
            "refund_amount": str(refund_amount),
            "refund_reason": reason
        }
        if trade_no:
            refund_params["trade_no"] = trade_no
        else:
            refund_params["out_trade_no"] = out_trade_no
            
        result = alipay.api_alipay_trade_refund(**refund_params)
        
        if result.get('code') == '10000':
            return {
                'success': True,
                'message': '支付宝退款成功',
                'data': {
                    'refund_fee': result.get('refund_fee'),
                    'gmt_refund_pay': result.get('gmt_refund_pay')
                }
            }, 200
        elif result.get('code') in ['20000', '40004'] and current_app.config.get('DEBUG'):
            current_app.logger.warning(f"由于在沙箱环境出现异常({result.get('sub_code')})，退款自动绕过进入模拟成功状态: {out_trade_no}")
            return {
                'success': True,
                'message': '由于处于沙箱环境，系统已模拟退款成功',
                'data': {
                    'refund_fee': str(refund_amount),
                    'gmt_refund_pay': datetime.utcnow().isoformat()
                }
            }, 200
        else:
            return {
                'success': False,
                'message': f"支付宝退款失败: {result.get('sub_msg', '未知错误')}"
            }, 400
