from app.models.user_entity import SysUser, Car
from app.extensions import db

class UserDao:
    @staticmethod
    def get_by_id(user_id):
        return SysUser.query.get(user_id)

    @staticmethod
    def get_by_username(username):
        return SysUser.query.filter_by(username=username).first()

    @staticmethod
    def get_by_user_no(user_no):
        """根据学号/工号查询用户"""
        return SysUser.query.filter_by(user_no=user_no).first()

    @staticmethod
    def exists_username(username):
        # 优化查询：只查是否存在，不加载对象
        return db.session.query(
            db.session.query(SysUser.user_id).filter_by(username=username).exists()
        ).scalar()

    @staticmethod
    def exists_user_no(user_no):
        """检查学号/工号是否存在"""
        if not user_no:
            return False
        return db.session.query(
            db.session.query(SysUser.user_id).filter_by(user_no=user_no).exists()
        ).scalar()

    @staticmethod
    def add_user(user: SysUser):
        """添加用户（注意：此处不提交事务，交由 Service 层控制）"""
        db.session.add(user)
        # db.session.commit() # 事务由 Service 统一提交

    @staticmethod
    def get_car_by_plate(plate_number):
        """根据车牌号查询车辆"""
        return Car.query.filter_by(plate_number=plate_number).first()

    @staticmethod
    def get_cars_by_user_id(user_id):
        """获取用户的所有车辆"""
        return Car.query.filter_by(user_id=user_id).all()

    @staticmethod
    def add_car(car: Car):
        """添加车辆"""
        db.session.add(car)
        
    @staticmethod
    def delete_car(car: Car):
        """删除车辆"""
        db.session.delete(car)