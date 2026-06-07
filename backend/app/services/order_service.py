"""
订单服务模块，提供停车订单的创建、支付、取消、查询、违约处理及退款等业务逻辑。
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from flask import current_app
from app.extensions import db, socketio
from app.models.order import ParkingOrder
from app.models.parking import ParkingSpot, ParkingZone
from app.models.user import SysUser
from app.models.car import Car
from app.utils.service_utils import handle_service_exception


class OrderService:
    """订单服务类"""

    @staticmethod
    @handle_service_exception(message_prefix="预约失败")
    def create_order(user, spot_id, plate_number, reserve_time_str=None):
        """
        处理创建预约订单业务逻辑。包含信用分校验、活跃订单上限检查、车辆唯一性及绑定验证、车位冲突检查，并使用悲观锁锁定车位。

        Args:
            user (SysUser): 当前用户对象
            spot_id (int): 待预约的车位 ID
            plate_number (str): 预约的车辆车牌号
            reserve_time_str (str, optional): 预约到达时间

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not spot_id or not plate_number:
            return {"success": False, "message": "车位ID和车牌号不能为空"}, 400

        from app.models.config import SysConfig

        # 解析与校验预约时间
        if reserve_time_str:
            try:
                if reserve_time_str.endswith("Z"):
                    reserve_time_str = reserve_time_str[:-1] + "+00:00"
                reserve_time = datetime.fromisoformat(reserve_time_str)
                if reserve_time.tzinfo is not None:
                    reserve_time = reserve_time.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                return {"success": False, "message": "预约时间格式错误"}, 400
        else:
            reserve_time = datetime.utcnow()

        # 校验预约到达时间是否合法（不能早于当前时间，不能晚于当前时间 + MAX_RESERVATION_HOURS）
        now = datetime.utcnow()
        max_hours = float(
            SysConfig.get_value(
                "MAX_RESERVATION_HOURS", current_app.config.get("MAX_RESERVATION_HOURS", 3)
            )
        )
        if reserve_time < now - timedelta(minutes=5):
            return {"success": False, "message": "预约到达时间不能早于当前时间"}, 400
        if reserve_time > now + timedelta(hours=max_hours) + timedelta(minutes=5):
            return {"success": False, "message": f"最长只能提前 {int(max_hours)} 小时预约车位"}, 400

        min_score = int(
            SysConfig.get_value(
                "MIN_CREDIT_SCORE", current_app.config.get("MIN_CREDIT_SCORE", 70)
            )
        )
        if user.credit_score < min_score:
            return {
                "success": False,
                "message": f"您的信用分({user.credit_score})低于及格线({min_score})，禁止预约",
            }, 403

        active_orders_count = ParkingOrder.query.filter(
            ParkingOrder.user_id == user.user_id, ParkingOrder.status.in_([0, 1, 2, 6])
        ).count()
        if active_orders_count >= 3:
            return {
                "success": False,
                "message": "您已有 3 个进行中的订单，已达到系统同时预约上限",
            }, 403

        active_car_order = ParkingOrder.query.filter(
            ParkingOrder.plate_number == plate_number,
            ParkingOrder.status.in_([0, 1, 2, 6]),
        ).first()
        if active_car_order:
            status_desc = {0: "预约中", 1: "停车中", 2: "待支付", 6: "待处理违约"}
            return {
                "success": False,
                "message": f'该车辆({plate_number})当前处于{status_desc.get(active_car_order.status, "活跃")}状态，不能重复预约',
            }, 403

        car = Car.query.filter_by(
            plate_number=plate_number, user_id=user.user_id
        ).first()
        if not car:
            return {"success": False, "message": "该车辆未绑定到您的账户"}, 403

        is_spot_reserved = ParkingOrder.query.filter_by(
            spot_id=spot_id, status=0
        ).first()
        if is_spot_reserved:
            return {"success": False, "message": "手慢了，该车位已被他人锁定"}, 409

        spot = (
            db.session.query(ParkingSpot)
            .with_for_update()
            .filter_by(spot_id=spot_id)
            .first()
        )
        if not spot:
            return {"success": False, "message": "车位不存在"}, 404
        if spot.status != 0:
            status_msg = {1: "车位已被车辆占用", 2: "车位正在维护中"}
            return {
                "success": False,
                "message": status_msg.get(spot.status, "车位不可用"),
            }, 409

        new_order = ParkingOrder(
            order_no=ParkingOrder.generate_order_no(),
            user_id=user.user_id,
            spot_id=spot_id,
            plate_number=plate_number,
            status=0,
            reserve_time=reserve_time,
        )
        db.session.add(new_order)
        db.session.commit()

        from app.services.parking_service import ParkingService

        ParkingService._broadcast_spot_update(
            spot.spot_id, spot.zone_id, 3, plate_number
        )
        OrderService._broadcast_order_update(new_order)

        return {
            "success": True,
            "message": "预约成功",
            "data": new_order.to_dict(),
        }, 201

    @staticmethod
    @handle_service_exception(message_prefix="支付失败")
    def pay_order(user, order_id, pay_way=0):
        """
        处理支付订单业务逻辑。

        Args:
            user (SysUser): 当前用户对象
            order_id (int): 待支付的订单 ID
            pay_way (int, optional): 支付方式，0 为余额支付. Defaults to 0.

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not order_id:
            return {"success": False, "message": "订单ID不能为空"}, 400

        order = ParkingOrder.query.filter_by(
            order_id=order_id, user_id=user.user_id
        ).first()
        if not order:
            return {"success": False, "message": "订单不存在"}, 404
        if order.status not in [2, 6]:
            return {"success": False, "message": "订单状态不正确"}, 400

        if pay_way == 0:
            if user.balance < order.total_fee:
                return {"success": False, "message": "余额不足"}, 400
            user.balance -= order.total_fee
        else:
            return {"success": False, "message": "暂不支持该支付方式"}, 400

        order.status = 3
        order.pay_time = datetime.utcnow()
        order.pay_way = pay_way
        db.session.commit()
        
        OrderService._broadcast_order_update(order)

        return {"success": True, "message": "支付成功", "data": order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="取消失败")
    def cancel_order(user, order_id):
        """
        处理取消预约业务逻辑，支持管理员强制取消操作。

        Args:
            user (SysUser): 操作用户对象，若是管理员可跨用户取消
            order_id (int): 待取消的订单 ID

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not order_id:
            return {"success": False, "message": "订单ID不能为空"}, 400

        if user.role == 3:
            order = ParkingOrder.query.get(order_id)
        else:
            order = ParkingOrder.query.filter_by(
                order_id=order_id, user_id=user.user_id
            ).first()

        if not order:
            return {"success": False, "message": "订单不存在"}, 404
        if order.status != 0:
            return {"success": False, "message": "该订单当前状态无法取消"}, 400

        order.status = 4
        spot = ParkingSpot.query.get(order.spot_id)
        db.session.commit()

        if spot:
            from app.services.parking_service import ParkingService

            ParkingService._broadcast_spot_update(spot.spot_id, spot.zone_id, 0, None)
            
        OrderService._broadcast_order_update(order)

        return {"success": True, "message": "取消成功", "data": order.to_dict()}, 200

    @staticmethod
    def search_orders(
        user,
        status=None,
        page=1,
        per_page=20,
        start_date=None,
        end_date=None,
        query_keyword=None,
    ):
        """
        统一订单查询逻辑，支持状态、日期范围、关键词搜索等多维过滤，以及分页功能。

        Args:
            user (SysUser): 当前用户对象（非管理员仅能查询自己的订单）
            status (int, optional): 订单状态过滤. Defaults to None.
            page (int, optional): 当前页码. Defaults to 1.
            per_page (int, optional): 每页记录数. Defaults to 20.
            start_date (datetime, optional): 开始日期过滤. Defaults to None.
            end_date (datetime, optional): 结束日期过滤. Defaults to None.
            query_keyword (str, optional): 模糊查询关键词（订单号、车牌、用户名、学号）. Defaults to None.

        Returns:
            tuple: 包含分页订单数据的响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        query = (
            db.session.query(
                ParkingOrder,
                SysUser.username,
                SysUser.user_no,
                SysUser.role,
                ParkingSpot.spot_no,
                ParkingZone.zone_name,
                ParkingZone.zone_id,
                ParkingZone.fee_rate,
                ParkingZone.free_time,
            )
            .join(SysUser, ParkingOrder.user_id == SysUser.user_id)
            .join(ParkingSpot, ParkingOrder.spot_id == ParkingSpot.spot_id)
            .join(ParkingZone, ParkingSpot.zone_id == ParkingZone.zone_id)
        )

        if user.role != 3:
            query = query.filter(ParkingOrder.user_id == user.user_id)

        if status is not None:
            query = query.filter(ParkingOrder.status == status)

        if start_date:
            query = query.filter(ParkingOrder.created_at >= start_date)
        if end_date:
            query = query.filter(ParkingOrder.created_at <= end_date)

        if query_keyword:
            k = f"%{query_keyword}%"
            query = query.filter(
                db.or_(
                    ParkingOrder.order_no.like(k),
                    ParkingOrder.plate_number.like(k),
                    SysUser.username.like(k),
                    SysUser.user_no.like(k),
                )
            )

        from sqlalchemy import case

        sort_weight = case({0: 0, 1: 0, 2: 1, 6: 1}, value=ParkingOrder.status, else_=2)

        pagination = query.order_by(
            sort_weight, ParkingOrder.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        orders_data = []
        for (
            order,
            username,
            user_no,
            role,
            spot_no,
            zone_name,
            zone_id,
            fee_rate,
            free_time,
        ) in pagination.items:
            o_dict = order.to_dict()
            o_dict.update(
                {
                    "username": username,
                    "user_no": user_no,
                    "user_role": role,
                    "spot_no": spot_no,
                    "zone_name": zone_name,
                    "zone_id": zone_id,
                    "fee_rate": float(fee_rate),
                    "free_time": free_time,
                }
            )
            orders_data.append(o_dict)

        return {
            "success": True,
            "data": {
                "orders": orders_data,
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
            },
        }, 200

    @staticmethod
    @handle_service_exception(message_prefix="违约处理失败")
    def process_order_violation(order_id, violation_type="payment"):
        """
        统一违约处理业务逻辑，扣除相应的违约金及信用分。

        Args:
            order_id (int): 订单 ID
            violation_type (str, optional): 违约类型，'payment' (支付超时) 或 'reservation' (预约未入场超时). Defaults to 'payment'.

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        order = ParkingOrder.query.get(order_id)
        if not order:
            return {"success": False, "message": "订单不存在"}, 404

        user = SysUser.query.get(order.user_id)
        if not user:
            return {"success": False, "message": "相关用户不存在"}, 404

        order.status = 6

        if violation_type == "reservation":
            order.out_time = datetime.utcnow()
            order.total_fee = Decimal(
                str(current_app.config.get("VIOLATION_FEE", 5.00))
            )
            penalty = current_app.config.get("CREDIT_PENALTY_DELAY", 10)

            spot = ParkingSpot.query.get(order.spot_id)
            if spot:
                from app.services.parking_service import ParkingService

                ParkingService._broadcast_spot_update(
                    spot.spot_id, spot.zone_id, 0, None
                )
        else:
            penalty = current_app.config.get("CREDIT_PENALTY_TIMEOUT", 5)

        user.credit_score = max(0, user.credit_score - penalty)

        db.session.commit()
        
        OrderService._broadcast_order_update(order)

        msg = f"订单 {order.order_no} ({violation_type}) 违约处理成功，扣除信用分 {penalty}"
        return {"success": True, "message": msg, "data": order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="退款失败")
    def refund_order(user, order_id):
        """
        处理退款业务逻辑，支持管理员操作及支付宝原路退款功能。

        Args:
            user (SysUser): 操作用户对象
            order_id (int): 待退款的订单 ID

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not order_id:
            return {"success": False, "message": "订单ID不能为空"}, 400

        if user.role == 3:
            order = ParkingOrder.query.get(order_id)
        else:
            order = ParkingOrder.query.filter_by(
                order_id=order_id, user_id=user.user_id
            ).first()

        if not order:
            return {"success": False, "message": "订单不存在"}, 404
        if order.status not in [3, 7]:
            return {"success": False, "message": "该订单当前状态无法执行退款"}, 400

        if order.pay_way == 0:
            owner = SysUser.query.get(order.user_id)
            if owner:
                owner.balance += order.total_fee
        elif order.pay_way == 2:
            from app.services.alipay_service import AlipayService

            result, code = AlipayService.refund_payment(order.order_no, order.total_fee)
            if not result.get("success"):
                return result, code

        order.status = 5
        db.session.commit()
        return {
            "success": True,
            "message": "已按原支付方式退款成功",
            "data": order.to_dict(),
        }, 200

    @staticmethod
    @handle_service_exception(message_prefix="申请退款失败")
    def apply_refund(user, order_id):
        """
        处理用户申请退款业务逻辑。

        Args:
            user (SysUser): 操作用户对象
            order_id (int): 待申请退款的订单 ID

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not order_id:
            return {"success": False, "message": "订单ID不能为空"}, 400

        order = ParkingOrder.query.filter_by(
            order_id=order_id, user_id=user.user_id
        ).first()
        if not order:
            return {"success": False, "message": "订单不存在"}, 404

        if order.status != 3:
            return {"success": False, "message": "该订单当前状态无法申请退款"}, 400

        from datetime import timedelta

        # 退款时限规则：离场后24小时内可申请
        if order.out_time and datetime.utcnow() > order.out_time + timedelta(hours=24):
            return {"success": False, "message": "离场已超过24小时，无法申请退款"}, 400

        order.status = 7  # 7-退款申请中
        db.session.commit()
        
        OrderService._broadcast_order_update(order)

        return {
            "success": True,
            "message": "退款申请已提交，等待审核",
            "data": order.to_dict(),
        }, 200

    @staticmethod
    def _broadcast_order_update(order):
        """广播订单状态更新事件"""
        from app.extensions import socketio
        try:
            socketio.emit(
                "order_status_update",
                {
                    "order_id": order.order_id,
                    "status": order.status,
                    "user_id": order.user_id,
                    "plate_number": order.plate_number
                },
            )
        except Exception as e:
            print(f"Error broadcasting order update: {e}")

    @staticmethod
    @handle_service_exception(message_prefix="拒绝退款失败")
    def reject_refund(user, order_id):
        """
        处理管理员拒绝退款业务逻辑。

        Args:
            user (SysUser): 操作用户对象 (需要是管理员)
            order_id (int): 订单 ID

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not order_id:
            return {"success": False, "message": "订单ID不能为空"}, 400
            
        if user.role != 3:
            return {"success": False, "message": "权限不足，仅管理员可拒绝退款"}, 403

        order = ParkingOrder.query.get(order_id)
        if not order:
            return {"success": False, "message": "订单不存在"}, 404

        if order.status != 7:
            return {"success": False, "message": "该订单当前状态不在退款申请中"}, 400

        order.status = 3  # 恢复为已完成/已结算状态
        db.session.commit()
        return {
            "success": True,
            "message": "已拒绝退款，订单状态恢复正常",
            "data": order.to_dict(),
        }, 200
