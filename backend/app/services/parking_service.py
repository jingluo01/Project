"""
停车服务模块，提供停车区域和车位查询、车辆入场/出场管理及场地维护等功能。
"""

from datetime import datetime
from decimal import Decimal
from app.extensions import db, socketio
from app.models.parking import ParkingZone, ParkingSpot
from app.models.order import ParkingOrder
from app.models.user import SysUser
from app.utils.fee_calculator import calculate_parking_fee
from app.utils.service_utils import handle_service_exception
from flask import current_app
import os

cv2 = None
np = None
LicensePlateCatcher = None
YOLO = None

def _import_cv2():
    """延迟导入cv2"""
    global cv2, np
    if cv2 is None:
        import cv2 as cv
        import numpy as numpy
        cv2 = cv
        np = numpy
    return cv2, np

def _import_lpr():
    """延迟导入车牌识别库"""
    global LicensePlateCatcher, YOLO
    if LicensePlateCatcher is None:
        from hyperlpr3 import LicensePlateCatcher as LPC
        from ultralytics import YOLO as YOLONet
        LicensePlateCatcher = LPC
        YOLO = YOLONet
    return LicensePlateCatcher, YOLO

class ParkingService:
    """停车服务类"""

    def __init__(self):
        """初始化停车服务"""
        self.model = None
        self.lpr = None

    def _ensure_models_loaded(self):
        """确保模型已加载"""
        if self.lpr is None:
            LPC, _ = _import_lpr()
            self.lpr = LPC()

    def process_plate_region(self, plate_img):
        """处理车牌区域图像"""
        return plate_img

    def recognize_plate_from_image(self, image_data):
        """
        从图像数据中识别车牌

        Args:
            image_data: 图像数据（字节流或numpy数组）

        Returns:
            识别结果（车牌号）或None
        """
        try:
            cv, numpy = _import_cv2()
            self._ensure_models_loaded()

            if isinstance(image_data, bytes):
                nparr = numpy.frombuffer(image_data, numpy.uint8)
                img = cv.imdecode(nparr, cv.IMREAD_COLOR)
            else:
                img = image_data

            if img is None:
                return None

            result_lpr = self.lpr(img)
            if result_lpr:
                if isinstance(result_lpr[0], list):
                    plate_text = result_lpr[0][0] if len(result_lpr[0]) > 0 else None
                elif isinstance(result_lpr[0], dict):
                    plate_text = result_lpr[0].get('license', None)
                else:
                    plate_text = str(result_lpr[0])
                if plate_text and plate_text != "UNKNOWN":
                    return plate_text

            return None

        except Exception as e:
            print(f"车牌识别错误: {str(e)}")
            return None

    @staticmethod
    def _broadcast_spot_update(spot_id, zone_id, status, current_plate=None):
        """通过 WebSocket 向前端广播车位状态变更并清理相关缓存。"""
        socketio.emit(
            "spot_status_update",
            {
                "spot_id": spot_id,
                "zone_id": zone_id,
                "status": status,
                "current_plate": current_plate,
            },
        )
        ParkingService._clear_spots_cache(zone_id)

    @staticmethod
    def _clear_spots_cache(zone_id=None):
        """清理 Redis 中的车位及区域缓存列表。"""
        from app.extensions import redis_client

        if not redis_client:
            return
        try:
            if zone_id:
                redis_client.delete(f"parking:spots:{zone_id}")
            else:
                keys = redis_client.keys("parking:spots:*")
                if keys:
                    redis_client.delete(*keys)
            redis_client.delete("parking:zones:all")
        except:
            pass

    @staticmethod
    def get_zones():
        """获取所有停车区域信息，优先使用 Redis 缓存读取。"""
        from app.extensions import redis_client
        import json

        cache_key = "parking:zones:all"
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return {"success": True, "data": json.loads(cached_data)}, 200
            except:
                pass

        zones = ParkingZone.query.all()
        data = [zone.to_dict() for zone in zones]

        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(data))
            except:
                pass

        return {"success": True, "data": data}, 200

    @staticmethod
    def get_spots(zone_id=None):
        """获取车位实时状态，含高并发条件下的短时缓存保护。"""
        from app.extensions import redis_client
        import json

        cache_key = f'parking:spots:{zone_id if zone_id else "all"}'
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return {"success": True, "data": json.loads(cached_data)}, 200
            except:
                pass

        if zone_id:
            spots = ParkingSpot.query.filter_by(zone_id=zone_id).all()
        else:
            spots = ParkingSpot.query.all()

        spot_ids = [s.spot_id for s in spots]
        reserved_orders = ParkingOrder.query.filter(
            ParkingOrder.spot_id.in_(spot_ids), ParkingOrder.status == 0
        ).all()
        reserved_spot_map = {
            order.spot_id: order.plate_number for order in reserved_orders
        }

        spots_data = []
        for spot in spots:
            spot_dict = spot.to_dict()
            if spot.status == 0 and spot.spot_id in reserved_spot_map:
                spot_dict["status"] = 3
                spot_dict["current_plate"] = reserved_spot_map[spot.spot_id]
            spots_data.append(spot_dict)

        if redis_client:
            try:
                redis_client.setex(cache_key, 3, json.dumps(spots_data))
            except:
                pass

        return {"success": True, "data": spots_data}, 200

    @staticmethod
    @handle_service_exception(message_prefix="入场失败")
    def vehicle_enter(plate_number):
        """处理车辆入场业务逻辑。"""
        if not plate_number:
            return {"success": False, "message": "车牌号不能为空"}, 400

        order = ParkingOrder.query.filter_by(
            plate_number=plate_number, status=0
        ).first()
        if not order:
            return {"success": False, "message": "未找到有效预约订单"}, 404

        order.status = 1
        order.in_time = datetime.utcnow()

        spot = ParkingSpot.query.get(order.spot_id)
        spot.status = 1
        spot.current_plate = plate_number

        db.session.commit()
        ParkingService._broadcast_spot_update(
            spot.spot_id, spot.zone_id, spot.status, plate_number
        )

        return {"success": True, "message": "入场成功", "data": order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="出场失败")
    def vehicle_exit(plate_number, auto_pay=True):
        """处理车辆出场识别及计费逻辑。"""
        if not plate_number:
            return {"success": False, "message": "车牌号不能为空"}, 400

        order = ParkingOrder.query.filter_by(
            plate_number=plate_number, status=1
        ).first()
        if not order:
            return {"success": False, "message": "未找到进行中的订单"}, 404

        order.out_time = datetime.utcnow()
        spot = ParkingSpot.query.get(order.spot_id)
        zone = ParkingZone.query.get(spot.zone_id)
        user = SysUser.query.get(order.user_id)

        total_fee = calculate_parking_fee(
            order.in_time,
            order.out_time,
            zone.fee_rate,
            zone.free_time,
            user.role,
            current_app.config["ROLE_DISCOUNT"],
        )
        order.total_fee = total_fee

        if auto_pay:
            has_violation = ParkingOrder.query.filter_by(
                user_id=user.user_id, status=6
            ).first()
            if (
                user.credit_score == current_app.config["PERFECT_CREDIT_SCORE"]
                and not has_violation
            ):
                if user.balance >= total_fee:
                    user.balance -= total_fee
                    order.status = 3
                    order.pay_time = datetime.utcnow()
                    order.pay_way = 0
                else:
                    order.status = 2
            else:
                order.status = 2
        else:
            order.status = 2

        spot.status = 0
        spot.current_plate = None
        db.session.commit()
        ParkingService._broadcast_spot_update(
            spot.spot_id, spot.zone_id, spot.status, None
        )

        return {"success": True, "message": "出场成功", "data": order.to_dict()}, 200

    @staticmethod
    @handle_service_exception(message_prefix="场地维护失败")
    def update_parking_or_zone(data):
        """处理修改车位状态或区域配置信息逻辑。"""
        if "spot_id" in data:
            spot = ParkingSpot.query.get(data["spot_id"])
            if not spot:
                return {"success": False, "message": "车位不存在"}, 404

            if "status" in data:
                spot.status = data["status"]
                ParkingService._broadcast_spot_update(
                    spot.spot_id, spot.zone_id, spot.status, spot.current_plate
                )

            db.session.commit()
            return {"success": True, "message": "车位状态更新成功"}, 200

        if "zone_id" in data:
            zone = ParkingZone.query.get(data["zone_id"])
            if not zone:
                return {"success": False, "message": "区域不存在"}, 404

            if "fee_rate" in data:
                zone.fee_rate = Decimal(str(data["fee_rate"]))
            if "free_time" in data:
                zone.free_time = data["free_time"]

            db.session.commit()

            from app.extensions import redis_client

            if redis_client:
                try:
                    redis_client.delete("parking:zones:all")
                except:
                    pass

            return {"success": True, "message": "区域费率更新成功"}, 200

        return {"success": False, "message": "缺少必要参数"}, 400

# 创建服务实例（不初始化模型）
parking_service = ParkingService()