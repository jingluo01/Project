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
    def exists_username(username):
        # 优化查询：只查是否存在，不加载对象
        return db.session.query(
            db.session.query(SysUser.user_id).filter_by(username=username).exists()
        ).scalar()

    @staticmethod
    def add_user(user: SysUser):
        """添加用户（注意：此处不提交事务，交由 Service 层控制）"""
        db.session.add(user)
        # db.session.commit() # 事务由 Service 统一提交

    @staticmethod
    def add_car(car: Car):
        db.session.add(car)