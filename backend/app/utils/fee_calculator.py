from datetime import datetime
from decimal import Decimal

def calculate_parking_fee(in_time, out_time, fee_rate, free_time_minutes, user_role, role_discount):
    """
    计算停车费用
    
    Args:
        in_time: 入场时间
        out_time: 出场时间
        fee_rate: 每小时费率
        free_time_minutes: 免费时长(分钟)
        user_role: 用户角色
        role_discount: 角色折扣配置
    
    Returns:
        Decimal: 应付费用
    """
    if not in_time or not out_time:
        return Decimal('0.00')
    
    # 计算停车时长(分钟)
    duration = (out_time - in_time).total_seconds() / 60
    
    # # 扣除免费时长
    # chargeable_minutes = max(0, duration - free_time_minutes)
    chargeable_minutes = duration
    
    # 转换为小时(向上取整)
    chargeable_hours = (chargeable_minutes + 59) // 60  # 不足1小时按1小时计
    
    # 计算基础费用
    base_fee = Decimal(str(chargeable_hours)) * Decimal(str(fee_rate))
    
    # 获取倍率因子
    from flask import current_app
    multiplier = Decimal(str(current_app.config.get('FEE_MULTIPLIER', 1.0)))
    
    # 应用角色折扣和倍率
    discount = Decimal(str(role_discount.get(user_role, 1.0)))
    final_fee = base_fee * discount * multiplier
    
    # 保留两位小数
    return final_fee.quantize(Decimal('0.01'))

def get_discount_rate(user_role, role_discount):
    """获取用户折扣率"""
    return role_discount.get(user_role, 1.0)
