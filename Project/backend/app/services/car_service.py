from app.extensions import db
from app.models.car import Car
from app.utils.validators import validate_plate_number
from app.utils.service_utils import handle_service_exception

class CarService:
    @staticmethod
    @handle_service_exception(message_prefix="绑定失败")
    def bind_car(user, plate_number, nickname=None):
        """绑定车辆业务逻辑"""
        if not plate_number:
            return {'success': False, 'message': '车牌号不能为空'}, 400
        
        if not validate_plate_number(plate_number):
            return {'success': False, 'message': '车牌号格式不正确'}, 400
        
        car_count = Car.query.filter_by(user_id=user.user_id).count()
        if car_count >= 3:
            return {'success': False, 'message': '每个用户最多只能绑定3辆车辆'}, 403
        
        existing_car = Car.query.filter_by(plate_number=plate_number).first()
        if existing_car:
            return {'success': False, 'message': '该车牌已被绑定'}, 409
        
        new_car = Car(
            user_id=user.user_id,
            plate_number=plate_number,
            nickname=nickname
        )
        
        db.session.add(new_car)
        db.session.commit()
        return {'success': True, 'message': '车辆绑定成功', 'data': new_car.to_dict()}, 201

    @staticmethod
    @handle_service_exception(message_prefix="解绑失败")
    def remove_car(user, car_id):
        """解绑车辆业务逻辑"""
        car = Car.query.filter_by(car_id=car_id, user_id=user.user_id).first()
        if not car:
            return {'success': False, 'message': '车辆不存在'}, 404
        
        db.session.delete(car)
        db.session.commit()
        return {'success': True, 'message': '车辆解绑成功'}, 200

    @staticmethod
    def get_user_cars(user):
        """获取用户拥有的车辆列表"""
        return [car.to_dict() for car in user.cars.all()]
