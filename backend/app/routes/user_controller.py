from flask import Blueprint, request, g
from app.services.user_service import UserService
from app.common.response import Result
from app.utils.decorators import login_required

user_bp = Blueprint('user', __name__, url_prefix='/api/user')
user_service = UserService()

@user_bp.route('/info', methods=['GET'])
@login_required
def get_info():
    """获取当前登录用户信息"""
    try:
        # g.user_id 由 @login_required 注入
        data = user_service.get_user_profile(g.user_id)
        return Result.success(data)
    except Exception as e:
        return Result.fail(str(e))

@user_bp.route('/car', methods=['POST'])
@login_required
def bind_car():
    """绑定车辆"""
    data = request.json
    plate_number = data.get('plate_number')
    
    if not plate_number:
        return Result.error(msg="车牌号不能为空")
        
    try:
        data = user_service.bind_car(g.user_id, plate_number)
        return Result.success(data, msg="车辆绑定成功")
    except ValueError as e:
        return Result.fail(str(e))
    except Exception as e:
        return Result.fail(f"绑定失败: {str(e)}")