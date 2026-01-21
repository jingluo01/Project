from flask import Blueprint, request
from app.services.auth_service import AuthService
from app.common.response import Result

# 定义蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_service = AuthService()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return Result.error(msg="用户名和密码不能为空")

    try:
        res = auth_service.login(username, password)
        return Result.success(res, msg="登录成功")
    except ValueError as e:
        return Result.fail(str(e))
    except Exception as e:
        return Result.fail(f"系统错误: {str(e)}", code=500)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 1) # 默认学生
    user_no = data.get('user_no') # 获取学号/工号
    
    if not username or not password:
        return Result.error(msg="用户名和密码不能为空")

    try:
        # 传入 user_no
        res = auth_service.register(username, password, role, user_no)
        return Result.success(res, msg="注册成功")
    except ValueError as e:
        return Result.fail(str(e))
    except Exception as e:
        return Result.fail(f"注册失败: {str(e)}")