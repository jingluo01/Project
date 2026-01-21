from app.dao.user_dao import UserDao
from app.models.user_entity import Car
from app.extensions import db

class UserService:
    def get_user_profile(self, user_id):
        """获取个人信息及名下车辆"""
        user = UserDao.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 获取关联车辆
        cars = UserDao.get_cars_by_user_id(user_id)
        
        # 组合数据
        data = user.to_dict()
        data['cars'] = [car.to_dict() for car in cars]
        return data

    def bind_car(self, user_id, plate_number):
        """绑定车辆"""
        # 1. 校验车牌是否已被绑定
        exist_car = UserDao.get_car_by_plate(plate_number)
        if exist_car:
            if exist_car.user_id == user_id:
                raise ValueError("你已经绑定过该车辆了")
            else:
                raise ValueError("该车牌已被其他用户绑定")
        
        try:
            # 2. 创建车辆
            new_car = Car(user_id=user_id, plate_number=plate_number)
            UserDao.add_car(new_car)
            db.session.commit()
            return new_car.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
            
    def unbind_car(self, user_id, car_id):
        """解绑车辆"""
        # 逻辑留空，可视需求添加
        pass