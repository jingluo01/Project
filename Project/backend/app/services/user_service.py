from app.extensions import db
from app.models.user import SysUser
from app.services.car_service import CarService
from app.utils.service_utils import handle_service_exception
from decimal import Decimal

class UserService:
    @staticmethod
    def get_profile(user):
        """获取用户画像逻辑"""
        profile = user.to_dict()
        profile['cars'] = CarService.get_user_cars(user)
        return {'success': True, 'data': profile}, 200

    @staticmethod
    @handle_service_exception(message_prefix="充值失败")
    def recharge(user, amount):
        """账户充值业务逻辑"""
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
        """获取用户列表逻辑"""
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
        """更新用户信息逻辑"""
        user = SysUser.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        
        # 允许修改的字段
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
