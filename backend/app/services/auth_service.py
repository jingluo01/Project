from werkzeug.security import generate_password_hash, check_password_hash
from app.dao.user_dao import UserDao
from app.models.user_entity import SysUser
from app.utils.jwt_util import JwtUtil
from app.extensions import db

class AuthService:
    def login(self, username, password):
        """登录逻辑"""
        user = UserDao.get_by_username(username)
        
        # 1. 用户不存在或密码错误
        if not user or not check_password_hash(user.password_hash, password):
            raise ValueError("用户名或密码错误")
        
        # 2. 账号被冻结
        if not user.is_active:
            raise ValueError("账号已被冻结")

        # 3. 生成 Token
        token = JwtUtil.generate_token(user.user_id)
        
        return {
            "token": token,
            "user": user.to_dict()
        }

    def register(self, username, password, role=1):
        """注册逻辑"""
        # 1. 检查用户名是否存在
        if UserDao.exists_username(username):
            raise ValueError("用户名已存在")

        try:
            # 2. 创建用户实体
            new_user = SysUser(
                username=username,
                password_hash=generate_password_hash(password), # 密码加密
                role=role
            )
            
            # 3. 调用 DAO
            UserDao.add_user(new_user)
            
            # 4. 提交事务 (原子操作)
            db.session.commit()
            
            return new_user.to_dict()
        except Exception as e:
            db.session.rollback() # 发生异常回滚
            raise e