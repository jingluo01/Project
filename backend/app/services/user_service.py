"""
用户服务模块，提供获取用户画像、账户充值、用户列表分页及信息更新等功能。
"""

from app.extensions import db
from app.models.user import SysUser
from app.services.car_service import CarService
from app.utils.service_utils import handle_service_exception
from decimal import Decimal

class UserService:
    """用户服务类"""

    @staticmethod
    def get_profile(user):
        """
        获取指定用户的画像逻辑，包含用户的基本信息和关联的车辆列表。

        Args:
            user (SysUser): 当前用户对象

        Returns:
            tuple: 包含具有用户数据的响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        profile = user.to_dict()
        profile['cars'] = CarService.get_user_cars(user)
        return {'success': True, 'data': profile}, 200

    @staticmethod
    @handle_service_exception(message_prefix="充值失败")
    def recharge(user, amount):
        """
        处理账户充值业务逻辑。

        Args:
            user (SysUser): 当前用户对象
            amount (float | str): 充值金额，需大于 0

        Returns:
            tuple: 包含响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        if not amount:
            return {'success': False, 'message': '充值金额不能为空'}, 400
        
        amount = Decimal(str(amount))
        if amount <= 0:
            return {'success': False, 'message': '充值金额必须大于0'}, 400
        
        user.balance += amount
        db.session.commit()
        return {
            'success': True,
            'message': '充值成功',
            'data': {'balance': float(user.balance)}
        }, 200

    @staticmethod
    def get_users_list(page=1, per_page=20):
        """
        获取系统的用户列表逻辑，支持分页查询，按创建时间降序排序。

        Args:
            page (int, optional): 当前页码. Defaults to 1.
            per_page (int, optional): 每页显示的记录数. Defaults to 20.

        Returns:
            tuple: 包含分页结果信息的响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        pagination = SysUser.query.order_by(SysUser.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'success': True,
            'data': {
                'users': [user.to_dict() for user in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page
            }
        }, 200

    @staticmethod
    @handle_service_exception(message_prefix="用户信息更新失败")
    def update_user(user_id, data):
        """
        更新指定用户的信息逻辑，支持修改用户名、角色、信用分、余额及账户状态等字段。

        Args:
            user_id (int): 待更新的用户 ID
            data (dict): 包含待修改数据的字典

        Returns:
            tuple: 包含更新后信息的响应字典 (dict) 和 HTTP 状态码 (int) 的元组
        """
        user = SysUser.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        
        if 'username' in data:
            user.username = data['username']
        if 'role' in data:
            user.role = data['role']
        if 'credit_score' in data:
            user.credit_score = data['credit_score']
        if 'balance' in data:
            user.balance = Decimal(str(data['balance']))
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        return {'success': True, 'message': '用户信息更新成功', 'data': user.to_dict()}, 200
