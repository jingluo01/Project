from flask import current_app
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
        
        # --- 核心：单设备登陆逻辑 - 覆盖旧 Session ---
        import app.extensions
        if app.extensions.redis_client:
            # 1. 存储当前唯一有效的 Token，过期时间与 JWT 一致
            app.extensions.redis_client.set(
                f"user_session:{user.user_id}", 
                token, 
                ex=int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            )
            
            # 2. 实时推送踢出通知 (WebSocket)
            # 向该用户的私有频道发送踢出指令，排除刚生成的这个 token
            app.extensions.socketio.emit(
                'kickout', 
                {'message': '您的账号在另一台设备登录，您已被强制下线'}, 
                room=f"user_{user.user_id}"
            )

        return {
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        }, 200

    @staticmethod
    def register(user_no, username, password):
        """
        用户注册业务逻辑 (交叉验证方案)
        1. 验证基础信息完整性
        2. 交叉验证学校官方库信息 (保证本校人员)
        3. 自动获取并应用校方库定义的角色身份
        """
        from app.models.school import SchoolMember

        if not user_no or not username or not password:
            return {'success': False, 'message': '请填写完整注册信息'}, 400
        
        if not validate_user_no(user_no):
            return {'success': False, 'message': '学号/工号格式不正确'}, 400
        
        if len(password) < 6:
            return {'success': False, 'message': '密码长度至少6位'}, 400

        # --- 第一阶段: 本地查重 ---
        if SysUser.query.filter_by(user_no=user_no).first():
            return {'success': False, 'message': '该账号已在系统中注册'}, 409

        # --- 第二阶段: 外部校方库交叉验证 ---
        # 验证逻辑: 学号必须存在且姓名必须完全匹配
        school_record = SchoolMember.query.filter_by(user_no=user_no, real_name=username).first()
        
        if not school_record:
            # 安全提示: 不明确告知是学号不存在还是姓名不匹配，增加破解难度
            return {'success': False, 'message': '身份验证失败：学号/工号与姓名不匹配，或非本校在库人员'}, 403

        # --- 第三阶段: 自动角色分配与账户创建 ---
        # 从校方库同步角色: 1(学生), 2(教师)
        role = school_record.member_type
        
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
            
            # --- 同步单设备登陆逻辑 ---
            import app.extensions
            if app.extensions.redis_client:
                app.extensions.redis_client.set(
                    f"user_session:{new_user.user_id}", 
                    token, 
                    ex=int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
                )

            return {
                'success': True,
                'message': f'验证成功！已作为{"教师" if role == 2 else "学生"}身份完成注册',
                'data': {
                    'token': token,
                    'user': new_user.to_dict()
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'系统同步失败: {str(e)}'}, 500

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
