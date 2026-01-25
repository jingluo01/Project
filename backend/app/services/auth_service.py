from app.extensions import db
from app.models.user import SysUser
from app.utils.auth_utils import hash_password, verify_password, generate_token
from app.utils.validators import validate_user_no

class AuthService:
    @staticmethod
    def login(user_no, password):
        """用户登录业务逻辑"""
        if not user_no or not password:
            return {'success': False, 'message': '学号/工号和密码不能为空'}, 400
        
        user = SysUser.query.filter_by(user_no=user_no).first()
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        
        if not user.is_active:
            return {'success': False, 'message': '账号已被禁用'}, 403
        
        if not verify_password(user.password, password):
            return {'success': False, 'message': '密码错误'}, 401
        
        token = generate_token(user.user_id, user.role)
        return {
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        }, 200

    @staticmethod
    def register(user_no, username, password, role=1):
        """用户注册业务逻辑"""
        if not user_no or not username or not password:
            return {'success': False, 'message': '请填写完整信息'}, 400
        
        if not validate_user_no(user_no):
            return {'success': False, 'message': '学号/工号格式不正确'}, 400
        
        if len(password) < 6:
            return {'success': False, 'message': '密码长度至少6位'}, 400
        
        if SysUser.query.filter_by(user_no=user_no).first():
            return {'success': False, 'message': '该学号/工号已注册'}, 409
        
        new_user = SysUser(
            user_no=user_no,
            username=username,
            password=hash_password(password),
            role=role,
            credit_score=100,
            balance=0.00
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            token = generate_token(new_user.user_id, new_user.role)
            return {
                'success': True,
                'message': '注册成功',
                'data': {
                    'token': token,
                    'user': new_user.to_dict()
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'注册失败: {str(e)}'}, 500

    @staticmethod
    def reset_password(user_no, new_password):
        """密码重置业务逻辑"""
        if not user_no or not new_password:
            return {'success': False, 'message': '请填写完整信息'}, 400
        
        if len(new_password) < 6:
            return {'success': False, 'message': '密码长度至少6位'}, 400
        
        user = SysUser.query.filter_by(user_no=user_no).first()
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        
        try:
            user.password = hash_password(new_password)
            db.session.commit()
            return {'success': True, 'message': '密码重置成功'}, 200
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'密码重置失败: {str(e)}'}, 500
