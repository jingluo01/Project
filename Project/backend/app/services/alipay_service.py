"""
支付宝支付服务
"""
from alipay import AliPay
from flask import current_app
from datetime import datetime
from app.models.order import ParkingOrder
from app.extensions import db

class MockAlipay:
    """Mock Alipay service for development"""
    def api_alipay_trade_precreate(self, **kwargs):
        from datetime import datetime
        return {
            'code': '10000',
            'msg': 'Success',
            'qr_code': 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=MockPayment', # Generate a real QR code image for visual effect
            'out_trade_no': kwargs.get('out_trade_no')
        }
    
    def api_alipay_trade_query(self, **kwargs):
        from datetime import datetime
        return {
            'code': '10000',
            'trade_status': 'TRADE_SUCCESS',
            'trade_no': 'MOCK_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'total_amount': '0.01'
        }
        
    def api_alipay_trade_refund(self, **kwargs):
        from datetime import datetime
        return {
            'code': '10000',
            'refund_fee': kwargs.get('refund_amount'),
            'gmt_refund_pay': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

class AlipayService:
    """支付宝支付服务类"""
    
    _alipay_instance = None
    
    @staticmethod
    def _format_key(key, key_type):
        """
        格式化RSA密钥
        如果密钥是一行字符串，将其转换为PEM格式（带头尾和换行）
        """
        if not key or key.startswith('-----'):
            return key
            
        # 去除可能存在的空格
        key = key.replace(' ', '')
            
        # 每64个字符插入一个换行符
        pem_key = '\n'.join([key[i:i+64] for i in range(0, len(key), 64)])
        
        if key_type == 'PRIVATE':
            return f"-----BEGIN RSA PRIVATE KEY-----\n{pem_key}\n-----END RSA PRIVATE KEY-----"
        else:
            return f"-----BEGIN PUBLIC KEY-----\n{pem_key}\n-----END PUBLIC KEY-----"

    @classmethod
    def get_alipay(cls):
        """获取支付宝实例（高性能单例）"""
        if not cls._alipay_instance:
            try:
                # 预读配置
                appid = current_app.config.get('ALIPAY_APPID')
                p_key = current_app.config.get('ALIPAY_PRIVATE_KEY')
                pub_key = current_app.config.get('ALIPAY_PUBLIC_KEY')
                
                # Check directly for missing config to fallback early
                if not appid or not p_key or not pub_key:
                    raise Exception("Missing Alipay Configuration")

                p_key_fmt = cls._format_key(p_key, 'PRIVATE')
                pub_key_fmt = cls._format_key(pub_key, 'PUBLIC')
                
                cls._alipay_instance = AliPay(
                    appid=appid,
                    app_notify_url=None,
                    app_private_key_string=p_key_fmt,
                    alipay_public_key_string=pub_key_fmt,
                    sign_type="RSA2",
                    debug=True
                )
            except Exception as e:
                # In development, fallback to Mock if config is invalid
                if current_app.config.get('FLASK_ENV') == 'development' or current_app.debug:
                    current_app.logger.warning(f"支付宝初始化失败 ('{str(e)}'). 开发环境已切换为 Mock 模式。")
                    cls._alipay_instance = MockAlipay()
                else:
                    current_app.logger.error(f"支付宝实例初始化失败: {str(e)}")
                    raise e
        return cls._alipay_instance
    
    @classmethod
    def create_qrcode_payment(cls, order_id):
        """
        创建扫码支付订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            dict: {
                'success': bool,
                'data': {
                    'qr_code': str,  # 二维码链接
                    'out_trade_no': str,  # 商户订单号
                    'expire_time': int  # 过期时间（秒）
                },
                'message': str
            }
        """
        try:
            # 获取订单信息
            order = ParkingOrder.query.get(order_id)
            if not order:
                return {'success': False, 'message': '订单不存在'}, 404
            
            if order.status not in [2, 6]:  # 只有待支付和违约订单可以支付
                return {'success': False, 'message': '订单状态不正确'}, 400
            
            # 获取支付宝实例
            alipay = cls.get_alipay()
            
            # 测试用：如果金额为0，强制改为0.01以通过支付宝校验
            amount = float(order.total_fee)
            if amount <= 0:
                amount = 0.01
            
            # 创建预下单（扫码支付）
            result = alipay.api_alipay_trade_precreate(
                subject=f"停车费支付-{order.plate_number}",
                out_trade_no=order.order_no,
                total_amount=str(amount),
                timeout_express="5m"  # 二维码5分钟有效
            )
            
            if result.get('code') == '10000':
                # 成功生成二维码
                qr_code = result.get('qr_code')
                return {
                    'success': True,
                    'data': {
                        'qr_code': qr_code,
                        'out_trade_no': order.order_no,
                        'expire_time': 300  # 5分钟
                    },
                    'message': '二维码生成成功'
                }, 200
            else:
                return {
                    'success': False,
                    'message': f"生成二维码失败: {result.get('msg', '未知错误')}"
                }, 500
                
        except Exception as e:
            current_app.logger.error(f"创建支付宝二维码失败: {str(e)}")
            return {'success': False, 'message': f'创建支付失败: {str(e)}'}, 500
    
    @classmethod
    def query_payment_status(cls, out_trade_no):
        """
        查询支付状态
        
        Args:
            out_trade_no: 商户订单号
            
        Returns:
            dict: {
                'success': bool,
                'data': {
                    'trade_status': str,  # WAIT_BUYER_PAY, TRADE_SUCCESS, TRADE_CLOSED
                    'trade_no': str,  # 支付宝交易号
                    'total_amount': str  # 交易金额
                },
                'message': str
            }
        """
        try:
            # 获取支付宝实例
            alipay = cls.get_alipay()
            
            # 查询交易状态
            # 查询交易状态
            result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
            
            if result.get('code') == '10000':
                trade_status = result.get('trade_status')
                
                # 如果支付成功，更新订单状态
                if trade_status == 'TRADE_SUCCESS':
                    order = ParkingOrder.query.filter_by(order_no=out_trade_no).first()
                    if order and order.status in [2, 6]:
                        order.status = 3  # 已完成
                        order.pay_time = datetime.utcnow()
                        order.pay_way = 2  # 支付宝支付
                        order.trade_no = result.get('trade_no') # 保存支付宝交易号
                        db.session.commit()
                        
                        current_app.logger.info(f"订单 {out_trade_no} 支付宝支付成功")
                
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
                # 交易不存在或查询失败
                return {
                    'success': True,
                    'data': {
                        'trade_status': 'NOT_EXIST',
                        'trade_no': '',
                        'total_amount': '0'
                    },
                    'message': result.get('sub_msg', '交易不存在')
                }, 200
        except Exception as e:
            current_app.logger.error(f"查询支付宝支付状态失败: {str(e)}")
            return {'success': False, 'message': f'查询失败: {str(e)}'}, 500

    @classmethod
    def refund_payment(cls, out_trade_no, refund_amount, reason="用户申请退款"):
        """
        支付宝原路退款
        
        Args:
            out_trade_no: 商户订单号
            refund_amount: 退款金额
            reason: 退款原因
            
        Returns:
            dict: { 'success': bool, 'message': str, 'data': dict }
        """
        try:
            alipay = cls.get_alipay()
            
            # 尝试获取 trade_no 进行精准退款
            from app.models.order import ParkingOrder
            order = ParkingOrder.query.filter_by(order_no=out_trade_no).first()
            trade_no = order.trade_no if order else None
            
            # 优先使用 trade_no
            refund_params = {
                "refund_amount": str(refund_amount),
                "refund_reason": reason
            }
            if trade_no:
                refund_params["trade_no"] = trade_no
            else:
                refund_params["out_trade_no"] = out_trade_no
                
            result = alipay.api_alipay_trade_refund(**refund_params)
            
            # 打印调试信息
            current_app.logger.info(f"[退款调试] 订单号: {out_trade_no}")
            current_app.logger.info(f"[退款调试] trade_no: {trade_no}")
            current_app.logger.info(f"[退款调试] 退款参数: {refund_params}")
            current_app.logger.info(f"[退款调试] 支付宝返回: {result}")
            
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
                # 沙箱环境常见错误的降级处理
                # 20000: 系统异常
                # 40004: 买家状态非法（沙箱账号限制）
                current_app.logger.warning(f"支付宝沙箱退款异常({result.get('sub_code')})，模拟退款成功: {out_trade_no}")
                return {
                    'success': True,
                    'message': '退款成功（沙箱模拟）',
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
        except Exception as e:
            current_app.logger.error(f"支付宝退款异常: {str(e)}")
            return {'success': False, 'message': f"退款系统异常: {str(e)}"}, 500
